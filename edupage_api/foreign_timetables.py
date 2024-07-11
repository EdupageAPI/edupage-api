import json
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List, Optional

from edupage_api.classes import Classes
from edupage_api.classrooms import Classrooms
from edupage_api.dbi import DbiHelper
from edupage_api.exceptions import (
    InsufficientPermissionsException,
    MissingDataException,
    RequestError,
    UnknownServerError,
)
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduTeacher, People


@dataclass
class LessonSkeleton:
    weekday: int
    start_time: time
    end_time: time
    subject_id: Optional[int]
    subject_name: Optional[str]
    classes: List[int]
    groups: List[str]
    classrooms: List[str]
    duration: int
    teachers: List[EduTeacher]


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
    def get_timetable_for_person(
        self, target_id: int, date: datetime
    ) -> List[LessonSkeleton]:
        all_teachers = People(self.edupage).get_teachers()
        students = People(self.edupage).get_students()

        def teacher_by_id(target_id: int):
            filtered = list(filter(lambda x: x.person_id == target_id, all_teachers))
            if not filtered:
                raise MissingDataException(
                    f"Teacher with id {target_id} doesn't exist!"
                )

            return filtered[0]

        def student_by_id(target_id: int):
            filtered = list(filter(lambda x: x.person_id == target_id, students))
            if not filtered:
                raise MissingDataException(
                    f"Student with id {target_id} doesn't exist!"
                )

            return filtered[0]

        def classroom_by_id(target_id: int):
            if not Classrooms(self.edupage).get_classroom(target_id):
                raise MissingDataException(
                    f"Classroom with id {target_id} doesn't exist!"
                )

        def class_by_id(target_id: int):
            if not Classes(self.edupage).get_class(target_id):
                raise MissingDataException(
                    f"Classroom with id {target_id} doesn't exist!"
                )

        def find_table_by_id(target_id):
            lookup_functions = [
                (teacher_by_id, "teachers"),
                (student_by_id, "students"),
                (classroom_by_id, "classrooms"),
                (class_by_id, "classes"),
            ]

            for func, table_name in lookup_functions:
                try:
                    func(target_id)
                    return table_name
                except:
                    continue

            raise MissingDataException(
                f"Teacher, student, classroom, or class with id {target_id} doesn't exist!"
            )

        table = find_table_by_id(target_id)

        try:
            timetable_data = self.__get_timetable_data(target_id, table, date)
        except RequestError as e:
            if "insuficient" in str(e).lower():
                raise InsufficientPermissionsException(f"Missing permissions: {str(e)}")
        except Exception as e:
            raise UnknownServerError(f"There was an unknown error: {str(e)}")

        skeletons = []
        for skeleton in timetable_data:
            if (
                skeleton.get("removed")
                or skeleton.get("main")
                or skeleton.get("type") == "absent"
            ):
                continue

            date_str = skeleton.get("date")
            date = datetime.strptime(date_str, "%Y-%m-%d")

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

            subject_id_str = skeleton.get("subjectid")
            subject_id = int(subject_id_str) if subject_id_str.isdigit() else None

            subject_name = None
            if subject_id is not None:
                subject_name = DbiHelper(self.edupage).fetch_subject_name(subject_id)

            classes = [int(id) for id in skeleton.get("classids")]
            groups = skeleton.get("groupnames")

            try:
                teachers = [teacher_by_id(int(id)) for id in skeleton.get("teacherids")]
            except:
                teachers = []

            classrooms = [classroom_by_id(id) for id in skeleton.get("classroomids")]

            duration = (
                skeleton.get("durationperiods")
                if skeleton.get("durationperiods") is not None
                else 1
            )

            new_skeleton = LessonSkeleton(
                date.weekday(),
                start_time,
                end_time,
                subject_id,
                subject_name,
                classes,
                groups,
                classrooms,
                duration,
                teachers,
            )
            skeletons.append(new_skeleton)
        return skeletons
