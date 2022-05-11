# For postponed evaluation of annotations
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from edupage_api.dbi import DbiHelper
from edupage_api.module import EdupageModule, Module, ModuleHelper


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"

    @staticmethod
    def parse(gender_str: str) -> Optional[Gender]:
        return ModuleHelper.parse_enum(gender_str, Gender)


class EduAccountType(str, Enum):
    STUDENT = "Student"
    TEACHER = "Teacher"
    PARENT = "Rodic"


@dataclass
class EduAccount:
    person_id: int
    name: str
    gender: Gender
    in_school_since: datetime
    account_type: EduAccountType

    @staticmethod
    def recognize_account_type(person_data: dict) -> EduAccountType:
        if person_data.get("numberinclass") is not None:
            return EduAccountType.STUDENT
        elif person_data.get("classroomid") is not None:
            return EduAccountType.TEACHER
        else:
            return EduAccountType.PARENT

    @staticmethod
    def parse(person_data: dict, person_id: int, edupage: EdupageModule) -> Optional[EduAccount]:
        account_type = EduAccount.recognize_account_type(person_data)

        if account_type == EduAccountType.STUDENT:
            class_id = ModuleHelper.parse_int(person_data.get("classid"))
            name = DbiHelper(edupage).fetch_student_name(person_id)
            gender = Gender.parse(person_data.get("gender"))
            student_since = ModuleHelper.strptime_or_none(person_data.get("datefrom"), "%Y-%m-%d")
            number_in_class = ModuleHelper.parse_int(person_data.get("numberinclass"))

            ModuleHelper.assert_none(name)

            return EduStudent(person_id, name, gender, student_since, class_id, number_in_class)
        elif account_type == EduAccountType.TEACHER:
            classroom_id = person_data.get("classroomid")
            classroom_name = DbiHelper(edupage).fetch_classroom_number(
                classroom_id) if ModuleHelper.parse_int(classroom_id) else ""

            name = DbiHelper(edupage).fetch_teacher_name(person_id)

            gender = Gender.parse(person_data.get("gender"))
            if teacher_since_str := person_data.get("datefrom"):
                teacher_since = datetime.strptime(teacher_since_str, "%Y-%m-%d")
            else:
                teacher_since = None

            if teacher_to_str := person_data.get("dateto"):
                teacher_to = datetime.strptime(teacher_to_str, "%Y-%m-%d")
            else:
                teacher_to = None

            return EduTeacher(person_id, name, gender, teacher_since, classroom_name, teacher_to)
        else:
            return None

    def get_id(self):
        return f"{self.account_type.value}-{self.person_id}"


@dataclass
class EduStudent(EduAccount):
    def __init__(self, person_id: int, name: str, gender: Gender, in_school_since: datetime,
                 class_id: int, number_in_class: int):
        super().__init__(person_id, name, gender, in_school_since, EduAccountType.STUDENT)

        self.class_id = class_id
        self.number_in_class = number_in_class


@dataclass
class EduStudentSkeleton:
    person_id: int
    name_short: str
    class_id: int


@dataclass
class EduParent(EduAccount):
    def __init__(self, person_id: int, name: str, gender: Gender, in_school_since: datetime):
        super().__init__(person_id, name, gender, in_school_since, EduAccountType.PARENT)


@dataclass
class EduTeacher(EduAccount):
    def __init__(self, person_id: int, name: str, gender: Gender, in_school_since: datetime,
                 classroom_name: str, teacher_to: datetime):
        super().__init__(person_id, name, gender, in_school_since, EduAccountType.TEACHER)

        self.teacher_to = teacher_to
        self.classroom_name = classroom_name


class People(Module):
    @ModuleHelper.logged_in
    def get_students(self) -> Optional[list]:
        students = DbiHelper(self.edupage).fetch_student_list()
        if students is None:
            return None

        result = []
        for student_id_str in students:
            if not student_id_str:
                continue

            student_id = int(student_id_str)
            student_data = students.get(student_id_str)

            student = EduAccount.parse(student_data, student_id, self.edupage)
            result.append(student)

        return result

    @ModuleHelper.logged_in
    def get_all_students(self) -> Optional[list[EduStudent]]:
        request_url = f"https://{self.edupage.subdomain}.edupage.org/rpr/server/maindbi.js?__func=mainDBIAccessor"
        data = {
            "__args": [
                None,
                self.edupage.get_school_year(),
                {},
                {
                    "op": "fetch",
                    "needed_part": {
                        "students": ["id", "classid", "short"],
                    }
                }
            ],
            "__gsh": self.edupage.gsec_hash
        }

        response = self.edupage.session.post(request_url, json=data).content.decode()
        students = json.loads(response).get("r").get("tables")[0].get("data_rows")

        result = []
        for student in students:
            student_id = int(student["id"])
            student_class_id = int(student["classid"]) if student["classid"] else None
            student_name_short = student["short"]

            student = EduStudentSkeleton(student_id, student_name_short, student_class_id)
            result.append(student)

        return result

    @ModuleHelper.logged_in
    def get_teacher(self, teacher_id: int) -> Optional[EduTeacher]:
        teacher_data = DbiHelper(self.edupage).fetch_teacher_data(teacher_id)
        if teacher_data is None:
            return None

        return EduAccount.parse(teacher_data, teacher_id, self.edupage)

    @ModuleHelper.logged_in
    def get_student(self, student_id: int) -> Optional[EduStudent]:
        student_data = DbiHelper(self.edupage).fetch_student_data(student_id)
        if student_data is None:
            return None

        return EduAccount.parse(student_data, student_id, self.edupage)

    @ModuleHelper.logged_in
    def get_teachers(self) -> Optional[list]:
        teachers = DbiHelper(self.edupage).fetch_teacher_list()
        if teachers is None:
            return None

        result = []
        for teacher_id_str in teachers:
            if not teacher_id_str:
                continue

            teacher_id = int(teacher_id_str)
            teacher_data = teachers.get(teacher_id_str)

            teacher = EduAccount.parse(teacher_data, teacher_id, self.edupage)
            result.append(teacher)

        return result
