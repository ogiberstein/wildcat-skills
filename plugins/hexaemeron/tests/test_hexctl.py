"""End-to-end tests for hexctl, run through the CLI the way the skill uses it."""

import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr
from io import StringIO
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
HEXCTL = os.path.join(HERE, "..", "skills", "fiat", "scripts", "hexctl.py")
PROTASIS = os.path.join(HERE, "..", "skills", "protasis", "scripts", "protasis.py")

SUITE = '["hexaemeron:x-ray", "hexaemeron:solidity-auditor"]'
"""A security_suite receipt shaped like the one preflight records.

These tests used the string "suite", which is neither a waiver nor a list of ids. The
round classifier reads it as a receipt it cannot make sense of, and demands the lint
results, which is the right answer for a receipt like that and the wrong fixture for a
test about a Solidity round.
"""

LINTS_CLEAN = ("--phylax-exit", "0", "--ephoros-exit", "0", "--hypomnema-exit", "0")
"""What a non-Solidity round records when all three lints came back clean."""


def hexctl_module():
    """The controller imported as a module.

    Every other test here drives the CLI, which is the surface the skill uses. The
    round classifier has no CLI of its own -- it decides what `audit-round` demands --
    so it is exercised directly rather than through a command that would only report
    it indirectly.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("hexctl_under_test", HEXCTL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def protasis_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("protasis_under_test", PROTASIS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HexctlCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.processes = []
        self.env = os.environ.copy()
        self.fake_refs = {}
        self.fake_prs = {}
        self.install_fake_delivery_tools()

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        self.tmp.cleanup()

    def run_ctl(self, *args, expect=0):
        pending_refs = dict(self.fake_refs)
        pending_prs = json.loads(json.dumps(self.fake_prs))
        state_path = os.path.join(self.dir, ".hexaemeron", "state.json")
        state = None
        if os.path.exists(state_path):
            try:
                with open(state_path, encoding="utf-8") as handle:
                    state = json.load(handle)
            except (OSError, ValueError):
                state = None
        if args[:2] == ("done", "implement") and expect == 0:
            branch = args[args.index("--branch") + 1]
            head = args[args.index("--commit") + 1]
            pending_refs[branch] = self.fake_sha(head)
        if args[:2] == ("done", "push") and expect == 0 and state is not None:
            step = state["steps"][state["current_step"] - 1]
            branch = step["receipts"]["implement"]["branch"]
            head = args[args.index("--head-commit") + 1]
            base = args[args.index("--pr-base") + 1] if "--pr-base" in args else state["base"]
            url = args[args.index("--pr-url") + 1]
            pending_refs[branch] = self.fake_sha(head)
            merge = args[args.index("--merge-commit") + 1] if "--merge-commit" in args else None
            pending_prs[url] = self.fake_pr(
                url, branch, base, self.fake_sha(head), merge
            )
        if args[:2] == ("done", "merge-step") and expect == 0 and state is not None:
            number = int(args[args.index("--step") + 1])
            url = state["steps"][number - 1]["receipts"]["push"]["pr_url"]
            merge = args[args.index("--merge-commit") + 1]
            pending_prs[url]["state"] = "MERGED"
            pending_prs[url]["mergeCommit"] = {"oid": merge}
            pending_refs[state["run_branch"]] = merge
            if number < len(state["steps"]):
                next_push = state["steps"][number]["receipts"].get("push", {})
                next_url = next_push.get("pr_url")
                if next_url in pending_prs:
                    pending_prs[next_url]["baseRefName"] = state["run_branch"]
        if args[:2] == ("done", "integrate") and expect == 0 and state is not None:
            url = args[args.index("--pr-url") + 1]
            merge = args[args.index("--merge-commit") + 1]
            head = pending_refs.get(state["run_branch"], self.fake_sha(state["run_branch"]))
            pending_prs[url] = self.fake_pr(
                url, state["run_branch"], state["base"], head, merge
            )
        env = dict(self.env)
        env["FAKE_GIT_REFS"] = json.dumps(pending_refs)
        env["FAKE_GH_PRS"] = json.dumps(pending_prs)
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
        if proc.returncode == 0:
            self.fake_refs = pending_refs
            self.fake_prs = pending_prs
        return proc

    @staticmethod
    def fake_sha(ref):
        return ref if re.fullmatch(r"[0-9a-f]{40}", ref) else hashlib.sha1(ref.encode()).hexdigest()

    @staticmethod
    def fake_pr(url, head, base, head_sha, merge_sha=None):
        return {
            "url": url,
            "state": "MERGED" if merge_sha else "OPEN",
            "headRefName": head,
            "headRefOid": head_sha,
            "baseRefName": base,
            "mergeCommit": {"oid": merge_sha} if merge_sha else None,
        }

    def install_fake_delivery_tools(self):
        fake_bin = os.path.join(self.dir, "delivery-tools")
        os.makedirs(fake_bin)
        real_git = shutil.which("git")
        git_script = os.path.join(fake_bin, "git")
        with open(git_script, "w", encoding="utf-8") as handle:
            handle.write(f"""#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
import time

args = sys.argv[1:]
mode = os.environ.get("FAKE_GIT_MODE", "valid")
if args and args[0] == "rev-parse":
    if mode == "missing-commit":
        raise SystemExit(2)
    ref = args[-1].removesuffix("^{{commit}}")
    refs = json.loads(os.environ.get("FAKE_GIT_REFS", "{{}}"))
    print(refs.get(ref, ref if re.fullmatch(r"[0-9a-f]{{40}}", ref) else hashlib.sha1(ref.encode()).hexdigest()))
elif args[:3] == ["remote", "get-url", "origin"]:
    print(os.environ.get("FAKE_GIT_ORIGIN", "https://github.com/wildcat-finance/example.git"))
elif args and args[0] == "merge-base":
    raise SystemExit(0)
elif args and args[0] == "rev-list":
    pair = next(value for value in args if ".." in value)
    base, head = pair.split("..", 1)
    if mode == "malformed-range":
        print("not-a-sha")
    elif mode == "intermediate":
        print(hashlib.sha1(b"middle").hexdigest())
        print(head)
    else:
        print(base if mode == "range-confusion" else head)
elif args and args[0] == "verify-commit":
    if os.environ.get("FAKE_GIT_LOG"):
        with open(os.environ["FAKE_GIT_LOG"], "a", encoding="utf-8") as log:
            log.write(args[-1] + "\\n")
    if mode == "timeout":
        time.sleep(2)
    if mode == "overflow":
        sys.stdout.write("signature" * 300000)
    if mode in ("nonzero", "unsigned"):
        sys.stderr.write("ghp_FAKE_SECRET raw signature material")
        raise SystemExit(7)
    print("FAKE SIGNATURE MATERIAL")
elif args and args[0] == "show":
    if mode == "missing-trailer":
        print("subject\\n\\nWildcat-Origin: shoggoth")
    elif mode == "duplicate-trailer":
        print("subject\\n\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nWildcat-Origin: shoggoth")
    else:
        print("subject\\n\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nWildcat-Origin: shoggoth")
else:
    os.execv({real_git!r}, [{real_git!r}, *args])
""")
        os.chmod(git_script, 0o755)

        gh_script = os.path.join(fake_bin, "gh")
        with open(gh_script, "w", encoding="utf-8") as handle:
            handle.write("""#!/usr/bin/env python3
import json
import os
import sys
import time

args = sys.argv[1:]
mode = os.environ.get("FAKE_GH_MODE", "valid")
if os.environ.get("FAKE_GH_LOG"):
    with open(os.environ["FAKE_GH_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\\n")
if mode == "timeout":
    time.sleep(2)
if mode == "overflow":
    sys.stdout.write("x" * 2200000)
    raise SystemExit(0)
if mode == "nonzero":
    sys.stderr.write("ghp_FAKE_SECRET rate limit response")
    raise SystemExit(9)
if mode == "invalid-json":
    print("not json")
    raise SystemExit(0)
if args[:2] == ["repo", "view"]:
    repository = "elsewhere/example" if mode == "repo-mismatch" else "wildcat-finance/example"
    print(json.dumps({"nameWithOwner": repository}))
    raise SystemExit(0)
if args[:2] == ["pr", "view"]:
    url = args[2]
    payload = json.loads(os.environ.get("FAKE_GH_PRS", "{}")).get(url)
    if payload is None:
        raise SystemExit(4)
    if mode == "pr-mismatch":
        payload["baseRefName"] = "wrong-base"
    print(json.dumps(payload))
    raise SystemExit(0)
sha = args[-1].rsplit("/", 1)[-1]
payload = {
    "sha": None if mode == "missing-sha" else sha,
    "commit": {"verification": {
        "verified": mode != "verified-false",
        "reason": os.environ.get("FAKE_GH_REASON", "expired_key") if mode == "invalid-reason" else "valid",
        "signature": "RAW FAKE SIGNATURE",
    }},
}
print(json.dumps(payload))
""")
        os.chmod(gh_script, 0o755)
        self.env["PATH"] = fake_bin + os.pathsep + self.env.get("PATH", "")

    def next_json(self):
        return json.loads(self.run_ctl("next").stdout)

    def write(self, name, content="stub\n"):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path) or self.dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return name

    def write_run_pr(self, carried="- nothing outstanding\n"):
        """The run-level pull request body the integrate receipt reads."""
        body = "Run body.\n"
        if carried is not None:
            body += "\n## Carried forward\n\n" + carried
        return self.write(os.path.join(".hexaemeron", "run-pr.md"), body)

    def init(self, topic="test topic"):
        self.run_ctl("init", "--topic", topic)

    def state(self):
        return json.loads(self.run_ctl("status", "--json").stdout)

    def run_branch(self):
        return self.state()["run_branch"]

    def step_branch(self, n, state=None):
        state = state or self.state()
        title = state["steps"][n - 1]["title"]
        tail = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:32].strip("-")
        return f"{state['run_branch']}-step-{n}-{tail or 'untitled'}"

    def step_base(self, n, state=None):
        state = state or self.state()
        if n == 1:
            return state["run_branch"]
        return self.step_branch(n - 1, state)

    def strip_run_branch(self):
        """Make the state look like a run started before stacked branches."""
        path = os.path.join(self.dir, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state.pop("run_branch", None)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)

    def merge_stack(self):
        for step in self.state()["steps"]:
            self.run_ctl("done", "merge-step", "--step", str(step["n"]),
                         "--merge-commit", format(step["n"], "x") * 40)

    def integrate_run(self, closed_issue_url=None):
        self.merge_stack()
        self.write_run_pr()
        args = ["done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                "--merge-commit", "f" * 40]
        if closed_issue_url:
            args += ["--closed-issue-url", closed_issue_url]
        self.run_ctl(*args)

    def spawn_lock_holder(self, ready, release, command="cmd_record"):
        program = """
import importlib.util
from pathlib import Path
import sys
import time

spec = importlib.util.spec_from_file_location("hexctl_under_test", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module.held_lock(sys.argv[2], sys.argv[3]):
    Path(sys.argv[4]).write_text("ready\\n", encoding="utf-8")
    while not Path(sys.argv[5]).exists():
        time.sleep(0.01)
"""
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                program,
                HEXCTL,
                self.dir,
                command,
                ready,
                release,
            ],
            cwd=self.dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.processes.append(process)
        return process

    def wait_for_file(self, path, process, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if os.path.exists(path):
                return
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.fail(
                    f"lock holder exited {process.returncode} before ready\n"
                    f"stdout: {stdout}\nstderr: {stderr}"
                )
            time.sleep(0.01)
        self.fail("lock holder did not become ready")

    def start_lock_holder(self, name="holder", command="cmd_record"):
        ready = os.path.join(self.dir, f"{name}.ready")
        release = os.path.join(self.dir, f"{name}.release")
        process = self.spawn_lock_holder(ready, release, command)
        self.wait_for_file(ready, process)
        return process, ready, release

    def release_lock_holder(self, process, release):
        with open(release, "w", encoding="utf-8") as handle:
            handle.write("release\n")
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, (stdout, stderr))

    def to_steps(self, titles=("Scaffold", "Core")):
        self.init()
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\n"
            "packet-state-drift | packet | compare state hash\n"
            "```\n",
        )
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n" + "\n".join(
                f"## Step {number}: {title}\n\n**Goal.** Ship {title}.\n"
                for number, title in enumerate(titles, 1)
            ),
        )
        steps = self.write("steps.json", json.dumps(list(titles)))
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps)
        self.git("init", "-b", "main")
        self.git("config", "user.email", "tests@example.com")
        self.git("config", "user.name", "Hexctl Tests")
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "fixture")
        state = self.state()
        self.git("branch", state["run_branch"])
        for step in state["steps"]:
            self.git("branch", self.step_branch(step["n"], state))

    def git(self, *args, expect=0):
        proc = subprocess.run(
            ["git", *args], cwd=self.dir, capture_output=True, text=True
        )
        if proc.returncode != expect:
            raise AssertionError(
                f"git {' '.join(args)} -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        return proc

    def to_audit(self):
        self.to_steps()
        self.run_ctl("done", "implement", "--branch", self.step_branch(1),
                     "--commit", "abc123")

    def finish_step(self, step_no=1):
        self.run_ctl("done", "implement", "--branch", self.step_branch(step_no),
                     "--commit", f"abc{step_no}")
        self.run_ctl("audit-round", "--findings", "0", "--log", "audit/AUDIT.md",
                     *LINTS_CLEAN)
        self.run_ctl("done", "audit")
        self.run_ctl("done", "prose", "--files", "3",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        self.run_ctl(
            "done", "push",
            "--pr-url", f"https://github.com/wildcat-finance/example/pull/{step_no}",
            "--head-commit", f"head{step_no}",
            "--pr-base", self.step_base(step_no),
        )


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
        proc = self.run_ctl("done", "runbook", "--artifact", rb,
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
        self.run_ctl("done", "study", "--artifact", study)
        rb = self.write(
            "runbook.md",
            "## Step 1: Scaffold\n\n**Goal.** Scaffold.\n\n"
            "## Step 2: Core\n\n**Goal.** Core.\n",
        )
        steps = self.write("steps.json",
                           json.dumps(["Scaffold", {"title": "Core"}]))
        self.run_ctl("done", "runbook", "--artifact", rb, "--steps-file", steps)
        out = self.next_json()
        self.assertEqual(out["do"], "implement")
        self.assertEqual(out["step"], 1)
        self.assertEqual(out["title"], "Scaffold")


class TestDelegationPackets(HexctlCase):
    def assert_packet(self, directive, agent, fields):
        self.assertEqual(directive["agent"], agent)
        self.assertEqual(set(directive["brief"]), set(fields))
        self.assertRegex(directive["state_sha256"], r"^[0-9a-f]{64}$")

    def test_surveyor_packet_is_total_and_reproducible(self):
        self.init("packet work")
        first = self.run_ctl("next").stdout
        second = self.run_ctl("next").stdout
        self.assertEqual(first, second)
        out = json.loads(first)
        self.assert_packet(
            out,
            "surveyor",
            ("topic", "target_dir", "base_ref", "output_path"),
        )
        self.assertEqual(out["brief"]["topic"], "packet work")
        self.assertEqual(out["brief"]["target_dir"], os.path.realpath(self.dir))
        self.assertEqual(out["brief"]["base_ref"], "main")
        self.assertEqual(
            out["brief"]["output_path"],
            os.path.realpath(os.path.join(self.dir, ".hexaemeron", "study.md")),
        )
        self.assertEqual(out["state_sha256"], hashlib.sha256(
            json.dumps(self.state(), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest())

    def test_all_four_role_briefs_and_inline_nulls(self):
        self.init()
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\n"
            "one | boundary | check\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        self.assertEqual(self.next_json()["agent"], None)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Core\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Core"]')
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps)
        self.git("init", "-b", "main")
        self.git("config", "user.email", "tests@example.com")
        self.git("config", "user.name", "Hexctl Tests")
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "base")
        state = self.state()
        self.git("branch", state["run_branch"])
        self.git("branch", self.step_branch(1, state))

        mason = self.next_json()
        self.assert_packet(mason, "mason", ("runbook_step", "branch", "branch_from"))
        source = mason["brief"]["runbook_step"]
        self.assertEqual(set(source), {"markdown", "path", "sha256", "number", "title"})
        self.assertEqual(source["number"], 1)
        self.assertEqual(source["title"], "Core")
        self.assertTrue(source["markdown"].startswith("## Step 1: Core\n"))

        self.run_ctl("done", "implement", "--branch", self.step_branch(1),
                     "--commit", "abc")
        inline = self.next_json()
        self.assertEqual((inline["do"], inline["agent"], inline["brief"]),
                         ("resolve-security-suite", None, {}))
        self.run_ctl("record", "security_suite", SUITE)
        warden = self.next_json()
        self.assert_packet(
            warden,
            "warden",
            ("step_branch", "stacked_branch", "security_suite", "plugin_root",
             "audit_log_path", "round", "risk_register"),
        )
        risk = warden["brief"]["risk_register"]
        self.assertEqual(set(risk), {"markdown", "path", "sha256"})
        self.assertEqual(risk["markdown"],
                         "```risk-register\none | boundary | check\n```\n")

        self.run_ctl("audit-round", "--findings", "0")
        closed = self.next_json()
        self.assertEqual((closed["do"], closed["agent"], closed["brief"]),
                         ("close-audit", None, {}))
        self.run_ctl("done", "audit")
        scribe = self.next_json()
        self.assert_packet(
            scribe, "scribe", ("files", "pr_base", "pr_draft_path", "plugin_root")
        )
        self.assertEqual(scribe["brief"]["files"], [])
        self.run_ctl("done", "prose", "--files", "1", "--skills",
                     "hexaemeron:imprimatur,hexaemeron:vulgate")
        push = self.next_json()
        self.assertEqual((push["do"], push["agent"], push["brief"]),
                         ("push", None, {}))
        self.run_ctl("done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
                     "--head-commit", "abc", "--pr-base", self.step_base(1))
        merge = self.next_json()
        self.assertEqual((merge["do"], merge["agent"], merge["brief"]),
                         ("merge-step", None, {}))
        self.run_ctl("done", "merge-step", "--step", "1", "--merge-commit", "1" * 40)
        integrate = self.next_json()
        self.assertEqual((integrate["do"], integrate["agent"], integrate["brief"]),
                         ("integrate", None, {}))
        self.write_run_pr()
        self.run_ctl("done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                     "--merge-commit", "f" * 40)
        done = self.next_json()
        self.assertEqual((done["do"], done["agent"], done["brief"]),
                         ("done", None, {}))

    def test_receipts_bind_bytes_and_mutation_refuses_packets(self):
        self.to_steps(("Core",))
        state = self.state()
        for name in ("study", "runbook"):
            receipt = state["receipts"][name]
            self.assertRegex(receipt["sha256"], r"^[0-9a-f]{64}$")
        self.write("runbook.md", "# changed\n")
        proc = self.run_ctl("next", expect=2)
        self.assertIn("runbook artefact digest changed", proc.stderr)

    def test_risk_block_drift_and_ambiguous_step_refuse(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.write("study.md", "# changed\n")
        proc = self.run_ctl("next", expect=2)
        self.assertIn("study artefact digest changed", proc.stderr)

        other = HexctlCase(methodName="runTest")
        other.setUp()
        try:
            other.init()
            study = other.write(
                "study.md", "```risk-register\none | boundary | check\n```\n"
            )
            other.run_ctl("done", "study", "--artifact", study)
            runbook = other.write(
                "runbook.md",
                "## Step 1: Core\n\nA.\n\n## Step 1: Core\n\nB.\n",
            )
            steps = other.write("steps.json", '["Core"]')
            other.run_ctl("done", "runbook", "--artifact", runbook,
                          "--steps-file", steps)
            proc = other.run_ctl("next", expect=2)
            self.assertIn("ambiguous runbook step", proc.stderr)
        finally:
            other.tearDown()

    def test_fenced_heading_and_register_decoys_are_not_selectors(self):
        self.init()
        study = self.write(
            "study.md",
            "~~~markdown\n```risk-register\nfake | fake | fake\n```\n~~~\n"
            "```risk-register\nreal | boundary | check\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "~~~markdown\n## Step 1: Core\n\nDecoy.\n~~~\n"
            "## Step 1: Core\n\n**Goal.** Real.\n",
        )
        steps = self.write("steps.json", '["Core"]')
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps)
        mason = self.next_json()
        self.assertEqual(
            mason["brief"]["runbook_step"]["markdown"],
            "## Step 1: Core\n\n**Goal.** Real.\n",
        )
        self.run_ctl("done", "implement", "--branch", self.step_branch(1),
                     "--commit", "abc")
        self.run_ctl("record", "security_suite", SUITE)
        warden = self.next_json()
        self.assertEqual(
            warden["brief"]["risk_register"]["markdown"],
            "```risk-register\nreal | boundary | check\n```\n",
        )

    def test_source_selectors_accept_the_protasis_spacing_grammar(self):
        controller = hexctl_module()
        protasis = protasis_module()
        heading = "## Step 1: Core   "
        self.assertIsNotNone(protasis.STEP.fullmatch(heading))
        step_source = {
            "text": heading + "\n\n**Goal.** Real.\n",
            "path": "/target/runbook.md",
            "sha256": "a" * 64,
        }
        selected = controller.source_runbook_step(
            step_source, {"n": 1, "title": "Core"}
        )
        self.assertEqual(selected["markdown"], heading + "\n\n**Goal.** Real.\n")

        register_lines = ["``` risk-register", "one | boundary | check", "```"]
        self.assertEqual(
            protasis._register_lines(register_lines, 1),
            [(2, "one | boundary | check")],
        )
        risk_source = {
            "text": "\n".join(register_lines) + "\n",
            "path": "/target/study.md",
            "sha256": "b" * 64,
        }
        selected = controller.source_risk_register(risk_source)
        self.assertEqual(selected["markdown"], "\n".join(register_lines) + "\n")

    def test_warden_refuses_an_invalid_assembled_stacked_branch(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("config", "set", "audit.stacked_suffix", '" bad"')
        proc = self.run_ctl("next", expect=2)
        self.assertIn("stacked_branch is not a valid Git branch", proc.stderr)

    def test_path_and_source_byte_caps_refuse(self):
        self.init()
        outside = tempfile.NamedTemporaryFile("w", delete=False)
        try:
            outside.write("outside\n")
            outside.close()
            proc = self.run_ctl("done", "study", "--artifact", outside.name,
                                expect=2)
            self.assertIn("escapes target directory", proc.stderr)
        finally:
            os.unlink(outside.name)

        large = self.write("large.md", "x" * (2 * 1024 * 1024 + 1))
        proc = self.run_ctl("done", "study", "--artifact", large, expect=2)
        self.assertIn("exceeds 2097152-byte cap", proc.stderr)

    def test_legacy_receipts_do_not_claim_source_binding(self):
        self.to_steps(("Core",))
        path = os.path.join(self.dir, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"].pop("sha256")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        out = self.next_json()
        self.assertEqual((out["agent"], out["brief"]), (None, {}))

    def test_missing_receipted_source_refuses(self):
        self.to_steps(("Core",))
        os.unlink(os.path.join(self.dir, "runbook.md"))
        proc = self.run_ctl("next", expect=2)
        self.assertIn("runbook artefact is not a regular file", proc.stderr)

    def test_scribe_diff_is_sorted_and_capped_at_500_entries(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        branch = self.step_branch(1)
        self.git("checkout", branch)
        for name in ("zeta.md", "alpha.md"):
            self.write(name, name)
        self.git("add", "zeta.md", "alpha.md")
        self.git("commit", "-m", "step")
        self.assertEqual(self.next_json()["brief"]["files"],
                         ["alpha.md", "zeta.md"])

        for number in range(499):
            self.write(f"many/{number:03d}.md", "x")
        self.git("add", "many")
        self.git("commit", "-m", "too many")
        proc = self.run_ctl("next", expect=2)
        self.assertIn("more than 500 paths", proc.stderr)

    def test_git_output_and_returned_path_caps_refuse(self):
        module = hexctl_module()
        fake_bin = os.path.join(self.dir, "fake-bin")
        os.makedirs(fake_bin)
        fake_git = os.path.join(fake_bin, "git")
        with open(fake_git, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nprintf '../escape.md\\0'\n")
        os.chmod(fake_git, 0o755)
        path = fake_bin + os.pathsep + os.environ.get("PATH", "")
        error = StringIO()
        with mock.patch.dict(os.environ, {"PATH": path}), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                module.scribe_files(self.dir, "base", "branch")
        self.assertIn("escapes target directory", error.getvalue())

        with open(fake_git, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                f"sys.stdout.buffer.write(b'x' * {2 * 1024 * 1024 + 1})\n"
            )
        error = StringIO()
        with mock.patch.dict(os.environ, {"PATH": path}), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                module.bounded_git(self.dir, ["diff"])
        self.assertIn("2097152-byte output cap", error.getvalue())


class TestCommitVerification(HexctlCase):
    def test_local_fake_git_negative_matrix_is_fail_closed_and_secret_safe(self):
        module = hexctl_module()
        module.GIT_TIMEOUT = 0.05
        for mode in (
            "nonzero", "timeout", "overflow", "missing-trailer",
            "duplicate-trailer", "range-confusion", "malformed-range",
            "missing-commit",
        ):
            with self.subTest(mode=mode):
                error = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {"PATH": self.env["PATH"], "FAKE_GIT_MODE": mode},
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.verify_local_range(self.dir, "base", "head", "step")
                self.assertNotIn("ghp_FAKE_SECRET", error.getvalue())
                self.assertNotIn("FAKE SIGNATURE MATERIAL", error.getvalue())

    def test_local_success_checks_every_intermediate_commit(self):
        module = hexctl_module()
        log_path = os.path.join(self.dir, "verified.log")
        with mock.patch.dict(
            os.environ,
            {
                "PATH": self.env["PATH"],
                "FAKE_GIT_MODE": "intermediate",
                "FAKE_GIT_LOG": log_path,
            },
        ):
            commits = module.verify_local_range(self.dir, "base", "head", "step")
        with open(log_path, encoding="utf-8") as handle:
            checked = handle.read().splitlines()
        self.assertEqual(commits, checked)
        self.assertEqual(len(checked), 2)

    def test_fake_github_negative_matrix_is_fail_closed_and_secret_safe(self):
        module = hexctl_module()
        module.GIT_TIMEOUT = 0.05
        for mode in (
            "nonzero", "timeout", "overflow", "invalid-json",
            "verified-false", "invalid-reason", "missing-sha",
        ):
            with self.subTest(mode=mode):
                error = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {"PATH": self.env["PATH"], "FAKE_GH_MODE": mode},
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.verify_github_commits(self.dir, ["a" * 40])
                self.assertNotIn("ghp_FAKE_SECRET", error.getvalue())
                self.assertNotIn("RAW FAKE SIGNATURE", error.getvalue())

        reasons = (
            "unknown_signature_type", "no_user", "unverified_email",
            "bad_email", "unknown_key", "malformed_signature", "invalid",
            "expired_key", "not_signing_key", "gpgverify_error",
            "gpgverify_unavailable", "unsigned",
        )
        for reason in reasons:
            with self.subTest(reason=reason):
                error = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {
                        "PATH": self.env["PATH"],
                        "FAKE_GH_MODE": "invalid-reason",
                        "FAKE_GH_REASON": reason,
                    },
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.verify_github_commits(self.dir, ["a" * 40])


class TestPublicationBindings(HexctlCase):
    def to_push(self):
        self.to_steps(("Ship",))
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )

    def test_implement_head_must_equal_declared_branch_tip(self):
        self.to_steps(("Ship",))
        proc = self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123", expect=2,
        )
        self.assertIn("branch tip", proc.stderr)

    def test_push_refuses_cross_repository_pr_and_mismatched_head(self):
        self.to_push()
        branch = self.step_branch(1)
        self.fake_refs[branch] = self.fake_sha("def456")
        proc = self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/elsewhere/example/pull/1",
            "--head-commit", "def456", "--pr-base", self.step_base(1),
            expect=2,
        )
        self.assertIn("repository", proc.stderr)

    def test_push_head_must_equal_pushed_branch_tip(self):
        self.to_push()
        proc = self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "def456", "--pr-base", self.step_base(1),
            expect=2,
        )
        self.assertIn("branch tip", proc.stderr)

    def test_repository_identity_is_bound_to_target_origin(self):
        module = hexctl_module()
        error = StringIO()
        with mock.patch.dict(
            os.environ,
            {"PATH": self.env["PATH"], "FAKE_GH_MODE": "repo-mismatch"},
        ), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                module.github_repository(self.dir)
        self.assertIn("target origin", error.getvalue())

    def test_invalid_github_value_is_refused_before_gh_and_not_echoed(self):
        module = hexctl_module()
        log_path = os.path.join(self.dir, "gh.log")
        error = StringIO()
        with mock.patch.dict(
            os.environ,
            {"PATH": self.env["PATH"], "FAKE_GH_LOG": log_path},
        ), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                module.verify_github_commits(self.dir, ["ghp_FAKE_SECRET"])
        self.assertNotIn("ghp_FAKE_SECRET", error.getvalue())
        self.assertFalse(os.path.exists(log_path))

    def test_merge_step_refuses_pr_topology_mismatch(self):
        self.to_push()
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "def456", "--pr-base", self.step_base(1),
        )
        self.env["FAKE_GH_MODE"] = "pr-mismatch"
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "b" * 40, expect=2,
        )
        self.assertIn("pull request", proc.stderr)

    def test_integrate_refuses_pr_topology_mismatch(self):
        self.to_push()
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "def456", "--pr-base", self.step_base(1),
        )
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "b" * 40,
        )
        self.write_run_pr()
        self.env["FAKE_GH_MODE"] = "pr-mismatch"
        proc = self.run_ctl(
            "done", "integrate",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "c" * 40, expect=2,
        )
        self.assertIn("pull request", proc.stderr)


class TestDelegationPacketLifecycle(HexctlCase):
    def stable_next(self, expected_do, expected_agent):
        first = self.run_ctl("next").stdout
        second = self.run_ctl("next").stdout
        self.assertEqual(first, second)
        packet = json.loads(first)
        self.assertEqual(packet["do"], expected_do)
        self.assertEqual(packet["agent"], expected_agent)
        return packet

    def test_fresh_run_emits_packets_through_integrate(self):
        self.init("fresh packet proof")
        self.stable_next("study", "surveyor")
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\n"
            "packet-state-drift | packet | compare state hash\n```\n",
        )
        self.run_ctl(
            "done", "study", "--artifact", study,
            "--skills", "hexaemeron:imprimatur",
        )
        self.stable_next("runbook", None)
        runbook = self.write(
            "runbook.md", "# Runbook\n\n## Step 1: Ship\n\n**Goal.** Ship.\n"
        )
        steps = self.write("steps.json", '["Ship"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        self.git("init", "-b", "main")
        self.git("config", "user.email", "tests@example.com")
        self.git("config", "user.name", "Hexctl Tests")
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "fixture")
        state = self.state()
        self.git("branch", state["run_branch"])
        self.git("branch", self.step_branch(1, state))
        self.stable_next("implement", "mason")
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "a" * 40,
        )
        self.stable_next("resolve-security-suite", None)
        self.run_ctl("record", "security_suite", SUITE)
        self.stable_next("audit-round", "warden")
        self.run_ctl("audit-round", "--findings", "0")
        self.stable_next("close-audit", None)
        self.run_ctl("done", "audit")
        self.stable_next("prose", "scribe")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.stable_next("push", None)
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )
        self.stable_next("merge-step", None)
        self.run_ctl(
            "done", "merge-step", "--step", "1", "--merge-commit", "e" * 40
        )
        self.stable_next("integrate", None)
        self.write_run_pr()
        self.run_ctl(
            "done", "integrate",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
        )
        self.stable_next("done", None)
        state = self.state()
        self.assertTrue(state["steps"][0]["receipts"]["implement"]["verified_commits"])
        self.assertTrue(state["steps"][0]["receipts"]["push"]["github_verified"])
        self.assertEqual(
            state["integrate"]["merges"]["1"]["github_verified"], ["e" * 40]
        )
        self.assertEqual(
            state["receipts"]["integrate"]["github_verified"], ["f" * 40]
        )
        with open(
            os.path.join(self.dir, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            ledger = handle.read()
        evidence = json.dumps(state) + ledger
        self.assertNotIn("FAKE SIGNATURE MATERIAL", evidence)
        self.assertNotIn("RAW FAKE SIGNATURE", evidence)
        self.run_ctl("verify")


class TestRunLock(HexctlCase):
    def test_live_holder_refuses_a_second_writer_with_an_actionable_message(self):
        self.init()
        holder, _, release = self.start_lock_holder()
        result = self.run_ctl("record", "key", '"value"', expect=1)
        self.assertIn(f"pid {holder.pid}", result.stderr)
        self.assertIn("`cmd_record`", result.stderr)
        self.assertIn("git worktree add", result.stderr)
        self.release_lock_holder(holder, release)

    def test_read_only_commands_answer_while_a_writer_holds_the_run(self):
        self.init()
        holder, _, release = self.start_lock_holder()
        for arguments in (("next",), ("status", "--json"), ("verify",)):
            with self.subTest(command=arguments[0]):
                self.run_ctl(*arguments)
        self.release_lock_holder(holder, release)

    def test_crashed_holder_needs_no_manual_cleanup(self):
        self.init()
        holder, _, _ = self.start_lock_holder()
        holder.kill()
        holder.communicate(timeout=5)
        self.run_ctl("record", "after_crash", '"accepted"')

    def test_normal_exit_clears_holder_metadata(self):
        self.init()
        holder, _, release = self.start_lock_holder()
        self.release_lock_holder(holder, release)
        path = os.path.join(self.dir, ".hexaemeron", "lock")
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), b"")

    def test_two_contenders_after_a_crash_cannot_both_take_the_lock(self):
        self.init()
        stale, _, _ = self.start_lock_holder("stale")
        stale.kill()
        stale.communicate(timeout=5)

        paths = []
        contenders = []
        for name in ("first", "second"):
            ready = os.path.join(self.dir, f"{name}.ready")
            release = os.path.join(self.dir, f"{name}.release")
            contenders.append(self.spawn_lock_holder(ready, release))
            paths.append((ready, release))

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            ready_indexes = [
                index
                for index, (ready, _) in enumerate(paths)
                if os.path.exists(ready)
            ]
            exited_indexes = [
                index
                for index, process in enumerate(contenders)
                if process.poll() is not None
            ]
            if len(ready_indexes) == 1 and len(exited_indexes) == 1:
                break
            time.sleep(0.01)
        else:
            self.fail("contenders did not resolve to one holder and one refusal")

        winner = ready_indexes[0]
        loser = exited_indexes[0]
        self.assertNotEqual(winner, loser)
        loser_out, loser_err = contenders[loser].communicate(timeout=5)
        self.assertEqual(contenders[loser].returncode, 1, (loser_out, loser_err))
        self.assertIn("another hexctl is holding this run", loser_err)
        self.assertIn(f"pid {contenders[winner].pid}", loser_err)
        self.release_lock_holder(contenders[winner], paths[winner][1])


class TestStepGates(HexctlCase):
    def test_step_phase_order_enforced(self):
        self.to_steps()
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("out of order", proc.stderr)

    def test_legacy_issue_phase_advances_without_creating_an_issue(self):
        self.to_steps()
        state_path = os.path.join(self.dir, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.dir, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["steps"][0]["phase"] = "issue"
        canonical_state = json.dumps(
            state, sort_keys=True, separators=(",", ":")
        )
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        entries[-1]["state"] = hashlib.sha256(canonical_state.encode()).hexdigest()
        unsigned = {key: value for key, value in entries[-1].items() if key != "hash"}
        entries[-1]["hash"] = hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")

        self.run_ctl("verify")
        directive = self.next_json()
        self.assertEqual(directive["do"], "implement")
        self.assertTrue(directive["legacy_issue_phase_skipped"])
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.assertEqual(self.next_json()["do"], "resolve-security-suite")


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
        self.run_ctl("audit-round", "--findings", "3", "--log", "audit/AUDIT.md")
        out = self.next_json()
        self.assertEqual(out["do"], "audit-round")
        self.assertEqual(out["round"], 2)
        self.assertEqual(out["prior_findings"], 3)

    def test_close_blocked_while_findings_open(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        self.run_ctl("audit-round", "--findings", "2", *LINTS_CLEAN)
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("open", proc.stderr)

    def test_clean_close_requires_fixes_evidence_when_findings_existed(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "2")
        self.run_ctl("audit-round", "--findings", "0")
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("fixes", proc.stderr)
        self.run_ctl("done", "audit", "--fixes-ref", "issue-1--audit@deadbeef")
        self.assertEqual(self.next_json()["do"], "prose")

    def test_fixes_commit_on_round_satisfies_evidence(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "1",
                     "--fixes-commit", "beef01")
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_no_further_leads_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "1", "--fixes-commit", "b1")
        proc = self.run_ctl("done", "audit", "--no-further-leads", expect=2)
        self.assertIn("--reason", proc.stderr)
        self.run_ctl("done", "audit", "--no-further-leads",
                     "--reason", "remaining lead is a gas nit, out of scope")

    def test_max_rounds_forces_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("config", "set", "audit.max_rounds", "2")
        self.run_ctl("audit-round", "--findings", "2", "--fixes-commit", "b1")
        self.run_ctl("audit-round", "--findings", "1", "--fixes-commit", "b2")
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn("max audit rounds", proc.stderr)
        out = self.next_json()
        self.assertEqual(out["do"], "audit-verdict")
        self.assertEqual(out["open_findings"], 1)


class TestProseAndPush(HexctlCase):
    def to_prose(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_prose_requires_both_configured_skills(self):
        self.to_prose()
        proc = self.run_ctl("done", "prose", "--files", "3",
                            "--skills", "hexaemeron:imprimatur", expect=2)
        self.assertIn("hexaemeron:vulgate", proc.stderr)
        self.run_ctl("done", "prose", "--files", "3",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")

    def test_push_requires_pr_url(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        proc = self.run_ctl("done", "push", expect=2)
        self.assertIn("--pr-url", proc.stderr)
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1", expect=2
        )
        self.assertIn("--head-commit", proc.stderr)
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", expect=2,
        )
        self.assertIn("--pr-base", proc.stderr)
        self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", self.step_base(1),
        )

    def test_step_pull_request_may_not_target_the_repository_base(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", "main", expect=2,
        )
        self.assertIn("--pr-base must be", proc.stderr)
        self.assertIn(self.run_branch(), proc.stderr)

    def test_step_pull_request_is_not_merged_during_the_run(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", self.step_base(1),
            "--merge-commit", "def456", expect=2,
        )
        self.assertIn("integrate", proc.stderr)

    def test_second_step_stacks_on_the_first(self):
        self.to_steps(("Scaffold", "Core"))
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        directive = self.next_json()
        self.assertEqual(directive["branch"], self.step_branch(1))
        self.assertEqual(directive["branch_from"], self.run_branch())
        self.assertEqual(directive["pr_base"], self.run_branch())
        self.assertFalse(directive["merge_now"])
        self.finish_step(1)
        directive = self.next_json()
        self.assertEqual(directive["branch"], self.step_branch(2))
        self.assertEqual(directive["branch_from"], self.step_branch(1))
        self.assertEqual(directive["pr_base"], self.step_branch(1))

    def test_run_branch_defaults_to_the_topic_slug_and_may_be_named(self):
        self.init("Borrowing-base covenant hook for V2.5")
        self.assertEqual(self.run_branch(), "fiat/borrowing-base-covenant-hook-for-v2-5")
        self.assertNotEqual(self.run_branch(), self.state()["base"])
        self.run_ctl("reset", expect=2)

    def test_named_run_branch_is_honoured_and_checked(self):
        proc = self.run_ctl("init", "--topic", "t", "--run-branch", "bad branch",
                            expect=2)
        self.assertIn("not a usable branch name", proc.stderr)
        proc = self.run_ctl("init", "--topic", "t", "--run-branch", "main",
                            "--base", "main", expect=2)
        self.assertIn("must differ from --base", proc.stderr)
        self.run_ctl("init", "--topic", "t", "--run-branch", "release/prep")
        self.assertEqual(self.run_branch(), "release/prep")

    def test_titleless_step_still_yields_a_usable_branch(self):
        self.to_steps(("###",))
        self.assertEqual(self.next_json()["branch"],
                         f"{self.run_branch()}-step-1-untitled")

    def test_step_branch_name_is_the_controller_s_to_give(self):
        self.to_steps(("Scaffold",))
        proc = self.run_ctl("done", "implement", "--branch", "step1",
                            "--commit", "abc123", expect=2)
        self.assertIn(self.step_branch(1), proc.stderr)

    def test_pre_stack_run_keeps_the_old_per_step_merge_contract(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        self.strip_run_branch()
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", expect=2,
        )
        self.assertIn("--merge-commit", proc.stderr)
        self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--merge-commit", "d" * 40,
        )
        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("implement", 2))
        self.assertNotIn("pr_base", out)

    def test_recorded_task_issue_must_be_closed_before_the_run_completes(self):
        self.to_prose()
        self.run_ctl("record", "task_issue", '"https://x/issues/74"')
        self.run_ctl(
            "done", "prose", "--files", "1",
            "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", self.step_base(1),
            "--closed-issue-url", "https://x/issues/74", expect=2,
        )
        self.assertIn("integrate phase", proc.stderr)
        self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", self.step_base(1),
        )
        self.finish_step(2)
        self.merge_stack()
        self.assertIn(
            "--closed-issue-url", self.next_json()["then"]
        )
        proc = self.run_ctl(
            "done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "runmerge", expect=2,
        )
        self.assertIn("--closed-issue-url", proc.stderr)
        proc = self.run_ctl(
            "done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
            "--closed-issue-url", "https://x/issues/75", expect=2,
        )
        self.assertIn("does not match", proc.stderr)
        self.write_run_pr()
        self.run_ctl(
            "done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
            "--closed-issue-url", "https://x/issues/74",
        )
        self.assertEqual(self.next_json()["do"], "done")

    def test_push_advances_steps_then_the_stack_integrates(self):
        self.to_steps(("One", "Two"))
        self.run_ctl("record", "security_suite", SUITE)
        run_branch = self.run_branch()
        first, second = self.step_branch(1), self.step_branch(2)
        self.finish_step(1)
        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("implement", 2))
        self.finish_step(2)

        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("merge-step", 1))
        self.assertEqual((out["branch"], out["into"]), (first, run_branch))

        proc = self.run_ctl("done", "merge-step", "--step", "2",
                            "--merge-commit", "m2", expect=2)
        self.assertIn("step order", proc.stderr)
        proc = self.run_ctl("done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                            "--merge-commit", "runmerge", expect=2)
        self.assertIn("still has to merge", proc.stderr)

        self.run_ctl("done", "merge-step", "--step", "1", "--merge-commit", "1" * 40)
        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("merge-step", 2))
        self.assertEqual((out["branch"], out["into"]), (second, run_branch))
        self.run_ctl("done", "merge-step", "--step", "2", "--merge-commit", "2" * 40)

        out = self.next_json()
        self.assertEqual(out["do"], "integrate")
        self.assertEqual((out["run_branch"], out["base"]), (run_branch, "main"))
        proc = self.run_ctl("done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                            expect=2)
        self.assertIn("--merge-commit", proc.stderr)
        self.write_run_pr()
        self.run_ctl("done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                     "--merge-commit", "f" * 40)
        self.assertEqual(self.next_json()["do"], "done")
        self.run_ctl("verify")

    def test_integrate_refuses_a_run_that_never_said_what_it_left_undone(self):
        self.to_steps(("One",))
        self.run_ctl("record", "security_suite", SUITE)
        self.finish_step(1)
        self.merge_stack()
        args = ["done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                "--merge-commit", "f" * 40]

        proc = self.run_ctl(*args, expect=2)
        self.assertIn("cannot be read", proc.stderr)

        self.write(os.path.join(".hexaemeron", "run-pr.md"),
                   "Run body with no section.\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("Carried forward", proc.stderr)

        self.write_run_pr(carried="\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("nothing under it", proc.stderr)

        # A later section cannot stand in for this one.
        self.write(os.path.join(".hexaemeron", "run-pr.md"),
                   "Run body.\n\n## Carried forward\n\n## Checks\n\n- root 38\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("nothing under it", proc.stderr)

        self.write_run_pr(carried="- no CI workflow for this plugin yet\n")
        self.run_ctl(*args)
        receipt = self.state()["receipts"]["integrate"]["carried_forward"]
        self.assertEqual(receipt["lines"], 1)
        self.assertEqual(receipt["path"], ".hexaemeron/run-pr.md")
        self.assertEqual(len(receipt["sha256"]), 64)
        self.run_ctl("verify")

    def test_reset_refuses_a_run_whose_stack_has_not_landed(self):
        self.to_steps(("One",))
        self.run_ctl("record", "security_suite", SUITE)
        self.finish_step(1)
        proc = self.run_ctl("reset", expect=2)
        self.assertIn("integrate", proc.stderr)


class TestControls(HexctlCase):
    def test_halt_blocks_progress_and_resume_restores(self):
        self.to_steps()
        self.run_ctl("halt", "--reason", "waiting on Oliver")
        self.assertEqual(self.next_json()["do"], "halted")
        proc = self.run_ctl("done", "implement", "--branch", "step-1",
                            "--commit", "abc123",
                            expect=2)
        self.assertIn("halted", proc.stderr)
        self.run_ctl("resume", "--note", "cleared")
        self.assertEqual(self.next_json()["do"], "implement")

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

    def test_verify_preserves_receipt_assertions_without_proving_them(self):
        self.to_steps(("One",))
        assertion = "all dragons defeated"
        self.run_ctl(
            "done",
            "implement",
            "--branch",
            self.step_branch(1),
            "--commit",
            "abc123",
            "--tests",
            assertion,
        )
        self.run_ctl("verify")
        state = json.loads(self.run_ctl("status", "--json").stdout)
        receipt = state["steps"][0]["receipts"]["implement"]
        self.assertEqual(receipt["tests"], assertion)

    def test_record_and_status_json(self):
        self.init()
        self.run_ctl("record", "note", '"local run"')
        state = json.loads(self.run_ctl("status", "--json").stdout)
        self.assertEqual(state["receipts"]["note"], "local run")
        self.assertEqual(state["phase"], "study")

    def test_reset_archives_completed_run_and_allows_reinit(self):
        self.to_steps(("One",))
        self.run_ctl("record", "security_suite", SUITE)
        self.finish_step(1)
        self.integrate_run()
        self.assertEqual(self.next_json()["do"], "done")

        self.run_ctl("reset")
        root = os.path.join(self.dir, ".hexaemeron")
        self.assertFalse(os.path.exists(os.path.join(root, "state.json")))
        archives = os.listdir(os.path.join(root, "archive"))
        self.assertEqual(len(archives), 1)
        archived = os.path.join(root, "archive", archives[0])
        self.assertTrue(os.path.exists(os.path.join(archived, "state.json")))
        self.assertTrue(os.path.exists(os.path.join(archived, "ledger.jsonl")))

        self.init("next topic")
        state = json.loads(self.run_ctl("status", "--json").stdout)
        self.assertEqual(state["topic"], "next topic")

    def test_reset_refuses_incomplete_run(self):
        self.init()
        proc = self.run_ctl("reset", expect=2)
        self.assertIn("refusing to reset an incomplete run", proc.stderr)
        self.assertEqual(self.next_json()["do"], "study")

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
        self.run_ctl("audit-round", "--findings", "2", "--log", "a.md",
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
                     "--steps-file", sf)
        proc = self.run_ctl("status")
        self.assertNotIn("\x1b", proc.stdout)


class LintReceiptTests(HexctlCase):
    """The three lint results a non-Solidity round owes, and the refusals."""

    def to_waived_audit(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')

    def to_solidity_audit(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)

    def rounds(self):
        return self.state()["steps"][0]["audit"]["rounds"]

    def test_a_non_solidity_round_is_refused_without_any_of_the_three(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", expect=2)
        for lint in ("phylax", "ephoros", "hypomnema"):
            self.assertIn(f"--{lint}-exit", proc.stderr)

    def test_the_refusal_names_only_what_is_still_missing(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0",
                            "--phylax-exit", "0", "--ephoros-exit", "0", expect=2)
        self.assertIn("--hypomnema-exit", proc.stderr)
        self.assertNotIn("--phylax-exit", proc.stderr)
        self.assertNotIn("--ephoros-exit", proc.stderr)

    def test_the_refusal_points_at_the_override(self):
        """A run whose receipt cannot be read but which really is a Solidity run has a
        way out, and the refusal says what it is."""
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", expect=2)
        self.assertIn("config set solidity true", proc.stderr)

    def test_a_complete_round_records_all_three(self):
        self.to_waived_audit()
        out = self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN).stdout
        self.assertIn("lints phylax 0, ephoros 0, hypomnema 0", out)
        self.assertEqual(
            self.rounds()[0]["lints"],
            {"phylax": 0, "ephoros": 0, "hypomnema": 0},
        )

    def test_a_recorded_non_zero_exit_survives_onto_the_round(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "3",
                     "--phylax-exit", "1", "--ephoros-exit", "0", "--hypomnema-exit", "2")
        self.assertEqual(
            self.rounds()[0]["lints"], {"phylax": 1, "ephoros": 0, "hypomnema": 2}
        )

    def test_zero_findings_beside_a_failing_lint_is_refused(self):
        """A non-zero lint exit is a finding like any other, so the two halves of the
        receipt would otherwise contradict each other."""
        self.to_waived_audit()
        for flag in ("--phylax-exit", "--ephoros-exit", "--hypomnema-exit"):
            with self.subTest(flag=flag):
                args = ["audit-round", "--findings", "0", *LINTS_CLEAN]
                args[args.index(flag) + 1] = "1"
                proc = self.run_ctl(*args, expect=2)
                self.assertIn("0 findings", proc.stderr)
                self.assertIn("finding like any other", proc.stderr)

    def test_a_failing_lint_with_findings_recorded_is_accepted(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "1",
                     "--phylax-exit", "1", "--ephoros-exit", "0", "--hypomnema-exit", "0")
        self.assertEqual(self.rounds()[0]["findings"], 1)

    def test_a_negative_exit_is_refused(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", "--phylax-exit", "-1",
                            "--ephoros-exit", "0", "--hypomnema-exit", "0", expect=2)
        self.assertIn("non-negative exit status", proc.stderr)

    def test_a_non_integer_exit_is_refused_by_the_parser(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", "--phylax-exit", "clean",
                            "--ephoros-exit", "0", "--hypomnema-exit", "0", expect=2)
        self.assertIn("invalid int value", proc.stderr)

    def test_a_solidity_round_needs_none_of_them(self):
        self.to_solidity_audit()
        self.run_ctl("audit-round", "--findings", "0", "--log", "audit/AUDIT.md")
        self.assertIsNone(self.rounds()[0]["lints"])

    def test_a_solidity_round_may_still_record_them(self):
        self.to_solidity_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.assertEqual(
            self.rounds()[0]["lints"], {"phylax": 0, "ephoros": 0, "hypomnema": 0}
        )

    def test_the_consistency_rule_applies_to_a_solidity_round_too(self):
        """If the exits are recorded at all, they have to agree with the count."""
        self.to_solidity_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", "--phylax-exit", "1",
                            "--ephoros-exit", "0", "--hypomnema-exit", "0", expect=2)
        self.assertIn("finding like any other", proc.stderr)

    def test_the_override_lifts_the_requirement(self):
        self.to_waived_audit()
        self.run_ctl("config", "set", "solidity", "true")
        self.run_ctl("audit-round", "--findings", "0", "--log", "audit/AUDIT.md")
        self.assertIsNone(self.rounds()[0]["lints"])

    def test_the_override_can_impose_it_on_a_recorded_suite(self):
        self.to_solidity_audit()
        self.run_ctl("config", "set", "solidity", "false")
        proc = self.run_ctl("audit-round", "--findings", "0", expect=2)
        self.assertIn("--phylax-exit", proc.stderr)

    def test_next_names_the_flags_a_non_solidity_round_owes(self):
        self.to_waived_audit()
        out = self.next_json()
        self.assertEqual(out["do"], "audit-round")
        self.assertEqual(
            out["lints"], ["--phylax-exit", "--ephoros-exit", "--hypomnema-exit"]
        )

    def test_next_stays_quiet_about_lints_on_a_solidity_round(self):
        self.to_solidity_audit()
        self.assertNotIn("lints", self.next_json())

    def test_next_still_names_them_on_a_later_round(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "2", *LINTS_CLEAN)
        out = self.next_json()
        self.assertEqual(out["round"], 2)
        self.assertEqual(out["prior_findings"], 2)
        self.assertIn("--phylax-exit", out["lints"])

    def test_closing_the_audit_reads_a_round_that_carries_lints(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", "--log", "audit/AUDIT.md",
                     *LINTS_CLEAN)
        self.run_ctl("done", "audit")
        self.assertEqual(self.state()["steps"][0]["phase"], "prose")

    def test_a_clean_close_now_implies_the_lints_passed(self):
        """An emergent property worth pinning. `done audit` calls a close clean when the
        last round found nothing, and the consistency rule forbids a zero findings count
        beside a non-zero exit, so a clean close cannot sit on a failing lint. Nothing
        asserted that, and it is the property the whole change buys."""
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", "--phylax-exit", "1",
                            "--ephoros-exit", "0", "--hypomnema-exit", "0", expect=2)
        self.assertIn("finding like any other", proc.stderr)

        self.run_ctl("audit-round", "--findings", "1", "--phylax-exit", "1",
                     "--ephoros-exit", "0", "--hypomnema-exit", "0")
        blocked = self.run_ctl("done", "audit", expect=2)
        self.assertIn("open", blocked.stderr)

        self.run_ctl("audit-round", "--findings", "0", "--log", "audit/AUDIT.md",
                     *LINTS_CLEAN)
        self.run_ctl("done", "audit", "--fixes-ref", "deadbeef")
        receipt = self.state()["steps"][0]["receipts"]["audit"]
        self.assertTrue(receipt["clean"])
        rounds = self.rounds()
        self.assertEqual(rounds[-1]["findings"], 0)
        self.assertEqual(set(rounds[-1]["lints"].values()), {0})

    def test_a_round_recorded_before_this_existed_still_reads(self):
        """Rounds already on disk carry no lints key. Every reader has to treat it as
        absent rather than assume it."""
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", "--log", "audit/AUDIT.md",
                     *LINTS_CLEAN)
        path = os.path.join(self.dir, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state["steps"][0]["audit"]["rounds"][0].pop("lints")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        self.run_ctl("status")
        self.run_ctl("next")
        self.run_ctl("done", "audit")
        self.assertEqual(self.state()["steps"][0]["phase"], "prose")


class RoundClassifierTests(unittest.TestCase):
    """Which rounds have to carry lint results, and why."""

    @classmethod
    def setUpClass(cls):
        cls.ctl = hexctl_module()

    def classify(self, suite=..., mode="auto"):
        receipts = {} if suite is ... else {"security_suite": suite}
        return self.ctl.solidity_round({"config": {"solidity": mode}, "receipts": receipts})

    def test_a_waiver_means_the_lints_are_the_mechanical_part(self):
        self.assertFalse(self.classify("waived: prose-only repo"))

    def test_a_waiver_is_recognised_whatever_its_case_and_spacing(self):
        for value in ("waived: x", "Waived: x", "  WAIVED: x  ", "waived x"):
            with self.subTest(receipt=value):
                self.assertFalse(self.classify(value))

    def test_a_recorded_suite_means_the_pashov_pair_ran(self):
        self.assertTrue(self.classify(["hexaemeron:x-ray", "hexaemeron:solidity-auditor"]))

    def test_an_empty_suite_list_is_not_a_suite_that_ran(self):
        """Recording no ids is not recording a suite. Demanding the lints is the safe
        direction when the receipt cannot be read as one."""
        self.assertFalse(self.classify([]))

    def test_a_receipt_that_is_neither_demands_the_lints(self):
        for value in ("suite", 7, {"suite": True}, None, True):
            with self.subTest(receipt=value):
                self.assertFalse(self.classify(value))

    def test_a_missing_receipt_infers_nothing(self):
        """`cmd_audit_round` refuses a missing receipt before asking this, so the
        classifier must not invent a requirement out of its absence."""
        self.assertTrue(self.classify())

    def test_the_config_key_overrides_the_receipt_in_both_directions(self):
        self.assertTrue(self.classify("waived: x", mode=True))
        self.assertFalse(self.classify(["hexaemeron:x-ray"], mode=False))

    def test_the_default_mode_is_auto(self):
        self.assertEqual(self.ctl.DEFAULT_CONFIG["solidity"], "auto")

    def test_the_waiver_prefix_is_what_preflight_writes(self):
        self.assertTrue("waived: reason".startswith(self.ctl.WAIVER_PREFIX))

    def test_the_three_lints_are_named_once(self):
        self.assertEqual(self.ctl.LINTS, ("phylax", "ephoros", "hypomnema"))

    def test_a_waiver_is_its_first_word_not_merely_a_prefix(self):
        """`startswith` alone read `waivedX` and `waived-ish` as waivers, which is not
        what the rule beside WAIVER_PREFIX says."""
        for value in ("waived: x", "waived", "  WAIVED: y  ", "waived x"):
            with self.subTest(receipt=value, expect=True):
                self.assertTrue(self.ctl.is_waiver(value))
        for value in ("waivedX", "waived-ish", "waivers: x", "unwaived: x", "not waived", ""):
            with self.subTest(receipt=value, expect=False):
                self.assertFalse(self.ctl.is_waiver(value))

    def test_a_state_whose_config_or_receipts_is_not_an_object_does_not_raise(self):
        """load_state validates no shape, so a hand-edited or half-written state
        reaches the classifier. A traceback out of the controller is a worse answer
        than the one every other fault here gets."""
        for config in (None, [], "auto", 7):
            with self.subTest(config=config):
                self.assertIsInstance(
                    self.ctl.solidity_round({"config": config, "receipts": {}}), bool
                )
        for receipts in (None, [], "waived", 7):
            with self.subTest(receipts=receipts):
                self.assertIsInstance(
                    self.ctl.solidity_round(
                        {"config": {"solidity": "auto"}, "receipts": receipts}
                    ),
                    bool,
                )
        self.assertIsInstance(self.ctl.solidity_round({}), bool)

    def test_as_dict_defeats_a_stored_null(self):
        """d.get(key, {}) returns the stored value when the key exists, so a state
        holding "integrate": null defeated the default and the next .get raised. Four
        chained reads in the controller had that shape."""
        for value in (None, [], "x", 7, True):
            with self.subTest(value=value):
                self.assertEqual(self.ctl.as_dict(value), {})
        self.assertEqual(self.ctl.as_dict({"a": 1}), {"a": 1})

    def test_no_chained_read_uses_a_container_default(self):
        """The pattern this run removed, asserted against the source so it does not
        come back: `.get(x, {}).` and `.get(x, []).` are both defeated by a stored
        null."""
        import re

        with open(HEXCTL, encoding="utf-8") as fh:
            source = fh.read()
        offenders = re.findall(r"\.get\([^)]*,\s*(?:\{\}|\[\])\)\s*\.", source)
        self.assertEqual(offenders, [], "use as_dict() instead")

    def test_an_integer_is_not_a_mode(self):
        for value in (0, 1, 2):
            with self.subTest(value=value):
                self.assertFalse(self.ctl.solidity_mode(value))
        for value in (True, False, "auto"):
            with self.subTest(value=value):
                self.assertTrue(self.ctl.solidity_mode(value))


class SolidityConfigTests(HexctlCase):
    def test_the_solidity_key_accepts_only_its_three_modes(self):
        self.init()
        for value in ('"auto"', "true", "false"):
            with self.subTest(value=value):
                self.run_ctl("config", "set", "solidity", value)
        self.assertEqual(json.loads(self.run_ctl("config", "get", "solidity").stdout), False)

    def test_a_value_outside_the_three_modes_is_refused(self):
        """`1` and `0` are in here because Python makes them equal to `True` and
        `False`, so a membership test would have stored an integer as a mode."""
        self.init()
        for value in ('"yes"', "1", "0", '"Auto"', '["auto"]', "null"):
            with self.subTest(value=value):
                proc = self.run_ctl("config", "set", "solidity", value, expect=2)
                self.assertIn("config solidity takes", proc.stderr)

    def test_a_refused_value_leaves_the_key_alone(self):
        self.init()
        self.run_ctl("config", "set", "solidity", "false")
        self.run_ctl("config", "set", "solidity", '"nonsense"', expect=2)
        self.assertEqual(json.loads(self.run_ctl("config", "get", "solidity").stdout), False)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class StaleControllerTests(unittest.TestCase):
    """A run driven by an installed plugin older than the repository it edits.

    A marketplace plugin is installed from a published copy, so a repository that
    also holds Fiat's source can be a whole evolution ahead of the controller
    driving the run. Every rule the newer one enforces then goes unenforced, and
    the receipt cannot show it: a flag the controller does not accept looks
    exactly like a rule nobody wrote. This shipped after a run recorded its lint
    results as prose because the installed `audit-round` was a version behind the
    flags its own ledger documented.
    """

    def _repo(self, directory, version):
        path = os.path.join(
            directory, "plugins", "hexaemeron", "skills", "fiat"
        )
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "EVOLUTION.md"), "w", encoding="utf-8") as fh:
            fh.write(f"- Current version: `{version}`\n")
        return directory

    def test_ledger_version_reads_the_declared_version(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "EVOLUTION.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# Ledger\n\n- Current version: `fiat-v4.4.1`\n- Frontier status: `open`\n")
            self.assertEqual(module.ledger_version(path), "fiat-v4.4.1")

    def test_ledger_version_is_none_when_absent_or_unreadable(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as directory:
            missing = os.path.join(directory, "nope.md")
            self.assertIsNone(module.ledger_version(missing))
            empty = os.path.join(directory, "empty.md")
            with open(empty, "w", encoding="utf-8") as fh:
                fh.write("# Ledger\n\nno version line here\n")
            self.assertIsNone(module.ledger_version(empty))

    def test_a_newer_checked_in_copy_is_reported(self):
        module = hexctl_module()
        running = module.ledger_version(
            os.path.join(os.path.dirname(HEXCTL), os.pardir, "EVOLUTION.md")
        )
        self.assertIsNotNone(running)
        with tempfile.TemporaryDirectory() as directory:
            self._repo(directory, "fiat-v99.9.9")
            found = module.stale_controller(directory)
        self.assertIsNotNone(found)
        self.assertEqual(found[0], running)
        self.assertEqual(found[1], "fiat-v99.9.9")
        self.assertIn("EVOLUTION.md", found[2])

    def test_matching_versions_are_silent(self):
        module = hexctl_module()
        running = module.ledger_version(
            os.path.join(os.path.dirname(HEXCTL), os.pardir, "EVOLUTION.md")
        )
        with tempfile.TemporaryDirectory() as directory:
            self._repo(directory, running)
            self.assertIsNone(module.stale_controller(directory))

    def test_a_target_without_fiat_is_silent(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(module.stale_controller(directory))

    def test_the_plugins_own_source_tree_is_not_compared_against_itself(self):
        """Running Fiat on the repository that holds it must not warn.

        The candidate it would find is the very ledger it just read, so a naive
        comparison is silent only by luck of the versions matching. It is skipped
        by identity instead.
        """
        module = hexctl_module()
        target = os.path.realpath(os.path.join(HERE, "..", "..", ".."))
        own = os.path.join(target, "plugins", "hexaemeron", "skills", "fiat", "EVOLUTION.md")
        if not os.path.isfile(own):
            self.skipTest("not running from the plugin's own checkout")
        self.assertIsNone(module.stale_controller(target))

    def test_init_warns_on_stderr_without_failing_the_run(self):
        module_dir = tempfile.mkdtemp()
        try:
            self._repo(module_dir, "fiat-v99.9.9")
            done = subprocess.run(
                [sys.executable, HEXCTL, "--dir", module_dir, "init",
                 "--topic", "stale probe", "--base", "main"],
                capture_output=True, text=True,
            )
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("warning", done.stderr)
            self.assertIn("fiat-v99.9.9", done.stderr)
            self.assertIn("initialised", done.stdout)
            # A warning that does not say what to do gets read and ignored.
            self.assertIn("plugin-currency.md", done.stderr)
            self.assertIn("controller_version", done.stderr)
        finally:
            import shutil
            shutil.rmtree(module_dir, ignore_errors=True)


LEDGER_HEADER = """# Widget evolution ledger

- Current version: `{version}`
- Frontier status: `{status}`
- Frontier revision: `{revision}`
- Current frontier: {frontier}
- Next Fiat job: {job}

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
"""


def widget_ledger(path, rows, *, version, status="open", revision="held-thing",
                  frontier="The widget does not do the thing.",
                  job="Make the widget do the thing."):
    """A governed ledger with the header and rows a caller dictates."""
    text = LEDGER_HEADER.format(version=version, status=status, revision=revision,
                                frontier=frontier, job=job) + "".join(rows)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def frontier_digest(status, revision, frontier, job):
    return hashlib.sha256(
        ("|".join((status, revision, frontier, job)) + "\n").encode("utf-8")
    ).hexdigest()


def row(version, axis, revision, digest, change="Did the thing."):
    return f"| `{version}` | {axis} | `{revision}` | `{digest}` | [e](f) | {change} |\n"


class FrontierGateTests(unittest.TestCase):
    """A frontier run proves its ledger update instead of asserting it.

    The maturity gate says to update the ledger exactly once per completed
    frontier job, in prose. This repository has already had to reconstruct two
    broken evolutions, so the terminal receipt now refuses until the ledger
    carries exactly one new row valid under the versioning contract.
    """

    HELD = ("open", "held-thing", "The widget does not do the thing.",
            "Make the widget do the thing.")
    NEXT = ("open", "new-thing", "The widget does the thing; the next is undone.",
            "Make the widget do the next thing.")

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.ledger = os.path.join(
            self.dir, "plugins", "demo", "skills", "widget", "EVOLUTION.md")
        self.base_digest = frontier_digest(*self.HELD)
        self.base_row = row("widget-v1.1.0", "baseline", self.HELD[1],
                            self.base_digest, "Versioning starts here.")
        widget_ledger(self.ledger, [self.base_row], version="widget-v1.1.0",
                      status=self.HELD[0], revision=self.HELD[1],
                      frontier=self.HELD[2], job=self.HELD[3])
        with open(self.ledger, "rb") as handle:
            ledger_sha256 = hashlib.sha256(handle.read()).hexdigest()
        self.before = {
            "ledger": os.path.relpath(self.ledger, self.dir),
            "sha256": ledger_sha256,
            "rows": 1,
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def fault(self):
        return hexctl_module().frontier_close_fault(self.ledger, self.before)

    def close_with(self, version, axis, header=None, digest=None, extra=()):
        header = header or self.NEXT
        widget_ledger(
            self.ledger,
            [self.base_row, row(version, axis, header[1],
                                digest or frontier_digest(*header)), *extra],
            version=version, status=header[0], revision=header[1],
            frontier=header[2], job=header[3])

    def test_an_untouched_ledger_is_refused(self):
        self.assertIn("byte-for-byte what it was at init", self.fault())

    def test_a_correct_evolution_row_closes(self):
        self.close_with("widget-v2.1.0", "evolution")
        self.assertIsNone(self.fault())

    def test_a_wrong_digest_is_refused(self):
        self.close_with("widget-v2.1.0", "evolution", digest="0" * 64)
        self.assertIn("digest does not match", self.fault())

    def test_wrong_axis_arithmetic_is_refused(self):
        self.close_with("widget-v9.1.0", "evolution")
        self.assertIn("must be widget-v2.1.0", self.fault())

    def test_two_new_rows_are_refused(self):
        self.close_with("widget-v2.1.0", "evolution",
                        extra=[row("widget-v3.1.0", "evolution", self.NEXT[1],
                                   frontier_digest(*self.NEXT))])
        self.assertIn("gained 2 history row(s)", self.fault())

    def test_a_generation_must_hold_the_frontier(self):
        # Same axis arithmetic, but the revision moved, which a generation may
        # not do: the held target has to survive it byte for byte.
        self.close_with("widget-v1.2.0", "generation")
        self.assertIn("retain the prior frontier revision", self.fault())

    def test_a_generation_holding_the_frontier_closes(self):
        self.close_with("widget-v1.2.0", "generation", header=self.HELD)
        self.assertIsNone(self.fault())

    def test_a_header_row_mismatch_is_refused(self):
        widget_ledger(
            self.ledger,
            [self.base_row, row("widget-v2.1.0", "evolution", self.NEXT[1],
                                frontier_digest(*self.NEXT))],
            version="widget-v7.7.7", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIn("they have to be the same row", self.fault())

    def test_a_mature_frontier_needs_no_next_job(self):
        mature = ("mature", "new-thing", "Nothing evidenced remains.",
                  "Make the widget do the next thing.")
        self.close_with("widget-v2.1.0", "evolution", header=mature)
        self.assertIn("`None -- mature`", self.fault())

    def test_a_mature_frontier_with_none_closes(self):
        mature = ("mature", "new-thing", "Nothing evidenced remains.",
                  "None -- mature")
        self.close_with("widget-v2.1.0", "evolution", header=mature)
        self.assertIsNone(self.fault())

    def test_an_unreadable_ledger_is_reported_not_raised(self):
        os.remove(self.ledger)
        self.assertIn("cannot be read", self.fault())

    def test_init_refuses_a_frontier_that_is_not_a_ledger(self):
        plain = os.path.join(self.dir, "notes.md")
        with open(plain, "w", encoding="utf-8") as fh:
            fh.write("# notes\n\nno version line\n")
        done = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "t",
             "--base", "main", "--frontier", "notes.md"],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 2)
        self.assertIn("states no `Current version`", done.stderr)

    def test_init_without_frontier_records_none(self):
        done = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "t",
             "--base", "main"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("frontier run:", done.stdout)
        with open(os.path.join(self.dir, ".hexaemeron", "state.json"),
                  encoding="utf-8") as fh:
            self.assertIsNone(json.load(fh)["frontier"])

    def test_init_in_frontier_mode_records_and_announces(self):
        done = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "t",
             "--base", "main", "--frontier", self.before["ledger"]],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("frontier run:", done.stdout)
        self.assertIn("widget-v1.1.0", done.stdout)
        with open(os.path.join(self.dir, ".hexaemeron", "state.json"),
                  encoding="utf-8") as fh:
            held = json.load(fh)["frontier"]
        self.assertEqual(held["rows"], 1)
        self.assertEqual(held["sha256"], self.before["sha256"])
