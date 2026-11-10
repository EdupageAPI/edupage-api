import unittest
from unittest.mock import patch

from edupage_api import Edupage
from edupage_api.grades import Grades


class GradeTypeTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True

    def get_grades(self, grade_data):
        with patch.object(
            Grades, "_Grades__get_grade_data", return_value=grade_data
        ), patch(
            "edupage_api.grades.DbiHelper.fetch_subject_name", return_value="Math"
        ):
            return Grades(self.api).get_grades(None, None)

    def get_grade(self, details, data="1", event_id="10"):
        grade_data = {
            "vsetkyZnamky": [
                {"udalostid": event_id, "datum": "2026-10-01 08:00:00", "data": data}
            ],
            "vsetkyUdalosti": {
                "edupage": {"10": {"p_meno": "Test", "PredmetID": "-5", **details}}
            },
        }
        with patch.object(
            Grades, "_Grades__get_grade_data", return_value=grade_data
        ), patch(
            "edupage_api.grades.DbiHelper.fetch_subject_name", return_value="Math"
        ):
            grades = Grades(self.api).get_grades(None, None)

        self.assertEqual(len(grades), 1)
        return grades[0]

    def test_normal_grade(self):
        grade = self.get_grade({"p_typ_udalosti": "1", "p_vaha": "20"})
        self.assertIsNone(grade.max_points)
        self.assertEqual(grade.importance, 1)

    def test_numeric_grade_type(self):
        grade = self.get_grade({"p_typ_udalosti": 1, "p_vaha": 20})
        self.assertIsNone(grade.max_points)
        self.assertEqual(grade.importance, 1)

    def test_percental_grade(self):
        grade = self.get_grade(
            {"p_typ_udalosti": "3", "p_vaha": "20", "p_vaha_body": "100"}, data="80"
        )
        self.assertEqual(grade.max_points, 100)
        self.assertEqual(grade.percent, 80)

    def test_symbolic_grade(self):
        grade = self.get_grade({"p_typ_udalosti": "4", "p_vaha": "20"}, data="Ú")
        self.assertEqual(grade.grade_n, "Ú")
        self.assertIsNone(grade.max_points)
        self.assertEqual(grade.importance, 1)
        self.assertIsNone(grade.percent)

    def test_unknown_grade_type_without_importance(self):
        grade = self.get_grade({"p_typ_udalosti": "9"}, data="A")
        self.assertIsNone(grade.max_points)
        self.assertIsNone(grade.importance)

    def test_numeric_event_id(self):
        grade = self.get_grade({"p_typ_udalosti": "1", "p_vaha": "20"}, event_id=10)
        self.assertEqual(grade.event_id, 10)
        self.assertEqual(grade.title, "Test")

    def test_grade_without_event_details_is_skipped(self):
        grades = self.get_grades(
            {
                "vsetkyZnamky": [
                    {"udalostid": 11, "datum": "2026-10-01 08:00:00", "data": "1"},
                    {"udalostid": 10, "datum": "2026-10-01 08:00:00", "data": "2"},
                ],
                "vsetkyUdalosti": {
                    "edupage": {
                        "10": {
                            "p_meno": "Test",
                            "PredmetID": "-5",
                            "p_typ_udalosti": "1",
                            "p_vaha": "20",
                        }
                    }
                },
            }
        )
        self.assertEqual([g.event_id for g in grades], [10])


if __name__ == "__main__":
    unittest.main()
