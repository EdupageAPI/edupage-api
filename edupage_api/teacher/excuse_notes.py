import json
from json import JSONDecodeError
from edupage_api.module import Module, ModuleHelper

class ExcuseNotes(Module):
    @ModuleHelper.logged_in
    def get_excuse_notes(self) -> dict:
        params = {
            "cmd": "HomeworkList",
            "module": "ospravedlnenky",
            "barNoSkin": "1",
            "ebuid": self.edupage.get_user_id()
        }

        response = self.edupage.session.get(f"https://{self.edupage.subdomain}.edupage.org/exam/", params=params)

        r = response.text
        r = r.split(".homeworklist(")[1].split(");")[0]

        try:
            excuse_notes = json.loads(r)
        except JSONDecodeError:
            raise Exception("134")

        return excuse_notes