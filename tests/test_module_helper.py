import unittest

from edupage_api.module import ModuleHelper


class ParseIntTests(unittest.TestCase):
    def test_parse_int(self):
        for value, expected in (
            ("4", 4),
            ("4.", 4),
            (13, 13),
            (0, 0),
            ("", None),
            ("abc", None),
            (None, None),
        ):
            with self.subTest(value=value):
                self.assertEqual(ModuleHelper.parse_int(value), expected)


if __name__ == "__main__":
    unittest.main()
