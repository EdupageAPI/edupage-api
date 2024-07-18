import json
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import List, Optional, Union

from edupage_api.classes import Class, Classes
from edupage_api.classrooms import Classroom, Classrooms
from edupage_api.exceptions import (
    InsufficientPermissionsException,
    MissingDataException,
    RequestError,
    UnknownServerError,
)
from edupage_api.module import EdupageModule, Module, ModuleHelper
from edupage_api.people import EduStudent, EduTeacher, People
from edupage_api.subjects import Subject, Subjects
from edupage_api.utils import RequestUtil


@dataclass
class Lesson:
    period: Optional[int]
    start_time: time
    end_time: time
    duration: int
    subject: Optional[Subject]
    classes: Optional[List[Class]]
    groups: Optional[List[str]]
    teachers: Optional[List[EduTeacher]]
    classrooms: Optional[List[Classroom]]
    curriculum: Optional[str]
    online_lesson_link: Optional[str]
    is_cancelled: bool
    is_event: bool

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
    def get_school_year(self):
        dp = self.edupage.data.get("dp")

        if dp is None:
            raise MissingDataException("You have no dp! (try logging in again)")

        return dp.get("year")

    def __get_timetable_data(self, target_id: int, table: str, date: date):
        request_data = {
            "__args": [
                None,
                {
                    "year": self.get_school_year(),
                    "datefrom": date.strftime("%Y-%m-%d"),
                    "dateto": date.strftime("%Y-%m-%d"),
                    "table": table,
                    "id": str(target_id),
                    "showColors": True,
                    "showIgroupsInClasses": True,
                    "showOrig": True,
                    "log_module": "CurrentTTView",
                },
            ],
            "__gsh": self.edupage.gsec_hash,
        }

        request_url = (
            f"https://{self.edupage.subdomain}.edupage.org/"
            "timetable/server/currenttt.js?__func=curentttGetData"
        )

        timetable_data = self.edupage.session.post(
            request_url, json=request_data
        ).content.decode()
        timetable_data = json.loads(timetable_data)

        timetable_data_response = timetable_data.get("r")
        timetable_data_error = timetable_data_response.get("error")

        if timetable_data_response is None:
            raise MissingDataException("The server returned an incorrect response.")

        if timetable_data_error is not None:
            raise RequestError(
                f"Edupage returned an error response: {timetable_data_error}"
            )

        return timetable_data_response.get("ttitems")

    def __get_date_plan(self, date: date):
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
        response_end = ",["

        curriculum_json = curriculum_response.text.split(response_start)[1].rsplit(
            response_end, 1
        )[0]

        data = json.loads(curriculum_json)

        dates = data.get("dates")
        date_plans = dates.get(date.strftime("%Y-%m-%d"))
        if date_plans is None:
            raise MissingDataException()

        return date_plans.get("plan")

    def __parse_timetable(self, plan):
        lessons = []
        for lesson in plan:
            if "header" in lesson and (
                not lesson.get("header")
                or lesson.get("header")[0].get("cmd") == "addlesson_t"
            ):
                continue

            period_str = lesson.get("uniperiod")
            period = int(period_str) if period_str.isdigit() else None

            start_time_str = lesson.get("starttime").replace("24:00", "23:59")
            start_time = (
                time(*map(int, start_time_str.split(":"))) if start_time_str else None
            )

            end_time_str = lesson.get("endtime").replace("24:00", "23:59")
            end_time = (
                time(*map(int, end_time_str.split(":"))) if end_time_str else None
            )

            duration = lesson.get("durationperiods", 1)

            subject_id = lesson.get("subjectid")
            subject = Subjects(self.edupage).get_subject(subject_id)

            classes = [
                edu_class
                for class_id in lesson.get("classids", [])
                if (edu_class := Classes(self.edupage).get_class(class_id)) is not None
            ]

            groups = [group for group in lesson.get("groupnames") if group != ""]

            teachers = [
                teacher
                for teacher_id in lesson.get("teacherids", [])
                if (teacher := People(self.edupage).get_teacher(teacher_id)) is not None
            ]

            classrooms = [
                classroom
                for classroom_id in lesson.get("classroomids", [])
                if (classroom := Classrooms(self.edupage).get_classroom(classroom_id))
                is not None
            ]

            is_cancelled = (
                lesson.get("removed")
                or lesson.get("type") == "absent"
                or lesson.get("type") == ""
            )
            is_event = (
                lesson.get("type") == "event"
                or lesson.get("type") == "out"
                or lesson.get("main")
            ) or False

            online_lesson_link = lesson.get("ol_url")

            try:
                curriculum = lesson.get("flags", {}).get("dp0", {}).get(
                    "note_wd"
                ) or lesson.get("flags", {}).get("event", {}).get("name")
            except AttributeError:
                curriculum = None

            lesson_object = Lesson(
                period,
                start_time,
                end_time,
                duration,
                subject,
                classes or None,
                groups or None,
                teachers or None,
                classrooms or None,
                curriculum or None,
                online_lesson_link,
                is_cancelled,
                is_event,
            )
            lessons.append(lesson_object)

        return Timetable(lessons)

    @ModuleHelper.logged_in
    def get_my_timetable(self, date: date) -> Optional[Timetable]:
        plan = self.__get_date_plan(date)
        return self.__parse_timetable(plan)

    @ModuleHelper.logged_in
    def get_timetable(
        self,
        target: Union[EduTeacher, EduStudent, Class, Classroom],
        date: date,
    ) -> Optional[Timetable]:

        lookup = {
            EduTeacher: ("teachers", "person_id"),
            EduStudent: ("students", "person_id"),
            Class: ("classes", "class_id"),
            Classroom: ("classrooms", "classroom_id"),
        }

        table, target_id_attr = lookup.get(type(target))
        target_id = getattr(target, target_id_attr)

        try:
            timetable_data = self.__get_timetable_data(target_id, table, date)
        except RequestError as e:
            if "insuficient" in str(e).lower():
                raise InsufficientPermissionsException(f"Missing permissions: {str(e)}")
        except Exception as e:
            raise UnknownServerError(f"There was an unknown error: {str(e)}")

        return self.__parse_timetable(timetable_data)
