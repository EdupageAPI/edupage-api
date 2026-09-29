import base64
import json
import unittest

from edupage_api.login import Login


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


if __name__ == "__main__":
    unittest.main()
