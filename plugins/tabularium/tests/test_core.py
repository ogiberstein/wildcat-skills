"""Canonical bytes and numeric boundaries."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from . import support
from tabularium_lib import core as core_module
from tabularium_lib.core import (
    MAX_SAFE_INTEGER,
    TabulariumError,
    canonical_json,
    jsonl_bytes,
    load_json,
    safe_integer,
    sha256_file,
    loads_json,
)


class CoreTests(unittest.TestCase):
    def test_canonical_json_is_sorted_compact_and_utf8(self):
        self.assertEqual(
            canonical_json({"z": 1, "a": "café"}),
            '{"a":"café","z":1}'.encode("utf-8"),
        )

    def test_jsonl_has_one_final_newline_per_row_and_keeps_order(self):
        self.assertEqual(jsonl_bytes([{"b": 2}, {"a": 1}]), b'{"b":2}\n{"a":1}\n')

    def test_floating_point_values_are_refused(self):
        with self.assertRaisesRegex(TabulariumError, "floating-point"):
            canonical_json({"amount": 0.1})

    def test_unsafe_integers_are_refused(self):
        with self.assertRaisesRegex(TabulariumError, "safe range"):
            canonical_json({"number": MAX_SAFE_INTEGER + 1})

    def test_duplicate_json_keys_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"a":1,"a":2}')
            with self.assertRaisesRegex(TabulariumError, "duplicate JSON key"):
                load_json(path)

    def test_sha256_file_hashes_the_actual_bytes(self):
        fixture = support.FIXTURES / "minimal-snapshot.json"
        self.assertEqual(sha256_file(fixture), hashlib.sha256(fixture.read_bytes()).hexdigest())

    def test_safe_integer_rejects_bool_float_negative_and_large_values(self):
        for value in (True, 1.0, -1, MAX_SAFE_INTEGER + 1):
            with self.subTest(value=value), self.assertRaises(TabulariumError):
                safe_integer(value, "field")

    def test_extremely_long_json_integer_uses_the_controlled_error_path(self):
        with self.assertRaisesRegex(TabulariumError, "not valid JSON"):
            loads_json(("1" * 10000).encode(), "huge integer")

    def test_deeply_nested_values_do_not_break_the_validation_walk(self):
        value = 0
        for _ in range(2000):
            value = [value]
        self.assertEqual(canonical_json(value).count(b"["), 2000)

    def test_encoder_recursion_error_uses_the_controlled_error_path(self):
        with mock.patch.object(core_module.json, "dumps", side_effect=RecursionError):
            with self.assertRaisesRegex(TabulariumError, "cannot be canonical JSON"):
                canonical_json({"value": 1})
