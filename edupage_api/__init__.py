from datetime import datetime
from edupage_api.timeline import TimelineEvents
from edupage_api.lunches import Lunches
from edupage_api.timetables import Timetable, Timetables
from typing import Optional, Union
from edupage_api.messages import Messages
from edupage_api.login import Login
from edupage_api.people import EduAccount, EduStudent, EduTeacher, People
from edupage_api.module import EdupageModule
from functools import wraps
import functools
import requests

class Edupage(EdupageModule):
    def __init__(self, request_timeout = 5):
        self.data = None 
        self.is_logged_in = False
        self.subdomain = None

        self.session = requests.session()
        self.session.request = functools.partial(self.session.request, timeout = request_timeout)

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
    
    def get_lunches(self, date: datetime):
        return Lunches(self).get_lunch(date)
    
    def get_notifications(self):
        return TimelineEvents(self).get_notifications()