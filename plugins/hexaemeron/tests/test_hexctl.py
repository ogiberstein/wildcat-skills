"""End-to-end tests for hexctl, run through the CLI the way the skill uses it."""

import argparse
import glob
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
from contextlib import ExitStack, redirect_stderr
from io import BytesIO, StringIO, TextIOWrapper
from pathlib import Path
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
HEXCTL = os.path.join(HERE, "..", "skills", "fiat", "scripts", "hexctl.py")
AUDIT_SYNOPSIS = os.path.join(
    HERE, "..", "skills", "fiat", "scripts", "audit_synopsis.py"
)
PROTASIS = os.path.join(HERE, "..", "skills", "protasis", "scripts", "protasis.py")
COMPLETE_STUDY = os.path.join(HERE, "fixtures", "protasis", "complete-study.md")

SUITE = '["hexaemeron:x-ray", "hexaemeron:solidity-auditor"]'
"""A security_suite receipt shaped like the one preflight records.

These tests used the string "suite", which is neither a waiver nor a list of ids. The
round classifier reads it as a receipt it cannot make sense of, and demands the lint
results, which is the right answer for a receipt like that and the wrong fixture for a
test about a Solidity round.
"""

LINTS_CLEAN = ("--phylax-exit", "0", "--ephoros-exit", "0", "--hypomnema-exit", "0")
"""What a non-Solidity round records when all three lints came back clean."""


def make_origin_checkout(path):
    """A real repository on `main` at `path`.

    `init` creates a worktree, so every fixture it runs against has to be a real
    repository. The fake git covers signatures, refs and pull requests; it cannot
    stand in for repository structure.
    """
    for argv in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "fixture@example.invalid"],
        ["config", "user.name", "Fixture"],
        ["config", "commit.gpgsign", "false"],
        ["commit", "-q", "--allow-empty", "-m", "base"],
    ):
        subprocess.run(["git", *argv], cwd=path, check=True, capture_output=True)


def run_target(base_dir):
    """Where a run started in `base_dir` keeps its state.

    `init` prints the run worktree and tells the caller to pass it as `--dir`.
    The tests follow the same breadcrumb rather than reaching past it, so they
    exercise the arrangement an operator actually gets.
    """
    crumb = os.path.join(base_dir, ".hexaemeron", "worktree")
    try:
        with open(crumb, encoding="utf-8") as handle:
            recorded = handle.read().strip()
    except OSError:
        return base_dir
    if recorded and os.path.exists(os.path.join(recorded, ".hexaemeron", "state.json")):
        return recorded
    return base_dir


class OriginCheckoutMixin:
    """A `target` that follows the run into its worktree."""

    @property
    def target(self):
        return run_target(self.dir)


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


def audit_synopsis_module():
    """The sibling renderer imported under the controller test runner."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "audit_synopsis_under_test", AUDIT_SYNOPSIS
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def protasis_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("protasis_under_test", PROTASIS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditSynopsisResourceBoundaryTests(unittest.TestCase):
    def test_record_framing_preserves_literal_separator_and_escape_tokens(self):
        renderer = audit_synopsis_module()
        lead = "Leads not pursued: literal <br>; escapes %, %%, and %b"
        source = (
            "\n".join(
                [
                    "## Fixture, step 1, round 1 -- 2026-08-23T02:17:46Z",
                    "",
                    "Audit schema: fiat-audit-round/v1",
                    "",
                    "Covered: fixture-risk=reviewed",
                    "",
                    "Not checked: none",
                    "",
                    "Elenchus verdict: null",
                    "",
                    "| id | severity | file | finding | status |",
                    "| --- | --- | --- | --- | --- |",
                    "| -- | -- | -- | none | -- |",
                    "",
                    lead,
                ]
            )
            + "\n"
        ).encode()
        rendered = renderer.render_source("audit/AUDIT.md", source)
        record = rendered["bytes"].decode().splitlines()[1]
        decoder = getattr(renderer, "decode_synopsis_record", None)
        physical = record.split("<br>") if decoder is None else decoder(record)

        self.assertEqual(physical[-1], lead)
        self.assertEqual(physical.count(lead), 1)
        self.assertTrue(callable(decoder))

    def test_many_short_lines_remain_inside_the_receipted_acceptance_domain(self):
        renderer = audit_synopsis_module()
        source = b"## legacy\nLeads not pursued:\n" + b"x\n" * 200_000
        rendered = renderer.render_source("audit/AUDIT.md", source)

        self.assertEqual(rendered["source_lines"], 200_002)
        self.assertEqual(rendered["h2_count"], 1)
        self.assertLess(len(rendered["bytes"]), renderer.SYNOPSIS_BYTES_MAX)

    def test_table_cell_scanner_scales_with_the_accepted_line_length(self):
        renderer = audit_synopsis_module()

        def elapsed(size):
            line = "| " + "x" * size + " | b | c | d | e |"
            started = time.process_time()
            self.assertEqual(len(renderer._table_cells(line)), 5)
            return time.process_time() - started

        small = elapsed(64 * 1024)
        large = elapsed(512 * 1024)
        self.assertLess(
            large,
            small * 20,
            f"table scan scaled from {small:.6f}s to {large:.6f}s",
        )


class HexctlCase(OriginCheckoutMixin, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.processes = []
        self.env = os.environ.copy()
        self.fake_refs = {}
        self.fake_prs = {}
        self.fake_parents = {}
        self.install_fake_delivery_tools()
        make_origin_checkout(self.dir)


    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        self.tmp.cleanup()

    def run_ctl(self, *args, expect=0):
        pending_refs = dict(self.fake_refs)
        pending_prs = json.loads(json.dumps(self.fake_prs))
        pending_parents = json.loads(json.dumps(self.fake_parents))
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        state = None
        if os.path.exists(state_path):
            try:
                with open(state_path, encoding="utf-8") as handle:
                    state = json.load(handle)
            except (OSError, ValueError):
                state = None
        if (
            args[:1] == ("audit-round",)
            and expect == 0
            and getattr(self, "auto_audit_records", True)
        ):
            self.append_valid_audit_record(args, state)
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
        env["FAKE_GIT_PARENTS"] = json.dumps(pending_parents)
        env["FAKE_GH_PRS"] = json.dumps(pending_prs)
        proc = subprocess.run(
            [sys.executable, HEXCTL, *args],
            cwd=self.target,
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
            self.fake_parents = pending_parents
        return proc

    def append_valid_audit_record(self, args, state):
        """Stand in for Warden when a controller test is not about log syntax."""
        if state is None:
            raise AssertionError("cannot write an audit record without controller state")
        findings = int(args[args.index("--findings") + 1])
        verdict = (
            args[args.index("--elenchus-verdict") + 1]
            if "--elenchus-verdict" in args
            else "null"
        )
        study_path = state["receipts"]["study"]["artifact"]
        if not os.path.isabs(study_path):
            study_path = os.path.join(self.target, study_path)
        with open(study_path, encoding="utf-8") as handle:
            study = handle.read()
        block = re.search(
            r"(?ms)^```risk-register\s*$\n(?P<body>.*?)^```\s*$",
            study,
        )
        if block is None:
            raise AssertionError("fixture study has no risk register")
        risk_ids = [
            line.split("|", 1)[0].strip()
            for line in block.group("body").splitlines()
            if line.strip()
        ]
        covered = "; ".join(f"{risk_id}=reviewed" for risk_id in risk_ids)
        round_number = len(
            state["steps"][state["current_step"] - 1]["audit"]["rounds"]
        ) + 1
        table_rows = (
            ["| -- | -- | -- | none | -- |"]
            if findings == 0
            else [
                f"| F-{index:02d} | low | fixture.py | finding {index} | open |"
                for index in range(1, findings + 1)
            ]
        )
        record = "\n".join(
            [
                f"## {state['topic']}, step {state['current_step']}, "
                f"round {round_number} -- 2026-08-23T02:17:46Z",
                "",
                "Audit schema: fiat-audit-round/v1",
                "",
                f"Covered: {covered}",
                "",
                "Not checked: none",
                "",
                f"Elenchus verdict: {verdict}",
                "",
                "| id | severity | file | finding | status |",
                "| --- | --- | --- | --- | --- |",
                *table_rows,
                "",
                "Leads not pursued: none",
                "",
            ]
        )
        log_path = state["config"]["audit"]["log_path"]
        path = log_path if os.path.isabs(log_path) else os.path.join(self.target, log_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        needs_gap = os.path.exists(path) and os.path.getsize(path) > 0
        with open(path, "a", encoding="utf-8") as handle:
            if needs_gap:
                handle.write("\n")
            handle.write(record)
        synopsis_result = subprocess.run(
            [sys.executable, AUDIT_SYNOPSIS, "--write", self.target],
            cwd=self.target,
            capture_output=True,
            text=True,
        )
        if synopsis_result.returncode:
            raise AssertionError(
                f"audit synopsis fixture failed\nstdout: {synopsis_result.stdout}"
                f"stderr: {synopsis_result.stderr}"
            )
        # Warden owns and commits the append in a real run. Keep the fixture's
        # worktree equally clean so retirement tests exercise controller state,
        # not an untracked stand-in log.
        synopsis_path = os.path.join(os.path.dirname(log_path), "AUDIT_SYNOPSIS.md")
        self.git("add", "--", log_path, synopsis_path)
        self.git("commit", "-q", "-m", "fixture audit record")

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
if args and args[0] == "rev-parse" and "--show-toplevel" not in args:
    if mode == "missing-commit":
        raise SystemExit(2)
    ref = args[-1].removesuffix("^{{commit}}")
    refs = json.loads(os.environ.get("FAKE_GIT_REFS", "{{}}"))
    print(refs.get(ref, ref if re.fullmatch(r"[0-9a-f]{{40}}", ref) else hashlib.sha1(ref.encode()).hexdigest()))
elif args[:3] == ["remote", "get-url", "origin"]:
    print(os.environ.get("FAKE_GIT_ORIGIN", "https://github.com/wildcat-finance/example.git"))
elif args and args[0] == "ls-remote":
    ref = args[-1]
    branch = ref.removeprefix("refs/heads/")
    refs = json.loads(os.environ.get("FAKE_GIT_REFS", "{{}}"))
    tip = refs.get(branch, hashlib.sha1(branch.encode()).hexdigest())
    if mode == "remote-absent":
        pass
    elif mode == "remote-malformed":
        print(f"not-a-sha\\t{{ref}}")
    elif mode == "remote-duplicate":
        print(f"{{tip}}\\t{{ref}}")
        print(f"{{tip}}\\t{{ref}}")
    else:
        print(f"{{tip}}\\t{{ref}}")
elif args and args[0] == "merge-base":
    raise SystemExit(0)
elif args and args[0] == "ls-tree":
    if mode == "baseline-unavailable":
        raise SystemExit(3)
    if "FAKE_GIT_BASELINE_HEX" not in os.environ:
        raise SystemExit(0)
    path = args[-1]
    object_id = "a" * 40
    tree_mode = "120000" if mode == "baseline-unsafe" else "100644"
    entry = tree_mode + " blob " + object_id + "\\t" + path + "\\0"
    sys.stdout.buffer.write(entry.encode())
    if mode == "baseline-ambiguous":
        sys.stdout.buffer.write(entry.encode())
elif args[:2] == ["cat-file", "-s"]:
    if mode == "baseline-unavailable":
        raise SystemExit(3)
    if mode == "baseline-malformed-size":
        print("not-a-size")
    elif mode == "baseline-oversized":
        print(2 * 1024 * 1024 + 1)
    else:
        print(len(bytes.fromhex(os.environ.get("FAKE_GIT_BASELINE_HEX", ""))))
elif args[:2] == ["cat-file", "blob"]:
    if mode == "baseline-unavailable":
        raise SystemExit(3)
    baseline = bytes.fromhex(os.environ.get("FAKE_GIT_BASELINE_HEX", ""))
    if mode == "baseline-short-read" and baseline:
        baseline = baseline[:-1]
    sys.stdout.buffer.write(baseline)
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
    if "--format=%P" in args:
        parents = json.loads(os.environ.get("FAKE_GIT_PARENTS", "{{}}"))
        print(" ".join(parents.get(args[-1], [])))
    elif mode == "missing-trailer":
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
    if mode == "pr-head-mismatch":
        payload["headRefOid"] = "9" * 40
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
        path = os.path.join(self.target, name)
        os.makedirs(os.path.dirname(path) or self.target, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return name

    def write_run_pr(self, carried="- nothing outstanding\n"):
        """The run-level pull request body the integrate receipt reads."""
        body = "Run body.\n"
        if carried is not None:
            body += "\n## Carried forward\n\n" + carried
        return self.write(os.path.join(".hexaemeron", "run-pr.md"), body)

    def init(self, topic="test topic", task_issue=None):
        args = ["init", "--topic", topic]
        if task_issue is not None:
            args += ["--task-issue", task_issue]
        self.run_ctl(*args)

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
        path = os.path.join(self.target, ".hexaemeron", "state.json")
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
                self.target,
                command,
                ready,
                release,
            ],
            cwd=self.target,
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

    def to_steps(self, titles=("Scaffold", "Core"), task_issue=None):
        self.init(task_issue=task_issue)
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
        # The repository and the run branch both exist already: the fixture is a
        # real checkout, and `init` cut the run branch when it created the run's
        # worktree. Only the step branches are still this helper's to make.
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "fixture")
        state = self.state()
        for step in state["steps"]:
            self.git("branch", self.step_branch(step["n"], state))

    def to_amendable_steps(self, titles=("Core", "Finish")):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            original = handle.read()
        study = self.write("study.md", original)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n" + "\n".join(
                f"## Step {number}: {title}\n\n**Goal.** {title}.\n"
                for number, title in enumerate(titles, 1)
            ),
        )
        steps = self.write("steps.json", json.dumps(list(titles)))
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        return original

    @staticmethod
    def amendment(
        verdicts=(
            "Step 1: entry holds; exit holds. "
            "Step 2: entry holds; exit holds."
        ),
        *,
        date="2026-08-22",
        what="The fixture assumption was corrected.",
        why="The receipted baseline disproved it.",
        touched="Steps 1 and 2.",
    ):
        return (
            f"\n### Amendment -- {date}\n\n"
            f"**What changed.** {what}\n"
            f"**Why.** {why}\n"
            f"**Steps touched.** {touched}\n"
            f"**Still holding.** {verdicts}\n"
        )

    def git(self, *args, expect=0):
        proc = subprocess.run(
            ["git", *args], cwd=self.target, capture_output=True, text=True
        )
        if proc.returncode != expect:
            raise AssertionError(
                f"git {' '.join(args)} -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        return proc

    def to_audit(self, task_issue=None):
        self.to_steps(task_issue=task_issue)
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
        root = os.path.join(self.target, ".hexaemeron")
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
        self.assertEqual(out["brief"]["target_dir"], os.path.realpath(self.target))
        self.assertEqual(out["brief"]["base_ref"], "main")
        self.assertEqual(
            out["brief"]["output_path"],
            os.path.realpath(os.path.join(self.target, ".hexaemeron", "study.md")),
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
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "base")
        state = self.state()
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
             "audit_log_path", "round", "risk_register", "runbook_step"),
        )
        risk = warden["brief"]["risk_register"]
        self.assertEqual(set(risk), {"markdown", "path", "sha256"})
        self.assertEqual(risk["markdown"],
                         "```risk-register\none | boundary | check\n```\n")
        self.assertEqual(warden["brief"]["runbook_step"], source)

        self.run_ctl("audit-round", "--findings", "0")
        closed = self.next_json()
        self.assertEqual((closed["do"], closed["agent"], closed["brief"]),
                         ("close-audit", None, {}))
        self.run_ctl("done", "audit")
        scribe = self.next_json()
        self.assert_packet(
            scribe, "scribe", ("files", "pr_base", "pr_draft_path", "plugin_root")
        )
        self.assertEqual(
            scribe["brief"]["files"],
            ["audit/AUDIT.md", "audit/AUDIT_SYNOPSIS.md"],
        )
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

    def test_amend_study_command_is_registered(self):
        self.to_steps(("Core",))
        parser = hexctl_module().build_parser()
        args = parser.parse_args(
            ["--dir", self.dir, "amend", "study", "--artifact", "study.md"]
        )
        self.assertEqual(args.fn.__name__, "cmd_amend_study")

    def test_amend_study_replaces_the_digest_refusal_before_next(self):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            original = handle.read()
        study = self.write("study.md", original)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            "## Step 1: Core\n\n**Goal.** Core.\n\n"
            "## Step 2: Finish\n\n**Goal.** Finish.\n",
        )
        steps = self.write("steps.json", '["Core", "Finish"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        amendment = (
            "\n### Amendment -- 2026-08-22\n\n"
            "**What changed.** The fixture assumption was corrected.\n"
            "**Why.** The receipted baseline disproved it.\n"
            "**Steps touched.** Steps 1 and 2.\n"
            "**Still holding.** Step 1: entry holds; exit holds. "
            "Step 2: entry holds; exit holds.\n"
        )
        candidate = self.write("candidate.md", original + amendment)
        self.write("study.md", original + amendment)

        refused = self.run_ctl("next", expect=2)
        self.assertIn("study artefact digest changed", refused.stderr)

        self.run_ctl("amend", "study", "--artifact", candidate)
        packet = self.next_json()
        self.assertEqual((packet["do"], packet["agent"]), ("implement", "mason"))

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
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"].pop("sha256")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        out = self.next_json()
        self.assertEqual((out["agent"], out["brief"]), (None, {}))

    def test_missing_receipted_source_refuses(self):
        self.to_steps(("Core",))
        os.unlink(os.path.join(self.target, "runbook.md"))
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
        self.assertEqual(
            self.next_json()["brief"]["files"],
            [
                "alpha.md",
                "audit/AUDIT.md",
                "audit/AUDIT_SYNOPSIS.md",
                "zeta.md",
            ],
        )

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


class TestStudyAmendments(HexctlCase):
    def test_temporary_git_repositories_demonstrate_holding_and_broken_runs(self):
        original = self.to_amendable_steps()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "tests@example.com")
        self.git("config", "user.name", "Hexctl Tests")
        self.git("add", "study.md", "runbook.md", "steps.json")
        self.git("commit", "-m", "temporary holding run")
        candidate_text = original + self.amendment()
        candidate = self.write("candidate.md", candidate_text)
        self.run_ctl("amend", "study", "--artifact", candidate)
        state = self.state()
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger_path, encoding="utf-8") as handle:
            ledger = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(state["receipts"]["study"]["sha256"],
                         hashlib.sha256(candidate_text.encode()).hexdigest())
        self.assertEqual(ledger[-1]["event"], "amend:study")
        self.assertEqual((self.next_json()["do"], self.next_json()["agent"]),
                         ("implement", "mason"))

        broken = HexctlCase(methodName="runTest")
        broken.setUp()
        try:
            original = broken.to_amendable_steps()
            broken.git("init", "-b", "main")
            broken.git("config", "user.email", "tests@example.com")
            broken.git("config", "user.name", "Hexctl Tests")
            broken.git("add", "study.md", "runbook.md", "steps.json")
            broken.git("commit", "-m", "temporary broken run")
            candidate = broken.write(
                "candidate.md",
                original + broken.amendment(
                    "Step 1: entry holds; exit broken. "
                    "Step 2: entry holds; exit holds."
                ),
            )
            broken.run_ctl("amend", "study", "--artifact", candidate)
            directive = broken.next_json()
            self.assertEqual((directive["do"], directive["agent"], directive["brief"]),
                             ("blocked", None, {}))
            self.assertIn("exit broken", directive["reason"])
        finally:
            broken.tearDown()

    def test_valid_append_records_digest_history_and_reconstructs_the_packet(self):
        original = self.to_amendable_steps()
        prior = hashlib.sha256(original.encode()).hexdigest()
        candidate_text = original + self.amendment()
        candidate = self.write("candidate.md", candidate_text)

        result = self.run_ctl("amend", "study", "--artifact", candidate)
        state = self.state()
        receipt = state["receipts"]["study"]
        amendment = receipt["amendments"][0]
        new = hashlib.sha256(candidate_text.encode()).hexdigest()
        suffix = candidate_text[len(original):].encode()

        self.assertEqual(receipt["sha256"], new)
        self.assertEqual(amendment["prior_sha256"], prior)
        self.assertEqual(amendment["new_sha256"], new)
        self.assertEqual(amendment["amendment_sha256"], hashlib.sha256(suffix).hexdigest())
        self.assertEqual(amendment["steps_touched"], [1, 2])
        self.assertEqual(
            amendment["step_verdicts"],
            [
                {"step": 1, "entry": "holds", "exit": "holds"},
                {"step": 2, "entry": "holds", "exit": "holds"},
            ],
        )
        self.assertIn(prior, result.stdout)
        self.assertIn(new, result.stdout)
        with open(os.path.join(self.target, "study.md"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), candidate_text)
        with open(os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), encoding="utf-8") as handle:
            ledger = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(ledger[-1]["event"], "amend:study")
        self.assertEqual(ledger[-1]["data"], amendment)
        first = self.next_json()
        second = self.next_json()
        self.assertEqual(first, second)
        self.assertEqual((first["do"], first["agent"]), ("implement", "mason"))

    def test_broken_current_step_is_recorded_and_durably_blocks_work(self):
        original = self.to_amendable_steps()
        candidate = self.write(
            "candidate.md",
            original + self.amendment(
                "Step 1: entry broken; exit holds. "
                "Step 2: entry holds; exit holds."
            ),
        )
        result = self.run_ctl("amend", "study", "--artifact", candidate)
        self.assertIn("dependent work is blocked", result.stdout)
        blocked = self.next_json()
        self.assertEqual((blocked["do"], blocked["agent"], blocked["brief"]),
                         ("blocked", None, {}))
        self.assertRegex(blocked["amendment_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("runbook-repair transition", blocked["recovery"])
        proc = self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc", expect=2,
        )
        self.assertIn("study amendment blocks step 1", proc.stderr)
        self.assertIn("BLOCKED:", self.run_ctl("status").stdout)
        self.run_ctl("verify")

    def test_prefix_drift_refuses_without_mutating_any_durable_record(self):
        original = self.to_amendable_steps()
        state_before = self.state()
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger_path, "rb") as handle:
            ledger_before = handle.read()
        candidate = self.write("candidate.md", "changed\n" + original + self.amendment())
        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("exact prefix", proc.stderr)
        self.assertEqual(self.state(), state_before)
        with open(ledger_path, "rb") as handle:
            self.assertEqual(handle.read(), ledger_before)
        with open(os.path.join(self.target, "study.md"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), original)

    def test_date_and_four_field_shape_are_exact(self):
        cases = {
            "invalid date": (self.amendment(date="2026-02-30"), "invalid calendar date"),
            "missing field": (
                self.amendment().replace(
                    "**Why.** The receipted baseline disproved it.\n", ""
                ),
                "field 'Why' must occur exactly once",
            ),
            "duplicate field": (
                self.amendment().replace(
                    "**Why.** The receipted baseline disproved it.\n",
                    "**Why.** First.\n**Why.** Second.\n",
                ),
                "field 'Why' must occur exactly once",
            ),
            "empty field": (
                self.amendment(what=""), "field 'What changed' must not be empty"
            ),
            "wrong order": (
                self.amendment().replace(
                    "**What changed.** The fixture assumption was corrected.\n"
                    "**Why.** The receipted baseline disproved it.\n",
                    "**Why.** The receipted baseline disproved it.\n"
                    "**What changed.** The fixture assumption was corrected.\n",
                ),
                "accepted four-field order",
            ),
        }
        for label, (suffix, message) in cases.items():
            with self.subTest(label=label):
                other = HexctlCase(methodName="runTest")
                other.setUp()
                try:
                    original = other.to_amendable_steps()
                    candidate = other.write("candidate.md", original + suffix)
                    proc = other.run_ctl(
                        "amend", "study", "--artifact", candidate, expect=2
                    )
                    self.assertIn(message, proc.stderr)
                finally:
                    other.tearDown()

    def test_every_unbuilt_step_gets_one_unambiguous_entry_and_exit_verdict(self):
        cases = {
            "missing": ("Step 1: entry holds; exit holds.", "missing verdict(s)"),
            "duplicate": (
                "Step 1: entry holds; exit holds. "
                "Step 1: entry holds; exit holds. "
                "Step 2: entry holds; exit holds.",
                "duplicate step verdict",
            ),
            "ambiguous": (
                "Step 1 probably holds. Step 2 should hold.", "only unambiguous"
            ),
            "unknown": (
                "Step 1: entry holds; exit holds. "
                "Step 2: entry holds; exit holds. "
                "Step 3: entry holds; exit holds.",
                "completed or unknown step",
            ),
        }
        for label, (verdicts, message) in cases.items():
            with self.subTest(label=label):
                other = HexctlCase(methodName="runTest")
                other.setUp()
                try:
                    original = other.to_amendable_steps()
                    candidate = other.write(
                        "candidate.md", original + other.amendment(verdicts)
                    )
                    proc = other.run_ctl(
                        "amend", "study", "--artifact", candidate, expect=2
                    )
                    self.assertIn(message, proc.stderr)
                finally:
                    other.tearDown()

    def test_completed_step_cannot_be_touched_or_given_a_new_verdict(self):
        original = self.to_amendable_steps()
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["steps"][0]["status"] = "done"
        state["steps"][0]["phase"] = "push"
        state["steps"][1]["status"] = "open"
        state["steps"][1]["phase"] = "implement"
        state["current_step"] = 2
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        candidate = self.write("candidate.md", original + self.amendment())
        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("cannot rewrite completed step(s): [1]", proc.stderr)

    def test_wrong_phase_and_legacy_unbound_receipt_refuse(self):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            original = handle.read()
        study = self.write("study.md", original)
        self.run_ctl("done", "study", "--artifact", study)
        candidate = self.write("candidate.md", original + self.amendment())
        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("only while build steps are active", proc.stderr)

        other = HexctlCase(methodName="runTest")
        other.setUp()
        try:
            original = other.to_amendable_steps()
            state_path = os.path.join(other.target, ".hexaemeron", "state.json")
            with open(state_path, encoding="utf-8") as handle:
                state = json.load(handle)
            state["receipts"]["study"].pop("sha256")
            with open(state_path, "w", encoding="utf-8") as handle:
                json.dump(state, handle)
            candidate = other.write("candidate.md", original + other.amendment())
            proc = other.run_ctl(
                "amend", "study", "--artifact", candidate, expect=2
            )
            self.assertIn("source-bound study receipt", proc.stderr)
        finally:
            other.tearDown()

    def test_candidate_path_and_size_bounds_refuse(self):
        original = self.to_amendable_steps()
        outside = tempfile.NamedTemporaryFile("w", delete=False)
        try:
            outside.write(original + self.amendment())
            outside.close()
            proc = self.run_ctl(
                "amend", "study", "--artifact", outside.name, expect=2
            )
            self.assertIn("escapes target directory", proc.stderr)
        finally:
            os.unlink(outside.name)

        large = self.write(
            "large.md", original + self.amendment() + "x" * (2 * 1024 * 1024)
        )
        proc = self.run_ctl("amend", "study", "--artifact", large, expect=2)
        self.assertIn("exceeds 2097152-byte cap", proc.stderr)

    def test_complete_candidate_must_pass_the_bundled_protasis_checker(self):
        self.to_steps(("Core", "Finish"))
        with open(os.path.join(self.target, "study.md"), encoding="utf-8") as handle:
            original = handle.read()
        candidate = self.write("candidate.md", original + self.amendment())
        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("Protasis rejected the amendment candidate", proc.stderr)
        self.assertNotIn("S001", proc.stderr)

    def test_live_controller_writer_blocks_amendment_mutation(self):
        original = self.to_amendable_steps()
        candidate = self.write("candidate.md", original + self.amendment())
        holder, _, release = self.start_lock_holder(command="cmd_record")
        try:
            proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=1)
            self.assertIn("another hexctl is holding this run", proc.stderr)
        finally:
            self.release_lock_holder(holder, release)

    def test_fenced_decoy_is_ignored_but_duplicate_block_and_trailing_section_refuse(self):
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            fixture = handle.read()
        decoy = fixture.replace(
            "## 1. Problem statement",
            "```markdown\n### Amendment -- 2026-01-01\n```\n\n"
            "## 1. Problem statement",
        )
        self.init()
        study = self.write("study.md", decoy)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md", "## Step 1: Core\n\n**Goal.** Core.\n"
            "## Step 2: Finish\n\n**Goal.** Finish.\n"
        )
        steps = self.write("steps.json", '["Core", "Finish"]')
        self.run_ctl("done", "runbook", "--artifact", runbook, "--steps-file", steps)
        candidate = self.write("candidate.md", decoy + self.amendment())
        self.run_ctl("amend", "study", "--artifact", candidate)

        for label, suffix, message in (
            ("duplicate", self.amendment() + self.amendment(), "more than one"),
            ("trailing", self.amendment() + "\n## Notes\n\nLater.\n", "final section"),
        ):
            with self.subTest(label=label):
                other = HexctlCase(methodName="runTest")
                other.setUp()
                try:
                    original = other.to_amendable_steps()
                    candidate = other.write("candidate.md", original + suffix)
                    proc = other.run_ctl(
                        "amend", "study", "--artifact", candidate, expect=2
                    )
                    self.assertIn(message, proc.stderr)
                finally:
                    other.tearDown()

    def test_short_fence_cannot_expose_an_amendment_heading_inside_a_long_fence(self):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            original = handle.read() + "\n````markdown\n```\n"
        study = self.write("study.md", original)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            "## Step 1: Core\n\n**Goal.** Core.\n\n"
            "## Step 2: Finish\n\n**Goal.** Finish.\n",
        )
        steps = self.write("steps.json", '["Core", "Finish"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        candidate = self.write("candidate.md", original + self.amendment())

        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("exact prefix", proc.stderr)

    def test_interrupted_replacement_is_durable_pending_work_and_recovers(self):
        original = self.to_amendable_steps()
        candidate_text = original + self.amendment()
        candidate = self.write("candidate.md", candidate_text)
        candidate_path = os.path.join(self.target, candidate)
        module = hexctl_module()

        with mock.patch.object(
            module,
            "commit",
            side_effect=KeyboardInterrupt(
                "simulated interruption after artefact replacement"
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                module.cmd_amend_study(
                    argparse.Namespace(dir=self.target, artifact=candidate_path)
                )

        with open(os.path.join(self.target, "study.md"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), candidate_text)
        pending = os.path.join(
            self.target, ".hexaemeron", "study-amendment-pending.json"
        )
        self.assertTrue(os.path.isfile(pending))
        refused = self.run_ctl("verify", expect=2)
        self.assertIn("study amendment transaction is pending", refused.stderr)

        recovered = self.run_ctl(
            "amend", "study", "--artifact", os.path.join(self.target, "study.md")
        )
        self.assertIn("recovered", recovered.stdout)
        self.assertFalse(os.path.exists(pending))
        self.run_ctl("verify")
        self.assertEqual(
            self.state()["receipts"]["study"]["sha256"],
            hashlib.sha256(candidate_text.encode()).hexdigest(),
        )

    def test_recovery_completes_a_written_ledger_event_without_duplicating_it(self):
        original = self.to_amendable_steps()
        candidate_text = original + self.amendment()
        candidate = self.write("candidate.md", candidate_text)
        module = hexctl_module()

        with mock.patch.object(
            module,
            "save_state",
            side_effect=OSError("simulated interruption before state replacement"),
        ):
            with self.assertRaises(OSError):
                module.cmd_amend_study(
                    argparse.Namespace(
                        dir=self.target,
                        artifact=os.path.join(self.target, candidate),
                    )
                )

        recovered = self.run_ctl(
            "amend", "study", "--artifact", os.path.join(self.target, "study.md")
        )
        self.assertIn("recovered", recovered.stdout)
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            events = [json.loads(line)["event"] for line in handle if line.strip()]
        self.assertEqual(events.count("amend:study"), 1)
        self.run_ctl("verify")

    def test_same_path_candidate_and_multiple_holding_amendments_are_supported(self):
        original = self.to_amendable_steps()
        first_text = original + self.amendment()
        self.write("study.md", first_text)
        self.run_ctl("amend", "study", "--artifact", "study.md")
        second_text = first_text + self.amendment(
            date="2026-08-23", what="A second baseline fact changed."
        )
        second = self.write("second.md", second_text)
        self.run_ctl("amend", "study", "--artifact", second)
        history = self.state()["receipts"]["study"]["amendments"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["prior_sha256"], history[0]["new_sha256"])

    def test_post_amendment_drift_refuses_next_and_verify(self):
        original = self.to_amendable_steps()
        candidate = self.write("candidate.md", original + self.amendment())
        self.run_ctl("amend", "study", "--artifact", candidate)
        self.write("study.md", original + self.amendment() + "drift\n")
        for command in (("next",), ("verify",)):
            with self.subTest(command=command[0]):
                proc = self.run_ctl(*command, expect=2)
                self.assertIn("study artefact digest changed", proc.stderr)


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

    def to_merge_step(self):
        self.to_push()
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )

    def to_integrate(self):
        self.to_merge_step()
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40,
        )
        self.write_run_pr()

    def edit_push_receipt(self, edit):
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        edit(state["steps"][0]["receipts"]["push"])
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)

    def prime_step_merge(self, merge_sha="e" * 40):
        pr = self.fake_prs["https://github.com/wildcat-finance/example/pull/1"]
        pr["state"] = "MERGED"
        pr["mergeCommit"] = {"oid": merge_sha}

    def set_post_push_head(self, head):
        branch = self.step_branch(1)
        self.fake_refs[branch] = head
        self.fake_prs["https://github.com/wildcat-finance/example/pull/1"][
            "headRefOid"
        ] = head

    def test_merge_repairs_legacy_push_receipt_missing_verified_head(self):
        self.to_merge_step()
        self.edit_push_receipt(
            lambda receipt: (
                receipt.pop("github_verified", None),
                receipt.pop("verified_commits", None),
            )
        )
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40,
        )
        repair = self.state()["integrate"]["merges"]["1"]["effective_push"]
        self.assertTrue(repair["repaired"])
        self.assertEqual(repair["head"], "d" * 40)

    def test_merge_repairs_signed_post_push_head(self):
        self.to_merge_step()
        repaired_head = "7" * 40
        self.set_post_push_head(repaired_head)
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40,
        )
        repair = self.state()["integrate"]["merges"]["1"]["effective_push"]
        self.assertTrue(repair["repaired"])
        self.assertEqual(repair["head"], repaired_head)

    def test_merge_time_repair_refuses_invalid_local_signature(self):
        self.to_merge_step()
        self.edit_push_receipt(lambda receipt: receipt.pop("github_verified", None))
        self.prime_step_merge()
        self.env["FAKE_GIT_MODE"] = "unsigned"
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn("valid local signature", proc.stderr)

    def test_merge_time_repair_refuses_invalid_github_verification(self):
        self.to_merge_step()
        self.set_post_push_head("7" * 40)
        self.prime_step_merge()
        self.env["FAKE_GH_MODE"] = "verified-false"
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn("not verified:true", proc.stderr)

    def test_merge_time_repair_refuses_remote_pr_head_mismatch(self):
        self.to_merge_step()
        self.fake_prs["https://github.com/wildcat-finance/example/pull/1"][
            "headRefOid"
        ] = "7" * 40
        self.prime_step_merge()
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn("remote branch tip", proc.stderr)

    def test_merge_time_repair_refuses_pr_topology_mismatch(self):
        self.to_merge_step()
        self.prime_step_merge()
        self.env["FAKE_GH_MODE"] = "pr-mismatch"
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn("topology", proc.stderr)

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

    def test_integrate_pr_head_must_equal_remote_run_branch_tip(self):
        self.to_integrate()
        state = self.state()
        url = "https://github.com/wildcat-finance/example/pull/2"
        self.fake_prs[url] = self.fake_pr(
            url,
            state["run_branch"],
            state["base"],
            self.fake_refs[state["run_branch"]],
            "f" * 40,
        )
        self.env["FAKE_GH_MODE"] = "pr-head-mismatch"
        proc = self.run_ctl(
            "done", "integrate",
            "--pr-url", url,
            "--merge-commit", "f" * 40, expect=2,
        )
        self.assertIn("remote run branch tip", proc.stderr)

    def test_remote_run_branch_tip_requires_one_exact_full_ref(self):
        module = hexctl_module()
        branch = "fiat/run"
        tip = "8" * 40
        base_env = {
            "PATH": self.env["PATH"],
            "FAKE_GIT_REFS": json.dumps({branch: tip}),
        }
        with mock.patch.dict(os.environ, base_env):
            self.assertEqual(module.remote_branch_tip(self.dir, branch), tip)
        for mode in ("remote-absent", "remote-malformed", "remote-duplicate"):
            with self.subTest(mode=mode):
                error = StringIO()
                with mock.patch.dict(
                    os.environ, {**base_env, "FAKE_GIT_MODE": mode}
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.remote_branch_tip(self.dir, branch)
                self.assertIn("remote run branch tip", error.getvalue())

    def test_integrate_remote_tip_must_equal_final_recorded_step_merge(self):
        self.to_integrate()
        state = self.state()
        url = "https://github.com/wildcat-finance/example/pull/2"
        divergent_tip = "8" * 40
        self.fake_refs[state["run_branch"]] = divergent_tip
        self.fake_prs[url] = self.fake_pr(
            url,
            state["run_branch"],
            state["base"],
            divergent_tip,
            "f" * 40,
        )
        proc = self.run_ctl(
            "done", "integrate", "--pr-url", url,
            "--merge-commit", "f" * 40, expect=2,
        )
        self.assertIn("final recorded step merge", proc.stderr)

    def prepare_run_sync(self, sync_sha="7" * 40, base_sha="6" * 40):
        self.to_integrate()
        state = self.state()
        final_merge = state["integrate"]["merges"]["1"]["merge_commit"]
        self.fake_refs[state["run_branch"]] = sync_sha
        self.fake_refs[state["base"]] = base_sha
        self.fake_parents[sync_sha] = [final_merge, base_sha]
        return state, sync_sha, base_sha

    def test_sync_run_receipts_exact_merge_and_allows_integration(self):
        state, sync_sha, base_sha = self.prepare_run_sync()
        self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha,
        )
        self.write_run_pr()
        self.run_ctl(
            "done", "integrate",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
        )
        receipt = self.state()["receipts"]["integrate"]
        self.assertEqual(receipt["run_head"], sync_sha)
        self.assertEqual(receipt["sync"]["base_head"], base_sha)
        self.assertEqual(receipt["sync"]["parents"], ["e" * 40, base_sha])

    def test_sync_run_refuses_wrong_merge_parents(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        self.fake_parents[sync_sha] = ["9" * 40, base_sha]
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, expect=2,
        )
        self.assertIn("merge parents", proc.stderr)

    def test_sync_run_refuses_unsigned_commit(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        self.env["FAKE_GIT_MODE"] = "unsigned"
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, expect=2,
        )
        self.assertIn("valid local signature", proc.stderr)

    def test_sync_run_refuses_stale_remote_base(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", "5" * 40, expect=2,
        )
        self.assertIn("remote base branch tip", proc.stderr)

    def test_sync_run_refuses_invalid_github_verification(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        self.env["FAKE_GH_MODE"] = "verified-false"
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, expect=2,
        )
        self.assertIn("not verified:true", proc.stderr)


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
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "fixture")
        state = self.state()
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
        self.assertFalse(
            state["integrate"]["merges"]["1"]["effective_push"]["repaired"]
        )
        self.assertEqual(
            state["receipts"]["integrate"]["github_verified"], ["f" * 40]
        )
        self.assertEqual(state["receipts"]["integrate"]["run_head"], "e" * 40)
        self.assertEqual(
            state["receipts"]["integrate"]["final_step_merge"], "e" * 40
        )
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
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
        # `git worktree add ../<name> main` was the old advice and it fails
        # whenever the base is already checked out, which is the ordinary case.
        self.assertNotIn("git worktree add", result.stderr)
        self.assertIn("hexctl --dir <checkout> init --topic", result.stderr)
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
        path = os.path.join(self.target, ".hexaemeron", "lock")
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
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
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
                     "--fixes-commit", "beef01",
                     "--elenchus-verdict", "guarded")
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_no_further_leads_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl(
            "audit-round", "--findings", "1", "--fixes-commit", "b1",
            "--elenchus-verdict", "guarded",
        )
        proc = self.run_ctl("done", "audit", "--no-further-leads", expect=2)
        self.assertIn("--reason", proc.stderr)
        self.run_ctl("done", "audit", "--no-further-leads",
                     "--reason", "remaining lead is a gas nit, out of scope")

    def test_max_rounds_forces_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("config", "set", "audit.max_rounds", "2")
        self.run_ctl(
            "audit-round", "--findings", "2", "--fixes-commit", "b1",
            "--elenchus-verdict", "guarded",
        )
        self.run_ctl(
            "audit-round", "--findings", "1", "--fixes-commit", "b2",
            "--elenchus-verdict", "guarded",
        )
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn("max audit rounds", proc.stderr)
        out = self.next_json()
        self.assertEqual(out["do"], "audit-verdict")
        self.assertEqual(out["open_findings"], 1)


class ElenchusVerdictReceiptTests(HexctlCase):
    VERDICTS = ("guarded", "unguarded", "passed", "inconclusive")

    def to_receiptable_audit(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)

    def state_ledger_digests(self):
        paths = (
            os.path.join(self.target, ".hexaemeron", "state.json"),
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
        )
        digests = []
        for path in paths:
            with open(path, "rb") as handle:
                digests.append(hashlib.sha256(handle.read()).hexdigest())
        return tuple(digests)

    def audit_events(self):
        path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        entries = []
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry["event"] == "audit-round":
                    entries.append(entry)
        return entries

    def make_last_round_legacy(self):
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        new_leaves = (
            "schema", "record_timestamp", "entry_sha256", "log_end_offset",
            "synopsis_sha256", "elenchus_verdict",
        )
        for leaf in new_leaves:
            state["steps"][0]["audit"]["rounds"][-1].pop(leaf, None)
        canonical_state = json.dumps(state, sort_keys=True, separators=(",", ":"))
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")

        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(entries[-1]["event"], "audit-round")
        for leaf in new_leaves:
            entries[-1]["data"].pop(leaf, None)
        entries[-1]["state"] = hashlib.sha256(canonical_state.encode()).hexdigest()
        unsigned = {key: value for key, value in entries[-1].items() if key != "hash"}
        entries[-1]["hash"] = hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")

    def test_the_closed_enum_records_state_ledger_and_stdout(self):
        self.to_receiptable_audit()
        for index, verdict in enumerate(self.VERDICTS, 1):
            with self.subTest(verdict=verdict):
                result = self.run_ctl(
                    "audit-round", "--findings", "1",
                    "--fixes-commit", f"fix-{index}",
                    "--elenchus-verdict", verdict,
                )
                self.assertIn(f"Elenchus {verdict}", result.stdout)

        rounds = self.state()["steps"][0]["audit"]["rounds"]
        self.assertEqual(
            [round_entry["elenchus_verdict"] for round_entry in rounds],
            list(self.VERDICTS),
        )
        self.assertEqual(
            [entry["data"]["elenchus_verdict"] for entry in self.audit_events()],
            list(self.VERDICTS),
        )

    def test_a_fix_without_a_verdict_is_refused_without_drift(self):
        self.to_receiptable_audit()
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "audit-round", "--findings", "1", "--fixes-commit", "fix-1",
            expect=2,
        )
        self.assertIn("--elenchus-verdict", result.stderr)
        for verdict in self.VERDICTS:
            self.assertIn(verdict, result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def test_an_unknown_verdict_is_refused_without_drift(self):
        self.to_receiptable_audit()
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "audit-round", "--findings", "1", "--fixes-commit", "fix-1",
            "--elenchus-verdict", "unknown", expect=2,
        )
        self.assertIn("--elenchus-verdict", result.stderr)
        for verdict in self.VERDICTS:
            self.assertIn(verdict, result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def test_a_verdict_without_a_fix_is_refused_without_drift(self):
        self.to_receiptable_audit()
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "audit-round", "--findings", "1",
            "--elenchus-verdict", "guarded", expect=2,
        )
        self.assertIn("--elenchus-verdict requires --fixes-commit", result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def test_a_no_fix_round_records_an_explicit_null(self):
        self.to_receiptable_audit()
        result = self.run_ctl("audit-round", "--findings", "0")
        self.assertIn("Elenchus null", result.stdout)
        round_entry = self.state()["steps"][0]["audit"]["rounds"][0]
        self.assertIn("elenchus_verdict", round_entry)
        self.assertIsNone(round_entry["elenchus_verdict"])
        event = self.audit_events()[0]
        self.assertIn("elenchus_verdict", event["data"])
        self.assertIsNone(event["data"]["elenchus_verdict"])

    def test_next_names_the_conditional_obligation_and_exact_values(self):
        self.to_receiptable_audit()
        expected = {
            "flag": "--elenchus-verdict",
            "required_with": "--fixes-commit",
            "choices": list(self.VERDICTS),
        }
        self.assertEqual(self.next_json()["elenchus_verdict"], expected)
        self.run_ctl("audit-round", "--findings", "1")
        self.assertEqual(self.next_json()["elenchus_verdict"], expected)

    def test_warden_reconstructs_the_exact_mason_runbook_step(self):
        self.to_steps(("Core",))
        mason_first = self.next_json()
        mason_second = self.next_json()
        self.assertEqual(mason_first, mason_second)
        self.assertEqual(
            set(mason_first["brief"]),
            {"runbook_step", "branch", "branch_from"},
        )
        expected_markdown = "## Step 1: Core\n\n**Goal.** Ship Core.\n"
        expected_source = {
            "markdown": expected_markdown,
            "path": os.path.realpath(os.path.join(self.target, "runbook.md")),
            "sha256": hashlib.sha256(
                ("# Runbook\n\n" + expected_markdown).encode()
            ).hexdigest(),
            "number": 1,
            "title": "Core",
        }
        self.assertEqual(mason_first["brief"]["runbook_step"], expected_source)

        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.run_ctl("record", "security_suite", SUITE)
        warden_first = self.next_json()
        warden_second = self.next_json()
        self.assertEqual(warden_first, warden_second)
        self.assertEqual(
            warden_first["brief"]["runbook_step"],
            mason_first["brief"]["runbook_step"],
        )
        self.assertEqual(
            set(warden_first["brief"]),
            {
                "step_branch", "stacked_branch", "security_suite", "plugin_root",
                "audit_log_path", "round", "risk_register", "runbook_step",
            },
        )

    def test_a_legacy_absent_key_survives_every_reader_and_later_round(self):
        self.to_receiptable_audit()
        self.run_ctl("audit-round", "--findings", "1")
        self.make_last_round_legacy()
        self.env["FAKE_GIT_BASELINE_HEX"] = Path(
            os.path.join(self.target, "audit", "AUDIT.md")
        ).read_bytes().hex()

        self.run_ctl("status")
        directive = self.next_json()
        self.assertEqual(directive["do"], "audit-round")
        self.run_ctl("verify")

        self.run_ctl(
            "audit-round", "--findings", "0", "--fixes-commit", "legacy-fix",
            "--elenchus-verdict", "passed",
        )
        self.run_ctl("done", "audit")
        self.run_ctl("verify")
        rounds = self.state()["steps"][0]["audit"]["rounds"]
        self.assertNotIn("elenchus_verdict", rounds[0])
        self.assertEqual(rounds[1]["elenchus_verdict"], "passed")
        self.assertEqual(self.state()["steps"][0]["phase"], "prose")


class AuditRecordSchemaTests(HexctlCase):
    """The receipt checks Warden's final append before durable mutation."""

    def setUp(self):
        super().setUp()
        self.auto_audit_records = False
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)

    def run_ctl(self, *args, expect=0):
        if args[:1] == ("audit-round",) and expect == 0:
            synopsis = subprocess.run(
                [sys.executable, AUDIT_SYNOPSIS, "--write", self.target],
                cwd=self.target,
                capture_output=True,
                text=True,
            )
            if synopsis.returncode:
                raise AssertionError(
                    f"audit synopsis fixture failed\nstdout: {synopsis.stdout}"
                    f"stderr: {synopsis.stderr}"
                )
        return super().run_ctl(*args, expect=expect)

    def state_ledger_digests(self):
        return tuple(
            hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in (
                os.path.join(self.target, ".hexaemeron", "state.json"),
                os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            )
        )

    def log_path(self):
        return os.path.join(self.target, "audit", "AUDIT.md")

    def record_lines(
        self,
        findings=0,
        verdict="null",
        *,
        timestamp="2026-08-23T02:17:46Z",
        covered="packet-state-drift=reviewed",
        omit=(),
        table_rows=None,
        extra=(),
    ):
        state = self.state()
        round_number = len(state["steps"][0]["audit"]["rounds"]) + 1
        rows = table_rows
        if rows is None:
            rows = (
                ["| -- | -- | -- | none | -- |"]
                if findings == 0
                else [
                    f"| F-{index:02d} | low | fixture.py | finding {index} | open |"
                    for index in range(1, findings + 1)
                ]
            )
        blocks = {
            "heading": [
                f"## {state['topic']}, step 1, round {round_number} -- {timestamp}"
            ],
            "schema": ["Audit schema: fiat-audit-round/v1"],
            "covered": [f"Covered: {covered}"],
            "not_checked": ["Not checked: none"],
            "verdict": [f"Elenchus verdict: {verdict}"],
            "table": [
                "| id | severity | file | finding | status |",
                "| --- | --- | --- | --- | --- |",
                *rows,
            ],
            "leads": ["Leads not pursued: none"],
        }
        lines = []
        for name in (
            "heading", "schema", "covered", "not_checked", "verdict", "table", "leads"
        ):
            if name not in omit:
                lines.extend(blocks[name])
                lines.append("")
        lines.extend(extra)
        return lines

    def write_record(self, *args, append=False, **kwargs):
        path = self.log_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        record = "\n".join(self.record_lines(*args, **kwargs)).encode()
        prefix = Path(path).read_bytes() if append and os.path.exists(path) else b""
        separator = b""
        if prefix:
            separator = b"\n" if prefix.endswith(b"\n") else b"\n\n"
        Path(path).write_bytes(prefix + separator + record)
        return path

    def set_fake_baseline(self, data):
        self.env["FAKE_GIT_BASELINE_HEX"] = data.hex()

    def rewrite_latest_round(self, **changes):
        state_path = Path(self.target, ".hexaemeron", "state.json")
        ledger_path = Path(self.target, ".hexaemeron", "ledger.jsonl")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        latest = state["steps"][0]["audit"]["rounds"][-1]
        for key, value in changes.items():
            if value is ...:
                latest.pop(key, None)
            else:
                latest[key] = value
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        entries = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        self.assertEqual(entries[-1]["event"], "audit-round")
        for key, value in changes.items():
            if value is ...:
                entries[-1]["data"].pop(key, None)
            else:
                entries[-1]["data"][key] = value
        entries[-1]["state"] = hashlib.sha256(
            json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        unsigned = {key: value for key, value in entries[-1].items() if key != "hash"}
        entries[-1]["hash"] = hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        ledger_path.write_text(
            "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries),
            encoding="utf-8",
        )

    def refuse(self, fragment, *args):
        before = self.state_ledger_digests()
        result = self.run_ctl("audit-round", *args, expect=2)
        self.assertIn(fragment, result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def write_synopsis(self):
        result = subprocess.run(
            [sys.executable, AUDIT_SYNOPSIS, "--write", self.target],
            cwd=self.target,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(
                f"audit synopsis fixture failed\nstdout: {result.stdout}"
                f"stderr: {result.stderr}"
            )
        return Path(self.log_path()).with_name("AUDIT_SYNOPSIS.md")

    def call_with_renderer(self, controller, renderer, stderr):
        class Loader:
            @staticmethod
            def exec_module(_module):
                pass

        specification = argparse.Namespace(loader=Loader())
        with (
            mock.patch.object(
                controller, "read_configured_audit_log",
                return_value=("audit/AUDIT.md", b"record"),
            ),
            mock.patch.object(controller, "audit_delta_start", return_value=0),
            mock.patch.object(controller, "audit_record_bytes", return_value=b"record"),
            mock.patch.object(
                controller,
                "parse_audit_record",
                return_value=("fiat-audit-round/v1", "2026-08-23T02:17:46Z"),
            ),
            mock.patch.object(
                controller.importlib.util,
                "spec_from_file_location",
                return_value=specification,
            ),
            mock.patch.object(
                controller.importlib.util, "module_from_spec", return_value=renderer
            ),
            redirect_stderr(stderr),
        ):
            return controller.validated_audit_record(
                self.target,
                {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                {"audit": {"rounds": []}},
                argparse.Namespace(log=None),
            )

    def assert_renderer_refusal(self, call):
        try:
            call()
        except BaseException as error:
            caught = error
        else:
            self.fail("renderer validation did not refuse")
        self.assertIsInstance(caught, SystemExit)
        self.assertEqual(caught.code, 2)

    def test_missing_stale_and_lossy_synopsis_refuse_without_drift(self):
        self.write_record()
        self.refuse("synopsis is missing", "--findings", "0")

        synopsis = self.write_synopsis()
        synopsis.write_bytes(synopsis.read_bytes() + b"stale\n")
        self.refuse("synopsis is stale", "--findings", "0")

        self.write_synopsis()
        text = synopsis.read_text(encoding="utf-8")
        synopsis.write_text(
            text.replace("Leads not pursued: none", "[lead dropped]", 1),
            encoding="utf-8",
        )
        self.refuse("synopsis is stale", "--findings", "0")

    def test_corrupt_renderer_import_is_a_bounded_refusal(self):
        controller = hexctl_module()

        class BrokenLoader:
            @staticmethod
            def exec_module(_module):
                raise RuntimeError("corrupt renderer fixture")

        specification = argparse.Namespace(loader=BrokenLoader())
        stderr = StringIO()
        with (
            mock.patch.object(
                controller, "read_configured_audit_log",
                return_value=("audit/AUDIT.md", b"record"),
            ),
            mock.patch.object(controller, "audit_delta_start", return_value=0),
            mock.patch.object(controller, "audit_record_bytes", return_value=b"record"),
            mock.patch.object(
                controller,
                "parse_audit_record",
                return_value=("fiat-audit-round/v1", "2026-08-23T02:17:46Z"),
            ),
            mock.patch.object(
                controller.importlib.util,
                "spec_from_file_location",
                return_value=specification,
            ),
            mock.patch.object(
                controller.importlib.util, "module_from_spec", return_value=object()
            ),
            redirect_stderr(stderr),
            self.assertRaises(BaseException) as raised,
        ):
            controller.validated_audit_record(
                self.target,
                {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                {"audit": {"rounds": []}},
                argparse.Namespace(log=None),
            )
        self.assertIsInstance(raised.exception, SystemExit)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("audit synopsis renderer cannot be loaded", stderr.getvalue())

    def test_renderer_cannot_terminate_successfully_at_checked_boundaries(self):
        controller = hexctl_module()

        class RendererError(Exception):
            def __str__(self):
                if renderer.stop_during_error_format:
                    raise SystemExit(0)
                return super().__str__()

        class StoppingRenderer:
            SynopsisError = RendererError
            stop_during_interface = False
            stop_during_validation = False
            stop_during_error_format = False

            def __getattribute__(self, name):
                if (
                    name == "validate_committed_synopsis"
                    and object.__getattribute__(self, "stop_during_interface")
                ):
                    raise SystemExit(0)
                return object.__getattribute__(self, name)

            @staticmethod
            def validate_committed_synopsis(*_args):
                if renderer.stop_during_error_format:
                    raise RendererError("renderer refusal")
                if renderer.stop_during_validation:
                    raise SystemExit(0)
                return "a" * 64

        renderer = StoppingRenderer()

        class StoppingLoader:
            stop_during_load = True

            def exec_module(self, _module):
                if self.stop_during_load:
                    raise SystemExit(0)

        loader = StoppingLoader()
        specification = argparse.Namespace(loader=loader)
        for stop_at in (
            "module",
            "load",
            "interface",
            "type-check",
            "validation",
            "error-format",
            "digest-check",
        ):
            with self.subTest(stop_at=stop_at):
                loader.stop_during_load = stop_at == "load"
                renderer.stop_during_interface = stop_at == "interface"
                renderer.stop_during_validation = stop_at == "validation"
                renderer.stop_during_error_format = stop_at == "error-format"
                stderr = StringIO()

                def create_module(_specification):
                    if stop_at == "module":
                        raise SystemExit(0)
                    return renderer

                with ExitStack() as stack:
                    stack.enter_context(mock.patch.object(
                        controller, "read_configured_audit_log",
                        return_value=("audit/AUDIT.md", b"record"),
                    ))
                    stack.enter_context(mock.patch.object(
                        controller, "audit_delta_start", return_value=0
                    ))
                    stack.enter_context(mock.patch.object(
                        controller, "audit_record_bytes", return_value=b"record"
                    ))
                    stack.enter_context(mock.patch.object(
                        controller,
                        "parse_audit_record",
                        return_value=(
                            "fiat-audit-round/v1", "2026-08-23T02:17:46Z"
                        ),
                    ))
                    stack.enter_context(mock.patch.object(
                        controller.importlib.util,
                        "spec_from_file_location",
                        return_value=specification,
                    ))
                    stack.enter_context(mock.patch.object(
                        controller.importlib.util,
                        "module_from_spec",
                        side_effect=create_module,
                    ))
                    if stop_at == "type-check":
                        stack.enter_context(mock.patch.object(
                            controller,
                            "issubclass",
                            side_effect=SystemExit(0),
                            create=True,
                        ))
                    if stop_at == "digest-check":
                        stack.enter_context(mock.patch.object(
                            controller.re, "fullmatch", side_effect=SystemExit(0)
                        ))
                    stack.enter_context(redirect_stderr(stderr))
                    raised = stack.enter_context(self.assertRaises(SystemExit))
                    controller.validated_audit_record(
                        self.target,
                        {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                        {"audit": {"rounds": []}},
                        argparse.Namespace(log=None),
                    )
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("audit synopsis renderer", stderr.getvalue())

    def test_declared_renderer_diagnostics_cannot_break_the_refusal(self):
        controller = hexctl_module()

        class RendererError(Exception):
            pass

        class Renderer:
            SynopsisError = RendererError
            message = "unsafe\nsurrogate: \ud800"

            @classmethod
            def validate_committed_synopsis(cls, *_args):
                raise RendererError(cls.message)

        before = self.state_ledger_digests()
        for message, expected, exact_size in (
            (
                "unsafe\x00\x1b\nsurrogate: \ud800\\",
                b"unsafe\\x00\\x1b\\nsurrogate: \\ud800\\\\",
                None,
            ),
            ("x" * 4_080, b"x" * 4_080, 4_096),
            ("x" * 4_081, b"audit synopsis renderer validation failed", None),
            ("x" * 4_096, b"audit synopsis renderer validation failed", None),
            ("\\" * 2_040, b"\\\\" * 2_040, 4_096),
            ("\\" * 2_041, b"audit synopsis renderer validation failed", None),
            ("x" * 5_000, b"audit synopsis renderer validation failed", None),
        ):
            with self.subTest(message_chars=len(message)):
                Renderer.message = message
                output = BytesIO()
                stderr = TextIOWrapper(output, encoding="ascii", errors="strict")
                try:
                    self.assert_renderer_refusal(lambda:
                        self.call_with_renderer(controller, Renderer(), stderr)
                    )
                    stderr.flush()
                    self.assertIn(expected, output.getvalue())
                    self.assertLessEqual(
                        len(output.getvalue()),
                        controller.AUDIT_RENDERER_DIAGNOSTIC_BYTES_MAX,
                    )
                    if exact_size is not None:
                        self.assertEqual(len(output.getvalue()), exact_size)
                    self.assertEqual(output.getvalue()[-1:], b"\n")
                    self.assertTrue(
                        all(32 <= byte <= 126 for byte in output.getvalue()[:-1])
                    )
                finally:
                    stderr.detach()
        self.assertEqual(self.state_ledger_digests(), before)

    def test_renderer_diagnostic_byte_cap_is_encoding_independent(self):
        controller = hexctl_module()
        for encoding in ("utf-8", "utf-16"):
            with self.subTest(encoding=encoding):
                output = BytesIO()
                stderr = TextIOWrapper(output, encoding=encoding, errors="strict")
                try:
                    with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                        controller.refuse_audit_renderer("x" * 4_080)
                    stderr.flush()
                    self.assertEqual(raised.exception.code, 2)
                    self.assertEqual(
                        len(output.getvalue()),
                        controller.AUDIT_RENDERER_DIAGNOSTIC_BYTES_MAX,
                    )
                finally:
                    stderr.detach()

    def test_renderer_diagnostic_completes_binary_short_writes(self):
        controller = hexctl_module()
        expected = b"hexctl: error: renderer refusal\n"

        class ShortBuffer:
            def __init__(self, limit):
                self.limit = limit
                self.output = bytearray()
                self.flushed = False

            def write(self, value):
                size = min(self.limit, len(value))
                self.output.extend(value[:size])
                return size

            def flush(self):
                self.flushed = True

        for limit in (1, 3, len(expected) - 1):
            with self.subTest(limit=limit):
                stderr = argparse.Namespace(buffer=ShortBuffer(limit))
                with mock.patch.object(controller.sys, "stderr", stderr):
                    with self.assertRaises(SystemExit) as raised:
                        controller.refuse_audit_renderer("renderer refusal")
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(bytes(stderr.buffer.output), expected)
                self.assertTrue(stderr.buffer.flushed)

    def test_renderer_diagnostic_binary_write_boundaries_preserve_exit(self):
        controller = hexctl_module()
        full_write = object()

        class BoundaryBuffer:
            def __init__(
                self, *, result=full_write, write_error=None, flush_error=None
            ):
                self.result = result
                self.write_error = write_error
                self.flush_error = flush_error

            def write(self, value):
                if self.write_error is not None:
                    raise self.write_error
                return len(value) if self.result is full_write else self.result

            def flush(self):
                if self.flush_error is not None:
                    raise self.flush_error

        for result in (None, 0, -1, True, 10_000):
            with self.subTest(result=result):
                stderr = argparse.Namespace(buffer=BoundaryBuffer(result=result))
                with mock.patch.object(controller.sys, "stderr", stderr):
                    with self.assertRaises(SystemExit) as raised:
                        controller.refuse_audit_renderer("renderer refusal")
                self.assertEqual(raised.exception.code, 2)

        for stage in ("write", "flush"):
            for failure in (OSError("diagnostic failure"), SystemExit(0)):
                with self.subTest(stage=stage, failure=type(failure).__name__):
                    stderr = argparse.Namespace(buffer=BoundaryBuffer(**{
                        f"{stage}_error": failure,
                    }))
                    with mock.patch.object(controller.sys, "stderr", stderr):
                        with self.assertRaises(SystemExit) as raised:
                            controller.refuse_audit_renderer("renderer refusal")
                    self.assertEqual(raised.exception.code, 2)

        for stage in ("write", "flush"):
            for failure in (KeyboardInterrupt(), GeneratorExit()):
                with self.subTest(stage=stage, failure=type(failure).__name__):
                    stderr = argparse.Namespace(buffer=BoundaryBuffer(**{
                        f"{stage}_error": failure,
                    }))
                    with mock.patch.object(controller.sys, "stderr", stderr):
                        try:
                            controller.refuse_audit_renderer("renderer refusal")
                        except BaseException as error:
                            caught = error
                        else:
                            self.fail("renderer diagnostic did not terminate")
                    self.assertIs(caught, failure)

        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            controller.refuse_audit_renderer("renderer refusal")
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(stderr.getvalue(), "hexctl: error: renderer refusal\n")

    def test_renderer_diagnostic_emission_cannot_report_false_success(self):
        controller = hexctl_module()

        class RendererError(Exception):
            pass

        renderer = argparse.Namespace(
            SynopsisError=RendererError,
            validate_committed_synopsis=lambda *_args: (_ for _ in ()).throw(
                RendererError("renderer refusal")
            ),
        )

        class BrokenDiagnostic(StringIO):
            def __init__(self, failure):
                super().__init__()
                self.failure = failure

            def write(self, _value):
                raise self.failure

        before = self.state_ledger_digests()
        for failure in (SystemExit(0), OSError("closed diagnostic stream")):
            with self.subTest(failure=type(failure).__name__):
                self.assert_renderer_refusal(lambda:
                    self.call_with_renderer(
                        controller, renderer, BrokenDiagnostic(failure)
                    )
                )
                self.assertEqual(self.state_ledger_digests(), before)

    def test_foreign_renderer_exceptions_and_process_interrupts_stay_distinct(self):
        controller = hexctl_module()

        class RendererError(Exception):
            pass

        for failure in (
            RuntimeError("foreign renderer failure"),
            KeyboardInterrupt(),
            GeneratorExit(),
        ):
            with self.subTest(failure=type(failure).__name__):
                renderer = argparse.Namespace(
                    SynopsisError=RendererError,
                    validate_committed_synopsis=lambda *_args, failure=failure: (
                        _ for _ in ()
                    ).throw(failure),
                )
                with self.assertRaises(type(failure)) as raised:
                    self.call_with_renderer(controller, renderer, StringIO())
                self.assertIs(raised.exception, failure)

    def test_corrupt_renderer_interface_is_a_bounded_refusal(self):
        controller = hexctl_module()

        class Loader:
            @staticmethod
            def exec_module(_module):
                pass

        specification = argparse.Namespace(loader=Loader())
        stderr = StringIO()
        with (
            mock.patch.object(
                controller, "read_configured_audit_log",
                return_value=("audit/AUDIT.md", b"record"),
            ),
            mock.patch.object(controller, "audit_delta_start", return_value=0),
            mock.patch.object(controller, "audit_record_bytes", return_value=b"record"),
            mock.patch.object(
                controller,
                "parse_audit_record",
                return_value=("fiat-audit-round/v1", "2026-08-23T02:17:46Z"),
            ),
            mock.patch.object(
                controller.importlib.util,
                "spec_from_file_location",
                return_value=specification,
            ),
            mock.patch.object(
                controller.importlib.util, "module_from_spec", return_value=object()
            ),
            redirect_stderr(stderr),
            self.assertRaises(BaseException) as raised,
        ):
            controller.validated_audit_record(
                self.target,
                {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                {"audit": {"rounds": []}},
                argparse.Namespace(log=None),
            )
        self.assertIsInstance(raised.exception, SystemExit)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("audit synopsis renderer cannot be loaded", stderr.getvalue())

    def test_renderer_must_return_one_sha256_digest(self):
        controller = hexctl_module()

        class RendererError(Exception):
            pass

        renderer = argparse.Namespace(
            SynopsisError=RendererError,
            validate_committed_synopsis=lambda *_args: "not-a-sha256",
        )

        class Loader:
            @staticmethod
            def exec_module(_module):
                pass

        specification = argparse.Namespace(loader=Loader())
        stderr = StringIO()
        with (
            mock.patch.object(
                controller, "read_configured_audit_log",
                return_value=("audit/AUDIT.md", b"record"),
            ),
            mock.patch.object(controller, "audit_delta_start", return_value=0),
            mock.patch.object(controller, "audit_record_bytes", return_value=b"record"),
            mock.patch.object(
                controller,
                "parse_audit_record",
                return_value=("fiat-audit-round/v1", "2026-08-23T02:17:46Z"),
            ),
            mock.patch.object(
                controller.importlib.util,
                "spec_from_file_location",
                return_value=specification,
            ),
            mock.patch.object(
                controller.importlib.util, "module_from_spec", return_value=renderer
            ),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            controller.validated_audit_record(
                self.target,
                {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                {"audit": {"rounds": []}},
                argparse.Namespace(log=None),
            )
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("renderer returned an invalid digest", stderr.getvalue())

    def test_date_only_heading_is_refused_before_mutation(self):
        self.write_record(timestamp="2026-08-23")
        self.refuse("record timestamp", "--findings", "0")

    def test_heading_identity_and_calendar_date_are_exact(self):
        self.write_record(timestamp="2026-02-30T02:17:46Z")
        self.refuse("calendar-valid", "--findings", "0")
        lines = self.record_lines()
        lines[0] = "## another topic, step 1, round 1 -- 2026-08-23T02:17:46Z"
        Path(self.log_path()).write_text("\n".join(lines), encoding="utf-8")
        self.refuse("topic, step, and round", "--findings", "0")

    def test_prior_offset_makes_legacy_markdown_irrelevant(self):
        self.write_record(findings=1)
        self.run_ctl("audit-round", "--findings", "1")
        path = Path(self.log_path())
        prefix = bytearray(path.read_bytes())
        prefix[3:11] = b"<script>"
        path.write_bytes(prefix)
        self.write_record(append=True)
        self.env["FAKE_GIT_MODE"] = "missing-commit"
        self.run_ctl("audit-round", "--findings", "0")

    def test_clean_log_only_predecessor_also_supplies_the_next_offset(self):
        self.write_record()
        self.run_ctl("audit-round", "--findings", "0")
        self.write_record(append=True)
        self.env["FAKE_GIT_MODE"] = "missing-commit"
        self.run_ctl("audit-round", "--findings", "0")

    def test_first_strict_round_accepts_a_git_absent_log(self):
        self.write_record()
        self.run_ctl("audit-round", "--findings", "0")
        latest = self.state()["steps"][0]["audit"]["rounds"][-1]
        self.assertEqual(latest["log_end_offset"], os.path.getsize(self.log_path()))

    def test_first_strict_round_preserves_a_git_baseline_ending_in_lf(self):
        baseline = b"legacy evidence\n"
        self.set_fake_baseline(baseline)
        Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
        Path(self.log_path()).write_bytes(baseline)
        self.write_record(append=True)
        self.run_ctl("audit-round", "--findings", "0")

    def test_first_strict_round_preserves_a_git_baseline_without_lf(self):
        baseline = b"legacy evidence"
        self.set_fake_baseline(baseline)
        Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
        Path(self.log_path()).write_bytes(baseline)
        self.write_record(append=True)
        self.run_ctl("audit-round", "--findings", "0")

    def test_legacy_missing_leaves_use_the_verified_git_blob(self):
        self.write_record(findings=1, verdict="guarded")
        self.run_ctl(
            "audit-round", "--findings", "1",
            "--fixes-commit", "legacy-fix",
            "--elenchus-verdict", "guarded",
        )
        baseline = Path(self.log_path()).read_bytes()
        self.rewrite_latest_round(
            schema=...,
            record_timestamp=...,
            entry_sha256=...,
            log_end_offset=...,
            elenchus_verdict=...,
        )
        self.run_ctl("status")
        self.run_ctl("verify")
        self.set_fake_baseline(baseline)
        self.write_record(append=True)
        self.run_ctl("audit-round", "--findings", "0")
        rounds = self.state()["steps"][0]["audit"]["rounds"]
        self.assertNotIn("log_end_offset", rounds[0])
        self.assertEqual(rounds[1]["log_end_offset"], os.path.getsize(self.log_path()))

    def test_git_baseline_failures_refuse_without_state_or_ledger_drift(self):
        baseline = b"legacy evidence\n"
        self.set_fake_baseline(baseline)
        Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
        Path(self.log_path()).write_bytes(baseline)
        self.write_record(append=True)
        for mode, fragment in (
            ("missing-commit", "baseline commit"),
            ("baseline-unavailable", "baseline path"),
            ("baseline-ambiguous", "ambiguous Git"),
            ("baseline-unsafe", "regular Git blob"),
            ("baseline-oversized", "byte cap"),
            ("baseline-malformed-size", "size is malformed"),
            ("baseline-short-read", "length does not match"),
        ):
            with self.subTest(mode=mode):
                self.env["FAKE_GIT_MODE"] = mode
                self.refuse(fragment, "--findings", "0")
        self.env.pop("FAKE_GIT_MODE", None)

    def test_changed_git_baseline_refuses_without_drift(self):
        self.set_fake_baseline(b"expected legacy\n")
        Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
        Path(self.log_path()).write_bytes(b"changed! legacy\n")
        self.write_record(append=True)
        self.refuse("changed before", "--findings", "0")

    def test_boundary_separator_is_exact_for_all_baseline_endings(self):
        record = "\n".join(self.record_lines()).encode()
        cases = (
            (b"", b"\n" + record),
            (b"legacy\n", b"legacy\n" + record),
            (b"legacy\n", b"legacy\n\n\n" + record),
            (b"legacy", b"legacy\n" + record),
            (b"legacy", b"legacy\n\n\n" + record),
        )
        for baseline, live in cases:
            with self.subTest(baseline=baseline, delta=live[len(baseline):]):
                self.set_fake_baseline(baseline)
                Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
                Path(self.log_path()).write_bytes(live)
                self.refuse("audit record", "--findings", "0")

    def test_malformed_mismatched_and_past_eof_offsets_never_fall_back(self):
        self.write_record(findings=1)
        self.run_ctl("audit-round", "--findings", "1")
        log = Path(self.log_path())
        initial_log = log.read_bytes()
        state_path = Path(self.target, ".hexaemeron", "state.json")
        ledger_path = Path(self.target, ".hexaemeron", "ledger.jsonl")
        initial_state = state_path.read_bytes()
        initial_ledger = ledger_path.read_bytes()
        cases = (
            ({"log_end_offset": True}, "non-boolean integer", True),
            ({"log_end_offset": "1"}, "non-boolean integer", True),
            ({"log_end_offset": -1}, "outside the current log", True),
            ({"log_end_offset": len(initial_log)}, "outside the current log", False),
            ({"log_end_offset": 2 * 1024 * 1024 + 1}, "outside", True),
            ({"log": "other/AUDIT.md"}, "does not match", True),
        )
        self.set_fake_baseline(initial_log)
        for changes, fragment, append in cases:
            with self.subTest(changes=changes):
                state_path.write_bytes(initial_state)
                ledger_path.write_bytes(initial_ledger)
                log.write_bytes(initial_log)
                self.rewrite_latest_round(**changes)
                if append:
                    self.write_record(append=True)
                self.refuse(fragment, "--findings", "0")

    def test_prefix_utf8_stays_outside_delta_parsing_but_fails_synopsis_input(self):
        self.write_record(findings=1)
        self.run_ctl("audit-round", "--findings", "1")
        path = Path(self.log_path())
        prefix = bytearray(path.read_bytes())
        prefix[0] = 0xff
        path.write_bytes(prefix)
        self.write_record(append=True)
        self.refuse("source is not UTF-8", "--findings", "0")

    def test_invalid_utf8_in_the_delta_refuses_without_drift(self):
        self.write_record(findings=1)
        self.run_ctl("audit-round", "--findings", "1")
        path = Path(self.log_path())
        path.write_bytes(path.read_bytes() + b"\n\xff\n")
        self.refuse("delta is not UTF-8", "--findings", "0")

    def test_raw_suffix_refuses_prelude_extra_fields_rows_headings_and_trailers(self):
        canonical = self.record_lines()
        placeholder = canonical.index("| -- | -- | -- | none | -- |")
        leads = canonical.index("Leads not pursued: none")
        cases = {
            "prelude": ["prelude", *canonical],
            "field": canonical[:leads] + ["Extra: value", ""] + canonical[leads:],
            "row": canonical[:placeholder + 1]
            + ["| F-02 | low | fixture.py | extra | open |"]
            + canonical[placeholder + 1:],
            "heading": canonical[:-1] + ["## later", ""],
            "trailer": canonical[:-1] + ["trailer", ""],
        }
        for name, lines in cases.items():
            with self.subTest(name=name):
                Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
                Path(self.log_path()).write_bytes("\n".join(lines).encode())
                self.refuse("audit record", "--findings", "0")

    def test_each_field_and_blank_separator_is_required(self):
        for omitted in (
            "schema", "covered", "not_checked", "verdict", "table", "leads"
        ):
            with self.subTest(omitted=omitted):
                self.write_record(omit=(omitted,))
                self.refuse("audit record", "--findings", "0")
        lines = self.record_lines()
        for index, line in enumerate(lines):
            if line != "":
                continue
            with self.subTest(blank_index=index):
                altered = lines[:index] + lines[index + 1:]
                Path(self.log_path()).write_bytes("\n".join(altered).encode())
                self.refuse("audit record", "--findings", "0")

    def test_active_round_ten_offset_is_a_stable_raw_boundary(self):
        controller = hexctl_module()
        repository = Path(HERE).parents[2]
        prefix = (repository / "audit" / "AUDIT.md").read_bytes()[:601787]
        self.assertEqual(len(prefix), 601787)
        self.assertEqual(
            hashlib.sha256(prefix).hexdigest(),
            "6f5e09a9bbb79582cab41839c9ae43b6becfd45fd3668f2845bf7f9cc887dffb",
        )
        step = {
            "n": 1,
            "audit": {
                "rounds": [
                    {"log": "audit/AUDIT.md", "log_end_offset": 601787}
                ]
            }
        }
        boundary = getattr(controller, "audit_delta_start", None)
        self.assertTrue(callable(boundary))
        self.assertEqual(
            boundary(
                str(repository), {"steps": [step]}, step,
                "audit/AUDIT.md", prefix + b"\nnext"
            ),
            601787,
        )

    def test_covered_refuses_missing_duplicate_unknown_and_invalid_values(self):
        for covered in (
            "",
            "packet-state-drift=reviewed; packet-state-drift=reviewed",
            "packet-state-drift=reviewed; unknown-risk=reviewed",
            "packet-state-drift=accepted",
        ):
            with self.subTest(covered=covered):
                self.write_record(covered=covered)
                self.refuse("Covered", "--findings", "0")

    def test_findings_count_zero_row_and_verdict_must_match(self):
        self.write_record(findings=1, table_rows=[])
        self.refuse("findings table", "--findings", "1")
        self.write_record(
            findings=0,
            table_rows=["| F-01 | low | fixture.py | unexpected | open |"],
        )
        self.refuse("zero-finding row", "--findings", "0")
        self.write_record(findings=1, verdict="guarded")
        self.refuse(
            "Elenchus verdict",
            "--findings", "1", "--fixes-commit", "fix-1",
            "--elenchus-verdict", "passed",
        )

    def test_findings_table_accepts_a_raw_escaped_pipe_in_a_cell(self):
        self.write_record(
            findings=1,
            table_rows=[
                r"| F-01 | low | fixture.py | comparison `a \| b` | open |"
            ],
        )
        self.run_ctl("audit-round", "--findings", "1")

    def test_controller_table_cell_scanner_scales_with_the_line_cap(self):
        controller = hexctl_module()

        def elapsed(size):
            line = "| " + "x" * size + " | b | c | d | e |"
            started = time.process_time()
            self.assertEqual(len(controller.audit_table_cells(line)), 5)
            return time.process_time() - started

        small = elapsed(64 * 1024)
        large = elapsed(512 * 1024)
        self.assertLess(
            large,
            small * 20,
            f"controller table scan scaled from {small:.6f}s to {large:.6f}s",
        )

    def test_findings_table_refuses_an_escaped_closing_pipe(self):
        self.write_record(
            findings=1,
            table_rows=[r"| F-01 | low | fixture.py | finding | open \|"],
        )
        self.refuse("malformed data row", "--findings", "1")

    def test_supplied_log_must_be_the_configured_path(self):
        self.write_record()
        self.refuse(
            "configured audit log path",
            "--findings", "0", "--log", "other/AUDIT.md",
        )
        alias = os.path.join(self.target, "audit", "alias.md")
        os.symlink("AUDIT.md", alias)
        self.refuse(
            "configured audit log path",
            "--findings", "0", "--log", "audit/alias.md",
        )

    def test_log_must_be_regular_contained_utf8_and_bounded(self):
        path = self.log_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.refuse("regular file", "--findings", "0")

        self.write_record()
        os.remove(path)
        os.mkdir(path)
        self.refuse("regular file", "--findings", "0")
        os.rmdir(path)

        real = os.path.join(os.path.dirname(path), "real.md")
        Path(real).write_text("\n".join(self.record_lines()), encoding="utf-8")
        os.symlink("real.md", path)
        self.refuse("symlink", "--findings", "0")
        os.remove(path)

        Path(path).write_bytes(b"\xff\n")
        self.refuse("UTF-8", "--findings", "0")
        Path(path).write_bytes(b"x" * (2 * 1024 * 1024 + 1))
        self.refuse("byte cap", "--findings", "0")

    def test_log_refuses_delta_line_and_total_byte_caps(self):
        path = self.write_record()
        record = Path(path).read_bytes()
        Path(path).write_bytes(b"x" * (1024 * 1024 + 1) + b"\n" + record)
        self.refuse("physical line", "--findings", "0")

        Path(path).write_bytes(b"x" * (2 * 1024 * 1024 + 1))
        self.refuse("byte cap", "--findings", "0")

    def test_high_cardinality_risk_coverage_stays_within_the_input_bound(self):
        controller = hexctl_module()
        count = 30_000
        register = (
            "```risk-register\n"
            + "\n".join(
                f"risk-{index} | boundary | check" for index in range(count)
            )
            + "\n```\n"
        )
        started = time.monotonic()
        with (
            mock.patch.object(controller, "receipted_source", return_value={}),
            mock.patch.object(
                controller,
                "source_risk_register",
                return_value={"markdown": register},
            ),
        ):
            risk_ids = controller.audit_risk_ids(".", {})
        controller.audit_covered(
            "; ".join(f"{risk_id}=reviewed" for risk_id in risk_ids),
            risk_ids,
        )
        elapsed = time.monotonic() - started
        self.assertEqual(len(risk_ids), count)
        self.assertLess(elapsed, 1.0)

    def test_invalid_configured_path_refuses_without_a_traceback(self):
        for invalid in ("audit/\0.md", "audit/\ud800.md"):
            with self.subTest(invalid=ascii(invalid)):
                self.run_ctl(
                    "config", "set", "audit.log_path", json.dumps(invalid)
                )
                self.refuse("valid filesystem path", "--findings", "0")

    def test_parent_symlink_swap_cannot_escape_the_descriptor_walk(self):
        controller = hexctl_module()
        with (
            tempfile.TemporaryDirectory() as raw_root,
            tempfile.TemporaryDirectory() as raw_outside,
        ):
            root = os.path.realpath(raw_root)
            outside = os.path.realpath(raw_outside)
            audit_dir = Path(root) / "audit"
            audit_dir.mkdir()
            (audit_dir / "AUDIT.md").write_bytes(b"inside")
            (Path(outside) / "AUDIT.md").write_bytes(b"outside")
            lexical = str(audit_dir / "AUDIT.md")
            real_open = os.open
            swapped = False

            def racing_open(target, flags, *args, **kwargs):
                nonlocal swapped
                opens_old_path = target == lexical
                opens_new_component = target == "audit" and "dir_fd" in kwargs
                if not swapped and (opens_old_path or opens_new_component):
                    swapped = True
                    audit_dir.rename(Path(root) / "audit-before-swap")
                    os.symlink(outside, audit_dir)
                return real_open(target, flags, *args, **kwargs)

            stderr = StringIO()
            with mock.patch.object(controller.os, "open", side_effect=racing_open):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    controller.read_configured_audit_log(
                        root, "audit/AUDIT.md", None
                    )
            self.assertIn("audit log path cannot be read", stderr.getvalue())

    def test_descriptor_walk_closes_a_child_when_its_stat_fails(self):
        controller = hexctl_module()
        with tempfile.TemporaryDirectory() as raw_root:
            root = os.path.realpath(raw_root)
            audit_dir = Path(root) / "audit"
            audit_dir.mkdir()
            (audit_dir / "AUDIT.md").write_bytes(b"inside")
            real_fstat = os.fstat
            opened = []

            def failing_child_stat(descriptor):
                opened.append(descriptor)
                if len(opened) == 2:
                    raise OSError("synthetic child fstat failure")
                return real_fstat(descriptor)

            stderr = StringIO()
            with mock.patch.object(
                controller.os, "fstat", side_effect=failing_child_stat
            ):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    controller.read_configured_audit_log(
                        root, "audit/AUDIT.md", None
                    )
            self.assertIn("audit log path cannot be read", stderr.getvalue())

            still_open = []
            for descriptor in opened:
                try:
                    real_fstat(descriptor)
                except OSError:
                    continue
                still_open.append(descriptor)
                os.close(descriptor)
            self.assertEqual(still_open, [])

    def test_canonical_reopen_closes_a_child_when_parent_close_fails(self):
        controller = hexctl_module()
        with tempfile.TemporaryDirectory() as raw_root:
            root = os.path.realpath(raw_root)
            audit_dir = Path(root) / "audit"
            audit_dir.mkdir()
            (audit_dir / "AUDIT.md").write_bytes(b"inside")
            real_open = os.open
            real_close = os.close
            real_fstat = os.fstat
            opened = []
            close_failed = False

            def tracking_open(*args, **kwargs):
                descriptor = real_open(*args, **kwargs)
                opened.append(descriptor)
                return descriptor

            def fail_current_parent_close(descriptor):
                nonlocal close_failed
                if len(opened) >= 5 and descriptor == opened[3] and not close_failed:
                    close_failed = True
                    raise OSError("synthetic parent close failure")
                return real_close(descriptor)

            stderr = StringIO()
            with (
                mock.patch.object(controller.os, "open", side_effect=tracking_open),
                mock.patch.object(
                    controller.os, "close", side_effect=fail_current_parent_close
                ),
                redirect_stderr(stderr),
                self.assertRaises(SystemExit),
            ):
                controller.read_configured_audit_log(
                    root, "audit/AUDIT.md", None
                )
            self.assertTrue(close_failed)
            self.assertIn("changed during read", stderr.getvalue())

            still_open = []
            for descriptor in opened:
                try:
                    real_fstat(descriptor)
                except OSError:
                    continue
                still_open.append(descriptor)
                real_close(descriptor)
            self.assertEqual(still_open, [])

    def test_descriptor_walk_refuses_a_platform_without_safe_primitives(self):
        controller = hexctl_module()
        with tempfile.TemporaryDirectory() as root:
            audit_dir = Path(root) / "audit"
            audit_dir.mkdir()
            (audit_dir / "AUDIT.md").write_bytes(b"inside")
            stderr = StringIO()
            with mock.patch.object(controller.os, "O_NOFOLLOW", 0):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    controller.read_configured_audit_log(
                        root, "audit/AUDIT.md", None
                    )
            self.assertIn("platform cannot safely read", stderr.getvalue())

    def test_configured_log_read_refuses_an_observed_in_place_rewrite(self):
        controller = hexctl_module()
        with tempfile.TemporaryDirectory() as raw_root:
            root = os.path.realpath(raw_root)
            audit_dir = Path(root) / "audit"
            audit_dir.mkdir()
            log = audit_dir / "AUDIT.md"
            log.write_bytes(b"inside")
            real_fdopen = controller.os.fdopen

            class RacingHandle:
                def __init__(self, descriptor, mode):
                    self.handle = real_fdopen(descriptor, mode)

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.handle.close()

                def fileno(self):
                    return self.handle.fileno()

                def read(self, size):
                    data = self.handle.read(size)
                    log.write_bytes(b"outside")
                    return data

            stderr = StringIO()
            with mock.patch.object(
                controller.os, "fdopen", side_effect=RacingHandle
            ):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    controller.read_configured_audit_log(
                        root, "audit/AUDIT.md", None
                    )
            self.assertIn("changed during read", stderr.getvalue())

    def test_configured_log_read_refuses_an_observed_parent_rebind(self):
        controller = hexctl_module()
        with tempfile.TemporaryDirectory() as raw_root:
            root = os.path.realpath(raw_root)
            audit_dir = Path(root) / "audit"
            audit_dir.mkdir()
            log = audit_dir / "AUDIT.md"
            log.write_bytes(b"inside")
            moved_dir = Path(root) / "moved-audit"
            real_fdopen = controller.os.fdopen

            class RacingHandle:
                def __init__(self, descriptor, mode):
                    self.handle = real_fdopen(descriptor, mode)

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.handle.close()

                def fileno(self):
                    return self.handle.fileno()

                def read(self, size):
                    data = self.handle.read(size)
                    audit_dir.rename(moved_dir)
                    audit_dir.mkdir()
                    (audit_dir / "AUDIT.md").write_bytes(b"outside")
                    return data

            stderr = StringIO()
            with mock.patch.object(
                controller.os, "fdopen", side_effect=RacingHandle
            ):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    controller.read_configured_audit_log(
                        root, "audit/AUDIT.md", None
                    )
            self.assertIn("changed during read", stderr.getvalue())

    def test_fifo_swap_cannot_block_the_final_open(self):
        controller = hexctl_module()
        with tempfile.TemporaryDirectory() as raw_root:
            root = os.path.realpath(raw_root)
            audit_dir = Path(root) / "audit"
            audit_dir.mkdir()
            log = audit_dir / "AUDIT.md"
            log.write_bytes(b"inside")
            real_open = os.open
            swapped = False

            def racing_open(target, flags, *args, **kwargs):
                nonlocal swapped
                if not swapped and target == "AUDIT.md" and "dir_fd" in kwargs:
                    self.assertTrue(flags & os.O_NONBLOCK)
                    swapped = True
                    log.unlink()
                    os.mkfifo(log)
                return real_open(target, flags, *args, **kwargs)

            stderr = StringIO()
            with mock.patch.object(controller.os, "open", side_effect=racing_open):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    controller.read_configured_audit_log(
                        root, "audit/AUDIT.md", None
                    )
            self.assertIn("not a regular file", stderr.getvalue())

    def test_escaping_configured_log_is_refused(self):
        self.run_ctl("config", "set", "audit.log_path", '"../AUDIT.md"')
        self.refuse("escapes target directory", "--findings", "0")

    def test_valid_rounds_store_schema_timestamp_digest_offset_and_exact_verdicts(self):
        expected_verdicts = ["guarded", "unguarded", "passed", "inconclusive", None]
        for index, verdict in enumerate(expected_verdicts, 1):
            findings = 0 if verdict is None else 1
            self.write_record(
                findings=findings,
                verdict=verdict or "null",
                append=index > 1,
            )
            args = ["--findings", str(findings), "--log", "audit/AUDIT.md"]
            if verdict is not None:
                args += [
                    "--fixes-commit", f"fix-{index}",
                    "--elenchus-verdict", verdict,
                ]
            self.run_ctl("audit-round", *args)
            round_entry = self.state()["steps"][0]["audit"]["rounds"][-1]
            self.assertEqual(round_entry.get("schema"), "fiat-audit-round/v1")
            self.assertEqual(round_entry["log"], "audit/AUDIT.md")
            self.assertEqual(
                round_entry.get("record_timestamp"), "2026-08-23T02:17:46Z"
            )
            self.assertRegex(
                round_entry.get("entry_sha256", ""), r"^[0-9a-f]{64}$"
            )
            self.assertRegex(
                round_entry.get("synopsis_sha256", ""), r"^[0-9a-f]{64}$"
            )
            self.assertEqual(
                round_entry.get("log_end_offset"), os.path.getsize(self.log_path())
            )
            self.assertEqual(round_entry["elenchus_verdict"], verdict)

        events = [
            json.loads(line)["data"]
            for line in Path(
                os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
            ).read_text(encoding="utf-8").splitlines()
            if json.loads(line)["event"] == "audit-round"
        ]
        self.assertEqual(
            [event.get("elenchus_verdict") for event in events], expected_verdicts
        )

    def test_audit_closure_cannot_replace_the_checked_log_path(self):
        self.write_record()
        self.run_ctl("audit-round", "--findings", "0")
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "done", "audit", "--log", "other/AUDIT.md", expect=2
        )
        self.assertIn("final round", result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

        self.run_ctl("done", "audit", "--log", "audit/AUDIT.md")
        self.assertEqual(
            self.state()["steps"][0]["receipts"]["audit"]["log"],
            "audit/AUDIT.md",
        )


class TestProseAndPush(HexctlCase):
    def to_prose(self, task_issue=None):
        self.to_audit(task_issue=task_issue)
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

    def test_task_issue_is_bound_to_the_initial_state_and_run_branch(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.init("Carry the task issue number", task_issue=issue)
        state = self.state()
        self.assertEqual(state["version"], 1)
        self.assertEqual(state["run_branch"], "fiat/438-carry-the-task-issue-number")
        self.assertEqual(state["receipts"]["task_issue"], issue)
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["event"], "init")
        self.assertEqual(entries[0]["data"]["task_issue"], issue)
        self.assertEqual(entries[0]["state"], hexctl_module().state_fingerprint(state))
        self.run_ctl("verify")

    def test_init_help_describes_the_issue_aware_branch_default(self):
        proc = self.run_ctl("init", "--help")
        self.assertIn("prefixed by task issue when supplied", proc.stdout)

    def test_task_issue_prefix_survives_a_long_topic(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.init("x" * 100, task_issue=issue)
        branch = self.run_branch()
        self.assertEqual(branch, "fiat/438-" + "x" * 44)
        self.assertEqual(len(branch.removeprefix("fiat/")), 48)

    def test_task_issue_prefix_uses_run_for_an_empty_topic_slug(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.init("###", task_issue=issue)
        self.assertEqual(self.run_branch(), "fiat/438-run")

    def test_task_issue_and_override_are_validated_before_state_creation(self):
        invalid_issues = (
            "not-a-url",
            "not-a-url/issues/438",
            "https:///issues/438",
            "javascript:payload/issues/438",
            "https://github.com/wildcat-finance/skills/issues/4\n38",
            "https://github.com/wildcat-finance/skills/issues/0",
            "https://github.com/wildcat-finance/skills/issues/0438",
            "https://github.com/wildcat-finance/skills/issues/438/extra",
            "https://github.com/wildcat-finance/skills/pull/438",
        )
        for issue in invalid_issues:
            with self.subTest(issue=issue):
                proc = self.run_ctl(
                    "init", "--topic", "t", "--task-issue", issue, expect=2
                )
                self.assertIn("--task-issue", proc.stderr)
                root = os.path.join(self.target, ".hexaemeron")
                self.assertFalse(os.path.exists(os.path.join(root, "state.json")))
                self.assertFalse(os.path.exists(os.path.join(root, "ledger.jsonl")))

        issue = "https://github.com/wildcat-finance/skills/issues/438"
        for branch in ("release/438-prep", "fiat/prep", "fiat/1438-prep"):
            with self.subTest(branch=branch):
                proc = self.run_ctl(
                    "init", "--topic", "t", "--task-issue", issue,
                    "--run-branch", branch, expect=2,
                )
                self.assertIn("fiat/438-", proc.stderr)
                root = os.path.join(self.target, ".hexaemeron")
                self.assertFalse(os.path.exists(os.path.join(root, "state.json")))
                self.assertFalse(os.path.exists(os.path.join(root, "ledger.jsonl")))

    def test_task_issue_allows_an_exact_issue_bearing_override(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.run_ctl(
            "init", "--topic", "t", "--task-issue", issue,
            "--run-branch", "fiat/438-prep",
        )
        self.assertEqual(self.run_branch(), "fiat/438-prep")

    def test_task_issue_run_branch_propagates_to_step_directives(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.to_steps(("Scaffold", "Core"), task_issue=issue)
        first = self.next_json()
        self.assertEqual(first["run_branch"], "fiat/438-test-topic")
        self.assertEqual(first["branch"], "fiat/438-test-topic-step-1-scaffold")
        self.assertEqual(first["branch_from"], "fiat/438-test-topic")
        self.assertEqual(first["pr_base"], "fiat/438-test-topic")
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        self.finish_step(1)
        second = self.next_json()
        self.assertEqual(second["branch"], "fiat/438-test-topic-step-2-core")
        self.assertEqual(second["branch_from"], first["branch"])
        self.assertEqual(second["pr_base"], first["branch"])

    def test_task_issue_cannot_first_be_recorded_after_init(self):
        self.init()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, "rb") as handle:
            state_before = handle.read()
        with open(ledger_path, "rb") as handle:
            ledger_before = handle.read()
        proc = self.run_ctl(
            "record", "task_issue",
            '"https://github.com/wildcat-finance/skills/issues/438"', expect=2,
        )
        self.assertIn("--task-issue", proc.stderr)
        with open(state_path, "rb") as handle:
            self.assertEqual(handle.read(), state_before)
        with open(ledger_path, "rb") as handle:
            self.assertEqual(handle.read(), ledger_before)

    def test_task_issue_repeat_is_idempotent_and_cannot_change(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.init(task_issue=issue)
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, "rb") as handle:
            state_before = handle.read()
        with open(ledger_path, "rb") as handle:
            ledger_before = handle.read()

        self.run_ctl("record", "task_issue", json.dumps(issue))
        proc = self.run_ctl(
            "record", "task_issue",
            '"https://github.com/wildcat-finance/skills/issues/439"', expect=2,
        )
        self.assertIn("cannot be changed", proc.stderr)
        with open(state_path, "rb") as handle:
            self.assertEqual(handle.read(), state_before)
        with open(ledger_path, "rb") as handle:
            self.assertEqual(handle.read(), ledger_before)

    def test_legacy_task_issue_state_keeps_its_stored_branch(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.to_steps(("One",))
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["task_issue"] = issue
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        controller = hexctl_module()
        entry = entries[-1]
        entry.pop("hash")
        entry["state"] = controller.state_fingerprint(state)
        entry["hash"] = hashlib.sha256(controller.canonical(entry).encode()).hexdigest()
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for item in entries:
                handle.write(json.dumps(item, sort_keys=True) + "\n")

        self.run_ctl("verify")
        self.assertEqual(self.state()["run_branch"], "fiat/test-topic")
        directive = self.next_json()
        self.assertEqual(directive["run_branch"], "fiat/test-topic")
        self.assertEqual(directive["branch"], "fiat/test-topic-step-1-one")

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
        self.to_prose(task_issue="https://x/issues/74")
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
        ledger = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
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

        # A run that lived in a worktree archives into the checkout it was
        # started from, because archiving inside the tree and then removing the
        # tree would destroy the archive in the same breath.
        root = os.path.join(self.dir, ".hexaemeron")
        self.run_ctl("reset")
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
        return os.path.join(self.target, ".hexaemeron", "state.json")

    def ledger_file(self):
        return os.path.join(self.target, ".hexaemeron", "ledger.jsonl")

    def to_audit_with_suite(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '["x","y"]')

    def test_state_edit_detected_by_verify(self):
        self.to_audit_with_suite()
        self.run_ctl("audit-round", "--findings", "2", "--log", "audit/AUDIT.md",
                     "--fixes-commit", "fff",
                     "--elenchus-verdict", "guarded")
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


class StateContainerValidationTests(HexctlCase):
    """Every state-backed command crosses one ordered, value-free shape gate."""

    def setUp(self):
        super().setUp()
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl(
            "audit-round", "--findings", "1", "--log", "audit/AUDIT.md"
        )
        self.state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        self.ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(self.state_path, "rb") as handle:
            self.valid_state_bytes = handle.read()
        with open(self.ledger_path, "rb") as handle:
            self.valid_ledger_bytes = handle.read()

    @staticmethod
    def replace_at(state, parts, value):
        node = state
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value

    @staticmethod
    def remove_at(state, parts):
        node = state
        for part in parts[:-1]:
            node = node[part]
        del node[parts[-1]]

    def write_state(self, state):
        with open(self.state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)

    def assert_command_parity(self, state, path, kind):
        self.write_state(state)
        with open(self.state_path, "rb") as handle:
            state_before = handle.read()
        expected = f"hexctl: error: state key '{path}' must be an {kind}\n"
        commands = (
            ("status",),
            ("next",),
            ("verify",),
            ("record", "shape_probe", '"secret-shaped-value"'),
        )
        for command in commands:
            with self.subTest(path=path, kind=kind, command=command[0]):
                proc = self.run_ctl(*command, expect=1)
                self.assertEqual(proc.stdout, "")
                self.assertEqual(proc.stderr, expected)
                self.assertNotIn("secret-shaped-value", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
                with open(self.state_path, "rb") as handle:
                    self.assertEqual(handle.read(), state_before)
                with open(self.ledger_path, "rb") as handle:
                    self.assertEqual(handle.read(), self.valid_ledger_bytes)

    def test_required_container_matrix_is_shared_by_every_command(self):
        cases = (
            ("config", "object", ("config",), []),
            ("config.skills", "object", ("config", "skills"), []),
            ("config.audit", "object", ("config", "audit"), []),
            ("config.git", "object", ("config", "git"), []),
            ("receipts", "object", ("receipts",), []),
            ("steps", "array", ("steps",), {}),
            ("steps[0].receipts", "object", ("steps", 0, "receipts"), []),
            ("steps[0].audit", "object", ("steps", 0, "audit"), []),
            (
                "steps[0].audit.rounds",
                "array",
                ("steps", 0, "audit", "rounds"),
                {},
            ),
        )
        self.assert_command_parity([], "$", "object")
        for path, kind, parts, wrong_kind in cases:
            with self.subTest(path=path, specimen="missing"):
                state = json.loads(self.valid_state_bytes)
                self.remove_at(state, parts)
                self.assert_command_parity(state, path, kind)
            with self.subTest(path=path, specimen="wrong-kind"):
                state = json.loads(self.valid_state_bytes)
                self.replace_at(state, parts, wrong_kind)
                self.assert_command_parity(state, path, kind)

        member_cases = (
            ("steps[0]", "object", ("steps", 0)),
            ("steps[1]", "object", ("steps", 1)),
            (
                "steps[0].audit.rounds[0]",
                "object",
                ("steps", 0, "audit", "rounds", 0),
            ),
        )
        for path, kind, parts in member_cases:
            with self.subTest(path=path, specimen="wrong-kind"):
                state = json.loads(self.valid_state_bytes)
                self.replace_at(state, parts, "secret-shaped-value")
                self.assert_command_parity(state, path, kind)

    def test_first_fault_follows_the_documented_order(self):
        cases = []

        state = json.loads(self.valid_state_bytes)
        del state["config"]
        state["receipts"] = []
        state["steps"] = {}
        cases.append((state, "config", "object"))

        state = json.loads(self.valid_state_bytes)
        state["config"]["skills"] = []
        state["receipts"] = []
        cases.append((state, "config.skills", "object"))

        state = json.loads(self.valid_state_bytes)
        state["steps"][0]["receipts"] = []
        state["steps"][0]["audit"] = []
        cases.append((state, "steps[0].receipts", "object"))

        state = json.loads(self.valid_state_bytes)
        state["steps"][0]["receipts"] = []
        state["steps"][1] = "secret-shaped-value"
        cases.append((state, "steps[1]", "object"))

        for state, path, kind in cases:
            with self.subTest(path=path):
                self.assert_command_parity(state, path, kind)

    def test_version_one_legacy_and_heterogeneous_receipts_still_load(self):
        state = json.loads(self.valid_state_bytes)
        state.pop("frontier")
        state.pop("run_branch")
        state["steps"][0]["phase"] = "issue"
        state["receipts"]["legacy_null"] = None
        state["receipts"]["legacy_list"] = [1, "two", {"three": True}]
        state["steps"][0]["receipts"]["legacy_scalar"] = 7
        state["steps"][0]["audit"]["rounds"][0]["legacy_leaf"] = [None]
        self.write_state(state)

        loaded = hexctl_module().load_state(self.target)

        self.assertEqual(loaded, state)
        self.assertEqual(loaded["version"], 1)


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
        path = os.path.join(self.target, ".hexaemeron", "state.json")
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

    def test_direct_classifier_calls_with_non_object_containers_do_not_raise(self):
        """The load boundary rejects these shapes for state-backed commands.

        Keep the classifier itself total for isolated callers and optional leaves.
        """
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


class StaleControllerTests(OriginCheckoutMixin, unittest.TestCase):
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
            make_origin_checkout(module_dir)
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


class FrontierGateTests(OriginCheckoutMixin, unittest.TestCase):
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
        make_origin_checkout(self.dir)
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
        with open(os.path.join(self.target, ".hexaemeron", "state.json"),
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
        with open(os.path.join(self.target, ".hexaemeron", "state.json"),
                  encoding="utf-8") as fh:
            held = json.load(fh)["frontier"]
        self.assertEqual(held["rows"], 1)
        self.assertEqual(held["sha256"], self.before["sha256"])


def compact_row(version, axis, revision, digest, change="Did the thing."):
    return f"- `{version}` | {axis} | `{revision}` | `{digest}` | [e](f) | {change}\n"


class LedgerRowShapeTests(unittest.TestCase):
    """The gate and the suite parse the same row set, whichever shape a
    ledger spells its history in.

    tests/test_evolution_contract.py accepts a table row and a compact bullet
    row; the issue 322 run halted because the gate read only the first, saw a
    two-row ledger as empty at init, and refused the one real new row at
    integrate (skills#443).
    """

    def test_a_compact_bullet_row_parses(self):
        digest = "a" * 64
        rows = hexctl_module().ledger_rows(
            compact_row("example-v0.1.0", "baseline", "held-job", digest))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["version"], "example-v0.1.0")
        self.assertEqual(rows[0]["digest"], digest)

    def test_a_table_row_still_parses(self):
        digest = "b" * 64
        rows = hexctl_module().ledger_rows(
            row("example-v0.1.0", "baseline", "held-job", digest))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["version"], "example-v0.1.0")

    def test_the_gate_parses_every_governed_ledger_in_the_tree(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ledgers = sorted(
            glob.glob(os.path.join(repo, "plugins", "*", "skills", "*", "EVOLUTION.md")))
        self.assertTrue(ledgers)
        module = hexctl_module()
        for ledger in ledgers:
            with self.subTest(ledger=os.path.relpath(ledger, repo)):
                with open(ledger, encoding="utf-8") as fh:
                    text = fh.read()
                self.assertTrue(
                    module.ledger_rows(text),
                    "a governed ledger parsed as having no history rows")


class FrontierGateCompactTests(FrontierGateTests):
    """The whole gate, over a ledger spelled in the compact bullet shape."""

    def setUp(self):
        super().setUp()
        self.base_row = compact_row(
            "widget-v1.1.0", "baseline", self.HELD[1], self.base_digest,
            "Versioning starts here.")
        widget_ledger(self.ledger, [self.base_row], version="widget-v1.1.0",
                      status=self.HELD[0], revision=self.HELD[1],
                      frontier=self.HELD[2], job=self.HELD[3])
        with open(self.ledger, "rb") as handle:
            self.before["sha256"] = hashlib.sha256(handle.read()).hexdigest()

    def close_with(self, version, axis, header=None, digest=None, extra=()):
        header = header or self.NEXT
        widget_ledger(
            self.ledger,
            [self.base_row, compact_row(version, axis, header[1],
                                        digest or frontier_digest(*header)),
             *extra],
            version=version, status=header[0], revision=header[1],
            frontier=header[2], job=header[3])

    def test_two_new_rows_are_refused(self):
        self.close_with("widget-v2.1.0", "evolution",
                        extra=[compact_row("widget-v3.1.0", "evolution",
                                           self.NEXT[1],
                                           frontier_digest(*self.NEXT))])
        self.assertIn("gained 2 history row(s)", self.fault())

    def test_a_header_row_mismatch_is_refused(self):
        widget_ledger(
            self.ledger,
            [self.base_row, compact_row("widget-v2.1.0", "evolution",
                                        self.NEXT[1],
                                        frontier_digest(*self.NEXT))],
            version="widget-v7.7.7", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIn("they have to be the same row", self.fault())


class FrontierGateLegacySnapshotTests(OriginCheckoutMixin, unittest.TestCase):
    """A snapshot taken while the gate could not see compact rows counted a
    real history as empty. The gate anchors on the init-time version instead
    of trusting that count, so such a run can still close honestly."""

    HELD = FrontierGateTests.HELD
    NEXT = FrontierGateTests.NEXT

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        make_origin_checkout(self.dir)
        self.ledger = os.path.join(
            self.dir, "plugins", "demo", "skills", "widget", "EVOLUTION.md")
        digest = frontier_digest(*self.HELD)
        self.rows = [
            compact_row("widget-v0.1.0", "baseline", self.HELD[1], digest,
                        "Versioning starts here."),
            compact_row("widget-v1.1.0", "evolution", self.HELD[1], digest),
        ]
        widget_ledger(self.ledger, self.rows, version="widget-v1.1.0",
                      status=self.HELD[0], revision=self.HELD[1],
                      frontier=self.HELD[2], job=self.HELD[3])
        with open(self.ledger, "rb") as handle:
            ledger_sha256 = hashlib.sha256(handle.read()).hexdigest()
        self.before = {
            "ledger": os.path.relpath(self.ledger, self.dir),
            "sha256": ledger_sha256,
            "rows": 0,
            "version_at_init": "widget-v1.1.0",
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def fault(self):
        return hexctl_module().frontier_close_fault(self.ledger, self.before)

    def test_one_row_after_the_init_version_closes(self):
        widget_ledger(
            self.ledger,
            [*self.rows, compact_row("widget-v2.1.0", "evolution", self.NEXT[1],
                                     frontier_digest(*self.NEXT))],
            version="widget-v2.1.0", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIsNone(self.fault())

    def test_two_rows_after_the_init_version_are_refused(self):
        widget_ledger(
            self.ledger,
            [*self.rows,
             compact_row("widget-v2.1.0", "evolution", self.NEXT[1],
                         frontier_digest(*self.NEXT)),
             compact_row("widget-v3.1.0", "evolution", self.NEXT[1],
                         frontier_digest(*self.NEXT))],
            version="widget-v3.1.0", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIn("gained 2 history row(s)", self.fault())

    def test_a_vanished_init_version_row_is_refused(self):
        widget_ledger(
            self.ledger,
            [compact_row("widget-v2.1.0", "evolution", self.NEXT[1],
                         frontier_digest(*self.NEXT))],
            version="widget-v2.1.0", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIn("no longer carries the init-time version row", self.fault())


class WorktreePathTests(unittest.TestCase):
    """Deriving one run's worktree path, and refusing every path that is not it.

    These call the deriver and the validator directly. Neither touches state, a
    ledger or the filesystem, so driving them through a command would only report
    them indirectly, and the point of the step is that a bad path is refused
    before anything exists to inspect.
    """

    def setUp(self):
        self.module = hexctl_module()
        self.dir = tempfile.mkdtemp()
        self.repo = os.path.join(self.dir, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.root = os.path.realpath(self.repo)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def refuse(self, *args, **kwargs):
        """Call the validator and return the single refusal line it printed."""
        error = StringIO()
        with redirect_stderr(error):
            with self.assertRaises(SystemExit) as caught:
                self.module.check_worktree_path(*args, **kwargs)
        self.assertNotEqual(caught.exception.code, 0)
        lines = [line for line in error.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, f"expected one refusal line, got {lines}")
        return lines[0]

    # -- the deriver ----------------------------------------------------

    def test_plain_run_branch_derives_the_expected_path(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/worktree-demo")
        self.assertEqual(
            derived,
            os.path.join(self.root, "tmp", "fiat", "fiat-worktree-demo"),
        )

    def test_issue_backed_branch_keeps_its_leading_number(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/439-run-in-a-worktree")
        self.assertEqual(os.path.basename(derived), "fiat-439-run-in-a-worktree")

    def test_one_run_branch_maps_to_one_path(self):
        first = self.module.run_worktree_path(self.repo, "fiat/a-topic")
        second = self.module.run_worktree_path(self.repo, "fiat/a-topic")
        other = self.module.run_worktree_path(self.repo, "fiat/another-topic")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_deriver_creates_nothing(self):
        before = sorted(os.listdir(self.repo))
        derived = self.module.run_worktree_path(self.repo, "fiat/untouched")
        self.assertFalse(os.path.exists(derived))
        self.assertEqual(sorted(os.listdir(self.repo)), before)

    def test_a_target_that_is_not_a_repository_refuses(self):
        plain = os.path.join(self.dir, "not-a-repo")
        os.makedirs(plain)
        error = StringIO()
        with redirect_stderr(error):
            with self.assertRaises(SystemExit) as caught:
                self.module.run_worktree_path(plain, "fiat/topic")
        self.assertNotEqual(caught.exception.code, 0)
        self.assertIn("not a git repository", error.getvalue())

    # -- the validator --------------------------------------------------

    def test_a_fresh_derived_path_is_accepted(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/fresh")
        self.assertEqual(
            self.module.check_worktree_path(self.root, derived), derived
        )

    def test_this_runs_registered_worktree_is_accepted_when_it_exists(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/resumed")
        os.makedirs(derived)
        self.assertEqual(
            self.module.check_worktree_path(self.root, derived, registered=derived),
            derived,
        )

    def test_a_path_that_already_exists_as_a_file_refuses(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/occupied")
        os.makedirs(os.path.dirname(derived))
        with open(derived, "w", encoding="utf-8") as handle:
            handle.write("not a worktree")
        self.assertIn("occupied", self.refuse(self.root, derived))

    def test_a_path_that_already_exists_as_an_unrelated_directory_refuses(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/squatted")
        os.makedirs(derived)
        with open(os.path.join(derived, "someone-elses.txt"), "w", encoding="utf-8") as h:
            h.write("work")
        self.assertIn("occupied", self.refuse(self.root, derived))

    def test_a_path_escaping_the_root_by_dotdot_refuses(self):
        self.assertIn(
            "escapes", self.refuse(self.root, os.path.join("tmp", "fiat", "..", "..", "..", "away"))
        )

    def test_an_absolute_path_outside_the_repository_refuses(self):
        outside = os.path.join(self.dir, "outside")
        self.assertIn("escapes", self.refuse(self.root, outside))

    def test_a_component_symlink_leaving_the_repository_refuses(self):
        outside = os.path.join(self.dir, "elsewhere")
        os.makedirs(outside)
        home = os.path.join(self.root, "tmp")
        os.symlink(outside, home)
        derived = os.path.join(home, "fiat", "fiat-topic")
        self.assertIn("symlink", self.refuse(self.root, derived))

    def test_a_final_component_symlink_leaving_the_repository_refuses(self):
        outside = os.path.join(self.dir, "target")
        os.makedirs(outside)
        os.makedirs(os.path.join(self.root, "tmp", "fiat"))
        derived = os.path.join(self.root, "tmp", "fiat", "fiat-linked")
        os.symlink(outside, derived)
        self.assertIn("symlink", self.refuse(self.root, derived))

    def test_the_repository_root_itself_refuses(self):
        self.assertIn("escapes", self.refuse(self.root, self.root))

    def test_a_refusal_leaves_no_state_no_ledger_and_no_breadcrumb(self):
        before = sorted(os.listdir(self.repo))
        self.refuse(self.root, os.path.join(self.dir, "outside"))
        self.assertEqual(sorted(os.listdir(self.repo)), before)
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".hexaemeron")))

    def test_a_refusal_names_the_path_without_echoing_its_contents(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/secret")
        os.makedirs(os.path.dirname(derived))
        with open(derived, "w", encoding="utf-8") as handle:
            handle.write("SENSITIVE-TOKEN-VALUE")
        line = self.refuse(self.root, derived)
        self.assertIn("fiat-secret", line)
        self.assertNotIn("SENSITIVE-TOKEN-VALUE", line)

    def test_a_dangling_symlink_at_the_derived_path_refuses(self):
        """A link that resolves nowhere still occupies the path.

        Occupancy was read off the resolved target, and a dangling link resolves
        to a path that does not exist, so the check saw a free path. It then
        returned the link's target rather than the path it was asked about, which
        would put the run's tree somewhere the deriver never chose.
        """
        derived = self.module.run_worktree_path(self.repo, "fiat/dangling")
        os.makedirs(os.path.dirname(derived))
        os.symlink(os.path.join(self.root, "nowhere-yet"), derived)
        self.assertIn("symlink", self.refuse(self.root, derived))

    def test_a_symlink_to_a_real_directory_inside_the_repository_refuses(self):
        """The run's tree is a real directory at the derived path, or it is nothing."""
        derived = self.module.run_worktree_path(self.repo, "fiat/redirected")
        inside = os.path.join(self.root, "real-dir")
        os.makedirs(inside)
        os.makedirs(os.path.dirname(derived))
        os.symlink(inside, derived)
        self.assertIn("symlink", self.refuse(self.root, derived))


class WorktreeCreationTests(HexctlCase):
    """`init` arranges the run's isolation, so no run can forget to.

    The origin checkout is the thing under test as much as the worktree is: a run
    that leaves it on a branch it created, or with a `git status` it did not have
    before, has failed even if every receipt it wrote is correct.
    """

    def origin(self, *args):
        proc = subprocess.run(["git", *args], cwd=self.dir, capture_output=True,
                              text=True, check=True)
        return proc.stdout.strip()

    def worktree_entries(self):
        listing = self.origin("worktree", "list", "--porcelain")
        return [line[len("worktree "):] for line in listing.splitlines()
                if line.startswith("worktree ")]

    # -- what a successful init arranges ---------------------------------

    def test_init_creates_the_tree_and_the_run_branch(self):
        before = self.worktree_entries()
        self.init()
        after = self.worktree_entries()
        self.assertEqual(len(after), len(before) + 1)
        created = [entry for entry in after if entry not in before][0]
        self.assertEqual(os.path.realpath(created), os.path.realpath(self.target))
        self.assertEqual(
            self.origin("rev-parse", "--abbrev-ref", "HEAD"), "main"
        )
        self.assertEqual(
            subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           cwd=self.target, capture_output=True, text=True).stdout.strip(),
            "fiat/test-topic",
        )

    def test_the_runs_state_lands_in_the_tree_not_the_checkout(self):
        self.init()
        self.assertNotEqual(os.path.realpath(self.target), os.path.realpath(self.dir))
        self.assertTrue(os.path.exists(
            os.path.join(self.target, ".hexaemeron", "state.json")))
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, ".hexaemeron", "state.json")))

    def test_the_breadcrumb_names_the_tree(self):
        self.init()
        with open(os.path.join(self.dir, ".hexaemeron", "worktree"),
                  encoding="utf-8") as handle:
            recorded = handle.read().strip()
        self.assertEqual(os.path.realpath(recorded), os.path.realpath(self.target))

    def test_the_checkout_keeps_only_the_breadcrumb_and_the_lock(self):
        """The breadcrumb is the only thing the run itself writes there.

        The directory around it is the kernel lock's, taken before any command
        runs, and the self-ignoring `.gitignore` the controller has always
        written. No state, no ledger, and nothing git can see.
        """
        self.init()
        kept = sorted(os.listdir(os.path.join(self.dir, ".hexaemeron")))
        self.assertEqual(kept, [".gitignore", "lock", "worktree"])

    def test_init_prints_the_dir_to_use_next(self):
        proc = self.run_ctl("init", "--topic", "printed path")
        self.assertIn(f"hexctl --dir {self.target} next", proc.stdout)

    # -- what it leaves alone --------------------------------------------

    def test_the_origin_checkout_is_unchanged_across_a_successful_init(self):
        before_head = self.origin("rev-parse", "HEAD")
        before_branch = self.origin("rev-parse", "--abbrev-ref", "HEAD")
        before_status = self.origin("status", "--short")
        self.init()
        self.assertEqual(self.origin("rev-parse", "HEAD"), before_head)
        self.assertEqual(self.origin("rev-parse", "--abbrev-ref", "HEAD"), before_branch)
        self.assertEqual(self.origin("status", "--short"), before_status)

    def test_the_worktree_home_does_not_show_as_untracked(self):
        """The home ignores itself, so the promise does not depend on the
        target repository already ignoring `tmp/`."""
        before = self.origin("status", "--short")
        self.init()
        self.assertEqual(self.origin("status", "--short"), before)
        self.assertNotIn("tmp/", self.origin("status", "--short"))

    def test_a_run_starts_from_a_dirty_origin_checkout(self):
        """The dirty tree is no longer the run's tree, so it no longer blocks."""
        with open(os.path.join(self.dir, "operators-work.txt"), "w",
                  encoding="utf-8") as handle:
            handle.write("uncommitted\n")
        before_status = self.origin("status", "--short")
        self.assertIn("operators-work.txt", before_status)
        self.init()
        self.assertEqual(self.origin("status", "--short"), before_status)
        self.assertTrue(os.path.exists(
            os.path.join(self.target, ".hexaemeron", "state.json")))

    # -- what it refuses --------------------------------------------------

    def test_a_run_branch_already_checked_out_elsewhere_refuses(self):
        other = os.path.join(self.dir, "other-tree")
        subprocess.run(["git", "worktree", "add", "-q", "-b", "fiat/test-topic",
                        other, "main"], cwd=self.dir, check=True, capture_output=True)
        proc = self.run_ctl("init", "--topic", "test topic", expect=2)
        self.assertIn("already checked out", proc.stderr)
        self.assertIn(other, proc.stderr)
        self.assert_nothing_recorded()

    def test_a_failing_worktree_add_refuses(self):
        """A branch that exists but is checked out nowhere still stops `add -b`."""
        subprocess.run(["git", "branch", "fiat/test-topic"], cwd=self.dir,
                       check=True, capture_output=True)
        proc = self.run_ctl("init", "--topic", "test topic", expect=2)
        self.assertIn("could not create the run worktree", proc.stderr)
        self.assert_nothing_recorded()

    def test_a_target_that_is_not_a_repository_refuses(self):
        plain = tempfile.mkdtemp()
        try:
            proc = subprocess.run(
                [sys.executable, HEXCTL, "--dir", plain, "init", "--topic", "t"],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("not a git repository", proc.stderr)
            for name in ("state.json", "ledger.jsonl", "worktree"):
                self.assertFalse(
                    os.path.exists(os.path.join(plain, ".hexaemeron", name)), name
                )
        finally:
            shutil.rmtree(plain, ignore_errors=True)

    def assert_nothing_recorded(self):
        """A refusal leaves no state, no ledger, no breadcrumb and no tree."""
        state_dir = os.path.join(self.dir, ".hexaemeron")
        self.assertFalse(os.path.exists(os.path.join(state_dir, "worktree")))
        self.assertFalse(os.path.exists(os.path.join(state_dir, "state.json")))
        self.assertFalse(os.path.exists(os.path.join(state_dir, "ledger.jsonl")))
        derived = os.path.join(self.dir, "tmp", "fiat", "fiat-test-topic")
        self.assertFalse(os.path.exists(derived))

    def test_two_runs_against_one_repository_each_get_their_own_tree(self):
        """The issue asks for two runs that do not contend, not for a second
        run that is refused."""
        self.init("run alpha")
        alpha = self.target
        second = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "run beta"],
            capture_output=True, text=True,
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        beta = os.path.join(self.dir, "tmp", "fiat", "fiat-run-beta")
        self.assertNotEqual(os.path.realpath(alpha), os.path.realpath(beta))
        for tree, branch in ((alpha, "fiat/run-alpha"), (beta, "fiat/run-beta")):
            self.assertTrue(os.path.exists(os.path.join(tree, ".hexaemeron", "state.json")))
            self.assertEqual(
                subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=tree,
                               capture_output=True, text=True).stdout.strip(),
                branch,
            )
        self.assertEqual(self.origin("rev-parse", "--abbrev-ref", "HEAD"), "main")

    def test_the_breadcrumb_records_every_live_run(self):
        self.init("run alpha")
        subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "run beta"],
            capture_output=True, text=True, check=True,
        )
        with open(os.path.join(self.dir, ".hexaemeron", "worktree"),
                  encoding="utf-8") as handle:
            recorded = [line.strip() for line in handle if line.strip()]
        self.assertEqual(len(recorded), 2)
        self.assertEqual(
            sorted(os.path.basename(entry) for entry in recorded),
            ["fiat-run-alpha", "fiat-run-beta"],
        )

    def test_repeating_a_topic_refuses_and_names_the_existing_tree(self):
        self.init("run alpha")
        existing = self.target
        again = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "run alpha"],
            capture_output=True, text=True,
        )
        self.assertEqual(again.returncode, 2)
        self.assertIn(existing, again.stderr)
        self.assertIn("--dir", again.stderr)


class ResumeAndRetirementTests(HexctlCase):
    """Finding the run again, and putting its tree away once it has landed."""

    def origin_ctl(self, *args):
        return subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, *args],
            capture_output=True, text=True,
        )

    def state_dir_listing(self):
        return sorted(os.listdir(os.path.join(self.dir, ".hexaemeron")))

    # -- resume -----------------------------------------------------------

    def test_status_from_the_checkout_names_the_runs_worktree(self):
        self.init()
        proc = self.origin_ctl("status")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(self.target, proc.stderr)
        self.assertIn(f"hexctl --dir {self.target} next", proc.stderr)

    def test_next_from_the_checkout_names_the_runs_worktree(self):
        self.init()
        proc = self.origin_ctl("next")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(f"hexctl --dir {self.target} next", proc.stderr)

    def test_pointing_at_the_checkout_changes_nothing(self):
        self.init()
        before = self.state_dir_listing()
        self.origin_ctl("status")
        self.origin_ctl("next")
        self.assertEqual(self.state_dir_listing(), before)
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, ".hexaemeron", "state.json")))

    def test_both_runs_are_named_when_the_checkout_started_two(self):
        self.init("run alpha")
        alpha = self.target
        subprocess.run([sys.executable, HEXCTL, "--dir", self.dir, "init",
                        "--topic", "run beta"], capture_output=True, check=True)
        beta = os.path.join(self.dir, "tmp", "fiat", "fiat-run-beta")
        proc = self.origin_ctl("status")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(alpha, proc.stderr)
        self.assertIn(beta, proc.stderr)

    def test_a_recorded_worktree_that_is_gone_refuses_by_name(self):
        self.init()
        recorded = self.target
        shutil.rmtree(recorded)
        proc = self.origin_ctl("status")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(recorded, proc.stderr)
        self.assertIn("no longer there", proc.stderr)

    def test_a_recorded_worktree_that_is_gone_does_not_start_a_second_run(self):
        self.init()
        shutil.rmtree(self.target)
        self.origin_ctl("next")
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, ".hexaemeron", "state.json")))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "tmp", "fiat",
                                                     "fiat-test-topic")))

    def test_state_already_in_a_checkout_still_resumes(self):
        """A run that predates the worktree keeps working where it is."""
        legacy = os.path.join(self.dir, ".hexaemeron")
        os.makedirs(legacy, exist_ok=True)
        self.init()
        shutil.copytree(os.path.join(self.target, ".hexaemeron"),
                        legacy, dirs_exist_ok=True)
        os.remove(os.path.join(legacy, "worktree"))
        proc = self.origin_ctl("status", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["topic"], "test topic")

    # -- retirement -------------------------------------------------------

    def land_a_run(self):
        """A one-step run, driven all the way to the integrate phase."""
        self.to_steps(titles=("Scaffold",))
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.finish_step(1)

    def test_reset_removes_a_clean_tree_and_archives_its_evidence(self):
        self.land_a_run()
        self.integrate_run()
        self.assertTrue(os.path.isdir(self.retired),
                        "integrate leaves the tree so status and verify still run")
        self.run_ctl("reset")
        self.assertFalse(os.path.isdir(self.retired))
        archives = os.listdir(os.path.join(self.dir, ".hexaemeron", "archive"))
        self.assertEqual(len(archives), 1)
        archived = os.path.join(self.dir, ".hexaemeron", "archive", archives[0])
        for name in ("state.json", "ledger.jsonl"):
            self.assertTrue(os.path.exists(os.path.join(archived, name)), name)

    def test_the_integrate_receipt_records_the_tree_as_clean(self):
        self.land_a_run()
        self.integrate_run()
        self.assertIs(self.state()["receipts"]["integrate"]["worktree_clean"], True)

    def test_a_tree_holding_work_is_kept_and_never_forced(self):
        self.land_a_run()
        held = self.target
        with open(os.path.join(held, "someone-was-working.txt"), "w",
                  encoding="utf-8") as handle:
            handle.write("do not lose me\n")
        self.integrate_run()
        self.run_ctl("reset")
        self.assertTrue(os.path.isdir(held))
        self.assertTrue(os.path.exists(
            os.path.join(held, "someone-was-working.txt")))
        archives = os.listdir(os.path.join(self.dir, ".hexaemeron", "archive"))
        self.assertEqual(len(archives), 1)

    def test_a_retired_run_drops_out_of_the_breadcrumb(self):
        self.land_a_run()
        self.integrate_run()
        self.run_ctl("reset")
        with open(os.path.join(self.dir, ".hexaemeron", "worktree"),
                  encoding="utf-8") as handle:
            self.assertEqual(handle.read().strip(), "")

    @property
    def retired(self):
        return os.path.join(self.dir, "tmp", "fiat", "fiat-test-topic")
