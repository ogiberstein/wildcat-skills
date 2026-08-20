"""Canonical JSON refusals and determinism."""

import unittest

from tests.support import SCRIPTS  # noqa: F401  (puts scripts on sys.path)

from berean_lib import BereanError, canonical


class CanonicalTests(unittest.TestCase):
    def test_one_spelling_sorted_and_compact(self):
        self.assertEqual(canonical.dumps({"b": 1, "a": [1, 2]}), '{"a":[1,2],"b":1}')

    def test_utf8_is_not_escaped(self):
        self.assertEqual(canonical.dumps({"s": "café"}), '{"s":"café"}')

    def test_floats_are_refused(self):
        with self.assertRaises(BereanError):
            canonical.dumps({"x": 1.5})

    def test_nested_floats_are_refused_with_a_path(self):
        with self.assertRaises(BereanError) as caught:
            canonical.dumps({"a": [{"b": 2.0}]})
        self.assertIn("$.a[0].b", str(caught.exception))

    def test_non_finite_numbers_are_refused(self):
        with self.assertRaises(BereanError):
            canonical.dumps({"x": float("nan")})

    def test_non_string_keys_are_refused(self):
        with self.assertRaises(BereanError):
            canonical.dumps({1: "x"})

    def test_unserialisable_values_are_refused(self):
        with self.assertRaises(BereanError):
            canonical.dumps({"x": object()})

    def test_booleans_and_integers_stay_distinct(self):
        self.assertEqual(canonical.dumps({"a": True, "b": 1}), '{"a":true,"b":1}')

    def test_encode_is_the_dumps_bytes(self):
        value = {"k": "v"}
        self.assertEqual(canonical.encode(value), canonical.dumps(value).encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
