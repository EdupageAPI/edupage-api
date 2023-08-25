from edupage_api import Edupage
from edupage_api.people import EduTeacher

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

teachers = edupage.get_teachers()

for i, teacher in enumerate(teachers):
    print(f"{i + 1}. {teacher.name}")