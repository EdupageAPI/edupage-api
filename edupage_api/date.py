import datetime

class EduDate:
	def __init__(self, year, day, month):
		self.year = year
		self.day = day
		self.month = month

	@staticmethod
	def from_formatted_date(formatted_date):
		if formatted_date == None:
			return None

		[year, day, month] = formatted_date.split("-")
		return EduDate(year, day, month)
	
	@staticmethod
	def now():
		now = datetime.datetime.now()
		
		return EduDate.from_formatted_date(now.strftime("%Y-%m-%d"))
	
	@staticmethod
	def yesterday_this_time():
		yesterday = datetime.datetime.now() + datetime.timedelta(days = -1)

		return EduDate.from_formatted_date(yesterday.strftime("%Y-%m-%d"))

	@staticmethod
	def tommorrow_this_time():
		tommorrow = datetime.datetime.now() + datetime.timedelta(days = 1)

		return EduDate.from_formatted_date(tommorrow.strftime("%Y-%m-%d"))
	
	def is_after_or_equals(self, date):
		return datetime.datetime.strptime(date, "%Y-%m-%d") >= datetime.datetime.strptime(self.__str__(), "%Y-%m-%d")

	def __str__(self):
		return "%s-%s-%s" % (self.year, self.month, self.day)

class EduExactTime:
	def __init__(self, hour: int, minute: int, second: int):
		self.hour = hour
		self.minute = minute
		self.second = second
	
	def is_before(self, other):
		return (other.hour == self.hour and other.minute <= self.minute) or \
			(other.hour < self.hour) or \
			(other.hour == self.hour and other.minute == self.minute and other.second < self.second)
	
	def is_before_or_equals(self, other):
		return (other.hour == self.hour and other.minute <= self.minute) or \
			(other.hour < self.hour) or \
			(other.hour == self.hour and other.minute == self.minute and other.second <= self.second)
	
	def is_after(self, other):
		return not self.is_before(other)
	
	def is_after_or_equals(self, other):
		return not self.is_before_or_equals(other)
	
	def equals(self, other):
		return other.hour == self.hour and other.minute == self.minute and other.second == self.second
	
	@staticmethod
	def now():
		datetime_now = datetime.datetime.now()

		return EduExactTime(datetime_now.hour, datetime_now.minute, datetime_now.second)
	
	@staticmethod
	def yesterday_this_time():
		datetime_yesterday = datetime.datetime.now() - datetime.timedelta(days = 1)

		return EduExactTime(datetime_yesterday.hour, datetime_yesterday.minute, datetime_yesterday.second) 

	@staticmethod
	def tommorrow_this_time():
		datetime_tommorrow = datetime.datetime.now() + datetime.timedelta(days = -1)

		return EduExactTime(datetime_tommorrow.hour, datetime_tommorrow.minute, datetime_tommorrow.second)

	@staticmethod
	def from_datetime(dtime):
		return EduExactTime(dtime.hour, dtime.minute, dtime.second)
	
	@staticmethod
	def from_formatted_string(s):
		if s == None:
			return None
		
		[hour, minute, second] = s.split(":")

		return EduExactTime(hour, minute, second)
	
	def __str__(self):
		return f"{self.hour}:{self.minute}:{self.second}"


class EduTime:
	def __init__(self, hour: int, minute: int):
		self.hour = hour
		self.minute = minute
	
	def is_before(self, other):
		return (other.hour == self.hour and other.minute < self.minute) or other.hour < self.hour
	
	def is_before_or_equals(self, other):
		return (other.hour == self.hour and other.minute <= self.minute) or other.hour < self.hour
	
	def is_after(self, other):
		return not self.is_before(other)
	
	def is_after_or_equals(self, other):
		return not self.is_before_or_equals(other)
	
	def equals(self, other):
		return other.hour == self.hour and other.minute == self.minute 

	@staticmethod
	def now():
		datetime_now = datetime.datetime.now()

		return EduTime(datetime_now.hour, datetime_now.minute)
	
	@staticmethod
	def yesterday():
		datetime_yesterday = datetime.datetime.now() - datetime.timedelta(days = 1)

		return EduTime(datetime_yesterday.hour, datetime_yesterday.minute) 

	@staticmethod
	def tommorrow():
		datetime_tommorrow = datetime.datetime.now() + datetime.timedelta(days = -1)

		return EduTime(datetime_tommorrow.hour, datetime_tommorrow.minute)

	@staticmethod
	def from_datetime(dtime):
		return EduTime(dtime.hour, dtime.minute)
	
	@staticmethod
	def from_formatted_string(s):
		if s == None:
			return None
		
		[hour, minute] = s.split(":")

		return EduTime(hour, minute)
	
	def __str__(self):
		return f"{self.hour}:{self.minute}"

class EduDateTime:
	def __init__(self, date: EduDate, hour, minute, second):
		self.date = date
		self.time = EduExactTime(int(hour), int(minute), int(second))

	@staticmethod
	def from_formatted_datetime(formatted_datetime):
		if formatted_datetime == None:
			return None
		
		split_date = formatted_datetime.split(" ")

		date = EduDate.from_formatted_date(split_date[0])
		time = split_date[1].split(":")

		return EduDateTime(date, time[0], time[1], time[2])
	
	def __str__(self):
		return f'{str(self.date)} {str(self.time)}'

class EduLength:
	def __init__(self, start, end):
		self.start = EduTime.from_formatted_string(start)
		self.end = EduTime.from_formatted_string(end)
	
	def __str__(self):
		return self.start + " - " + self.end