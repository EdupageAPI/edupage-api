import datetime

from edupage_api import Edupage

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

# My timetable
date = datetime.date(2024, 6, 12)
timetable = edupage.get_my_timetable(date)

print(f"My timetable from {date}:")

for lesson in timetable:
    print(f"[{lesson.period}] {lesson.subject.name} ({lesson.teachers[0].name})")

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
    print(f"[{lesson.period}] {lesson.subject.name} ({lesson.teachers[0].name})")
