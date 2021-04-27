import gzip, base64
import urllib.parse, json
from pprint import pprint


class GradeUtil:
    def __init__(self, grade_data):
        self.data = grade_data

    def idToTeacher(self, teacher_id):
        if teacher_id == None:
            return None

        teachers = self.data.get("ucitelia")

        # this dict contains data about the
        # date when this teacher was employed
        # or when will he/she retire / is planned quit this job
        # (datefrom, dateto)
        teacher = teachers.get(teacher_id)

        teacher_name = teacher.get("firstname") + " " + teacher.get("lastname")

        return teacher_name


class LessonUtil:
    @staticmethod
    def isOnlineLesson(lesson):
        # We cannot import from timetables.py because of circular import
        return "EduOnlineLesson" in str(type(lesson)) 


class IdUtil:
    def __init__(self, data):
        self.data = data
        self.dbi = data.get("dbi")

    def idToClass(self, c_id):
        if c_id == None:
            return None

        return self.dbi.get("classes").get(c_id).get("name")

    def idToTeacher(self, t_id):
        if t_id == None:
            return None

        teacher_data = self.dbi.get("teachers").get(t_id)
        teacher_full_name = teacher_data.get(
            "firstname") + " " + teacher_data.get("lastname")
        return teacher_full_name

    def idToClassroom(self, c_id):
        if c_id == None:
            return None
        return self.dbi.get("classrooms").get(c_id).get("short")

    def idToSubject(self, s_id):
        if s_id == None:
            return s_id
        return self.dbi.get("subjects").get(s_id).get("short")


class RequestUtil:
    @staticmethod
    def urlencode(string):
        return urllib.parse.quote(string)

    @staticmethod
    def encodeFormData(data):
        output = ""
        for i, key in enumerate(data.keys(), start=0):
            value = data[key]
            entry = f"{RequestUtil.urlencode(key)}={RequestUtil.urlencode(value)}"

            if i != 0:
                output += f"&{entry}"
            else:
                output += entry

        return output

    @staticmethod
    def encodeAttachments(attachments):
        output = {}

        for attachment in attachments:
            output[attachment.url] = attachment.filename

        return json.dumps(output)
