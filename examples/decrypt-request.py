from edupage_api.compression import RequestData
import zlib
from urllib.parse import unquote
import sys

if len(sys.argv) != 2:
    print("Usage: python decrypt-request.py \"<request body>\"")
    sys.exit(1)

pairs = sys.argv[1].split("&")

request_data = {}
for pair in pairs:
    key, value = pair.split("=")
    request_data[unquote(key)] = unquote(value)

s = request_data["eqap"]
compressed = RequestData.chromium_base64_decode(s[3:])

decompressed = zlib.decompress(bytes([ord(ch) for ch in compressed]), wbits=-15)
print(unquote(decompressed.decode()))