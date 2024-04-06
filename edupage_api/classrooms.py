import json
from edupage_api.dbi import DbiHelper
from dataclasses import dataclass
from typing import Optional
from edupage_api.module import Module, ModuleHelper
from datetime import datetime, date, time, timedelta

@dataclass
class EduClassroom:
    classroom_id: int
    name: str
    short: str

    def __init__(self, classroom_id, name, short):
        self.classroom_id = classroom_id
        self.name = name
        self.short = short

class Classrooms(Module):
    @ModuleHelper.logged_in
    def get_classrooms(self) -> Optional[list]:
        classroom_list = DbiHelper(self.edupage).fetch_classroom_list()

        if classroom_list is None:
            return None

        classrooms = []

        for classroom_id_str in classroom_list:
            if not classroom_id_str:
                continue

            classrooms.append(EduClassroom(int(classroom_id_str),
                classroom_list[classroom_id_str]["name"],
                classroom_list[classroom_id_str]["short"]))

        return classrooms

    @ModuleHelper.logged_in
    def get_free_classrooms(self, datetime: datetime) -> Optional[list]:
        classrooms = self.get_classrooms()
        free_classrooms = []
        for classroom in classrooms:
            timetable = self.edupage.get_classroom_timetable(
                str(classroom.classroom_id), datetime
            )

            today_lessons = []

            for lesson in timetable:
                if lesson.weekday is datetime.weekday():
                    today_lessons.append(lesson)

            free = True

            print(lesson.start_time)
            print(lesson.end_time)
            print(datetime)

            for lesson in today_lessons:
                if lesson.start_time <= datetime.time() and \
                    lesson.end_time >= datetime.time():
                    free = False

            if free:
                free_classrooms.append(classroom)

        return free_classrooms
