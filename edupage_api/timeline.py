# For postponed evaluation of annotations
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Union

from edupage_api.dbi import DbiHelper
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduAccount


# data.dbi.event_types
class EventType(str, Enum):
    # Messages
    MESSAGE = "sprava"
    POLL = "anketa"
    NEWS = "news"

    # ****************************************

    # Exam types
    BIG_EXAM = "bexam"
    HOMEWORK = "homework"
    ORAL_EXAM = "oexam"
    PAPER = "rexam"
    PROJECT_EXAM = "pexam"
    SHORT_EXAM = "sexam"
    TESTING = "testing"

    # Exam manipulation
    EXAM_ASSIGNMENT = "testpridelenie"
    EXAM_EVALUATION = "testvysledok"
    HOMEWORK_STUDENT_STATE = "homeworkstudentstav"
    HOMEWORK_TEST = "etesthw"
    TEST_RESULT = "testvysledok"

    # ****************************************

    # Grades
    GRADE = "znamka"
    GRADES_DOC = "znamkydoc"

    # ****************************************

    # Events
    CLASS_BOOK = "other_cb"
    CLASS_TEACHER_EVENT = "ctevent"
    CLASSIFICATION_MEETING = "bmeeting"
    CULTURE = "culture"
    EVENT = "event"
    EXCURSION = "excursion"
    PARENTS_EVENING = "parentsevening"
    PROCESS = "process"
    SCHOOL_EVENT = "schoolevent"
    SCHOOL_TRIP = "trip"
    TEACHER_MEETING = "meeting"

    # Free days
    FREE_DAY = "freeday"
    HOLIDAY = "holiday"
    SHORT_HOLIDAY = "sholiday"
    TT_CANCEL = "ttcancel"

    # Lessons
    CLASS_TEACHER_LESSON = "ctlesson"
    DISTANT_LEARNING = "distant"
    LESSON = "lesson"
    PROJECT = "project"
    PROJECT_LESSON = "plesson"
    SAFETY_INSTRUCTIONING = "other_safety"
    TUTORING = "rlesson"

    # ****************************************

    # Timetable
    TIMETABLE = "timetable"

    # Substitution
    BOOKED_ROOM = "bookroom"
    CHANGE_ROOM = "changeroom"
    SUBSTITUTION = "substitution"

    # ****************************************

    # Presence
    ARRIVAL_TO_SCHOOL = "pipnutie"

    # Absence
    EXCUSED_LESSON = "ospravedlnenka"
    REPRESENTATION = "representation"
    STUDENT_ABSENT = "student_absent"

    # ****************************************

    # Food
    FOOD_CREDIT = "strava_kredit"
    FOOD_SERVED = "strava_vydaj"
    NEW_MENU = "h_stravamenu"

    # ****************************************

    # Contest
    CONFIRMATION = "confirmation"
    CONTEST = "contest"

    # Photo album
    ALBUM = "album"

    # Other
    BEE = "vcelicka"
    OTHER = "other"

    # Helper
    H_ATTENDANCE = "h_attendance"
    H_BEE = "h_vcelicka"
    H_CLEARCACHE = "h_clearcache"
    H_CLEARDBI = "h_cleardbi"
    H_CLEARISICDATA = "h_clearisicdata"
    H_CLEARPLANS = "h_clearplany"
    H_CONTENST = "h_contest"
    H_DAILYPLAN = "h_dailyplan"
    H_EDUSETTINGS = "h_edusettings"
    H_FINANCES = "h_financie"
    H_GRADES = "h_znamky"
    H_HOMEWORK = "h_homework"
    H_PROCESS = "h_process"
    H_PROCESSTYPES = "h_processtypes"
    H_SETTINGS = "h_settings"
    H_SUBSTITUTION = "h_substitution"
    H_TIMETABLE = "h_timetable"
    H_USERPHOTO = "h_userphoto"

    @staticmethod
    def parse(event_type_str: str) -> Optional[EventType]:
        return ModuleHelper.parse_enum(event_type_str, EventType)


@dataclass
class TimelineEvent:
    event_id: int
    timestamp: datetime
    text: str
    author: Union[EduAccount, str]
    recipient: Union[EduAccount, str]
    event_type: EventType
    additional_data: dict


class TimelineEvents(Module):
    @ModuleHelper.logged_in
    def get_notifications(self):
        output = []

        timeline_items = self.edupage.data.get("items")

        for event in timeline_items:
            event_id_str = event.get("timelineid")
            if not event_id_str:
                continue

            event_id = int(event_id_str)
            event_data = json.loads(event.get("data"))

            event_type_str = event.get("typ")
            if not event_id_str:
                continue
            event_type = EventType.parse(event_type_str)

            if event_type is None:
                print(event_type_str)

            event_timestamp = datetime.strptime(event.get("timestamp"), "%Y-%m-%d %H:%M:%S")
            text = event.get("text")

            # what about different languages?
            # for message event type
            if text.startswith("Dôležitá správa"):
                text = event_data.get("messageContent")

            if text == "":
                try:
                    text = event_data.get("nazov")
                except:
                    text = ""

            # todo: add support for "*"
            recipient_name = event.get("user_meno")
            recipient_data = DbiHelper(self.edupage).fetch_person_data_by_name(recipient_name)

            if recipient_name in ["*", "Celá škola"]:
                recipient = "*"
            elif type(recipient_name) == str:
                recipient = recipient_name
            else:
                ModuleHelper.assert_none(recipient_data)

                recipient = EduAccount.parse(recipient_data, recipient_data.get("id"), self.edupage)

            # todo: add support for "*"
            author_name = event.get("vlastnik_meno")
            author_data = DbiHelper(self.edupage).fetch_person_data_by_name(author_name)

            if author_name == "*":
                author = "*"
            elif type(author_name) == str:
                author = author_name
            else:
                ModuleHelper.assert_none(author_data)
                author = EduAccount.parse(author_data, author_data.get("id"), self.edupage)

            additional_data = event.get("data")
            if additional_data and type(additional_data) == str:
                additional_data = json.loads(additional_data)

            event = TimelineEvent(event_id, event_timestamp, text, author,
                                  recipient, event_type, additional_data)
            output.append(event)
        return output
