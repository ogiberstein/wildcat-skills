"""Canonical JSON stays strict and byte-stable."""

from pathlib import Path
import os
import tempfile
import unittest

from lazarus_lib.canonical import dump, dump_jsonl, dumps, load, load_jsonl, loads
from lazarus_lib.errors import FormatError, ResourceLimitError


class CanonicalTests(unittest.TestCase):
    def test_object_insertion_order_does_not_change_bytes(self):
        left = {"z": [2, 1], "a": {"b": True, "a": None}}
        right = {"a": {"a": None, "b": True}, "z": [2, 1]}
        self.assertEqual(dumps(left), dumps(right))
        self.assertEqual(dumps(left), b'{"a":{"a":null,"b":true},"z":[2,1]}')
        self.assertEqual(dumps({"text": "caf\u00e9"}), b'{"text":"caf\xc3\xa9"}')

    def test_json_and_jsonl_have_one_trailing_newline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(dump(root / "one.json", {"b": 2, "a": 1}), b'{"a":1,"b":2}\n')
            data = dump_jsonl(root / "rows.jsonl", [{"id": 2}, {"id": 1}], sort_key=lambda row: row["id"])
            self.assertEqual(data, b'{"id":1}\n{"id":2}\n')
            self.assertEqual(load_jsonl(root / "rows.jsonl"), [{"id": 1}, {"id": 2}])

    def test_duplicate_keys_and_non_integer_numbers_fail(self):
        with self.assertRaisesRegex(FormatError, "duplicate JSON key"):
            loads(b'{"a":1,"a":2}')
        for source in (b'{"n":1.5}', b'{"n":NaN}', b'{"n":Infinity}'):
            with self.subTest(source=source), self.assertRaises(FormatError):
                loads(source)

    def test_invalid_utf8_and_unsupported_values_fail(self):
        with self.assertRaisesRegex(FormatError, "not UTF-8"):
            loads(b'"\xff"')
        with self.assertRaisesRegex(FormatError, "unsupported JSON value"):
            dumps({"bad": {1, 2}})

    def test_byte_depth_record_and_count_limits_fail_closed(self):
        with self.assertRaises(ResourceLimitError):
            loads(b'{"a":1}', max_bytes=3)
        nested = None
        for _ in range(66):
            nested = [nested]
        with self.assertRaises(ResourceLimitError):
            dumps(nested)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = Path(directory) / "rows.jsonl"
            path.write_bytes(b'{"a":1}\n{"a":2}\n')
            with self.assertRaises(ResourceLimitError):
                load_jsonl(path, max_records=1)
            with self.assertRaises(ResourceLimitError):
                load_jsonl(path, max_record_bytes=4)
            with self.assertRaises(ResourceLimitError):
                dump(root / "large.json", {"value": "abcdef"}, max_bytes=4)
            with self.assertRaises(ResourceLimitError):
                dump_jsonl(path, [{"value": "abcdef"}], max_record_bytes=4)
            with self.assertRaises(ResourceLimitError):
                dump_jsonl(path, [{"a": 1}, {"b": 2}], max_bytes=8)

    def test_jsonl_requires_nonempty_newline_terminated_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.jsonl"
            path.write_bytes(b'{"a":1}')
            with self.assertRaisesRegex(FormatError, "trailing newline"):
                load_jsonl(path)
            path.write_bytes(b'\n')
            with self.assertRaisesRegex(FormatError, "empty"):
                load_jsonl(path)

    def test_jsonl_record_limit_stops_an_oversized_iterable(self):
        consumed = []

        def records():
            for number in range(100):
                consumed.append(number)
                yield {"number": number}

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ResourceLimitError):
                dump_jsonl(Path(directory) / "rows.jsonl", records(), max_records=2)
        self.assertEqual(consumed, [0, 1, 2])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are POSIX-only")
    def test_direct_loaders_reject_a_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            os.mkfifo(path)
            with self.assertRaisesRegex(FormatError, "regular file"):
                load(path)
            with self.assertRaisesRegex(FormatError, "regular file"):
                load_jsonl(path)


if __name__ == "__main__":
    unittest.main()
