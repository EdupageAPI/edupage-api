class EduLesson:
	def __init__(self, name, teacher, classroom, length, online_lesson_link):
		self.name = name
		self.teacher = teacher
		self.classroom = classroom
		self.length = length
		self.online_lesson_link = online_lesson_link

class EduTimetable:
	def __init__(self, lessons):
		self.lessons = lessons
	
	def get_lesson_at_time(self, edutime):
		for lesson in self.lessons:
			if lesson.length.start.is_after_or_equals(edutime) and lesson.length.end.is_before_or_equals(edutime):
				return lesson 

		return None
	
	def get_next_lesson_at_time(self, edutime):
		previous = None
		for lesson in self.lessons:
			if previous == None:
				if lesson.start.is_before(edutime):
					return lesson
			else:
				if lesson.start.is_before(edutime) and previous.end.is_after(edutime):
					return lesson
			
			previous = lesson
		
		return None
	
	def get_first_lesson(self):
		return self.lessons[0]
	
	def get_last_lesson(self):
		return self.lessons[-1]