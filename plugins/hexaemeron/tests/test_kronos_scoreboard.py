"""The Kronos scoreboard records a ranking pass so the next one can be compared.

Kronos reranks from scratch every pass, so an axis score that moves for a job
nobody touched is invisible. These cases hold the writer to the two things that
make the record worth keeping: it refuses a pass it cannot vouch for, and the
held-job hash it writes is the one the ledger itself records.
"""

import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "kronos" / "scripts" / "kronos.py"
REPO = ROOT.parents[1]

spec = importlib.util.spec_from_file_location("kronos_scoreboard", SCRIPT)
kronos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kronos)


LEDGER = """# Example evolution ledger

- Current version: `example-v0.2.0`
- Frontier status: `open`
- Frontier revision: `some-revision`
- Current frontier: A frontier sentence.
- Next Fiat job: Do the thing that is held.
"""


def canonical_digest(status, revision, frontier, job):
    line = "|".join((status, revision, frontier, job)) + "\n"
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


class ScoreboardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.scoreboard = self.root / ".kronos" / "scoreboard.jsonl"
        (self.root / "alpha").mkdir()
        (self.root / "alpha" / "EVOLUTION.md").write_text(LEDGER, encoding="utf-8")
        (self.root / "beta").mkdir()
        (self.root / "beta" / "EVOLUTION.md").write_text(
            LEDGER.replace("some-revision", "other-revision"), encoding="utf-8"
        )
        self.addCleanup(self.tmp.cleanup)

    def candidate(self, skill="alpha", **overrides):
        base = {
            "skill": skill,
            "ledger": f"{skill}/EVOLUTION.md",
            "impact": 30,
            "urgency": 20,
            "readiness": 15,
            "unblocks": 10,
            "basis": f"{skill} has a held job with evidence behind it.",
        }
        base.update(overrides)
        return base

    def document(self, candidates=None, **overrides):
        base = {
            "scope": "the checkout",
            "mode": "full",
            "candidates": candidates or [self.candidate()],
            "selected": "alpha",
        }
        base.update(overrides)
        return base

    def run_record(self, document, root=None):
        argv = ["record", "--scoreboard", str(self.scoreboard), "--root", str(root or self.root)]
        payload = document if isinstance(document, str) else json.dumps(document)
        out, err = io.StringIO(), io.StringIO()

        class Stdin:
            buffer = io.BytesIO(payload.encode("utf-8"))

        real_stdin, kronos.sys.stdin = kronos.sys.stdin, Stdin()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = kronos.main(argv)
        finally:
            kronos.sys.stdin = real_stdin
        return code, out.getvalue(), err.getvalue()

    def run_show(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = kronos.main(["show", "--scoreboard", str(self.scoreboard)])
        return code, out.getvalue()

    def lines(self):
        return self.scoreboard.read_text(encoding="utf-8").splitlines()

    # -- the clean path -------------------------------------------------

    def test_a_valid_pass_appends_exactly_one_line(self):
        code, out, _ = self.run_record(self.document())
        self.assertEqual(code, 0)
        self.assertIn("pass 1 recorded", out)
        self.assertEqual(len(self.lines()), 1)

    def test_the_written_hash_is_the_digest_the_ledger_itself_records(self):
        self.run_record(self.document())
        entry = json.loads(self.lines()[0])
        self.assertEqual(
            entry["candidates"][0]["held_job"],
            canonical_digest(
                "open", "some-revision", "A frontier sentence.", "Do the thing that is held."
            ),
        )

    def test_the_scoreboard_directory_is_created_gitignored(self):
        self.run_record(self.document())
        self.assertEqual((self.scoreboard.parent / ".gitignore").read_text(encoding="utf-8"), "*\n")

    def test_pass_numbers_increase(self):
        self.run_record(self.document())
        code, out, _ = self.run_record(self.document())
        self.assertEqual(code, 0)
        self.assertIn("pass 2 recorded", out)
        self.assertEqual([json.loads(line)["pass"] for line in self.lines()], [1, 2])

    def test_the_axis_caps_sum_to_one_hundred(self):
        self.assertEqual(sum(cap for _, cap in kronos.AXES), 100)

    # -- refusals -------------------------------------------------------

    def assertRefused(self, document, code_name, root=None):
        code, _, err = self.run_record(document, root=root)
        self.assertEqual(code, 1)
        self.assertIn(code_name, err)
        self.assertFalse(self.scoreboard.exists(), "a refusal must append nothing")

    def test_stdin_that_is_not_json_is_refused(self):
        self.assertRefused("not json at all", "K001")

    def test_an_axis_over_its_cap_is_refused(self):
        self.assertRefused(self.document([self.candidate(unblocks=16)]), "K004")

    def test_a_negative_axis_is_refused(self):
        self.assertRefused(self.document([self.candidate(impact=-1)]), "K004")

    def test_a_stated_total_that_disagrees_with_the_axes_is_refused(self):
        self.assertRefused(self.document([self.candidate(total=105)]), "K005")

    def test_a_stated_total_that_agrees_is_accepted(self):
        code, _, err = self.run_record(self.document([self.candidate(total=75)]))
        self.assertEqual(code, 0, err)

    def test_an_unknown_field_is_refused_rather_than_stored(self):
        self.assertRefused(self.document([self.candidate(note="extra")]), "K003")

    def test_a_missing_field_is_refused(self):
        candidate = self.candidate()
        del candidate["basis"]
        self.assertRefused(self.document([candidate]), "K002")

    def test_a_selection_the_tie_break_does_not_pick_is_refused(self):
        candidates = [self.candidate("alpha"), self.candidate("beta", impact=40)]
        self.assertRefused(self.document(candidates, selected="alpha"), "K006")

    def test_the_tie_break_prefers_impact_then_readiness(self):
        candidates = [
            self.candidate("alpha", impact=20, urgency=25, readiness=15, unblocks=10),
            self.candidate("beta", impact=25, urgency=20, readiness=15, unblocks=10),
        ]
        code, _, err = self.run_record(self.document(candidates, selected="beta"))
        self.assertEqual(code, 0, err)

    def test_a_ledger_outside_the_root_is_refused(self):
        outside = Path(self.tmp.name).parent / "elsewhere.md"
        self.assertRefused(
            self.document([self.candidate(ledger=str(outside))]), "K007"
        )

    def test_a_ledger_that_is_a_directory_is_refused(self):
        self.assertRefused(self.document([self.candidate(ledger="alpha")]), "K007")

    def test_a_ledger_missing_a_frontier_field_is_refused(self):
        (self.root / "alpha" / "EVOLUTION.md").write_text("# nothing here\n", encoding="utf-8")
        self.assertRefused(self.document(), "K007")

    def test_more_candidates_than_the_cap_is_refused(self):
        many = [self.candidate(f"skill-{n}") for n in range(kronos.MAX_CANDIDATES + 1)]
        self.assertRefused(self.document(many, selected="skill-0"), "K009")

    def test_two_candidates_naming_one_skill_is_refused(self):
        self.assertRefused(self.document([self.candidate(), self.candidate()]), "K002")

    def test_an_unknown_mode_is_refused(self):
        self.assertRefused(self.document(mode="whatever"), "K002")

    def test_a_truncated_final_line_is_refused_rather_than_written_past(self):
        self.run_record(self.document())
        with self.scoreboard.open("a", encoding="utf-8") as handle:
            handle.write('{"pass": 2, "candi')
        code, _, err = self.run_record(self.document())
        self.assertEqual(code, 1)
        self.assertIn("K008", err)
        self.assertEqual(len(self.lines()), 2, "the partial line stays, nothing is appended")

    def test_a_symlinked_scoreboard_directory_is_refused(self):
        """Round 1 wrote through a symlinked .kronos into an unnamed directory.

        Both the scoreboard and its `*` gitignore landed there. Where the link
        pointed somewhere git watches, that is the dirty tree the whole design
        exists to avoid.
        """
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.scoreboard.parent.symlink_to(elsewhere)
        code, _, err = self.run_record(self.document())
        self.assertEqual(code, 1)
        self.assertIn("K010", err)
        self.assertEqual(list(elsewhere.iterdir()), [], "nothing may be written through the link")

    def test_a_symlinked_scoreboard_file_is_refused(self):
        """resolve() follows the link, so the first fix never saw it."""
        elsewhere = self.root / "elsewhere.jsonl"
        self.scoreboard.parent.mkdir(parents=True)
        self.scoreboard.symlink_to(elsewhere)
        code, _, err = self.run_record(self.document())
        self.assertEqual(code, 1)
        self.assertIn("K010", err)
        self.assertFalse(elsewhere.exists(), "nothing may be written through the link")

    def test_a_scoreboard_directory_that_is_a_file_is_refused(self):
        self.scoreboard.parent.write_text("not a directory", encoding="utf-8")
        code, _, err = self.run_record(self.document())
        self.assertEqual(code, 1)
        self.assertIn("K010", err)

    def test_a_run_field_that_is_not_a_string_is_refused(self):
        self.assertRefused(self.document(run={"url": "https://example.invalid"}), "K002")

    def test_a_run_field_that_is_a_string_survives_into_the_record(self):
        url = "https://github.com/wildcat-finance/skills/pull/1"
        code, _, err = self.run_record(self.document(run=url))
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(self.lines()[0])["run"], url)

    # -- reading it back ------------------------------------------------

    def test_show_marks_an_axis_that_moved_under_an_unchanged_held_job(self):
        self.run_record(self.document())
        self.run_record(self.document([self.candidate(impact=35)]))
        code, out = self.run_show()
        self.assertEqual(code, 0)
        self.assertIn("drift: impact 30 -> 35, held job unchanged", out)
        self.assertIn("2 pass(es), 1 with drift", out)

    def test_show_reports_no_drift_when_the_held_job_changed_too(self):
        self.run_record(self.document())
        (self.root / "alpha" / "EVOLUTION.md").write_text(
            LEDGER.replace("Do the thing that is held.", "Do a different held thing."),
            encoding="utf-8",
        )
        self.run_record(self.document([self.candidate(impact=35)]))
        _, out = self.run_show()
        self.assertNotIn("drift:", out)
        self.assertIn("2 pass(es), 0 with drift", out)

    def test_show_on_an_absent_scoreboard_says_so_and_exits_clean(self):
        code, out = self.run_show()
        self.assertEqual(code, 0)
        self.assertIn("no scoreboard at", out)

    def test_show_marks_the_selected_candidate(self):
        self.run_record(self.document([self.candidate("alpha"), self.candidate("beta", impact=40)],
                                      selected="beta"))
        _, out = self.run_show()
        selected = [line for line in out.splitlines() if line.lstrip().startswith("*")]
        self.assertEqual(len(selected), 1)
        self.assertIn("beta", selected[0])

    # -- the skill and the script agree ---------------------------------

    def test_every_field_the_script_accepts_is_named_in_the_skill(self):
        """Round 1 documented a refusal for `total` without documenting the field.

        A caller reading only SKILL.md could be refused over something it never
        told them they could send, and the two drift apart silently otherwise.
        """
        skill = (ROOT / "skills" / "kronos" / "SKILL.md").read_text(encoding="utf-8")
        section = skill.split("## Scoreboard", 1)[1].split("## Hard rules", 1)[0]
        for name in sorted(kronos.PASS_FIELDS | kronos.CANDIDATE_FIELDS):
            with self.subTest(field=name):
                self.assertIn(f"`{name}`", section)

    def test_the_pass_is_recorded_once_the_fiat_run_is_named(self):
        """The run link is half the record, and it does not exist at selection."""
        skill = (ROOT / "skills" / "kronos" / "SKILL.md").read_text(encoding="utf-8")
        loop = skill.split("## Loop", 1)[1].split("## Scoreboard", 1)[0]
        step_four = loop.split("4. ", 1)[1].split("5. ", 1)[0]
        step_six = loop.split("6. ", 1)[1].split("7. ", 1)[0]
        self.assertNotIn("record the pass", step_four)
        self.assertIn("record the pass", step_six)

    # -- against the real ledgers ---------------------------------------

    def test_the_hash_matches_a_real_governed_ledger_history_row(self):
        ledger = REPO / "plugins" / "hexaemeron" / "skills" / "kronos" / "EVOLUTION.md"
        computed = kronos.held_job_hash(ledger)
        self.assertIn(f"`{computed}`", ledger.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
