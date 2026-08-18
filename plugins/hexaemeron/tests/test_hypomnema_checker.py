"""The Hypomnema record lint catches pointers that lead nowhere.

A record pointing at something absent is worse than no record, because it
reads as though the reason exists and was checked.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "hypomnema" / "scripts" / "hypomnema.py"

spec = importlib.util.spec_from_file_location("hypomnema_lint", SCRIPT)
hypomnema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hypomnema)


def codes(source, *, siblings=(), adrs=None):
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        for name in siblings:
            target = base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("present", encoding="utf-8")
        path = base / "record.md"
        path.write_text(source, encoding="utf-8")
        return sorted(f.code for f in hypomnema.check(path, adrs))


class Links(unittest.TestCase):
    def test_it_flags_a_link_to_nothing(self):
        self.assertIn("H001", codes("See [the ledger](EVOLUTION.md)."))

    def test_it_allows_a_link_that_resolves(self):
        self.assertEqual([], codes("See [the ledger](EVOLUTION.md).",
                                   siblings=("EVOLUTION.md",)))

    def test_it_allows_an_external_link(self):
        self.assertEqual([], codes("See [the spec](https://example.org/spec)."))

    def test_it_allows_an_anchor_on_a_file_that_exists(self):
        self.assertEqual([], codes("See [rule four](rules.md#four).",
                                   siblings=("rules.md",)))

    def test_it_ignores_links_inside_a_code_fence(self):
        self.assertEqual([], codes("```\n[example](nowhere.md)\n```\n"))

    def test_it_ignores_an_image(self):
        self.assertEqual([], codes("![diagram](missing.png)"))


class Superseding(unittest.TestCase):
    def test_it_flags_a_successor_that_does_not_exist(self):
        self.assertIn("H002", codes("## Status\nSuperseded by ADR-009\n",
                                    adrs={"ADR-001"}))

    def test_it_allows_a_successor_that_exists(self):
        self.assertEqual([], codes("## Status\nSuperseded by ADR-009\n",
                                   adrs={"ADR-001", "ADR-009"}))


class Runbooks(unittest.TestCase):
    def test_it_flags_a_missing_runbook(self):
        self.assertIn("H003", codes("Alert: pending age. runbook: docs/runbooks/pending.md"))

    def test_it_allows_a_runbook_that_exists(self):
        self.assertEqual([], codes("Alert: pending age. runbook: docs/runbooks/pending.md",
                                   siblings=("docs/runbooks/pending.md",)))

    def test_it_ignores_prose_after_the_word_runbook(self):
        self.assertEqual([], codes(
            "Three lines is a runbook: what fired, what to check, who to wake."))


class Suppression(unittest.TestCase):
    def test_a_stated_reason_on_the_line_above_suppresses(self):
        self.assertEqual([], codes(
            "<!-- hypomnema: allow generated in the target repository -->\n"
            "See [generated output](invariants.md)."))

    def test_a_stated_reason_on_the_same_line_suppresses(self):
        self.assertEqual([], codes(
            "See [it](invariants.md). <!-- hypomnema: allow generated downstream -->"))

    def test_a_pragma_below_the_finding_does_not_suppress(self):
        self.assertIn("H001", codes(
            "See [generated output](invariants.md).\n"
            "<!-- hypomnema: allow generated in the target repository -->"))

    def test_a_bare_pragma_does_not_suppress(self):
        self.assertIn("H001", codes(
            "<!-- hypomnema: allow -->\nSee [generated output](invariants.md)."))


class OverTheMarketplace(unittest.TestCase):
    def test_first_party_records_all_resolve(self):
        marketplace = ROOT.parents[1]
        files = hypomnema.walk([str(marketplace / "plugins"), str(marketplace / "docs")])
        index = hypomnema.adr_index(files)
        findings = []
        for path in files:
            findings.extend(hypomnema.check(path, index))
        self.assertEqual([], [str(f) for f in findings])

    def test_the_vendored_suite_is_skipped_by_default(self):
        marketplace = ROOT.parents[1]
        paths = hypomnema.walk([str(marketplace / "plugins" / "hexaemeron" / "skills")])
        self.assertEqual([], [p for p in paths if "x-ray" in p.parts])


if __name__ == "__main__":
    unittest.main()
