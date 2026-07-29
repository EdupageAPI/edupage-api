import base64
import hashlib
import json
import unittest
import zlib
from urllib.parse import urlencode

from edupage_api.login import Login


class LoginRpcEncodingTests(unittest.TestCase):
    def test_encode_decode_rpc_payload_round_trip(self):
        payload = {"username": "demo", "password": "secret"}

        encoded = Login._encode_rpc_payload(payload)

        self.assertIn("eqap", encoded)
        self.assertEqual(encoded["eqaz"], "1")
        self.assertEqual(encoded["eqacs"], hashlib.sha1(encoded["eqap"].encode()).hexdigest())

        decoded = Login._decode_rpc_response(
            "eqz:" + base64.b64encode(json.dumps({"status": "OK", "token": "abc"}).encode()).decode()
        )

        self.assertEqual(decoded["status"], "OK")
        self.assertEqual(decoded["token"], "abc")


if __name__ == "__main__":
    unittest.main()
