from dataclasses import dataclass
from typing import Optional, Union

from edupage_api.classrooms import Classroom, Classrooms
from edupage_api.dbi import DbiHelper
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduTeacher, People


@dataclass
class Class:
    class_id: int
    name: str
    short: str
    homeroom_teachers: Optional[list[EduTeacher]]
    homeroom: Optional[Classroom]
    grade: Optional[int]


class Classes(Module):
    @ModuleHelper.logged_in
    def get_classes(self) -> Optional[list]:
        classes_list = DbiHelper(self.edupage).fetch_class_list()

        if classes_list is None:
            return None

        classes = []

        for class_id_str, class_info in classes_list.items():
            if not class_id_str:
                continue

            home_teacher_ids = [
                class_info.get("teacherid"),
                class_info.get("teacher2id"),
            ]
            home_teachers = [
                People(self.edupage).get_teacher(tid) for tid in home_teacher_ids if tid
            ]
            home_teachers = [ht for ht in home_teachers if ht]

            homeroom_id = class_info.get("classroomid")
            homeroom = Classrooms(self.edupage).get_classroom(homeroom_id)

            classes.append(
                Class(
                    int(class_id_str),
                    class_info["name"],
                    class_info["short"],
                    home_teachers if home_teachers else None,
                    homeroom,
                    int(class_info["grade"]) if class_info["grade"] else None,
                )
            )

        return classes

    def get_class(self, class_id: Union[int, str]) -> Optional[Class]:
        try:
            class_id = int(class_id)
        except (ValueError, TypeError):
            return None

        return next(
            (
                edu_class
                for edu_class in self.get_classes()
                if edu_class.class_id == class_id
            ),
            None,
        )
