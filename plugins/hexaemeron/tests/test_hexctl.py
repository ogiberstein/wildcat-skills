"""End-to-end tests for hexctl, run through the CLI the way the skill uses it."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HEXCTL = os.path.join(HERE, "..", "skills", "fiat", "scripts", "hexctl.py")


class HexctlCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def run_ctl(self, *args, expect=0, verify=False, env=None):
        """Drive hexctl the way the skill does.

        These cases run in a bare temporary directory with no repository and no
        `gh`, so by default they receipt with `--unverified`, which is the
        escape the controller offers for exactly that situation. `verify=True`
        leaves it off, for the cases in TestVerification that build a real
        repository and put a stub `gh` on PATH to exercise the checks.
        """
        args = list(args)
        if (
            not verify
            and args
            and args[0] in ("done", "audit-round")
            and "--unverified" not in args
        ):
            args += ["--unverified", "unit test: no repository or gh here"]
        proc = subprocess.run(
            [sys.executable, HEXCTL, *args],
            cwd=self.dir,
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.returncode != expect:
            raise AssertionError(
                f"hexctl {' '.join(args)} -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        return proc

    def next_json(self):
        return json.loads(self.run_ctl("next").stdout)

    def write(self, name, content="stub\n"):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path) or self.dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return name

    def init(self, topic="test topic"):
        self.run_ctl("init", "--topic", topic)

    def to_steps(self, titles=("Scaffold", "Core")):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write("runbook.md")
        steps = self.write("steps.json", json.dumps(list(titles)))
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps, "--epic-issue", "https://x/epic")

    def to_audit(self):
        self.to_steps()
        self.run_ctl("done", "issue", "--issue-url", "https://x/1")
        self.run_ctl("done", "implement", "--branch", "issue-1-scaffold",
                     "--commit", "abc123")

    def finish_step(self, issue_no=1):
        self.run_ctl("done", "issue", "--issue-url", f"https://x/{issue_no}")
        self.run_ctl("done", "implement", "--branch", f"issue-{issue_no}",
                     "--commit", "abc123")
        self.run_ctl("audit-round", "--findings", "0",
                     "--log", self.write("audit/AUDIT.md"))
        self.run_ctl("done", "audit")
        self.run_ctl("done", "prose", "--files", "3",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        self.run_ctl("done", "push", "--pr-url", f"https://x/pr/{issue_no}",
                     "--checkboxes", "4/4", "--issue-state", "closed")


class TestLifecycle(HexctlCase):
    def test_init_creates_state_ledger_and_gitignore(self):
        self.init()
        root = os.path.join(self.dir, ".hexaemeron")
        self.assertTrue(os.path.exists(os.path.join(root, "state.json")))
        self.assertTrue(os.path.exists(os.path.join(root, "ledger.jsonl")))
        with open(os.path.join(root, ".gitignore")) as fh:
            self.assertEqual(fh.read().strip(), "*")

    def test_init_twice_fails(self):
        self.init()
        proc = self.run_ctl("init", "--topic", "again", expect=2)
        self.assertIn("already exists", proc.stderr)

    def test_next_initial_is_study(self):
        self.init("widget factory")
        out = self.next_json()
        self.assertEqual(out["do"], "study")
        self.assertEqual(out["topic"], "widget factory")

    def test_done_out_of_order_rejected(self):
        self.init()
        rb = self.write("runbook.md")
        steps = self.write("steps.json", '["a"]')
        proc = self.run_ctl("done", "runbook", "--epic-issue", "https://x/epic",
                            "--artifact", rb,
                            "--steps-file", steps, expect=2)
        self.assertIn("out of order", proc.stderr)

    def test_study_requires_existing_artifact(self):
        self.init()
        proc = self.run_ctl("done", "study", "--artifact", "missing.md",
                            expect=2)
        self.assertIn("not found", proc.stderr)

    def test_runbook_registers_steps_and_opens_first(self):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        rb = self.write("runbook.md")
        steps = self.write("steps.json",
                           json.dumps(["Scaffold", {"title": "Core"}]))
        self.run_ctl("done", "runbook", "--artifact", rb, "--steps-file", steps,
                     "--epic-issue", "https://x/epic")
        out = self.next_json()
        self.assertEqual(out["do"], "issue")
        self.assertEqual(out["step"], 1)
        self.assertEqual(out["title"], "Scaffold")


class TestStepGates(HexctlCase):
    def test_issue_requires_url(self):
        self.to_steps()
        proc = self.run_ctl("done", "issue", expect=2)
        self.assertIn("--issue-url", proc.stderr)

    def test_step_phase_order_enforced(self):
        self.to_steps()
        proc = self.run_ctl("done", "implement", "--branch", "b",
                            "--commit", "c", expect=2)
        self.assertIn("out of order", proc.stderr)

    def test_subissues_recorded(self):
        self.to_steps()
        self.run_ctl("done", "issue", "--issue-url", "https://x/1",
                     "--subissue-url", "https://x/2",
                     "--subissue-url", "https://x/3")
        state = json.loads(self.run_ctl("status", "--json").stdout)
        subs = state["steps"][0]["receipts"]["issue"]["subissues"]
        self.assertEqual(subs, ["https://x/2", "https://x/3"])


class TestAuditLoop(HexctlCase):
    def test_round_requires_security_suite_receipt(self):
        self.to_audit()
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn("security_suite", proc.stderr)
        out = self.next_json()
        self.assertEqual(out["do"], "resolve-security-suite")

    def test_rounds_advance_and_next_tracks_them(self):
        self.to_audit()
        self.run_ctl("record", "security_suite",
                     '["pashov-xray","pashov-solidity-auditor"]')
        self.assertEqual(self.next_json()["do"], "audit-round")
        self.run_ctl("audit-round", "--findings", "3", "--log", self.write("audit/AUDIT.md"), "--fixes-commit", "cafe3")
        out = self.next_json()
        self.assertEqual(out["do"], "audit-round")
        self.assertEqual(out["round"], 2)
        self.assertEqual(out["prior_findings"], 3)

    def test_close_blocked_while_findings_open(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        self.run_ctl("audit-round", "--findings", "2", "--log", self.write("audit/AUDIT.md"), "--fixes-commit", "cafe2")
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("open", proc.stderr)

    def test_clean_close_requires_fixes_evidence_when_findings_existed(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("audit-round", "--findings", "2",
                     "--log", self.write("audit/AUDIT.md"))
        self.run_ctl("audit-round", "--findings", "0")
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("fixes", proc.stderr)
        self.run_ctl("done", "audit", "--fixes-ref", "issue-1--audit@deadbeef")
        self.assertEqual(self.next_json()["do"], "prose")

    def test_fixes_commit_on_round_satisfies_evidence(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("audit-round", "--findings", "1",
                     "--log", self.write("audit/AUDIT.md"),
                     "--fixes-commit", "beef01")
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_no_further_leads_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("audit-round", "--findings", "1", "--log", self.write("audit/AUDIT.md"), "--fixes-commit", "b1")
        proc = self.run_ctl("done", "audit", "--no-further-leads", expect=2)
        self.assertIn("--reason", proc.stderr)
        self.run_ctl("done", "audit", "--no-further-leads",
                     "--reason", "remaining lead is a gas nit, out of scope")

    def test_max_rounds_forces_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("config", "set", "audit.max_rounds", "2")
        self.run_ctl("audit-round", "--findings", "2", "--log", self.write("audit/AUDIT.md"), "--fixes-commit", "b1")
        self.run_ctl("audit-round", "--findings", "1", "--log", self.write("audit/AUDIT.md"), "--fixes-commit", "b2")
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn("max audit rounds", proc.stderr)
        out = self.next_json()
        self.assertEqual(out["do"], "audit-verdict")
        self.assertEqual(out["open_findings"], 1)


class TestProseAndPush(HexctlCase):
    def to_prose(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_prose_requires_both_configured_skills(self):
        self.to_prose()
        proc = self.run_ctl("done", "prose", "--files", "3",
                            "--skills", "hexaemeron:imprimatur", expect=2)
        self.assertIn("hexaemeron:vulgate", proc.stderr)
        self.run_ctl("done", "prose", "--files", "3",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")

    def test_push_checkbox_and_issue_state_rules(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        base = ["done", "push", "--pr-url", "https://x/pr/1"]
        self.run_ctl(*base, "--checkboxes", "seven", "--issue-state", "open",
                     expect=2)
        self.run_ctl(*base, "--checkboxes", "5/4", "--issue-state", "open",
                     expect=2)
        proc = self.run_ctl(*base, "--checkboxes", "4/4",
                            "--issue-state", "open", expect=2)
        self.assertIn("must be closed", proc.stderr)
        proc = self.run_ctl(*base, "--checkboxes", "3/4",
                            "--issue-state", "closed", expect=2)
        self.assertIn("stay", proc.stderr)
        self.run_ctl(*base, "--checkboxes", "3/4", "--issue-state", "open")

    def test_push_advances_steps_then_run_completes(self):
        self.to_steps(("One", "Two"))
        self.run_ctl("record", "security_suite", '"suite"')
        self.finish_step(1)
        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("issue", 2))
        self.finish_step(2)
        self.assertEqual(self.next_json()["do"], "done")


class TestControls(HexctlCase):
    def test_halt_blocks_progress_and_resume_restores(self):
        self.to_steps()
        self.run_ctl("halt", "--reason", "waiting on Oliver")
        self.assertEqual(self.next_json()["do"], "halted")
        proc = self.run_ctl("done", "issue", "--issue-url", "https://x/1",
                            expect=2)
        self.assertIn("halted", proc.stderr)
        self.run_ctl("resume", "--note", "cleared")
        self.assertEqual(self.next_json()["do"], "issue")

    def test_verify_ok_and_tamper_detected(self):
        self.to_steps()
        self.run_ctl("verify")
        ledger = os.path.join(self.dir, ".hexaemeron", "ledger.jsonl")
        with open(ledger) as fh:
            lines = fh.read().splitlines()
        entry = json.loads(lines[0])
        entry["data"]["topic"] = "someone edited history"
        lines[0] = json.dumps(entry, sort_keys=True)
        with open(ledger, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        proc = self.run_ctl("verify", expect=1)
        self.assertIn("chain broken", proc.stderr)

    def test_record_and_status_json(self):
        self.init()
        self.run_ctl("record", "epic_issue", "https://x/epic")
        state = json.loads(self.run_ctl("status", "--json").stdout)
        self.assertEqual(state["receipts"]["epic_issue"], "https://x/epic")
        self.assertEqual(state["phase"], "study")

    def test_config_get_set_roundtrip(self):
        self.init()
        self.run_ctl("config", "set", "audit.max_rounds", "3")
        out = self.run_ctl("config", "get", "audit.max_rounds").stdout.strip()
        self.assertEqual(out, "3")
        proc = self.run_ctl("config", "get", "audit.nope", expect=2)
        self.assertIn("not found", proc.stderr)



class TestFuzzRegressions(HexctlCase):
    """Pins for the day-5 fuzz findings (F-01..F-09)."""

    def state_file(self):
        return os.path.join(self.dir, ".hexaemeron", "state.json")

    def ledger_file(self):
        return os.path.join(self.dir, ".hexaemeron", "ledger.jsonl")

    def to_audit_with_suite(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '["x","y"]')

    def test_state_edit_detected_by_verify(self):
        self.to_audit_with_suite()
        self.run_ctl("audit-round", "--findings", "2", "--log", self.write("a.md"),
                     "--fixes-commit", "fff")
        with open(self.state_file()) as fh:
            st = json.load(fh)
        st["steps"][0]["audit"]["rounds"][0]["findings"] = 0
        with open(self.state_file(), "w") as fh:
            json.dump(st, fh)
        proc = self.run_ctl("verify", expect=1)
        self.assertIn("edited outside hexctl", proc.stderr)

    def test_corrupt_state_dies_cleanly(self):
        self.to_audit_with_suite()
        with open(self.state_file(), "w") as fh:
            fh.write("{broken")
        for argv in (["status"], ["next"], ["record", "k", "v"]):
            proc = self.run_ctl(*argv, expect=1)
            self.assertNotIn("Traceback", proc.stderr)
            self.assertIn("unreadable", proc.stderr)

    def test_corrupt_ledger_dies_cleanly(self):
        self.to_audit_with_suite()
        with open(self.ledger_file(), "a") as fh:
            fh.write("garbage\n")
        proc = self.run_ctl("verify", expect=1)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("chain broken", proc.stderr)
        proc = self.run_ctl("record", "k", "v", expect=1)
        self.assertNotIn("Traceback", proc.stderr)

    def test_bad_steps_json_dies_cleanly(self):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write("runbook.md")
        bad = self.write("bad.json", "{not json")
        proc = self.run_ctl("done", "runbook", "--artifact", runbook,
                            "--steps-file", bad, expect=2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("not valid JSON", proc.stderr)

    def test_blank_step_title_refused(self):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write("runbook.md")
        sf = self.write("s.json", '["ok", "  "]')
        proc = self.run_ctl("done", "runbook", "--artifact", runbook,
                            "--steps-file", sf, expect=2)
        self.assertIn("non-empty", proc.stderr)

    def test_max_rounds_validated(self):
        self.to_audit_with_suite()
        self.run_ctl("config", "set", "audit.max_rounds", '"eight"')
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("must be an integer", proc.stderr)
        self.run_ctl("config", "set", "audit.max_rounds", "0")
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn(">= 1", proc.stderr)
        self.run_ctl("config", "set", "audit.max_rounds", "8")
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("verify")

    def test_prose_nonstring_config_ids(self):
        self.to_audit_with_suite()
        self.run_ctl("config", "set", "skills.prose_lint", "123")
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        proc = self.run_ctl("done", "prose", "--files", "1",
                            "--skills", "hexaemeron:vulgate", expect=2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("123", proc.stderr)
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "123,hexaemeron:vulgate")

    def test_record_reserved_keys_refused(self):
        self.to_audit_with_suite()
        proc = self.run_ctl("record", "study", '"forged"', expect=2)
        self.assertIn("phase receipt", proc.stderr)

    def test_status_strips_control_chars(self):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write("runbook.md")
        sf = self.write("s.json", json.dumps(["\u001b[31mEVIL\u001b[0m step"]))
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", sf, "--epic-issue", "https://x/epic")
        proc = self.run_ctl("status")
        self.assertNotIn("\x1b", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestVerification(HexctlCase):
    """The claims a receipt makes, checked against the world it makes them about.

    Every case here builds a real repository and puts a stub `gh` on PATH, so
    the controller is answering from git and from GitHub's shape rather than
    from what it was told. The bug these exist for is real: a push was once
    receipted as 21/21 against an issue carrying 20 boxes, and nothing noticed.
    """

    def setUp(self):
        super().setUp()
        self.bin = os.path.join(self.dir, "stub-bin")
        os.makedirs(self.bin, exist_ok=True)
        self.env = os.environ.copy()
        self.env["PATH"] = self.bin + os.pathsep + self.env["PATH"]

    # -- fixtures ---------------------------------------------------------

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.dir, capture_output=True, text=True
        )

    def repo(self):
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "Test")
        self.write("seed.txt")
        self.git("add", "-A")
        self.git("commit", "-qm", "seed")
        return self.git("rev-parse", "HEAD").stdout.strip()

    def branch(self, name):
        self.git("checkout", "-q", "-b", name)
        self.write(name.replace("/", "_") + ".txt")
        self.git("add", "-A")
        self.git("commit", "-qm", name)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def stub_gh(self, issue=None, pr=None):
        """A `gh` that answers with whatever the case wants it to say."""
        issue = issue or {"state": "OPEN", "body": "## Description\n"}
        pr = pr or {"state": "OPEN", "headRefName": "b", "isDraft": False}
        with open(os.path.join(self.dir, "issue.json"), "w") as fh:
            json.dump(issue, fh)
        with open(os.path.join(self.dir, "pr.json"), "w") as fh:
            json.dump(pr, fh)
        path = os.path.join(self.bin, "gh")
        with open(path, "w") as fh:
            fh.write(
                "#!/bin/sh\ncase \"$1\" in\n"
                "  issue) cat %s ;;\n"
                "  pr) cat %s ;;\n"
                "  *) exit 1 ;;\nesac\n"
                % (
                    json.dumps(os.path.join(self.dir, "issue.json")),
                    json.dumps(os.path.join(self.dir, "pr.json")),
                )
            )
        os.chmod(path, 0o755)

    def headers_body(self, checked=0, unchecked=0):
        body = "".join("## %s\n" % h for h in (
            "Description", "TODO", "Acceptance Criteria", "User Value / Need"
        ))
        body += "".join("- [x] done\n" for _ in range(checked))
        body += "".join("- [ ] todo\n" for _ in range(unchecked))
        return body

    def to_implement(self):
        """A run at step 1's implement phase, in a real repository."""
        self.repo()
        self.to_steps()
        self.stub_gh(issue={"state": "OPEN", "body": self.headers_body()})
        self.run_ctl("done", "issue", "--issue-url", "https://x/1",
                     verify=True, env=self.env)

    # -- git: the commit and the branch a receipt names --------------------

    def test_a_commit_that_does_not_exist_is_refused(self):
        self.to_implement()
        proc = self.run_ctl("done", "implement", "--branch", "main",
                            "--commit", "deadbeefdeadbeef",
                            expect=2, verify=True, env=self.env)
        self.assertIn("not a commit", proc.stderr)

    def test_a_branch_that_does_not_exist_is_refused(self):
        self.to_implement()
        head = self.git("rev-parse", "HEAD").stdout.strip()
        proc = self.run_ctl("done", "implement", "--branch", "no-such-branch",
                            "--commit", head,
                            expect=2, verify=True, env=self.env)
        self.assertIn("does not exist", proc.stderr)

    def test_a_commit_not_on_the_named_branch_is_refused(self):
        self.to_implement()
        main_head = self.git("rev-parse", "main").stdout.strip()
        side = self.branch("issue-1-scaffold")
        self.git("checkout", "-q", "main")
        proc = self.run_ctl("done", "implement", "--branch", "main",
                            "--commit", side,
                            expect=2, verify=True, env=self.env)
        self.assertIn("is not on branch", proc.stderr)
        self.assertTrue(main_head)

    def test_a_verified_implement_records_that_it_was_checked(self):
        self.to_implement()
        head = self.branch("issue-1-scaffold")
        self.run_ctl("done", "implement", "--branch", "issue-1-scaffold",
                     "--commit", head, verify=True, env=self.env)
        state = json.load(open(os.path.join(self.dir, ".hexaemeron", "state.json")))
        self.assertTrue(state["steps"][0]["receipts"]["implement"]["verified"])

    def test_unverified_is_allowed_and_its_reason_is_recorded(self):
        self.to_implement()
        self.run_ctl("done", "implement", "--branch", "whatever",
                     "--commit", "nonsense", "--unverified", "no repo today",
                     verify=True, env=self.env)
        state = json.load(open(os.path.join(self.dir, ".hexaemeron", "state.json")))
        receipt = state["steps"][0]["receipts"]["implement"]
        self.assertFalse(receipt["verified"])
        self.assertEqual(receipt["unverified_reason"], "no repo today")

    # -- gh: the issue and the pull request --------------------------------

    def test_an_issue_missing_a_configured_header_is_refused(self):
        self.repo()
        self.to_steps()
        self.stub_gh(issue={"state": "OPEN", "body": "## Description\n"})
        proc = self.run_ctl("done", "issue", "--issue-url", "https://x/1",
                            expect=2, verify=True, env=self.env)
        self.assertIn("Acceptance Criteria", proc.stderr)

    def test_an_issue_that_is_already_closed_is_refused(self):
        self.repo()
        self.to_steps()
        self.stub_gh(issue={"state": "CLOSED", "body": self.headers_body()})
        proc = self.run_ctl("done", "issue", "--issue-url", "https://x/1",
                            expect=2, verify=True, env=self.env)
        self.assertIn("stays open", proc.stderr)

    def to_push(self, checked, unchecked, pr=None):
        self.to_implement()
        head = self.branch("issue-1-scaffold")
        self.run_ctl("done", "implement", "--branch", "issue-1-scaffold",
                     "--commit", head, verify=True, env=self.env)
        self.run_ctl("record", "security_suite", '"waived: python only"')
        self.run_ctl("audit-round", "--findings", "0", verify=True, env=self.env)
        self.run_ctl("done", "audit", verify=True, env=self.env)
        self.run_ctl("done", "prose", "--files", "1", "--skills",
                     "hexaemeron:imprimatur,hexaemeron:vulgate",
                     verify=True, env=self.env)
        self.stub_gh(
            issue={"state": "CLOSED" if not unchecked else "OPEN",
                   "body": self.headers_body(checked, unchecked)},
            pr=pr or {"state": "OPEN", "headRefName": "issue-1-scaffold",
                      "isDraft": False},
        )

    def test_a_checkbox_count_the_issue_does_not_carry_is_refused(self):
        """The bug this whole class exists for."""
        self.to_push(checked=20, unchecked=0)
        proc = self.run_ctl("done", "push", "--pr-url", "https://x/pr/1",
                            "--checkboxes", "21/21", "--issue-state", "closed",
                            expect=2, verify=True, env=self.env)
        self.assertIn("carries 20/20", proc.stderr)

    def test_a_truthful_checkbox_count_is_accepted(self):
        self.to_push(checked=20, unchecked=0)
        self.run_ctl("done", "push", "--pr-url", "https://x/pr/1",
                     "--checkboxes", "20/20", "--issue-state", "closed",
                     verify=True, env=self.env)

    def test_an_issue_state_that_disagrees_with_the_issue_is_refused(self):
        """The counts agree; the state does not. Only the state is at fault."""
        self.to_push(checked=1, unchecked=1)
        self.stub_gh(
            issue={"state": "CLOSED", "body": self.headers_body(1, 1)},
            pr={"state": "OPEN", "headRefName": "issue-1-scaffold",
                "isDraft": False},
        )
        proc = self.run_ctl("done", "push", "--pr-url", "https://x/pr/1",
                            "--checkboxes", "1/2", "--issue-state", "open",
                            expect=2, verify=True, env=self.env)
        self.assertIn("--issue-state says open", proc.stderr)
        self.assertNotIn("carries", proc.stderr)

    def test_a_pull_request_from_another_branch_is_refused(self):
        self.to_push(checked=20, unchecked=0,
                     pr={"state": "OPEN", "headRefName": "someone-elses",
                         "isDraft": False})
        proc = self.run_ctl("done", "push", "--pr-url", "https://x/pr/1",
                            "--checkboxes", "20/20", "--issue-state", "closed",
                            expect=2, verify=True, env=self.env)
        self.assertIn("this step built", proc.stderr)

    def test_a_draft_pull_request_against_a_non_draft_config_is_refused(self):
        self.to_push(checked=20, unchecked=0,
                     pr={"state": "OPEN", "headRefName": "issue-1-scaffold",
                         "isDraft": True})
        proc = self.run_ctl("done", "push", "--pr-url", "https://x/pr/1",
                            "--checkboxes", "20/20", "--issue-state", "closed",
                            expect=2, verify=True, env=self.env)
        self.assertIn("draft_pr", proc.stderr)

    # -- the waiver, and the loop boundary ---------------------------------

    def test_the_suite_cannot_be_waived_over_a_tree_carrying_solidity(self):
        self.repo()
        self.to_steps()
        self.write("contracts/Thing.sol", "// SPDX-License-Identifier: MIT\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "solidity")
        proc = self.run_ctl("record", "security_suite", '"waived: felt like it"',
                            expect=2, env=self.env)
        self.assertIn("carries Solidity", proc.stderr)

    def test_the_suite_may_still_be_waived_without_solidity(self):
        self.repo()
        self.to_steps()
        self.run_ctl("record", "security_suite", '"waived: python only"',
                     env=self.env)

    def test_next_says_whether_the_loop_should_continue(self):
        self.to_steps()
        out = self.next_json()
        self.assertFalse(out["stop"])
        self.assertTrue(out["continue_after_receipt"])

    def test_next_says_stop_when_the_run_is_halted(self):
        self.to_steps()
        self.run_ctl("halt", "--reason", "asked to")
        out = self.next_json()
        self.assertTrue(out["stop"])
        self.assertIn("halted", out["stop_reason"])
