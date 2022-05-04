# For postponed evaluation of annotations
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, Union

from edupage_api.exceptions import ExpiredSessionException, InvalidTeacherException
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduTeacher, People


class Action(str, Enum):
    ADDITION = "add"
    CHANGE = "change"
    DELETION = "remove"

    @staticmethod
    def parse(string: str) -> Optional[Action]:
        return ModuleHelper.parse_enum(string, Action)


@dataclass
class TimetableChange:
    change_class: str
    lesson_n: int
    title: str
    action: Union[Action, tuple[int, int]]


class Substitution(Module):
    def __get_substitution_data(self, date: date) -> str:
        url = (f"https://{self.edupage.subdomain}.edupage.org/substitution/server/viewer.js"
               "?__func=getSubstViewerDayDataHtml")

        data = {
            "__args": [
                None,
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "mode": "classes"
                }
            ],
            "__gsh": self.edupage.gsec_hash
        }

        response = self.edupage.session.post(url, json=data).content.decode()
        response = json.loads(response)

        if response.get("reload"):
            raise ExpiredSessionException("Invalid gsec hash! "
                                          "(Expired session, try logging in again!)")

        return response.get("r")

    @ModuleHelper.logged_in
    def get_missing_teachers(self, date: date) -> Optional[list[EduTeacher]]:
        html = self.__get_substitution_data(date)
        missing_teachers_string = (html.split("<span class=\"print-font-resizable\">")[1]
                                       .split("</span>")[0])

        if not missing_teachers_string:
            return None

        _title, missing_teachers = missing_teachers_string.split(": ")

        all_teachers = People(self.edupage).get_teachers()

        missing_teachers = [
            (t.strip()
              .split("  (")[0])
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
    def get_timetable_changes(self, date: date) -> Optional[list[TimetableChange]]:
        html = self.__get_substitution_data(date)

        class_delim = ("</div><div class=\"section print-nobreak\">"
                       "<div class=\"header\"><span class=\"print-font-resizable\">")
        changes_by_class_dirty = html.split(class_delim)[1:]

        if not changes_by_class_dirty:
            return None

        footer_delim = ("<div style=\"text-align:center;font-size:12px\">"
                        "<a href=\"https://www.asctimetables.com\" target=\"_blank\">"
                        "www.asctimetables.com</a> -")
        changes_by_class_dirty[-1] = changes_by_class_dirty[-1].split(footer_delim)[0]

        changes = [
            (x.replace("</div>", "")
              .replace("<div class=\"period\">", "")
              .replace("<span class=\"print-font-resizable\">", "")
              .replace("<div class=\"info\">", ""))
            for x in changes_by_class_dirty
        ]

        lesson_changes = []
        for class_changes in changes:
            class_changes_data = class_changes.split("</span><div class=\"rows\">")
            change_class = class_changes_data[0]

            class_changes_rows = class_changes_data[1].split("<div class=\"row ")[1:]

            for change in class_changes_rows:
                change = change.replace("\">", "</span>")
                action, lesson_n, title = change.split("</span>")[:-1]

                if "<img src=" in title:
                    title = title.split(">")[1]

                action = Action.parse(action)

                if "-" in lesson_n:
                    lesson_from, lesson_to = lesson_n.split(" - ")
                    lesson_n = (ModuleHelper.parse_int(lesson_from),
                                ModuleHelper.parse_int(lesson_to))
                else:
                    lesson_n = ModuleHelper.parse_int(lesson_n)

                lesson_change = TimetableChange(change_class, lesson_n, title, action)
                lesson_changes.append(lesson_change)

        return lesson_changes
