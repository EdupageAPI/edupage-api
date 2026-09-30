import json
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

from edupage_api.compression import RequestData
from edupage_api.exceptions import (
    BadCredentialsException,
    MissingDataException,
    RequestError,
    RetryLaterException,
    SecondFactorFailedException,
)
from edupage_api.login_session import LoginSession
from edupage_api.module import EdupageModule


@dataclass
class TwoFactorLogin:
    __authentication_endpoint: Optional[str]
    __authentication_token: Optional[str]
    __csrf_token: Optional[str]
    __edupage: EdupageModule
    __use_modern_rpc: bool = False

    __code: Optional[str] = None

    # Only provided by modern RPC 2FA page
    email: Optional[str] = None
    device_names: Optional[list[str]] = None

    @staticmethod
    def __extract_form_fields(page: str) -> Optional[dict]:
        try:
            return {
                "csrfauth": page.split('csrfauth" value="', 1)[1].split('"', 1)[0],
                "au": page.split('au" value="', 1)[1].split('"', 1)[0],
                "gu": page.split('gu" value="', 1)[1].split('"', 1)[0],
            }
        except IndexError:
            return None

    @staticmethod
    def __get_page_data(edupage: EdupageModule) -> dict:
        request_url = (
            f"https://{edupage.subdomain}.edupage.org/login/twofactor?akcia=getData"
        )
        response = edupage.session.post(request_url)

        try:
            data = response.json()
        except ValueError:
            return {}

        return data if isinstance(data, dict) else {}

    @classmethod
    def from_page(
        cls, edupage: EdupageModule, page: str
    ) -> Optional["TwoFactorLogin"]:
        """Create the object from EduPage's two-factor page.

        Args:
            edupage (EdupageModule): The edupage instance with `subdomain` set.
            page (str): The HTML of `/login/twofactor`.

        Returns:
            Optional[TwoFactorLogin]: `None` if the page is not a known two-factor page.
        """

        fields = cls.__extract_form_fields(page)
        if fields:
            return cls(fields["gu"], fields["au"], fields["csrfauth"], edupage)

        if "/login/pics/jsw/twofactorlogin.js" not in page:
            return None

        page_data = cls.__get_page_data(edupage)

        device_names = page_data.get("deviceNames")
        if device_names is not None:
            device_names = [name for name in device_names if name]

        return cls(
            None,
            None,
            None,
            edupage,
            True,
            email=page_data.get("email"),
            device_names=device_names,
        )

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

    @staticmethod
    def __request_error(message: str, data: dict) -> RequestError:
        details = data.get("data")
        if isinstance(details, dict) and details.get("retryInSeconds"):
            return RetryLaterException(message, int(details["retryInSeconds"]))

        return RequestError(message)

    def resend_notifications(self):
        """Resends the notification to all devices.

        It shares the countdown timer with `TwoFactorLogin.send_email_code`.

        Raises:
            RetryLaterException: It was requested too soon; try again after `retry_in_seconds`.
            RequestError: The notification could not be resent.
        """

        request_url = f"https://{self.__edupage.subdomain}.edupage.org/login/twofactor?akcia=resendNotifs"
        response = self.__edupage.session.post(request_url)

        data = response.json()
        if data.get("status") != "ok":
            raise self.__request_error(
                f"Failed to resend notifications: {str(data)}", data
            )

    def send_email_code(self):
        """Send the 2fa code to your email.

        EduPage allows sending a code (by email, or with `TwoFactorLogin.resend_notifications`)
        only after a countdown. The timer is about 30 seconds after entering username and password,
        and is reset to 60 seconds once a code is sent. Until then this raises `RetryLaterException`;
        call it again after `retry_in_seconds`.

        Use `TwoFactorLogin.finish_with_code` to finish the login with the received code.
        The address the code was sent to is stored in `TwoFactorLogin.email`.

        Raises:
            RetryLaterException: It was requested too soon; try again after `retry_in_seconds`.
            RequestError: The code could not be sent.
        """

        request_url = f"https://{self.__edupage.subdomain}.edupage.org/login/twofactor?akcia=sendEmail"
        response = self.__edupage.session.post(request_url)

        data = response.json()
        if data.get("status") != "ok":
            raise self.__request_error(f"Failed to send the email: {str(data)}", data)

        self.email = data["data"].get("email") or self.email

    def __finish(self, code: str):
        if self.__use_modern_rpc:
            self.__finish_with_modern_rpc(code)
            return

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

            LoginSession(self.__edupage).reload_data(
                self.__edupage.subdomain, cookies["PHPSESSID"], self.__edupage.username
            )

            return

        raise SecondFactorFailedException(
            f"Second factor failed! (wrong/expired code? expired session?)"
        )

    def __finish_with_modern_rpc(self, code: str):
        """Complete the JavaScript-based 2FA flow used by current EduPage pages."""

        base_url = f"https://{self.__edupage.subdomain}.edupage.org"
        response = self.__edupage.session.post(
            f"{base_url}/login/?cmd=MainLogin&akcia=login",
            data=RequestData.encode_request_body(
                {
                    "rpcparams": json.dumps(
                        {
                            "t2fasec": code,
                            "2fNoSave": "y",
                            "2fform": "1",
                            "tu": None,
                            "gu": None,
                            "au": None,
                        }
                    )
                }
            ),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        result = LoginSession.parse_rpc_response(response.text)

        if not result or result.get("status") != "OK":
            raise SecondFactorFailedException(
                "Second factor failed! (wrong/expired code? expired session?)"
            )

        user_page = self.__edupage.session.get(
            urljoin(base_url, result.get("redirectUrl", "/user/"))
        )
        LoginSession(self.__edupage).parse_login_data(user_page.content.decode())

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
        """Finish the second factor authentication process with a 2fa verification code.

        If you are using a device to confirm the login, please use `TwoFactorLogin.finish`.

        Verification code is valid for 5 minutes. After that it is refused like a wrong one.
        Use `TwoFactorLogin.send_email_code` or `TwoFactorLogin.resend_notifications` to
        request a new code and continue (without a need to provide username and password again).

        Args:
            code (str): The 2fa code from your email or from the mobile app.

        Raises:
            SecondFactorFailedException: An invalid 2fa code was provided, or it came after the 5 minutes.
        """
        self.__finish(code)
