import unittest
from unittest.mock import Mock

from edupage_api import Edupage
from edupage_api.dbi import DbiHelper


class DbiItemGroupTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True
        self.api.subdomain = "example"
        self.api.session = Mock()

    def test_empty_group_serialised_as_array_is_read_as_empty_mapping(self):
        # EduPage serialises a dbi item group that has no entries as [] instead
        # of {}. Mapping access must keep working.
        self.api.data = {"dbi": {"classrooms": []}}

        self.assertEqual(DbiHelper(self.api).fetch_classroom_list(), {})
        self.assertIsNone(DbiHelper(self.api).fetch_classroom_number("42"))
        self.assertIsNone(DbiHelper(self.api).fetch_teacher_data("42"))

    def test_every_group_type_is_normalised_not_just_classrooms(self):
        # The shape change is not tied to one group; any group may arrive as an
        # empty array. Each of these is reached through .get() by
        # __get_item_with_id.
        self.api.data = {
            "dbi": {
                "teachers": [],
                "students": [],
                "subjects": [],
                "classrooms": [],
                "classes": [],
            }
        }
        dbi = DbiHelper(self.api)

        self.assertEqual(dbi.fetch_teacher_list(), {})
        self.assertEqual(dbi.fetch_student_list(), {})
        self.assertEqual(dbi.fetch_subject_list(), {})
        self.assertEqual(dbi.fetch_classroom_list(), {})
        self.assertEqual(dbi.fetch_class_list(), {})

        self.assertIsNone(dbi.fetch_teacher_data("1"))
        self.assertIsNone(dbi.fetch_student_data("1"))
        self.assertIsNone(dbi.fetch_subject_name("1"))
        self.assertIsNone(dbi.fetch_classroom_number("1"))
        self.assertIsNone(dbi.fetch_class_name("1"))

    def test_group_serialised_as_dict_is_returned_unchanged(self):
        classes = {"-2": {"id": -2, "name": "A", "short": "A"}}
        self.api.data = {"dbi": {"classes": classes}}

        self.assertIs(DbiHelper(self.api).fetch_class_list(), classes)
        self.assertEqual(DbiHelper(self.api).fetch_class_name("-2"), "A")

    def test_missing_group_still_returns_none(self):
        self.api.data = {"dbi": {}}

        self.assertIsNone(DbiHelper(self.api).fetch_classroom_list())
        self.assertIsNone(DbiHelper(self.api).fetch_classroom_number("42"))

    def test_missing_dbi_still_returns_none(self):
        self.api.data = {}

        self.assertIsNone(DbiHelper(self.api).fetch_classroom_list())

    def test_populated_array_group_is_not_reinterpreted(self):
        # A populated array has never been observed. It must keep failing loudly
        # rather than be mapped onto positional keys, which would fabricate ids
        # that can never match a real reference.
        self.api.data = {"dbi": {"classrooms": [{"name": "R1", "short": "R1"}]}}

        with self.assertRaises(AttributeError):
            DbiHelper(self.api).fetch_classroom_number("42")


if __name__ == "__main__":
    unittest.main()
