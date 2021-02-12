from edupage_api.date import EduDate, EduDateTime

class EduHomework:
	def __init__(self, due_date, subject, groups, title, description, event_id, class_name, datetime_added):
		self.due_date = EduDate.from_formatted_date(due_date)
		self.subject = subject
		self.groups = groups
		self.title = title
		self.description = description
		self.event_id = event_id
		self.datetime_added = EduDateTime.from_formatted_datetime(datetime_added)
	
	def __str__(self):
		return f'{self.title}: {self.description}'

class EduNews:
	def __init__(self, text, date_added, author, recipient):
		self.text = text
		self.date_added = EduDateTime.from_formatted_datetime(date_added)
		self.author = author
		self.recipient = recipient
	
	def __str__(self):
		return f'{self.text}'