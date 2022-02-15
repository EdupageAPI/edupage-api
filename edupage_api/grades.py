import json
from datetime import datetime

from edupage_api.dbi import DbiHelper
from edupage_api.exceptions import FailedToParseGradeDataError
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduTeacher


class EduGrade:
    def __init__(self, event_id: int, title: str, grade_n: int,
                 date: datetime, subject_id: int, subject_name: str,
                 teacher: EduTeacher, max_points: float, importance: float,
                 verbal: True, percent: float):
        self.event_id = event_id
        self.title = title
        self.grade_n = grade_n
        self.date = date
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.teacher = teacher
        self.max_points = max_points
        self.importance = importance
        self.verbal = verbal
        self.percent = percent


class Grades(Module):
    def __parse_grade_data(self, data: str) -> dict:
        json_string = data.split(".znamkyStudentViewer(")[1] \
                          .split(");\r\n\t\t});\r\n\t\t</script>")[0]

        return json.loads(json_string)

    def __get_grade_data(self):
        request_url = f"https://{self.edupage.subdomain}.edupage.org/znamky/"

        response = self.edupage.session.get(request_url).content.decode()

        try:
            return self.__parse_grade_data(response)
        except json.JSONDecodeError:
            raise FailedToParseGradeDataError("Failed to parse JSON")

    @ModuleHelper.logged_in
    def get_grades(self) -> list[EduGrade]:
        grade_data = self.__get_grade_data()

        grades = grade_data.get("vsetkyZnamky")
        grade_details = grade_data.get("vsetkyUdalosti").get("edupage")

        output = []
        for grade in grades:
            event_id_str = grade.get("udalostid")
            if not event_id_str:
                continue

            event_id = int(event_id_str)

            details = grade_details.get(event_id_str)
            title = details.get("p_meno")

            grade_n = ModuleHelper.parse_int(grade.get("data"))

            date_str = grade.get("datum")
            date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

            subject_id_str = details.get("PredmetID")
            if subject_id_str is None or subject_id_str == "vsetky":
                continue

            subject_id = int(subject_id_str)
            subject_name = DbiHelper(self.edupage).fetch_subject_name(subject_id)

            teacher_id_str = details.get("UcitelID")
            if teacher_id_str is None:
                teacher = None
            else:
                teacher_id = int(teacher_id_str)
                teacher_data = DbiHelper(self.edupage).fetch_teacher_data(teacher_id)

                teacher = EduTeacher.parse(teacher_data, teacher_id, self.edupage)

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

            grade = EduGrade(event_id, title, grade_n, date, subject_id,
                             subject_name, teacher, max_points, importance, verbal, percent)
            output.append(grade)

        return output
