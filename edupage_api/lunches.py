import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional
from enum import Enum

from edupage_api.exceptions import (
    FailedToChangeMealError,
    FailedToRateException,
    InvalidMealsData,
    NotLoggedInException,
)
from edupage_api.module import EdupageModule, Module, ModuleHelper


@dataclass
class Rating:
    __date: str
    __boarder_id: str

    quality_average: float
    quality_ratings: float

    quantity_average: float
    quantity_ratings: float

    def rate(self, edupage: EdupageModule, quantity: int, quality: int):
        if not edupage.is_logged_in:
            raise NotLoggedInException()

        request_url = f"https://{edupage.subdomain}.edupage.org/menu/"

        data = {
            "akcia": "ulozHodnotenia",
            "stravnikid": self.__boarder_id,
            "mysqlDate": self.__date,
            "jedlo_dna": "2",
            "kvalita": str(quality),
            "mnozstvo": str(quantity),
        }

        response = edupage.session.post(request_url, data=data)
        parsed_response = json.loads(response.content.decode())

        error = parsed_response.get("error")
        if error is None or error != "":
            raise FailedToRateException()


@dataclass
class Menu:
    name: str
    allergens: str
    weight: str
    number: str
    rating: Optional[Rating]

class MealType(Enum):
    SNACK = 1
    LUNCH = 2
    AFTERNOON_SNACK = 3

@dataclass
class Meal:
    served_from: Optional[datetime]
    served_to: Optional[datetime]
    amount_of_foods: int
    chooseable_menus: list[str]
    can_be_changed_until: datetime
    title: str
    menus: List[Menu]
    date: datetime
    ordered_meal: Optional[str]
    meal_type: MealType
    __boarder_id: str
    __meal_index: str

    def __iter__(self):
        return iter(self.menus)

    def __make_choice(self, edupage: EdupageModule, choice_str: str):
        request_url = f"https://{edupage.subdomain}.edupage.org/menu/"

        boarder_menu = {
            "stravnikid": self.__boarder_id,
            "mysqlDate": self.date.strftime("%Y-%m-%d"),
            "jids": {self.__meal_index: choice_str},
            "view": "pc_listok",
            "pravo": "Student",
        }

        data = {
            "akcia": "ulozJedlaStravnika",
            "jedlaStravnika": json.dumps(boarder_menu),
        }

        response = edupage.session.post(
            request_url, data=data
        ).content.decode()

        if json.loads(response).get("error") != "":
            raise FailedToChangeMealError()

    def choose(self, edupage: EdupageModule, number: int):
        letters = "ABCDEFGH"
        letter = letters[number - 1]

        self.__make_choice(edupage, letter)
        self.ordered_meal = letter

    def sign_off(self, edupage: EdupageModule):
        self.__make_choice(edupage, "AX")
        self.ordered_meal = None

@dataclass
class Meals:
    snack: Optional[Meal]
    lunch: Optional[Meal]
    afternoon_snack: Optional[Meal]
    


class Lunches(Module):
    def parse_meal(self, meal_index: str, meal: dict, boarder_id: str, date: date) -> Optional[Meal]:
        if meal is None:
            return None
        
        if meal.get("isCooking") == False:
            return None

        ordered_meal = None
        meal_record = meal.get("evidencia")

        if meal_record is not None:
            ordered_meal = meal_record.get("stav")

            if ordered_meal == "V":
                ordered_meal = meal_record.get("obj")

        served_from_str = meal.get("vydaj_od")
        served_to_str = meal.get("vydaj_do")

        if served_from_str:
            served_from = datetime.strptime(served_from_str, "%H:%M")
        else:
            served_from = None

        if served_to_str:
            served_to = datetime.strptime(served_to_str, "%H:%M")
        else:
            served_to = None

        title = meal.get("nazov")

        amount_of_foods = meal.get("druhov_jedal")
        chooseable_menus = list(meal.get("choosableMenus").keys())

        can_be_changed_until = meal.get("zmen_do")

        menus = []

        for food in meal.get("rows"):
            if not food:
                continue

            name = food.get("nazov")
            allergens = food.get("alergenyStr")
            weight = food.get("hmotnostiStr")
            number = food.get("menusStr")
            rating = None

            if number is not None:
                number = number.replace(": ", "")
                rating = meal.get("hodnotenia")
                if rating is not None and rating:
                    rating = rating.get(number)

                    [quality, quantity] = rating

                    quality_average = quality.get("priemer")
                    quality_ratings = quality.get("pocet")

                    quantity_average = quantity.get("priemer")
                    quantity_ratings = quantity.get("pocet")

                    rating = Rating(
                        date.strftime("%Y-%m-%d"),
                        boarder_id,
                        quality_average,
                        quantity_average,
                        quality_ratings,
                        quantity_ratings,
                    )
                else:
                    rating = None
            menus.append(Menu(name, allergens, weight, number, rating))
        
        return Meal(
            served_from,
            served_to,
            amount_of_foods,
            chooseable_menus,
            can_be_changed_until,
            title,
            menus,
            date,
            ordered_meal,
            MealType(int(meal_index)),
            boarder_id,
            meal_index
        )

    @ModuleHelper.logged_in
    def get_meals(self, date: date) -> Optional[Meals]:
        date_strftime = date.strftime("%Y%m%d")
        request_url = f"https://{self.edupage.subdomain}.edupage.org/menu/?date={date_strftime}"
        response = self.edupage.session.get(request_url).content.decode()

        lunch_data = json.loads(
            response.split("edupageData: ")[1].split(",\r\n")[0]
        )
        lunches_data = lunch_data.get(self.edupage.subdomain)
        try:
            boarder_id = (
                lunches_data.get("novyListok").get("addInfo").get("stravnikid")
            )
        except AttributeError as e:
            raise InvalidMealsData(f"Missing boarder id: {e}")

        meals = lunches_data.get("novyListok").get(date.strftime("%Y-%m-%d"))
        if meals is None:
            return None
        
        snack = self.parse_meal("1", meals.get("1"), boarder_id, date)
        lunch = self.parse_meal("2", meals.get("2"), boarder_id, date)
        afternoon_snack = self.parse_meal("3", meals.get("3"), boarder_id, date)
        
        return Meals(snack, lunch, afternoon_snack)
        
        