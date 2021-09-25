from __future__ import annotations # for postponed evaluation of annotations
from typing import Union
from edupage_api.module import Module, ModuleHelper
from edupage_api.dbi import DbiHelper
from enum import Enum
from datetime import datetime

class Gender(Enum):
    MALE = "M"
    FEMALE = "F"

    @staticmethod
    def parse(gender_str: str) -> Union[Gender, None]:
        filtered = list(filter(lambda x: x.value == gender_str, list(Gender)))

        if not filtered:
            return None
        
        return filtered[0]



class EduAccountType(Enum):
    STUDENT = "Student"
    TEACHER = "Teacher"

class EduAccount:
    def __init__(self, person_id: int, name: str, gender: Gender, in_school_since: datetime, account_type: EduAccountType):
        self.person_id = person_id
        self.name = name
        self.gender = gender
        self.in_school_since = in_school_since

class EduStudent(EduAccount):
    def __init__(self, person_id: int, name: str, gender: Gender, in_school_since: datetime,
                class_id: int, number_in_class: int):
        super().__init__(person_id, name, gender, in_school_since, EduAccountType.STUDENT)

        self.class_id = class_id
        self.number_in_class = number_in_class

class EduTeacher(EduAccount):
    def __init__(self, person_id: int, name: str, gender: Gender, in_school_since: datetime,
                classroom_name: str):
        super().__init__(person_id, name, gender, in_school_since, EduAccountType.TEACHER)

        self.classroom_name = classroom_name

class People(Module):
    @ModuleHelper.logged_in
    def get_students(self) -> Union[list, None]:
        students = DbiHelper(self.edupage).fetch_student_list()
        if students is None:
            return None
        
        result = []
        for student_id_str in students:
            if not student_id_str:
                continue            

            student_id = int(student_id_str)

            student_data = students.get(student_id_str)

            class_id = ModuleHelper.int_or_none(student_data.get("classid"))
            name = DbiHelper(self.edupage).fetch_student_name(student_id)
            gender = Gender.parse(student_data.get("gender"))
            student_since = ModuleHelper.strptime_or_none(student_data.get("datefrom"), "%Y-%m-%d")
            number_in_class = ModuleHelper.int_or_none(student_data.get("numberinclass"))

            ModuleHelper.assert_none(name)
            
            student = EduStudent(student_id, name, gender, student_since, class_id, number_in_class)
            result.append(student)
        
        return result

    @ModuleHelper.logged_in
    def get_teacher(self, teacher_id: int) -> Union[EduTeacher, None]:
        teacher_data = DbiHelper(self.edupage).fetch_teacher_data(teacher_id)
        if teacher_data is None:
            return None

        classroom_id = teacher_data.get("classroomid")
        classroom_name =  DbiHelper(self.edupage).fetch_classroom_number(classroom_id) if ModuleHelper.int_or_none(classroom_id) else ""

        name = DbiHelper(self.edupage).fetch_teacher_name(teacher_id)
        gender = Gender.parse(teacher_data.get("gender"))
        teacher_since = datetime.strptime(teacher_data.get("datefrom"), "%Y-%m-%d")

        ModuleHelper.assert_none(gender)

        return EduTeacher(teacher_id, name, gender, teacher_since, classroom_name)

    
    @ModuleHelper.logged_in
    def get_student(self, student_id: int) -> Union[EduStudent, None]:
        student_data = DbiHelper(self.edupage).fetch_student_data(student_id)
        if student_data is None:
            return None

        class_id = ModuleHelper.int_or_none(student_data.get("classid"))
        name = DbiHelper(self.edupage).fetch_student_name(student_id)
        gender = Gender.parse(student_data.get("gender"))
        student_since = ModuleHelper.strptime_or_none(student_data.get("datefrom"), "%Y-%m-%d")
        number_in_class = ModuleHelper.int_or_none(student_data.get("numberinclass"))

        ModuleHelper.assert_none(name)
        
        return EduStudent(student_id, name, gender, student_since, class_id, number_in_class)
    
    @ModuleHelper.logged_in
    def get_teachers(self) -> Union[list, None]:
        teachers = DbiHelper(self.edupage).fetch_teacher_list()
        if teachers is None:
            return None
        
        result = []
        for teacher_id_str in teachers:
            if not teacher_id_str:
                continue

            teacher_id = int(teacher_id_str)

            teacher_data = teachers.get(teacher_id_str)

            classroom_id = teacher_data.get("classroomid")
            classroom_name =  DbiHelper(self.edupage).fetch_classroom_number(classroom_id) if ModuleHelper.int_or_none(classroom_id) else ""

            name = DbiHelper(self.edupage).fetch_teacher_name(teacher_id)
            gender = Gender.parse(teacher_data.get("gender"))
            teacher_since = datetime.strptime(teacher_data.get("datefrom"), "%Y-%m-%d")

            ModuleHelper.assert_none(gender)

            teacher = EduTeacher(teacher_id, name, gender, teacher_since, classroom_name)
            result.append(teacher)
        
        return result