"""Synthetic fixtures based on observed response shapes; no account data."""

import json
import unittest
from unittest.mock import Mock

from edupage_api import Edupage
from edupage_api.exceptions import (
    ExpiredSessionException,
    MissingDataException,
    NotLoggedInException,
)
from edupage_api.registrations import Registrations


def html(widget, data):
    return (
        '<script>$("#fixture").'
        + widget
        + "("
        + json.dumps(data)
        + "); ignored();</script>"
    )


def response(text="", data=None, status=200, url="https://school.edupage.org/signin/"):
    return Mock(text=text, status_code=status, url=url, json=Mock(return_value=data))


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True
        self.api.subdomain = "school"
        self.api.session = Mock()
        self.module = Registrations(self.api)

    def set_responses(self, *responses):
        self.api.session.post.side_effect = responses

    def bootstrap(self):
        return response(
            html("signinHome", {"formurl": "/signin/?jwid=dynamic&cmd=SigninHome"})
        )

    def detail(self, **values):
        data = {
            "actionData": {
                "actionid": "a/1",
                "name": "Survey ); { }",
                "time_from": "2026-10-01 09:00:00",
                "time_to": "2026-11-01 18:00:00",
                "active": True,
                "targets": [
                    {
                        "targetid": "q1",
                        "name": "Question",
                        "data": {
                            "type": "card",
                            "content": {"type": "multiple", "text": "Pick"},
                        },
                    }
                ],
            },
            "votable": True,
            "selection": {},
        }
        data.update(values)
        return response(html("signinactionplayer", data))

    def test_empty_assigned_list(self):
        self.set_responses(self.bootstrap(), response(data={"actions": []}))
        self.assertEqual(self.api.get_registrations(), [])
        args, kwargs = self.api.session.post.call_args
        self.assertIn("akcia=getData", args[0])
        self.assertEqual(kwargs["data"], {"pohlad": "openableActions"})

    def test_list_deduplicates_and_loads_closed_detail(self):
        closed = {"actionid": "1", "name": "Closed", "active": False, "targets": []}
        self.set_responses(
            self.bootstrap(),
            response(data={"actions": [{"actionid": "1"}, {"actionid": "1"}]}),
            response(
                html("signinactionplayer", {"actionData": closed, "votable": False})
            ),
        )
        result = self.module.get_registrations()
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0].active)
        self.assertEqual(self.api.session.post.call_count, 3)

    def test_survey_content_and_json_answers(self):
        self.set_responses(
            self.detail(
                selection={"q1": {"stav": "answered", "answers": '{"choice": [2]}'}}
            )
        )
        result = self.api.get_registration("a/1")
        self.assertEqual(result.targets[0].question["type"], "multiple")
        self.assertEqual(result.selection[0].answers, {"choice": [2]})
        self.assertEqual(result.opens_at.utcoffset().total_seconds(), 7200)
        self.assertEqual(result.closes_at.utcoffset().total_seconds(), 3600)
        self.assertIn("actionid=a%2F1", self.api.session.post.call_args.args[0])

    def test_confirmed_parent_and_temporary_selection(self):
        self.set_responses(
            self.detail(
                parentConfirmed=True,
                selection={
                    "1": {
                        "stav": "ok",
                        "parent_confirmed": "2026-10-01 10:00:00",
                        "answers": None,
                    },
                    "2": {"stav": "reserved", "reserved_till": "2026-10-01 10:05:00"},
                },
            )
        )
        result = self.module.get_registration("1")
        self.assertTrue(result.parent_confirmed)
        self.assertEqual(result.selection[1].status, "reserved")
        self.assertIsNotNone(result.selection[1].reserved_until)

    def test_history(self):
        self.set_responses(
            self.bootstrap(),
            response(
                data={
                    "history": [
                        {
                            "actionid": "1",
                            "action_name": "Action",
                            "timestamp": "2026-10-01 09:00:00",
                        }
                    ]
                }
            ),
        )
        self.assertEqual(self.api.get_registration_history()[0].name, "Action")
        self.assertEqual(
            self.api.session.post.call_args.kwargs["data"], {"pohlad": "history"}
        )

    def test_missing_list_is_failure_not_empty(self):
        self.set_responses(self.bootstrap(), response(data={}))
        with self.assertRaises(MissingDataException):
            self.module.get_registrations()

    def test_login_expiration(self):
        self.set_responses(
            response('<input type="password">', url="https://school.edupage.org/login/")
        )
        with self.assertRaises(ExpiredSessionException):
            self.module.get_registrations()

    def test_password_dialog_on_authenticated_page_is_not_expiry(self):
        page = self.bootstrap()
        page.text += '<dialog hidden><input type="password"></dialog>'
        self.set_responses(page, response(data={"actions": []}))
        self.assertEqual(self.module.get_registrations(), [])

    def test_login_text_in_query_is_not_expiry(self):
        page = self.bootstrap()
        page.url = "https://school.edupage.org/signin/?return=/login/"
        self.set_responses(page, response(data={"actions": []}))
        self.assertEqual(self.module.get_registrations(), [])

    def test_not_logged_in(self):
        self.api.is_logged_in = False
        with self.assertRaises(NotLoggedInException):
            self.api.get_consultations()
        self.api.session.post.assert_not_called()

    def test_unexpected_html(self):
        self.set_responses(response("<html>maintenance</html>"))
        with self.assertRaises(MissingDataException):
            self.module.get_consultations()

    def test_external_bootstrap_url_rejected(self):
        self.set_responses(
            response(
                html("signinHome", {"formurl": "https://other.test/signin/?jwid=x"})
            )
        )
        with self.assertRaises(MissingDataException):
            self.module.get_registrations()
        self.assertEqual(self.api.session.post.call_count, 1)

    def test_mutations_and_external_hosts_rejected(self):
        for path in (
            "/signin/?cmd=SigninActionPlayer&akcia=confirm",
            "/calendar/?cmd=KonzultacneHodinyVisit&akcia=rezervuj",
            "/calendar/?cmd=KonzultacneHodinyVisit&akcia=zrus",
            "https://other.test/signin/?cmd=SigninHome",
        ):
            with self.assertRaises(ValueError):
                self.module._request(path)
        self.api.session.post.assert_not_called()

    def test_consultation_overview_and_dedup_own_reservations(self):
        booking = {
            "konzultaciaid": "2",
            "cas_odkedy": "2026-11-10 13:00:00",
            "visitid": "v1",
        }
        row = {
            "konzultaciaid": "2",
            "ucitelid": "-1",
            "p_meno": "Example",
            "p_priezvisko": "Teacher",
            "cas_od": "2026-11-10 13:00:00",
            "cas_do": "2026-11-10 15:00:00",
            "timeframe": "30",
        }
        self.set_responses(
            response(
                html(
                    "konzultacneHodinyScheduler2",
                    {
                        "hodinyVsetci": {
                            "2026-11-10": [row, {**row, "konzultaciaid": "3"}]
                        },
                        "rezervacie": [booking],
                        "rezervacieMoje": [booking],
                    },
                )
            )
        )
        result = self.api.get_consultations()
        self.assertEqual(len(result.consultations), 2)
        self.assertEqual(len(result.reservations), 1)
        self.assertIsNone(result.consultations[0].booking_closes_at)

    def test_empty_consultations(self):
        self.set_responses(
            response(
                html(
                    "konzultacneHodinyScheduler2",
                    {"hodinyVsetci": {}, "rezervacie": []},
                )
            )
        )
        result = self.module.get_consultations()
        self.assertEqual(result.consultations, [])
        self.assertEqual(result.reservations, [])

    def test_slots_and_unknown_state(self):
        # Free state observed live; occupied variants are synthetic contract tests.
        states = [
            "free",
            "confirmed",
            "confirmed moje",
            "unconfirmed moje",
            "mystery closed",
        ]
        slots = "".join(
            f'<div class="timeframe {state}" data-konzultaciaid="3" '
            f'data-cas="{1794312000 + i * 1800}" data-visitid="" data-platnost=""></div>'
            for i, state in enumerate(states)
        )
        self.set_responses(response("<script>var konzultacieVDni=[];</script>" + slots))
        result = self.api.get_consultation_slots("3")
        self.assertEqual(
            [s.status for s in result],
            ["free", "reserved", "reserved", "temporary", "unknown"],
        )
        self.assertTrue(result[2].own)
        self.assertTrue(result[4].closed)
        self.assertEqual(result[0].starts_at.isoformat(), "2026-11-10T12:00:00+00:00")
        self.assertEqual(self.api.session.post.call_count, 1)
        self.assertNotIn("akcia=", self.api.session.post.call_args.args[0])
