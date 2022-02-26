import urllib.parse
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Optional

import requests

from edupage_api.exceptions import (MissingDataException,
                                    NotAnOnlineLessonError,
                                    NotLoggedInException)


class EdupageModule:
    subdomain: str
    session: requests.Session
    data: dict
    is_logged_in: bool
    gsec_hash: str


class Module:
    def __init__(self, edupage: EdupageModule):
        self.edupage = edupage


class ModuleHelper:
    # Helper Functions

    @staticmethod
    def parse_int(val: str) -> Optional[int]:
        try:
            return int("".join(filter(str.isdigit, val)))
        except ValueError:
            return None

    """
    If any argument of this function is none, it throws MissingDataException
    """
    @staticmethod
    def assert_none(*args):
        if None in args:
            raise MissingDataException()

    @staticmethod
    def parse_enum(string: str, enum_type: Enum):
        filtered = list(filter(lambda x: x.value == string, list(enum_type)))

        if not filtered:
            return None

        return filtered[0]

    @staticmethod
    def return_first_not_null(*args):
        for x in args:
            if x:
                return x

    @staticmethod
    def urlencode(string: str) -> str:
        return urllib.parse.quote(string)

    @staticmethod
    def encode_form_data(data: dict) -> str:
        output = ""
        for i, key in enumerate(data.keys(), start=0):
            value = data[key]
            entry = f"{ModuleHelper.urlencode(key)}={ModuleHelper.urlencode(value)}"

            output += f"&{entry}" if i != 0 else entry
        return output

    @staticmethod
    def strptime_or_none(date_string: str, format: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_string, format)
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

            return method(self, *method_args, **method_kwargs)
        return __impl

    @staticmethod
    def online_lesson(method):
        @wraps(method)
        def __impl(self, *method_args, **method_kwargs):
            if self.online_lesson_link is None:
                raise NotAnOnlineLessonError()
            return method(self, *method_args, **method_kwargs)

        return __impl
