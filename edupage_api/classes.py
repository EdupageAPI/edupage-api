from dataclasses import dataclass
from typing import Optional

from edupage_api.classrooms import Classroom, Classrooms
from edupage_api.dbi import DbiHelper
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduTeacher, People


@dataclass
class Class:
    class_id: int
    name: str
    short: str
    homeroom_teachers: list[EduTeacher]
    homeroom: Classroom
    grade: int


class Classes(Module):
    @ModuleHelper.logged_in
    def get_classes(self) -> Optional[list]:
        classes_list = DbiHelper(self.edupage).fetch_class_list()

        if classes_list is None:
            return None

        classes = []

        for class_id_str in classes_list:
            if not class_id_str:
                continue

            home_teacher = People(self.edupage).get_teacher(
                classes_list[class_id_str]["teacherid"]
            )
            home_teacher2 = People(self.edupage).get_teacher(
                classes_list[class_id_str]["teacher2id"]
            )
            home_teachers = (
                [home_teacher, home_teacher2] if home_teacher2 else [home_teacher]
            )

            homeroom = Classrooms(self.edupage).get_classroom(
                int(classes_list[class_id_str]["classroomid"])
            )

            classes.append(
                Class(
                    int(class_id_str),
                    classes_list[class_id_str]["name"],
                    classes_list[class_id_str]["short"],
                    home_teachers,
                    homeroom,
                    int(classes_list[class_id_str]["grade"]),
                )
            )

        return classes

    def get_class(self, class_id: int) -> Optional[Class]:
        return next(
            (edu_class for edu_class in self.get_classes() if edu_class.class_id == class_id),
            None,
        )
