import base64
import json
import unittest
from unittest.mock import patch

from edupage_api.exceptions import RequestError, RetryLaterException
from edupage_api.login import Login
from edupage_api.login_session import LoginSession
from edupage_api.twofactor import TwoFactorLogin
from edupage_api.module import EdupageModule


class FakeResponse:
    def __init__(self, text, url="https://school.edupage.org/user/"):
        self.text = text
        self.content = text.encode()
        self.url = url

    def json(self):
        return json.loads(self.text)


class FakeSession:
    def __init__(self, post_responses, get_responses):
        self.post_responses = iter(post_responses)
        self.get_responses = iter(get_responses)
        self.post_calls = []

    def post(self, url, data=None, headers=None):
        self.post_calls.append((url, data, headers))
        return next(self.post_responses)

    def get(self, url):
        return next(self.get_responses)


class FakeEdupage(EdupageModule):
    def __init__(self, session):
        self.subdomain = "school"
        self.username = "student"
        self.session = session
        self.data = None
        self.is_logged_in = False
        self.gsec_hash = None


class LoginRpcResponseParsingTests(unittest.TestCase):
    def test_parse_plain_json_response(self):
        self.assertEqual(
            LoginSession.parse_rpc_response('{"status": "OK"}'), {"status": "OK"}
        )

    def test_parse_compressed_response(self):
        response = "eqz:" + base64.b64encode(b'{"status": "OK"}').decode()

        self.assertEqual(LoginSession.parse_rpc_response(response), {"status": "OK"})

    def test_parse_empty_response(self):
        self.assertIsNone(LoginSession.parse_rpc_response(""))

    def test_parse_invalid_response(self):
        self.assertIsNone(LoginSession.parse_rpc_response("not json at all"))

    def test_parse_response_with_invalid_base64(self):
        self.assertIsNone(LoginSession.parse_rpc_response("eqz:!!!"))


class ModernTwoFactorLoginTests(unittest.TestCase):
    def test_current_two_factor_page_uses_rpc_completion(self):
        session = FakeSession(
            [FakeResponse(json.dumps({"status": "OK", "redirectUrl": "/user/"}))],
            [FakeResponse('userhome({"userid": "student"});')],
        )
        edupage = FakeEdupage(session)

        with patch(
            "edupage_api.twofactor.RequestData.encode_request_body",
            return_value="encoded-request",
        ) as encode_request_body:
            TwoFactorLogin(None, None, None, edupage, True).finish_with_code("123456")

        self.assertTrue(edupage.is_logged_in)
        self.assertEqual(edupage.data, {"userid": "student"})
        encode_request_body.assert_called_once_with(
            {
                "rpcparams": json.dumps(
                    {
                        "t2fasec": "123456",
                        "2fNoSave": "y",
                        "2fform": "1",
                        "tu": None,
                        "gu": None,
                        "au": None,
                    }
                )
            }
        )
        self.assertEqual(
            session.post_calls[0][0],
            "https://school.edupage.org/login/?cmd=MainLogin&akcia=login",
        )
        self.assertEqual(
            session.post_calls[0][2],
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

    def test_current_two_factor_page_is_detected_without_legacy_fields(self):
        response = FakeResponse(
            "",
            "https://school.edupage.org/login/twofactor?sn=1",
        )
        session = FakeSession(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "status": "ok",
                            "deviceNames": ["Phone", ""],
                            "email": "student@example.com",
                        }
                    )
                )
            ],
            [FakeResponse('<script src="/login/pics/jsw/twofactorlogin.js"></script>')],
        )
        edupage = FakeEdupage(session)

        two_factor = Login(edupage)._Login__finish_login(response, "school", "student")

        self.assertIsInstance(two_factor, TwoFactorLogin)
        self.assertTrue(two_factor._TwoFactorLogin__use_modern_rpc)
        self.assertEqual(two_factor.device_names, ["Phone"])
        self.assertEqual(two_factor.email, "student@example.com")
        self.assertEqual(
            session.post_calls[0][0],
            "https://school.edupage.org/login/twofactor?akcia=getData",
        )


def modern_two_factor(response):
    session = FakeSession([response], [])
    return TwoFactorLogin(
        None, None, None, FakeEdupage(session), True, email="student@example.com"
    )


class SendEmailCodeTests(unittest.TestCase):
    def send_email_code(self, response_data):
        two_factor = modern_two_factor(FakeResponse(json.dumps(response_data)))

        two_factor.send_email_code()

        return two_factor

    def test_sent_email_updates_the_address(self):
        two_factor = self.send_email_code(
            {"status": "ok", "data": {"email": "parent@example.com"}}
        )

        self.assertEqual(two_factor.email, "parent@example.com")

    def test_sent_email_without_address_keeps_the_known_one(self):
        two_factor = self.send_email_code({"status": "ok", "data": {}})

        self.assertEqual(two_factor.email, "student@example.com")

    def test_sent_email_with_empty_list_data_keeps_the_known_one(self):
        two_factor = self.send_email_code({"status": "ok", "data": []})

        self.assertEqual(two_factor.email, "student@example.com")

    def test_email_requested_too_soon_asks_to_retry_later(self):
        with self.assertRaises(RetryLaterException) as context:
            self.send_email_code({"status": "fail", "data": {"retryInSeconds": 10}})

        self.assertEqual(context.exception.retry_in_seconds, 10)

    def test_other_failures_raise_request_error(self):
        with self.assertRaises(RequestError) as context:
            self.send_email_code({"status": "fail", "data": {"err": "unknown"}})

        self.assertNotIsInstance(context.exception, RetryLaterException)


class ResendNotificationsTests(unittest.TestCase):
    def test_resend_requested_too_soon_asks_to_retry_later(self):
        two_factor = modern_two_factor(
            FakeResponse(json.dumps({"status": "fail", "data": {"retryInSeconds": 10}}))
        )

        with self.assertRaises(RetryLaterException) as context:
            two_factor.resend_notifications()

        self.assertEqual(context.exception.retry_in_seconds, 10)

    def test_failure_with_text_data_raises_request_error(self):
        two_factor = modern_two_factor(
            FakeResponse(json.dumps({"status": "fail", "data": "Unknown error"}))
        )

        with self.assertRaises(RequestError) as context:
            two_factor.resend_notifications()

        self.assertNotIsInstance(context.exception, RetryLaterException)


if __name__ == "__main__":
    unittest.main()
