from dataclasses import dataclass
from typing import Optional, Union

from edupage_api.dbi import DbiHelper
from edupage_api.module import Module, ModuleHelper


@dataclass
class Subject:
    subject_id: int
    name: str
    short: str


class Subjects(Module):
    @ModuleHelper.logged_in
    def get_subjects(self) -> Optional[list]:
        subject_list = DbiHelper(self.edupage).fetch_subject_list()

        if subject_list is None:
            return None

        subjects = []

        for subject_id_str in subject_list:
            if not subject_id_str:
                continue

            subjects.append(
                Subject(
                    int(subject_id_str),
                    subject_list[subject_id_str]["name"],
                    subject_list[subject_id_str]["short"],
                )
            )

        return subjects

    def get_subject(self, subject_id: Union[int, str]) -> Optional[Subject]:
        try:
            subject_id = int(subject_id)
        except (ValueError, TypeError):
            return None

        return next(
            (
                subject
                for subject in self.get_subjects()
                if subject.subject_id == subject_id
            ),
            None,
        )
