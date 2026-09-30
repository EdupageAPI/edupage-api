import time

from edupage_api import Edupage
from edupage_api.exceptions import (
    BadCredentialsException,
    RequestError,
    RetryLaterException,
    SecondFactorFailedException,
)

edupage = Edupage()

USERNAME = "Username"
PASSWORD = "Password"
SUBDOMAIN = "Your school's subdomain"


def send_after_countdown(send):
    # The first verification code goes to the EduPage app right after the login.
    # EduPage then asks to wait before sending a code again.
    while True:
        try:
            return send()
        except RetryLaterException as e:
            print(f"Sending in {e.retry_in_seconds} seconds...")
            time.sleep(e.retry_in_seconds)


try:
    second_factor = edupage.login(USERNAME, PASSWORD, SUBDOMAIN)
    confirmation_method = input(
        "Choose confirmation method: 1 -> mobile app, 2 -> code: "
    )

    if confirmation_method == "1":
        while not second_factor.is_confirmed():
            time.sleep(0.5)
        second_factor.finish()

    elif confirmation_method == "2":
        # Verification code is sent to mobile app or by e-mail. Validity is 5 minutes.
        # After that, you can get a new one ('email' or 'resend') and enter it.
        email = second_factor.email or "your email"
        prompt = f"Enter 2FA code (or 'email' to send it to {email}, 'resend' to resend it): "
        while not edupage.is_logged_in:
            code = input(prompt)
            try:
                if code.lower() == "email":
                    send_after_countdown(second_factor.send_email_code)
                    print(f"Code sent to {second_factor.email or email}")
                elif code.lower() == "resend":
                    send_after_countdown(second_factor.resend_notifications)
                else:
                    second_factor.finish_with_code(code)
            except SecondFactorFailedException:
                print("Wrong code, or more than 5 minutes passed: try again, or get a new code")
            except RequestError as e:
                print(e)

except BadCredentialsException:
    print("Wrong username or password")
except SecondFactorFailedException:
    print("Second factor failed")

if edupage.is_logged_in:
    print("Logged in")
else:
    print("Login failed")
