from edupage_api.date import EduDate, EduDateTime
from enum import Enum


class EduHomework:
    def __init__(self, id, done, done_date, due_date, subject, groups, title, description, event_id,
                 class_name, datetime_added):
        self.id = id
        self.done = done
        self.done_date = EduDateTime.from_formatted_datetime(done_date)
        self.due_date = EduDate.from_formatted_date(due_date)
        self.subject = subject
        self.groups = groups
        self.title = title
        self.description = description
        self.event_id = event_id
        self.class_name = class_name
        self.datetime_added = EduDateTime.from_formatted_datetime(
            datetime_added)

    def __str__(self):
        return f'{self.subject}: {self.title}'


class EduNews:
    def __init__(self, text, date_added, author, recipient):
        self.text = text
        self.date_added = EduDateTime.from_formatted_datetime(date_added)
        self.author = author
        self.recipient = recipient

    def __str__(self):
        return f'{self.text}'


class EduAttachment:
    def __init__(self, url, filename):
        self.url = url
        self.filename = filename
    
class NotificationType(Enum):
    MESSAGE = 0,
    HOMEWORK = 1
    GRADE = 2
    SUBSTITUTION = 3
    TIMETABLE = 4
    EVENT = 5

    def parse(s):
        if "sprava" in s:
            return NotificationType.MESSAGE
        elif "homework" in s:
            return NotificationType.HOMEWORK
        elif "znamka" in s:
            return NotificationType.GRADE
        elif "substitution" in s:
            return NotificationType.SUBSTITUTION
        elif "timetable" in s:
            return NotificationType.TIMETABLE
        elif "event" in s:
            return NotificationType.EVENT

class EduNotification:
	def __init__(self, id, thing, author, recipient, text, date_added, attachments, subject, name, due_date, grade, start, end, duration, event_kind):
		self.id = id
		self.thing = thing
		self.author = author
		self.recipient = recipient
		self.text = text
		self.date_added = EduDateTime.from_formatted_datetime(date_added)
		self.attachments = attachments
		self.subject = subject
		self.name = name
		self.due_date = EduDate.from_formatted_date(due_date)
		self.grade = grade
		self.start = EduDate.from_formatted_date(start)
		self.end = EduDate.from_formatted_date(end)
		self.duration = duration
		self.event_kind = event_kind
		
		def __str__(self):
			return f'{self.thing}, {self.text}'
  
