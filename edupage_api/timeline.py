import json
from datetime import datetime
from enum import Enum
from typing import Optional

from edupage_api.dbi import DbiHelper
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduAccount, Gender


# data.dbi.event_types
class EventType(Enum):
    TT_CANCEL = "ttcancel"
    HOLIDAY = "holiday"
    SHORT_HOLIDAY = "sholiday"
    FREE_DAY = "freeday"
    DISTANT_LEARNING = "distant"
    LESSON = "lesson"
    PROJECT_LESSON = "plesson"
    TUTORING = "rlesson"
    CLASS_TEACHER_LESSON = "ctlesson"
    SCHOOL_EVENT = "schoolevent"
    SCHOOL_TRIP = "trip"
    CULTURE = "culture"
    EXCURSION = "excursion"
    CLASS_TEACHER_EVENT = "ctevent"
    TESTING = "testing"
    BIG_EXAM = "bexam"
    SHORT_EXAM = "sexam"
    ORAL_EXAM = "oexam"
    PAPER = "rexam"
    PROJECT = "project"
    TEACHER_MEETING = "meeting"
    CLASSIFICATION_MEETING = "bmeeting"
    BOOKED_ROOM = "bookroom"
    CHANGE_ROOM = "changeroom"
    OTHER = "other"
    SAFETY_INSTRUCTIONING = "other_safety"
    PARENTS_EVENING = "parentsevening"
    CLASS_BOOK = "other_cb"
    REPRESENTATION = "representation"
    NEW_MENU = "h_stravamenu"
    HOMEWORK_TEST = "etesthw"
    PROJECT_EXAM = "pexam"
    EVENT = "event"
    H_SUBSTITUTION = "h_substitution"
    H_CLEARCACHE = "h_clearcache"
    H_FINANCES = "h_financie"
    H_CLEARPLANS = "h_clearplany"
    H_HOMEWORK = "h_homework"
    H_DAILYPLAN = "h_dailyplan"
    ARRIVAL_TO_SCHOOL = "pipnutie"
    FOOD_SERVED = "strava_vydaj"
    GRADE = "znamka"
    MESSAGE = "sprava"
    NEWS = "news"
    TIMETABLE = "timetable"
    HOMEWORK = "homework"
    H_PROCESSTYPES = "h_processtypes"
    CONFIRMATION = "confirmation"
    H_TIMETABLE = "h_timetable"
    STUDENT_ABSENT = "student_absent"
    H_GRADES = "h_znamky"
    GRADES_DOC = "znamkydoc"
    H_CLEARDBI = "h_cleardbi"
    H_CLEARISICDATA = "h_clearisicdata"
    H_EDUSETTINGS = "h_edusettings"
    SUBSTITUTION = "substitution"
    H_ATTENDANCE = "h_attendance"
    EXCUSED_LESSON = "ospravedlnenka"
    ALBUM = "album"
    H_PROCESS = "h_process"
    CONTEST = "contest"
    FOOD_CREDIT = "strava_kredit"
    PROCESS = "process"
    EXAM_EVALUATION = "testvysledok"
    EXAM_ASSIGNMENT = "testpridelenie"
    H_SETTINGS = "h_settings"
    HOMEWORK_EVALUATION = "homeworkstudentstav"
    ASSIGNED_TEST = "testpridelenie"
    H_BEE = "h_vcelicka"
    H_CONTENST = "h_contest"
    TEST_RESULT = "testvysledok"
    HOMEWORK_STUDENT_STATE = "homeworkstudentstav"

    @staticmethod
    def parse(string: str) -> Optional[Gender]:
        return ModuleHelper.parse_enum(string, EventType)


class TimelineEvent:
    def __init__(self, event_id: int, timestamp: datetime, text: str,
                 author: EduAccount, recipient: EduAccount, event_type: EventType,
                 additional_data: dict):
        self.event_id = event_id
        self.timestamp = timestamp
        self.text = text
        self.author = author
        self.recipient = recipient
        self.event_type = event_type
        self.additional_data = additional_data


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
