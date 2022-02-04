import json
import urllib.parse


class GradeUtil:
    def __init__(self, grade_data):
        self.data = grade_data

    def id_to_teacher(self, teacher_id):
        if teacher_id is None:
            return None

        try:
            teachers = self.data.get("ucitelia")

            # This dict contains data about the
            # date when this teacher was employed
            # or when will he/she retire / is planned quit this job
            # (datefrom, dateto)
            teacher = teachers.get(teacher_id)

            teacher_name = teacher.get("firstname") + " " + teacher.get("lastname")
        except:
            teacher_name = None

        return teacher_name


class LessonUtil:
    @staticmethod
    def is_online_lesson(lesson):
        # We cannot import from timetables.py because of circular import
        return "EduOnlineLesson" in str(type(lesson))


class IdUtil:
    def __init__(self, data):
        self.data = data
        self.dbi = data.get("dbi")

    def id_to_class(self, c_id):
        if c_id is None:
            return None

        try:
            class_name = self.dbi.get("classes").get(c_id).get("name")
        except:
            class_name = None

        return class_name

    def id_to_teacher(self, t_id):
        if t_id is None:
            return None

        try:
            teacher_data = self.dbi.get("teachers").get(t_id)
            teacher_full_name = teacher_data.get(
                "firstname") + " " + teacher_data.get("lastname")
        except:
            teacher_full_name = None

        return teacher_full_name

    def id_to_classroom(self, c_id):
        if c_id is None:
            return None

        try:
            classroom = self.dbi.get("classrooms").get(c_id).get("short")
        except:
            classroom = None

        return classroom

    def id_to_subject(self, s_id):
        if s_id is None:
            return s_id

        try:
            subject = self.dbi.get("subjects").get(s_id).get("short")
        except:
            subject = None

        return subject


class RequestUtil:
    @staticmethod
    def urlencode(string):
        return urllib.parse.quote(string)

    @staticmethod
    def encode_form_data(data):
        output = ""
        for i, key in enumerate(data.keys(), start=0):
            value = data[key]
            entry = f"{RequestUtil.urlencode(key)}={RequestUtil.urlencode(value)}"

            output += f"&{entry}" if i != 0 else entry
        return output

    @staticmethod
    def encode_attachments(attachments):
        output = {attachment.url: attachment.filename for attachment in attachments}

        return json.dumps(output)
