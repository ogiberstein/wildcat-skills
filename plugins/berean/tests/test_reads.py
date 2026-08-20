"""Preserved read records: recomputed keys, closed outcomes, one spelling."""

import os
import tempfile
import unittest

from tests.support import SCRIPTS  # noqa: F401

from berean_lib import BereanError, canonical, reads


def record(method, params, result="0x01", **overrides):
    body = {
        "schema_version": 1,
        "request_key": reads.request_key(method, params),
        "method": method,
        "params": params,
        "required": True,
        "evidence": "recorded-rpc",
        "outcome": {"result": result},
    }
    body.update(overrides)
    return body


def write_reads(path, records):
    lines = [canonical.dumps(item) for item in records]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


class RequestKeyTests(unittest.TestCase):
    def test_the_key_is_the_canonical_request_digest(self):
        key = reads.request_key("eth_getStorageAt", ["0xabc", "0x0", "0xc7da16"])
        self.assertRegex(key, "^[0-9a-f]{64}$")
        again = reads.request_key("eth_getStorageAt", ["0xabc", "0x0", "0xc7da16"])
        self.assertEqual(key, again)

    def test_params_order_changes_the_key(self):
        one = reads.request_key("m", ["a", "b"])
        two = reads.request_key("m", ["b", "a"])
        self.assertNotEqual(one, two)

    def test_non_list_params_are_refused(self):
        with self.assertRaises(BereanError):
            reads.request_key("m", {"a": 1})


class RecordTests(unittest.TestCase):
    def test_a_preserved_record_validates(self):
        reads.validate_record(record("eth_getCode", ["0xabc", "0xc7da16"]))

    def test_a_forged_key_is_refused(self):
        item = record("eth_getCode", ["0xabc", "0xc7da16"])
        item["request_key"] = reads.request_key("eth_getCode", ["0xdef", "0xc7da16"])
        with self.assertRaises(BereanError):
            reads.validate_record(item)

    def test_an_outcome_with_result_and_error_is_refused(self):
        item = record("m", [])
        item["outcome"] = {"result": "0x01", "error": {"code": 1, "message": "no"}}
        with self.assertRaises(BereanError):
            reads.validate_record(item)

    def test_an_unknown_evidence_class_is_refused(self):
        item = record("m", [], evidence="proof_backed")
        with self.assertRaises(BereanError):
            reads.validate_record(item)

    def test_an_undeclared_field_is_refused(self):
        item = record("m", [])
        item["verdict"] = "fine"
        with self.assertRaises(BereanError):
            reads.validate_record(item)

    def test_an_error_outcome_needs_code_and_message(self):
        item = record("m", [])
        item["outcome"] = {"error": {"code": -32070}}
        with self.assertRaises(BereanError):
            reads.validate_record(item)


class FileTests(unittest.TestCase):
    def test_a_sorted_file_loads_keyed_by_request(self):
        with tempfile.TemporaryDirectory() as root:
            items = sorted(
                (record("eth_getCode", ["0xabc", "0xc7da16"]), record("eth_getStorageAt", ["0xabc", "0x0", "0xc7da16"])),
                key=lambda item: item["request_key"],
            )
            path = os.path.join(root, "reads.jsonl")
            write_reads(path, items)
            loaded = reads.load(path)
            self.assertEqual(sorted(loaded), [item["request_key"] for item in items])

    def test_an_unsorted_file_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            items = sorted(
                (record("a_method", []), record("b_method", [])),
                key=lambda item: item["request_key"],
                reverse=True,
            )
            path = os.path.join(root, "reads.jsonl")
            write_reads(path, items)
            with self.assertRaises(BereanError):
                reads.load(path)

    def test_a_duplicate_key_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            item = record("a_method", [])
            path = os.path.join(root, "reads.jsonl")
            write_reads(path, [item, item])
            with self.assertRaises(BereanError):
                reads.load(path)

    def test_an_empty_file_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "reads.jsonl")
            with open(path, "w", encoding="utf-8"):
                pass
            with self.assertRaises(BereanError):
                reads.load(path)


if __name__ == "__main__":
    unittest.main()
