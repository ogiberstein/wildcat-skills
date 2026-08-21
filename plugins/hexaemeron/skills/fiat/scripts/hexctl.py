#!/usr/bin/env python3
"""hexctl - deterministic, receipt-backed controller for the one-shot loop.

The model does the work; this script decides what comes next and refuses to
advance without a receipt. State lives in `.hexaemeron/state.json` beside an
append-only, hash-chained ledger (`.hexaemeron/ledger.jsonl`). Every mutating
command appends a ledger entry, so `verify` can prove the run history was not
edited after the fact.

Phase order is fixed. Globally: study -> runbook -> steps -> integrate -> done.
Within each step: implement -> audit -> prose -> push. Step branches chain off
one another and their pull requests stack; nothing merges while the steps run.
The integrate phase merges the stack into the run branch in step order, then
merges the run branch into the recorded base exactly once and closes any
recorded task issue.

Exit codes: 0 success, 2 validation/usage error, 1 unexpected failure.
Stdout from `next` and `status --json` is a single JSON object; everything
human-facing goes to plain text or stderr.
"""

import argparse
import contextlib
import datetime
import fcntl
import glob
import hashlib
import json
import os
import re
import selectors
import subprocess
import sys
import time

STATE_DIR_NAME = ".hexaemeron"
STATE_FILE = "state.json"
LEDGER_FILE = "ledger.jsonl"

# The run-level pull request body the prose phase writes and the integrate
# phase opens the integration pull request from. It is the last thing a run
# writes into the repository, so it is where the work a run gave up on has to
# be named: the next study over the same target reads it as prior art.
RUN_PR_FILE = "run-pr.md"
CARRIED_FORWARD_HEADING = "## Carried forward"

# ``issue`` remains accepted only so runs created by older controllers can
# advance directly into implementation without losing their ledger history.
STEP_PHASES = ["issue", "implement", "audit", "prose", "push"]
GLOBAL_PHASES = ["study", "runbook", "steps", "integrate", "done"]

# Decorative only: the day each phase maps to in the plugin's naming conceit.
DAY = {
    "study": 1,
    "runbook": 2,
    "issue": 3,
    "implement": 4,
    "audit": 5,
    "prose": 6,
    "push": 7,
}

DEFAULT_CONFIG = {
    "skills": {
        "prose_lint": "hexaemeron:imprimatur",
        "voice": "hexaemeron:vulgate",
        # The Pashov suite is vendored in this plugin. Preflight records
        # these ids via `record security_suite ...` -- the controller gates
        # the audit phase on that receipt, not on this list.
        "security": [
            "hexaemeron:x-ray",
            "hexaemeron:solidity-auditor",
            "hexaemeron:fizz",
        ],
    },
    "audit": {
        "max_rounds": 8,
        "stacked_suffix": "--audit",
        "fold": False,
        "log_path": "audit/AUDIT.md",
    },
    "git": {
        "base": "main",
        "run_branch_prefix": "fiat/",
        "draft_pr": False,
    },
    "solidity": "auto",
}

LINTS = ("phylax", "ephoros", "hypomnema")
"""The three bundled lints a non-Solidity audit round runs.

Named here so the flags, the refusal message and the stored round all read from one
list. `references/audit-loop.md` is the contract they satisfy.
"""

SOLIDITY_MODES = ("auto", True, False)
"""What `config solidity` accepts.

`auto` reads the answer off the `security_suite` receipt, which is where the run
already recorded whether the Pashov pair applies. `true` and `false` force it, for a
repository where the receipt does not tell the truth about the diff.
"""


def solidity_mode(value) -> bool:
    """True when a value is one of the three modes.

    Checked by identity rather than by `in SOLIDITY_MODES`, because Python makes
    `1 == True` and `0 == False`, so membership would accept an integer as a mode and
    store it. `config set solidity 1` is a caller error, not a way to spell `true`.
    """
    if isinstance(value, bool):
        return True
    return value == "auto"

WAIVER_PREFIX = "waived"
"""How a `security_suite` receipt says the Pashov pair did not run.

One rule, so the classifier never guesses: the receipt is a waiver when it is a string
whose first word is this, ignoring case and surrounding space. Preflight writes
`"waived: <reason>"`, and a reason is the point of the string.
"""

def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


SOURCE_BYTES_MAX = 2 * 1024 * 1024
GIT_OUTPUT_MAX = 2 * 1024 * 1024
GIT_PATHS_MAX = 500
GIT_TIMEOUT = 30


def scoped_path(base_dir: str, supplied: str, label: str) -> str:
    """Resolve one path and refuse anything outside the target directory."""
    root = os.path.realpath(base_dir)
    candidate = supplied if os.path.isabs(supplied) else os.path.join(root, supplied)
    resolved = os.path.realpath(candidate)
    try:
        inside = os.path.commonpath((root, resolved)) == root
    except ValueError:
        inside = False
    if not inside:
        die(f"{label} escapes target directory: {supplied}")
    return resolved


def read_bounded_source(base_dir: str, supplied: str, label: str) -> tuple[str, bytes]:
    """Read a source artefact once, with containment and a hard byte ceiling."""
    path = scoped_path(base_dir, supplied, label)
    if not os.path.isfile(path):
        die(f"{label} is not a regular file: {supplied}")
    try:
        with open(path, "rb") as handle:
            data = handle.read(SOURCE_BYTES_MAX + 1)
    except OSError as exc:
        die(f"{label} cannot be read: {exc}")
    if len(data) > SOURCE_BYTES_MAX:
        die(f"{label} exceeds {SOURCE_BYTES_MAX}-byte cap")
    return path, data


def decoded_source(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        die(f"{label} is not UTF-8 text")


def plugin_root() -> str:
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def die(msg: str, code: int = 2) -> None:
    print(f"hexctl: error: {msg}", file=sys.stderr)
    sys.exit(code)


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def as_dict(value) -> dict:
    """A mapping, or an empty one.

    `d.get(key, {})` returns the stored value when the key exists, so a state holding
    `"integrate": null` defeats the default and the next `.get` raises. `load_state`
    validates no shape, so this is the guard every chained read here needs.
    """
    return value if isinstance(value, dict) else {}


def is_waiver(value) -> bool:
    """True when a `security_suite` receipt says the Pashov pair did not run.

    The first word has to be the prefix, not merely start with it: `startswith` alone
    read `waivedX` and `waived-ish` as waivers, which the rule beside `WAIVER_PREFIX`
    does not say. Both currently land on the same answer by another route, so the
    mismatch was invisible; it would stop being invisible the moment a message
    explained which branch it took.
    """
    if not isinstance(value, str):
        return False
    first = value.strip().lower().replace(":", " ").split()
    return bool(first) and first[0] == WAIVER_PREFIX


def solidity_round(state: dict) -> bool:
    """Whether this run's audit rounds are Solidity rounds.

    False means the round's mechanical part is the three bundled lints, so
    `audit-round` requires their exit statuses.

    Under `auto` the answer comes from the `security_suite` receipt: a waiver means no
    Solidity, a non-empty list of suite ids means Solidity. Anything else -- an empty
    list, a number, an object -- is not a suite that ran, so it is treated as a
    non-Solidity round and the lints are required. Demanding more evidence is the safe
    direction when the receipt cannot be read.

    A missing receipt reads as Solidity, because nothing can be inferred from it.
    `cmd_audit_round` refuses a missing receipt before ever asking this.

    A state file whose `config` or `receipts` is not an object is read as though the
    key were absent rather than allowed to raise. `load_state` validates no shape, so a
    hand-edited or half-written state reaches this function, and a traceback out of the
    controller is a worse answer than the one every other fault here gets.
    """
    mode = as_dict(state.get("config")).get("solidity", "auto")
    if mode is True or mode is False:
        return mode
    receipts = as_dict(state.get("receipts"))
    if "security_suite" not in receipts:
        return True
    suite = receipts["security_suite"]
    if is_waiver(suite):
        return False
    return isinstance(suite, list) and bool(suite)


# ------------------------------------------------------------------ branches

SLUG_RE = re.compile(r"[^a-z0-9]+")

# Conservative subset of git's refname rules: no whitespace, no traversal, no
# leading or trailing separator, nothing that needs quoting in a shell.
BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*[A-Za-z0-9]$")


def slug(text: str, limit: int = 48) -> str:
    return SLUG_RE.sub("-", text.lower()).strip("-")[:limit].strip("-")


def check_branch_name(name: str) -> None:
    if not BRANCH_RE.match(name) or ".." in name or "//" in name:
        die(f"'{name}' is not a usable branch name")
    if name.endswith(".lock"):
        die(f"'{name}' is not a usable branch name")


def run_branch_of(state: dict):
    """The run's integration branch, or None for a run started before 3.4."""
    return state.get("run_branch")


def step_branch_name(state: dict, step: dict) -> str:
    """Descriptive chained step branch: run slug, step number, step title.

    A sibling of the run branch rather than a child of it, because git cannot
    hold `fiat/x` and `fiat/x/step-1-y` as refs at the same time.
    """
    tail = slug(step["title"], 32) or "untitled"
    return f"{run_branch_of(state)}-step-{step['n']}-{tail}"


def step_pr_base(state: dict, step: dict) -> str:
    """A step stacks on the step below it; step 1 stacks on the run branch."""
    if step["n"] <= 1:
        return run_branch_of(state)
    return step_branch_name(state, state["steps"][step["n"] - 2])


def branch_plan(state: dict, step: dict) -> dict:
    """Branch to cut and pull request base for a step, when the run has a run
    branch. A pre-3.4 run gets nothing here and keeps its old freedom."""
    if not run_branch_of(state):
        return {}
    parent = step_pr_base(state, step)
    return {
        "run_branch": run_branch_of(state),
        "branch": step_branch_name(state, step),
        "branch_from": parent,
        "pr_base": parent,
        "merge_now": False,
    }


def expected_task_issue(state: dict):
    task_issue = state["receipts"].get("task_issue")
    if isinstance(task_issue, str):
        return task_issue
    if isinstance(task_issue, dict):
        return task_issue.get("url")
    return None


# ---------------------------------------------------------------- state io

def state_root(base_dir: str) -> str:
    return os.path.join(base_dir, STATE_DIR_NAME)


def state_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), STATE_FILE)


def ledger_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), LEDGER_FILE)


def run_pr_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), RUN_PR_FILE)


def load_state(base_dir: str) -> dict:
    path = state_path(base_dir)
    if not os.path.exists(path):
        die(f"no state at {path}; run `hexctl init --topic ...` first")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, OSError) as exc:
        die(f"state file unreadable at {path}: {exc}", 1)


MUTATING = frozenset(
    {
        "cmd_init",
        "cmd_record",
        "cmd_config",
        "cmd_done",
        "cmd_audit_round",
        "cmd_halt",
        "cmd_resume",
        "cmd_reset",
    }
)
"""Commands that write. `status`, `next` and `verify` only read, and blocking
them would stop a second agent from finding out why it is blocked."""


def lock_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), "lock")


def read_holder(descriptor: int) -> dict:
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        data = os.read(descriptor, 4096)
        return json.loads(data.decode("utf-8")) if data else {}
    except (UnicodeDecodeError, ValueError, OSError):
        return {}


def holder_is_alive(pid) -> bool:
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def read_live_holder(descriptor: int) -> dict:
    """Wait briefly for a new owner to replace metadata left by a crash."""
    holder = {}
    for _ in range(50):
        holder = read_holder(descriptor)
        if holder_is_alive(holder.get("pid")):
            break
        time.sleep(0.002)
    return holder


@contextlib.contextmanager
def held_lock(base_dir: str, command: str):
    """Hold the run for the length of one mutating command.

    The ledger is a read-modify-write: an entry takes the previous entry's
    hash as its parent. Two commands interleaving there produce two entries
    claiming the same parent, and `verify` reports the chain as broken
    afterwards. This turns that into a refusal beforehand.

    The kernel owns the exclusion. It releases the lock when a process exits,
    including after a crash, so stale metadata never needs to be unlinked and
    two contenders cannot both reclaim it. The file remains as an ignored
    place to publish holder details for a refused writer.
    """
    root = state_root(base_dir)
    if not os.path.isdir(root):
        # Only `init` legitimately runs without a state directory, and it
        # creates one. Anything else is about to fail with a better message
        # than a lock could give, so do not litter the directory to say so.
        if command != "cmd_init":
            yield
            return
        os.makedirs(root, exist_ok=True)

    path = lock_path(base_dir)
    fd = os.open(
        path,
        os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0),
        0o644,
    )
    acquired = False

    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError:
            holder = read_live_holder(fd)
            die(
                "another hexctl is holding this run: pid {pid} running "
                "`{cmd}` since {since}.\n"
                "Two agents in one directory share one run and one ledger. "
                "Give each its own working directory, for example "
                "`git worktree add ../<name> main`, and run one there.".format(
                    pid=holder.get("pid", "unknown"),
                    cmd=holder.get("command", "unknown"),
                    since=holder.get("ts", "unknown"),
                ),
                1,
            )
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(
            fd,
            json.dumps(
                {"pid": os.getpid(), "command": command, "ts": now()}
            ).encode()
            + b"\n",
        )
        os.fsync(fd)
        yield
    finally:
        if acquired:
            try:
                os.ftruncate(fd, 0)
                os.fsync(fd)
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        else:
            os.close(fd)


def save_state(base_dir: str, state: dict) -> None:
    path = state_path(base_dir)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def state_fingerprint(state: dict) -> str:
    return hashlib.sha256(canonical(state).encode()).hexdigest()


def append_ledger(base_dir: str, event: str, data: dict, state_hash: str) -> None:
    path = ledger_path(base_dir)
    prev = "genesis"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        if lines:
            try:
                prev = json.loads(lines[-1])["hash"]
            except (ValueError, KeyError, TypeError):
                die("ledger corrupt: last entry unreadable; run `hexctl verify`", 1)
    entry = {
        "ts": now(),
        "event": event,
        "data": data,
        "prev": prev,
        "state": state_hash,
    }
    entry["hash"] = hashlib.sha256(canonical(entry).encode()).hexdigest()
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def commit(base_dir: str, state: dict, event: str, data: dict) -> None:
    append_ledger(base_dir, event, data, state_fingerprint(state))
    save_state(base_dir, state)


# ------------------------------------------------------------- step helpers

def current_step(state: dict) -> dict:
    n = state.get("current_step")
    if n is None:
        die("no step is open")
    for step in state["steps"]:
        if step["n"] == n:
            return step
    die(f"state corrupt: current_step={n} not found; run `hexctl verify`", 1)


def require_global_phase(state: dict, phase: str) -> None:
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state["phase"] != phase:
        die(f"out of order: expected phase '{state['phase']}', got '{phase}'")


def require_step_phase(state: dict, phase: str) -> dict:
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state["phase"] != "steps":
        die(f"out of order: run is in phase '{state['phase']}', not working steps")
    step = current_step(state)
    if step["phase"] != phase:
        die(
            f"out of order: step {step['n']} is in phase '{step['phase']}', "
            f"got 'done {phase}'"
        )
    return step


def max_rounds_of(state: dict) -> int:
    raw = state["config"]["audit"]["max_rounds"]
    try:
        val = int(raw)
    except (TypeError, ValueError):
        die(f"config audit.max_rounds must be an integer >= 1 (got {raw!r})")
    if val < 1:
        die(f"config audit.max_rounds must be >= 1 (got {val})")
    return val


def parse_value(raw: str):
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


# ------------------------------------------------------------------ commands

def cmd_init(args) -> None:
    root = state_root(args.dir)
    if os.path.exists(state_path(args.dir)):
        die(f"state already exists at {root}; resume with `hexctl next`")
    os.makedirs(root, exist_ok=True)
    # Self-ignoring: git never sees the state directory even in repos whose
    # .gitignore was not touched. Nested .gitignore with `*` covers it.
    with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as fh:
        fh.write("*\n")
    prefix = DEFAULT_CONFIG["git"]["run_branch_prefix"]
    run_branch = args.run_branch or f"{prefix}{slug(args.topic) or 'run'}"
    check_branch_name(run_branch)
    if run_branch == args.base:
        die("--run-branch must differ from --base; the run needs its own branch")
    frontier = None
    if args.frontier:
        ledger = args.frontier if os.path.isabs(args.frontier) else \
            os.path.join(args.dir, args.frontier)
        if not os.path.isfile(ledger):
            die(f"--frontier {args.frontier} is not a file; name the target "
                f"skill's EVOLUTION.md")
        with open(ledger, encoding="utf-8") as fh:
            text = fh.read()
        if ledger_field(text, "Current version") is None:
            die(f"--frontier {args.frontier} states no `Current version`; it "
                f"does not look like a governed ledger")
        frontier = {
            "ledger": os.path.relpath(ledger, args.dir),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "rows": len(ledger_rows(text)),
            "version_at_init": ledger_field(text, "Current version"),
        }

    state = {
        "version": 1,
        "controller": "hexctl",
        "topic": args.topic,
        "base": args.base,
        "run_branch": run_branch,
        "created_at": now(),
        "phase": "study",
        "current_step": None,
        "steps": [],
        "receipts": {},
        "config": json.loads(json.dumps(DEFAULT_CONFIG)),
        "halted": None,
        "frontier": frontier,
    }
    commit(
        args.dir,
        state,
        "init",
        {"topic": args.topic, "base": args.base, "run_branch": run_branch},
    )
    print(
        f"initialised {root} (topic: {args.topic}); "
        f"run branch {run_branch} off {args.base}"
    )
    if frontier is not None:
        print(
            f"frontier run: {frontier['ledger']} at {frontier['version_at_init']}, "
            f"{frontier['rows']} row(s). `done integrate` refuses until it "
            f"carries exactly one new valid row."
        )
    stale = stale_controller(args.dir)
    if stale is not None:
        running, checked_in, path = stale
        print(
            f"hexctl: warning: this controller is {running}, and {path} in the "
            f"target repository is {checked_in}. The run will use the older "
            f"one, so a receipt it cannot record is a gap in this run's "
            f"evidence rather than a rule that does not exist. Follow "
            f"references/plugin-currency.md: update the plugin through this "
            f"host's own installer, refresh, and re-resolve the paths, or "
            f"record a controller_version receipt saying why that could not "
            f"happen.",
            file=sys.stderr,
        )


def ledger_version(evolution_md: str) -> str | None:
    """The `Current version` a skill's EVOLUTION.md declares."""
    try:
        with open(evolution_md, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("- Current version:"):
                    return line.split(":", 1)[1].strip().strip("`") or None
    except OSError:
        return None
    return None


LEDGER_ROW = re.compile(
    r"^\| `(?P<version>[^`]+)` \| (?P<axis>baseline|evolution|generation|epoch) "
    r"\| `(?P<revision>[^`]+)` \| `(?P<digest>[0-9a-f]{64})` "
    r"\| (?P<evidence>.*?) \| (?P<change>.*?) \|$"
)
"""One history row. Deliberately the same shape tests/test_evolution_contract.py
matches, so the gate and the suite cannot disagree about what a row is."""

LEDGER_AXES = ("baseline", "evolution", "generation", "epoch")


def ledger_rows(text: str) -> list[dict]:
    return [m.groupdict() for m in
            (LEDGER_ROW.fullmatch(line) for line in text.splitlines()) if m]


def ledger_field(text: str, name: str) -> str | None:
    match = re.search(rf"(?m)^- {re.escape(name)}: (.+)$", text)
    return match.group(1).strip().strip("`") if match else None


def ledger_frontier_digest(text: str) -> str | None:
    """SHA-256 over the four-field canonical line, including its newline."""
    fields = [ledger_field(text, name) for name in
              ("Frontier status", "Frontier revision", "Current frontier",
               "Next Fiat job")]
    if any(f is None for f in fields):
        return None
    return hashlib.sha256(("|".join(fields) + "\n").encode("utf-8")).hexdigest()


def _label_parts(label: str, skill: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(rf"{re.escape(skill)}-v(\d+)\.(\d+)\.(\d+)", label)
    return tuple(int(g) for g in match.groups()) if match else None


def carried_forward_lines(text: str) -> list[str] | None:
    """The lines under the carried-forward heading, or None when it is absent.

    Reading stops at the next heading, so a later section cannot stand in for
    this one.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != CARRIED_FORWARD_HEADING:
            continue
        said = []
        for candidate in lines[index + 1:]:
            if candidate.startswith("#"):
                break
            if candidate.strip():
                said.append(candidate.strip())
        return said
    return None


def carried_forward_fault(path: str) -> str | None:
    """Why this run has not said what it leaves unfinished, or None.

    A run that gives up on something records it in the body of the last pull
    request it lands, because that is what the next study reads. A run that
    finished everything still writes the section: an absent heading cannot be
    told apart from a question nobody asked.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return (f"the run-level pull request body {path} cannot be read "
                f"({exc}); the prose phase writes it and the integration pull "
                f"request is opened from it")

    said = carried_forward_lines(text)
    if said is None:
        return (f"{path} has no '{CARRIED_FORWARD_HEADING}' section; name every "
                f"lead left unpursued, finding accepted rather than fixed, "
                f"boundary refused and claim left unverified, or say plainly "
                f"that this run leaves none")
    if not said:
        return (f"{path} carries a '{CARRIED_FORWARD_HEADING}' heading with "
                f"nothing under it; say what is unfinished, or say that "
                f"nothing is")
    return None


def carried_forward_record(path: str) -> dict:
    """What the receipt keeps about the section, once it has passed."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return {
        "path": os.path.join(STATE_DIR_NAME, RUN_PR_FILE),
        "lines": len(carried_forward_lines(text) or []),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def frontier_close_fault(path: str, before: dict) -> str | None:
    """Why this run has not closed the frontier it declared, or None.

    The maturity gate says to update the ledger exactly once, and says it in
    prose. This repository has already had to reconstruct two broken evolutions,
    so the run proves the update instead of asserting it.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return f"the declared ledger {path} cannot be read ({exc})"

    if hashlib.sha256(text.encode("utf-8")).hexdigest() == before["sha256"]:
        return (f"{path} is byte-for-byte what it was at init; a completed "
                f"frontier job records one new row")

    rows = ledger_rows(text)
    gained = len(rows) - before["rows"]
    if gained != 1:
        return (f"{path} gained {gained} history row(s); the contract allows "
                f"exactly one per completed frontier job")

    row = rows[-1]
    skill = os.path.basename(os.path.dirname(path))
    current = ledger_field(text, "Current version")
    if row["version"] != current:
        return (f"the new row is {row['version']} and the header says "
                f"{current}; they have to be the same row")
    if row["revision"] != ledger_field(text, "Frontier revision"):
        return (f"the new row's revision {row['revision']!r} is not the "
                f"header's {ledger_field(text, 'Frontier revision')!r}")

    expected = ledger_frontier_digest(text)
    if expected is None:
        return f"{path} is missing one of the four frontier header fields"
    if row["digest"] != expected:
        return (f"the new row's digest does not match the frontier line it "
                f"describes; recomputed {expected[:16]}...")

    parts = _label_parts(row["version"], skill)
    prior = rows[-2] if len(rows) > 1 else None
    if parts is None:
        return f"{row['version']} is not a valid label for {skill}"
    if prior is not None:
        before_parts = _label_parts(prior["version"], skill)
        if before_parts is None:
            return f"the previous row {prior['version']} is not a valid label"
        axis, bumped = row["axis"], None
        if axis == "evolution":
            bumped = (before_parts[0] + 1, before_parts[1], before_parts[2])
        elif axis == "generation":
            bumped = (before_parts[0], before_parts[1] + 1, before_parts[2])
            if row["revision"] != prior["revision"]:
                return "a generation entry must retain the prior frontier revision"
            if row["digest"] != prior["digest"]:
                return "a generation entry must retain the prior frontier digest"
        elif axis == "epoch":
            bumped = (before_parts[0], before_parts[1], before_parts[2] + 1)
            if row["digest"] != prior["digest"] and \
                    "reopen" not in (row["evidence"] + row["change"]).lower():
                return "an epoch entry that moves the frontier must record the reopening"
        if bumped is not None and parts != bumped:
            article = "an" if axis[0] in "aeiou" else "a"
            return (f"{article} {axis} entry from {prior['version']} must be "
                    f"{skill}-v{bumped[0]}.{bumped[1]}.{bumped[2]}, not "
                    f"{row['version']}")

    status = ledger_field(text, "Frontier status")
    next_job = ledger_field(text, "Next Fiat job")
    if status not in ("open", "mature"):
        return f"frontier status {status!r} is neither open nor mature"
    if status == "mature" and next_job != "None -- mature":
        return "a mature frontier's next job has to be `None -- mature`"
    if status == "open" and next_job == "None -- mature":
        return "an open frontier cannot hold `None -- mature` as its next job"
    return None


def stale_controller(target_dir: str) -> tuple[str, str, str] | None:
    """Whether the running Fiat is older than a copy checked into the target.

    A marketplace plugin is installed from a published copy, so a repository
    that also holds Fiat's source can be a whole evolution ahead of the
    controller driving the run. Every rule the newer one enforces then goes
    unenforced silently, which is the one failure mode a receipt cannot show:
    the missing flag looks like a rule that was never written.

    Returns (running label, checked-in label, repo-relative path), or None when
    there is nothing to compare or the two agree.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    running = ledger_version(os.path.join(here, os.pardir, "EVOLUTION.md"))
    if running is None:
        return None
    for candidate in sorted(
        glob.glob(
            os.path.join(target_dir, "plugins", "*", "skills", "fiat", "EVOLUTION.md")
        )
    ):
        if os.path.realpath(candidate) == os.path.realpath(
            os.path.join(here, os.pardir, "EVOLUTION.md")
        ):
            continue  # the run's target is the plugin's own source tree
        checked_in = ledger_version(candidate)
        if checked_in is not None and checked_in != running:
            return running, checked_in, os.path.relpath(candidate, target_dir)
    return None


RESERVED_RECEIPTS = {"study", "runbook"}


def cmd_record(args) -> None:
    state = load_state(args.dir)
    if args.key in RESERVED_RECEIPTS:
        die(f"'{args.key}' is a phase receipt; only `hexctl done {args.key}` writes it")
    if state.get("halted") and args.key != "halt_note":
        # Recording context while halted is allowed; progress commands are not.
        pass
    value = parse_value(args.value)
    state["receipts"][args.key] = value
    commit(args.dir, state, "record", {"key": args.key, "value": value})
    print(f"recorded {args.key}")


def cmd_config(args) -> None:
    state = load_state(args.dir)
    node = state["config"]
    parts = args.path.split(".")
    if args.action == "get":
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                die(f"config path not found: {args.path}")
            node = node[part]
        print(json.dumps(node))
        return
    if not args.value:
        die("config set requires a value")
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            die(f"config path not found: {args.path}")
        node = node[part]
    leaf = parts[-1]
    if not isinstance(node, dict) or leaf not in node:
        die(f"config path not found: {args.path}")
    value = parse_value(args.value)
    if args.path == "solidity" and not solidity_mode(value):
        die(
            "config solidity takes %s; got %r"
            % (", ".join(json.dumps(m) for m in SOLIDITY_MODES), value)
        )
    node[leaf] = value
    commit(args.dir, state, "config-set", {"path": args.path, "value": node[leaf]})
    print(f"set {args.path}")


def _require_file(path: str, label: str) -> str:
    if not path:
        die(f"--{label} is required")
    if not os.path.exists(path):
        die(f"{label} not found on disk: {path}")
    return path


def done_study(args, state: dict) -> None:
    require_global_phase(state, "study")
    artifact = _require_file(args.artifact, "artifact")
    _, artifact_bytes = read_bounded_source(args.dir, artifact, "study artefact")
    skills = [s for s in (args.skills or "").split(",") if s]
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    state["receipts"]["study"] = {
        "artifact": artifact,
        "sha256": digest,
        "skills": skills,
    }
    state["phase"] = "runbook"
    commit(
        args.dir,
        state,
        "done:study",
        {"artifact": artifact, "sha256": digest, "skills": skills},
    )
    print("study receipted; phase -> runbook")


def done_runbook(args, state: dict) -> None:
    require_global_phase(state, "runbook")
    artifact = _require_file(args.artifact, "artifact")
    _, artifact_bytes = read_bounded_source(args.dir, artifact, "runbook artefact")
    steps_file = _require_file(args.steps_file, "steps-file")
    _, steps_bytes = read_bounded_source(args.dir, steps_file, "steps file")
    try:
        raw = json.loads(decoded_source(steps_bytes, "steps file"))
    except ValueError as exc:
        die(f"steps-file is not valid JSON: {exc}")
    if not isinstance(raw, list) or not raw:
        die("steps-file must be a non-empty JSON list")
    titles = []
    for item in raw:
        if isinstance(item, str):
            titles.append(item)
        elif isinstance(item, dict) and isinstance(item.get("title"), str):
            titles.append(item["title"])
        else:
            die("each step must be a string or an object with a 'title'")
    if any(not title.strip() for title in titles):
        die("step titles must be non-empty")
    state["steps"] = [
        {
            "n": i + 1,
            "title": title,
            "status": "pending",
            "phase": None,
            "receipts": {},
            "audit": {"rounds": []},
        }
        for i, title in enumerate(titles)
    ]
    state["steps"][0]["status"] = "open"
    state["steps"][0]["phase"] = "implement"
    state["current_step"] = 1
    state["phase"] = "steps"
    receipt = {"artifact": artifact, "steps": titles}
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    state["receipts"]["runbook"] = {
        "artifact": artifact,
        "sha256": digest,
        "step_count": len(titles),
    }
    receipt["sha256"] = digest
    commit(args.dir, state, "done:runbook", receipt)
    print(f"runbook receipted; {len(titles)} steps registered; step 1 -> implement")


def done_implement(args, state: dict) -> None:
    # Runs created before issue-free Fiat may still be parked at ``issue``.
    # Treat that legacy phase as implementation-ready and retire it in the
    # implementation receipt rather than forcing a GitHub side effect.
    step = current_step(state)
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state["phase"] != "steps" or step["phase"] not in ("issue", "implement"):
        require_step_phase(state, "implement")
    legacy_phase = step["phase"] == "issue"
    if not args.branch or not args.commit:
        die("--branch and --commit are required")
    if run_branch_of(state):
        expected = step_branch_name(state, step)
        if args.branch != expected:
            die(
                f"--branch must be '{expected}', chained off "
                f"'{step_pr_base(state, step)}'; got '{args.branch}'"
            )
    step["receipts"]["implement"] = {
        "branch": args.branch,
        "commit": args.commit,
        "tests": args.tests,
    }
    step["phase"] = "audit"
    commit(
        args.dir,
        state,
        "done:implement",
        {
            "step": step["n"],
            "branch": args.branch,
            "commit": args.commit,
            "legacy_issue_phase_skipped": legacy_phase,
        },
    )
    print(f"step {step['n']} implementation receipted; phase -> audit")


def cmd_audit_round(args) -> None:
    state = load_state(args.dir)
    step = require_step_phase(state, "audit")
    if "security_suite" not in state["receipts"]:
        die(
            "no security_suite receipt; resolve the installed suite first "
            "(`hexctl record security_suite '<ids or waived:reason>'`)"
        )
    rounds = step["audit"]["rounds"]
    max_rounds = max_rounds_of(state)
    if len(rounds) >= max_rounds:
        die(
            f"max audit rounds ({max_rounds}) reached for step {step['n']}; "
            "close with `done audit --no-further-leads --reason ...` or `halt`"
        )
    if args.findings is None or args.findings < 0:
        die("--findings must be a non-negative integer")

    exits = {lint: getattr(args, f"{lint}_exit", None) for lint in LINTS}
    for lint, value in exits.items():
        if value is not None and value < 0:
            die(f"--{lint}-exit must be a non-negative exit status, got {value}")

    if not solidity_round(state):
        absent = [f"--{lint}-exit" for lint in LINTS if exits[lint] is None]
        if absent:
            one = len(absent) == 1
            die(
                "this round runs the three bundled lints, so it still needs "
                + ", ".join(absent)
                + "; a round recorded without "
                + ("that" if one else "them")
                + " cannot say whether "
                + ("it ran" if one else "they ran")
                + " (see references/audit-loop.md; `config set solidity true` if this "
                "run really is a Solidity one)"
            )

    recorded = {lint: value for lint, value in exits.items() if value is not None}
    dirty = sorted(lint for lint, value in recorded.items() if value)
    if dirty and args.findings == 0:
        die(
            "round reports 0 findings while "
            + ", ".join(f"{lint} exited {recorded[lint]}" for lint in dirty)
            + "; a non-zero lint exit is a finding like any other"
        )

    entry = {
        "round": len(rounds) + 1,
        "findings": args.findings,
        "log": args.log,
        "fixes_commit": args.fixes_commit,
        "lints": recorded or None,
        "ts": now(),
    }
    rounds.append(entry)
    commit(args.dir, state, "audit-round", {"step": step["n"], **entry})
    tail = ""
    if recorded:
        tail = "; lints " + ", ".join(
            f"{lint} {recorded[lint]}" for lint in LINTS if lint in recorded
        )
    print(
        f"step {step['n']} audit round {entry['round']} recorded "
        f"({args.findings} finding(s)){tail}"
    )


def done_audit(args, state: dict) -> None:
    step = require_step_phase(state, "audit")
    if "security_suite" not in state["receipts"]:
        die("no security_suite receipt; the audit phase never legitimately ran")
    rounds = step["audit"]["rounds"]
    if not rounds:
        die("no audit rounds recorded; run at least one round before closing")
    last = rounds[-1]
    clean = last["findings"] == 0
    if not clean and not args.no_further_leads:
        die(
            f"last round left {last['findings']} finding(s) open; either run "
            "another round or close with --no-further-leads --reason ..."
        )
    if args.no_further_leads and not args.reason:
        die("--no-further-leads requires --reason")
    had_findings = any(r["findings"] > 0 for r in rounds)
    fixes_ref = args.fixes_ref or next(
        (r["fixes_commit"] for r in reversed(rounds) if r.get("fixes_commit")), None
    )
    if had_findings and not fixes_ref:
        die(
            "findings were recorded but no fixes reference exists; pass "
            "--fixes-ref or record fixes commits on the rounds"
        )
    step["receipts"]["audit"] = {
        "rounds": len(rounds),
        "clean": clean,
        "no_further_leads": bool(args.no_further_leads),
        "reason": args.reason,
        "fixes_ref": fixes_ref,
        "log": args.log or last.get("log"),
    }
    step["phase"] = "prose"
    commit(
        args.dir,
        state,
        "done:audit",
        {"step": step["n"], **step["receipts"]["audit"]},
    )
    print(f"step {step['n']} audit receipted; phase -> prose")


def done_prose(args, state: dict) -> None:
    step = require_step_phase(state, "prose")
    if args.files is None or args.files < 0:
        die("--files must be a non-negative integer")
    applied = {s for s in (args.skills or "").split(",") if s}
    required = {
        str(state["config"]["skills"]["prose_lint"]),
        str(state["config"]["skills"]["voice"]),
    }
    missing = sorted(required - applied)
    if missing:
        die(f"prose pass is missing required skill(s): {', '.join(missing)}")
    step["receipts"]["prose"] = {"files": args.files, "skills": sorted(applied)}
    step["phase"] = "push"
    commit(
        args.dir,
        state,
        "done:prose",
        {"step": step["n"], "files": args.files, "skills": sorted(applied)},
    )
    print(f"step {step['n']} prose pass receipted; phase -> push")


def done_push(args, state: dict) -> None:
    step = require_step_phase(state, "push")
    if not args.pr_url:
        die("--pr-url is required")
    if not args.head_commit:
        die("--head-commit is required")
    stacked = run_branch_of(state) is not None
    if stacked:
        expected_base = step_pr_base(state, step)
        if not args.pr_base:
            die(
                f"--pr-base is required; this step's pull request targets "
                f"'{expected_base}', never the repository default branch"
            )
        if args.pr_base != expected_base:
            die(f"--pr-base must be '{expected_base}'; got '{args.pr_base}'")
        if args.merge_commit:
            die(
                "a step pull request does not merge during the run; the stack "
                "merges in step order in the integrate phase"
            )
        if args.closed_issue_url:
            die(
                "a recorded task issue closes in the integrate phase, once the "
                "run branch lands on the base"
            )
    else:
        if not args.merge_commit:
            die(
                "--merge-commit is required; the pull request is not terminal "
                "until merged"
            )
        expected_issue = expected_task_issue(state)
        if state["receipts"].get("task_issue") is not None and not args.closed_issue_url:
            die("--closed-issue-url is required because a task_issue receipt exists")
        if expected_issue and args.closed_issue_url != expected_issue:
            die(
                "--closed-issue-url does not match the recorded task_issue "
                f"({expected_issue})"
            )
    step["receipts"]["push"] = {
        "pr_url": args.pr_url,
        "head_commit": args.head_commit,
        "pr_base": args.pr_base,
        "merge_commit": args.merge_commit,
        "closed_issue_url": args.closed_issue_url,
    }
    step["status"] = "done"
    step["phase"] = "done"
    remaining = [s for s in state["steps"] if s["status"] == "pending"]
    if remaining:
        nxt = remaining[0]
        nxt["status"] = "open"
        nxt["phase"] = "implement"
        state["current_step"] = nxt["n"]
        tail = f"step {nxt['n']} -> implement"
    else:
        state["current_step"] = None
        if stacked:
            state["phase"] = "integrate"
            state["integrate"] = {"merged": [], "merges": {}}
            tail = f"stack complete; merge it into {run_branch_of(state)}"
        else:
            state["phase"] = "done"
            tail = "all steps done"
    commit(
        args.dir,
        state,
        "done:push",
        {"step": step["n"], **step["receipts"]["push"]},
    )
    if stacked:
        print(
            f"step {step['n']} pushed and stacked on '{args.pr_base}'; {tail}"
        )
    else:
        print(f"step {step['n']} published, merged, and receipted; {tail}")


def _integrate_directive(state: dict) -> dict:
    """Merge the stack bottom up, then the run branch into the base once."""
    run_branch = run_branch_of(state)
    merged = as_dict(state.get("integrate")).get("merged") or []
    for step in state["steps"]:
        if step["n"] in merged:
            continue
        return {
            "do": "merge-step",
            "step": step["n"],
            "title": step["title"],
            "branch": step_branch_name(state, step),
            "pr_url": as_dict(step["receipts"].get("push")).get("pr_url"),
            "into": run_branch,
            "then": (
                f"hexctl done merge-step --step {step['n']} "
                "--merge-commit <sha>"
            ),
        }
    then = "hexctl done integrate --pr-url <url> --merge-commit <sha>"
    if expected_task_issue(state):
        then += " --closed-issue-url <url>"
    return {
        "do": "integrate",
        "run_branch": run_branch,
        "base": state["base"],
        "steps": len(state["steps"]),
        "then": then,
    }


def done_merge_step(args, state: dict) -> None:
    if state["phase"] != "integrate":
        die(
            "merge-step is an integrate-phase receipt; the run is in phase "
            f"'{state['phase']}'"
        )
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if args.step is None:
        die("--step is required")
    if not args.merge_commit:
        die("--merge-commit is required")
    pending = _integrate_directive(state)
    if pending["do"] != "merge-step":
        die(f"every step already merged into '{run_branch_of(state)}'")
    if args.step != pending["step"]:
        die(
            f"the stack merges in step order; step {pending['step']} "
            f"('{pending['branch']}') is next, not step {args.step}"
        )
    integrate = state.setdefault("integrate", {"merged": [], "merges": {}})
    integrate.setdefault("merged", []).append(args.step)
    integrate.setdefault("merges", {})[str(args.step)] = {
        "branch": pending["branch"],
        "into": pending["into"],
        "merge_commit": args.merge_commit,
    }
    commit(
        args.dir,
        state,
        "done:merge-step",
        {
            "step": args.step,
            "branch": pending["branch"],
            "into": pending["into"],
            "merge_commit": args.merge_commit,
        },
    )
    remaining = len(state["steps"]) - len(integrate["merged"])
    tail = f"{remaining} step(s) left in the stack" if remaining else "stack merged"
    print(f"step {args.step} merged into {pending['into']}; {tail}")


def done_integrate(args, state: dict) -> None:
    if state["phase"] != "integrate":
        die(
            "integrate is the terminal phase; the run is in phase "
            f"'{state['phase']}'"
        )
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    pending = _integrate_directive(state)
    if pending["do"] != "integrate":
        die(
            f"step {pending['step']} still has to merge into "
            f"'{run_branch_of(state)}' first"
        )
    if not args.pr_url:
        die("--pr-url is required")
    if not args.merge_commit:
        die(
            "--merge-commit is required; the run is not complete until the run "
            f"branch is merged into '{state['base']}'"
        )
    frontier = as_dict(state.get("frontier"))
    if frontier:
        fault = frontier_close_fault(
            os.path.join(args.dir, frontier["ledger"]), frontier)
        if fault:
            die(
                f"the frontier ledger has not been closed: {fault}. This run "
                f"declared {frontier['ledger']} at init; update it exactly once "
                f"per the versioning contract, or `hexctl halt` and say why not"
            )
    expected_issue = expected_task_issue(state)
    if state["receipts"].get("task_issue") is not None and not args.closed_issue_url:
        die("--closed-issue-url is required because a task_issue receipt exists")
    if expected_issue and args.closed_issue_url != expected_issue:
        die(
            "--closed-issue-url does not match the recorded task_issue "
            f"({expected_issue})"
        )
    carried = carried_forward_fault(run_pr_path(args.dir))
    if carried:
        die(carried)
    state["receipts"]["integrate"] = {
        "run_branch": run_branch_of(state),
        "base": state["base"],
        "pr_url": args.pr_url,
        "merge_commit": args.merge_commit,
        "closed_issue_url": args.closed_issue_url,
        "carried_forward": carried_forward_record(run_pr_path(args.dir)),
    }
    state["phase"] = "done"
    commit(args.dir, state, "done:integrate", state["receipts"]["integrate"])
    print(
        f"{run_branch_of(state)} merged into {state['base']} "
        f"({args.merge_commit}); run complete"
    )


DONE_HANDLERS = {
    "study": done_study,
    "runbook": done_runbook,
    "implement": done_implement,
    "audit": done_audit,
    "prose": done_prose,
    "push": done_push,
    "merge-step": done_merge_step,
    "integrate": done_integrate,
}


def cmd_done(args) -> None:
    state = load_state(args.dir)
    handler = DONE_HANDLERS.get(args.phase)
    if handler is None:
        die(f"unknown phase '{args.phase}'")
    handler(args, state)


def receipted_source(base_dir: str, state: dict, name: str):
    """Return a verified source artefact, or None for a legacy receipt."""
    receipt = as_dict(as_dict(state.get("receipts")).get(name))
    expected = receipt.get("sha256")
    if expected is None:
        return None
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        die(f"{name} receipt has an invalid sha256")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, str) or not artifact:
        die(f"{name} receipt has no artefact path")
    path, data = read_bounded_source(base_dir, artifact, f"{name} artefact")
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        die(
            f"{name} artefact digest changed: expected {expected}, got {actual}; "
            "restore the receipted bytes or halt the run"
        )
    return {
        "path": path,
        "sha256": expected,
        "text": decoded_source(data, f"{name} artefact"),
    }


STEP_HEADING_RE = re.compile(r"^## Step (?P<number>[1-9][0-9]*): (?P<title>.+)$")
MARKDOWN_FENCE_RE = re.compile(r"^\s*(?P<mark>`{3,}|~{3,})")
RISK_OPEN_RE = re.compile(r"^(?P<mark>`{3,}|~{3,})risk-register[ \t]*$")


def markdown_lines(text: str):
    """Yield source offsets and fence state without treating quoted headings as real."""
    offset = 0
    open_mark = None
    for physical in text.splitlines(keepends=True):
        line = physical.rstrip("\r\n")
        fence = MARKDOWN_FENCE_RE.match(line)
        was_open = open_mark
        if fence:
            mark = fence.group("mark")[0]
            if open_mark is None:
                open_mark = mark
            elif mark == open_mark:
                open_mark = None
            yield offset, offset + len(physical), line, True, was_open
        else:
            yield offset, offset + len(physical), line, open_mark is not None, was_open
        offset += len(physical)


def source_runbook_step(source: dict, step: dict) -> dict:
    """Select one exact numbered step block without interpreting its schema."""
    text = source["text"]
    headings = []
    for start, _, line, in_fence, _ in markdown_lines(text):
        if in_fence:
            continue
        match = STEP_HEADING_RE.fullmatch(line)
        if match:
            headings.append((start, match))
    matches = []
    for index, (start, heading) in enumerate(headings):
        if int(heading.group("number")) != step["n"]:
            continue
        if heading.group("title") != step["title"]:
            continue
        end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        matches.append(text[start:end])
    if not matches:
        die(
            f"runbook step {step['n']} '{step['title']}' has no exact source block"
        )
    if len(matches) != 1:
        die(f"ambiguous runbook step {step['n']} '{step['title']}'")
    return {
        "markdown": matches[0],
        "path": source["path"],
        "sha256": source["sha256"],
        "number": step["n"],
        "title": step["title"],
    }


def source_risk_register(source: dict) -> dict:
    """Carry the unique fenced register; Protasis remains its shape authority."""
    text = source["text"]
    matches = []
    start = None
    risk_mark = None
    for line_start, line_end, line, is_fence, was_open in markdown_lines(text):
        if start is None and was_open is None:
            opened = RISK_OPEN_RE.fullmatch(line)
            if opened:
                start = line_start
                risk_mark = opened.group("mark")[0]
            continue
        if start is not None and is_fence and was_open == risk_mark:
            fence = MARKDOWN_FENCE_RE.match(line)
            if fence and fence.group("mark")[0] == risk_mark:
                matches.append(text[start:line_end])
                start = None
                risk_mark = None
    if not matches:
        die("study artefact has no fenced risk-register block")
    if len(matches) != 1:
        die("study artefact has an ambiguous fenced risk-register block")
    return {
        "markdown": matches[0],
        "path": source["path"],
        "sha256": source["sha256"],
    }


def bounded_git(base_dir: str, argv: list[str]) -> bytes:
    """Run Git without a shell and stop on time, output or exit-status faults."""
    try:
        process = subprocess.Popen(
            ["git", *argv],
            cwd=os.path.realpath(base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
        )
    except OSError as exc:
        die(f"git {' '.join(argv)} could not start: {exc}")
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    output = bytearray()
    deadline = time.monotonic() + GIT_TIMEOUT
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                process.wait()
                die(f"git {' '.join(argv)} timed out after {GIT_TIMEOUT} seconds")
            events = selector.select(min(remaining, 0.1))
            if not events and process.poll() is not None:
                events = [(key, selectors.EVENT_READ) for key in selector.get_map().values()]
            for key, _ in events:
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                output.extend(chunk)
                if len(output) > GIT_OUTPUT_MAX:
                    process.kill()
                    process.wait()
                    die(f"git {' '.join(argv)} exceeded {GIT_OUTPUT_MAX}-byte output cap")
        returncode = process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        die(f"git {' '.join(argv)} timed out after {GIT_TIMEOUT} seconds")
    finally:
        selector.close()
    if returncode != 0:
        message = output.decode("utf-8", errors="replace").strip()
        die(f"git {' '.join(argv)} failed with exit {returncode}: {message}")
    return bytes(output)


def scribe_files(base_dir: str, pr_base: str, branch: str) -> list[str]:
    check_branch_name(pr_base)
    check_branch_name(branch)
    raw = bounded_git(base_dir, ["diff", "--name-only", "-z", f"{pr_base}..{branch}", "--"])
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        die("git diff path list is not UTF-8")
    paths = [path for path in decoded.split("\0") if path]
    unique = sorted(set(paths))
    if len(unique) > GIT_PATHS_MAX:
        die(f"git diff returned more than {GIT_PATHS_MAX} paths")
    for path in unique:
        if os.path.isabs(path) or path in (".", ".."):
            die(f"git diff returned an unsafe path: {path}")
        scoped_path(base_dir, path, "git diff path")
    return unique


def delegation_packet(base_dir: str, state: dict, directive: dict) -> dict:
    """Add the total packet envelope and build only the four delegated briefs."""
    packet = {
        **directive,
        "state_sha256": state_fingerprint(state),
        "agent": None,
        "brief": {},
    }
    action = directive.get("do")
    root = os.path.realpath(base_dir)
    if action == "study":
        packet["agent"] = "surveyor"
        packet["brief"] = {
            "topic": state["topic"],
            "target_dir": root,
            "base_ref": state["base"],
            "output_path": scoped_path(
                root, os.path.join(STATE_DIR_NAME, "study.md"), "study output"
            ),
        }
        return packet

    if action not in ("implement", "audit-round", "prose"):
        return packet

    if not run_branch_of(state):
        return packet

    runbook = receipted_source(root, state, "runbook")
    study = receipted_source(root, state, "study")
    if runbook is None or study is None:
        # A pre-generation state cannot establish the source claims needed by
        # the four new briefs, so it retains an explicit inline directive.
        return packet

    step = current_step(state)
    plan = branch_plan(state, step)
    if action == "implement":
        packet["agent"] = "mason"
        packet["brief"] = {
            "runbook_step": source_runbook_step(runbook, step),
            "branch": plan["branch"],
            "branch_from": plan["branch_from"],
        }
        return packet

    root_plugin = plugin_root()
    if action == "audit-round":
        audit = as_dict(as_dict(state.get("config")).get("audit"))
        log = audit.get("log_path")
        suffix = audit.get("stacked_suffix")
        if not isinstance(log, str) or not log:
            die("audit config has no log_path for the warden packet")
        if not isinstance(suffix, str) or not suffix:
            die("audit config has no stacked_suffix for the warden packet")
        packet["agent"] = "warden"
        packet["brief"] = {
            "step_branch": plan["branch"],
            "stacked_branch": plan["branch"] + suffix,
            "security_suite": as_dict(state.get("receipts")).get("security_suite"),
            "plugin_root": root_plugin,
            "audit_log_path": scoped_path(root, log, "audit log path"),
            "round": directive["round"],
            "risk_register": source_risk_register(study),
        }
        return packet

    pr_base = plan["pr_base"]
    packet["agent"] = "scribe"
    packet["brief"] = {
        "files": scribe_files(root, pr_base, plan["branch"]),
        "pr_base": pr_base,
        "pr_draft_path": scoped_path(
            root,
            os.path.join(STATE_DIR_NAME, "steps", str(step["n"]), "pr.md"),
            "PR draft path",
        ),
        "plugin_root": root_plugin,
    }
    return packet


def cmd_next(args) -> None:
    state = load_state(args.dir)
    out = delegation_packet(args.dir, state, _next_directive(state))
    print(json.dumps(out))


def _next_directive(state: dict) -> dict:
    if state.get("halted"):
        return {"do": "halted", "reason": state["halted"]["reason"]}
    phase = state["phase"]
    if phase == "study":
        return {
            "do": "study",
            "topic": state["topic"],
            "then": "hexctl done study --artifact <path> --skills <csv>",
        }
    if phase == "runbook":
        return {
            "do": "runbook",
            "then": "hexctl done runbook --artifact <path> --steps-file <path>",
        }
    if phase == "integrate":
        return _integrate_directive(state)
    if phase == "done":
        return {"do": "done", "steps": len(state["steps"])}
    step = current_step(state)
    base = {"step": step["n"], "title": step["title"]}
    if step["phase"] == "audit":
        if "security_suite" not in state["receipts"]:
            return {
                **base,
                "do": "resolve-security-suite",
                "then": "hexctl record security_suite '<ids or waived:reason>'",
            }
        rounds = step["audit"]["rounds"]
        max_rounds = max_rounds_of(state)
        lints_owed = not solidity_round(state)
        owed = {"lints": [f"--{lint}-exit" for lint in LINTS]} if lints_owed else {}
        if not rounds:
            return {**base, "do": "audit-round", "round": 1, **owed}
        last = rounds[-1]
        if last["findings"] == 0:
            return {**base, "do": "close-audit", "rounds": len(rounds)}
        if len(rounds) >= max_rounds:
            return {
                **base,
                "do": "audit-verdict",
                "rounds": len(rounds),
                "open_findings": last["findings"],
            }
        return {
            **base,
            "do": "audit-round",
            "round": len(rounds) + 1,
            "prior_findings": last["findings"],
            **owed,
        }
    if step["phase"] == "issue":
        return {**base, "do": "implement", "legacy_issue_phase_skipped": True}
    if step["phase"] in ("implement", "push"):
        return {**base, "do": step["phase"], **branch_plan(state, step)}
    return {**base, "do": step["phase"]}


CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def clean(text: str) -> str:
    return CONTROL_RE.sub(" ", text)


def cmd_status(args) -> None:
    state = load_state(args.dir)
    if args.json:
        print(json.dumps(state, indent=2))
        return
    print(f"topic: {clean(state['topic'])}")
    print(f"base:  {state['base']}")
    if state.get("run_branch"):
        print(f"run:   {state['run_branch']} -> {state['base']}")
    if state.get("halted"):
        print(f"HALTED: {state['halted']['reason']}")
    phase = state["phase"]
    if phase in ("study", "runbook"):
        print(f"phase: {phase} (day {DAY[phase]})")
    elif phase == "integrate":
        merged = len(as_dict(state.get("integrate")).get("merged") or [])
        print(
            f"phase: integrate ({merged}/{len(state['steps'])} steps merged "
            f"into {state['run_branch']})"
        )
    elif phase == "done":
        print(f"phase: done ({len(state['steps'])} steps shipped)")
    else:
        step = current_step(state)
        sp = step["phase"]
        day = "rest" if sp == "push" else f"day {DAY[sp]}"
        print(f"phase: step {step['n']}/{len(state['steps'])} '{clean(step['title'])}' -> {sp} ({day})")
        if sp == "audit":
            rounds = step["audit"]["rounds"]
            tail = rounds[-1]["findings"] if rounds else "-"
            print(f"audit: {len(rounds)} round(s), last findings: {tail}")
    for step in state["steps"]:
        mark = {"pending": " ", "open": ">", "done": "x"}[step["status"]]
        print(f"  [{mark}] {step['n']}. {clean(step['title'])}")


def cmd_halt(args) -> None:
    state = load_state(args.dir)
    if not args.reason:
        die("--reason is required")
    state["halted"] = {"reason": args.reason, "ts": now()}
    commit(args.dir, state, "halt", {"reason": args.reason})
    print(f"halted: {args.reason}")


def cmd_resume(args) -> None:
    state = load_state(args.dir)
    if not state.get("halted"):
        die("run is not halted")
    note = args.note or ""
    state["halted"] = None
    commit(args.dir, state, "resume", {"note": note})
    print("resumed")


def verify_run(base_dir: str) -> int:
    state = load_state(base_dir)
    path = ledger_path(base_dir)
    if not os.path.exists(path):
        die("ledger missing", 1)
    prev = "genesis"
    count = 0
    last_state = None
    with open(path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                expected = hashlib.sha256(
                    canonical(
                        {
                            "ts": entry["ts"],
                            "event": entry["event"],
                            "data": entry["data"],
                            "prev": entry["prev"],
                            "state": entry["state"],
                        }
                    ).encode()
                ).hexdigest()
                broken = entry["prev"] != prev or entry["hash"] != expected
            except (ValueError, KeyError, TypeError):
                broken = True
            if broken:
                die(f"ledger chain broken at line {i}", 1)
            prev = entry["hash"]
            last_state = entry["state"]
            count += 1
    if last_state is not None and state_fingerprint(state) != last_state:
        die(
            "state file does not match the last ledger entry; "
            "state.json was edited outside hexctl", 1
        )
    if state["phase"] == "integrate":
        merged = as_dict(state.get("integrate")).get("merged") or []
        expected = [s["n"] for s in state["steps"][: len(merged)]]
        if merged != expected:
            die(
                "integrate state is inconsistent: the stack must merge in step "
                f"order, got {merged}", 1
            )
    if state["phase"] == "steps":
        step = current_step(state)
        if step["status"] != "open" or step["phase"] not in STEP_PHASES:
            die("state inconsistent: current step is not open", 1)
    return count


def cmd_verify(args) -> None:
    count = verify_run(args.dir)
    print(f"ok: {count} ledger entries, chain intact, state consistent")


def cmd_reset(args) -> None:
    """Archive a completed run inside its ignored state directory."""
    count = verify_run(args.dir)
    state = load_state(args.dir)
    if state["phase"] != "done":
        die(
            f"refusing to reset an incomplete run in phase '{state['phase']}'; "
            "resume it or halt it explicitly"
        )

    root = state_root(args.dir)
    archive_root = os.path.join(root, "archive")
    os.makedirs(archive_root, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    topic = re.sub(r"[^a-z0-9]+", "-", state["topic"].lower()).strip("-")[:48]
    name = f"{stamp}-{topic or 'completed-run'}"
    destination = os.path.join(archive_root, name)
    suffix = 2
    while os.path.exists(destination):
        destination = os.path.join(archive_root, f"{name}-{suffix}")
        suffix += 1
    os.makedirs(destination)

    preserved = {".gitignore", "archive", "lock"}
    for entry in os.listdir(root):
        if entry in preserved:
            continue
        os.replace(os.path.join(root, entry), os.path.join(destination, entry))

    print(
        f"archived completed run ({count} ledger entries) at {destination}; "
        "active state cleared"
    )


# ---------------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hexctl", description=__doc__)
    p.add_argument("--dir", default=".", help="directory holding the state dir")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="start a run")
    sp.add_argument("--topic", required=True)
    sp.add_argument("--base", default="main")
    sp.add_argument(
        "--run-branch",
        dest="run_branch",
        help="integration branch for the whole run (default: slug of --topic)",
    )
    sp.add_argument(
        "--frontier",
        help="EVOLUTION.md this run is meant to advance; the terminal receipt "
             "then refuses until it carries exactly one new valid row",
    )
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("status", help="show run state")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("next", help="emit the single next action as JSON")
    sp.set_defaults(fn=cmd_next)

    sp = sub.add_parser("record", help="store a named receipt")
    sp.add_argument("key")
    sp.add_argument("value")
    sp.set_defaults(fn=cmd_record)

    sp = sub.add_parser("config", help="get or set a config value")
    sp.add_argument("action", choices=["get", "set"])
    sp.add_argument("path")
    sp.add_argument("value", nargs="?")
    sp.set_defaults(fn=cmd_config)

    sp = sub.add_parser("done", help="receipt a completed phase")
    sp.add_argument("phase", choices=list(DONE_HANDLERS))
    sp.add_argument("--artifact")
    sp.add_argument("--skills")
    sp.add_argument("--steps-file", dest="steps_file")
    sp.add_argument("--branch")
    sp.add_argument("--commit")
    sp.add_argument("--tests")
    sp.add_argument("--no-further-leads", dest="no_further_leads", action="store_true")
    sp.add_argument("--reason")
    sp.add_argument("--fixes-ref", dest="fixes_ref")
    sp.add_argument("--log")
    sp.add_argument("--files", type=int)
    sp.add_argument("--pr-url", dest="pr_url")
    sp.add_argument("--pr-base", dest="pr_base")
    sp.add_argument("--step", type=int)
    sp.add_argument("--head-commit", dest="head_commit")
    sp.add_argument("--merge-commit", dest="merge_commit")
    sp.add_argument("--closed-issue-url", dest="closed_issue_url")
    sp.set_defaults(fn=cmd_done)

    sp = sub.add_parser("audit-round", help="record one security round")
    sp.add_argument("--findings", type=int, required=True)
    sp.add_argument("--log")
    sp.add_argument("--fixes-commit", dest="fixes_commit")
    for lint in LINTS:
        sp.add_argument(
            f"--{lint}-exit",
            dest=f"{lint}_exit",
            type=int,
            help=f"the exit status {lint} returned; 0 is clean",
        )
    sp.set_defaults(fn=cmd_audit_round)

    sp = sub.add_parser("halt", help="stop the run with a reason")
    sp.add_argument("--reason")
    sp.set_defaults(fn=cmd_halt)

    sp = sub.add_parser("resume", help="clear a halt")
    sp.add_argument("--note")
    sp.set_defaults(fn=cmd_resume)

    sp = sub.add_parser(
        "reset", help="archive a completed run and clear its active state"
    )
    sp.set_defaults(fn=cmd_reset)

    sp = sub.add_parser("verify", help="check ledger chain and state consistency")
    sp.set_defaults(fn=cmd_verify)

    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.fn.__name__ in MUTATING:
        with held_lock(args.dir, args.fn.__name__):
            args.fn(args)
        return
    args.fn(args)


if __name__ == "__main__":
    main()
