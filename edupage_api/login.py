import json
from json import JSONDecodeError

from edupage_api.exceptions import BadCredentialsException
from edupage_api.module import Module


class Login(Module):
    def __parse_login_data(self, data):
        json_string = (data.split("userhome(", 1)[1]
                           .rsplit(");", 2)[0]
                           .replace("\t", "")
                           .replace("\n", "")
                           .replace("\r", ""))

        self.edupage.data = json.loads(json_string)
        self.edupage.is_logged_in = True

        self.edupage.gsec_hash = data.split("ASC.gsechash=\"")[1].split("\"")[0]

    def login_auto(self, username: str, password: str):
        """Login using https://portal.edupage.org. If this doesn't work, please use `Login.login`.

        Args:
            username (str): Your username.
            password (str): Your password.

        Raises:
            BadCredentialsException: Your credentials are invalid.
        """

        parameters = {
            "meno": username,
            "heslo": password,
            "akcia": "login"
        }

        request_url = "https://portal.edupage.org/index.php?jwid=jw2&module=login"
        response = self.edupage.session.post(request_url, params=parameters)
        data = response.content.decode()

        if "wrongPassword" in response.url or "errorbox" in data:
            raise BadCredentialsException()

        self.__parse_login_data(data)
        self.edupage.subdomain = data.split("-->")[0].split(" ")[-1]

    def login(self, username: str, password: str, subdomain: str):
        """Login while specifying the subdomain to log into.

        Args:
            username (str): Your username.
            password (str): Your password.
            subdomain (str): Subdomain of your school (https://{subdomain}.edupage.org).

        Raises:
            BadCredentialsException: Your credentials are invalid.
        """

        request_url = f"https://{subdomain}.edupage.org/login/index.php"

        csrf_response = self.edupage.session.get(request_url).content.decode()

        csrf_token = csrf_response.split("name=\"csrfauth\" value=\"")[1].split("\"")[0]

        parameters = {
            "username": username,
            "password": password,
            "csrfauth": csrf_token
        }

        request_url = f"https://{subdomain}.edupage.org/login/edubarLogin.php"

        response = self.edupage.session.post(request_url, parameters)

        if "bad=1" in response.url:
            raise BadCredentialsException()

        self.__parse_login_data(response.content.decode())
        self.edupage.subdomain = subdomain

    def reload_data(self, subdomain: str, session_id: str):
        request_url = f"https://{subdomain}.edupage.org/user"

        self.edupage.session.cookies.set("PHPSESSID", session_id)

        response = self.edupage.session.get(request_url)

        try:
            self.__parse_login_data(response.content.decode())
            self.edupage.subdomain = subdomain
        except (TypeError, JSONDecodeError) as e:
            raise BadCredentialsException(f"Invalid session id: {e}")
