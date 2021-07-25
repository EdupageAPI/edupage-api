
import json
from edupage_api.date import EduDate, EduDateTime, EduTime

class EduMenu:
    def __init__(self, name, allergens, weight, number, rating):
        self.name = name
        self.allergens = allergens
        self.weight = weight
        self.number = number
        self.rating = rating

class EduRating:
    def __init__(self, mysql_date, boarder_id, 
                quality_average, quantity_average, 
                quality_ratings, quantity_ratings): # rating out of 5 points
        self.quantity_average = quantity_average
        self.quality_average = quality_average
        self.quality_ratings = quality_ratings
        self.quantity_ratings = quantity_ratings
        self.__date = mysql_date
        self.__boarder_id = boarder_id
    
    def rate(self, edupage, quantity, quality):
        self.quality = quality
        self.quantity = quantity

        request_url = f"https://{edupage.school}.edupage.org/menu/"

        data = {
            "akcia": "ulozHodnotenia",
            "stravnikid": self.__boarder_id,
            "mysqlDate": self.__date,
            "jedlo_dna": "2",
            "kvalita": str(quality),
            "mnozstvo": str(quantity)
        }

        try:
            response = edupage.session.post(request_url, data=data)
            parsed_response = json.loads(response.content.decode())
            error = parsed_response.get("error")
            if not error is None and error == "":
                return True
            else:
                return False
        except:
            return False

class EduLunch:
    def __init__(self, served_from, served_to, amount_of_foods, 
                 chooseable_menus, can_be_changed_until,
                 title, menus, date, boarder_id):
        self.date = date
        self.served_from = EduTime.from_formatted_string(served_from)
        self.served_to = EduTime.from_formatted_string(served_to)
        self.amount_of_foods = amount_of_foods
        self.chooseable_menus = chooseable_menus
        self.can_be_changed_until = EduDateTime.from_formatted_string(can_be_changed_until) 
        self.title = title
        self.menus = menus
        self.__boarder_id = boarder_id

    def choose(self, edupage, number):
        letters = "ABCDEFGH"
        letter = letters[number - 1]

        request_url = f"https://{edupage.school}.edupage.org/menu/"

        boarder_menu = {
            "stravnikid": self.__boarder_id,
            "mysqlDate": str(self.date),
            "jids": {
                "2": letter
            },
            "view": "pc_listok",
            "pravo": "Student"
        }

        data = {
            "akcia": "ulozJedlaStravnika",
            "jedlaStravnika": json.dumps(boarder_menu)
        }

        response = edupage.session.post(request_url, data = data)
        if json.loads(response.content.decode()).get("error") == "":
            return True
        else:
            return False
    
    def sign_off(self, edupage):
        request_url = f"https://{edupage.school}.edupage.org/menu/"

        boarder_menu = {
            "stravnikid": self.__boarder_id,
            "mysqlDate": str(self.date),
            "jids": {
                "2": "AX"
            },
            "view": "pc_listok",
            "pravo": "Student"
        }

        data = {
            "akcia": "ulozJedlaStravnika",
            "jedlaStravnika": json.dumps(boarder_menu)
        }

        response = edupage.session.post(request_url, data = data)
        if json.loads(response.content.decode()).get("error") == "":
            return True
        else:
            return False