from datetime import date
import requests, json, datetime, pprint

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

class GradeUtil:
	def __init__(self, grade_data):
		self.data = grade_data
	
	def id_to_teacher(self, teacher_id):
		teachers = self.data.get("ucitelia")

		# this dict contains data about the 
		# date when this teacher was employed
		# or when will he/she retire / is planned quit this job
		# (datefrom, dateto) 
		teacher = teachers.get(teacher_id) 

		teacher_name = teacher.get("firstname") + " " + teacher.get("lastname")
		
		return teacher_name 

class IdUtil:
	def __init__(self, data):
		self.data = data
		self.dbi = data.get("dbi")
	
	def id_to_class(self, c_id):
		return self.dbi.get("classes").get(c_id).get("name")

	def id_to_teacher(self, t_id):
		teacher_data = self.dbi.get("teachers").get(t_id)
		teacher_full_name = teacher_data.get("firstname") + " " + teacher_data.get("lastname")
		return teacher_full_name

	def id_to_classroom(self, c_id):
		return self.dbi.get("classrooms").get(c_id).get("short")

	def id_to_subject(self, s_id):
		return self.dbi.get("subjects").get(s_id).get("short")

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

class EduNews:
	def __init__(self, text, date_added, author, recipient):
		self.text = text
		self.date_added = EduDateTime.from_formatted_datetime(date_added)
		self.author = author
		self.recipient = recipient
	
	def __str__(self):
		return f'{self.text}'

# This is just a message that a grade has been received
# and it contains no information about what the grade is.
class EduGradeEvent:
	def __init__(self, teacher, title, subject, average, weight, datetime_added):
		self.teacher = teacher
		self.title = title
		self.subject = subject
		self.average = average
		self.datetime_added = EduDateTime.from_formatted_datetime(datetime_added)
	
	def __str__(self):
		return f'{self.title}'

class EduStudent:
	def __init__(self, gender, firstname, lastname, student_id, number, is_out):
		self.gender = gender
		self.firstname = firstname
		self.lastname = lastname
		self.fullname = firstname + " " + lastname
		self.id = int(student_id)
		self.number_in_class = int(number) 
		self.is_out = is_out
	
	def __sort__(self):
		return self.number_in_class
	
	def __str__(self):
		return "{gender: %s, name: %s, id: %d, number: %s, is_out: %s" % (self.gender, self.fullname, self.id, self.number_in_class, self.is_out)

class EduLength:
	def __init__(self, start, end):
		self.start = start
		self.end = end
	
	def __str__(self):
		return self.start + " - " + self.end

class EduLesson:
	def __init__(self, name, teacher, classroom, length, online_lesson_link):
		self.name = name
		self.teacher = teacher
		self.classroom = classroom
		self.length = length
		self.online_lesson_link = online_lesson_link

class Edupage:
	def __init__(self, username, password):
		self.school = None
		self.username = username
		self.password = password
		self.is_logged_in = False
		self.session = requests.session()
	
	def login(self):
		parameters = {"meno": self.username, "password": self.password, "akcia": "login"}
		response = self.session.post("https://portal.edupage.org/index.php?jwid=jw2&module=Login", parameters)
		if "wrongPassword" in response.url:
			return False
		try:
			js_json = response.content.decode() \
									.split("$j(document).ready(function() {")[1] \
									.split(");")[0] \
									.replace("\t", "") \
									.split("userhome(")[1] \
									.replace("\n", "") \
									.replace("\r", "")
		except TypeError:
			return False
		except IndexError:
			return False
		self.school = response.url.split(".edupage.org")[0] \
								.split("https://")[1]
		self.cookies = response.cookies.get_dict()
		self.headers = response.headers
		self.data = json.loads(js_json)
		self.is_logged_in = True
		self.ids = IdUtil(self.data)
		return True
	
	def get_available_timetable_dates(self):
		if not self.is_logged_in:
			return None
		
		dp = self.data.get("dp")
		if dp == None:
			return None
		
		dates = dp.get("dates")
		return list(dates.keys())

	def get_timetable(self, date):
		if not self.is_logged_in:
			return None
		dp = self.data.get("dp")
		if dp == None:
			return None
			
		dates = dp.get("dates")
		date_plans = dates.get(str(date))
		if date_plans == None:
			return None
		
		plan = date_plans.get("plan")
		subjects = []
		for subj in plan:
			header = subj.get("header")
			if len(header) == 0:
				return subjects
			
			subject_id = subj.get("subjectid")
			subject_name = self.ids.id_to_subject(subject_id)
			
			teacher_id = subj.get("teacherids")[0]
			teacher_full_name = self.ids.id_to_teacher(teacher_id)

			classroom_id = subj.get("classroomids")[0]
			classroom_number = self.ids.id_to_classroom(classroom_id)

			start = subj.get("starttime")
			end = subj.get("endtime")
			length = EduLength(start, end)

			online_lesson_link = subj.get("ol_url")
			
			lesson = EduLesson(subject_name, teacher_full_name, classroom_number, length, online_lesson_link) 
			subjects.append(lesson)

			
		return subjects
	
	def get_homework(self):
		if not self.is_logged_in:
			return None
		
		items = self.data.get("items")
		if items == None:
			return None
		
		ids = IdUtil(self.data)

		homework = []
		for item in items:
			if not item.get("typ") == "homework":
				continue

			title = item.get("user_meno")

			data = json.loads(item.get("data"))

			if data == None:
				print(item)

			due_date = data.get("date")

			groups = data.get("skupiny")
			description = data.get("nazov")

			event_id = data.get("superid")

			class_name = ids.id_to_class(data.get("triedaid"))

			subject = ids.id_to_subject(data.get("predmetid"))

			timestamp = item.get("timestamp")

			current_homework = EduHomework(due_date, subject, groups, title, description, event_id, class_name, timestamp)
			homework.append(current_homework)
		
		return homework

	def get_news(self):
		if not self.is_logged_in:
			return None
		
		items = self.data.get("items")
		if items == None:
			return None
		
		news = []
		for item in items:
			if not item.get("typ") == "news":
				continue

			text = item.get("text")
			timestamp = item.get("timestamp")
			author = item.get("vlastnik_meno")
			recipient = item.get("user_meno")

			news_message = EduNews(text, timestamp, author, recipient)
			news.append(news_message)
		
		return news

	# this method will soon be removed
	# because all messages will be
	# handled in some other way
	"""
	def get_grade_messages(self):
		if not self.is_logged_in:
			return None
		
		items = self.data.get("items")
		if items == None:
			return None

		ids = IdUtil(self.data)

		messages = []
		for item in items:
			if not item.get("typ") == "znamka":
				continue

			timestamp = item.get("timestamp")
			teacher = item.get("vlastnik_meno")
			text = item.get("text")

			data = json.loads(item.get("data"))
			subject_id = list(data.keys())[0]

			subject = ids.id_to_subject(subject_id)

			grade_data = data.get(subject_id)[0]
			
			grade_id = grade_data.get("znamkaid")
			grade = grade_data.get("data")
			action = grade_data.get("akcia")

			edugrade = EduGradeMessage(teacher, text, subject, grade, action, grade_id, timestamp)
			messages.append(edugrade)
		
		return messages
	"""
	
	def get_grade_data(self):
		response = self.session.get(f"https://{self.school}.edupage.org/znamky")
		
		return json.loads(response.content.decode() \
									.split(".znamkyStudentViewer(")[1] \
									.split(");\r\n\t\t});\r\n\t\t</script>")[0])

	def get_received_grade_events(self):
		grade_data = self.get_grade_data()

		util = GradeUtil(grade_data)
		id_util = IdUtil(self.data)

		received_grade_events = []

		providers = grade_data.get("vsetkyUdalosti")
		events = providers.get("edupage")
		for event_id in events:
			event = events.get(event_id)

			if event.get("stav") == None:
				continue

			name = event.get("p_meno")
			average = event.get("priemer")
			timestamp = event.get("timestamp")

			weight = event.get("p_vaha")

			teacher_id = event.get("UcitelID")
			teacher = util.id_to_teacher(teacher_id)

			subject_id = event.get()
			subject = id_util.id_to_subject(subject_id)

			event = EduGradeEvent(teacher, name, subject, average, weight, timestamp)
			received_grade_events.append(event)
		
		return received_grade_events
	
	def get_students(self):
		try:
			students = self.data.get("dbi").get("students")
		except Exception as e:
			print(e)
			return None
		if students == None:
			return []
		
		result = []
		for student_id in students:
			student_data = students.get(student_id)
			gender = student_data.get("gender")
			firstname = student_data.get("firstname")
			lastname = student_data.get("lastname")
			is_out = student_data.get("isOut")
			number_in_class = student_data.get("numberinclass")


			student = EduStudent(gender, firstname, lastname, student_id, number_in_class, is_out)
			result.append(student)
		return result


def main():
	edu = Edupage(input("Username?"), input("Password?"))
	was_successfull = edu.login()
	if was_successfull:
		print("Login successfull!")
	else:
		print("Failed to login: username or password")
		return
	edu.get_grade_data()

if __name__ == "__main__":
	main()

"""
TODO:
	- All message types
	- a way to wait for new messages/news/grades... listeners?
"""
