"""The Protasis runbook schema check catches a step that omits a field.

A step missing its exit command is invisible until someone reads the runbook
carefully, and the phase that reads it carefully has already started building.
"""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "protasis" / "scripts" / "protasis.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "protasis"
REPO = ROOT.parents[1]

spec = importlib.util.spec_from_file_location("protasis_check", SCRIPT)
protasis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protasis)

COMPLETE_STEP = """## Step 1: A complete step

**Goal.** Do the thing.
**Entry.** A clean tree.
**Exit.** Proved by `pytest`.
**Files.** `a.py`.
**Tests.** One case.
**Disciplines.** none, docs only.
"""


def findings(source):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "runbook.md"
        path.write_text(source, encoding="utf-8")
        return protasis.check(path)


def codes(source):
    return sorted(f.code for f in findings(source))


def without(field):
    """The complete step with one required field removed."""
    keep = [line for line in COMPLETE_STEP.splitlines()
            if not line.startswith(f"**{field}.**")]
    return "\n".join(keep) + "\n"


class RequiredFields(unittest.TestCase):
    def test_a_complete_step_is_clean(self):
        self.assertEqual(codes(COMPLETE_STEP), [])

    def test_each_required_field_is_required(self):
        for field in protasis.REQUIRED:
            with self.subTest(field=field):
                self.assertIn("P001", codes(without(field)))

    def test_the_finding_names_the_missing_field(self):
        found = findings(without("Disciplines"))
        self.assertEqual(len(found), 1)
        self.assertIn("**Disciplines.**", found[0].message)

    def test_the_finding_names_the_step_it_is_in(self):
        found = findings(without("Goal"))
        self.assertIn("A complete step", found[0].message)

    def test_the_finding_points_at_the_heading_line(self):
        found = findings("\n" + without("Goal"))
        self.assertEqual(found[0].line, 2)


class ExitCommands(unittest.TestCase):
    def test_an_exit_with_no_command_is_a_finding(self):
        source = COMPLETE_STEP.replace("**Exit.** Proved by `pytest`.",
                                       "**Exit.** Reviewed and working.")
        self.assertIn("P002", codes(source))

    def test_a_fenced_block_counts_as_a_command(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** Proved by the suite.\n\n```bash\npytest\n```\n")
        self.assertNotIn("P002", codes(source))

    def test_an_inline_span_counts_as_a_command(self):
        self.assertNotIn("P002", codes(COMPLETE_STEP))

    def test_no_exit_reports_the_missing_field_not_the_missing_command(self):
        self.assertEqual(codes(without("Exit")), ["P001"])

    def test_another_field_s_code_does_not_answer_for_the_exit(self):
        """The guard for the step-wide search.

        `**Files.** `a.py`` is close to universal, so a command search over the
        whole step lets any other field answer for the exit and P002 never
        fires on a real runbook.
        """
        source = COMPLETE_STEP.replace("**Exit.** Proved by `pytest`.",
                                       "**Exit.** Reviewed and working.")
        self.assertIn("`a.py`", source)
        self.assertIn("P002", codes(source))

    def test_a_fenced_block_after_the_exit_still_counts(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** Proved by the suite.\n\n```bash\npytest\n```")
        self.assertNotIn("P002", codes(source))

    def test_a_fenced_block_under_a_later_field_does_not_count(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.", "**Exit.** Reviewed.").replace(
            "**Tests.** One case.", "**Tests.** One case.\n\n```bash\npytest\n```")
        self.assertIn("P002", codes(source))


class Documents(unittest.TestCase):
    def test_a_document_with_no_step_is_a_finding(self):
        self.assertEqual(codes("# Title\n\n## Steps\n\nDecided later.\n"),
                         ["P003"])

    def test_a_step_heading_inside_a_fence_is_not_a_step(self):
        source = "# Title\n\n```markdown\n## Step 1: Example\n```\n"
        self.assertEqual(codes(source), ["P003"])

    def test_a_fenced_heading_does_not_truncate_the_last_step(self):
        """The guard for fence tracking in the end scan.

        A runbook that quotes a step heading inside an example, which this
        repository's own contract does, would otherwise cut its last step short
        at the quote and report the fields below it missing.
        """
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** Proved by:\n\n```markdown\n## Step 99: quoted, not real\n```")
        self.assertEqual(codes(source), [])

    def test_a_tilde_fence_is_a_fence(self):
        """The guard for backtick-only fence matching.

        Tildes are a CommonMark fence, so a runbook using them had its examples
        read as real content: a quoted step heading became a step with no fields
        and the document collected findings it had not earned. A false positive
        costs more trust than a miss.
        """
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** see\n\n~~~\n## Step 9: quoted, not real\n~~~")
        self.assertEqual(codes(source), [])

    def test_a_fence_is_closed_only_by_its_own_marker(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** see\n\n~~~\n```\n## Step 9: quoted\n```\n~~~")
        self.assertEqual(codes(source), [])

    def test_a_longer_fence_run_is_a_fence(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** see\n\n````\n## Step 9: quoted\n````")
        self.assertEqual(codes(source), [])

    def test_a_trailing_section_is_not_read_into_the_last_step(self):
        source = COMPLETE_STEP + "\n## Notes\n\n**Goal.** Not a step field.\n"
        self.assertEqual(codes(source), [])

    def test_a_missing_path_is_reported_not_raised(self):
        found = protasis.check(Path("does-not-exist-9d3f.md"))
        self.assertEqual([f.code for f in found], ["P000"])

    def test_a_directory_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as directory:
            found = protasis.check(Path(directory))
        self.assertEqual([f.code for f in found], ["P000"])

    def test_an_oversized_document_is_refused(self):
        source = COMPLETE_STEP + ("x" * (protasis.MAX_BYTES + 1))
        self.assertEqual(codes(source), ["P000"])

    def test_steps_past_the_cap_are_reported_not_dropped(self):
        """The guard for silent truncation.

        Capping the work is right; capping it and still reporting clean is the
        false confidence this module exists to avoid. A broken step past the cap
        must not hide behind a clean verdict.
        """
        capped = "\n".join(COMPLETE_STEP.replace("Step 1:", f"Step {n}:")
                           for n in range(1, protasis.MAX_STEPS + 1))
        source = capped + "\n## Step 9999: Broken\n\n**Goal.** only this.\n"
        found = codes(source)
        self.assertIn("P004", found)

    def test_a_dropped_step_does_not_answer_for_the_last_tracked_one(self):
        """The guard for span absorption past the cap.

        The last tracked step's body ran to the next non-step heading, so a step
        dropped by the cap donated its fields upward and the broken step above
        it passed while missing five of six.
        """
        original = protasis.MAX_STEPS
        try:
            protasis.MAX_STEPS = 2
            sound = COMPLETE_STEP.replace("Step 1:", "Step 1:")
            broken = "## Step 2: Broken and last tracked\n\n**Goal.** only this.\n"
            past = COMPLETE_STEP.replace("Step 1:", "Step 3:")
            found = codes(sound + "\n" + broken + "\n" + past)
        finally:
            protasis.MAX_STEPS = original
        self.assertEqual(found.count("P001"), 5, found)
        self.assertIn("P004", found)

    def test_a_document_inside_the_cap_reports_no_truncation(self):
        capped = "\n".join(COMPLETE_STEP.replace("Step 1:", f"Step {n}:")
                           for n in range(1, protasis.MAX_STEPS + 1))
        self.assertEqual(codes(capped), [])


class Suppression(unittest.TestCase):
    def test_an_allow_comment_above_the_heading_suppresses_the_step(self):
        source = "<!-- protasis: allow fields live upstream -->\n" + \
                 "## Step 1: Bare\n"
        self.assertEqual(codes(source), [])

    def test_an_allow_comment_on_the_heading_line_suppresses_the_step(self):
        source = "## Step 1: Bare <!-- protasis: allow fields live upstream -->\n"
        self.assertEqual(codes(source), [])

    def test_an_allow_comment_needs_a_reason(self):
        source = "<!-- protasis: allow -->\n## Step 1: Bare\n"
        self.assertIn("P001", codes(source))


class Invocation(unittest.TestCase):
    def test_clean_exits_zero(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = protasis.main([str(FIXTURES / "complete-runbook.md")])
        self.assertEqual(code, 0)
        self.assertIn("clean", buffer.getvalue())

    def test_findings_exit_one(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = protasis.main([str(FIXTURES / "incomplete-runbook.md")])
        self.assertEqual(code, 1)

    def test_json_format_is_machine_readable(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            protasis.main([str(FIXTURES / "incomplete-runbook.md"),
                           "--format", "json"])
        payload = json.loads(buffer.getvalue())
        self.assertTrue(payload)
        self.assertEqual(sorted(payload[0]), ["code", "line", "message", "path"])

    def test_no_paths_is_a_bad_invocation(self):
        with self.assertRaises(SystemExit) as caught:
            with redirect_stdout(io.StringIO()):
                protasis.main([])
        self.assertEqual(caught.exception.code, 2)


class Fixtures(unittest.TestCase):
    def test_the_incomplete_fixture_catches_every_omission(self):
        found = protasis.check(FIXTURES / "incomplete-runbook.md")
        missing = {f.message.split("**")[1] for f in found if f.code == "P001"}
        self.assertEqual(missing, {f"{name}." for name in protasis.REQUIRED})
        self.assertEqual(sum(1 for f in found if f.code == "P002"), 1)

    def test_this_runs_own_runbook_is_clean(self):
        """The acceptance condition: the contract's first runbook passes."""
        runbook = REPO / "docs" / "protasis-discipline-cores" / "runbook.md"
        self.assertTrue(runbook.is_file(), runbook)
        self.assertEqual(protasis.check(runbook), [])


if __name__ == "__main__":
    unittest.main()
