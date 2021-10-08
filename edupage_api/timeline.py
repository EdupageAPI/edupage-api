from datetime import datetime
from edupage_api.dbi import DbiHelper
from edupage_api.people import EduAccount, Gender
from typing import Optional
from edupage_api.module import Module, ModuleHelper
from enum import Enum
import json

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

    @staticmethod
    def parse(string: str) -> Optional[Gender]:
        return ModuleHelper.parse_enum(string, EventType)

class TimelineEvent:
    def __init__(self, event_id: int, timestamp: datetime, text: str,
                 author: EduAccount, recipient: EduAccount, event_type: EventType):
        self.event_id = event_id
        self.timestamp = timestamp
        self.text = text
        self.author = author
        self.recipient = recipient
        self.event_type = event_type

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
            print(recipient_name)

            if recipient_name == "*" or recipient_name == "Celá škola":
                recipient = "*"
            else:
                ModuleHelper.assert_none(recipient_data)

                recipient = EduAccount.parse(recipient_data, recipient_data.get("id"), self.edupage)

            # todo: add support for "*"
            author_name = event.get("vlastnik_meno")
            author_data = DbiHelper(self.edupage).fetch_person_data_by_name(author_name)

            print(author_name)
            if author_name == "*":
                author = "*"
            else:
                ModuleHelper.assert_none(author_data)
                author = EduAccount.parse(author_data, author_data.get("id"), self.edupage)

            event = TimelineEvent(event_id, event_timestamp, text, author, recipient, event_type)
            output.append(event)
        return output