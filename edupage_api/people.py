class EduUser:
    def __init__(self, gender, firstname, lastname, p_id, is_out):
        self.gender = gender
        self.firstname = firstname
        self.lastname = lastname
        self.fullname = firstname + " " + lastname
        self.id = int(p_id)
        self.is_out = is_out

    def get_id(self):
        raise NotImplementedError()

    def __str__(self):
        return str(self.__dict__)


class EduStudent(EduUser):
    def __init__(self, gender, firstname, lastname, student_id, number,
                 is_out):
        super().__init__(gender, firstname, lastname, student_id, is_out)
        try:
            self.number_in_class = int(number)
        except ValueError:
            self.number_in_class = None

    def get_id(self):
        return f"Student{str(self.id)}"

    def __sort__(self):
        return self.number_in_class


class EduTeacher(EduUser):
    def __init__(self, gender, firstname, lastname, teacher_id, classroom,
                 is_out):
        super().__init__(gender, firstname, lastname, teacher_id, is_out)

    def get_id(self):
        return f"Ucitel{str(self.id)}"