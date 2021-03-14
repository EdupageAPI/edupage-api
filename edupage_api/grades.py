from edupage_api.date import EduDateTime


# This is just a message that a grade has been received
# and it contains no information about what the grade is.
class EduGradeEvent:
    def __init__(self, teacher, title, subject, average, weight,
                 datetime_added):
        self.teacher = teacher
        self.title = title
        self.subject = subject
        self.average = average
        self.datetime_added = EduDateTime.from_formatted_datetime(
            datetime_added)

    def __str__(self):
        return f'{self.title}: {self.average}'
