from typing import Union
import json

from edupage_api.exceptions import InvalidRecipientsException, RequestError
from edupage_api.module import Module
from edupage_api.people import EduAccount
from edupage_api.compression import RequestData

class Messages(Module):
    def send_message(self, recipients: Union[list[EduAccount], EduAccount, list[str]], body: str) -> int:
        recipient_string = ""

        if isinstance(recipients, list):
            if len(recipients) == 0:
                raise InvalidRecipientsException("The recipients parameter is empty!")

            if type(recipients[0]) == EduAccount:
                recipient_string = ";".join([r.get_id() for r in recipients])
            else:
                recipient_string = ";".join(recipients)
        else:
            recipient_string = recipients.get_id()

        data = RequestData.encode_request_body({
            "selectedUser": recipient_string,
            "text": body,
            "attachements": "{}",
            "receipt": "0",
            "typ": "sprava",
        })

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        request_url = f"https://{self.edupage.subdomain}.edupage.org/timeline/?=&akcia=createItem&eqav=1&maxEqav=7"
        response = self.edupage.session.post(request_url, data=data, headers=headers)

        response_text = RequestData.decode_response(response.text)
        if response_text == "0":
            raise RequestError("Edupage returned an error response")
        
        response = json.loads(response_text)
        
        changes = response.get("changes")
        if changes == [] or changes is None:
            raise RequestError("Failed to send message (edupage returned an empty 'changes' array) - https://github.com/ivanhrabcak/edupage-api/issues/62")
        
        return int(changes[0].get("timelineid"))