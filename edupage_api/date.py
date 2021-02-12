import datetime

class EduDate:
	def __init__(self, year, day, month):
		self.year = year
		self.day = day
		self.month = month

	@staticmethod
	def from_formatted_date(formatted_date):
		s = formatted_date.split("-")
		return EduDate(s[0], s[2], s[1])
	
	@staticmethod
	def today():
		now = datetime.datetime.now()
		
		return EduDate.from_formatted_date(now.strftime("%Y-%m-%d"))
	
	@staticmethod
	def yesterday():
		yesterday = datetime.datetime.now() + datetime.timedelta(days = -1)

		return EduDate.from_formatted_date(yesterday.strftime("%Y-%m-%d"))

	@staticmethod
	def tommorrow():
		tommorrow = datetime.datetime.now() + datetime.timedelta(days = 1)

		return EduDate.from_formatted_date(tommorrow.strftime("%Y-%m-%d"))
	
	def is_after_or_equals(self, date):
		return datetime.datetime.strptime(date, "%Y-%m-%d") >= datetime.datetime.strptime(self.__str__(), "%Y-%m-%d")

	def __str__(self):
		return "%s-%s-%s" % (self.year, self.month, self.day)


class EduDateTime:
	def __init__(self, date: EduDate, hour, minute, second):
		self.date = date
		self.hour = hour
		self.minute = minute
		self.second = second

	@staticmethod
	def from_formatted_datetime(formatted_datetime):
		split_date = formatted_datetime.split(" ")

		date = EduDate.from_formatted_date(split_date[0])
		time = split_date[1].split(":")

		return EduDateTime(date, time[0], time[1], time[2])
	
	def __str__(self):
		return f'{str(self.date)} {self.hour}:{self.minute}:{self.second}'

class EduLength:
	def __init__(self, start, end):
		self.start = start
		self.end = end
	
	def __str__(self):
		return self.start + " - " + self.end