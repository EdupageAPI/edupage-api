import unittest
from datetime import date
from unittest.mock import Mock, patch

from edupage_api import Edupage
from edupage_api.exceptions import MissingDataException
from edupage_api.timetables import Timetables


class ParentTimetableTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True
        self.api.subdomain = "example"
        self.api.session = Mock()

    def login_as(self, user_id, **data):
        self.api.data = {"userid": user_id, **data}

    def test_parent_without_selected_child_must_switch(self):
        for child_ids in ([-5], [-5, -6], [], None):
            with self.subTest(child_ids=child_ids):
                self.login_as("Rodic-1", parentStudentids=child_ids)

                with self.assertRaisesRegex(MissingDataException, "switch_to_child"):
                    Timetables(self.api).get_my_timetable(date(2026, 10, 12))

    def test_parent_with_selected_child_gets_childs_timetable(self):
        self.login_as("Rodic-1", parentStudentids=[-5, -6])
        self.api._selected_child_id = -6
        student = Mock()

        with patch(
            "edupage_api.timetables.People.get_student", return_value=student
        ) as get_student, patch.object(
            Timetables, "get_timetable", return_value="timetable"
        ) as get_timetable:
            result = Timetables(self.api).get_my_timetable(date(2026, 10, 12))

        get_student.assert_called_once_with(-6)
        get_timetable.assert_called_once_with(student, date(2026, 10, 12))
        self.assertEqual(result, "timetable")

    def test_unexpected_response_raises_missing_data(self):
        self.login_as("Student-1")
        self.api.session.get.return_value.text = 'href="?gpid=1&gsh=abc"'
        self.api.session.post.return_value.text = "JS:window.location.reload();"

        with self.assertRaises(MissingDataException):
            Timetables(self.api).get_my_timetable(date(2026, 10, 12))


if __name__ == "__main__":
    unittest.main()
