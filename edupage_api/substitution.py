import json

from datetime import date
from edupage_api.exceptions import ExpiredSessionException, InvalidTeacherException
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduTeacher, People


class Substitution(Module):
    @ModuleHelper.logged_in
    def get_missing_teachers(self, date: date) -> list[EduTeacher]:
        url = f"https://{self.edupage.subdomain}.edupage.org/substitution/server/viewer.js?__func=getSubstViewerDayDataHtml"

        data = {
            "__args": [None, {
                "date": date.strftime("%Y-%m-%d"),
                "mode": "classes"
            }],
            "__gsh": self.edupage.gsec_hash
        }

        response = self.edupage.session.post(url, json=data).content.decode()
        response = json.loads(response)

        if response.get("reload"):
            raise ExpiredSessionException("Invalid gsec hash! (Expired session, try logging in again!)")

        html = response.get("r")
        missing_teachers_string = html.split("<span class=\"print-font-resizable\">")[1].split("</span>")[0]

        _title, missing_teachers = missing_teachers_string.split(": ")

        all_teachers = People(self.edupage).get_teachers()

        missing_teachers = [t.strip() for t in missing_teachers.split(", ")]
        try:
            missing_teachers = [list(filter(lambda x: x.name == t, all_teachers))[0] for t in missing_teachers]
        except IndexError:
            raise InvalidTeacherException("Invalid teacher in substitution! (The teacher is no longer frequenting this school)")

        return missing_teachers
