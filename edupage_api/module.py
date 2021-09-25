from datetime import datetime

import requests
from functools import wraps
from typing import Union
from edupage_api.exceptions import MissingDataException, NotAnOnlineLessonError, NotLoggedInException
import urllib.parse

class EdupageModule:
    subdomain: str
    session: requests.Session
    data: dict
    is_logged_in: bool

class Module:
    def __init__(self, edupage: EdupageModule):
        self.edupage = edupage
    
class ModuleHelper:
    # Helper Functions

    @staticmethod
    def int_or_none(val: str) -> Union[int, None]:
        if val.isdigit():
            return int(val)

    """
    If any argument of this function is none, it throws MissingDataException
    """
    @staticmethod
    def assert_none(*args):
        if None in args:
            raise MissingDataException()

    
    @staticmethod
    def urlencode(string: str) -> str:
        return urllib.parse.quote(string)

    @staticmethod
    def encode_form_data(data: dict) -> str:
        output = ""
        for i, key in enumerate(data.keys(), start=0):
            value = data[key]
            entry = f"{ModuleHelper.urlencode(key)}={ModuleHelper.urlencode(value)}"

            if i != 0:
                output += f"&{entry}"
            else:
                output += entry

        return output
    
    @staticmethod
    def strptime_or_none(date_string: str, format: str) -> Union[datetime, None]:
        try:
            datetime.strptime(date_string, format)
        except ValueError:
            return None

    # Decorators

    """
    Throws NotLoggedInException if someone uses a method with this decorator
    and hasn't logged in yet
    """
    @staticmethod
    def logged_in(method):
        @wraps(method)
        def __impl(self: Module, *method_args, **method_kwargs):
            if not self.edupage.is_logged_in:
                raise NotLoggedInException()

            method_output = method(self, *method_args, **method_kwargs)
            
            return method_output
        return __impl
    
    @staticmethod
    def online_lesson(method):
        @wraps(method)
        def __impl(self, *method_args, **method_kwargs):
            if self.online_lesson_link is None:
                raise NotAnOnlineLessonError()
            method_output = method(self, *method_args, **method_kwargs)

            return method_output
        
        return __impl