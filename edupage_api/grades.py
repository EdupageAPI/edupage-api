from edupage_api.date import EduExactDateTime


# This is just a message that a grade has been received
# and it contains no information about what the grade is.
class EduGradeEvent:
    def __init__(self, teacher, title, subject, average, weight,
                 datetime_added):
        self.teacher = teacher
        self.title = title
        self.subject = subject
        self.average = average
        self.weight = weight
        self.datetime_added = EduExactDateTime.from_formatted_string(
            datetime_added)

    def __str__(self):
        return f'{self.title}: {self.average}'


class EduGrade:
    def __init__(self, event_id, title, grade, importance, datetime_added, subject, teacher, percent, verbal,
                 max_points):
        self.id = event_id
        self.title = title
        self.grade = grade
        self.importance = importance
        self.datetime_added = EduExactDateTime.from_formatted_string(datetime_added)
        self.subject = subject
        self.teacher = teacher
        self.percent = percent
        self.verbal = verbal
        self.max_points = max_points

    def __str__(self):
        return f'{self.title}: {self.grade}'
