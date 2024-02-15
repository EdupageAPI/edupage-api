import json
from json import JSONDecodeError

from edupage_api.exceptions import BadCredentialsException
from edupage_api.module import Module


class Login(Module):
    def __parse_login_data(self, data):
        json_string = (
            data.split("userhome(", 1)[1]
            .rsplit(");", 2)[0]
            .replace("\t", "")
            .replace("\n", "")
            .replace("\r", "")
        )

        self.edupage.data = json.loads(json_string)
        self.edupage.is_logged_in = True

        self.edupage.gsec_hash = data.split('ASC.gsechash="')[1].split('"')[0]

    def login(self, username: str, password: str, subdomain: str = "login1"):
        """Login to your school's Edupage account.
        If the subdomain is not specified, the https://login1.edupage.org is used.

        Args:
            username (str): Your username.
            password (str): Your password.
            subdomain (str): Subdomain of your school (https://{subdomain}.edupage.org).

        Raises:
            BadCredentialsException: Your credentials are invalid.
        """

        request_url = f"https://{subdomain}.edupage.org/login/index.php"

        response = self.edupage.session.get(request_url)
        data = response.content.decode()

        csrf_token = data.split('name="csrfauth" value="')[1].split('"')[0]

        parameters = {
            "csrfauth": csrf_token,
            "username": username,
            "password": password,
        }

        request_url = f"https://{subdomain}.edupage.org/login/edubarLogin.php"

        response = self.edupage.session.post(request_url, parameters)
        data = response.content.decode()

        if "bad=1" in response.url:
            raise BadCredentialsException()

        if subdomain == "login1":
            subdomain = data.split("-->")[0].split(" ")[-1]

        self.__parse_login_data(data)
        self.edupage.subdomain = subdomain
        self.edupage.username = username

    def reload_data(self, subdomain: str, session_id: str, username: str):
        request_url = f"https://{subdomain}.edupage.org/user"

        self.edupage.session.cookies.set("PHPSESSID", session_id)

        response = self.edupage.session.get(request_url)

        try:
            self.__parse_login_data(response.content.decode())
            self.edupage.subdomain = subdomain
            self.edupage.username = username
        except (TypeError, JSONDecodeError) as e:
            raise BadCredentialsException(f"Invalid session id: {e}")
