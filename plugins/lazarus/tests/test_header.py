"""Execution headers hash with exactly the fields active at their fork."""

import copy
import unittest

from lazarus_lib.errors import FormatError, IntegrityError
from lazarus_lib.header import compute_header_hash, header_fields, verify_header
from lazarus_lib.hexvalue import encode_hex

from . import support


class HeaderTests(unittest.TestCase):
    def test_mainnet_genesis_header_recomputes_the_published_hash(self):
        header = support.genesis_header()
        self.assertEqual(
            encode_hex(compute_header_hash(header)),
            "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3",
        )
        report = verify_header(header)
        self.assertEqual(report["field_count"], 15)
        self.assertEqual(report["state_root"], header["state_root"])

    def test_london_shanghai_cancun_and_prague_suffixes_are_ordered(self):
        header = support.genesis_header()
        header["rpc_result"].update(
            {
                "baseFeePerGas": "0x1",
                "withdrawalsRoot": support.hash32("21"),
                "blobGasUsed": "0x0",
                "excessBlobGas": "0x1",
                "parentBeaconBlockRoot": support.hash32("22"),
                "requestsHash": support.hash32("23"),
            }
        )
        self.assertEqual(len(header_fields(header)), 21)
        for field, expected in (
            ("requestsHash", 21),
            ("parentBeaconBlockRoot", 20),
            ("withdrawalsRoot", 17),
            ("baseFeePerGas", 16),
        ):
            reduced = copy.deepcopy(header)
            suffix = [
                "baseFeePerGas",
                "withdrawalsRoot",
                "blobGasUsed",
                "excessBlobGas",
                "parentBeaconBlockRoot",
                "requestsHash",
            ]
            for name in suffix[suffix.index(field) + 1 :]:
                reduced["rpc_result"].pop(name, None)
            self.assertEqual(len(header_fields(reduced)), expected)

    def test_partial_or_out_of_order_fork_suffixes_fail(self):
        header = support.genesis_header()
        header["rpc_result"]["withdrawalsRoot"] = support.hash32()
        with self.assertRaisesRegex(FormatError, "baseFee"):
            header_fields(header)
        header = support.genesis_header()
        header["rpc_result"].update(
            {"baseFeePerGas": "0x1", "withdrawalsRoot": support.hash32(), "blobGasUsed": "0x0"}
        )
        with self.assertRaisesRegex(FormatError, "Cancun"):
            header_fields(header)

    def test_wrong_hash_and_field_mutation_fail(self):
        header = support.genesis_header()
        header["hash"] = header["rpc_result"]["hash"] = support.hash32("ff")
        with self.assertRaisesRegex(IntegrityError, "hash mismatch"):
            verify_header(header)
        header = support.genesis_header()
        header["rpc_result"]["gasUsed"] = "0x1"
        with self.assertRaisesRegex(IntegrityError, "hash mismatch"):
            verify_header(header)

    def test_missing_fields_extra_data_and_fixed_widths_fail(self):
        header = support.genesis_header()
        del header["rpc_result"]["difficulty"]
        with self.assertRaisesRegex(FormatError, "difficulty"):
            compute_header_hash(header)
        header = support.genesis_header()
        header["rpc_result"]["extraData"] = "0x" + "00" * 33
        with self.assertRaisesRegex(FormatError, "extraData"):
            compute_header_hash(header)
        header = support.genesis_header()
        header["rpc_result"]["nonce"] = "0x00"
        with self.assertRaisesRegex(FormatError, "8 bytes"):
            compute_header_hash(header)


if __name__ == "__main__":
    unittest.main()
