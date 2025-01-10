from edupage_api import Edupage
from datetime import datetime

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

meals = edupage.get_meals(datetime.today().date())

lunch = meals.lunch
print(lunch.menus)

snack = meals.snack
print(snack.menus)

# i don't want a snack for today!
snack.sign_off(edupage) 