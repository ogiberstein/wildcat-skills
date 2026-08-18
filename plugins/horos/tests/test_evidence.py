"""The evidence bundle's prose cannot drift from its committed boundary."""

from pathlib import Path
import json
import re
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
EVIDENCE = PLUGIN / "docs" / "evidence"
BUNDLE = EVIDENCE / "wildcat-app-v2.md"
BOUNDARY = EVIDENCE / "wildcat-app-v2.boundary.json"
BUNDLE_2 = EVIDENCE / "wildcat-app-v2-rules.md"
BOUNDARY_2 = EVIDENCE / "wildcat-app-v2-rules.boundary.json"


def capture_lines(bundle=BUNDLE, tag="evidence"):
    text = bundle.read_text(encoding="utf-8")
    return dict(re.findall(rf"<!-- {tag}:(\S+) (\S+) -->", text))


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


class SecondCaptureTests(unittest.TestCase):
    def test_the_quoted_totals_equal_the_boundary_documents(self):
        lines = capture_lines(BUNDLE_2, "evidence2")
        document = json.loads(BOUNDARY_2.read_text(encoding="utf-8"))
        counts = document["counts"]
        self.assertEqual(int(lines["entries"]), len(document["entries"]))
        self.assertEqual(int(lines["files_walked"]), counts["files_walked"])
        for category in ("generated", "binary", "lockfile", "blob", "asset"):
            self.assertEqual(
                int(lines["bytes_" + category]), counts["bytes_" + category]
            )
        classified = sum(entry["bytes"] for entry in document["entries"])
        self.assertEqual(int(lines["classified_bytes"]), classified)

    def test_both_captures_name_the_same_commit(self):
        self.assertEqual(
            capture_lines()["commit"], capture_lines(BUNDLE_2, "evidence2")["commit"]
        )

    def test_the_delta_is_exactly_the_two_rule_families(self):
        old = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        new = json.loads(BOUNDARY_2.read_text(encoding="utf-8"))
        old_paths = {entry["path"] for entry in old["entries"]}
        new_paths = {entry["path"] for entry in new["entries"]}
        self.assertEqual(old_paths - new_paths, set())
        for path in new_paths - old_paths:
            self.assertTrue(
                path.endswith(".svg")
                or (path.endswith(".sql") and "migrations" in path.split("/")),
                path,
            )

    def test_the_second_share_exceeds_the_first(self):
        first = capture_lines()
        second = capture_lines(BUNDLE_2, "evidence2")
        self.assertEqual(first["total_bytes"], second["total_bytes"])
        self.assertGreater(
            int(second["classified_bytes"]), int(first["classified_bytes"])
        )
        share = 100 * int(second["classified_bytes"]) / int(second["total_bytes"])
        self.assertAlmostEqual(share, 83.3, places=1)


if __name__ == "__main__":
    unittest.main()
