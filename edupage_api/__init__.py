import functools
from datetime import datetime
from io import TextIOWrapper
from typing import Optional

import requests
from requests import Response

from edupage_api.cloud import Cloud, EduCloudFile
from edupage_api.custom_request import CustomRequest
from edupage_api.grades import EduGrade, Grades
from edupage_api.login import Login
from edupage_api.lunches import Lunch, Lunches
from edupage_api.messages import Messages
from edupage_api.module import EdupageModule
from edupage_api.people import EduAccount, EduStudent, EduTeacher, People
from edupage_api.timeline import TimelineEvent, TimelineEvents
from edupage_api.timetables import Timetable, Timetables


class Edupage(EdupageModule):
    def __init__(self, request_timeout=5):
        self.data = None
        self.is_logged_in = False
        self.subdomain = None

        self.session = requests.session()
        self.session.request = functools.partial(self.session.request, timeout=request_timeout)

    def login(self, username: str, password: str, subdomain: str):
        Login(self).login(username, password, subdomain)

    def login_auto(self, username: str, password: str):
        Login(self).login_auto(username, password)

    def get_students(self) -> Optional[list[EduStudent]]:
        return People(self).get_students()

    def get_teachers(self) -> Optional[list[EduTeacher]]:
        return People(self).get_teachers()

    def send_message(self, recipients: Optional[list[EduAccount]], body: str):
        Messages(self).send_message(recipients, body)

    def get_timetable(self, date: datetime) -> Optional[Timetable]:
        return Timetables(self).get_timetable(date)

    def get_lunches(self, date: datetime) -> Optional[Lunch]:
        return Lunches(self).get_lunch(date)

    def get_notifications(self) -> list[TimelineEvent]:
        return TimelineEvents(self).get_notifications()

    def cloud_upload(self, fd: TextIOWrapper) -> EduCloudFile:
        return Cloud(self).upload_file(fd)

    def get_grades(self) -> list[EduGrade]:
        return Grades(self).get_grades()

    def get_user_id(self) -> str:
        return self.data.get("userid")

    # method -> "GET" or "POST"
    def custom_request(self, url: str, method: str, data: str = "", headers: dict = {}) -> Response:
        return CustomRequest(self).custom_request(url, method, data, headers)
