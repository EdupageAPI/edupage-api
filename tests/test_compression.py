import base64
import hashlib
import json
import unittest
import zlib
from urllib.parse import quote, unquote

from edupage_api.compression import RequestData
from edupage_api.exceptions import Base64DecodeError


class RequestDataEncodingTests(unittest.TestCase):
    def test_encode_request_body_round_trip(self):
        rpc_params = json.dumps(
            {"username": "demo", "password": "secret"}, separators=(",", ":")
        )

        encoded = RequestData.encode_request_body({"rpcparams": rpc_params})

        fields = {k: unquote(v) for k, v in (kv.split("=", 1) for kv in encoded.split("&"))}

        self.assertEqual(fields["eqaz"], "1")
        self.assertTrue(fields["eqap"].startswith("dz:"))
        self.assertEqual(
            fields["eqacs"], hashlib.sha1(fields["eqap"].encode()).hexdigest()
        )

        compressed = base64.b64decode(fields["eqap"][3:])
        decompressed = zlib.decompress(compressed, -zlib.MAX_WBITS).decode()

        self.assertEqual(decompressed, "rpcparams=" + quote(rpc_params))

    def test_decode_response_compressed(self):
        payload = json.dumps({"status": "OK", "token": "abc"})
        response = "eqz:" + base64.b64encode(payload.encode()).decode()

        self.assertEqual(RequestData.decode_response(response), payload)

    def test_decode_response_not_compressed(self):
        response = '{"status": "OK"}'

        self.assertEqual(RequestData.decode_response(response), response)

    def test_decode_response_invalid_base64_raises(self):
        with self.assertRaises(Base64DecodeError):
            RequestData.decode_response("eqz:!!!")


if __name__ == "__main__":
    unittest.main()
