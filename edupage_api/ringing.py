from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum

from edupage_api.module import Module, ModuleHelper


class RingingType(str, Enum):
    BREAK = "BREAK"
    LESSON = "LESSON"


@dataclass
class RingingTime:
    # The thing this ringing is announcing (break or lesson)
    type: RingingType
    time: time


class RingingTimes(Module):
    @staticmethod
    def __parse_time(s: str) -> time:
        hours, minutes = s.split(":")
        return time(int(hours), int(minutes))

    @staticmethod
    def __set_hours_and_minutes(dt: datetime, hours: int, minutes: int) -> datetime:
        return datetime(dt.year, dt.month, dt.day, hours, minutes)

    @staticmethod
    def __get_next_workday(date_time: datetime):
        if date_time.date().weekday() == 5:
            date_time = RingingTimes.__set_hours_and_minutes(date_time, 0, 0)
            return date_time + timedelta(days=2)
        elif date_time.date().weekday() == 6:
            date_time = RingingTimes.__set_hours_and_minutes(date_time, 0, 0)
            return date_time + timedelta(days=1)
        else:
            return date_time

    @ModuleHelper.logged_in
    def get_next_ringing_time(self, date_time: datetime) -> RingingTime:
        date_time = RingingTimes.__get_next_workday(date_time)

        ringing_times = self.edupage.data.get("zvonenia")
        for ringing_time in ringing_times:
            start_time = RingingTimes.__parse_time(ringing_time.get("starttime"))
            if date_time.time() < start_time:
                date_time = RingingTimes.__set_hours_and_minutes(
                    date_time, start_time.hour, start_time.minute
                )

                return RingingTime(RingingType.LESSON, date_time)

            end_time = RingingTimes.__parse_time(ringing_time.get("endtime"))
            if date_time.time() < end_time:
                date_time = RingingTimes.__set_hours_and_minutes(
                    date_time, end_time.hour, end_time.minute
                )

                return RingingTime(RingingType.BREAK, date_time)

        date_time += timedelta(1)
        date_time = RingingTimes.__set_hours_and_minutes(date_time, 0, 0)

        return self.get_next_ringing_time(date_time)
