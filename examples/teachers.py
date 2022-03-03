from edupage_api import Edupage
from edupage_api.people import EduTeacher

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

teachers = edupage.get_teachers()

def print_teacher_info(teacher: EduTeacher):
    print(f"{teacher.name} is in your school since {teacher.in_school_since}")

oldest_teacher = teachers[0]
for teacher in teachers:
    if not teacher.in_school_since:
        continue


    if teacher.in_school_since < oldest_teacher.in_school_since:
        oldest_teacher = teacher

print("The oldest teacher (the longest time in your school):")
print_teacher_info(oldest_teacher)

yonguest_teacher = teachers[0]
for teacher in teachers:
    if not teacher.in_school_since:
        continue

    if teacher.in_school_since > yonguest_teacher.in_school_since:
        yonguest_teacher = teacher

print("\n\nThe yonguest teacher in your school (the shortest time in your school):")
print_teacher_info(yonguest_teacher)