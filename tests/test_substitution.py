import unittest
from unittest.mock import Mock, patch

from edupage_api import Edupage
from edupage_api.people import UnknownTeacher
from edupage_api.substitution import Substitution


class MissingTeachersTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True

    def get_missing_teachers(self, missing_teachers_string, teachers):
        html = (
            '<div class="header"><span class="print-font-resizable">'
            f"{missing_teachers_string}</span></div>"
        )

        with (
            patch.object(
                Substitution, "_Substitution__get_substitution_data", return_value=html
            ),
            patch(
                "edupage_api.substitution.People.get_teachers", return_value=teachers
            ),
        ):
            return Substitution(self.api).get_missing_teachers(None)

    def test_known_teachers_are_returned(self):
        novak = Mock()
        novak.name = "Ján Novák"
        kovac = Mock()
        kovac.name = "Peter Kováč"

        missing_teachers = self.get_missing_teachers(
            "Chýbajúci učitelia: Ján Novák  (1 - 3), Peter Kováč", [novak, kovac]
        )

        self.assertEqual(missing_teachers, [novak, kovac])

    def test_unknown_teacher_does_not_fail_the_whole_list(self):
        novak = Mock()
        novak.name = "Ján Novák"

        missing_teachers = self.get_missing_teachers(
            "Chýbajúci učitelia: Ján Novák + Juraj Malý", [novak]
        )

        self.assertEqual(missing_teachers, [novak, UnknownTeacher("Juraj Malý")])


if __name__ == "__main__":
    unittest.main()
