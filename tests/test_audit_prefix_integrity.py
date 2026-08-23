"""Keep every audit byte present when issue 429 started."""

from pathlib import Path
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "audit-prefixes.json"
AUDIT_PATHS = (
    "audit/AUDIT.md",
    "plugins/ariadne/audit/AUDIT.md",
    "plugins/hexaemeron/audit/AUDIT.md",
    "plugins/pandects/audit/AUDIT.md",
    "plugins/probitas/audit/AUDIT.md",
    "plugins/tabularium/audit/AUDIT.md",
)


def check_prefix(data, expected):
    size = expected["bytes"]
    if len(data) < size:
        raise ValueError(f"{expected['path']}: protected prefix was shortened")
    prefix = data[:size]
    digest = hashlib.sha256(prefix).hexdigest()
    if digest != expected["sha256"]:
        raise ValueError(f"{expected['path']}: protected prefix digest changed")
    lines = prefix.count(b"\n")
    if lines != expected["lines"]:
        raise ValueError(f"{expected['path']}: protected prefix line count changed")


def check_starting_ref(data, expected):
    """Refuse a fixture that re-blesses bytes absent from its named commit."""
    if len(data) != expected["bytes"]:
        raise ValueError(f"{expected['path']}: starting ref byte length disagrees")
    if hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise ValueError(f"{expected['path']}: starting ref digest disagrees")
    if data.count(b"\n") != expected["lines"]:
        raise ValueError(f"{expected['path']}: starting ref line count disagrees")


def source_at(ref, path):
    return subprocess.run(
        ["git", "--no-replace-objects", "show", f"{ref}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def current_source(root, path):
    """Read one lexical regular path without following a substituted alias."""
    candidate = root / path
    try:
        resolved = candidate.resolve(strict=True)
        info = candidate.lstat()
    except OSError as exc:
        raise ValueError(f"{path}: protected path cannot be read") from exc
    if resolved != candidate or not stat.S_ISREG(info.st_mode):
        raise ValueError(f"{path}: protected path traverses a symlink")
    return candidate.read_bytes()


class AuditPrefixIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_identity_and_current_prefixes(self):
        self.assertEqual(self.fixture["schema"], "fiat-audit-prefixes/v1")
        self.assertEqual(
            self.fixture["starting_ref"],
            "ced4e6f439021b7509833ed5da66348c86d22f01",
        )
        self.assertEqual(
            tuple(item["path"] for item in self.fixture["prefixes"]),
            AUDIT_PATHS,
        )
        for expected in self.fixture["prefixes"]:
            with self.subTest(path=expected["path"]):
                check_starting_ref(
                    source_at(self.fixture["starting_ref"], expected["path"]),
                    expected,
                )
                check_prefix(current_source(ROOT, expected["path"]), expected)

    def test_a_changed_prefix_cannot_be_reblessed_in_the_fixture(self):
        expected = self.fixture["prefixes"][2]
        original = source_at(self.fixture["starting_ref"], expected["path"])
        changed = bytearray(original)
        changed[10] ^= 1
        reblessed = {
            **expected,
            "sha256": hashlib.sha256(changed).hexdigest(),
        }

        check_prefix(bytes(changed), reblessed)
        with self.assertRaisesRegex(ValueError, "starting ref digest disagrees"):
            check_starting_ref(original, reblessed)

    def test_edit_truncate_and_insertion_fail_while_append_passes(self):
        expected = self.fixture["prefixes"][2]
        original = (ROOT / expected["path"]).read_bytes()

        edited = bytearray(original)
        edited[10] ^= 1
        with self.assertRaisesRegex(ValueError, "digest changed"):
            check_prefix(bytes(edited), expected)
        with self.assertRaisesRegex(ValueError, "shortened"):
            check_prefix(original[:-1], expected)
        with self.assertRaisesRegex(ValueError, "digest changed"):
            check_prefix(original[:10] + b"x" + original[10:], expected)

        check_prefix(original + b"\nfuture round\n", expected)

    def test_a_substituted_protected_path_is_refused(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(os.path.realpath(raw_root))
            outside = root / "moved"
            outside.mkdir()
            (outside / "AUDIT.md").write_bytes(b"preserved bytes")

            final_alias = root / "AUDIT.md"
            final_alias.symlink_to(outside / "AUDIT.md")
            with self.assertRaisesRegex(ValueError, "traverses a symlink"):
                current_source(root, "AUDIT.md")

            final_alias.unlink()
            ancestor_alias = root / "audit"
            ancestor_alias.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "traverses a symlink"):
                current_source(root, "audit/AUDIT.md")


if __name__ == "__main__":
    unittest.main()
