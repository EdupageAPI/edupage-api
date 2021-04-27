import datetime


class EduDate:
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    @staticmethod
    def fromFormattedDate(formatted_date):
        if formatted_date == None:
            return None

        [year, month, day] = formatted_date.split("-")
        return EduDate(year, month, day)

    @staticmethod
    def today():
        now = datetime.datetime.now()

        return EduDate.fromFormattedDate(now.strftime("%Y-%m-%d"))

    class ThisTime:
        @staticmethod
        def yesterday():
            yesterday = datetime.datetime.now() + datetime.timedelta(days=-1)

            return EduDate.fromFormattedDate(yesterday.strftime("%Y-%m-%d"))

        @staticmethod
        def tomorrow():
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

            return EduDate.fromFormattedDate(tomorrow.strftime("%Y-%m-%d"))

    def afterOrEquals(self, date):
        return datetime.datetime.strptime(
            date, "%Y-%m-%d") >= datetime.datetime.strptime(
                self.__str__(), "%Y-%m-%d")

    def __str__(self):
        return "%04d-%02d-%02d" % (int(self.year), int(self.month), int(self.day))


class EduExactTime:
    def __init__(self, hour: int, minute: int, second: int):
        self.hour = hour
        self.minute = minute
        self.second = second

    def before(self, other):
        return other.hour > self.hour or \
              (other.hour == self.hour and other.minute > self.minute) or \
              (other.hour == self.hour and other.minute == self.minute and other.second > self.second)

    def beforeOrEquals(self, other):
        return self.before(other) or self.equals(other)

    def after(self, other):
        return other.hour < self.hour or \
              (other.hour == self.hour and other.minute < self.minute) or \
              (other.hour == self.hour and other.minute == self.minute and other.second < self.second)

    def afterOrEquals(self, other):
        return self.after(other) or self.equals(other)

    def equals(self, other):
        return other.hour == self.hour and other.minute == self.minute and other.second == self.second

    @staticmethod
    def now():
        datetime_now = datetime.datetime.now()

        return EduExactTime(datetime_now.hour, datetime_now.minute,
                            datetime_now.second)

    class ThisTime:
        @staticmethod
        def yesterday():
            datetime_yesterday = datetime.datetime.now() - datetime.timedelta(
                days=1)

            return EduExactTime(datetime_yesterday.hour, datetime_yesterday.minute,
                                datetime_yesterday.second)

        @staticmethod
        def tomorrow():
            datetime_tomorrow = datetime.datetime.now() + datetime.timedelta(
                days=-1)

            return EduExactTime(datetime_tomorrow.hour, datetime_tomorrow.minute,
                                datetime_tomorrow.second)

    @staticmethod
    def fromDatetime(dtime):
        return EduExactTime(dtime.hour, dtime.minute, dtime.second)

    @staticmethod
    def fromFormattedString(s):
        if s == None:
            return None

        [hour, minute, second] = s.split(":")

        return EduExactTime(hour, minute, second)

    def __str__(self):
        return "%02d:%02d:%02d" % (int(self.hour), int(self.minute), int(self.second))


class EduTime:
    def __init__(self, hour: int, minute: int):
        if type(hour) != int:
            self.hour = int(hour)
        else:
            self.hour = hour
        
        if type(minute) != int:
            self.minute = int(minute)
        else:
            self.minute = minute
       

    def is_before(self, other):
        return other.hour > self.hour or (other.hour == self.hour and other.minute > self.minute)

    def is_before_or_equals(self, other):
        return self.is_before(other) or self.equals(other)

    def is_after(self, other):
        return other.hour < self.hour or (other.hour == self.hour and other.minute < self.minute)

    def is_after_or_equals(self, other):
        return self.is_after(other) or self.equals(other)

    def equals(self, other):
        return other.hour == self.hour and other.minute == self.minute

    @staticmethod
    def now():
        datetime_now = datetime.datetime.now()

        return EduTime(datetime_now.hour, datetime_now.minute)

    @staticmethod
    def yesterday():
        datetime_yesterday = datetime.datetime.now() - datetime.timedelta(
            days=1)

        return EduTime(datetime_yesterday.hour, datetime_yesterday.minute)

    @staticmethod
    def tomorrow():
        datetime_tomorrow = datetime.datetime.now() + datetime.timedelta(
            days=-1)

        return EduTime(datetime_tomorrow.hour, datetime_tomorrow.minute)

    @staticmethod
    def from_datetime(dtime):
        return EduTime(dtime.hour, dtime.minute)

    @staticmethod
    def fromFormattedString(s):
        if s == None:
            return None

        [hour, minute] = s.split(":")

        return EduTime(hour, minute)

    def __str__(self):
        return "%02d:%02d" % (int(self.hour), int(self.minute))


class EduDateTime:
    def __init__(self, date: EduDate, hour, minute, second):
        self.date = date
        self.time = EduExactTime(int(hour), int(minute), int(second))

    @staticmethod
    def fromformattedDatetime(formatted_datetime):
        if formatted_datetime == None:
            return None

        split_date = formatted_datetime.split(" ")

        date = EduDate.fromFormattedDate(split_date[0])
        time = split_date[1].split(":")

        return EduDateTime(date, time[0], time[1], time[2])

    def __str__(self):
        return f'{str(self.date)} {str(self.time)}'


class EduLength:
    def __init__(self, start, end):
        self.start = EduTime.fromFormattedString(start)
        self.end = EduTime.fromFormattedString(end)

    def __str__(self):
        return str(self.start) + " – " + str(self.end)
