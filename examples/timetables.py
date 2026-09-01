import datetime

from edupage_api import Edupage

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

# My timetable
# Leave as None to keep the original get_my_timetable() behavior.
# Set a full student name to explicitly switch to a specific child.
student_name = None
# student_name = "Alžbeta Výborná"

if student_name is not None:
    students = edupage.get_students() or []

    student = next(
        (student for student in students if student.name == student_name),
        None,
    )

    if student is None:
        available_students = [student.name for student in students]
        raise RuntimeError(
            f"Student {student_name!r} was not found. "
            f"Available students: {available_students}"
        )

    edupage.switch_to_child(student)

date = datetime.date(2024, 6, 12)
timetable = edupage.get_my_timetable(date)

print(f"My timetable from {date}:")

for lesson in timetable:
    teacher_name = lesson.teachers[0].name if lesson.teachers else "?"
    print(f"[{lesson.period}] {lesson.subject.name} ({teacher_name})")

print()


# Someone else's timetable
classrooms = edupage.get_classrooms()

# for i, classroom in enumerate(classrooms):
#     print(i, classroom.name)

classroom = classrooms[0]
date = datetime.date(2024, 6, 12)
timetable = edupage.get_timetable(classroom, date)
print(f"Timetable from {date} for classroom '{classroom.name}':")

for lesson in timetable:
    teacher_name = lesson.teachers[0].name if lesson.teachers else "?"
    print(f"[{lesson.period}] {lesson.subject.name} ({teacher_name})")
