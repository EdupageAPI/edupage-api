from edupage_api.module import EdupageModule, ModuleHelper
from edupage_api.teacher.excuse_notes import ExcuseNotes


class TeacherEdupage:
    def __init__(self, edupage: EdupageModule):
        self.edupage = edupage

        my_user_id = self.edupage.get_user_id()

        self.is_teacher = "Ucitel" not in my_user_id and "Admin" not in my_user_id

    def get_excuse_notes(self):
        return ExcuseNotes(self.edupage).get_excuse_notes()

