import functools
from datetime import date, datetime
from io import TextIOWrapper
from typing import Optional, Union

import requests
from requests import Response

from edupage_api.classes import Class, Classes
from edupage_api.classrooms import Classroom, Classrooms
from edupage_api.cloud import Cloud, EduCloudFile
from edupage_api.custom_request import CustomRequest
from edupage_api.grades import EduGrade, Grades, Term
from edupage_api.login import Login, TwoFactorLogin
from edupage_api.lunches import Lunches, Meals
from edupage_api.messages import Messages
from edupage_api.module import EdupageModule
from edupage_api.parent import Parent
from edupage_api.people import (
    EduAccount,
    EduStudent,
    EduStudentSkeleton,
    EduTeacher,
    People,
)
from edupage_api.ringing import RingingTime, RingingTimes
from edupage_api.subjects import Subject, Subjects
from edupage_api.substitution import Substitution, TimetableChange
from edupage_api.timeline import TimelineEvent, TimelineEvents
from edupage_api.timetables import Timetable, Timetables


class Edupage(EdupageModule):
    def __init__(self, request_timeout=5):
        """Initialize `Edupage` object.

        Args:
            request_timeout (int, optional): Length of request timeout in seconds.
                If want to upload bigger files, you will have to increase its value.
                Defaults to `5`.
        """

        self.data = None
        self.is_logged_in = False
        self.subdomain = None
        self.gsec_hash = None
        self.username = None

        self.session = requests.session()
        self.session.request = functools.partial(
            self.session.request, timeout=request_timeout
        )

    def login(
        self, username: str, password: str, subdomain: str
    ) -> Optional[TwoFactorLogin]:
        """Login while specifying the subdomain to log into.

        Args:
            username (str): Your username.
            password (str): Your password.
            subdomain (str): Subdomain of your school (https://{subdomain}.edupage.org).

        Returns:
            Optional[TwoFactorLogin]: Returns `None` if no second factor was needed to login,
            or the `TwoFactorLogin` object that is used to complete 2fa.
        """

        return Login(self).login(username, password, subdomain)

    def login_auto(self, username: str, password: str) -> Optional[TwoFactorLogin]:
        """Login using https://portal.edupage.org. If this doesn't work, please use `Edupage.login`.

        Args:
            username (str): Your username.
            password (str): Your password.

        Returns:
            Optional[TwoFactorLogin]: Returns `None` if no second factor was needed to login,
            or the `TwoFactorLogin` object that is used to complete 2fa.
        """

        return Login(self).login(username, password)

    def get_students(self) -> Optional[list[EduStudent]]:
        """Get list of all students in your class.

        Returns:
            Optional[list[EduStudent]]: List of `EduStudent`s.
        """

        return People(self).get_students()

    def get_all_students(self) -> Optional[list[EduStudentSkeleton]]:
        """Get list of all students in your school.

        Returns:
            Optional[list[EduStudentSkeleton]]: List of `EduStudentSkeleton`s.
        """

        return People(self).get_all_students()

    def get_teachers(self) -> Optional[list[EduTeacher]]:
        """Get list of all teachers in your school.

        Returns:
            Optional[list[EduTeacher]]: List of `EduTeacher`s.
        """

        return People(self).get_teachers()

    def get_classrooms(self) -> Optional[list[Classroom]]:
        """Get list of all classrooms in your school.

        Returns:
            Optional[list[Classroom]]: List of `Classroom`s.
        """

        return Classrooms(self).get_classrooms()

    def get_classes(self) -> Optional[list[Class]]:
        """Get list of all classes in your school.

        Returns:
            Optional[list[Class]]: List of `Class`es.
        """

        return Classes(self).get_classes()

    def get_subjects(self) -> Optional[list[Subject]]:
        """Get list of all subjects in your school.

        Returns:
            Optional[list[Subject]]: List of `Subject`s.
        """

        return Subjects(self).get_subjects()

    def send_message(
        self, recipients: Union[list[EduAccount], EduAccount], body: str
    ) -> int:
        """Send message.

        Args:
            recipients (Optional[list[EduAccount]]): Recipients of your message (list of `EduAccount`s).
            body (str): Body of your message.

        Returns:
            int: The timeline id of the new message.
        """

        return Messages(self).send_message(recipients, body)

    def get_my_timetable(self, date: date) -> Optional[Timetable]:
        """Get timetable for the logged-in user on a specified date.

        Args:
            date (datetime.date): The date for which you want to get timetable

        Returns:
            Optional[Timetable]: `Timetable` object for the specified date, if available; otherwise, `None`.
        """

        return Timetables(self).get_my_timetable(date)

    def get_meals(self, date: date) -> Optional[Meals]:
        """Get lunches.

        Args:
            date (datetime.date): Date from which you want to get lunches.

        Returns:
            Optional[Lunch]: Lunch object for entered date.
        """

        return Lunches(self).get_meals(date)

    def get_notifications(self) -> list[TimelineEvent]:
        """Get list of all available notifications.

        Returns:
            list[TimelineEvent]: List of `TimelineEvent`s.
        """

        return TimelineEvents(self).get_notifications()

    def get_notification_history(self, date_from: date) -> list[TimelineEvent]:
        """Get a list of all available notifications since `date_from` (until now).

        This method can be used instead of `get_notifications` if notifications older than
        1 month are needed.

        Args:
            date_from (datetime.date): The first day of the date range

        Returns:
            list[TimelineEvent]: List of all notifications since `date_from` up to now.
        """
        return TimelineEvents(self).get_notifications_history(date_from)

    def cloud_upload(self, fd: TextIOWrapper) -> EduCloudFile:
        """Upload file to EduPage cloud.

        Args:
            fd (TextIOWrapper): File you want to upload.

        Returns:
            EduCloudFile: Object of uploaded file.
        """

        return Cloud(self).upload_file(fd)

    def get_grades(self) -> list[EduGrade]:
        """Get a list of all available grades.

        Returns:
            list[EduGrade]: List of `EduGrade`s.
        """

        return Grades(self).get_grades(year=None, term=None)

    def get_grades_for_term(self, year: int, term: Term) -> list[EduGrade]:
        """Get a list of all available grades for a given year and term

        Returns:
            list[EduGrade]: List of `EduGrade`s
        """

        return Grades(self).get_grades(year=year, term=term)

    def get_user_id(self) -> str:
        """Get your EduPage user ID.

        Returns:
            str: Your EduPage user ID.
        """

        return self.data.get("userid")

    def custom_request(
        self, url: str, method: str, data: str = "", headers: dict = {}
    ) -> Response:
        """Send custom request to EduPage.

        Args:
            url (str): URL endpoint.
            method (str): Method (`GET` or `POST`).
            data (str, optional): Request data. Defaults to `""`.
            headers (dict, optional): Request headers. Defaults to `{}`.

        Returns:
            Response: Response.
        """

        return CustomRequest(self).custom_request(url, method, data, headers)

    def get_missing_teachers(self, date: date) -> list[EduTeacher]:
        """Get missing teachers for a given date.

        Args:
            date (datetime.date): The date you want to get this information for.

        Returns:
            list[EduTeacher]: List of the missing teachers for `date`.
        """
        return Substitution(self).get_missing_teachers(date)

    def get_timetable_changes(self, date: date) -> list[TimetableChange]:
        """Get the changes in the timetable for a given date.

        Args:
            date (datetime.date): The date you want to get this information for.

        Returns:
            list[TimetableChange]: List of changes in the timetable.
        """
        return Substitution(self).get_timetable_changes(date)

    def get_school_year(self) -> int:
        """Returns the current school year.

        Returns:
            int: The starting year of the current school year.
        """
        return Timetables(self).get_school_year()

    def get_timetable(
        self,
        target: Union[EduTeacher, EduStudent, Class, Classroom],
        date: date,
    ) -> Optional[Timetable]:
        """Get timetable of a teacher, student, class, or classroom for a specific date.

        Args:
            target (Union[EduTeacher, EduStudent, Class, Classroom]): The target entity whose timetable you want.
            date (datetime.date): The date for which you want the timetable.

        Returns:
            Optional[Timetable]: `Timetable` object for the specified date, if available; otherwise, `None`.
        """

        return Timetables(self).get_timetable(target, date)

    def get_next_ringing_time(self, date_time: datetime) -> RingingTime:
        """Get the next lesson's ringing time for given `date_time`.

        Args:
            date_time (datetime.datetime): The (date)time you want to get this information for.

        Returns:
            RingingTime: The type (break or lesson) and time of the next ringing.
        """
        return RingingTimes(self).get_next_ringing_time(date_time)

    def switch_to_child(self, child: Union[EduAccount, int]):
        """Switch to an account of a child - can only be used on parent accounts

        Args:
            child (EduAccount | int): The account or `person_id` of the child you want to switch to

        Note: When you switch to a child account, all other methods will return data as if you were logged in as `child`
        """
        Parent(self).switch_to_child(child)

    def switch_to_parent(self):
        """Switches back to your parent account - can only be used on parent accounts"""
        Parent(self).switch_to_parent()

    @classmethod
    def from_session_id(cls, session_id: str, subdomain: str, username: str):
        """Create an `Edupage` instance with a session id and subdomain.

        Args:
            session_id (str): The `PHPSESSID` cookie.
            subdomain (str): Subdomain of the school which cookie is from.
            username (str): The username of the account this session_id is from.

        Returns:
            Edupage: A new `Edupage` instance.
        """
        instance = cls()

        Login(instance).reload_data(subdomain, session_id, username)

        return instance
