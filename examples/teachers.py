from edupage_api import Edupage
from edupage_api.people import EduTeacher

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

teachers = edupage.get_teachers()


def print_teacher_info(teacher: EduTeacher):
    print(f"{teacher.name} is in your school since {teacher.in_school_since}")


oldest_teacher = None
for teacher in teachers:
    if not teacher.in_school_since:
        continue

    if oldest_teacher is None:
        oldest_teacher = teacher
        continue

    if teacher.in_school_since < oldest_teacher.in_school_since:
        oldest_teacher = teacher

print("The oldest teacher (the longest time in your school):")
print_teacher_info(oldest_teacher)

youngest_teacher = None
for teacher in teachers:
    if not teacher.in_school_since:
        continue

    if youngest_teacher is None:
        youngest_teacher = teacher
        continue

    if teacher.in_school_since > youngest_teacher.in_school_since:
        youngest_teacher = teacher

print("\n\nThe youngest teacher in your school (the shortest time in your school):")
print_teacher_info(youngest_teacher)
