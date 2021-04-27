import datetime, json
from edupage_api.utils import LessonUtil


class EduLesson:
    def __init__(self, period, name, subject_id, teacher, classroom, length):
        self.period = period
        self.name = name
        self.teacher = teacher
        self.classroom = classroom
        self.length = length
        self.subject_id = subject_id

    def __str__(self):
        return str(self.__dict__)


class EduOnlineLesson(EduLesson):
    def __init__(self, period, name, subject_id, teacher, classroom, length,
                 online_lesson_link):
        super().__init__(period, name, subject_id, teacher, classroom, length)
        self.online_lesson_link = online_lesson_link

    # Tell edupage that you are on this online lesson
    def signIntoLesson(self, edupage):
        request_url = "https://" + edupage.school + ".edupage.org/dashboard/eb.php"

        response = edupage.session.get(request_url)

        # we will need this for the next request
        gse_hash = response.content.decode() \
                                        .split("gsechash=")[1] \
                                        .split('"')[1]  # I have no idea what this is, but it can be easily parsed

        request_url = "https://" + edupage.school + ".edupage.org/dashboard/server/onlinelesson.js?__func=getOnlineLessonOpenUrl"

        today = datetime.datetime.now()
        post_data = {
            "__args": [  # wtf is this name
                None,  # The first element is always null???
                {
                    "click": True,
                    "date": today.strftime("%Y-%m-%d"),
                    "ol_url": self.online_lesson_link,
                    "subjectid": self.subject_id
                }
            ],
            "__gsh":
            gse_hash
        }

        response = edupage.session.post(request_url, json=post_data)
        # if reload is True, request failed: the gsh hash was wrong:(
        return json.loads(response.content.decode()).get("reload") == None


class EduTimetable:
    def __init__(self, lessons):
        self.lessons = lessons
        
    class Lesson:
        def getAtTime(self, edutime):
            for lesson in self.lessons:
                if edutime.afterOrEquals(lesson.length.start) and edutime.beforeOrEquals(lesson.length.end):
                    return lesson

            return None

    class NextLesson:
        def getAtTime(self, edutime):
            for lesson in self.lessons:
                if edutime.before(lesson.length.start):
                    return lesson

            return None

        def getOnlineAtTime(self, edutime):
            for lesson in self.lessons:
                if edutime.before(lesson.length.start):
                    if LessonUtil.isOnlineLesson(lesson):
                        return lesson

            return None

    def getFirstLesson(self):
        return self.lessons[0]

    def getLastLesson(self):
        return self.lessons[-1]
