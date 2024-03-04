import time
from edupage_api import Edupage
from edupage_api.exceptions import SecondFactorFailedException, BadCredentialsException

edupage = Edupage()

USERNAME = "Username"
PASSWORD = "Password"
SUBDOMAIN = "Your school's subdomain"

try:
    second_factor = edupage.login_2fa(USERNAME, PASSWORD, SUBDOMAIN)
    confirmation_method = input(
        "Choose confirmation method: 1 -> mobile app, 2 -> code: "
    )

    if confirmation_method == "1":
        while not second_factor.is_confirmed():
            time.sleep(0.5)
        second_factor.finish()

    elif confirmation_method == "2":
        code = input("Enter 2FA code (or 'resend' to resend the code): ")
        while code.lower() == "resend":
            second_factor.resend_notifications()
            code = input("Enter 2FA code (or 'resend' to resend the code): ")
        second_factor.finish_with_code(code)

except BadCredentialsException:
    print("Wrong username or password")
except SecondFactorFailedException:
    print("Second factor failed")

if edupage.is_logged_in:
    print("Logged in")
else:
    print("Login failed")
