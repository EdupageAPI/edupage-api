import base64
import json
import unittest
from unittest.mock import patch

from edupage_api.login import Login, TwoFactorLogin


class FakeResponse:
    def __init__(self, text, url="https://school.edupage.org/user/"):
        self.text = text
        self.content = text.encode()
        self.url = url


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


class FakeEdupage:
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
            Login._parse_rpc_response('{"status": "OK"}'), {"status": "OK"}
        )

    def test_parse_compressed_response(self):
        response = "eqz:" + base64.b64encode(b'{"status": "OK"}').decode()

        self.assertEqual(Login._parse_rpc_response(response), {"status": "OK"})

    def test_parse_empty_response(self):
        self.assertIsNone(Login._parse_rpc_response(""))

    def test_parse_invalid_response(self):
        self.assertIsNone(Login._parse_rpc_response("not json at all"))

    def test_parse_response_with_invalid_base64(self):
        self.assertIsNone(Login._parse_rpc_response("eqz:!!!"))


class ModernTwoFactorLoginTests(unittest.TestCase):
    def test_current_two_factor_page_uses_rpc_completion(self):
        session = FakeSession(
            [FakeResponse(json.dumps({"status": "OK", "redirectUrl": "/user/"}))],
            [FakeResponse('userhome({"userid": "student"});')],
        )
        edupage = FakeEdupage(session)

        with patch(
            "edupage_api.login.RequestData.encode_request_body",
            return_value="encoded-request",
        ) as encode_request_body:
            TwoFactorLogin(None, None, None, edupage, True).finish_with_code(
                "123456"
            )

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
            [],
            [
                FakeResponse(
                    '<script src="/login/pics/jsw/twofactorlogin.js"></script>'
                )
            ],
        )
        edupage = FakeEdupage(session)

        two_factor = Login(edupage)._Login__finish_login(
            response, "school", "student"
        )

        self.assertIsInstance(two_factor, TwoFactorLogin)
        self.assertTrue(two_factor._TwoFactorLogin__use_modern_rpc)


if __name__ == "__main__":
    unittest.main()
