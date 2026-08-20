"""Digest and untrusted-reader refusals."""

import os
import tempfile
import unittest

from tests.support import SCRIPTS  # noqa: F401

from berean_lib import BereanError, digests, jsonio, paths


class HexTests(unittest.TestCase):
    def test_lowercase_hex_passes(self):
        digests.check_hex("a" * 64, "digest")

    def test_uppercase_hex_is_refused_not_folded(self):
        with self.assertRaises(BereanError):
            digests.check_hex("A" * 64, "digest")

    def test_wrong_length_is_refused(self):
        with self.assertRaises(BereanError):
            digests.check_hex("ab", "digest")


class FileTests(unittest.TestCase):
    def test_symlinks_are_refused(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "real.txt")
            with open(target, "w") as handle:
                handle.write("x")
            link = os.path.join(root, "link.txt")
            os.symlink(target, link)
            with self.assertRaises(BereanError):
                digests.read_file(link)

    def test_missing_files_are_refused(self):
        with self.assertRaises(BereanError):
            digests.read_file("/no/such/file")

    def test_oversize_files_are_refused(self):
        with tempfile.TemporaryDirectory() as root:
            big = os.path.join(root, "big.bin")
            with open(big, "wb") as handle:
                handle.truncate(digests.MAX_FILE_BYTES + 1)
            with self.assertRaises(BereanError):
                digests.read_file(big)


class ListingTests(unittest.TestCase):
    def test_a_rename_changes_the_listing_digest(self):
        digest = digests.of_bytes(b"same bytes")
        one = digests.of_listing([("a.md", digest)])
        two = digests.of_listing([("b.md", digest)])
        self.assertNotEqual(one, two)

    def test_order_does_not_change_the_listing_digest(self):
        entries = [("a.md", digests.of_bytes(b"a")), ("b.md", digests.of_bytes(b"b"))]
        self.assertEqual(digests.of_listing(entries), digests.of_listing(reversed(entries)))

    def test_control_characters_in_paths_are_refused(self):
        with self.assertRaises(BereanError):
            digests.of_listing([("a\nb.md", digests.of_bytes(b"a"))])


class JsonTests(unittest.TestCase):
    def test_duplicate_keys_are_refused(self):
        with self.assertRaises(BereanError):
            jsonio.loads('{"a": 1, "a": 2}')

    def test_floats_are_refused(self):
        with self.assertRaises(BereanError):
            jsonio.loads('{"a": 1.5}')

    def test_depth_over_the_ceiling_is_refused(self):
        text = "[" * 40 + "]" * 40
        with self.assertRaises(BereanError):
            jsonio.loads(text)

    def test_closed_field_tables_refuse_extras_and_absences(self):
        with self.assertRaises(BereanError):
            jsonio.require({"a": 1, "z": 2}, ("a", "b"), "thing")
        with self.assertRaises(BereanError):
            jsonio.require({"a": 1}, ("a", "b"), "thing")

    def test_booleans_are_not_whole_numbers(self):
        with self.assertRaises(BereanError):
            jsonio.whole_number(True, "count")


class PathTests(unittest.TestCase):
    def test_absolute_paths_are_refused(self):
        with self.assertRaises(BereanError):
            paths.usable("/etc/passwd")

    def test_parent_traversal_is_refused(self):
        with self.assertRaises(BereanError):
            paths.usable("a/../b.md")

    def test_backslashes_are_refused_not_normalised(self):
        with self.assertRaises(BereanError):
            paths.usable("a\\b.md")

    def test_plain_relative_paths_pass(self):
        self.assertEqual(paths.usable("docs/a.md"), "docs/a.md")


if __name__ == "__main__":
    unittest.main()
