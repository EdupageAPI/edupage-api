import unittest

from edupage_api import Edupage


class StudentParseTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True

    def get_student(self, number_in_class):
        self.api.data = {
            "dbi": {
                "students": {
                    "1": {
                        "firstname": "Example",
                        "lastname": "Student",
                        "gender": "M",
                        "classid": "7",
                        "datefrom": "2026-09-01",
                        "numberinclass": number_in_class,
                    }
                }
            }
        }

        return self.api.get_students()[0]

    def test_string_number_in_class(self):
        self.assertEqual(self.get_student("12").number_in_class, 12)

    def test_numeric_number_in_class(self):
        self.assertEqual(self.get_student(12).number_in_class, 12)


if __name__ == "__main__":
    unittest.main()
