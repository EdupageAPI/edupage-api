import sys

from datetime import datetime
from edupage_api import Edupage

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

today = datetime.now()
meals = edupage.get_meals(today)

if meals is None:
    print(f"No meal choices for today ({today.date()}) yet!")
    sys.exit(0)

for meal_name, meal in [("snack", meals.snack), ("lunch", meals.lunch), ("afternoon snack", meals.afternoon_snack)]:
    if meal is None:
        print(f"No {meal_name + ('es' if meal_name == 'lunch' else 's')} available!")
        continue
    
    chosen_meal_index = (
        "ABCDEFGH".index(meal.ordered_meal) if meal.ordered_meal is not None else None
    )
    
    for menu_index_str in meal.chooseable_menus:
        menu_index = int(menu_index_str)
        is_chosen = chosen_meal_index + 1 == menu_index
        print(f"[{menu_index_str}] {meal.menus[menu_index].name} {'(chosen)' if is_chosen else ''}")
    
    lunch_n = input(f"Which {meal_name} do you want? ")
    while lunch_n not in meal.chooseable_menus and lunch_n != "-1":
        lunch_n = input(f"Which {meal_name} do you want? ")
    
    if lunch_n != "-1":
        meal.choose(edupage, int(lunch_n))
    
    print("Ok!")
