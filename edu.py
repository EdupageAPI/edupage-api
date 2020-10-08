import requests, json, datetime

class EduDate:
	def __init__(self, year, day, month):
		self.year = year
		self.day = day
		self.month = month

	def __init__(self, formatted_date):
		s = formatted_date.split("-")
		self.year = s[0]
		self.month = s[1]
		self.day = s[2]

	def __str__(self):
		return "%s-%s-%s" % (self.year, self.month, self.day)

class Ids:
	def __init__(self, data):
		self.data = data
		self.dbi = data.get("dbi")

	def IdToTeacher(self, id):
		teacher_data = self.dbi.get("teachers").get(id)
		teacher_full_name = teacher_data.get("firstname") + " " + teacher_data.get("lastname")
		return teacher_full_name

	def IdToClassroom(self, id):
		return self.dbi.get("classrooms").get(id).get("short")

	def IdToSubject(self, id):
		return self.dbi.get("subjects").get(id).get("short")

class EduLength:
	def __init__(self, start, end):
		self.start = start
		self.end = end
	
	def __str__(self):
		return self.start + " - " + self.end

class Lesson:
	def __init__(self, name, teacher, classroom, length):
		self.name = name
		self.teacher = teacher
		self.classroom = classroom
		self.length = length

class Edupage:
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.is_logged_in = False
	
	def login(self):
		parameters = {"meno": self.username, "password": self.password, "akcia": "login"}
		response = requests.post("https://portal.edupage.org/index.php?jwid=jw2&module=Login", parameters)
		if "wrongPassword" in response.url:
			return False
		js_json = response.content.decode().split("$j(document).ready(function() {")[1].split(");")[0].replace("\t", "").split("userhome(")[1].replace("\n", "").replace("\r", "")
		self.data = json.loads(js_json)   
		self.is_logged_in = True
		self.ids = Ids(self.data)
		return True

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
			subject_name = self.ids.IdToSubject(subject_id)
			
			teacher_id = subj.get("teacherids")[0]
			teacher_full_name = self.ids.IdToTeacher(teacher_id)

			classroom_id = subj.get("classroomids")[0]
			classroom_number = self.ids.IdToClassroom(classroom_id)

			start = subj.get("starttime")
			end = subj.get("endtime")
			length = EduLength(start, end)
			
			lesson = Lesson(subject_name, teacher_full_name, classroom_number, length) 
			subjects.append(lesson)

			
		return subjects


def main():
	datet = datetime.datetime.now()
	date = EduDate(str(datet).split(" ")[0])

	edu = Edupage(input("Username? "), input("Password? "))
	was_successfull = edu.login()
	if was_successfull:
		print("Login successfull!")
	else:
		print("Failed to login: bad username or password")
		return
	timetable = edu.get_timetable(date)
	if timetable == None:
		print("No timetable for this date.")
		return
	for lesson in timetable:
		print(lesson.name)
		print(lesson.teacher)
		print(lesson.classroom)
		print(str(lesson.length))
		print("\n")

if __name__ == "__main__":
	main()
