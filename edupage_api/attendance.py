import json

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from edupage_api.module import Module, ModuleHelper
from edupage_api.exceptions import MissingDataException


@dataclass
class AttendenceStatDetail:
    count: float
    excused: float
    unexcused: float


@dataclass
class AttendanceStatistic:
    total_lessons_absent: AttendenceStatDetail
    total_late_minutes: AttendenceStatDetail
    total_early_minutes: AttendenceStatDetail

    theory_lessons_total: AttendenceStatDetail
    theory_lessons_absent: AttendenceStatDetail
    theory_late_minutes: AttendenceStatDetail
    theory_early_minutes: AttendenceStatDetail

    training_lessons_total: AttendenceStatDetail
    training_lessons_absent: AttendenceStatDetail
    training_late_minutes: AttendenceStatDetail
    training_early_minutes: AttendenceStatDetail

    late_count: float
    early_count: float
    present_lessons_count: float
    distant_lessons_count: float

    # TODO (in the future): fields: "todo", "error", "sa_dontcount" - what do they mean?


@dataclass
class Arrival:
    date: date
    arrival: Optional[datetime]
    departure: Optional[datetime]


class Attendance(Module):
    def __get_attendance_data(self, user_id: str):
        request_url = f"https://{self.edupage.subdomain}.edupage.org/dashboard/eb.php"
        params = {
            "ebuid": user_id,
            "mode": "attendance",
        }

        response = self.edupage.session.get(request_url, params=params)
        response_html = response.text

        user_id_number = Attendance.__get_user_id_number(user_id)
        try:
            data = response_html.split(
                'ASC.requireAsync("/dashboard/dochadzka.js#initZiak").then'
            )[1][37:].split(f",[{user_id_number}],true);")[0]

            return json.loads(data)
        except IndexError:
            raise MissingDataException(
                'Unexpected response from attendance endpoint! (expected string `ASC.requireAsync("/dashboard/dochadzka.js#initZiak").then` to be in the response)'
            )

    @staticmethod
    def __get_user_id_number(user_id: str):
        return user_id.replace("Student", "").replace("Ucitel", "")

    def get_attendance_available_days(self, user_id: str) -> list[str]:
        user_id_number = Attendance.__get_user_id_number(
            self.edupage.get_user_id()  # pyright: ignore[reportAttributeAccessIssue]
        )

        target_user_id_number = Attendance.__get_user_id_number(user_id)
        attendance_data = self.__get_attendance_data(user_id_number)

        stats = attendance_data["dateStats"]
        return stats[target_user_id_number].keys()

    @ModuleHelper.logged_in
    def get_arrivals(self, user_id: str) -> dict[str, Arrival]:
        user_id_number = Attendance.__get_user_id_number(
            self.edupage.get_user_id()  # pyright: ignore[reportAttributeAccessIssue]
        )

        target_user_id_number = Attendance.__get_user_id_number(user_id)

        attendance_data = self.__get_attendance_data(user_id_number)
        detailed_stats = attendance_data["students"][target_user_id_number]

        arrivals = {}
        for raw_date, arrival_data in detailed_stats.items():
            if "prichod" not in arrival_data and "odchod" not in arrival_data:
                continue

            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()

            arrival_time = (
                datetime.strptime(
                    arrival_data.get("prichod"),
                    "%H:%M:%S",
                ).replace(
                    year=parsed_date.year, month=parsed_date.month, day=parsed_date.day
                )
                if arrival_data.get("prichod") is not None
                else None
            )

            departure_time = (
                datetime.strptime(
                    arrival_data.get("odchod"),
                    "%H:%M:%S",
                ).replace(
                    year=parsed_date.year, month=parsed_date.month, day=parsed_date.day
                )
                if arrival_data.get("odchod") is not None
                else None
            )

            arrivals[raw_date] = Arrival(parsed_date, arrival_time, departure_time)

        return arrivals

    @ModuleHelper.logged_in
    def get_attendance_statistics(self, user_id: str, date: date):
        user_id_number = Attendance.__get_user_id_number(
            self.edupage.get_user_id()  # pyright: ignore[reportAttributeAccessIssue]
        )

        target_user_id_number = Attendance.__get_user_id_number(user_id)

        attendance_data = self.__get_attendance_data(user_id_number)

        all_stats = attendance_data["dateStats"]
        stats = all_stats[target_user_id_number][date.strftime("%Y-%m-%d")]

        total_lessons_absent = AttendenceStatDetail(
            count=stats.get("absent"),
            excused=stats.get("excused"),
            unexcused=stats.get("unexcused"),
        )

        total_late_minutes = AttendenceStatDetail(
            count=stats.get("late_minutes"),
            excused=stats.get("late_excused_auto"),
            unexcused=stats.get("late_unexcused_auto"),
        )

        total_early_minutes = AttendenceStatDetail(
            count=stats.get("early_minutes"),
            excused=stats.get("early_excused_auto"),
            unexcused=stats.get("early_unexcused_auto"),
        )

        theory_lessons_total = AttendenceStatDetail(
            count=stats.get("teoria_absent"),
            excused=stats.get("teoria_excused"),
            unexcused=stats.get("teoria_unexcused"),
        )

        theory_lessons_absent = AttendenceStatDetail(
            count=stats.get("teoria_absent_only"),
            excused=stats.get("teoria_absent_excused"),
            unexcused=stats.get("teoria_absent_unexcused"),
        )

        theory_early_minutes = AttendenceStatDetail(
            count=stats.get("teoria_early"),
            excused=stats.get("teoria_early_excused"),
            unexcused=stats.get("teoria_early_unexcused"),
        )

        theory_late_minutes = AttendenceStatDetail(
            count=stats.get("teoria_late"),
            excused=stats.get("teoria_late_excused"),
            unexcused=stats.get("teoria_late_unexcused"),
        )

        training_lessons_total = AttendenceStatDetail(
            count=stats.get("prax_absent"),
            excused=stats.get("prax_excused"),
            unexcused=stats.get("prax_unexcused"),
        )

        training_lessons_absent = AttendenceStatDetail(
            count=stats.get("prax_absent_only"),
            excused=stats.get("prax_absent_excused"),
            unexcused=stats.get("prax_absent_unexcused"),
        )

        training_early_minutes = AttendenceStatDetail(
            count=stats.get("prax_early"),
            excused=stats.get("prax_early_excused"),
            unexcused=stats.get("prax_early_unexcused"),
        )

        training_late_minutes = AttendenceStatDetail(
            count=stats.get("prax_late"),
            excused=stats.get("prax_late_excused"),
            unexcused=stats.get("prax_late_unexcused"),
        )

        return AttendanceStatistic(
            total_lessons_absent,
            total_late_minutes,
            total_early_minutes,
            theory_lessons_total,
            theory_lessons_absent,
            theory_late_minutes,
            theory_early_minutes,
            training_lessons_total,
            training_lessons_absent,
            training_late_minutes,
            training_early_minutes,
            late_count=stats.get("late"),
            early_count=stats.get("early"),
            present_lessons_count=stats.get("present"),
            distant_lessons_count=stats.get("distant"),
        )
