import json
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Optional

from requests import Response

from edupage_api.exceptions import (BadCredentialsException,
                                    MissingDataException, RequestError,
                                    SecondFactorFailedException)
from edupage_api.module import EdupageModule, Module


@dataclass
class TwoFactorLogin:
    __authentication_endpoint: str
    __authentication_token: str
    __csrf_token: str
    __edupage: EdupageModule

    __code: Optional[str] = None

    def is_confirmed(self):
        """Check if the second factor process was finished by confirmation with a device.

        If this function returns true, you can safely use `TwoFactorLogin.finish` to finish the second factor authentication process.

        Returns:
            bool: True if the second factor was confirmed with a device.
        """

        request_url = f"https://{self.__edupage.subdomain}.edupage.org/login/twofactor?akcia=checkIfConfirmed"
        response = self.__edupage.session.post(request_url)

        data = response.json()
        if data.get("status") == "fail":
            return False
        elif data.get("status") != "ok":
            raise MissingDataException(
                f"Invalid response from edupage's server!: {str(data)}"
            )

        self.__code = data["data"]

        return True

    def resend_notifications(self):
        """Resends the confirmation notification to all devices."""

        request_url = f"https://{self.__edupage.subdomain}.edupage.org/login/twofactor?akcia=resendNotifs"
        response = self.__edupage.session.post(request_url)

        data = response.json()
        if data.get("status") != "ok":
            raise RequestError(f"Failed to resend notifications: {str(data)}")

    def __finish(self, code: str):
        request_url = (
            f"https://{self.__edupage.subdomain}.edupage.org/login/edubarLogin.php"
        )
        parameters = {
            "csrfauth": self.__csrf_token,
            "t2fasec": code,
            "2fNoSave": "y",
            "2fform": "1",
            "gu": self.__authentication_endpoint,
            "au": self.__authentication_token,
        }

        response = self.__edupage.session.post(request_url, parameters)

        if "window.location = gu;" in response.text:
            cookies = self.__edupage.session.cookies.get_dict(
                f"{self.__edupage.subdomain}.edupage.org"
            )

            Login(self.__edupage).reload_data(
                self.__edupage.subdomain, cookies["PHPSESSID"], self.__edupage.username
            )

            return

        raise SecondFactorFailedException(
            f"Second factor failed! (wrong/expired code? expired session?)"
        )

    def finish(self):
        """Finish the second factor authentication process.
        This function should be used when using a device to confirm the login. If you are using email 2fa codes, please use `TwoFactorLogin.finish_with_code`.

        Notes:
            - This function can only be used after `TwoFactorLogin.is_confirmed` returned `True`.
            - This function can raise `SecondFactorFailedException` if there is a big delay from calling `TwoFactorLogin.is_confirmed` (and getting `True` as a result) to calling `TwoFactorLogin.finish`.

        Raises:
            BadCredentialsException: You didn't call and get the `True` result from `TwoFactorLogin.is_confirmed` before calling this function.
            SecondFactorFailedException: The delay between calling `TwoFactorLogin.is_confirmed` and `TwoFactorLogin.finish` was too long, or there was another error with the second factor authentication confirmation process.
        """

        if self.__code is None:
            raise BadCredentialsException(
                "Not confirmed! (you can only call finish after `TwoFactorLogin.is_confirmed` has returned True)"
            )

        self.__finish(self.__code)

    def finish_with_code(self, code: str):
        """Finish the second factor authentication process.
        This function should be used when email 2fa codes are used to confirm the login. If you are using a device to confirm the login, please use `TwoFactorLogin.finish`.

        Args:
            code (str): The 2fa code from your email or from the mobile app.

        Raises:
            SecondFactorFailedException: An invalid 2fa code was provided.
        """
        self.__finish(code)


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

    def login(
        self, username: str, password: str, subdomain: str = "login1"
    ) -> Optional[TwoFactorLogin]:
        """Login to your school's Edupage account (optionally with 2 factor authentication).

        If you do not have 2 factor authentication set up, this function will return `None`.
        The login will still work and succeed.

        See the `Edupage.TwoFactorLogin` documentation or the examples for more details
        of the 2 factor authentication process.

        Args:
            username (str): Your username.
            password (str): Your password.
            subdomain (str): Subdomain of your school (https://{subdomain}.edupage.org).

        Returns:
            Optional[TwoFactorLogin]: The object that can be used to complete the second factor
                (or `None` — if the second factor is not set up)

        Raises:
            BadCredentialsException: Your credentials are invalid.
            SecondFactorFailed: The second factor login timed out
                or there was another problem with the second factor.
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

        if "bad=1" in response.url:
            raise BadCredentialsException()
        
        data = response.content.decode()

        if subdomain == "login1":
            subdomain = data.split("-->")[0].split(" ")[-1]

        self.edupage.subdomain = subdomain
        self.edupage.username = username

        if "twofactor" not in response.url:
            # 2FA not needed
            self.__parse_login_data(data)
            return

        request_url = (
            f"https://{self.edupage.subdomain}.edupage.org/login/twofactor?sn=1"
        )
        
        two_factor_response = self.edupage.session.get(request_url)

        data = two_factor_response.content.decode()

        csrf_token = data.split('csrfauth" value="')[1].split('"')[0]

        authentication_token = data.split('au" value="')[1].split('"')[0]
        authentication_endpoint = data.split('gu" value="')[1].split('"')[0]

        return TwoFactorLogin(
            authentication_endpoint, authentication_token, csrf_token, self.edupage
        )

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
