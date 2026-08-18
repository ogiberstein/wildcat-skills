"""The shipped example proves the pipeline and the discipline cannot drift."""

from pathlib import Path
from unittest import mock
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN / "examples" / "fixture"


class DisciplineTests(unittest.TestCase):
    def test_the_security_review_rule_survives_in_the_final_skill_text(self):
        rule = "No reading boundary applies during security review."
        text = (PLUGIN / "skills" / "horos" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(rule, text)

    def test_the_committed_boundary_matches_a_fresh_scan_byte_for_byte(self):
        committed = (FIXTURE / horos.BOUNDARY_RELPATH).read_text(encoding="utf-8")
        fresh = horos.render(horos.boundary_document(horos.scan_tree(str(FIXTURE))))
        self.assertEqual(committed, fresh)

    def test_the_cli_json_output_matches_the_committed_boundary(self):
        committed = (FIXTURE / horos.BOUNDARY_RELPATH).read_text(encoding="utf-8")
        with mock.patch.object(sys, "stdout", new=io.StringIO()) as stdout:
            code = horos.main(["scan", str(FIXTURE), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), committed)

    def test_the_documented_mutation_makes_check_fail_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = os.path.join(tmp, "fixture")
            shutil.copytree(FIXTURE, copy, symlinks=True)
            os.unlink(os.path.join(copy, "yarn.lock"))
            out = io.StringIO()
            code = horos.check_tree(copy, out=out)
            self.assertEqual(code, 1)
            self.assertIn(
                "drift: yarn.lock: in the boundary but no longer evidenced",
                out.getvalue(),
            )

    def test_the_fixture_covers_every_shipped_rule_class(self):
        result = horos.scan_tree(str(FIXTURE))
        hard = result["entries"]
        candidates = result["candidates"]
        self.assertEqual(
            {entry["category"] for entry in hard},
            {"binary", "lockfile", "generated", "vendored"},
        )
        self.assertEqual(
            {entry["category"] for entry in candidates},
            {"binary", "generated", "blob", "asset"},
        )
        self.assertTrue(all(entry["grade"] == "hard" for entry in hard))
        self.assertTrue(all(entry["grade"] == "candidate" for entry in candidates))
        hard_evidence = " | ".join(entry["evidence"] for entry in hard)
        for family in (
            "marker",
            "corroborated by sample",
            "package-manager structure",
            "sourcemap",
            ".gitattributes",
            "file signature",
            "lockfile name",
        ):
            self.assertIn(family, hard_evidence)
        candidate_evidence = " | ".join(entry["evidence"] for entry in candidates)
        for family in (
            "null byte",
            "uncorroborated",
            "no newline",
            "mean line length",
            "svg root element",
            "migrations directory segment",
        ):
            self.assertIn(family, candidate_evidence)

    def test_the_readable_files_stay_readable(self):
        result = horos.scan_tree(str(FIXTURE))
        listed = [entry["path"] for entry in result["entries"]]
        listed += [entry["path"] for entry in result["candidates"]]
        self.assertNotIn("src/app.py", listed)
        self.assertNotIn("build/util.py", listed)

    def test_the_committed_candidates_match_a_fresh_scan_byte_for_byte(self):
        committed = (FIXTURE / horos.CANDIDATES_RELPATH).read_text(encoding="utf-8")
        fresh = horos.render(horos.candidates_document(horos.scan_tree(str(FIXTURE))))
        self.assertEqual(committed, fresh)


if __name__ == "__main__":
    unittest.main()
