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

    def test_clean_pointer_check_does_not_establish_record_correctness(self):
        self.assertEqual(
            [],
            codes(
                "See [the decision](decision.md).",
                siblings=("decision.md",),
            ),
        )

    def test_missing_pointer_recovers_when_target_is_restored(self):
        source = "See [the decision](decision.md)."
        self.assertIn("H001", codes(source))
        self.assertEqual([], codes(source, siblings=("decision.md",)))


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


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hypomnema"

COMPLETE_RECORD = """# ADR-051: A complete specimen

## Status

Accepted, 2026-08-21.

## Context

What forced a choice.

## Decision

What was chosen.

## Alternatives

- What lost, and why.

## Consequences

What this commits us to.
"""


def record_codes(source, name="ADR-051-complete.md", directory="decisions"):
    with tempfile.TemporaryDirectory() as base:
        target = Path(base) / directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
        return sorted(f.code for f in hypomnema.check(target))


class RecordShape(unittest.TestCase):
    def test_a_complete_record_is_clean(self):
        self.assertEqual([], record_codes(COMPLETE_RECORD))

    def test_each_of_the_five_sections_is_required(self):
        for name in hypomnema.SECTIONS:
            with self.subTest(section=name):
                source = COMPLETE_RECORD.replace(f"## {name}\n", f"## Kept out\n")
                found = record_codes(source)
                self.assertIn("H004", found)

    def test_the_finding_names_the_missing_section(self):
        source = COMPLETE_RECORD.replace("## Alternatives\n", "## Options\n")
        with tempfile.TemporaryDirectory() as base:
            target = Path(base) / "decisions" / "ADR-051-complete.md"
            target.parent.mkdir(parents=True)
            target.write_text(source, encoding="utf-8")
            found = hypomnema.check(target)
        self.assertEqual(["H004"], [f.code for f in found])
        self.assertIn("## Alternatives", found[0].message)

    def test_an_undated_status_is_a_finding(self):
        source = COMPLETE_RECORD.replace("Accepted, 2026-08-21.", "Accepted.")
        self.assertEqual(["H005"], record_codes(source))

    def test_an_empty_status_section_is_a_finding(self):
        source = COMPLETE_RECORD.replace("Accepted, 2026-08-21.\n", "")
        self.assertEqual(["H005"], record_codes(source))

    def test_a_file_not_named_as_a_record_earns_no_shape_verdict(self):
        source = COMPLETE_RECORD.replace("## Alternatives\n", "## Options\n")
        self.assertEqual([], record_codes(source, name="notes.md"))

    def test_a_record_name_outside_a_decisions_directory_earns_no_shape_verdict(self):
        source = COMPLETE_RECORD.replace("## Alternatives\n", "## Options\n")
        self.assertEqual([], record_codes(source, directory="drafts"))

    def test_a_section_heading_inside_a_fence_does_not_count(self):
        source = COMPLETE_RECORD.replace(
            "## Alternatives\n\n- What lost, and why.\n",
            "```markdown\n## Alternatives\n```\n")
        self.assertEqual(["H004"], record_codes(source))

    def test_a_pragma_on_the_first_line_suppresses_the_missing_section(self):
        source = COMPLETE_RECORD.replace(
            "# ADR-051: A complete specimen",
            "# ADR-051: A complete specimen "
            "<!-- hypomnema: allow imported before the template settled -->"
        ).replace("## Alternatives\n", "## Options\n")
        self.assertEqual([], record_codes(source))

    def test_a_pragma_on_the_status_heading_suppresses_the_dated_check(self):
        source = COMPLETE_RECORD.replace(
            "## Status", "## Status <!-- hypomnema: allow imported undated -->"
        ).replace("Accepted, 2026-08-21.", "Accepted.")
        self.assertEqual([], record_codes(source))

    def test_the_fixture_records_name_each_omission(self):
        findings = []
        for path in sorted((FIXTURES / "decisions").glob("*.md")):
            findings.extend(hypomnema.check(path))
        self.assertEqual(sorted(f.code for f in findings),
                         ["H004", "H004", "H004", "H005"])

    def test_the_walk_skips_fixture_specimens_by_default(self):
        marketplace = ROOT.parents[1]
        paths = hypomnema.walk([str(marketplace / "plugins")])
        self.assertEqual([], [p for p in paths if "fixtures" in p.parts])

    def test_naming_a_fixtures_path_still_reads_it(self):
        paths = hypomnema.walk([str(FIXTURES / "decisions")])
        self.assertEqual(2, len(paths))

    def test_the_trees_six_records_pass(self):
        marketplace = ROOT.parents[1]
        decisions = marketplace / "docs" / "decisions"
        paths = hypomnema.walk([str(decisions)])
        self.assertEqual(6, len(paths))
        findings = []
        for path in paths:
            findings.extend(hypomnema.check(path))
        self.assertEqual([], [str(f) for f in findings])


if __name__ == "__main__":
    unittest.main()
