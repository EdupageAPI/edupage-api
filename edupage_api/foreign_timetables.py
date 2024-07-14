import json
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List, Optional, Union

from edupage_api.classes import Class, Classes
from edupage_api.classrooms import Classroom, Classrooms
from edupage_api.exceptions import (
    InsufficientPermissionsException,
    MissingDataException,
    RequestError,
    UnknownServerError,
)
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduStudent, EduTeacher, People
from edupage_api.subjects import Subject, Subjects


@dataclass
class LessonSkeleton:
    period: Optional[int]
    start_time: time
    end_time: time
    duration: int
    subject: Optional[Subject]
    classes: Optional[List[Class]]
    groups: Optional[List[str]]
    teachers: Optional[List[EduTeacher]]
    classrooms: Optional[List[Classroom]]
    is_removed: bool
    is_event: bool


class ForeignTimetables(Module):
    def __get_this_week_weekday(self, date: datetime, n: int) -> datetime:
        return date - timedelta(days=(date.weekday() - n))

    def get_school_year(self):
        dp = self.edupage.data.get("dp")

        if dp is None:
            raise MissingDataException("You have no dp! (try logging in again)")

        return dp.get("year")

    def __get_timetable_data(self, id: int, table: str, date: datetime):
        this_monday = self.__get_this_week_weekday(date, 0)
        this_sunday = self.__get_this_week_weekday(date, 6)

        request_data = {
            "__args": [
                None,
                {
                    "year": self.get_school_year(),
                    "datefrom": this_monday.strftime("%Y-%m-%d"),
                    "dateto": this_sunday.strftime("%Y-%m-%d"),
                    "table": table,
                    "id": str(id),
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

    @ModuleHelper.logged_in
    def get_foreign_timetable(
        self,
        target: Union[EduTeacher, EduStudent, Class, Classroom],
        date: datetime,
    ) -> Optional[List[LessonSkeleton]]:

        lookup = {
            EduTeacher: ("teachers", "person_id"),
            EduStudent: ("students", "person_id"),
            Class: ("classes", "class_id"),
            Classroom: ("classrooms", "classroom_id"),
        }

        table = lookup.get(type(target))[0]
        target_id = getattr(target, lookup.get(type(target))[1])

        try:
            timetable_data = self.__get_timetable_data(target_id, table, date)
        except RequestError as e:
            if "insuficient" in str(e).lower():
                raise InsufficientPermissionsException(f"Missing permissions: {str(e)}")
        except Exception as e:
            raise UnknownServerError(f"There was an unknown error: {str(e)}")

        skeletons = []
        for skeleton in timetable_data:
            date_str = skeleton.get("date")
            lesson_date = datetime.strptime(date_str, "%Y-%m-%d")

            # Skip lessons from other days
            if lesson_date != date:
                continue

            period_str = skeleton.get("uniperiod")
            period = int(period_str) if period_str.isdigit() else None

            start_time_str = skeleton.get("starttime")
            if start_time_str == "24:00":
                start_time_str = "23:59"
            start_time_dt = datetime.strptime(start_time_str, "%H:%M")
            start_time = time(start_time_dt.hour, start_time_dt.minute)

            end_time_str = skeleton.get("endtime")
            if end_time_str == "24:00":
                end_time_str = "23:59"
            end_time_dt = datetime.strptime(end_time_str, "%H:%M")
            end_time = time(end_time_dt.hour, end_time_dt.minute)

            subject = (
                Subjects(self.edupage).get_subject(int(skeleton["subjectid"]))
                if skeleton.get("subjectid", "").isdigit()
                else None
            )

            classes = [
                edu_class
                for class_id in skeleton.get("classids", [])
                if class_id.isdigit()
                for edu_class in [Classes(self.edupage).get_class(int(class_id))]
                if edu_class is not None
            ]

            groups = [group for group in skeleton.get("groupnames") if group != ""]

            teachers = [
                teacher
                for teacher_id in skeleton.get("teacherids", [])
                if teacher_id.isdigit()
                for teacher in [People(self.edupage).get_teacher(int(teacher_id))]
                if teacher is not None
            ]

            classrooms = [
                classroom
                for classroom_id in skeleton.get("classroomids", [])
                if classroom_id.isdigit()
                for classroom in [
                    Classrooms(self.edupage).get_classroom(int(classroom_id))
                ]
                if classroom is not None
            ]

            duration = (
                skeleton.get("durationperiods")
                if skeleton.get("durationperiods") is not None
                else 1
            )

            is_removed = skeleton.get("removed") or skeleton.get("type") == "absent"
            is_event = (
                skeleton.get("type") == "event"
                or skeleton.get("type") == "out"
                or skeleton.get("main")
            ) or False

            new_skeleton = LessonSkeleton(
                period,
                start_time,
                end_time,
                duration,
                subject,
                classes or None,
                groups or None,
                teachers or None,
                classrooms or None,
                is_removed,
                is_event,
            )
            skeletons.append(new_skeleton)
        return skeletons
