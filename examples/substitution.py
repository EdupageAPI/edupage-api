from datetime import datetime

from edupage_api import Edupage

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

tomorrow = datetime.now()
missing_teachers = edupage.get_missing_teachers(tomorrow)

print(f"There are {len(missing_teachers)} missing tomorrow!")

print()

print("Teachers missing:", end=" ")
for i, teacher in enumerate(missing_teachers):
    if i != 0:
        print(", ", end="")
    
    print(f"{teacher.name}", end="")