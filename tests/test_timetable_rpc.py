"""Unavailable timetable RPC data must not masquerade as authentication failure."""

import json
import unittest
from datetime import date
from unittest.mock import Mock, patch

from edupage_api import Edupage
from edupage_api.exceptions import MissingDataException, RequestError
from edupage_api.timetables import Timetables


class TimetableRpcTests(unittest.TestCase):
    def read(self, payload):
        api = Edupage()
        api.subdomain = "school"
        api.session = Mock()
        api.session.post.return_value.content = json.dumps(payload).encode()
        with patch.object(Timetables, "get_school_year", return_value=2026):
            return Timetables(api)._Timetables__get_timetable_data(-1, "students", date(2026, 11, 10))

    def test_null_missing_and_invalid_results_have_structural_diagnostics(self):
        for payload in (None, [], {}, {"r": None}, {"r": []}, {"r": "invalid"}, {"e": "PRIVATE PAYLOAD"}):
            with self.subTest(payload=payload):
                with self.assertRaises(MissingDataException) as caught:
                    self.read(payload)
                self.assertNotIn("PRIVATE PAYLOAD", str(caught.exception))

    def test_valid_empty_timetable_remains_valid(self):
        self.assertEqual(self.read({"r": {"ttitems": []}}), [])

    def test_explicit_error_remains_request_error(self):
        with self.assertRaises(RequestError):
            self.read({"r": {"error": "server unavailable"}})

    def test_public_reader_preserves_missing_data_exception(self):
        from edupage_api.people import EduStudent

        api = Edupage()
        api.is_logged_in = True
        student = EduStudent.__new__(EduStudent)
        student.person_id = -1
        with patch.object(Timetables, "_Timetables__get_timetable_data", side_effect=MissingDataException("r is null")):
            with self.assertRaises(MissingDataException):
                Timetables(api).get_timetable(student, date(2026, 11, 10))
