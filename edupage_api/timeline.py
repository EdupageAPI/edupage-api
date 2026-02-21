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


class TimelineEvents(Module):
    def __parse_items(
        self, timeline_items: dict, user_props: Optional[dict] = None
    ) -> list[TimelineEvent]:
        output = []

        if user_props is None:
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
