import json
import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import Mock

from edupage_api.attendance import Attendance
from edupage_api.exceptions import (
    InsufficientPermissionsException,
    MissingDataException,
)


class AttendanceTests(unittest.TestCase):
    def attendance(self, payload):
        html = (
            'ASC.requireAsync("/dashboard/dochadzka.js#initZiak").then'
            '(function(f){return f(gi1,gi2,'
            + json.dumps(payload)
            + ',[-42],true);});'
        )
        self.session = Mock()
        self.session.get.return_value.text = html
        api = SimpleNamespace(
            is_logged_in=True, subdomain="school", session=self.session,
            get_user_id=lambda: "Rodic-7",
        )
        return Attendance(api)

    def test_signed_student_id_is_preserved(self):
        api = self.attendance({"students": {"-42": {
            "2026-09-25": {"prichod": "07:56:00", "odchod": "12:34:00"},
        }}})
        result = api.get_arrivals("Student-42")["2026-09-25"]
        self.assertEqual(result.arrival, datetime(2026, 9, 25, 7, 56))
        self.assertEqual(result.departure, datetime(2026, 9, 25, 12, 34))

    def test_empty_child_list_is_a_valid_empty_result(self):
        api = self.attendance({"students": {"42": []}, "dateStats": []})
        self.assertEqual(api.get_arrivals("Student42"), {})
        self.assertEqual(api.get_days_with_available_attendance("Student42"), [])
        with self.assertRaises(MissingDataException):
            api.get_attendance_statistics("Student42", date(2026, 9, 25))

    def test_empty_statistics_variants_for_known_child(self):
        for stats in ([], {}, {"42": []}, {"42": {}}):
            with self.subTest(stats=stats):
                api = self.attendance({"students": {"42": {}}, "dateStats": stats})
                self.assertEqual(api.get_days_with_available_attendance("42"), [])
                with self.assertRaises(MissingDataException):
                    api.get_attendance_statistics("42", date(2026, 9, 25))

    def test_unknown_child_is_not_reported_as_empty(self):
        for students in ([], {}, {"99": []}):
            with self.subTest(students=students):
                api = self.attendance({"students": students, "dateStats": []})
                for method, args in (
                    (api.get_arrivals, ("Student42",)),
                    (api.get_days_with_available_attendance, ("Student42",)),
                    (api.get_attendance_statistics, ("Student42", date(2026, 9, 25))),
                ):
                    with self.assertRaises(InsufficientPermissionsException):
                        method(*args)

    def test_nonempty_malformed_sections_are_not_silently_ignored(self):
        for value in ([1], None, "invalid"):
            with self.subTest(value=value):
                api = self.attendance({"students": {"42": value}})
                with self.assertRaises(MissingDataException):
                    api.get_arrivals("42")

    def test_statistics_for_signed_id_and_missing_date(self):
        api = self.attendance({"students": {"-42": {}}, "dateStats": {"-42": {
            "2026-09-25": {"absent": 2, "excused": 2, "unexcused": 0},
        }}})
        self.assertEqual(
            api.get_days_with_available_attendance("Student-42"),
            [date(2026, 9, 25)],
        )
        stats = api.get_attendance_statistics("Student-42", date(2026, 9, 25))
        self.assertEqual(stats.total_lessons_absent.count, 2)
        self.assertEqual(stats.total_lessons_absent.unexcused, 0)
        with self.assertRaises(MissingDataException):
            api.get_attendance_statistics("Student-42", date(2026, 9, 24))


if __name__ == "__main__":
    unittest.main()
