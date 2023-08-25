from edupage_api import Edupage
from edupage_api.people import EduTeacher

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

teachers = edupage.get_teachers()

def print_teacher_name(teacher: EduTeacher):
    print(f"{teacher.name}")

for teacher in teachers:
    print_teacher_name(teacher)