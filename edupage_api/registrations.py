"""Read-only registrations, surveys and teacher consultations.

Uses the existing session and never executes JavaScript or submits a selection.
Question content is exposed as server JSON, since EduPage question types vary.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlencode, urlsplit
from zoneinfo import ZoneInfo

from edupage_api.exceptions import (
    ExpiredSessionException,
    MissingDataException,
    RequestError,
)
from edupage_api.module import Module, ModuleHelper


def _date(value, tz):
    return datetime.fromisoformat(value).replace(tzinfo=ZoneInfo(tz)) if value else None


def _true(value):
    return value is True or value in (1, "1", "yes")


class _HTML(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.scripts = []
        self.slots = []
        self._script = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and not attrs.get("src"):
            self._script = []
        if "timeframe" in attrs.get("class", "").split() and attrs.get("data-cas"):
            self.slots.append(attrs)

    def handle_data(self, data):
        if self._script is not None:
            self._script.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            self.scripts.append("".join(self._script))
            self._script = None


def _bootstrap(text, widget):
    for script in _HTML(text).scripts:
        match = re.search(r"\." + re.escape(widget) + r"\s*\(\s*(\{)", script)
        if match:
            try:
                data, _ = json.JSONDecoder().raw_decode(script[match.start(1) :])
                return data
            except (ValueError, TypeError) as exc:
                raise MissingDataException("Invalid EduPage bootstrap JSON") from exc
    raise MissingDataException(f"EduPage bootstrap {widget} missing")


@dataclass
class RegistrationSelection:
    target_id: str
    status: str
    answers: object = None
    parent_confirmed_at: datetime | None = None
    reserved_until: datetime | None = None


@dataclass
class RegistrationTarget:
    target_id: str
    name: str
    question: object = None
    minimum: int | None = None
    maximum: int | None = None
    confirmed_count: int | None = None
    reserved_count: int | None = None


@dataclass
class Registration:
    action_id: str
    name: str
    note: str = ""
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    active: bool = False
    votable: bool = False
    parent_confirmed: bool = False
    targets: list[RegistrationTarget] = field(default_factory=list)
    selection: list[RegistrationSelection] = field(default_factory=list)
    requires_parent_confirmation: bool = False


@dataclass
class RegistrationHistory:
    action_id: str
    name: str
    timestamp: datetime | None


@dataclass
class Consultation:
    consultation_id: str
    teacher_id: str
    teacher_name: str
    starts_at: datetime | None
    ends_at: datetime | None
    slot_minutes: int
    booking_opens_at: datetime | None
    booking_closes_at: datetime | None
    note: str = ""
    teaches_student: bool | None = None
    is_class_teacher: bool = False


@dataclass
class ConsultationReservation:
    consultation_id: str
    starts_at: datetime | None
    visit_id: str | None = None


@dataclass
class ConsultationOverview:
    consultations: list[Consultation]
    reservations: list[ConsultationReservation]


@dataclass
class ConsultationSlot:
    consultation_id: str
    starts_at: datetime
    status: str
    own: bool
    visit_id: str | None = None
    expires_at: datetime | None = None
    closed: bool = False


def _number(value):
    return int(value) if value not in (None, "") else None


class Registrations(Module):
    """Read operations in the currently selected account/child context.

    EduPage local timestamps use ``timezone_name`` (default Europe/Prague).
    Callers with schools in another timezone must pass that school's timezone.
    """

    def __init__(self, edupage, timezone_name="Europe/Prague"):
        super().__init__(edupage)
        ZoneInfo(timezone_name)  # Validate before any request.
        self.timezone = timezone_name

    def _request(self, path, data=None):
        parts = urlsplit(path)
        if parts.scheme or parts.netloc or parts.path not in ("/signin/", "/calendar/"):
            raise ValueError("Unexpected EduPage read endpoint")
        query = parse_qs(parts.query, keep_blank_values=True)
        if query.get("cmd", [None])[0] not in (
            "SigninHome",
            "SigninActionPlayer",
            "KonzultacneHodinyScheduler",
            "KonzultacneHodinyVisit",
        ) or any(k.startswith("ak_") for k in query):
            raise ValueError("Unexpected EduPage read command")
        if any(action != "getData" for action in query.get("akcia", [])):
            raise ValueError("Only read actions are supported")
        response = self.edupage.session.post(
            f"https://{self.edupage.subdomain}.edupage.org{path}", data=data or {}
        )
        if response.status_code != 200:
            raise RequestError(f"EduPage returned HTTP {response.status_code}")
        # Shared headers/dialogs may contain password inputs on logged-in pages.
        # Only the final URL path, not arbitrary HTML or query text, is evidence
        # of an authentication redirect. Missing module bootstrap stays a data error.
        if urlsplit(response.url).path.rstrip("/") == "/login" or urlsplit(response.url).path.startswith("/login/"):
            raise ExpiredSessionException("EduPage session expired")
        return response

    def _view(self, path, widget, view):
        bootstrap = _bootstrap(self._request(path).text, widget)
        # Never forward arbitrary URLs/commands from returned JavaScript.
        form = urlsplit(bootstrap["formurl"])
        if form.path != urlsplit(path).path or form.scheme or form.netloc:
            raise MissingDataException("Unexpected EduPage form URL")
        params = parse_qs(form.query)
        jwid = params.get("jwid", [None])[0]
        if not jwid:
            raise MissingDataException("EduPage form identifier missing")
        command = parse_qs(urlsplit(path).query)["cmd"][0]
        query = urlencode({"cmd": command, "jwid": jwid, "akcia": "getData"})
        response = self._request(f"{form.path}?{query}", {"pohlad": view})
        try:
            result = response.json()
        except ValueError as exc:
            raise MissingDataException("Expected EduPage JSON view") from exc
        if not isinstance(result, dict):
            raise MissingDataException("Expected EduPage view object")
        return result

    @ModuleHelper.logged_in
    def get_registrations(self):
        """List assigned actions, including closed actions; fetch each detail."""
        data = self._view("/signin/?cmd=SigninHome", "signinHome", "openableActions")
        if not isinstance(data.get("actions"), list):
            raise MissingDataException("EduPage actions missing")
        ids = dict.fromkeys(str(r["actionid"]) for r in data["actions"])
        return [self.get_registration(action_id) for action_id in ids]

    @ModuleHelper.logged_in
    def get_registration(self, action_id):
        """Read questions, options and own selections without voting."""
        path = "/signin/?" + urlencode(
            {"cmd": "SigninActionPlayer", "actionid": str(action_id)}
        )
        data = _bootstrap(self._request(path).text, "signinactionplayer")
        row = data["actionData"]
        targets = []
        for target in row.get("targets") or []:
            content = target.get("data") or {}
            targets.append(
                RegistrationTarget(
                    str(target["targetid"]),
                    target.get("name") or "",
                    content.get("content") if content.get("type") == "card" else None,
                    _number(target.get("min_users")),
                    _number(target.get("max_users")),
                    _number(target.get("confirmed_count")),
                    _number(target.get("reserved_count")),
                )
            )
        selections = []
        for target_id, selection in (data.get("selection") or {}).items():
            answers = selection.get("answers")
            if isinstance(answers, str):
                answers = json.loads(answers)
            selections.append(
                RegistrationSelection(
                    str(target_id),
                    selection.get("stav") or "unknown",
                    answers,
                    _date(selection.get("parent_confirmed"), self.timezone),
                    _date(selection.get("reserved_till"), self.timezone),
                )
            )
        return Registration(
            str(row["actionid"]),
            row.get("name") or "",
            row.get("note") or "",
            _date(row.get("time_from"), self.timezone),
            _date(row.get("time_to"), self.timezone),
            _true(row.get("active")),
            _true(data.get("votable")),
            _true(data.get("parentConfirmed")),
            targets,
            selections,
            str((row.get("data") or {}).get("parents_block") or "") in ("1", "2", "3"),
        )

    @ModuleHelper.logged_in
    def get_registration_history(self):
        data = self._view("/signin/?cmd=SigninHome", "signinHome", "history")
        if not isinstance(data.get("history"), list):
            raise MissingDataException("EduPage history missing")
        return [
            RegistrationHistory(
                str(r["actionid"]),
                r.get("action_name") or "",
                _date(r.get("timestamp"), self.timezone),
            )
            for r in data["history"]
        ]

    @ModuleHelper.logged_in
    def get_consultations(self):
        """Read offered blocks and reservations of the current account."""
        data = _bootstrap(
            self._request("/calendar/?cmd=KonzultacneHodinyScheduler").text,
            "konzultacneHodinyScheduler2",
        )
        if not isinstance(data.get("hodinyVsetci"), dict):
            raise MissingDataException("EduPage consultation blocks missing")
        blocks = []
        for rows in data["hodinyVsetci"].values():
            for row in rows:
                blocks.append(
                    Consultation(
                        str(row["konzultaciaid"]),
                        str(row["ucitelid"]),
                        " ".join(
                            filter(None, (row.get("p_meno"), row.get("p_priezvisko")))
                        ),
                        _date(row.get("cas_od"), self.timezone),
                        _date(row.get("cas_do"), self.timezone),
                        int(row["timeframe"]),
                        _date(row.get("prihlasovanie_odkedy"), self.timezone),
                        _date(row.get("prihlasovanie_dokedy"), self.timezone),
                        row.get("poznamka") or "",
                        bool((data.get("coUci") or {}).get(str(row["ucitelid"])))
                        if isinstance(data.get("coUci"), dict)
                        else None,
                    )
                )
        if "rezervacie" not in data and "rezervacieMoje" not in data:
            raise MissingDataException("EduPage own reservation list missing")
        bookings = {}
        for row in (data.get("rezervacie") or []) + (data.get("rezervacieMoje") or []):
            booking = ConsultationReservation(
                str(row["konzultaciaid"]),
                _date(
                    row.get("cas_odkedy") or row.get("cas_rezervacie"), self.timezone
                ),
                str(row["visitid"]) if row.get("visitid") else None,
            )
            if booking.starts_at is None:
                raise MissingDataException("EduPage reservation start missing")
            bookings[(booking.consultation_id, booking.starts_at)] = booking
        return ConsultationOverview(blocks, list(bookings.values()))

    @ModuleHelper.logged_in
    def get_consultation_slots(self, consultation_id):
        """Read server-rendered slot states. Never click or reserve a slot."""
        path = "/calendar/?" + urlencode(
            {
                "cmd": "KonzultacneHodinyVisit",
                "konzultaciaids": str(consultation_id),
                "asDialog": "1",
            }
        )
        text = self._request(path).text
        if "konzultacieVDni" not in text:
            raise MissingDataException("EduPage consultation detail missing")
        return self._slots(text, consultation_id)

    def _slots(self, text, consultation_id):
        result = []
        for row in _HTML(text).slots:
            if row.get("data-konzultaciaid") != str(consultation_id):
                continue
            classes = row.get("class", "").split()
            status = (
                "temporary"
                if "unconfirmed" in classes
                else "reserved"
                if "confirmed" in classes
                else "free"
                if "free" in classes
                else "unknown"
            )
            result.append(
                ConsultationSlot(
                    str(consultation_id),
                    datetime.fromtimestamp(int(row["data-cas"]), timezone.utc),
                    status,
                    "moje" in classes,
                    row.get("data-visitid") or None,
                    _date(row.get("data-platnost"), self.timezone),
                    "closed" in classes,
                )
            )
        return result
