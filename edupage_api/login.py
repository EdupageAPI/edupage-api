import json
from typing import Optional
from urllib.parse import urljoin, urlparse

from edupage_api.compression import RequestData
from edupage_api.exceptions import BadCredentialsException, CaptchaException
from edupage_api.login_session import LoginSession
from edupage_api.module import Module
from edupage_api.twofactor import TwoFactorLogin


class Login(Module):
    def __finish_login(self, response, subdomain: str, username: str):
        data = response.content.decode()

        if subdomain == "login1":
            subdomain = urlparse(response.url).hostname.split(".")[0]

        self.edupage.subdomain = subdomain
        self.edupage.username = username

        if "twofactor" not in response.url:
            LoginSession(self.edupage).parse_login_data(data)
            return None

        request_url = (
            f"https://{self.edupage.subdomain}.edupage.org/login/twofactor?sn=1"
        )

        two_factor_response = self.edupage.session.get(request_url)

        data = two_factor_response.content.decode()

        two_factor = TwoFactorLogin.from_page(self.edupage, data)
        if two_factor is None:
            raise BadCredentialsException("EduPage did not provide two-factor fields")

        return two_factor

    def __login_with_rpc(self, username: str, password: str, subdomain: str):
        # Mirrors the login process (mainlogin.js):
        # 1. akcia=getToken
        # 2. akcia=login
        base_url = f"https://{subdomain}.edupage.org"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = self.edupage.session.get(f"{base_url}/login/?cmd=MainLogin")
        if response.status_code != 200:
            return None

        token_response_raw = self.edupage.session.post(
            f"{base_url}/login/?cmd=MainLogin&akcia=getToken",
            data=RequestData.encode_request_body(
                {"rpcparams": json.dumps({"username": username, "edupage": ""})}
            ),
            headers=headers,
        )
        if token_response_raw.status_code != 200:
            return None
        token_response = LoginSession.parse_rpc_response(token_response_raw.text)

        token = token_response.get("token") if token_response else None
        if not token:
            return None

        login_response_raw = self.edupage.session.post(
            f"{base_url}/login/?cmd=MainLogin&akcia=login",
            data=RequestData.encode_request_body(
                {
                    "rpcparams": json.dumps(
                        {
                            "username": username,
                            "password": password,
                            "userToken": token,
                            "edupage": "",
                            "ctxt": "",
                            "tu": None,
                            "gu": None,
                            "au": None,
                        }
                    )
                }
            ),
            headers=headers,
        )

        if login_response_raw.status_code != 200:
            return None

        login_response = LoginSession.parse_rpc_response(login_response_raw.text)
        if not login_response:
            return None

        error_id = (login_response.get("err") or {}).get("error_id")
        redirect_url = login_response.get("redirectUrl")

        # `invalid_token` means our csrf token was rejected
        if error_id == "invalid_token" or not redirect_url:
            return None

        return self.edupage.session.get(urljoin(base_url, redirect_url))

    def login(
        self, username: str, password: str, subdomain: str = "login1"
    ) -> TwoFactorLogin | None:
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
            CaptchaException: The login process failed because of a captcha.
            SecondFactorFailed: The second factor login timed out
                or there was another problem with the second factor.
        """

        response = self.__login_with_rpc(username, password, subdomain)

        if response is None:
            request_url = f"https://{subdomain}.edupage.org/login/?cmd=MainLogin"

            get_response = self.edupage.session.get(request_url)
            data = get_response.content.decode()

            try:
                csrf_token = data.split('"csrftoken":"', 1)[1].split('"', 1)[0]
            except IndexError:
                raise BadCredentialsException("EduPage did not provide a login token")

            parameters = {
                "csrfauth": csrf_token,
                "username": username,
                "password": password,
            }

            request_url = f"https://{subdomain}.edupage.org/login/edubarLogin.php"

            response = self.edupage.session.post(request_url, parameters)

            if "cap=1" in response.url or "lerr=b43b43" in response.url:
                raise CaptchaException()

            if "bad=1" in response.url:
                raise BadCredentialsException()

        return self.__finish_login(response, subdomain, username)
