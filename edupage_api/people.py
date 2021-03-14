class EduStudent:
    def __init__(self, gender, firstname, lastname, student_id, number,
                 is_out):
        self.gender = gender
        self.firstname = firstname
        self.lastname = lastname
        self.fullname = firstname + " " + lastname
        self.id = int(student_id)
        self.number_in_class = int(number)
        self.is_out = is_out

    def __sort__(self):
        return self.number_in_class

    def __str__(self):
        return "{gender: %s, name: %s, id: %d, number: %s, is_out: %s}" % (
            self.gender, self.fullname, self.id, self.number_in_class,
            self.is_out)


class EduTeacher:
    def __init__(self, gender, firstname, lastname, teacher_id, classroom,
                 is_out):
        self.gender = gender
        self.firstname = firstname
        self.lastname = lastname
        self.fullname = firstname + " " + lastname
        self.id = int(teacher_id)
        self.classroom = classroom
        self.is_out = is_out

    def __str__(self):
        return "{gender: %s, name: %s, id: %d, classroom: %s, is_out: %s}" % (
            self.gender, self.fullname, self.id, self.classroom, self.is_out)
