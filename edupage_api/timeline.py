from datetime import datetime
from edupage_api.people import Gender
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

            event_timestamp = datetime.strftime("%Y-%m-%d %H:%M:%S")
            text = event.get("text")

            # what about diffrent languages?
            # for message event type
            if text.startswith("Dôležitá správa"):
                text = event.data.get("messageContent")
            
            if text == "":
                try:
                    text = event.data.get("nazov")
                except:
                    text = ""

