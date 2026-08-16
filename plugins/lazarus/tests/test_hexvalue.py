"""Ethereum hex quantities and fixed-width values fail before proof use."""

import unittest

from lazarus_lib.errors import FormatError
from lazarus_lib.hexvalue import (
    address_bytes,
    hash32_bytes,
    hex_bytes,
    quantity,
    quantity_bytes,
    slot_bytes,
    uint_from_rlp,
)


class HexValueTests(unittest.TestCase):
    def test_canonical_quantities_convert_to_ints_and_minimal_bytes(self):
        self.assertEqual(quantity("0x0"), 0)
        self.assertEqual(quantity("0xff"), 255)
        self.assertEqual(quantity_bytes("0x0"), b"")
        self.assertEqual(quantity_bytes("0x100"), b"\x01\x00")

    def test_noncanonical_negative_uppercase_and_wide_quantities_fail(self):
        for value in ("0x00", "0x01", "0xA", "1", "-0x1", "0x1" + "0" * 64):
            with self.subTest(value=value), self.assertRaises(FormatError):
                quantity(value)

    def test_hex_bytes_require_prefix_pairs_and_requested_width(self):
        self.assertEqual(hex_bytes("0x00ff"), b"\x00\xff")
        self.assertEqual(address_bytes("0x" + "11" * 20), b"\x11" * 20)
        self.assertEqual(slot_bytes("0x" + "22" * 32), b"\x22" * 32)
        self.assertEqual(hash32_bytes("0x" + "AA" * 32), b"\xaa" * 32)
        for value in ("00", "0x0", "0xzz"):
            with self.subTest(value=value), self.assertRaises(FormatError):
                hex_bytes(value)
        with self.assertRaises(FormatError):
            address_bytes("0x" + "11" * 19)

    def test_rlp_integers_reject_leading_zero_and_values_over_256_bits(self):
        self.assertEqual(uint_from_rlp(b""), 0)
        self.assertEqual(uint_from_rlp(b"\x01\x00"), 256)
        with self.assertRaisesRegex(FormatError, "leading zero"):
            uint_from_rlp(b"\x00")
        with self.assertRaisesRegex(FormatError, "256 bits"):
            uint_from_rlp(b"\x01" * 33)


if __name__ == "__main__":
    unittest.main()
