"""Synthetic write protocol tests; no real school requests."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from edupage_api import Edupage
from edupage_api.consultation_booking import ConsultationBooking
from edupage_api.exceptions import (
    ConsultationClosed,
    ConsultationError,
    ConsultationLimitReached,
    ConsultationNotOwned,
    ConsultationSlotTaken,
    ConsultationUncertain,
    ExpiredSessionException,
)
from edupage_api.registrations import (
    Consultation,
    ConsultationOverview,
    ConsultationReservation,
    ConsultationSlot,
)
from requests import Timeout


def make_booking():
    api = Edupage()
    api.subdomain, api.is_logged_in = ("school", True)
    api.session = Mock()
    module = ConsultationBooking(api)
    future = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=3)
    block = Consultation(
        "b1",
        "t1",
        "Teacher",
        future,
        future + timedelta(hours=1),
        30,
        None,
        future - timedelta(days=1),
        teaches_student=True,
    )
    module.get_consultations = Mock(return_value=ConsultationOverview([block], []))
    slot = ConsultationSlot("b1", future, "free", False)
    module._detail = Mock(
        return_value=("/calendar/?cmd=KonzultacneHodinyVisit&jwid=dynamic", [slot])
    )
    module.get_consultation_slots = Mock(
        return_value=[ConsultationSlot("b1", future, "reserved", True, "v1")]
    )
    api.session.post.side_effect = [
        Mock(
            status_code=200,
            url="https://school.edupage.org/calendar/",
            text="",
            json=Mock(return_value={"status": "ok", "data": {"visitid": "v1"}}),
        ),
        Mock(
            status_code=200,
            url="https://school.edupage.org/calendar/",
            text="",
            json=Mock(return_value={"status": "ok"}),
        ),
    ]
    return (module, future, block, slot)


class ConsultationBookingTests(unittest.TestCase):
    def test_dry_run_performs_no_write(self):
        booking = make_booking()
        m, start, _, _ = booking
        plan = m.book_consultation_slot("b1", start, dry_run=True)
        self.assertEqual(plan["reserve"]["cas"], str(int(start.timestamp())))
        m.edupage.session.post.assert_not_called()

    def test_book_holds_confirms_and_verifies(self):
        booking = make_booking()
        m, start, _, _ = booking
        result = m.book_consultation_slot("b1", start)
        self.assertEqual(result.visit_id, "v1")
        calls = m.edupage.session.post.call_args_list
        self.assertEqual(
            [c.args[0].split("akcia=")[1] for c in calls], ["rezervuj", "confirm"]
        )
        self.assertEqual(calls[1].kwargs["data"], {"visitids": "v1"})
        m.get_consultation_slots.assert_called_once_with("b1")

    def test_not_free_rejected_before_write(self):
        for status in ["reserved", "temporary", "unknown"]:
            with self.subTest(status=status):
                booking = make_booking()
                m, start, _, slot = booking
                slot.status = status
                with self.assertRaises(ConsultationSlotTaken):
                    m.book_consultation_slot("b1", start)
                m.edupage.session.post.assert_not_called()

    def test_closed_window(self):
        booking = make_booking()
        m, start, block, _ = booking
        block.booking_closes_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        with self.assertRaises(ConsultationClosed):
            m.book_consultation_slot("b1", start)
        m.edupage.session.post.assert_not_called()

    def test_existing_own_reservation_not_replaced(self):
        booking = make_booking()
        m, start, _, slot = booking
        slot.own = True
        with self.assertRaises(ConsultationLimitReached):
            m.book_consultation_slot("b1", start)

    def test_timeout_no_retry_and_no_confirmation(self):
        booking = make_booking()
        m, start, _, _ = booking
        m.edupage.session.post.side_effect = Timeout()
        with self.assertRaises(ConsultationUncertain):
            m.book_consultation_slot("b1", start)
        self.assertEqual(m.edupage.session.post.call_count, 1)

    def test_confirmation_must_be_verified(self):
        booking = make_booking()
        m, start, _, _ = booking
        m.get_consultation_slots.return_value = []
        with self.assertRaises(ConsultationUncertain):
            m.book_consultation_slot("b1", start)
        self.assertEqual(m.edupage.session.post.call_count, 2)

    def test_expired_session(self):
        booking = make_booking()
        m, start, _, _ = booking
        m.edupage.session.post.side_effect = None
        m.edupage.session.post.return_value = Mock(
            status_code=200, url="https://school.edupage.org/login/", text=""
        )
        with self.assertRaises(ExpiredSessionException):
            m.book_consultation_slot("b1", start)

    def test_cancel_requires_own_id(self):
        booking = make_booking()
        m, _, _, _ = booking
        with self.assertRaises(ConsultationNotOwned):
            m.cancel_consultation("foreign")
        m.edupage.session.post.assert_not_called()

    def test_cancel_dry_run_and_actual_verified(self):
        booking = make_booking()
        m, start, _, slot = booking
        m.get_consultations.return_value.reservations = [
            ConsultationReservation("b1", start, "v1")
        ]
        slot.own, slot.status, slot.visit_id = (True, "reserved", "v1")
        plan = m.cancel_consultation("v1", dry_run=True)
        self.assertEqual(plan["cancel"], {"konzultaciaid": "b1"})
        m.edupage.session.post.assert_not_called()
        m.get_consultation_slots.return_value = []
        m.cancel_consultation("v1")
        self.assertIn("akcia=zrus", m.edupage.session.post.call_args.args[0])
        self.assertEqual(m.edupage.session.post.call_count, 1)

    def test_cancel_refuses_ambiguous_block(self):
        booking = make_booking()
        m, start, _, slot = booking
        m.get_consultations.return_value.reservations = [
            ConsultationReservation("b1", start, "v1")
        ]
        slot.own, slot.visit_id = (True, "v1")
        m._detail.return_value[1].append(
            ConsultationSlot(
                "b1", start + timedelta(minutes=30), "reserved", True, "v2"
            )
        )
        with self.assertRaises(ConsultationNotOwned):
            m.cancel_consultation("v1")
        m.edupage.session.post.assert_not_called()

    def test_aware_time_and_note_validation(self):
        booking = make_booking()
        m, start, _, _ = booking
        with self.assertRaises(ValueError):
            m.book_consultation_slot("b1", start.replace(tzinfo=None))
        with self.assertRaises(ConsultationError) as error:
            m.book_consultation_slot("b1", start, note="Please call")
        self.assertEqual(error.exception.code, "note_unsupported")

    def test_extract_dynamic_form_does_not_execute_script(self):
        booking = make_booking()
        m, _, _, _ = booking
        del m._detail
        m._request = Mock(
            return_value=Mock(
                text="<script>var ignored=\"unsafe()\";\n        $j.post('\\/calendar\\/?jwid=hello\\u0026asDialog=1\\u0026cmd=KonzultacneHodinyVisit&akcia=rezervuj',{});\n        </script>"
            )
        )
        path, slots = m._detail("b1")
        self.assertIn("jwid=hello", path)
        self.assertEqual(slots, [])

    def test_nonexistent_time_is_not_reported_as_taken(self):
        booking = make_booking()
        from edupage_api.exceptions import ConsultationSlotNotFound

        m, start, _, _ = booking
        with self.assertRaises(ConsultationSlotNotFound) as error:
            m.book_consultation_slot("b1", start + timedelta(minutes=7), dry_run=True)
        self.assertEqual(error.exception.code, "slot_not_found")
        m.edupage.session.post.assert_not_called()
