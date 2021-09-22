from edupage_api.lunches import EduLunch, EduMenu, EduRating
import requests
import json
import functools
import sys
import os

from edupage_api.utils import *
from edupage_api.date import *
from edupage_api.timetables import *
from edupage_api.messages import *
from edupage_api.grades import *
from edupage_api.people import *
from edupage_api.exceptions import *
from edupage_api.logging import *

globals().update(NotificationType.__members__)  # Statically import the NotificationType enum

# https://stackoverflow.com/questions/7445658/how-to-detect-if-the-console-does-support-ansi-escape-codes-in-python
def term_supports_color():
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                  'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return supported_platform and is_a_tty

class Edupage:
    def __init__(self, school, username, password, timeout = 5, log_level: LogLevel = LogLevel.WARNING):
        self.school = school
        self.username = username
        self.password = password
        self.is_logged_in = False
        self.session = requests.session()

        # Set a timeout for all requests made with this session
        self.session.request = functools.partial(self.session.request, timeout = timeout)

        self.logger = Logger(log_level, term_supports_color())

    # A new way of logging in, contains some neat new features
    # and security measures such as english code or csrf tokens
    def login(self):
        # We first have to make a request to index.php to get the csrf token
        request_url = f"https://{self.school}.edupage.org/login/index.php"

        csrf_response = self.session.get(request_url).content.decode()

        # Parse the token from the HTML
        csrf_token = csrf_response.split(
            "name=\"csrfauth\" value=\"")[1].split("\"")[0]

        self.logger.debug(f"Fetched csrf token: {csrf_token}")

        # Now is everything the same as in the first approach, we just add the csrf token
        parameters = {
            "username": self.username,
            "password": self.password,
            "csrfauth": csrf_token
        }
        request_url = f"https://{self.school}.edupage.org/login/edubarLogin.php"

        response = self.session.post(request_url, parameters)

        if "bad=1" in response.url:
            self.logger.warning("Incorrect credentials")
            raise BadCredentialsException()

        try:
            self.parse_login_data(response.content.decode())
        except (IndexError, TypeError) as e:
            self.logger.warning(f"There was an error while parsing login response: {e}")
            raise LoginDataParsingException()
        except Exception as e:
            self.logger.warning("There was a unhandled error, parsing login data. Printing additional information")
            raise e

        self.logger.debug("Successfully logged in!")
        return True

    def send_keepalive(self):
        if not self.is_logged_in:
            return None

        response = self.session.post(f"https://{self.school}.edupage.org/login/eauth?portalping")

        try:
            return json.loads(response.content.decode())
        except:
            return None

    def parse_login_data(self, data):
        
        js_json = data.split("$j(document).ready(function() {")[1] \
            .split(");")[0] \
            .replace("\t", "") \
            .split("userhome(")[1] \
            .replace("\n", "") \
            .replace("\r", "")
        self.logger.debug(f"Parsed html document: {js_json[:50]}")
        
        self.data = json.loads(js_json)
        
        
        self.logger.debug("Successfully deseralised data json!")
        
        self.is_logged_in = True
        self.ids = IdUtil(self.data)

    def get_available_timetable_dates(self):
        if not self.is_logged_in:
            return None

        dp = self.data.get("dp")
        if dp is None:
            self.logger.warning("DP is none!")
            return None

        dates = dp.get("dates")
        return list(dates.keys())

    def get_timetable(self, date):
        if not self.is_logged_in:
            return None
        dp = self.data.get("dp")
        if dp is None:
            self.logger.warning("DP is none!")
            return None

        dates = dp.get("dates")
        self.logger.debug("Getting date plans...")
        date_plans = dates.get(str(date))
        if date_plans is None:
            self.logger.warning("Date plans is none!")
            return None

        self.logger.debug("Starting lesson parsing...")
        plan = date_plans.get("plan")
        lessons = []
        for subj in plan:
            header = subj.get("header")
            if len(header) == 0:
                self.logger.debug("Found dummy lesson!")
                continue

            period = subj.get("uniperiod")

            subject_id = subj.get("subjectid")
            self.logger.debug(f"Parsing subject with id {subject_id}")
            if subject_id is not None and len(subject_id) != 0:
                subject_name = self.ids.id_to_subject(subject_id)
                self.logger.debug("Successfully fetched subject name from data!")
            else:
                self.logger.warning("Subject id couldn't be found in data or is none!")
                subject_name = header[0].get("text")

            teacher_id = subj.get("teacherids")
            self.logger.debug(f"Parsing teacher with id {teacher_id}")
            if teacher_id is not None and len(teacher_id) != 0:
                teacher_full_name = self.ids.id_to_teacher(teacher_id[0])
                self.logger.debug("Successfully fetched teacher name from data!")
            else:
                self.logger.warning("The teacher's name couldn't be found in data or is none!")
                teacher_full_name = None

            classroom_id = subj.get("classroomids")
            self.logger.debug(f"Parsing classroom number with id {classroom_id}")
            if classroom_id is not None and len(classroom_id) != 0:
                classroom_number = self.ids.id_to_classroom(classroom_id[0])
                self.logger.debug("Successfully fetched classroom number from data!")
            else:
                self.logger.warning("The classroom's number couldn't be found in data or is none!")
                classroom_number = None

            start = subj.get("starttime")
            end = subj.get("endtime")
            length = EduLength(start, end)

            online_lesson_link = subj.get("ol_url")

            if online_lesson_link is not None:
                lesson = EduOnlineLesson(period, subject_name, subject_id,
                                         teacher_full_name, classroom_number,
                                         length, online_lesson_link)
            else:
                lesson = EduLesson(period, subject_name, subject_id,
                                   teacher_full_name, classroom_number, length)

            lessons.append(lesson)

        self.logger.debug("Successfully constructed timetable!")
        return EduTimetable(lessons)

    def get_homework(self):
        if not self.is_logged_in:
            return None

        items = self.data.get("items")
        if items is None:
            self.logger.warning("The items entry in data is empty, couldn't parse homework!")
            return None

        ids = IdUtil(self.data)

        self.logger.debug("Starting homework parsing...")
        homework = []
        for item in items:
            if not item.get("typ") == "homework":
                continue

            data = json.loads(item.get("data"))

            if data is None:
                self.logger.warning("Found item with homework type with empty data, skipping...")
                continue

            if data.get("triedaid") is None:
                self.logger.warning("Found item with homework type with empty classroom id, skipping...")
                continue

            title = data.get("nazov")

            homework_id = item.get("timelineid")

            if str(homework_id) in self.data["userProps"]:
                if self.data["userProps"][str(homework_id)]["doneMaxCas"]:
                    self.logger.debug("Homework is done!")
                    done = True
                    done_date = self.data["userProps"][str(homework_id)]["doneMaxCas"]
            else:
                self.logger.debug("Homework is not done!")
                done = False
                done_date = None

            due_date = data.get("date")

            groups = data.get("skupiny")
            description = data.get("popis")

            event_id = data.get("superid")

            self.logger.debug("Parsing class name...")
            class_name = ids.id_to_class(data.get("triedaid"))

            self.logger.debug("Parsing subject name...")
            subject = ids.id_to_subject(data.get("predmetid"))

            timestamp = item.get("timestamp")

            current_homework = EduHomework(homework_id, done, done_date, due_date, subject, groups, title,
                                           description, event_id, class_name,
                                           timestamp)
            homework.append(current_homework)

        self.logger.debug("Successfully constructed list of homework!")
        return homework

    def get_news(self):
        if not self.is_logged_in:
            return None

        items = self.data.get("items")
        if items is None:
            self.logger.warning("The items entry in data is empty, couldn't parse news!")
            return None

        self.logger.debug("Starting news parsing...")
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

        self.logger.debug("Successfully constructed list of news!")
        return news

    # This method will soon be removed
    # because all messages will be try
    # handled in some other way:
    """
    def get_grade_messages(self):
        if not self.is_logged_in:
            return None

        items = self.data.get("items")
        if items is None:
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

        return json.loads(response.content.decode()
                          .split(".znamkyStudentViewer(")[1]
                          .split(");\r\n\t\t});\r\n\t\t</script>")[0])

    def get_received_grade_events(self):
        if not self.is_logged_in:
            return None

        grade_data = self.__get_grade_data()

        util = GradeUtil(grade_data)
        id_util = IdUtil(self.data)

        received_grade_events = []

        self.logger.debug("Starting grade event parsing...")
        providers = grade_data.get("vsetkyUdalosti")
        events = providers.get("edupage")
        for event_id in events:
            event = events.get(event_id)

            if event.get("stav") is None:
                self.logger.debug("Found dummy grade, skipping...")
                continue

            name = event.get("p_meno")
            average = event.get("priemer")
            timestamp = event.get("timestamp")

            weight = event.get("p_vaha")

            teacher_id = event.get("UcitelID")
            self.logger.debug(f"Parsing teacher with id: {teacher_id}")
            teacher = util.id_to_teacher(teacher_id)
            
            subject_id = event.get("PredmetID")
            self.logger.debug(f"Parsing subject with id: {subject_id}")
            subject = id_util.id_to_subject(subject_id)

            event = EduGradeEvent(teacher, name, subject, average, weight, timestamp)
            received_grade_events.append(event)

        self.logger.debug("Successfully constructed list of grade events!")
        return received_grade_events

    def get_grades(self):
        if not self.is_logged_in:
            return None

        grade_data = self.__get_grade_data()
        grades = grade_data.get("vsetkyZnamky")
        grade_details = grade_data.get("vsetkyUdalosti").get("edupage")
        output = []

        subjects = grade_data.get("predmety")

        teachers = grade_data.get("ucitelia")

        self.logger.debug("Starting grade parsing...")
        for grade in grades:
            event_id = str(grade.get("udalostid"))
            details = grade_details.get(event_id)

            title = details.get("p_meno").strip()

            grade_n = grade.get("data")

            datetime_added = grade.get("datum")

            subject_id = details.get("PredmetID")
            if subject_id == "vsetky":
                self.logger.warning("Found grade with bad subject id!")
                continue
            else:
                subject = subjects[str(subject_id)].get("p_meno")

            teacher_id = details.get("UcitelID")
            self.logger.debug(f"Parsing teacher with id {teacher_id}")
            if teacher_id is not None:
                teacher_id = int(teacher_id)
                teacher = teachers[str(teacher_id)]
                teacher = teacher.get("firstname") + " " + teacher.get("lastname")
            else:
                self.logger.warning("Couldn't parse teacher id!")
                teacher = None

            max_points = details.get("p_vaha_body")
            max_points = int(max_points) if max_points is not None else None

            importance = details.get("p_vaha")
            importance = 0 if float(importance) == 0 else 20 / float(importance)

            try:
                verbal = False
                if max_points:
                    percent = round(float(grade_n) / float(max_points) * 100, 2)
                else:
                    percent = None
            except:
                verbal = True
                percent = None

            grade = EduGrade(event_id, title, grade_n, importance,
                             datetime_added, subject, teacher, percent, verbal, max_points)
            output.append(grade)

        self.logger.debug("Successfully constructed a list of grades!")
        return output

    def get_notifications(self):
        if not self.is_logged_in:
            return None

        output = []

        subjects = self.data.get("subjects")
        event_types = self.data.get("dbi").get("event_types")
        grades = self.get_grades()

        self.logger.debug("Starting notification parsing...")
        for notification in self.data.get("items"):
            text = None
            date_added = None
            attachments = None
            subject = None
            name = None
            due_date = None
            grade = None
            start = None
            end = None
            duration = None
            event_type_name = None

            data = json.loads(notification.get("data"))

            notification_id = notification.get("timelineid")

            notification_type = notification.get("typ")
            notification_type = NotificationType.parse(notification_type)
            if notification_type is None:
                self.logger.warning("Found notification with empty type, skipping...")
                continue

            author = notification.get("vlastnik_meno")

            recipient = notification.get("user_meno")

            text = notification.get("text")

            if text.startswith("Dôležitá správa"):
                text = data.get("messageContent")

            if text == "":
                try:
                    text = data.get("nazov")
                except:
                    text = ""

            date_added = notification.get("timestamp")

            attachments = []
            try:
                atts = data.get("attachements")
                for attachment in atts:
                    attachments.append(EduAttachment(
                        attachment, atts[attachment]))
            except:
                pass

            try:
                if data:
                    subject = data.get("subjectid")
                    subject = subjects[subject]
            except:
                pass

            if notification_type == HOMEWORK and data:
                name = data.get("nazov")
                due_date = data.get("date")
            elif notification_type == EVENT and data:
                name = data.get("name")
            elif notification_type == GRADE:
                for g in grades:
                    if int(g.id) == int(notification_id):
                        grade = g
                        break

            if notification_type == EVENT and data:
                start = data.get("cas_udalosti")
                end = data.get("repeat_to")
                event_type = str(data.get("typ"))
                event_type_name = event_types[event_type].get("name")

            notification = EduNotification(notification_id, notification_type, author, recipient, text,
                                           date_added, attachments, subject, name, due_date,
                                           grade, start, end, duration, event_type_name)
            output.append(notification)
        self.logger.debug("Finished notification parsing!")
        return output

    def get_lunch(self, date):
        if not self.is_logged_in:
            return None

        request_url = f"https://{self.school}.edupage.org/menu/"
        response = self.session.get(request_url)
        response = response.content.decode()

        boarder_id = None
        lunch_data = None

        self.logger.debug("Starting lunch parsing...")
        try:
            boarder_id = response.split('var stravnikid = "')[1].split('"')[0]
            lunch_data = json.loads(response.split(
                'var novyListok = ')[1].split(";")[0])
            self.logger.debug(f"Successfully parsed data and boarder id ({boarder_id})!")
        except:
            self.logger.warning("Couldn't parse lunch data!")
            return None

        lunch = lunch_data.get(str(date))
        if lunch is None:
            return None

        lunch = lunch.get("2")

        served_from = lunch.get("vydaj_od")
        served_to = lunch.get("vyday_do")

        title = lunch.get("nazov")

        amount_of_foods = lunch.get("druhov_jedal")
        chooseable_menus = list(lunch.get("choosableMenus").keys())

        can_be_changed_until = lunch.get("zmen_do")

        menus = []
        for food in lunch.get("rows"):
            if food == []:
                self.logger.warning("Found empty food object")
                continue
            name = food.get("nazov")
            allergens = food.get("alergenyStr")
            weight = food.get("hmotnostiStr")
            number = food.get("menusStr")
            rating = None

            if number is not None:
                number = number.replace(": ", "")
                rating = lunch.get("hodnotenia")
                if rating is not None and rating != []:
                    rating = rating.get(number)

                    [quality, quantity] = rating

                    quality_average = quality.get("priemer")
                    quality_ratings = quality.get("pocet")

                    quantity_average = quantity.get("priemer")
                    quantity_ratings = quantity.get("pocet")

                    rating = EduRating(date, boarder_id, quality_average,
                                       quantity_average, quality_ratings,
                                       quantity_ratings)
                else:
                    rating = None

            menus.append(EduMenu(name, allergens, weight, number, rating))
        
        self.logger.debug("Succesfully constructed lunch object!")

        return EduLunch(served_from, served_to, amount_of_foods,
                        chooseable_menus, can_be_changed_until,
                        title, menus, date, boarder_id)

    def get_students(self):
        if not self.is_logged_in:
            return None

        try:
            students = self.data.get("dbi").get("students")
        except Exception as e:
            self.logger.warning("Couldn't fetch students from DBI!")
            return None
        if students is None:
            self.logger.warning("The list students is empty!")
            return []

        result = []
        for student_id in students:
            student_data = students.get(student_id)
            class_id = student_data.get("classid")
            firstname = student_data.get("firstname")
            lastname = student_data.get("lastname")
            gender = student_data.get("gender")
            date_from = student_data.get("datefrom")
            date_to = student_data.get("dateto")
            number_in_class = student_data.get("numberinclass")
            odbor_id = student_data.get("odborid")
            is_out = student_data.get("isOut")

            student = EduStudent(student_id, class_id, firstname, lastname,
                                 gender, date_from, date_to, number_in_class,
                                 odbor_id, is_out)
            result.append(student)

        self.logger.debug("Succesfully constructed list of students!")
        return result

    def get_teachers(self):
        if not self.is_logged_in:
            return None

        dbi = self.data.get("dbi")
        if dbi is None:
            self.logger.warning("DBI is none!")
            return None

        id_util = IdUtil(self.data)

        teachers = dbi.get("teachers")

        result = []
        for teacher_id in teachers:
            teacher_data = teachers.get(teacher_id)

            gender = teacher_data.get("gender")
            firstname = teacher_data.get("firstname")
            lastname = teacher_data.get("lastname")
            short = teacher_data.get("short")

            classroom_id = teacher_data.get("classroomid")
            if classroom_id != "":
                classroom_name = id_util.id_to_classroom(classroom_id)
            else:
                classroom_name = ""

            date_from = teacher_data.get("datefrom")
            date_to = teacher_data.get("dateto")

            is_out = teacher_data.get("isOut")

            teacher = EduTeacher(teacher_id, firstname, lastname, short, gender,
                                 classroom_id, classroom_name, date_from, date_to,
                                 is_out)
            result.append(teacher)
        self.logger.debug("Successfully constructed list of teachers!")
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
    def send_message(self, recipients, body, attachments=None):
        if attachments is None:
            attachments = []
        recipients_post_data = ""

        if type(recipients) == list:
            for i, recipient in enumerate(recipients, start=0):
                if i != 0:
                    recipients_post_data += f";{recipient.get_id()}"
                else:
                    recipients_post_data += recipient.get_id()
        else:
            recipients_post_data = recipients.get_id()

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

        self.session.post(f'https://{self.school}.edupage.org/timeline/',
                          headers=headers,
                          params=params,
                          data=RequestUtil.encode_form_data(data))
