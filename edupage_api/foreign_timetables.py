import json
from dataclasses import dataclass
from datetime import date, time
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

    @ModuleHelper.logged_in
    def get_foreign_timetable(
        self,
        target: Union[EduTeacher, EduStudent, Class, Classroom],
        date: date,
    ) -> Optional[List[LessonSkeleton]]:

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

        skeletons = []
        for skeleton in timetable_data:
            period_str = skeleton.get("uniperiod")
            period = int(period_str) if period_str.isdigit() else None

            start_time_str = skeleton.get("starttime").replace("24:00", "23:59")
            start_time = (
                time(*map(int, start_time_str.split(":"))) if start_time_str else None
            )

            end_time_str = skeleton.get("endtime").replace("24:00", "23:59")
            end_time = (
                time(*map(int, end_time_str.split(":"))) if end_time_str else None
            )

            duration = skeleton.get("durationperiods", 1)

            subject_id = skeleton.get("subjectid")
            subject = Subjects(self.edupage).get_subject(subject_id)

            classes = [
                edu_class
                for class_id in skeleton.get("classids", [])
                if (edu_class := Classes(self.edupage).get_class(class_id)) is not None
            ]

            groups = [group for group in skeleton.get("groupnames") if group != ""]

            teachers = [
                teacher
                for teacher_id in skeleton.get("teacherids", [])
                if (teacher := People(self.edupage).get_teacher(teacher_id)) is not None
            ]

            classrooms = [
                classroom
                for classroom_id in skeleton.get("classroomids", [])
                if (classroom := Classrooms(self.edupage).get_classroom(classroom_id))
                is not None
            ]

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
