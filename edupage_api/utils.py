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