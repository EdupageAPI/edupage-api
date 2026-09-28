import unittest
from datetime import time
from unittest.mock import patch

from edupage_api import Edupage
from edupage_api.subjects import Subject, Subjects
from edupage_api.timetables import Timetables


class TimetableEventNameTests(unittest.TestCase):
    def parse(self, **fields):
        plan = {
            "type": "event",
            "uniperiod": "",
            "starttime": "00:00",
            "endtime": "24:00",
            "groupnames": [],
            **fields,
        }
        timetable = Timetables(Edupage())._Timetables__parse_timetable([plan])
        self.assertEqual(len(timetable.lessons), 1)
        return timetable.lessons[0]

    def test_preserves_top_level_event_name_without_flags(self):
        lesson = self.parse(name="Svátek: Den české státnosti")
        self.assertEqual(lesson.curriculum, "Svátek: Den české státnosti")
        self.assertTrue(lesson.is_event)
        self.assertIsNone(lesson.subject)
        self.assertEqual(lesson.start_time, time(0, 0))
        self.assertEqual(lesson.end_time, time(23, 59))

    def test_fallback_handles_empty_or_non_object_flags(self):
        for flags in ({}, None, [], {"event": None}, {"dp0": None}):
            with self.subTest(flags=flags):
                self.assertEqual(
                    self.parse(name="School trip", flags=flags).curriculum,
                    "School trip",
                )

    def test_existing_curriculum_and_nested_event_name_keep_precedence(self):
        for flags, expected in (
            ({"event": {"name": "Nested title"}}, "Nested title"),
            (
                {"dp0": {"note_wd": "Curriculum"}, "event": {"name": "Nested title"}},
                "Curriculum",
            ),
        ):
            with self.subTest(flags=flags):
                self.assertEqual(
                    self.parse(name="Fallback title", flags=flags).curriculum,
                    expected,
                )

    def test_fallback_only_applies_to_events_without_subjects(self):
        self.assertIsNone(self.parse(type="lesson", name="Lesson label").curriculum)
        subject = Subject(1, "Mathematics", "Math")
        with patch.object(Subjects, "get_subject", return_value=subject):
            lesson = self.parse(subjectid="1", name="Event label")
        self.assertIs(lesson.subject, subject)
        self.assertIsNone(lesson.curriculum)

    def test_uses_existing_event_classification(self):
        for fields in ({"type": "out"}, {"type": "lesson", "main": True}):
            with self.subTest(fields=fields):
                self.assertEqual(
                    self.parse(name="School event", **fields).curriculum,
                    "School event",
                )

    def test_missing_blank_or_non_string_names_are_not_curriculum(self):
        self.assertIsNone(self.parse().curriculum)
        for name in (None, "", "   ", 42, [], {}):
            with self.subTest(name=name):
                self.assertIsNone(self.parse(name=name).curriculum)


if __name__ == "__main__":
    unittest.main()
