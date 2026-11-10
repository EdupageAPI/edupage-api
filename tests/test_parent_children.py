import unittest
from unittest.mock import Mock

from edupage_api import Edupage
from edupage_api.exceptions import NotParentException
from edupage_api.people import EduStudent


def student_data(first, last, number):
    return {
        "firstname": first,
        "lastname": last,
        "gender": "M",
        "classid": "1",
        "numberinclass": str(number),
        "datefrom": "2020-09-01",
    }


class GetChildrenTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True
        self.api.session = Mock()

    def login_as(self, user_id, **data):
        self.api.data = {
            "userid": user_id,
            "dbi": {
                "students": {
                    "-5": student_data("Anna", "Novak", 1),
                    "-6": student_data("Boris", "Novak", 2),
                    "-7": student_data("Cyril", "Other", 3),
                }
            },
            **data,
        }

    def test_returns_only_the_parents_children(self):
        self.login_as("Rodic-1", parentStudentids=[-5, -6])

        children = self.api.get_children()

        self.assertEqual([c.person_id for c in children], [-5, -6])
        self.assertTrue(all(isinstance(c, EduStudent) for c in children))
        self.assertEqual(children[0].name, "Anna Novak")

    def test_accepts_string_ids(self):
        self.login_as("Rodic-1", parentStudentids=["-6"])

        self.assertEqual([c.person_id for c in self.api.get_children()], [-6])

    def test_no_children_returns_empty_list(self):
        for child_ids in ([], None):
            with self.subTest(child_ids=child_ids):
                self.login_as("Rodic-1", parentStudentids=child_ids)

                self.assertEqual(self.api.get_children(), [])

    def test_child_missing_from_dbi_is_skipped(self):
        self.login_as("Rodic-1", parentStudentids=[-5, -99])

        self.assertEqual([c.person_id for c in self.api.get_children()], [-5])

    def test_numeric_fields_may_be_ints_or_empty(self):
        # EduPage sends numberinclass as a string for some students and an int for others
        self.login_as("Rodic-1", parentStudentids=[-5, -6])
        students = self.api.data["dbi"]["students"]
        students["-5"]["numberinclass"] = 13
        students["-6"]["numberinclass"] = ""

        children = self.api.get_children()

        self.assertEqual([c.number_in_class for c in children], [13, None])

    def test_not_a_parent_raises(self):
        self.login_as("Student-1", parentStudentids=[-5])

        with self.assertRaises(NotParentException):
            self.api.get_children()

    def test_no_requests_are_made(self):
        self.login_as("Rodic-1", parentStudentids=[-5])

        self.api.get_children()

        self.api.session.get.assert_not_called()
        self.api.session.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
