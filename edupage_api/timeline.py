# For postponed evaluation of annotations
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import Optional, Union

from edupage_api.dbi import DbiHelper
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduAccount
from edupage_api.utils import RequestUtil
from edupage_api.exceptions import RequestError, MissingDataException


# data.dbi.event_types
class EventType(str, Enum):
    # Messages
    MESSAGE = "sprava"
    CHAT = "chat"
    POLL = "anketa"
    NEWS = "news"
    GENERIC_NOTIFICATION = "genotif"
    TEACHER_CONSULTATION = "konzultaciemsg"
    LIBRARY = "library"

    # ****************************************

    # Exam types
    BIG_EXAM = "bexam"
    HOMEWORK = "homework"
    ORAL_EXAM = "oexam"
    PAPER = "rexam"
    PROJECT_EXAM = "pexam"
    SHORT_EXAM = "sexam"
    TESTING = "testing"
    TEST_ME_MODULE = "testme"

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
    ENROLLMENT = "signin"
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
    EXCUSED_LESSON_REMINDER = "ospravedlnenka_reminder"
    REPRESENTATION = "representation"
    STUDENT_ABSENT = "student_absent"

    # ****************************************

    # Food
    FOOD_CREDIT = "strava_kredit"
    FOOD_SERVED = "strava_vydaj"
    NEW_MENU = "h_stravamenu"
    NEW_MENU_UPLOADED = "stravamenu"
    FOOD_ADMINISTRATION = "strava_prerusObnovObj"

    # ****************************************

    # Contest
    CONFIRMATION = "confirmation"
    CONTEST = "contest"

    # Photo album
    ALBUM = "album"

    # Payments
    PAYMENTS_PUBLISHED = "payments"

    # Lost and found
    LOST_AND_FOUND = "lost"

    # Other
    BEE = "vcelicka"
    OTHER = "other"
    SETTINGS = "settings"
    TWO_FACTOR_AUTHENTICATION = "fa2"

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
    H_IGROUPS = "h_igroups"
    H_PROCESS = "h_process"
    H_PROCESSTYPES = "h_processtypes"
    H_SETTINGS = "h_settings"
    H_SUBSTITUTION = "h_substitution"
    H_TIMETABLE = "h_timetable"
    H_USERPHOTO = "h_userphoto"

    @staticmethod
    def parse(event_type_str: str) -> Optional[EventType]:
        return ModuleHelper.parse_enum(
            event_type_str, EventType  # pyright: ignore[reportArgumentType]
        )


@dataclass
class TimelineEvent:
    event_id: int
    timestamp: datetime
    text: str
    author: Union[EduAccount, str]
    recipient: Union[EduAccount, str]
    event_type: EventType
    additional_data: dict
    is_done: bool = False
    done_at: Optional[datetime] = None
    is_starred: bool = False
    reaction_count: int = 0
    created_at: Optional[datetime] = None
    is_removed: bool = False

    # Meaning depends on `event_type`, e.g. chat_id for EventType.CHAT.
    # An int when the value is numeric, otherwise the raw str (e.g. hex IDs, dates).
    other_id: Optional[Union[int, str]] = None

    # event_id of the event this one replies to,
    # e.g. a reply to an EventType.MESSAGE points to the original message's event_id.
    response_to: Optional[int] = None

    # Meaning depends on `event_type`, e.g. the deadline day for EventType.HOMEWORK.
    event_time: Optional[datetime] = None


class TimelineEvents(Module):
    def __parse_items(
        self, timeline_items: dict, user_props: Optional[dict] = None
    ) -> list[TimelineEvent]:
        output = []

        # EduPage also returns [] when there are no user properties.
        if not isinstance(user_props, dict):
            user_props = {}

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

            event_timestamp = datetime.strptime(
                event.get("timestamp"), "%Y-%m-%d %H:%M:%S"
            )
            text = event.get("text")

            # Important messages have a localized placeholder in `text`.
            # Prefer the actual body without depending on the account language.
            message_content = (
                event_data.get("messageContent")
                if isinstance(event_data, dict)
                else None
            )
            if (
                event_type == EventType.MESSAGE
                and isinstance(message_content, str)
                and message_content.strip()
            ):
                text = message_content

            if text == "":
                try:
                    text = event_data.get("nazov")
                except:
                    text = ""

            # todo: add support for "*"
            recipient_name = event.get("user_meno")
            recipient_data = DbiHelper(self.edupage).fetch_person_data_by_name(
                recipient_name
            )

            if recipient_name in ["*", "Celá škola"]:
                recipient = "*"
            elif type(recipient_name) == str:
                recipient = recipient_name
            else:
                ModuleHelper.assert_none(recipient_data)

                recipient = EduAccount.parse(
                    recipient_data, recipient_data.get("id"), self.edupage
                )

            # todo: add support for "*"
            author_name = event.get("vlastnik_meno")
            author_data = DbiHelper(self.edupage).fetch_person_data_by_name(author_name)

            if author_name == "*":
                author = "*"
            elif type(author_name) == str:
                author = author_name
            else:
                ModuleHelper.assert_none(author_data)
                author = EduAccount.parse(
                    author_data, author_data.get("id"), self.edupage
                )

            additional_data = event.get("data")
            if additional_data and type(additional_data) == str:
                additional_data = json.loads(additional_data)

            # Parse user-specific state from userProps
            props = user_props.get(event_id_str, {})
            if not isinstance(props, dict):
                props = {}

            is_starred = props.get("starred") == "1"

            done_at = None
            done_at_str = props.get("doneMaxCas")
            if done_at_str:
                try:
                    done_at = datetime.strptime(done_at_str, "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    pass
            is_done = done_at is not None

            # Parse additional fields from raw event
            reaction_count = 0
            try:
                reaction_count = int(event.get("pocet_reakcii", 0))
            except (ValueError, TypeError):
                pass

            created_at = None
            created_at_str = event.get("cas_pridania")
            if created_at_str:
                try:
                    created_at = datetime.strptime(
                        created_at_str, "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, TypeError):
                    pass

            is_removed = event.get("removed") == "1"

            other_id = None
            ineid = event.get("ineid")
            if ineid:
                try:
                    other_id = int(ineid)
                except (ValueError, TypeError):
                    other_id = ineid

            response_to = None
            reakcia_na = event.get("reakcia_na")
            if reakcia_na:
                try:
                    response_to = int(reakcia_na)
                except (ValueError, TypeError):
                    pass

            event_time = None
            event_time_str = event.get("cas_udalosti")
            if event_time_str:
                try:
                    event_time = datetime.strptime(
                        event_time_str, "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, TypeError):
                    pass

            event = TimelineEvent(
                event_id,
                event_timestamp,
                text,
                author,
                recipient,
                event_type,
                additional_data,
                is_done=is_done,
                done_at=done_at,
                is_starred=is_starred,
                reaction_count=reaction_count,
                created_at=created_at,
                is_removed=is_removed,
                other_id=other_id,
                response_to=response_to,
                event_time=event_time,
            )
            output.append(event)

        return output

    def __get_user_props(self) -> dict:
        """Get user properties (starred, done state) from cached login data."""
        if self.edupage.data is None:
            return {}
        result = self.edupage.data.get("userProps")
        return result if isinstance(result, dict) else {}

    @ModuleHelper.logged_in
    def get_notifications_history(self, date_from: date):
        request_url = f"https://{self.edupage.subdomain}.edupage.org/timeline/"
        params = [
            ("module", "todo"),
            ("filterTab", ""),
            ("akcia", "getData"),
            ("filterTab", "messages"),
        ]

        response = self.edupage.session.post(
            request_url,
            params=params,
            data=RequestUtil.encode_form_data(
                {
                    "datefrom": date_from.strftime("%Y-%m-%d"),
                }
            ),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise RequestError(
                f"Edupage returned an error: status={response.status_code}"
            )

        data = response.json()
        if "timelineItems" not in data:
            raise MissingDataException(
                "Unexpected response from edupage! (no events in this time period?)"
            )

        # The history endpoint returns user props under "timelineUserProps"
        user_props = data.get("timelineUserProps")
        if user_props is None:
            user_props = self.__get_user_props()

        return self.__parse_items(data["timelineItems"], user_props)

    @ModuleHelper.logged_in
    def get_notifications(self):
        return self.__parse_items(
            self.edupage.data.get("items"),  # pyright: ignore[reportArgumentType]
            self.__get_user_props(),
        )
