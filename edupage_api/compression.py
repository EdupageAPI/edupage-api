import zlib
from hashlib import sha1
from typing import Union
from edupage_api.exceptions import Base64DecodeError

from edupage_api.module import ModuleHelper

# compression parameters from https://github.com/rgnter/epea_cpp
# encoding and decoding from https://github.com/jsdom/abab
class RequestData:
    @staticmethod
    def __compress(data: bytes) -> bytes:
        compressor = zlib.compressobj(
            -1,
            zlib.DEFLATED,
            -15,
            8,
            zlib.Z_DEFAULT_STRATEGY
        )


        compressor.compress(data)
        return compressor.flush(zlib.Z_FINISH)

    @staticmethod
    def chromium_base64_encode(data: str) -> str:
        # "The btoa() method must throw an "InvalidCharacterError" DOMException if
        # data contains any character whose code point is greater than U+00FF."
        for ch in data:
            if ord(ch) > 255:
                return None

        length = len(data)
        i = 0

        # Lookup table for btoa(), which converts a six-bit number into the
        # corresponding ASCII character.
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        def btoa_lookup(index):
            if index >= 0 and index < 64:
                return chars[index]
            
            return None

        out = ""
        for i in range(0, length, 3):
            groups_of_six = [None, None, None, None]
            groups_of_six[0] = ord(data[i]) >> 2
            groups_of_six[1] = (ord(data[i]) & 0x03) << 4

            if length > i + 1:
                groups_of_six[1] |= ord(data[i + 1]) >> 4
                groups_of_six[2] = (ord(data[i + 1]) & 0x0f) << 2

            if length > i + 2:
                groups_of_six[2] |= ord(data[i + 2]) >> 6
                groups_of_six[3] = ord(data[i + 2]) & 0x3f

            for k in groups_of_six:
                if k is None:
                    out += "="
                else:
                    out += btoa_lookup(k)
                
            
            i += 3

        return out
                

    def chromium_base64_decode(data: str) -> str:
        # "Remove all ASCII whitespace from data."
        [data := data.replace(char, "") for char in "\t\n\f\r"]
        
        # "If data's code point length divides by 4 leaving no remainder, then: if data ends
        # with one or two U+003D (=) code points, then remove them from data."
        if len(data) % 4 == 0:
            if data.endswith("=="):
                data = data.replace("==", "")
            elif data.endswith("="):
                data = data.replace("=", "")
        
        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        def atob_lookup(ch: str):
            try:
                return allowed_chars.index(ch)
            except ValueError:
                return None

        # "If data's code point length divides by 4 leaving a remainder of 1, then return
        # failure."
        #
        # "If data contains a code point that is not one of
        #
        # U+002B (+)
        # U+002F (/)
        # ASCII alphanumeric
        #
        # then return failure."
        data_contains_invalid_chars = False in [ch in allowed_chars for ch in data]
        if len(data) % 4 == 1 or data_contains_invalid_chars:
            return None
        
        # "Let output be an empty byte sequence."
        output = ""

        # "Let buffer be an empty buffer that can have bits appended to it."
        #
        # We append bits via left-shift and or.  accumulatedBits is used to track
        # when we've gotten to 24 bits.
        buffer = 0
        accumulated_bits = 0
        
        # "Let position be a position variable for data, initially pointing at the
        # start of data."
        #
        # "While position does not point past the end of data:"
        for ch in data:
            # "Find the code point pointed to by position in the second column of
            # Table 1: The Base 64 Alphabet of RFC 4648. Let n be the number given in
            # the first cell of the same row.
            #
            # "Append to buffer the six bits corresponding to n, most significant bit
            # first."
            #
            # atob_lookup() implements the table from RFC 4648.
            buffer <<= 6
            buffer |= atob_lookup(ch)
            accumulated_bits += 6

            # "If buffer has accumulated 24 bits, interpret them as three 8-bit
            # big-endian numbers. Append three bytes with values equal to those
            # numbers to output, in the same order, and then empty buffer."
            if accumulated_bits == 24:
                output += chr((buffer & 0xff0000) >> 16)
                output += chr((buffer & 0xff00) >> 8)
                output += chr(buffer & 0xff)
                
                buffer = 0
                accumulated_bits = 0
        
        # "If buffer is not empty, it contains either 12 or 18 bits. If it contains
        # 12 bits, then discard the last four and interpret the remaining eight as
        # an 8-bit big-endian number. If it contains 18 bits, then discard the last
        # two and interpret the remaining 16 as two 8-bit big-endian numbers. Append
        # the one or two bytes with values equal to those one or two numbers to
        # output, in the same order."
        if accumulated_bits == 12:
            buffer >>= 4
            output += chr(buffer)
        elif accumulated_bits == 18:
            buffer >>= 2
            output += chr((buffer & 0xff00) >> 8)
            output += chr(buffer & 0xff)
        
        return output
    

    @staticmethod
    def __encode_data(data: str) -> bytes:
        compressed = RequestData.__compress(data.encode())

        encoded = RequestData.chromium_base64_encode("".join([chr(ch) for ch in compressed]))

        return encoded
    
    @staticmethod
    def __decode_data(data: str) -> str:
        return RequestData.chromium_base64_decode(data)

    @staticmethod
    def encode_request_body(request_data: Union[dict, str]) -> str:
        encoded_data = ModuleHelper.encode_form_data(request_data) if type(request_data) == dict else request_data
        encoded_data = RequestData.__encode_data(encoded_data)
        data_hash = sha1(encoded_data.encode()).hexdigest()

        return ModuleHelper.encode_form_data({
            "eqap": f"dz:{encoded_data}",
            "eqacs": data_hash,
            "eqaz": "1" # use "encryption"? (compression)
        })
    
    @staticmethod
    def decode_response(response: str) -> str:
        # error
        if response.startswith("eqwd:"):
            return RequestData.chromium_base64_decode(response[5:])
        
        # response not compressed
        if not response.startswith("eqz:"):
            return response
        

        decoded = RequestData.__decode_data(response[4:])
        if decoded is None:
            raise Base64DecodeError("Failed to decode response.")
        
        return decoded