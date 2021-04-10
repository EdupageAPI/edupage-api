from datetime import date
import requests, json, datetime
import pprint, base64, hashlib

from edupage_api.utils import *
from edupage_api.date import *
from edupage_api.timetables import *
from edupage_api.messages import *
from edupage_api.grades import *
from edupage_api.people import *
from edupage_api.exceptions import *


class Edupage:
    def __init__(self, school, username, password):
        self.school = school
        self.username = username
        self.password = password
        self.is_logged_in = False
        self.session = requests.session()

    # a new way of logging in, contains some neat new features
    # and security measures such as english code or csrf tokens
    def login(self):
        # we first have to make a request to index.php to get the csrf token
        request_url = "https://" + self.school + ".edupage.org/login/index.php"

        csrf_response = self.session.get(request_url).content.decode()

        # we parse the token from the html
        csrf_token = csrf_response.split(
            "name=\"csrfauth\" value=\"")[1].split("\"")[0]

        # now everything is the same as in the first approach, we just add the csrf token
        parameters = {
            "username": self.username,
            "password": self.password,
            "csrfauth": csrf_token
        }
        request_url = "https://" + self.school + ".edupage.org/login/edubarLogin.php"

        response = self.session.post(request_url, parameters)

        if "bad=1" in response.url:
            raise BadCredentialsException()

        try:
            self.parse_login_data(response.content.decode())
        except (IndexError, TypeError):
            raise LoginDataParsingException()

        return True

    def parse_login_data(self, data):
        js_json = data.split("$j(document).ready(function() {")[1] \
              .split(");")[0] \
              .replace("\t", "") \
              .split("userhome(")[1] \
              .replace("\n", "") \
              .replace("\r", "")
        self.data = json.loads(js_json)
        self.is_logged_in = True
        self.ids = IdUtil(self.data)

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
        lessons = []
        for subj in plan:
            header = subj.get("header")
            if len(header) == 0:
                continue

            subject_id = subj.get("subjectid")
            print(f"Subject ID when fetching data: {subject_id}")
            subject_name = self.ids.id_to_subject(subject_id)

            teacher_id = subj.get("teacherids")
            if teacher_id != None and len(teacher_id) != 0:
                teacher_full_name = self.ids.id_to_teacher(teacher_id[0])
            else:
                teacher_full_name = None

            classroom_id = subj.get("classroomids")
            if classroom_id != None and len(classroom_id) != 0:
                classroom_number = self.ids.id_to_classroom(classroom_id[0])
            else:
                classroom_number = None

            start = subj.get("starttime")
            end = subj.get("endtime")
            length = EduLength(start, end)

            online_lesson_link = subj.get("ol_url")

            if online_lesson_link != None:
                lesson = EduOnlineLesson(subject_name, subject_id,
                                         teacher_full_name, classroom_number,
                                         length, online_lesson_link)
            else:
                lesson = EduLesson(subject_name, subject_id, teacher_full_name,
                                   classroom_number, length)
            lessons.append(lesson)

        return EduTimetable(lessons)

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
                continue

            if data.get("triedaid") == None:
                continue

            due_date = data.get("date")

            groups = data.get("skupiny")
            description = data.get("nazov")

            event_id = data.get("superid")

            class_name = ids.id_to_class(data.get("triedaid"))

            subject = ids.id_to_subject(data.get("predmetid"))

            timestamp = item.get("timestamp")

            current_homework = EduHomework(due_date, subject, groups, title,
                                           description, event_id, class_name,
                                           timestamp)
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
    # because all messages will betry:
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

    def __get_grade_data(self):
        response = self.session.get(
            f"https://{self.school}.edupage.org/znamky")

        return json.loads(response.content.decode() \
               .split(".znamkyStudentViewer(")[1] \
               .split(");\r\n\t\t});\r\n\t\t</script>")[0])

    def get_received_grade_events(self):
        if not self.is_logged_in:
            return None

        grade_data = self.__get_grade_data()

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

            subject_id = event.get("PredmetID")
            subject = id_util.id_to_subject(subject_id)

            event = EduGradeEvent(teacher, name, subject, average, weight,
                                  timestamp)
            received_grade_events.append(event)

        return received_grade_events

    def get_students(self):
        if not self.is_logged_in:
            return None

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

            student = EduStudent(gender, firstname, lastname, student_id,
                                 number_in_class, is_out)
            result.append(student)

        return result

    def get_teachers(self):
        if not self.is_logged_in:
            return None

        dbi = self.data.get("dbi")
        if dbi == None:
            return None

        id_util = IdUtil(dbi)

        teachers = dbi.get("teachers")

        result = []
        for teacher_id in teachers:
            teacher_data = teachers.get(teacher_id)

            gender = teacher_data.get("gender")
            firstname = teacher_data.get("firstname")
            lastname = teacher_data.get("lastname")

            classroom_id = teacher_data.get("classroomid")
            classroom = id_util.id_to_classroom(classroom_id)

            is_out = teacher_data.get("isOut")

            teacher = EduTeacher(gender, firstname, lastname, teacher_id,
                                 classroom, is_out)
            result.append(teacher)

        return result

    def get_user_id(self):
        return self.data.get("userid")

    # if (votingParams.answers && votingParams.answers.length > 0) {
    #     postData["votingParams"] = JSON.stringify(votingParams);
    # }

    # if (opts.edupageLink) {
    #     postData["edupageLink"] = JSON.stringify(opts.edupageLink);
    # }

    # if (opts.asKonzultacie) {
    #     postData["sendAsKonzultacie"] = '1';
    # }

    # if (d.repliesDisabled) {
    #     postData["repliesDisabled"] = '1';
    # }

    # if (d.repliesToAllDisabled) {
    #     postData["repliesToAllDisabled"] = '1';
    # }
    def send_message(self, recipients: EduUser, body, attachments=[]):
        recipients_post_data = ""

        if type(recipients) == list:
            for i, recipient in enumerate(recipients, start=0):
                if i != 0:
                    recipients_post_data += f";{recipient.get_id()}"
                else:
                    recipients_post_data += recipient.get_id()

        data = {
            "receipt": "0",
            "selectedUser": recipients_post_data,
            "text": body,
            "typ": "sprava",
            "attachements": RequestUtil.encode_attachments(attachments)
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

        params = (
            ('akcia', 'createItem'),
            ('eqav', '7'),
            ('maxEqav', '7'),
        )

        self.session.post('https://' + self.school + '.edupage.org/timeline/',
                          headers=headers,
                          params=params,
                          data=RequestUtil.encode_form_data(data))
