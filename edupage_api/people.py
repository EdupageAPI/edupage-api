class EduStudent:
    def __init__(self, student_id, class_id, firstname, lastname, gender, date_from, date_to, number_in_class, odbor_id,
                 is_out):
        self.id = int(student_id)
        self.class_id = int(class_id)
        self.firstname = firstname
        self.lastname = lastname
        self.fullname = firstname + " " + lastname
        self.gender = gender
        self.date_from = date_from
        self.date_to = date_to
        self.number_in_class = number_in_class
        self.odbor_id = odbor_id
        self.is_out = is_out

        try:
            self.number_in_class = int(number_in_class)
        except ValueError:
            self.number_in_class = None

    def get_id(self):
        return f"Student{str(self.id)}"

    def __str__(self):
        return f"{self.id} | {self.fullname}"

    def __sort__(self):
        return self.number_in_class


class EduTeacher:
    def __init__(self, teacher_id, firstname, lastname, short, gender, classroom_id, classroom_name, date_from, date_to,
                 is_out):
        self.id = int(teacher_id)
        self.firstname = firstname
        self.lastname = lastname
        self.fullname = firstname + " " + lastname
        self.short = short
        self.gender = gender
        self.classroom_id = classroom_id
        self.classroom_name = classroom_name
        self.date_from = date_from
        self.date_to = date_to
        self.is_out = is_out

    def get_id(self):
        return f"Ucitel{str(self.id)}"

    def __str__(self):
        return f"{self.id} | {self.fullname}"

    def __sort__(self):
        return self.id
