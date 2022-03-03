from typing import Union

from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduAccount


class Messages(Module):
    def send_message(self, recipients: Union[list[EduAccount], EduAccount], body: str):
        recipient_string = ""

        if isinstance(recipients, list):
            for i, recipient in enumerate(recipients):
                recipient_string += f"{recipient.get_id()}"
                if i == len(recipients) - 1:
                    recipient_string += ";"
        else:
            recipient_string = recipients.get_id()

        data = {
            "receipt": "0",
            "selectedUser": recipient_string,
            "text": body,
            "typ": "sprava",
            "attachments": "{}"
        }

        params = (
            ("akcia", "createItem"),
        )

        request_url = f"https://{self.edupage.subdomain}.edupage.org/timeline"
        self.edupage.session.post(request_url, params=params,
                                  data=ModuleHelper.encode_form_data(data))
