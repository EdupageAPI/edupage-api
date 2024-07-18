from dataclasses import dataclass
from typing import Optional, Union

from edupage_api.dbi import DbiHelper
from edupage_api.module import Module, ModuleHelper


@dataclass
class Classroom:
    classroom_id: int
    name: str
    short: str


class Classrooms(Module):
    @ModuleHelper.logged_in
    def get_classrooms(self) -> Optional[list]:
        classroom_list = DbiHelper(self.edupage).fetch_classroom_list()

        if classroom_list is None:
            return None

        classrooms = []

        for classroom_id_str in classroom_list:
            if not classroom_id_str:
                continue

            classrooms.append(
                Classroom(
                    int(classroom_id_str),
                    classroom_list[classroom_id_str]["name"],
                    classroom_list[classroom_id_str]["short"],
                )
            )

        return classrooms

    def get_classroom(self, classroom_id: Union[int, str]) -> Optional[Classroom]:
        try:
            classroom_id = int(classroom_id)
        except (ValueError, TypeError):
            return None

        return next(
            (
                classroom
                for classroom in self.get_classrooms()
                if classroom.classroom_id == classroom_id
            ),
            None,
        )
