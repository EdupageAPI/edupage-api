import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from edupage_api.dbi import DbiHelper
from edupage_api.exceptions import MissingDataException
from edupage_api.module import EdupageModule, Module, ModuleHelper
from edupage_api.people import EduTeacher, People


@dataclass
class Lesson:
    teachers: List[EduTeacher]
    classrooms: List[str]
    start_of_lesson: datetime
    end_of_lesson: datetime
    online_lesson_link: Optional[str]
    subject_id: int
    name: str

    def is_online_lesson(self) -> bool:
        return self.online_lesson_link is None

    @ModuleHelper.online_lesson
    def sign_into_lesson(self, edupage: EdupageModule):
        request_url = f"https://{edupage.subdomain}.edupage.org/dashboard/eb.php"

        response = edupage.session.get(request_url)

        gse_hash = response.content.decode() \
                                   .split("gsechash=")[1] \
                                   .split('"')[1]

        request_url = f"https://{edupage.subdomain}.edupage.org/dashboard/server/onlinelesson.js?__func=getOnlineLessonOpenUrl"
        today = datetime.today()
        post_data = {
            "__args": [
                None,
                    {
                        "click": True,
                        "date": today.strftime("%Y-%m-%d"),
                        "ol_url": self.online_lesson_link,
                        "subjectid": self.subject_id
                    }
            ],
            "__gsh": gse_hash
        }

        response = edupage.session.post(request_url, json=post_data)
        return json.loads(response.content.decode()).get("reload") is not None


@dataclass
class Timetable:
    lessons: List[Lesson]

    def __iter__(self):
        return iter(self.lessons)

    def get_lesson_at_time(self, time: datetime):
        # this is done to drop the date part of the datetime
        hour, minute = time.hour, time.minute
        time = datetime(hour=hour, minute=minute)

        for lesson in self.lessons:
            if time >= lesson.start_of_lesson and time <= lesson.end_of_lesson:
                return lesson

    def get_next_lesson_at_time(self, time: datetime):
        # this is done to drop the date part of the datetime
        hour, minute = time.hour, time.minute
        time = datetime(hour=hour, minute=minute)

        for lesson in self.lessons:
            if time < lesson.start_of_lesson:
                return lesson

    def get_next_online_lesson_at_time(self, time: datetime):
        for lesson in self.lessons:
            if time < lesson.start_of_lesson and lesson.is_online_lesson():
                return lesson

    def get_first_lesson(self):
        if len(self.lessons) > 0:
            return self.lessons[0]

    def get_last_lesson(self):
        if len(self.lessons) > 0:
            return self.lessons[-1]


class Timetables(Module):
    def __get_dp(self) -> dict:
        dp = self.edupage.data.get("dp")
        if dp is None:
            raise MissingDataException()

        return dp

    def get_timetable(self, date: datetime) -> Optional[Timetable]:
        dp = self.__get_dp()

        dates = dp.get("dates")
        date_plans = dates.get(date.strftime("%Y-%m-%d"))
        if date_plans is None:
            raise MissingDataException()

        plan = date_plans.get("plan")

        lessons = []
        for subject in plan:
            header = subject.get("header")
            if len(header) == 0:
                continue

            subject_id = int(subject.get("subjectid")) if subject.get("subjectid") else None
            if subject_id:
                subject_name = DbiHelper(self.edupage).fetch_subject_name(subject_id)
            else:
                subject_name = header[0].get("text")

            teachers = []
            teacher_ids = subject.get("teacherids")
            if teacher_ids is not None and len(teacher_ids) != 0:
                for teacher_id_str in teacher_ids:
                    if not teacher_id_str:
                        continue

                    teacher_id = int(teacher_id_str)
                    teacher = People(self.edupage).get_teacher(teacher_id)

                    teachers.append(teacher)

            classrooms = []
            classroom_ids = subject.get("classroomids")
            if classroom_ids is not None and len(classroom_ids) != 0:
                for classroom_id_str in classroom_ids:
                    if not classroom_id_str:
                        continue

                    classroom_id = int(classroom_id_str)
                    classroom_number = DbiHelper(self.edupage).fetch_classroom_number(classroom_id)

                    classrooms.append(classroom_number)

            start_of_lesson_str = subject.get("starttime")
            end_of_lesson_str = subject.get("endtime")

            ModuleHelper.assert_none(start_of_lesson_str, end_of_lesson_str)

            now = datetime.now()

            try:
                start_of_lesson = datetime.strptime(start_of_lesson_str, "%H:%M")
            except ValueError:
                start_of_lesson = datetime(hour=0, minute=0, day=now.day,
                                           month=now.month, year=now.year)

            try:
                end_of_lesson = datetime.strptime(end_of_lesson_str, "%H:%M")
            except ValueError:
                end_of_lesson = datetime(hour=0, minute=0, day=now.day,
                                         month=now.month, year=now.year)

            online_lesson_link = subject.get("ol_url")

            lesson = Lesson(teachers, classrooms, start_of_lesson, end_of_lesson,
                            online_lesson_link, subject_id, subject_name)
            lessons.append(lesson)

        return Timetable(lessons)
