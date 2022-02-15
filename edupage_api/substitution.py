import enum
import json

from datetime import date
from typing import Union
from edupage_api.exceptions import ExpiredSessionException, InvalidTeacherException
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduTeacher, People


class Action(enum.Enum):
    DELETION = enum.auto()
    CHANGE = enum.auto()
    ADDITION = enum.auto()


class TimetableChange:
    def __init__(self, change_class: str, lesson_n: int, action: Union[Action, tuple[int, int]]):
        self.change_class = change_class
        self.lesson_n = lesson_n
        self.action = action


class Substitution(Module):
    def __get_substitution_data(self, date: date) -> str:
        url = (f"https://{self.edupage.subdomain}.edupage.org/substitution/server/viewer.js"
               "?__func=getSubstViewerDayDataHtml")

        data = {
            "__args": [None, {
                "date": date.strftime("%Y-%m-%d"),
                "mode": "classes"
            }],
            "__gsh": self.edupage.gsec_hash
        }

        response = self.edupage.session.post(url, json=data).content.decode()
        response = json.loads(response)

        if response.get("reload"):
            raise ExpiredSessionException("Invalid gsec hash! "
                                          "(Expired session, try logging in again!)")

        return response.get("r")

    @ModuleHelper.logged_in
    def get_missing_teachers(self, date: date) -> list[EduTeacher]:
        html = self.__get_substitution_data(date)
        missing_teachers_string = (html.split("<span class=\"print-font-resizable\">")[1]
                                       .split("</span>")[0])

        _title, missing_teachers = missing_teachers_string.split(": ")

        all_teachers = People(self.edupage).get_teachers()

        missing_teachers = [
            t.strip()
            for t in missing_teachers.split(", ")
        ]

        try:
            missing_teachers = [
                list(filter(lambda x: x.name == t, all_teachers))[0]
                for t in missing_teachers
            ]
        except IndexError:
            raise InvalidTeacherException("Invalid teacher in substitution! "
                                          "(The teacher is no longer frequenting this school)")

        return missing_teachers

    @ModuleHelper.logged_in
    def get_timetable_changes(self, date: date) -> list[TimetableChange]:
        html = self.__get_substitution_data(date)

        class_delim = ("</div><div class=\"section print-nobreak\">"
                       "<div class=\"header\"><span class=\"print-font-resizable\">")
        changes_by_class_dirty = html.split(class_delim)[1:]

        footer_delim = ("<div style=\"text-align:center;font-size:12px\">"
                        "<a href=\"https://www.asctimetables.com\" target=\"_blank\">"
                        "www.asctimetables.com</a> -")
        changes_by_class_dirty[-1] = changes_by_class_dirty[-1].split(footer_delim)[0]

        changes = [
            (x.replace("</div>", "")
              .replace("<div class=\"rows\">", "")
              .replace("<div class=\"period\">", "")
              .replace("<span class=\"print-font-resizable\">", "")
              .replace("<div class=\"info\">", ""))
            for x in changes_by_class_dirty
        ]

        lesson_changes = []
        for change in changes:
            change_class, lesson_n, teacher, *_ = change.split("</span>")

            action = None
            if "<div class=\"row change\">" in lesson_n:
                action = Action.CHANGE
            elif "<div class=\"row remove\">" in lesson_n:
                action = Action.DELETION
            elif "<div class=\"row add\">" in lesson_n:
                action = Action.ADDITION

            if "-" in lesson_n:
                lesson_from, lesson_to = lesson_n.split(" - ")
                lesson_n = (ModuleHelper.parse_int(lesson_from), ModuleHelper.parse_int(lesson_to))
            else:
                lesson_n = ModuleHelper.parse_int(lesson_n)

            lesson_change = TimetableChange(change_class, lesson_n, action)
            lesson_changes.append(lesson_change)

        return lesson_changes
