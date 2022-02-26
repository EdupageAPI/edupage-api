from datetime import date, datetime, time, timedelta

import json
from typing import List
from edupage_api.exceptions import MissingDataException, RequestError
from edupage_api.module import EdupageModule, Module, ModuleHelper
from edupage_api.people import EduTeacher

class LessonSkeleton:
    def __init__(self, weekday: int, start_time: time, end_time: time, 
        subject_id: int, classes: List[int], groups: List[str], 
        classrooms: List[int], duration: int, teachers: List[EduTeacher]):
        self.weekday = weekday
        self.start_time = start_time
        self.end_time = end_time
        self.subject_id = subject_id
        self.classes = classes
        self.groups = groups
        # self.classrooms = classrooms
        self.duration = duration
        self.teachers = teachers

class ForeignTimetables(Module):
    def __get_this_week_weekday(self, date: datetime, n: int) -> datetime:
        current_day = date
        
        if n < current_day.weekday():
            while current_day.weekday() != n:
                current_day = current_day - timedelta(days=1)
        else:
            while current_day.weekday() != n:
                current_day = current_day + timedelta(days=1)
        return current_day
    
    def get_school_year(self):
        dp = self.edupage.data.get("dp")

        if dp is None:
            raise MissingDataException("You have no dp! (try logging in again)")
        
        return dp.get("year")

    def __get_timetable_data(self, id: int, date: datetime):
        this_monday = self.__get_this_week_weekday(datetime.now(), 0)
        this_sunday = self.__get_this_week_weekday(datetime.now(), 6)

        request_data = {"__args":
            [None, 
                {
                    "year": self.get_school_year(),
                    "datefrom": this_monday.strftime("%Y-%m-%d"),
                    "dateto": this_sunday.strftime("%Y-%m-%d"),
                    "table": "teachers",
                    "id": str(id),
                    "showColors": True,
                    "showIgroupsInClasses": True,
                    "showOrig": True,
                    "log_module":"CurrentTTView"
                }] ,"__gsh": self.edupage.gsec_hash
        }
        
        
        request_url = f"https://{self.edupage.subdomain}.edupage.org/" + \
                        "timetable/server/currenttt.js?__func=curentttGetData"
        
        timetable_data = self.edupage.session.post(request_url, json=request_data).content.decode()
        timetable_data = json.loads(timetable_data)

        if timetable_data.get("e") is not None:
            raise RequestError("Edupage returned an error response!")

        if timetable_data.get("r") is None:
            raise MissingDataException("The server returned an incorrect response.")
        
        return timetable_data.get("r").get("ttitems")

    @ModuleHelper.logged_in
    def get_timetable_for_person(self, id: int, date: datetime) -> List[LessonSkeleton]:
        timetable_data = self.__get_timetable_data(id, date)

        all_teachers = self.edupage.get_teachers()
        def teacher_by_id(id: int):
            filtered = list(filter(lambda x: x.person_id == id, all_teachers))
            if len(filtered) == 0:
                raise MissingDataException(f"Teacher with id {id} doesn't exist!")
            
            return filtered[0]

        skeletons = []
        for skeleton in timetable_data:
            date_str = skeleton.get("date")
            date = datetime.strptime(date_str, "%Y-%m-%d")

            start_time_str = skeleton.get("starttime")
            start_time = datetime.strptime(start_time_str, "%H:%M")
            start_time = time(start_time.hour, start_time.minute)

            end_time_str = skeleton.get("starttime")
            end_time = datetime.strptime(end_time_str, "%H:%M")
            end_time = time(end_time.hour, end_time.minute)

            # todo: subject id as subject object
            subject_id_str = skeleton.get("subjectid")
            subject_id = int(subject_id_str) if subject_id_str.isdigit() else None
            
            classes = [int(id) for id in skeleton.get("classids")]
            groups = skeleton.get("groupnames")
            teachers = [teacher_by_id(int(id)) for id in skeleton.get("teacherids")]
            
            # todo: classrooms

            duration = skeleton.get("durationperiods")

            new_skeleton = LessonSkeleton(date.weekday, start_time, end_time, 
                                          subject_id, classes, groups, [], 
                                          duration, teachers)
            skeletons.append(new_skeleton)
        return skeletons