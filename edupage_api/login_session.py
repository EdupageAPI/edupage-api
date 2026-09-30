import json
from json import JSONDecodeError
from typing import Optional

from edupage_api.compression import RequestData
from edupage_api.exceptions import BadCredentialsException, Base64DecodeError
from edupage_api.module import Module


class LoginSession(Module):
    """Session handling shared by `Login` and `TwoFactorLogin`."""

    @staticmethod
    def parse_rpc_response(text: str) -> Optional[dict]:
        if not text:
            return None

        try:
            decoded = RequestData.decode_response(text)
            return json.loads(decoded)
        except (Base64DecodeError, TypeError, JSONDecodeError):
            return None

    def parse_login_data(self, data: str):
        try:
            json_string = (
                data.split("userhome(", 1)[1]
                .rsplit(");", 2)[0]
                .replace("\t", "")
                .replace("\n", "")
                .replace("\r", "")
            )
        except IndexError:
            raise BadCredentialsException("EduPage did not return login data")

        self.edupage.data = json.loads(json_string)
        self.edupage.is_logged_in = True

        try:
            self.edupage.gsec_hash = data.split('ASC.gsechash="', 1)[1].split('"', 1)[0]
        except IndexError:
            self.edupage.gsec_hash = None

    def reload_data(self, subdomain: str, session_id: str, username: str):
        request_url = f"https://{subdomain}.edupage.org/user"

        # Only send the session cookie to this school's subdomain
        self.edupage.session.cookies.set(
            "PHPSESSID", session_id, domain=f"{subdomain}.edupage.org"
        )

        response = self.edupage.session.get(request_url)

        try:
            self.parse_login_data(response.content.decode())
            self.edupage.subdomain = subdomain
            self.edupage.username = username
        except (TypeError, JSONDecodeError) as e:
            raise BadCredentialsException(f"Invalid session id: {e}")
