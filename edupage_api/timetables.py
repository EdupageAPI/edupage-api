import json
from dataclasses import dataclass
from datetime import datetime, time
from typing import List, Optional

from edupage_api.classes import Class, Classes
from edupage_api.classrooms import Classroom, Classrooms
from edupage_api.exceptions import MissingDataException
from edupage_api.module import EdupageModule, Module, ModuleHelper
from edupage_api.people import EduTeacher, People
from edupage_api.subjects import Subject, Subjects
from edupage_api.utils import RequestUtil


@dataclass
class Lesson:
    period: Optional[int]
    start_time: time
    end_time: time
    subject: Optional[Subject]
    classes: Optional[List[Class]]
    groups: Optional[List[str]]
    teachers: Optional[List[EduTeacher]]
    classrooms: Optional[List[Classroom]]
    online_lesson_link: Optional[str]
    curriculum: Optional[str] = None

    def is_online_lesson(self) -> bool:
        return self.online_lesson_link is not None

    @ModuleHelper.online_lesson
    def sign_into_lesson(self, edupage: EdupageModule):
        request_url = f"https://{edupage.subdomain}.edupage.org/dashboard/eb.php"

        response = edupage.session.get(request_url)

        gse_hash = response.content.decode().split("gsechash=")[1].split('"')[1]

        request_url = f"https://{edupage.subdomain}.edupage.org/dashboard/server/onlinelesson.js?__func=getOnlineLessonOpenUrl"
        today = datetime.today()
        post_data = {
            "__args": [
                None,
                {
                    "click": True,
                    "date": today.strftime("%Y-%m-%d"),
                    "ol_url": self.online_lesson_link,
                    "subjectid": self.subject_id,
                },
            ],
            "__gsh": gse_hash,
        }

        response = edupage.session.post(request_url, json=post_data)
        return json.loads(response.content.decode()).get("reload") is not None


@dataclass
class Timetable:
    lessons: List[Lesson]

    def __iter__(self):
        return iter(self.lessons)

    def get_lesson_at_time(self, time: time):
        for lesson in self.lessons:
            if time >= lesson.start_time and time <= lesson.end_time:
                return lesson

    def get_next_lesson_at_time(self, time: time):
        for lesson in self.lessons:
            if time < lesson.start_time:
                return lesson

    def get_next_online_lesson_at_time(self, time: time):
        for lesson in self.lessons:
            if time < lesson.start_time and lesson.is_online_lesson():
                return lesson

    def get_first_lesson(self):
        if len(self.lessons) > 0:
            return self.lessons[0]

    def get_last_lesson(self):
        if len(self.lessons) > 0:
            return self.lessons[-1]


class Timetables(Module):
    def __get_date_plan(self, date: datetime):
        csrf_request_url = (
            f"https://{self.edupage.subdomain}.edupage.org/dashboard/eb.php?mode=ttday"
        )
        csrf_response = self.edupage.session.get(csrf_request_url)

        gpid = csrf_response.text.split("gpid=")[1].split("&")[0]
        gsh = csrf_response.text.split("gsh=")[1].split('"')[0]

        next_gpid = int(gpid) + 1

        url = f"https://{self.edupage.subdomain}.edupage.org/gcall"
        curriculum_response = self.edupage.session.post(
            url,
            data=RequestUtil.encode_form_data(
                {
                    "gpid": str(next_gpid),
                    "gsh": gsh,
                    "action": "loadData",
                    "user": self.edupage.get_user_id(),
                    "changes": "{}",
                    "date": date.strftime("%Y-%m-%d"),
                    "dateto": date.strftime("%Y-%m-%d"),
                    "_LJSL": "4096",
                }
            ),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        response_start = self.edupage.get_user_id() + '",'
        response_end = ",[]);"

        curriculum_json = curriculum_response.text.split(response_start)[1].split(
            response_end
        )[0]

        data = json.loads(curriculum_json)

        dates = data.get("dates")
        date_plans = dates.get(date.strftime("%Y-%m-%d"))
        if date_plans is None:
            raise MissingDataException()

        return date_plans.get("plan")

    @ModuleHelper.logged_in
    def get_timetable(self, date: datetime) -> Optional[Timetable]:
        plan = self.__get_date_plan(date)

        lessons = []
        for lesson in plan:
            if not lesson.get("header"):
                continue

            period_str = lesson.get("uniperiod")
            period = int(period_str) if period_str.isdigit() else None

            start_time_str = lesson.get("starttime")
            if start_time_str == "24:00":
                start_time_str = "23:59"
            start_time_dt = datetime.strptime(start_time_str, "%H:%M")
            start_time = time(start_time_dt.hour, start_time_dt.minute)

            end_time_str = lesson.get("endtime")
            if end_time_str == "24:00":
                end_time_str = "23:59"
            end_time_dt = datetime.strptime(end_time_str, "%H:%M")
            end_time = time(end_time_dt.hour, end_time_dt.minute)

            subject_id = lesson.get("subjectid")
            subject = (
                Subjects(self.edupage).get_subject(int(subject_id))
                if subject_id.isdigit()
                else None
            )

            class_ids = lesson.get("classids", [])
            classes = [
                Classes(self.edupage).get_class(int(class_id))
                for class_id in class_ids
                if class_id.isdigit()
            ]

            groups = [group for group in lesson.get("groupnames") if group != ""]

            teacher_ids = lesson.get("teacherids", [])
            teachers = [
                People(self.edupage).get_teacher(int(teacher_id))
                for teacher_id in teacher_ids
                if teacher_id.isdigit()
            ]

            classroom_ids = lesson.get("classroomids", [])
            classrooms = [
                Classrooms(self.edupage).get_classroom(int(classroom_id))
                for classroom_id in classroom_ids
                if classroom_id.isdigit()
            ]

            online_lesson_link = lesson.get("ol_url")

            curriculum = lesson.get("flags", {}).get("dp0", {}).get("note_wd", None)

            lesson_object = Lesson(
                period,
                start_time,
                end_time,
                subject,
                classes or None,
                groups or None,
                teachers or None,
                classrooms or None,
                online_lesson_link,
                curriculum,
            )
            lessons.append(lesson_object)

        return Timetable(lessons)
