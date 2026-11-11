import unittest
from unittest.mock import patch

from edupage_api import Edupage
from edupage_api.grades import Grades
from edupage_api.exceptions import FailedToParseGradeDataError


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
        with (
            patch.object(Grades, "_Grades__get_grade_data", return_value=grade_data),
            patch(
                "edupage_api.grades.DbiHelper.fetch_subject_name", return_value="Math"
            ),
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

    def test_grade_without_event_details_reports_incomplete_response(self):
        with self.assertRaises(FailedToParseGradeDataError):
            self.get_grades(
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

if __name__ == "__main__":
    unittest.main()


class MissingGradeMetadataTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True

    def test_numeric_event_ids_match_json_object_keys(self):
        payload = {
            "vsetkyZnamky": [
                {"udalostid": 10, "datum": "2026-10-21 10:00:00", "data": "1"}
            ],
            "vsetkyUdalosti": {
                "edupage": {
                    "10": {
                        "p_meno": "Test",
                        "PredmetID": "1",
                        "p_typ_udalosti": "1",
                        "p_vaha": "20",
                    }
                }
            },
        }
        with (
            patch.object(Grades, "_Grades__get_grade_data", return_value=payload),
            patch(
                "edupage_api.grades.DbiHelper.fetch_subject_name",
                return_value="Subject",
            ),
        ):
            result = Grades(self.api).get_grades(None, None)
        self.assertEqual(result[0].grade_n, 1)

    def test_missing_event_does_not_silently_change_average(self):
        from edupage_api.exceptions import FailedToParseGradeDataError

        payload = {
            "vsetkyZnamky": [{"udalostid": "10"}],
            "vsetkyUdalosti": {"edupage": {}},
        }
        with patch.object(Grades, "_Grades__get_grade_data", return_value=payload):
            with self.assertRaisesRegex(
                FailedToParseGradeDataError, r"vsetkyUdalosti.edupage\[10\]"
            ):
                Grades(self.api).get_grades(None, None)

    def test_empty_grades_do_not_require_event_metadata(self):
        with patch.object(
            Grades,
            "_Grades__get_grade_data",
            return_value={"vsetkyZnamky": [], "vsetkyUdalosti": None},
        ):
            self.assertEqual(Grades(self.api).get_grades(None, None), [])

    def test_missing_event_collection_has_concrete_error(self):
        from edupage_api.exceptions import FailedToParseGradeDataError

        with patch.object(
            Grades,
            "_Grades__get_grade_data",
            return_value={
                "vsetkyZnamky": [{"udalostid": "10"}],
                "vsetkyUdalosti": None,
            },
        ):
            with self.assertRaisesRegex(
                FailedToParseGradeDataError, "vsetkyUdalosti object"
            ):
                Grades(self.api).get_grades(None, None)


class GradeSkipLoggingTests(unittest.TestCase):
    def test_skip_reasons_and_counts_without_grade_values(self):
        api = Edupage()
        api.is_logged_in = True
        payload = {
            "vsetkyZnamky": [
                {"data": "PRIVATE_VALUE"},
                {"udalostid": "11", "datum": "2026-10-19 13:16:00", "data": "PRIVATE_VALUE"},
                {"udalostid": "12", "datum": "2026-10-19 13:16:00", "data": "PRIVATE_VALUE"},
            ],
            "vsetkyUdalosti": {"edupage": {"11": {}, "12": {"PredmetID": "vsetky"}}},
        }
        with patch.object(Grades, "_Grades__get_grade_data", return_value=payload), self.assertLogs("edupage_api.grades", level="DEBUG") as captured:
            self.assertEqual(Grades(api).get_grades(None, None), [])
        log = " ".join(captured.output)
        for reason in ("keys=['data']", "missing_subject_id", "all_subjects", "received=3 parsed=0 skipped=3"):
            self.assertIn(reason, log)
        self.assertNotIn("PRIVATE_VALUE", log)


class StandaloneGradeTests(unittest.TestCase):
    def test_standalone_and_event_grades_preserve_count_and_identity(self):
        api = Edupage()
        api.is_logged_in = True
        payload = {
            "vsetkyZnamky": [
                {"udalostid": 0, "znamkaid": "42", "predmetid": -5, "datum": "2026-10-19 13:16:00", "data": "A", "p_vaha": "40"},
                {"udalostid": "0", "znamkaid": "43", "predmetid": -5, "datum": "2026-10-20 13:16:00", "data": "(NESPLNĚNO)"},
                {"udalostid": "10", "datum": "2026-10-19 13:16:00", "data": "B"},
            ],
            "vsetkyUdalosti": {"edupage": {"10": {"PredmetID": "-5", "p_typ_udalosti": "4", "p_vaha": "20"}}},
        }
        with patch.object(Grades, "_Grades__get_grade_data", return_value=payload), patch("edupage_api.grades.DbiHelper.fetch_subject_name", return_value="Inf"):
            result = Grades(api).get_grades(None, None)
        self.assertEqual([grade.grade_n for grade in result], ["A", "(NESPLNĚNO)", "B"])
        self.assertEqual(result[0].grade_id, "42")
        self.assertIsNone(result[0].event_id)
        self.assertEqual(result[0].importance, 2)
        self.assertEqual(api.grade_read_report, {"received": 3, "parsed": 3, "skipped": 0, "skip_reasons": {}})


class ObservedStandaloneSchemaTests(unittest.TestCase):
    def test_thirteen_rows_keep_four_zero_event_grades_for_current_and_term(self):
        """Anonymized observed schema: nine event marks + four standalone marks."""
        from edupage_api.grades import Term
        api = Edupage()
        api.is_logged_in = True
        rows = []
        for index in range(13):
            rows.append({
                "provider": "edupage", "znamkaid": 100 + index,
                "studentid": -1, "predmetid": -5,
                "udalostid": 0 if index in (0, 2, 3, 11) else 200 + index,
                "data": "A", "datum": "2026-01-01 08:00:00", "ucitelid": -2,
                "podpisane": None, "podpisane_rodic": None,
            })
        payload = {"vsetkyZnamky": rows, "vsetkyUdalosti": {"edupage": {
            str(row["udalostid"]): {"PredmetID": -5, "p_meno": "Paper", "p_typ_udalosti": "4", "p_vaha": 20}
            for row in rows if row["udalostid"]
        }}}
        for term in (None, Term.FIRST):
            with self.subTest(term=term), patch.object(Grades, "_Grades__get_grade_data", return_value=payload), patch.object(Grades, "_Grades__get_grade_data_for_term", return_value=payload), patch("edupage_api.grades.DbiHelper.fetch_subject_name", return_value="Subject"), patch("edupage_api.grades.DbiHelper.fetch_teacher_data", return_value=None):
                result = Grades(api).get_grades(term, 2026 if term else None)
            self.assertEqual(len(result), 13)
            self.assertEqual(sum(mark.event_id is None for mark in result), 4)
            self.assertEqual(result[11].grade_id, "111")
            self.assertEqual(result[11].importance, 1)
            self.assertEqual(api.grade_read_report["skipped"], 0)


class GradeReportAtomicityTests(unittest.TestCase):
    def test_failed_read_does_not_replace_last_successful_report(self):
        from edupage_api.exceptions import FailedToParseGradeDataError
        api = Edupage()
        api.is_logged_in = True
        previous = {"received": 7, "parsed": 7, "skipped": 0, "skip_reasons": {}}
        api.grade_read_report = previous
        payload = {"vsetkyZnamky": [{"udalostid": 10}], "vsetkyUdalosti": {"edupage": {}}}
        with patch.object(Grades, "_Grades__get_grade_data", return_value=payload), self.assertRaises(FailedToParseGradeDataError):
            Grades(api).get_grades(None, None)
        self.assertIs(api.grade_read_report, previous)
