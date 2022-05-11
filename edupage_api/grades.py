import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from edupage_api.dbi import DbiHelper
from edupage_api.exceptions import FailedToParseGradeDataError
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduTeacher


@dataclass
class EduGrade:
    event_id: int
    title: str
    grade_n: Optional[Union[int, float, str]]
    comment: Optional[str]
    date: datetime
    subject_id: int
    subject_name: Optional[str]
    teacher: Optional[EduTeacher]
    max_points: Optional[float]
    importance: float
    verbal: bool
    percent: float


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
            # ID
            event_id_str = grade.get("udalostid")
            if not event_id_str:
                continue

            event_id = int(event_id_str)

            # Title
            details = grade_details.get(event_id_str)
            title = details.get("p_meno")

            # Date
            date_str = grade.get("datum")
            date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

            # Subject ID and name
            subject_id_str = details.get("PredmetID")
            if subject_id_str is None or subject_id_str == "vsetky":
                continue

            subject_id = int(subject_id_str)
            subject_name = DbiHelper(self.edupage).fetch_subject_name(subject_id)

            # Teacher
            teacher_id_str = details.get("UcitelID")
            if teacher_id_str is None:
                teacher = None
            else:
                teacher_id = int(teacher_id_str)
                teacher_data = DbiHelper(self.edupage).fetch_teacher_data(teacher_id)

                if teacher_data is None:
                    teacher = None
                else:
                    teacher = EduTeacher.parse(teacher_data, teacher_id, self.edupage)

            # Maximal points and importance
            grade_type = details.get("p_typ_udalosti")
            if grade_type == "1":
                # Normal grade (1 – 5)
                max_points = None
                importance = float(details.get("p_vaha")) / 20
            elif grade_type == "2":
                # Points grade (in points – e.g. 0 – 20 points)
                max_points = int(details.get("p_vaha"))
                importance = None
            elif grade_type == "3":
                # Percental grade (0 – 100 %)
                max_points = int(details.get("p_vaha_body"))
                importance = float(details.get("p_vaha")) / 20

             # Grade
            grade_raw = grade.get("data").split(" (", 1)
            if grade_raw[0].isdigit():
                grade_n = float(grade_raw[0])
            else:
                grade_n = grade_raw[0]

            try:
                comment = grade_raw[1].rsplit(")", 1)[0]
            except IndexError:
                comment = None

            # Verbal and percents
            try:
                verbal = False

                if max_points:
                    percent = round(float(grade_n) / float(max_points) * 100, 2)
                elif max_points == 0:
                    percent = float("inf")
                else:
                    percent = None
            except:
                verbal = True

            grade = EduGrade(event_id, title, grade_n, comment, date, subject_id,
                             subject_name, teacher, max_points, importance, verbal, percent)
            output.append(grade)

        return output
