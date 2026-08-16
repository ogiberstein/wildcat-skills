"""Fixture paths remain inside their root and never cross symlinks."""

from pathlib import Path
import os
import tempfile
import unittest

from lazarus_lib.errors import PathError, ResourceLimitError
from lazarus_lib.paths import (
    list_fixture_files,
    read_confined_bytes,
    validate_relative_path,
)


class PathTests(unittest.TestCase):
    def test_normal_relative_path_resolves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            target = root / "data" / "record.json"
            target.write_text("{}\n")
            self.assertEqual(
                read_confined_bytes(root, "data/record.json", max_bytes=100), b"{}\n"
            )
            self.assertEqual(list_fixture_files(root), {"data/record.json"})

    def test_absolute_traversal_backslash_and_non_normal_paths_fail(self):
        bad = ("/tmp/x", "../x", "a/../x", "a\\x", "./x", "x\x00y", "")
        for value in bad:
            with self.subTest(value=value), self.assertRaises(PathError):
                validate_relative_path(value)

    def test_file_and_directory_symlinks_fail(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "secret"
            external.write_text("secret")
            os.symlink(external, root / "linked-file")
            with self.assertRaisesRegex(PathError, "symlink"):
                read_confined_bytes(root, "linked-file", max_bytes=100)
            os.symlink(Path(outside), root / "linked-dir")
            with self.assertRaises(PathError):
                read_confined_bytes(root, "linked-dir/secret", max_bytes=100)
            with self.assertRaisesRegex(PathError, "symlink"):
                list_fixture_files(root)

    def test_missing_non_file_and_oversized_components_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "folder").mkdir()
            with self.assertRaises(PathError):
                read_confined_bytes(root, "missing", max_bytes=100)
            with self.assertRaisesRegex(PathError, "regular file"):
                read_confined_bytes(root, "folder", max_bytes=100)
            target = root / "large"
            target.write_bytes(b"12345")
            with self.assertRaises(ResourceLimitError):
                read_confined_bytes(root, "large", max_bytes=4)

    def test_fixture_entry_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one").mkdir()
            (root / "two").mkdir()
            (root / "three").mkdir()
            with self.assertRaises(ResourceLimitError):
                list_fixture_files(root, max_entries=2)


if __name__ == "__main__":
    unittest.main()
