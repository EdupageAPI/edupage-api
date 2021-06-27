from edupage_api.date import EduDate, EduExactDateTime
from enum import Enum
import json


class EduHomework:
    def __init__(self, homework_id, done, done_date, due_date, subject, groups, title, description, event_id,
                 class_name, datetime_added):
        self.id = homework_id
        self.done = done
        self.done_date = EduExactDateTime.from_formatted_string(done_date)
        self.due_date = EduDate.from_formatted_string(due_date)
        self.subject = subject
        self.groups = groups
        self.title = title
        self.description = description
        self.event_id = event_id
        self.class_name = class_name
        self.datetime_added = EduExactDateTime.from_formatted_string(
            datetime_added)

    def __str__(self):
        return f'{self.subject}: {self.title}'


class EduNews:
    def __init__(self, text, date_added, author, recipient):
        self.text = text
        self.date_added = EduExactDateTime.from_formatted_string(date_added)
        self.author = author
        self.recipient = recipient

    def __str__(self):
        return f'{self.text}'


class EduAttachment:
    def __init__(self, url, filename):
        self.url = url
        self.filename = filename


class NotificationType(Enum):
    MESSAGE = 0
    HOMEWORK = 1
    GRADE = 2
    SUBSTITUTION = 3
    TIMETABLE = 4
    EVENT = 5

    @staticmethod
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
    def __init__(self, notification_id, event_type, author, recipient, text, date_added, attachments, subject, name,
                    due_date, grade, start, end, duration, event_type_name):
        self.id = notification_id
        self.event_type = event_type
        self.author = author
        self.recipient = recipient
        self.text = text
        self.date_added = EduExactDateTime.from_formatted_string(date_added)
        self.attachments = attachments
        self.subject = subject
        self.name = name
        self.due_date = EduDate.from_formatted_string(due_date)
        self.grade = grade
        self.start = EduDate.from_formatted_string(start)
        self.end = EduDate.from_formatted_string(end)
        self.duration = duration
        self.event_type_name = event_type_name

    def __str__(self):
        return f'{self.event_type}, {self.text}'
    
    def __add_reaction(self, edupage, state):
        request_url = f"https://{edupage.school}.edupage.org/timeline/?akcia=createConfirmation"

        data = {
            "groupid": self.id,
            "confirmType": "like",
            "val": state
        }

        response = edupage.session.post(request_url, data = data)

        try:
            response_data = json.loads(response.content.decode())
            if response_data.get("status") == "ok":
                return True
            else:
                return False
        except:
            return False

    def like(self, edupage):
        return self.__add_reaction(edupage, "1")
    
    def remove_like(self, edupage):
        return self.__add_reaction(edupage, "0")

  
