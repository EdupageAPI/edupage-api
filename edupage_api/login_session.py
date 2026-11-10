import json
from html.parser import HTMLParser
from json import JSONDecodeError
from typing import Optional

from edupage_api.compression import RequestData
from edupage_api.exceptions import BadCredentialsException, Base64DecodeError
from edupage_api.module import Module


class _AccountRows(HTMLParser):
    """Read server-issued account identifiers without executing page scripts."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "edubarChangeEdurowBtn" in attrs.get("class", "").split():
            row = attrs.get("data-rowid", "")
            if row:
                self.rows.append(row)


class LoginSession(Module):
    """Session handling shared by `Login` and `TwoFactorLogin`."""

    @staticmethod
    def parse_rpc_response(text: str) -> dict | None:
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
        rows = _AccountRows()
        rows.feed(data)
        self.edupage._account_rows = rows.rows
        self.edupage.is_logged_in = True

        try:
            self.edupage.gsec_hash = data.split('ASC.gsechash="', 1)[1].split('"', 1)[0]
        except IndexError:
            self.edupage.gsec_hash = None

    def logout(self):
        if self.edupage.is_logged_in:
            self.edupage.session.post(
                f"https://{self.edupage.subdomain}.edupage.org/login/logout.php"
            )

        self.edupage.session.cookies.clear()
        self.edupage.data = None
        self.edupage.is_logged_in = False
        self.edupage.subdomain = None
        self.edupage.gsec_hash = None
        self.edupage.username = None
        self.edupage._selected_child_id = None
        self.edupage._account_rows = []

    def reload_data(self, subdomain: str, session_id: str, username: str):
        request_url = f"https://{subdomain}.edupage.org/user"

        # Only send the session cookie to this school's subdomain
        self.edupage.session.cookies.set(
            "PHPSESSID", session_id, domain=f"{subdomain}.edupage.org"
        )

        # Do not leave a previous successful login marked valid after failure.
        self.edupage.is_logged_in = False
        self.edupage.data = None
        self.edupage._account_rows = []
        response = self.edupage.session.get(request_url)

        try:
            self.parse_login_data(response.content.decode())
            self.edupage.subdomain = subdomain
            self.edupage.username = username
        except (TypeError, JSONDecodeError) as e:
            raise BadCredentialsException(f"Invalid session id: {e}")
