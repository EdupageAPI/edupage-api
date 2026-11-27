"""Explicit consultation writes. Read-only Registrations never calls this module."""

import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlsplit

from requests import RequestException

from edupage_api.exceptions import (
    ConsultationClosed,
    ConsultationError,
    ConsultationLimitReached,
    ConsultationNotOwned,
    ConsultationSlotNotFound,
    ConsultationSlotTaken,
    ConsultationUncertain,
    ExpiredSessionException,
)
from edupage_api.module import ModuleHelper
from edupage_api.registrations import _HTML, ConsultationReservation, Registrations


class ConsultationBooking(Registrations):
    def _detail(self, consultation_id):
        path = "/calendar/?" + urlencode(
            {
                "cmd": "KonzultacneHodinyVisit",
                "konzultaciaids": str(consultation_id),
                "asDialog": "1",
            }
        )
        text = self._request(path).text
        # Only extract the literal transport URL. Never execute a script.
        for script in _HTML(text).scripts:
            match = re.search(r"\$j\.post\('((?:\\.|[^'\\])*)&akcia=rezervuj'", script)
            if match:
                literal = json.loads('"' + match[1].replace('"', '\\"') + '"')
                parts = urlsplit(literal)
                params = parse_qs(parts.query)
                if (
                    parts.scheme
                    or parts.netloc
                    or parts.path != "/calendar/"
                    or params.get("cmd") != ["KonzultacneHodinyVisit"]
                    or not params.get("jwid")
                ):
                    raise ConsultationError("Unexpected consultation form")
                path = "/calendar/?" + urlencode(
                    {
                        "cmd": "KonzultacneHodinyVisit",
                        "jwid": params["jwid"][0],
                        "asDialog": "1",
                    }
                )
                return path, self._slots(text, consultation_id)
        raise ConsultationError("Consultation booking form missing")

    def _write(self, path, action, data, *, json_required=True):
        if action not in ("rezervuj", "confirm", "zrus"):
            raise ValueError("Unsupported consultation write")
        try:
            response = self.edupage.session.post(
                f"https://{self.edupage.subdomain}.edupage.org{path}&akcia={action}",
                data=data,
            )
        except RequestException as exc:
            # No retry: the server may already have accepted the operation.
            raise ConsultationUncertain(
                "Write outcome is unknown; check EduPage"
            ) from exc
        if "/login" in response.url or re.search(
            r"<input[^>]+type=[\'\"]password", response.text, re.I
        ):
            raise ExpiredSessionException("EduPage session expired")
        if response.status_code != 200:
            raise ConsultationUncertain("Write outcome is unknown; check EduPage")
        try:
            result = response.json()
        except ValueError as exc:
            if not json_required:
                return None  # Cancellation is verified by a fresh read.
            raise ConsultationUncertain(
                "Unexpected write response; check EduPage"
            ) from exc
        if not isinstance(result, dict):
            if not json_required:
                return None
            raise ConsultationUncertain("Unexpected write response; check EduPage")
        if result.get("status") == "ok":
            return result
        if not json_required and "status" not in result:
            return result
        # Only recognized machine-readable codes are classified. Do not infer
        # server error meanings from localized free text.
        code = result.get("code") or (result.get("data") or {}).get("code")
        error = {
            "slot_taken": ConsultationSlotTaken,
            "booking_closed": ConsultationClosed,
            "booking_limit": ConsultationLimitReached,
        }.get(code, ConsultationError)
        raise error("EduPage rejected the consultation request")

    @ModuleHelper.logged_in
    def book_consultation_slot(
        self, consultation_id, starts_at, *, dry_run=False, note=None
    ):
        if note:
            # The inspected booking protocol has no note field. Never discard it silently.
            error = ConsultationError(
                "Participant notes are not supported by this protocol"
            )
            error.code = "note_unsupported"
            raise error
        if (
            not isinstance(starts_at, datetime)
            or starts_at.tzinfo is None
            or starts_at.utcoffset() is None
        ):
            raise ValueError("starts_at must be a timezone-aware datetime")
        now = datetime.now(timezone.utc)
        if starts_at <= now:
            raise ConsultationClosed("Consultation is in the past")
        overview = self.get_consultations()
        block = next(
            (
                b
                for b in overview.consultations
                if b.consultation_id == str(consultation_id)
            ),
            None,
        )
        if block is None:
            raise ConsultationClosed("Consultation no longer offered")
        if (block.booking_opens_at and now < block.booking_opens_at) or (
            block.booking_closes_at and now > block.booking_closes_at
        ):
            raise ConsultationClosed("Booking window is closed")
        path, slots = self._detail(consultation_id)
        if any(s.own for s in slots):
            raise ConsultationLimitReached(
                "An own reservation already exists in this block"
            )
        slot = next((s for s in slots if s.starts_at == starts_at), None)
        if slot is None:
            raise ConsultationSlotNotFound(
                "This time does not exist in the consultation block"
            )
        if slot.status != "free":
            raise ConsultationSlotTaken("Slot is no longer free")
        if slot.closed:
            raise ConsultationClosed("Slot is closed")
        epoch = int(slot.starts_at.timestamp())
        if starts_at.timestamp() != epoch:
            raise ValueError("Slot start must match an exact server timeframe")
        plan = {
            "consultation_id": str(consultation_id),
            "start": starts_at.isoformat(),
            "reserve": {"konzultaciaid": str(consultation_id), "cas": str(epoch)},
            "confirm": {"visitids": "<returned visit_id>"},
        }
        if dry_run:
            return plan
        held = self._write(path, "rezervuj", plan["reserve"])
        visit_id = str((held.get("data") or {}).get("visitid") or "")
        if not visit_id:
            raise ConsultationUncertain(
                "Missing visit ID after reservation; check EduPage"
            )
        try:
            self._write(path, "confirm", {"visitids": visit_id})
            confirmed = self.get_consultation_slots(consultation_id)
        except ExpiredSessionException:
            raise
        except Exception as exc:
            raise ConsultationUncertain(
                f"Reservation {visit_id} may be held; check EduPage"
            ) from exc
        if not any(
            s.own
            and s.visit_id == visit_id
            and s.status == "reserved"
            and s.starts_at == starts_at
            for s in confirmed
        ):
            raise ConsultationUncertain(
                f"Reservation {visit_id} was not verified as confirmed"
            )
        return ConsultationReservation(str(consultation_id), starts_at, visit_id)

    @ModuleHelper.logged_in
    def cancel_consultation(self, visit_id, *, dry_run=False):
        # The server cancels by block, not visit ID. Resolve own ownership first
        # and refuse ambiguous blocks, rather than cancelling an unrelated visit.
        overview = self.get_consultations()
        booking = next(
            (r for r in overview.reservations if r.visit_id == str(visit_id)), None
        )
        if booking is None:
            raise ConsultationNotOwned("Own booking not found")
        path, slots = self._detail(booking.consultation_id)
        own = [s for s in slots if s.own]
        if len(own) != 1 or own[0].visit_id != str(visit_id):
            raise ConsultationNotOwned("Booking ownership is ambiguous")
        plan = {
            "visit_id": str(visit_id),
            "cancel": {"konzultaciaid": booking.consultation_id},
        }
        if dry_run:
            return plan
        self._write(path, "zrus", plan["cancel"], json_required=False)
        try:
            remaining = self.get_consultation_slots(booking.consultation_id)
        except Exception as exc:
            raise ConsultationUncertain("Cancellation could not be verified") from exc
        if any(s.own and s.visit_id == str(visit_id) for s in remaining):
            raise ConsultationUncertain("Reservation still present after cancellation")
        return None
