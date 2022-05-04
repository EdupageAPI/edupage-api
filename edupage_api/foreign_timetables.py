import json
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List, Optional

from edupage_api.dbi import DbiHelper
from edupage_api.exceptions import MissingDataException, RequestError
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
                    "log_module": "CurrentTTView"
                }
            ],
            "__gsh": self.edupage.gsec_hash
        }

        request_url = (f"https://{self.edupage.subdomain}.edupage.org/"
                       "timetable/server/currenttt.js?__func=curentttGetData")

        timetable_data = self.edupage.session.post(request_url, json=request_data).content.decode()
        timetable_data = json.loads(timetable_data)

        timetable_data_response = timetable_data.get("r")
        timetable_data_error = timetable_data_response.get("error")

        if timetable_data_response is None:
            raise MissingDataException("The server returned an incorrect response.")

        if timetable_data_error is not None:
            raise RequestError(f"Edupage returned an error response: {timetable_data_error}")

        return timetable_data_response.get("ttitems")

    @ModuleHelper.logged_in
    def get_timetable_for_person(self, id: int, date: datetime) -> List[LessonSkeleton]:
        all_teachers = People(self.edupage).get_teachers()
        students = People(self.edupage).get_students()

        def teacher_by_id(id: int):
            filtered = list(filter(lambda x: x.person_id == id, all_teachers))
            if not filtered:
                raise MissingDataException(f"Teacher with id {id} doesn't exist!")

            return filtered[0]

        def student_by_id(id: int):
            filtered = list(filter(lambda x: x.person_id == id, students))
            if not filtered:
                raise MissingDataException(f"Student with id {id} doesn't exist!")

            return filtered[0]

        def classroom_by_id(id: int):
            return DbiHelper(self.edupage).fetch_classroom_number(id)

        table = None
        try:
            teacher_by_id(id)
            table = "teachers"
        except:
            try:
                student_by_id(id)
                table = "students"
            except:
                if classroom_by_id(id):
                    table = "classrooms"

        if not table:
            raise MissingDataException(f"Teacher, student or class with id {id} doesn't exist!")

        timetable_data = self.__get_timetable_data(id, table, date)

        skeletons = []
        for skeleton in timetable_data:
            date_str = skeleton.get("date")
            date = datetime.strptime(date_str, "%Y-%m-%d")

            start_time_str = skeleton.get("starttime")
            start_time_dt = datetime.strptime(start_time_str, "%H:%M")
            start_time = time(start_time_dt.hour, start_time_dt.minute)

            end_time_str = skeleton.get("endtime")
            end_time_dt = datetime.strptime(end_time_str, "%H:%M")
            end_time = time(end_time_dt.hour, end_time_dt.minute)

            subject_id_str = skeleton.get("subjectid")
            subject_id = int(subject_id_str) if subject_id_str.isdigit() else None

            subject_name = None
            if subject_id is not None:
                subject_name = DbiHelper(self.edupage).fetch_subject_name(subject_id)

            classes = [int(id) for id in skeleton.get("classids")]
            groups = skeleton.get("groupnames")
            teachers = [teacher_by_id(int(id)) for id in skeleton.get("teacherids")]
            classrooms = [classroom_by_id(int(id)) for id in skeleton.get("classroomids")]

            duration = (skeleton.get("durationperiods")
                        if skeleton.get("durationperiods") is not None else 1)

            new_skeleton = LessonSkeleton(date.weekday(), start_time, end_time,
                                          subject_id, subject_name, classes, groups, classrooms,
                                          duration, teachers)
            skeletons.append(new_skeleton)
        return skeletons
