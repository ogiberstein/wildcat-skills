"""Strict RLP accepts canonical Ethereum values and rejects alternate bytes."""

import unittest

from lazarus_lib.errors import FormatError
from lazarus_lib.rlp import decode, encode


class RlpTests(unittest.TestCase):
    def test_known_strings_lists_and_long_payloads_round_trip(self):
        self.assertEqual(encode(b"dog"), b"\x83dog")
        self.assertEqual(encode([b"cat", b"dog"]), b"\xc8\x83cat\x83dog")
        self.assertEqual(decode(b"\x83dog"), b"dog")
        payload = b"x" * 56
        self.assertEqual(decode(encode(payload)), payload)
        nested = [b"", [b"a", b"b"], payload]
        self.assertEqual(decode(encode(nested)), nested)

    def test_truncation_trailing_bytes_and_wrong_types_fail(self):
        for raw in (b"", b"\x83ab", b"\xc3\x81", b"\x80\x80"):
            with self.subTest(raw=raw), self.assertRaises(FormatError):
                decode(raw)
        with self.assertRaises(FormatError):
            encode("not bytes")

    def test_overlong_strings_lists_and_lengths_fail(self):
        invalid = (
            b"\x81\x00",
            b"\xb8\x01x",
            b"\xb9\x00\x38" + b"x" * 56,
            b"\xf8\x01\x80",
            b"\xf9\x00\x38" + b"\x80" * 56,
        )
        for raw in invalid:
            with self.subTest(raw=raw[:8]), self.assertRaises(FormatError):
                decode(raw)

    def test_excessive_nesting_fails_at_the_bound(self):
        value = b"x"
        for _ in range(70):
            value = [value]
        with self.assertRaisesRegex(FormatError, "too deep"):
            decode(encode(value))


if __name__ == "__main__":
    unittest.main()
