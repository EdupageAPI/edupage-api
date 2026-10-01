import json
import unittest
from datetime import date
from unittest.mock import Mock

from edupage_api import Edupage


class MealsParsingTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True
        self.api.subdomain = "example"
        self.api.session = Mock()

    def get_meals(self, edupage_data):
        page = (
            "<script>\r\n"
            f"\t\t\tedupageData: {json.dumps(edupage_data)},\r\n"
            "</script>"
        )
        self.api.session.get.return_value.content = page.encode()
        return self.api.get_meals(date(2024, 11, 26))

    def test_empty_edupage_data_returns_none(self):
        self.assertIsNone(self.get_meals([]))

    def test_lunch_is_parsed(self):
        meals = self.get_meals(
            {
                "example": {
                    "novyListok": {
                        "addInfo": {"stravnikid": "123"},
                        "2024-11-26": {
                            "2": {
                                "nazov": "Obed",
                                "druhov_jedal": 2,
                                "choosableMenus": {"A": "Menu A", "B": "Menu B"},
                                "zmen_do": "2024-11-25 14:00:00",
                                "evidencia": {"stav": "V", "obj": "A"},
                                "rows": [{"nazov": "Polievka"}],
                            }
                        },
                    }
                }
            }
        )

        self.assertIsNone(meals.snack)
        self.assertEqual(meals.lunch.ordered_meal, "A")
        self.assertEqual(meals.lunch.chooseable_menus, ["A", "B"])
        self.assertEqual(meals.lunch.menus[0].name, "Polievka")


if __name__ == "__main__":
    unittest.main()
