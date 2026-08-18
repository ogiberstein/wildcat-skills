"""The evidence bundle's prose cannot drift from its committed boundary."""

from pathlib import Path
import json
import re
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
EVIDENCE = PLUGIN / "docs" / "evidence"
BUNDLE = EVIDENCE / "wildcat-app-v2.md"
BOUNDARY = EVIDENCE / "wildcat-app-v2.boundary.json"


def capture_lines():
    text = BUNDLE.read_text(encoding="utf-8")
    return dict(re.findall(r"<!-- evidence:(\S+) (\S+) -->", text))


class EvidenceBundleTests(unittest.TestCase):
    def test_the_boundary_document_parses_with_the_shipped_schema(self):
        document = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        self.assertEqual(document["schema"], 1)
        self.assertEqual(document["tool"], "horos")

    def test_the_quoted_totals_equal_the_boundary_documents(self):
        lines = capture_lines()
        document = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        counts = document["counts"]
        self.assertEqual(int(lines["entries"]), len(document["entries"]))
        self.assertEqual(int(lines["files_walked"]), counts["files_walked"])
        self.assertEqual(
            int(lines["files_skipped_unreadable"]), counts["files_skipped_unreadable"]
        )
        for category in ("generated", "binary", "lockfile", "blob"):
            self.assertEqual(
                int(lines["bytes_" + category]), counts["bytes_" + category]
            )
        classified = sum(entry["bytes"] for entry in document["entries"])
        self.assertEqual(int(lines["classified_bytes"]), classified)

    def test_the_bundle_names_its_commit(self):
        lines = capture_lines()
        self.assertRegex(lines["commit"], r"^[0-9a-f]{40}$")
        self.assertIn(lines["commit"], BUNDLE.read_text(encoding="utf-8"))

    def test_the_criterion_arithmetic_holds(self):
        lines = capture_lines()
        share = 100 * int(lines["classified_bytes"]) / int(lines["total_bytes"])
        self.assertGreaterEqual(share, 60.0)
        self.assertAlmostEqual(share, 80.3, places=1)


if __name__ == "__main__":
    unittest.main()
