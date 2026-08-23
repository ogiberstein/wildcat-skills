"""Keep every audit byte present when issue 429 started."""

from pathlib import Path
import hashlib
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "audit-prefixes.json"


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
        self.assertEqual(len(self.fixture["prefixes"]), 6)
        for expected in self.fixture["prefixes"]:
            with self.subTest(path=expected["path"]):
                check_prefix((ROOT / expected["path"]).read_bytes(), expected)

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


if __name__ == "__main__":
    unittest.main()
