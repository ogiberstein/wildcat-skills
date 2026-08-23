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
import importlib.util
import json
import os
import re
import selectors
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse

STATE_DIR_NAME = ".hexaemeron"
STATE_FILE = "state.json"
LEDGER_FILE = "ledger.jsonl"
STUDY_AMENDMENT_PENDING_FILE = "study-amendment-pending.json"

# The run-level pull request body the prose phase writes and the integrate
# phase opens the integration pull request from. It is the last thing a run
# writes into the repository, so it is where the work a run gave up on has to
# be named: the next study over the same target reads it as prior art.
RUN_PR_FILE = "run-pr.md"
WORKTREE_FILE = "worktree"
"""The one line the origin checkout keeps, naming the tree the run works in."""
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

ELENCHUS_VERDICTS = ("guarded", "unguarded", "passed", "inconclusive")
"""The complete Elenchus result vocabulary accepted on an audit fix receipt."""

AUDIT_RECORD_SCHEMA = "fiat-audit-round/v1"
AUDIT_COVERAGE_VALUES = ("reviewed", "not-applicable")
AUDIT_FINDINGS_HEADER = "| id | severity | file | finding | status |"
AUDIT_FINDINGS_SEPARATOR = "| --- | --- | --- | --- | --- |"
AUDIT_ZERO_FINDING_ROW = "| -- | -- | -- | none | -- |"
AUDIT_TIMESTAMP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", re.ASCII
)
AUDIT_OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd
AUDIT_PHYSICAL_LINE_BYTES_MAX = 1024 * 1024


def elenchus_verdict_obligation() -> dict:
    """Describe the conditional audit-round input without claiming it was run."""
    return {
        "flag": "--elenchus-verdict",
        "required_with": "--fixes-commit",
        "choices": list(ELENCHUS_VERDICTS),
    }


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
    try:
        root = os.path.realpath(base_dir)
        candidate = (
            supplied if os.path.isabs(supplied) else os.path.join(root, supplied)
        )
        resolved = os.path.realpath(candidate)
    except (OSError, TypeError, ValueError):
        die(f"{label} is not a valid filesystem path")
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


def read_configured_audit_log(
    base_dir: str, configured: str, supplied: str | None
) -> tuple[str, bytes]:
    """Read the one configured log without following aliases or symlinks."""
    if not isinstance(configured, str) or not configured:
        die("audit config has no log_path")
    root = os.path.realpath(base_dir)
    configured_path = scoped_path(root, configured, "audit log path")
    lexical = os.path.abspath(
        configured if os.path.isabs(configured) else os.path.join(root, configured)
    )
    if supplied is not None:
        supplied_lexical = os.path.abspath(
            supplied if os.path.isabs(supplied) else os.path.join(root, supplied)
        )
        supplied_path = scoped_path(root, supplied, "supplied audit log path")
        if supplied_lexical != lexical:
            die("--log must name the configured audit log path")
        if supplied_path != supplied_lexical:
            die("supplied audit log path traverses a symlink")
    if lexical != configured_path:
        die("audit log path traverses a symlink")
    try:
        info = os.lstat(lexical)
    except OSError:
        die("audit log path is not a regular file")
    if stat.S_ISLNK(info.st_mode):
        die("audit log path is a symlink")
    if not stat.S_ISREG(info.st_mode):
        die("audit log path is not a regular file")

    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_only = getattr(os, "O_DIRECTORY", 0)
    non_blocking = getattr(os, "O_NONBLOCK", 0)
    if (
        not no_follow
        or not directory_only
        or not non_blocking
        or not AUDIT_OPEN_SUPPORTS_DIR_FD
    ):
        die("platform cannot safely read the configured audit log")
    close_exec = getattr(os, "O_CLOEXEC", 0)
    directory_flags = (
        os.O_RDONLY | close_exec | no_follow | directory_only
    )
    file_flags = os.O_RDONLY | close_exec | no_follow | non_blocking
    relative = os.path.relpath(lexical, root)
    components = relative.split(os.sep)
    directory_descriptor = None
    file_descriptor = None
    try:
        directory_descriptor = os.open(root, directory_flags)
        if not stat.S_ISDIR(os.fstat(directory_descriptor).st_mode):
            die("target directory is not a regular directory")
        for component in components[:-1]:
            next_descriptor = None
            try:
                next_descriptor = os.open(
                    component, directory_flags, dir_fd=directory_descriptor
                )
                if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                    die("audit log path has a non-directory component")
                os.close(directory_descriptor)
                directory_descriptor = next_descriptor
                next_descriptor = None
            finally:
                if next_descriptor is not None:
                    with contextlib.suppress(OSError):
                        os.close(next_descriptor)
        file_descriptor = os.open(
            components[-1], file_flags, dir_fd=directory_descriptor
        )
        handle = os.fdopen(file_descriptor, "rb")
        file_descriptor = None
        with handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                die("audit log path is not a regular file")
            if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                die("audit log path changed during access")
            data = handle.read(SOURCE_BYTES_MAX + 1)
            finished = os.fstat(handle.fileno())
            opened_identity = (
                opened.st_dev,
                opened.st_ino,
                opened.st_size,
                opened.st_mtime_ns,
                opened.st_ctime_ns,
            )
            finished_identity = (
                finished.st_dev,
                finished.st_ino,
                finished.st_size,
                finished.st_mtime_ns,
                finished.st_ctime_ns,
            )
            if opened_identity != finished_identity or (
                len(data) <= SOURCE_BYTES_MAX and len(data) != finished.st_size
            ):
                die("audit log path changed during read")
    except OSError:
        die("audit log path cannot be read")
    finally:
        if file_descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(file_descriptor)
        if directory_descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(directory_descriptor)
    if len(data) > SOURCE_BYTES_MAX:
        die(f"audit log path exceeds {SOURCE_BYTES_MAX}-byte cap")
    return relative.replace(os.sep, "/"), data


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
    `"integrate": null` defeats the default and the next `.get` raises. The load
    boundary rejects required containers; this remains defensive for optional leaves
    and isolated callers.
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

    Direct callers whose `config` or `receipts` is not an object read it as absent
    rather than raising. State-backed commands cannot reach this fallback because the
    load boundary rejects those wrong-kind containers first.
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
TASK_ISSUE_PATH_RE = re.compile(r".*/issues/([1-9][0-9]*)\Z")

# Conservative subset of git's refname rules: no whitespace, no traversal, no
# leading or trailing separator, nothing that needs quoting in a shell.
BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*[A-Za-z0-9]$")


def slug(text: str, limit: int = 48) -> str:
    return SLUG_RE.sub("-", text.lower()).strip("-")[:limit].strip("-")


def task_issue_number(value: str) -> str:
    parsed = None
    if isinstance(value, str) and not any(
        character.isspace() or ord(character) < 32 or ord(character) == 127
        for character in value
    ):
        try:
            parsed = urllib.parse.urlsplit(value)
            hostname = parsed.hostname
        except ValueError:
            parsed = None
            hostname = None
    else:
        hostname = None
    path = parsed.path if parsed is not None else ""
    match = TASK_ISSUE_PATH_RE.fullmatch(path)
    if (
        match is None
        or parsed is None
        or parsed.scheme not in ("http", "https")
        or hostname is None
    ):
        die(
            "--task-issue must be an absolute HTTP(S) URL with a path ending in "
            "/issues/<positive-number>"
        )
    return match.group(1)


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


def require_state_container(value, path: str, expected_type: type):
    """Return one required state container or stop with a value-free fault."""
    if not isinstance(value, expected_type):
        kind = "object" if expected_type is dict else "array"
        die(f"state key '{path}' must be an {kind}", 1)
    return value


def validate_state_shape(state) -> dict:
    """Validate the version-1 container spine in one deterministic order.

    Leaves heterogeneous receipt and field payloads to their existing semantic
    checks. This boundary establishes only the containers every reader traverses.
    """
    root = require_state_container(state, "$", dict)
    config = require_state_container(root.get("config"), "config", dict)
    for section in ("skills", "audit", "git"):
        require_state_container(
            config.get(section), f"config.{section}", dict
        )
    require_state_container(root.get("receipts"), "receipts", dict)
    steps = require_state_container(root.get("steps"), "steps", list)

    for step_index, step in enumerate(steps):
        require_state_container(step, f"steps[{step_index}]", dict)

    for step_index, step in enumerate(steps):
        prefix = f"steps[{step_index}]"
        require_state_container(step.get("receipts"), f"{prefix}.receipts", dict)
        audit = require_state_container(step.get("audit"), f"{prefix}.audit", dict)
        rounds = require_state_container(
            audit.get("rounds"), f"{prefix}.audit.rounds", list
        )
        for round_index, round_entry in enumerate(rounds):
            require_state_container(
                round_entry,
                f"{prefix}.audit.rounds[{round_index}]",
                dict,
            )
    return root


def study_amendment_pending_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), STUDY_AMENDMENT_PENDING_FILE)


def load_study_amendment_pending(base_dir: str) -> dict | None:
    """Read the bounded write-ahead record for an interrupted amendment."""
    path = study_amendment_pending_path(base_dir)
    if not os.path.exists(path):
        return None
    if os.path.islink(path) or not os.path.isfile(path):
        die("study amendment pending record is not a regular file", 1)
    try:
        with open(path, "rb") as handle:
            raw = handle.read(65537)
    except OSError as exc:
        die(f"study amendment pending record cannot be read: {exc}", 1)
    if len(raw) > 65536:
        die("study amendment pending record exceeds 65536-byte cap", 1)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        die("study amendment pending record is malformed", 1)
    if not isinstance(value, dict) or value.get("version") != 1:
        die("study amendment pending record has an unsupported shape", 1)
    if not isinstance(value.get("artifact"), str) or not value["artifact"]:
        die("study amendment pending record has no artefact path", 1)
    before = value.get("state_before_sha256")
    if not isinstance(before, str) or not re.fullmatch(r"[0-9a-f]{64}", before):
        die("study amendment pending record has an invalid state digest", 1)
    amendment = value.get("amendment")
    if not isinstance(amendment, dict):
        die("study amendment pending record has no amendment object", 1)
    return value


def write_study_amendment_pending(base_dir: str, value: dict) -> None:
    """Publish a durable marker before replacing any receipted study bytes."""
    root = state_root(base_dir)
    path = study_amendment_pending_path(base_dir)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".study-amendment-pending-", dir=root
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        die(f"study amendment pending record could not be written: {exc}", 1)


def clear_study_amendment_pending(base_dir: str) -> None:
    """Remove the write-ahead marker only after the receipt commit is durable."""
    path = study_amendment_pending_path(base_dir)
    try:
        os.unlink(path)
        directory = os.open(state_root(base_dir), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except FileNotFoundError:
        return
    except OSError as exc:
        die(f"study amendment pending record could not be cleared: {exc}", 1)


def load_state(base_dir: str, *, allow_pending_amendment: bool = False) -> dict:
    path = state_path(base_dir)
    if not os.path.exists(path):
        # A checkout that started a run has no state of its own: the run's state
        # is in its worktree. Say which one and how to reach it, rather than
        # reporting the absence and letting somebody start a second run over the
        # top of the first.
        live = read_breadcrumbs(base_dir)
        if live:
            named = "\n".join(f"  hexctl --dir {entry} next" for entry in live)
            die(
                f"no state here; this checkout's {'run works' if len(live) == 1 else 'runs work'} "
                f"in {'its own worktree' if len(live) == 1 else 'their own worktrees'}:\n{named}"
            )
        recorded = raw_breadcrumbs(base_dir)
        if recorded:
            named = ", ".join(recorded)
            die(
                f"this checkout recorded a run worktree that is no longer "
                f"there: {named}. Restore it or clear the breadcrumb at "
                f"{breadcrumb_path(base_dir)}; a second run is not started for you"
            )
        die(f"no state at {path}; run `hexctl init --topic ...` first")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except (ValueError, OSError) as exc:
        die(f"state file unreadable at {path}: {exc}", 1)
    state = validate_state_shape(state)
    if not allow_pending_amendment and load_study_amendment_pending(base_dir):
        die(
            "study amendment transaction is pending; rerun `hexctl amend study "
            "--artifact <canonical-study>` to recover before continuing"
        )
    return state


MUTATING = frozenset(
    {
        "cmd_init",
        "cmd_record",
        "cmd_config",
        "cmd_amend_study",
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
                "Two agents in one run's worktree share one run and one "
                "ledger. Each run gets its own tree at init, so start a "
                "separate run with `hexctl --dir <checkout> init --topic "
                "...`, or wait for this one.".format(
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


def last_local_commit(step: dict):
    """The last commit whose local signature and trailers were receipted."""
    for round_entry in reversed(as_dict(step.get("audit")).get("rounds") or []):
        verified = as_dict(round_entry).get("verified_commits") or []
        if verified:
            return verified[-1]
    implement = as_dict(as_dict(step.get("receipts")).get("implement"))
    verified = implement.get("verified_commits") or []
    if verified:
        return verified[-1]
    return implement.get("commit")


def require_global_phase(state: dict, phase: str) -> None:
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state["phase"] != phase:
        die(f"out of order: expected phase '{state['phase']}', got '{phase}'")


def amendment_block(state: dict) -> dict | None:
    """Return the latest recorded broken verdict for the current step."""
    if state.get("phase") != "steps" or state.get("current_step") is None:
        return None
    amendments = as_dict(as_dict(state.get("receipts")).get("study")).get(
        "amendments"
    )
    if not isinstance(amendments, list):
        return None
    step_number = state["current_step"]
    for amendment in reversed(amendments):
        verdicts = as_dict(amendment).get("step_verdicts")
        if not isinstance(verdicts, list):
            continue
        for verdict in verdicts:
            item = as_dict(verdict)
            if item.get("step") != step_number:
                continue
            if item.get("entry") == "holds" and item.get("exit") == "holds":
                return None
            return {
                "step": step_number,
                "entry": item.get("entry"),
                "exit": item.get("exit"),
                "amendment_sha256": amendment.get("amendment_sha256"),
                "study_sha256": amendment.get("new_sha256"),
            }
    return None


def require_no_amendment_block(state: dict) -> None:
    blocked = amendment_block(state)
    if blocked is None:
        return
    die(
        "study amendment blocks step {step}: entry {entry}, exit {exit}; "
        "inspect the amendment, halt the run, or use a separately specified "
        "runbook-repair transition".format(**blocked)
    )


def require_step_phase(state: dict, phase: str) -> dict:
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state["phase"] != "steps":
        die(f"out of order: run is in phase '{state['phase']}', not working steps")
    require_no_amendment_block(state)
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
    origin_root = os.path.realpath(args.dir)
    root = state_root(args.dir)
    if os.path.exists(state_path(args.dir)):
        die(f"state already exists at {root}; resume with `hexctl next`")
    prefix = DEFAULT_CONFIG["git"]["run_branch_prefix"]
    issue_number = (
        task_issue_number(args.task_issue) if args.task_issue is not None else None
    )
    topic_slug = slug(args.topic) or "run"
    automatic_tail = (
        topic_slug
        if issue_number is None
        else slug(f"{issue_number}-{topic_slug}", 48)
    )
    run_branch = args.run_branch or f"{prefix}{automatic_tail}"
    check_branch_name(run_branch)
    if issue_number is not None:
        required_prefix = f"{prefix}{issue_number}-"
        if not run_branch.startswith(required_prefix):
            die(
                f"--run-branch for task issue {issue_number} must start with "
                f"'{required_prefix}'"
            )
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

    # Everything refusable happens before the first mutation. The path is derived
    # and validated, and the branch is checked for an existing tree, while a
    # refusal still costs nothing: no worktree, no state, no ledger, no
    # breadcrumb.
    repo_root = repository_root(args.dir)
    candidate = run_worktree_path(args.dir, run_branch)
    if os.path.exists(state_path(candidate)):
        die(
            f"this run already has a worktree at {candidate}; "
            f"resume with `hexctl --dir {candidate} next`"
        )
    worktree = check_worktree_path(repo_root, candidate)
    refuse_checked_out_branch(args.dir, run_branch)

    home = os.path.dirname(worktree)
    os.makedirs(home, exist_ok=True)
    # Self-ignoring, the same trick the state directory uses. Without it the
    # worktree home shows as untracked in the origin checkout, which both breaks
    # the promise that a run leaves that checkout's `git status` alone and blocks
    # the next run, because preflight refuses a dirty tree. Doing it here rather
    # than leaning on the target repository's own rules means the promise holds
    # whichever repository the run was started in.
    home_gitignore = os.path.join(home, ".gitignore")
    if not os.path.exists(home_gitignore):
        with open(home_gitignore, "w", encoding="utf-8") as fh:
            fh.write("*\n")
    bounded_git(
        args.dir,
        ["worktree", "add", "-b", run_branch, worktree, args.base],
        refusal=(
            f"could not create the run worktree at {worktree} "
            f"for '{run_branch}' off '{args.base}'"
        ),
    )

    # From here the run's home is the worktree, so a failure has something to
    # undo. Anything that goes wrong while writing state takes the tree with it,
    # because a tree with no state is not a run anybody can resume.
    root = state_root(worktree)
    try:
        os.makedirs(root, exist_ok=True)
        # Self-ignoring: git never sees the state directory even in repos whose
        # .gitignore was not touched. Nested .gitignore with `*` covers it.
        with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("*\n")
    except OSError:
        remove_run_worktree(args.dir, worktree)
        die(f"could not write the run's state into {root}")

    receipts = {}
    if args.task_issue is not None:
        receipts["task_issue"] = args.task_issue

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
        "receipts": receipts,
        "config": json.loads(json.dumps(DEFAULT_CONFIG)),
        "halted": None,
        "frontier": frontier,
    }
    state["worktree"] = worktree
    state["origin"] = origin_root
    init_data = {"topic": args.topic, "base": args.base, "run_branch": run_branch}
    if args.task_issue is not None:
        init_data["task_issue"] = args.task_issue
    try:
        commit(worktree, state, "init", init_data)
        write_breadcrumbs(args.dir, worktree)
    except OSError:
        remove_run_worktree(args.dir, worktree)
        die(f"could not record the run at {root}")
    print(
        f"initialised {root} (topic: {args.topic}); "
        f"run branch {run_branch} off {args.base}"
    )
    print(f"run worktree {worktree}")
    print(f"work in it: hexctl --dir {worktree} next")
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
LEDGER_ROW_COMPACT = re.compile(
    r"^- `(?P<version>[^`]+)` \| (?P<axis>baseline|evolution|generation|epoch) "
    r"\| `(?P<revision>[^`]+)` \| `(?P<digest>[0-9a-f]{64})` "
    r"\| (?P<evidence>.*?) \| (?P<change>.*?)$"
)
"""One history row, in either spelling tests/test_evolution_contract.py
accepts, so the gate and the suite cannot disagree about what a row is.
Reading only the table shape counted a compact-list ledger as empty and
refused a real completed frontier (skills#443)."""

LEDGER_AXES = ("baseline", "evolution", "generation", "epoch")


def ledger_rows(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        match = LEDGER_ROW.fullmatch(line) or LEDGER_ROW_COMPACT.fullmatch(line)
        if match:
            rows.append(match.groupdict())
    return rows


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
    # Anchor on the init-time version rather than the stored count: a snapshot
    # taken while the gate misread a ledger's row spelling counted a real
    # history as empty, and the anchor survives that (skills#443).
    anchor = before.get("version_at_init")
    anchor_at = [i for i, r in enumerate(rows) if r["version"] == anchor]
    if anchor is not None and not anchor_at:
        return (f"{path} no longer carries the init-time version row "
                f"{anchor!r}; history is append-only")
    gained = (len(rows) - (anchor_at[-1] + 1) if anchor_at
              else len(rows) - before["rows"])
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
    if args.key == "task_issue":
        if args.key not in state["receipts"]:
            die(
                "task_issue must be supplied by `init --task-issue`; "
                "the stored run branch cannot be renamed"
            )
        if value != state["receipts"][args.key]:
            die("task_issue is already recorded and cannot be changed")
        print("task_issue already recorded")
        return
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
    require_no_amendment_block(state)
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
    range_base = step_pr_base(state, step) if run_branch_of(state) else state["base"]
    branch_tip = resolved_commit(
        args.dir, args.branch, f"step {step['n']} implementation branch"
    )
    supplied_head = resolved_commit(
        args.dir, args.commit, f"step {step['n']} implementation head"
    )
    if branch_tip != supplied_head:
        die(f"step {step['n']} implementation head is not the declared branch tip")
    verified_commits = verify_local_range(
        args.dir, range_base, args.commit, f"step {step['n']} implementation"
    )
    step["receipts"]["implement"] = {
        "branch": args.branch,
        "commit": args.commit,
        "tests": args.tests,
        "verified_commits": verified_commits,
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
            "verified_commits": verified_commits,
            "legacy_issue_phase_skipped": legacy_phase,
        },
    )
    print(f"step {step['n']} implementation receipted; phase -> audit")


def audit_risk_ids(base_dir: str, state: dict) -> list[str]:
    """Return the exact ids from Protasis's receipted risk-register block."""
    study = receipted_source(base_dir, state, "study")
    if study is None:
        die("study receipt is unavailable for Covered validation")
    register = source_risk_register(study)["markdown"]
    risk_ids = []
    seen = set()
    for line in register.splitlines()[1:-1]:
        if not line.strip():
            continue
        risk_id = line.split("|", 1)[0].strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", risk_id):
            die("study risk register has an invalid id")
        if risk_id in seen:
            die("study risk register has a duplicate id")
        seen.add(risk_id)
        risk_ids.append(risk_id)
    if not risk_ids:
        die("study risk register has no ids")
    return risk_ids


def audit_baseline_blob(base_dir: str, step: dict, log_path: str) -> bytes:
    """Read the configured log blob at the last locally verified commit."""
    baseline_ref = last_local_commit(step)
    if not isinstance(baseline_ref, str) or not baseline_ref:
        die("audit baseline has no locally verified commit")
    baseline_commit = resolved_commit(
        base_dir, baseline_ref, "audit baseline commit"
    )
    listing = bounded_git(
        base_dir,
        ["ls-tree", "-z", "--full-tree", baseline_commit, "--", log_path],
        "audit baseline path cannot be read from its verified commit",
    )
    if not listing:
        return b""
    if not listing.endswith(b"\0"):
        die("audit baseline path returned an ambiguous Git result")
    entries = [entry for entry in listing.split(b"\0") if entry]
    if len(entries) != 1:
        die("audit baseline path returned an ambiguous Git result")
    metadata, separator, raw_path = entries[0].partition(b"\t")
    match = re.fullmatch(
        rb"(?P<mode>[0-7]{6}) (?P<kind>[a-z]+) "
        rb"(?P<object>[0-9a-f]{40}(?:[0-9a-f]{24})?)",
        metadata,
    )
    try:
        listed_path = raw_path.decode("utf-8")
    except UnicodeDecodeError:
        listed_path = None
    if separator != b"\t" or match is None or listed_path != log_path:
        die("audit baseline path returned an ambiguous Git result")
    if match.group("kind") != b"blob" or match.group("mode") not in (
        b"100644",
        b"100755",
    ):
        die("audit baseline path is not a regular Git blob")
    object_id = match.group("object").decode("ascii")
    size_text = tool_text(
        bounded_git(
            base_dir,
            ["cat-file", "-s", object_id],
            "audit baseline blob size cannot be read",
        ),
        "audit baseline blob size",
    ).strip()
    if not re.fullmatch(r"0|[1-9][0-9]*", size_text):
        die("audit baseline blob size is malformed")
    size = int(size_text)
    if size > SOURCE_BYTES_MAX:
        die(f"audit baseline blob exceeds {SOURCE_BYTES_MAX}-byte cap")
    blob = bounded_git(
        base_dir,
        ["cat-file", "blob", object_id],
        "audit baseline blob cannot be read",
    )
    if len(blob) != size:
        die("audit baseline blob length does not match Git metadata")
    return blob


def audit_delta_start(
    base_dir: str, state: dict, step: dict, log_path: str, data: bytes
) -> int:
    """Choose the durable boundary before the one unreceipted raw suffix."""
    latest_offset = None
    for prior_step in state.get("steps") or []:
        if as_dict(prior_step).get("n") > step["n"]:
            break
        rounds = as_dict(as_dict(prior_step).get("audit")).get("rounds") or []
        for round_entry in rounds:
            entry = as_dict(round_entry)
            if "log_end_offset" not in entry:
                continue
            if entry.get("log") != log_path:
                die("stored audit log path does not match the configured log")
            offset = entry["log_end_offset"]
            if isinstance(offset, bool) or not isinstance(offset, int):
                die("stored audit log end offset must be a non-boolean integer")
            if offset < 0 or offset > SOURCE_BYTES_MAX or offset >= len(data):
                die("stored audit log end offset is outside the current log")
            latest_offset = offset
    if latest_offset is not None:
        return latest_offset

    baseline = audit_baseline_blob(base_dir, step, log_path)
    if len(data) <= len(baseline):
        die("audit log does not append a new record after its Git baseline")
    if data[:len(baseline)] != baseline:
        die("audit log changed before its Git baseline boundary")
    return len(baseline)


def audit_covered(value: str, expected_ids: list[str]) -> None:
    """Check total, unique risk disposition without retaining or printing prose."""
    expected = set(expected_ids)
    dispositions = {}
    for raw in value.split(";"):
        item = raw.strip()
        if not item or item.count("=") != 1:
            die("audit record Covered has a malformed risk disposition")
        risk_id, disposition = (part.strip() for part in item.split("=", 1))
        if risk_id in dispositions:
            die("audit record Covered has a duplicate risk id")
        if risk_id not in expected:
            die("audit record Covered has an unknown risk id")
        if disposition not in AUDIT_COVERAGE_VALUES:
            die("audit record Covered has an invalid disposition")
        dispositions[risk_id] = disposition
    missing = [risk_id for risk_id in expected_ids if risk_id not in dispositions]
    if missing:
        die("audit record Covered is missing a study risk id")


def audit_table_cells(line: str) -> list[str]:
    """Split one raw row at pipes not escaped by an odd backslash run."""
    trailing_slashes = len(line) - 1 - len(line[:-1].rstrip("\\"))
    if (
        len(line) < 2
        or not line.startswith("|")
        or not line.endswith("|")
        or trailing_slashes % 2
    ):
        return []
    cells = [""]
    slashes = 0
    for char in line[1:-1]:
        if char == "|" and slashes % 2 == 0:
            cells.append("")
        else:
            cells[-1] += char
        slashes = slashes + 1 if char == "\\" else 0
    return [cell.strip() for cell in cells]


def audit_raw_field(line: str, label: str) -> str:
    """Read one exact raw field line without exposing its value."""
    prefix = f"{label}: "
    if not line.startswith(prefix):
        die(f"audit record is missing or malformed {label}")
    value = line[len(prefix):]
    if not value or not value.strip() or value != value.strip():
        die(f"audit record {label} must have a canonical non-empty value")
    return value


def audit_record_bytes(data: bytes, start: int) -> bytes:
    """Return the exact LF-only record after its boundary separator."""
    if start == 0:
        separator = b""
    elif data[start - 1:start] == b"\n":
        separator = b"\n"
    else:
        separator = b"\n\n"
    delta = data[start:]
    if not delta.startswith(separator):
        die("audit record has a non-canonical boundary separator")
    record = delta[len(separator):]
    if not record or b"\r" in delta:
        die("audit record must use LF line endings")
    if not record.endswith(b"\n"):
        die("audit record must end with one LF at EOF")
    for physical in record.split(b"\n"):
        if len(physical) > AUDIT_PHYSICAL_LINE_BYTES_MAX:
            die(
                "audit record has a physical line over "
                f"{AUDIT_PHYSICAL_LINE_BYTES_MAX}-byte cap"
            )
    return record


def audit_line(lines: list[str], index: int, expected: str, label: str) -> int:
    """Consume one exact line from the raw record grammar."""
    if index >= len(lines) or lines[index] != expected:
        die(f"audit record has a non-canonical {label}")
    return index + 1


def audit_field_line(
    lines: list[str], index: int, label: str
) -> tuple[int, str]:
    if index >= len(lines):
        die(f"audit record is missing {label}")
    return index + 1, audit_raw_field(lines[index], label)


def parse_audit_record(
    record: bytes, base_dir: str, state: dict, step: dict, args
) -> tuple[str, str]:
    """Validate the one exact raw suffix and return schema and timestamp."""
    try:
        text = record.decode("utf-8")
    except UnicodeDecodeError:
        die("audit record delta is not UTF-8 text")
    lines = text[:-1].split("\n")
    round_number = len(step["audit"]["rounds"]) + 1
    heading_prefix = (
        f"## {state['topic']}, step {step['n']}, round {round_number} -- "
    )
    if not lines or not lines[0].startswith(heading_prefix):
        die("audit record heading does not match topic, step, and round")
    timestamp = lines[0][len(heading_prefix):]
    if not AUDIT_TIMESTAMP_RE.fullmatch(timestamp):
        die("audit record timestamp must be YYYY-MM-DDTHH:MM:SSZ UTC")
    try:
        parsed_timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        die("audit record timestamp is not calendar-valid")
    if parsed_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") != timestamp:
        die("audit record timestamp is not canonical UTC")

    index = 1
    index = audit_line(lines, index, "", "blank line after heading")
    index, schema = audit_field_line(lines, index, "Audit schema")
    if schema != AUDIT_RECORD_SCHEMA:
        die(f"Audit schema must be {AUDIT_RECORD_SCHEMA}")
    index = audit_line(lines, index, "", "blank line after Audit schema")
    index, covered = audit_field_line(lines, index, "Covered")
    audit_covered(covered, audit_risk_ids(base_dir, state))
    index = audit_line(lines, index, "", "blank line after Covered")
    index, _ = audit_field_line(lines, index, "Not checked")
    index = audit_line(lines, index, "", "blank line after Not checked")
    index, verdict = audit_field_line(lines, index, "Elenchus verdict")
    expected_verdict = args.elenchus_verdict or "null"
    if verdict != expected_verdict:
        die("audit record Elenchus verdict does not match the receipt")
    index = audit_line(lines, index, "", "blank line after Elenchus verdict")
    index = audit_line(
        lines, index, AUDIT_FINDINGS_HEADER, "findings table header"
    )
    index = audit_line(
        lines, index, AUDIT_FINDINGS_SEPARATOR, "findings table separator"
    )

    row_count = 1 if args.findings == 0 else args.findings
    rows = []
    for _ in range(row_count):
        if index >= len(lines):
            die("audit record findings table row count does not match --findings")
        row = lines[index]
        cells = audit_table_cells(row)
        if len(cells) != 5 or any(not cell for cell in cells):
            die("audit record findings table has a malformed data row")
        rows.append(row)
        index += 1
    if args.findings == 0:
        if rows != [AUDIT_ZERO_FINDING_ROW]:
            die("audit record findings table must use the exact zero-finding row")
    elif AUDIT_ZERO_FINDING_ROW in rows:
        die("audit record findings table row count does not match --findings")
    if index >= len(lines) or lines[index] != "":
        die("audit record findings table row count does not match --findings")
    index += 1
    index, _ = audit_field_line(lines, index, "Leads not pursued")
    if index != len(lines):
        die("audit record has content after Leads not pursued")
    return schema, timestamp


def validated_audit_record(
    base_dir: str, state: dict, step: dict, args
) -> dict:
    """Validate one raw Warden append and return only receipt-safe evidence."""
    audit = as_dict(as_dict(state.get("config")).get("audit"))
    log_path, data = read_configured_audit_log(
        base_dir, audit.get("log_path"), args.log
    )
    entry_start = audit_delta_start(base_dir, state, step, log_path, data)
    entry_bytes = audit_record_bytes(data, entry_start)
    schema, timestamp = parse_audit_record(
        entry_bytes, base_dir, state, step, args
    )
    synopsis_path = os.path.join(
        os.path.dirname(__file__), "audit_synopsis.py"
    )
    if not os.path.isfile(synopsis_path):
        die("audit synopsis renderer is unavailable")
    try:
        specification = importlib.util.spec_from_file_location(
            "fiat_audit_synopsis", synopsis_path
        )
        if specification is None or specification.loader is None:
            die("audit synopsis renderer cannot be loaded")
        renderer = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(renderer)
    except (OSError, ImportError, SyntaxError):
        die("audit synopsis renderer cannot be loaded")
    try:
        synopsis_sha256 = renderer.validate_committed_synopsis(
            base_dir, log_path, data
        )
    except renderer.SynopsisError as error:
        die(str(error))
    return {
        "schema": schema,
        "log": log_path,
        "record_timestamp": timestamp,
        "entry_sha256": hashlib.sha256(entry_bytes).hexdigest(),
        "log_end_offset": len(data),
        "synopsis_sha256": synopsis_sha256,
    }


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
    if args.fixes_commit and args.elenchus_verdict is None:
        die(
            "--elenchus-verdict is required with --fixes-commit; accepted values: "
            + ", ".join(ELENCHUS_VERDICTS)
        )
    if args.elenchus_verdict is not None and not args.fixes_commit:
        die("--elenchus-verdict requires --fixes-commit")

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

    record = validated_audit_record(args.dir, state, step, args)

    verified_commits = []
    if args.fixes_commit:
        base = last_local_commit(step)
        if not base:
            die(f"step {step['n']} has no verified implementation commit")
        verified_commits = verify_local_range(
            args.dir, base, args.fixes_commit, f"step {step['n']} audit fixes"
        )
    entry = {
        "round": len(rounds) + 1,
        "findings": args.findings,
        **record,
        "fixes_commit": args.fixes_commit,
        "elenchus_verdict": args.elenchus_verdict,
        "verified_commits": verified_commits,
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
    tail += f"; Elenchus {entry['elenchus_verdict'] or 'null'}"
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
    strict_log = last.get("schema") == AUDIT_RECORD_SCHEMA
    if strict_log and args.log is not None and args.log != last.get("log"):
        die("--log must name the final round's checked audit log")
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
    verified_fixes = []
    recorded_fix = next(
        (r.get("fixes_commit") for r in reversed(rounds) if r.get("fixes_commit")),
        None,
    )
    if fixes_ref and fixes_ref != recorded_fix:
        base = last_local_commit(step)
        if not base:
            die(f"step {step['n']} has no verified commit before its fixes reference")
        verified_fixes = verify_local_range(
            args.dir, base, fixes_ref, f"step {step['n']} audit closure fixes"
        )
    step["receipts"]["audit"] = {
        "rounds": len(rounds),
        "clean": clean,
        "no_further_leads": bool(args.no_further_leads),
        "reason": args.reason,
        "fixes_ref": fixes_ref,
        "log": (
            last.get("log") if strict_log else args.log or last.get("log")
        ),
        "verified_fixes": verified_fixes,
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
    range_base = args.pr_base if stacked else state["base"]
    branch = (
        step_branch_name(state, step)
        if stacked
        else as_dict(step["receipts"].get("implement")).get("branch")
    )
    if not isinstance(branch, str) or not branch:
        die("step push has no recorded implementation branch")
    branch_tip = resolved_commit(args.dir, branch, f"step {step['n']} pushed branch")
    supplied_head = resolved_commit(args.dir, args.head_commit, f"step {step['n']} push head")
    if branch_tip != supplied_head:
        die(f"step {step['n']} push head is not the pushed branch tip")
    verified_commits = verify_local_range(
        args.dir, range_base, args.head_commit, f"step {step['n']} push"
    )
    pr_record = inspect_pull_request(
        args.dir,
        args.pr_url,
        expected_head=branch,
        expected_base=(args.pr_base if stacked else state["base"]),
        expected_head_sha=verified_commits[-1],
        expected_merge_sha=args.merge_commit,
    )
    github_verified = verify_github_commits(args.dir, verified_commits)
    merge_verified = []
    if args.merge_commit:
        merge_verified = verify_github_commits(args.dir, [args.merge_commit])
    step["receipts"]["push"] = {
        "pr_url": args.pr_url,
        "head_commit": args.head_commit,
        "pr_base": args.pr_base,
        "merge_commit": args.merge_commit,
        "closed_issue_url": args.closed_issue_url,
        "verified_commits": verified_commits,
        "github_verified": github_verified,
        "github_merge_verified": merge_verified,
        "pull_request": pr_record,
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
    step = state["steps"][args.step - 1]
    push_receipt = as_dict(step["receipts"].get("push"))
    pr_record = inspect_pull_request(
        args.dir,
        pending["pr_url"],
        expected_head=pending["branch"],
        expected_base=pending["into"],
        expected_head_sha=None,
        expected_merge_sha=args.merge_commit,
    )
    remote_head = remote_branch_tip(args.dir, pending["branch"])
    if pr_record["head_sha"] != remote_head:
        die("recorded pull request head does not match its remote branch tip")
    recorded_local = push_receipt.get("verified_commits")
    recorded_github = push_receipt.get("github_verified")
    recorded_current = (
        isinstance(recorded_local, list)
        and isinstance(recorded_github, list)
        and recorded_local == recorded_github
        and bool(recorded_local)
        and all(isinstance(sha, str) and COMMIT_RE.fullmatch(sha) for sha in recorded_local)
        and recorded_local[-1] == remote_head
    )
    if recorded_current:
        effective_push = {
            "repaired": False,
            "pr_base": push_receipt.get("pr_base"),
            "head": remote_head,
            "verified_commits": recorded_local,
            "github_verified": recorded_github,
        }
    else:
        expected_pr_base = step_pr_base(state, step)
        pr_base = push_receipt.get("pr_base")
        if not isinstance(pr_base, str) or pr_base != expected_pr_base:
            die("recorded step pull request has no exact PR base for repair")
        repaired_local = verify_local_range(
            args.dir,
            pr_base,
            remote_head,
            f"step {step['n']} merge-time push repair",
        )
        repaired_github = verify_github_commits(args.dir, repaired_local)
        effective_push = {
            "repaired": True,
            "pr_base": pr_base,
            "head": remote_head,
            "verified_commits": repaired_local,
            "github_verified": repaired_github,
        }
    github_verified = verify_github_commits(args.dir, [args.merge_commit])
    integrate = state.setdefault("integrate", {"merged": [], "merges": {}})
    integrate.setdefault("merged", []).append(args.step)
    integrate.setdefault("merges", {})[str(args.step)] = {
        "branch": pending["branch"],
        "into": pending["into"],
        "merge_commit": args.merge_commit,
        "github_verified": github_verified,
        "pull_request": pr_record,
        "effective_push": effective_push,
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
            "github_verified": github_verified,
            "pull_request": pr_record,
            "effective_push": effective_push,
        },
    )
    remaining = len(state["steps"]) - len(integrate["merged"])
    tail = f"{remaining} step(s) left in the stack" if remaining else "stack merged"
    print(f"step {args.step} merged into {pending['into']}; {tail}")


def done_sync_run(args, state: dict) -> None:
    """Receipt one signed merge of the current base into a completed run stack."""
    if state["phase"] != "integrate":
        die(
            "sync-run is an integrate-phase receipt; the run is in phase "
            f"'{state['phase']}'"
        )
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    pending = _integrate_directive(state)
    if pending["do"] != "integrate":
        die(
            f"step {pending['step']} still has to merge into "
            f"'{run_branch_of(state)}' before the run can sync"
        )
    integrate = state.setdefault("integrate", {"merged": [], "merges": {}})
    if integrate.get("sync") is not None:
        die("the run branch already has a recorded integration sync")
    if not args.commit:
        die("--commit is required for sync-run")
    if not args.base_commit:
        die("--base-commit is required for sync-run")
    sync_tip = require_full_sha(args.commit, "run sync commit")
    base_tip = require_full_sha(args.base_commit, "run sync base commit")
    remote_tip = remote_branch_tip(args.dir, run_branch_of(state))
    if remote_tip != sync_tip:
        die("run sync commit does not match the remote run branch tip")
    remote_base = remote_branch_tip(
        args.dir, state["base"], "remote base branch tip"
    )
    if remote_base != base_tip:
        die("run sync base commit does not match the remote base branch tip")
    final_step = state["steps"][-1]["n"]
    merge_records = as_dict(integrate.get("merges"))
    final_merge = as_dict(merge_records.get(str(final_step))).get("merge_commit")
    recorded_tip = require_full_sha(final_merge, "final recorded step merge")
    parents = commit_parents(args.dir, sync_tip, "run sync commit")
    expected_parents = [recorded_tip, base_tip]
    if parents != expected_parents:
        die(
            "run sync merge parents do not match the final recorded step merge "
            "and the exact remote base tip"
        )
    verify_local_commit(args.dir, sync_tip, "run branch integration sync")
    github_verified = verify_github_commits(args.dir, [sync_tip])
    integrate["sync"] = {
        "commit": sync_tip,
        "base_head": base_tip,
        "parents": parents,
        "github_verified": github_verified,
    }
    commit(args.dir, state, "done:sync-run", integrate["sync"])
    print(
        f"{run_branch_of(state)} synced with {state['base']} at {base_tip}; "
        "integration may continue"
    )


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
    remote_tip = remote_branch_tip(args.dir, run_branch_of(state))
    final_step = state["steps"][-1]["n"]
    integrate = as_dict(state.get("integrate"))
    merge_records = as_dict(integrate.get("merges"))
    final_merge = as_dict(merge_records.get(str(final_step))).get("merge_commit")
    recorded_tip = require_full_sha(final_merge, "final recorded step merge")
    sync = as_dict(integrate.get("sync"))
    expected_tip = recorded_tip
    if sync:
        expected_tip = require_full_sha(sync.get("commit"), "recorded run sync commit")
    if remote_tip != expected_tip:
        if sync:
            die("remote run branch tip does not match the recorded run sync commit")
        die("remote run branch tip does not match the final recorded step merge")
    pr_record = inspect_pull_request(
        args.dir,
        args.pr_url,
        expected_head=run_branch_of(state),
        expected_base=state["base"],
        expected_head_sha=remote_tip,
        expected_merge_sha=args.merge_commit,
        expected_head_label="remote run branch tip",
    )
    github_verified = verify_github_commits(args.dir, [args.merge_commit])
    state["receipts"]["integrate"] = {
        "run_branch": run_branch_of(state),
        "base": state["base"],
        "pr_url": args.pr_url,
        "merge_commit": args.merge_commit,
        "closed_issue_url": args.closed_issue_url,
        "carried_forward": carried_forward_record(run_pr_path(args.dir)),
        "github_verified": github_verified,
        "pull_request": pr_record,
        "run_head": remote_tip,
        "final_step_merge": recorded_tip,
    }
    if sync:
        state["receipts"]["integrate"]["sync"] = sync
    worktree = state.get("worktree")
    if worktree and os.path.isdir(worktree):
        state["receipts"]["integrate"]["worktree_clean"] = worktree_is_clean(worktree)
    state["phase"] = "done"
    commit(args.dir, state, "done:integrate", state["receipts"]["integrate"])
    if worktree and os.path.isdir(worktree):
        clean = state["receipts"]["integrate"]["worktree_clean"]
        print(
            f"run worktree {worktree} "
            + ("is clean; `hexctl reset` will archive the run and remove it"
               if clean else
               "holds modifications; `hexctl reset` will archive the run and "
               "keep the tree. Nothing is ever forced")
        )
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
    "sync-run": done_sync_run,
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


# This is Protasis's accepted STEP grammar with only the number-group name
# changed for this packet shape. The selector carries bytes accepted by that
# authority; it does not impose a narrower second grammar.
STEP_HEADING_RE = re.compile(
    r"^##\s+Step\s+(?P<number>\d+)\s*:\s*(?P<title>.*?)\s*$"
)
MARKDOWN_FENCE_RE = re.compile(
    r"^ {0,3}(?P<mark>`{3,}|~{3,})(?P<remainder>.*)$"
)
RISK_REGISTER_INFO = "risk-register"
AMENDMENT_HEADING_RE = re.compile(
    r"^###\s+Amendment\s+--\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$"
)
AMENDMENT_FIELDS = ("What changed", "Why", "Steps touched", "Still holding")
AMENDMENT_FIELD_RE = re.compile(
    r"^\*\*(?P<name>What changed|Why|Steps touched|Still holding)\.\*\*"
    r"(?:\s*(?P<value>.*))?$"
)
ANY_AMENDMENT_FIELD_RE = re.compile(r"^\*\*[^*\n]+\.\*\*(?:\s*.*)?$")
STEP_VERDICT_RE = re.compile(
    r"Step\s+(?P<step>[1-9]\d*)\s*:\s*"
    r"entry\s+(?P<entry>holds|broken)\s*;\s*"
    r"exit\s+(?P<exit>holds|broken)\s*\.",
    re.IGNORECASE,
)


def markdown_fence(line: str):
    """Return one CommonMark fence marker, excluding invalid backtick info."""
    fence = MARKDOWN_FENCE_RE.match(line)
    if (
        fence is not None
        and fence.group("mark").startswith("`")
        and "`" in fence.group("remainder")
    ):
        return None
    return fence


def markdown_blank(line: str) -> bool:
    """Whether one physical line is blank under CommonMark's ASCII grammar."""
    return re.fullmatch(r"[ \t]*", line) is not None


def markdown_physical_lines(text: str):
    """Yield only CommonMark's LF, CRLF, and CR-delimited physical lines."""
    start = 0
    for ending in re.finditer(r"\r\n|\r|\n", text):
        yield text[start:ending.end()]
        start = ending.end()
    if start < len(text):
        yield text[start:]


def markdown_lines(text: str):
    """Yield source offsets and fence state without treating quoted headings as real."""
    offset = 0
    open_mark = None
    open_length = None
    for physical in markdown_physical_lines(text):
        line = physical.rstrip("\r\n")
        fence = markdown_fence(line)
        was_open = open_mark
        if fence:
            sequence = fence.group("mark")
            mark = sequence[0]
            if open_mark is None:
                open_mark = mark
                open_length = len(sequence)
            elif (
                mark == open_mark
                and len(sequence) >= open_length
                and not fence.group("remainder").strip(" \t")
            ):
                open_mark = None
                open_length = None
            yield offset, offset + len(physical), line, True, was_open
        else:
            yield offset, offset + len(physical), line, open_mark is not None, was_open
        offset += len(physical)


def _study_amendment_boundary(text: str, expected: str) -> tuple[int, int, str]:
    """Find the one real final amendment whose byte prefix has the receipt hash."""
    headings = []
    for start, _, line, in_fence, _ in markdown_lines(text):
        if in_fence:
            continue
        match = AMENDMENT_HEADING_RE.fullmatch(line)
        if match:
            headings.append((start, match.group("date")))

    matches = []
    for heading_start, date_text in headings:
        boundary = heading_start
        candidates = [boundary]
        while boundary > 0 and text[boundary - 1] in "\r\n":
            boundary -= 1
            candidates.append(boundary)
        for candidate in candidates:
            digest = hashlib.sha256(text[:candidate].encode("utf-8")).hexdigest()
            if digest == expected:
                matches.append((candidate, heading_start, date_text))

    if not matches:
        die(
            "amendment candidate does not preserve the currently receipted "
            "study bytes as its exact prefix"
        )
    if len(matches) != 1:
        die("amendment candidate has an ambiguous receipted prefix boundary")
    boundary, heading_start, date_text = matches[0]
    later = [start for start, _ in headings if start > heading_start]
    if later:
        die("amendment candidate appends more than one final amendment block")
    try:
        datetime.date.fromisoformat(date_text)
    except ValueError:
        die(f"amendment heading has an invalid calendar date: {date_text}")
    return boundary, heading_start, date_text


def _study_amendment_fields(text: str, heading_start: int) -> dict[str, str]:
    """Read the four ordered fields in the final amendment and nothing else."""
    fields = []
    headings_after = []
    for start, end, line, in_fence, _ in markdown_lines(text):
        if start <= heading_start or in_fence:
            continue
        if re.fullmatch(r"#{1,3}\s+.*", line):
            headings_after.append(line)
        match = AMENDMENT_FIELD_RE.fullmatch(line)
        if match:
            fields.append((start, end, match.group("name"), match.group("value") or ""))
            continue
        if ANY_AMENDMENT_FIELD_RE.fullmatch(line):
            die(f"amendment carries an unexpected field: {line}")
    if headings_after:
        die("amendment block must be the final section of the study")

    names = [item[2] for item in fields]
    if names != list(AMENDMENT_FIELDS):
        for name in AMENDMENT_FIELDS:
            count = names.count(name)
            if count != 1:
                die(f"amendment field '{name}' must occur exactly once (got {count})")
        die("amendment fields must appear in the accepted four-field order")

    values = {}
    for index, (_, end, name, first_line) in enumerate(fields):
        stop = fields[index + 1][0] if index + 1 < len(fields) else len(text)
        value = " ".join((first_line + "\n" + text[end:stop]).split())
        if not value:
            die(f"amendment field '{name}' must not be empty")
        values[name] = value
    return values


def _study_step_verdicts(fields: dict[str, str], state: dict) -> tuple[list[int], list[dict]]:
    """Bind touched steps and exact entry/exit verdicts to every unbuilt step."""
    touched_text = fields["Steps touched"]
    if re.search(r"\bsteps?\b", touched_text, re.IGNORECASE) is None:
        die("amendment field 'Steps touched' must name at least one step number")
    touched = sorted({int(value) for value in re.findall(r"\b\d+\b", touched_text)})
    if not touched:
        die("amendment field 'Steps touched' must name at least one step number")

    all_steps = {step["n"]: step for step in state["steps"]}
    unknown_touched = [number for number in touched if number not in all_steps]
    if unknown_touched:
        die(f"amendment names unknown touched step(s): {unknown_touched}")
    completed_touched = [
        number for number in touched if all_steps[number].get("status") == "done"
    ]
    if completed_touched:
        die(f"amendment cannot rewrite completed step(s): {completed_touched}")

    verdict_text = fields["Still holding"]
    verdicts = []
    cursor = 0
    for match in STEP_VERDICT_RE.finditer(verdict_text):
        if verdict_text[cursor:match.start()].strip():
            die(
                "amendment field 'Still holding' must contain only unambiguous "
                "'Step N: entry holds|broken; exit holds|broken.' verdicts"
            )
        verdicts.append(
            {
                "step": int(match.group("step")),
                "entry": match.group("entry").lower(),
                "exit": match.group("exit").lower(),
            }
        )
        cursor = match.end()
    if verdict_text[cursor:].strip():
        die(
            "amendment field 'Still holding' must contain only unambiguous "
            "'Step N: entry holds|broken; exit holds|broken.' verdicts"
        )

    numbers = [verdict["step"] for verdict in verdicts]
    duplicates = sorted({number for number in numbers if numbers.count(number) > 1})
    if duplicates:
        die(f"amendment has duplicate step verdict(s): {duplicates}")

    unbuilt = sorted(
        step["n"] for step in state["steps"] if step.get("status") != "done"
    )
    completed = sorted(set(numbers) - set(unbuilt))
    if completed:
        die(f"amendment cannot rewrite completed or unknown step(s): {completed}")
    missing = sorted(set(unbuilt) - set(numbers))
    if missing:
        die(f"amendment is missing verdict(s) for unbuilt step(s): {missing}")
    return touched, sorted(verdicts, key=lambda item: item["step"])


def _check_amended_study(base_dir: str, candidate: bytes) -> None:
    """Run Protasis over the exact captured bytes through a controlled file."""
    root = state_root(base_dir)
    os.makedirs(root, exist_ok=True)
    descriptor, path = tempfile.mkstemp(prefix="amended-study-", suffix=".md", dir=root)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(candidate)
            handle.flush()
            os.fsync(handle.fileno())
        checker = os.path.join(plugin_root(), "skills", "protasis", "scripts", "protasis.py")
        bounded_tool(
            base_dir,
            sys.executable,
            [checker, "--study", path],
            "Protasis rejected the amendment candidate",
        )
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def _replace_study_bytes(path: str, data: bytes) -> None:
    """Replace the canonical study atomically after every validation has passed."""
    directory = os.path.dirname(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".hexctl-study-", dir=directory)
    try:
        os.fchmod(descriptor, os.stat(path).st_mode & 0o777)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        parent = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    except OSError as exc:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        die(f"study artefact could not be replaced atomically: {exc}", 1)


def _study_amendment_record(
    state: dict, expected: str, candidate: bytes
) -> dict:
    """Validate captured candidate bytes and return only bounded receipt data."""
    text = decoded_source(candidate, "study amendment candidate")
    boundary, heading_start, date_text = _study_amendment_boundary(text, expected)
    fields = _study_amendment_fields(text, heading_start)
    touched, verdicts = _study_step_verdicts(fields, state)
    prefix_bytes = text[:boundary].encode("utf-8")
    amendment_bytes = candidate[len(prefix_bytes):]
    return {
        "date": date_text,
        "prior_sha256": hashlib.sha256(prefix_bytes).hexdigest(),
        "new_sha256": hashlib.sha256(candidate).hexdigest(),
        "amendment_sha256": hashlib.sha256(amendment_bytes).hexdigest(),
        "steps_touched": touched,
        "step_verdicts": verdicts,
    }


def _apply_study_amendment_receipt(receipt: dict, amendment: dict) -> None:
    history = receipt.setdefault("amendments", [])
    history.append(amendment)
    receipt["sha256"] = amendment["new_sha256"]


def _commit_or_complete_study_amendment(
    base_dir: str, state: dict, amendment: dict
) -> None:
    """Do not duplicate an event written before an interrupted state replace."""
    last = None
    path = ledger_path(base_dir)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = [line for line in handle.read().splitlines() if line.strip()]
        if lines:
            last = json.loads(lines[-1])
    except (OSError, ValueError):
        last = None
    expected_state = state_fingerprint(state)
    if (
        isinstance(last, dict)
        and last.get("event") == "amend:study"
        and last.get("data") == amendment
        and last.get("state") == expected_state
    ):
        save_state(base_dir, state)
        return
    commit(base_dir, state, "amend:study", amendment)


def _recover_study_amendment(
    base_dir: str, state: dict, pending: dict
) -> bool:
    """Finish or roll back the labelled gap left by an interrupted command.

    Returns True after the pending amendment is committed or visibly rolled
    back. A later command may retry a rolled-back candidate as a fresh
    transaction.
    """
    receipt = as_dict(as_dict(state.get("receipts")).get("study"))
    artifact = receipt.get("artifact")
    if artifact != pending["artifact"]:
        die("pending study amendment does not match the current artefact path", 1)
    amendment = pending["amendment"]
    prior = amendment.get("prior_sha256")
    new = amendment.get("new_sha256")
    if not all(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
        for value in (prior, new)
    ):
        die("pending study amendment has invalid receipt digests", 1)

    canonical_path, canonical = read_bounded_source(
        base_dir, artifact, "study artefact"
    )
    actual = hashlib.sha256(canonical).hexdigest()
    current = receipt.get("sha256")

    if current == new:
        history = receipt.get("amendments")
        if (
            actual != new
            or not isinstance(history, list)
            or not history
            or history[-1] != amendment
        ):
            die("pending study amendment disagrees with the committed receipt", 1)
        verify_run(base_dir, allow_pending_amendment=True)
        clear_study_amendment_pending(base_dir)
        print(f"study amendment recovered: committed {new}")
        return True

    if current != prior or state_fingerprint(state) != pending["state_before_sha256"]:
        die("pending study amendment no longer matches controller state", 1)
    if actual == prior:
        verify_run(base_dir, allow_pending_amendment=True)
        clear_study_amendment_pending(base_dir)
        print(f"study amendment recovered: rolled back to {prior}")
        return True
    if actual != new:
        die(
            "pending study amendment found neither the prior nor candidate bytes; "
            "restore one recorded digest before recovery",
            1,
        )

    recovered = _study_amendment_record(state, prior, canonical)
    _check_amended_study(base_dir, canonical)
    if recovered != amendment:
        die("pending study amendment metadata does not match the candidate bytes", 1)
    existing_history = receipt.get("amendments")
    if existing_history is not None and not isinstance(existing_history, list):
        die("study receipt amendments history must be an array", 1)
    _apply_study_amendment_receipt(receipt, amendment)
    _commit_or_complete_study_amendment(base_dir, state, amendment)
    verify_run(base_dir, allow_pending_amendment=True)
    clear_study_amendment_pending(base_dir)
    print(f"study amendment recovered: recorded {new}")
    return True


def cmd_amend_study(args) -> None:
    """Receipt one append-only Protasis amendment while build steps are active."""
    state = load_state(args.dir, allow_pending_amendment=True)
    pending = load_study_amendment_pending(args.dir)
    if pending is not None and _recover_study_amendment(args.dir, state, pending):
        return
    if state.get("halted"):
        die(f"run is halted ({state['halted']['reason']}); `hexctl resume` first")
    if state.get("phase") != "steps":
        die("study amendments are accepted only while build steps are active")
    require_no_amendment_block(state)

    receipt = as_dict(as_dict(state.get("receipts")).get("study"))
    expected = receipt.get("sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        die("study amendment requires a source-bound study receipt with sha256")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, str) or not artifact:
        die("study receipt has no artefact path")

    candidate_arg = _require_file(args.artifact, "artifact")
    candidate_path, candidate = read_bounded_source(
        args.dir, candidate_arg, "study amendment candidate"
    )
    canonical_path, canonical_bytes = read_bounded_source(
        args.dir, artifact, "study artefact"
    )
    if candidate_path != canonical_path:
        actual = hashlib.sha256(canonical_bytes).hexdigest()
        if actual != expected and canonical_bytes != candidate:
            die(
                f"study artefact digest changed: expected {expected}, got {actual}; "
                "restore the receipted bytes or halt the run"
            )

    amendment = _study_amendment_record(state, expected, candidate)
    _check_amended_study(args.dir, candidate)
    existing_history = receipt.get("amendments")
    if existing_history is not None and not isinstance(existing_history, list):
        die("study receipt amendments history must be an array", 1)

    pending = {
        "version": 1,
        "artifact": artifact,
        "state_before_sha256": state_fingerprint(state),
        "amendment": amendment,
    }
    write_study_amendment_pending(args.dir, pending)
    # Replace from the captured bytes even when the candidate is already the
    # canonical path. An editor can change that path after the bounded read;
    # the receipt must name the bytes this command validated, not a later read.
    _replace_study_bytes(canonical_path, candidate)
    _apply_study_amendment_receipt(receipt, amendment)
    commit(args.dir, state, "amend:study", amendment)
    verify_run(args.dir, allow_pending_amendment=True)
    clear_study_amendment_pending(args.dir)

    current = state["current_step"]
    verdict = next(item for item in amendment["step_verdicts"] if item["step"] == current)
    disposition = (
        "holds" if verdict["entry"] == "holds" and verdict["exit"] == "holds"
        else "broken; dependent work is blocked"
    )
    print(
        f"study amended: prior {amendment['prior_sha256']}; "
        f"new {amendment['new_sha256']}; amendment "
        f"{amendment['amendment_sha256']}; step {current} {disposition}"
    )


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
        if start is None and was_open is None and is_fence:
            opened = markdown_fence(line)
            if opened:
                mark = opened.group("mark")
                info = line.strip()[len(mark):].strip()
            else:
                info = None
            if info == RISK_REGISTER_INFO:
                start = line_start
                risk_mark = mark[0]
            continue
        if start is not None and is_fence and was_open == risk_mark:
            fence = markdown_fence(line)
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


def bounded_run(base_dir: str, program: str, argv: list[str]) -> tuple[int, bytes]:
    """Run one fixed-argv tool and return its status and output.

    The reader itself: no shell, a hard timeout, a hard output cap, and nothing
    from the child's stream in any diagnosis. Callers that treat a non-zero
    status as fatal go through `bounded_tool`; callers for which a refusal is a
    real answer, such as git declining to remove a tree holding modifications,
    read the status here.
    """
    operation = f"{program} {argv[0]}" if argv else program
    try:
        process = subprocess.Popen(
            [program, *argv],
            cwd=os.path.realpath(base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
        )
    except OSError as exc:
        die(f"{operation} could not start")
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
                die(f"{operation} timed out after {GIT_TIMEOUT} seconds")
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
                    die(f"{operation} exceeded {GIT_OUTPUT_MAX}-byte output cap")
        returncode = process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        die(f"{operation} timed out after {GIT_TIMEOUT} seconds")
    finally:
        selector.close()
        process.stdout.close()
    return returncode, bytes(output)


def bounded_tool(
    base_dir: str,
    program: str,
    argv: list[str],
    refusal: str | None = None,
) -> bytes:
    """Run one fixed-argv tool without exposing its output in failures."""
    returncode, output = bounded_run(base_dir, program, argv)
    if returncode != 0:
        if refusal is not None:
            die(refusal)
        operation = f"{program} {argv[0]}" if argv else program
        die(f"{operation} failed with exit {returncode}")
    return output


def bounded_tool_status(base_dir: str, program: str, argv: list[str]) -> int:
    """The exit status of one fixed-argv tool, for callers a refusal informs."""
    return bounded_run(base_dir, program, argv)[0]


def bounded_git(base_dir: str, argv: list[str], refusal: str | None = None) -> bytes:
    return bounded_tool(base_dir, "git", argv, refusal)


WORKTREE_HOME = ("tmp", "fiat")
"""Where a run's worktree goes, under the repository's already-ignored scratch root.

Ignoring the home is not what keeps a scan honest: git reports a nested worktree as
one opaque directory either way. It is what keeps the next run startable, because
preflight refuses a dirty tree and an unignored directory here would show as
untracked.
"""


def flattened_run_branch(run_branch: str) -> str:
    """A run branch as one directory name, so one run maps to one path."""
    check_branch_name(run_branch)
    return run_branch.replace("/", "-")


def repository_root(base_dir: str) -> str:
    """The worktree root git reports for `base_dir`.

    A target that is not a Git repository refuses here rather than running in
    place. That is the fail-closed fallback the study chose, and it is a breaking
    change for anyone who relied on an in-place run.
    """
    root = os.path.realpath(base_dir)
    reported = bounded_git(
        base_dir,
        ["rev-parse", "--show-toplevel"],
        refusal=f"not a git repository: {root}",
    ).decode("utf-8", "replace").strip()
    if not reported:
        die(f"not a git repository: {root}")
    return os.path.realpath(reported)


def run_worktree_path(base_dir: str, run_branch: str) -> str:
    """The one path this run's worktree belongs at. Creates nothing."""
    return os.path.join(
        repository_root(base_dir), *WORKTREE_HOME, flattened_run_branch(run_branch)
    )


def check_worktree_path(root: str, candidate: str, registered: str | None = None) -> str:
    """Refuse a worktree path before anything is created at it.

    Five ways a path fails: it leaves the repository once resolved, a component on
    the way to it is a symlink leaving the repository, it is the repository root
    itself, it is a symlink, or it already exists as something other than this
    run's own tree.

    Occupancy is read off the supplied path with `lexists`, not off the resolved
    one. A dangling link resolves to a path that does not exist, so reading the
    target saw a free path and then returned the target rather than the path it
    was asked about -- which would put the run's tree somewhere the deriver never
    chose. A link at the derived path is refused whether it dangles or not: the
    run's tree is a real directory there, or it is nothing.

    The walk is over the supplied components rather than the resolved path. Horos
    finding S4-R1-01 is the reason: a control that inspects only the path it was
    given refuses a final-component symlink while stepping over one mid-path, and
    `git -C` resolves symlinks before it answers, so the refusal has to happen
    before git is asked anything. Traversal is refused on the raw components for
    the same reason -- normalising `..` first is what lets a symlink be stepped
    over lexically.

    Every refusal names the path, reads nothing at it, and writes nothing.
    """
    root = os.path.realpath(root)
    supplied = candidate
    if os.path.isabs(candidate):
        try:
            relative = os.path.relpath(candidate, root)
        except ValueError:
            die(f"worktree path escapes the repository: {supplied}")
    else:
        relative = candidate
    parts = [part for part in relative.split(os.sep) if part not in ("", ".")]
    if not parts or any(part == os.pardir for part in parts):
        die(f"worktree path escapes the repository: {supplied}")
    walked = root
    for part in parts:
        walked = os.path.join(walked, part)
        if os.path.islink(walked) and not contained_in(root, os.path.realpath(walked)):
            die(f"worktree path crosses a symlink out of the repository: {walked}")
    resolved = os.path.realpath(walked)
    if not contained_in(root, resolved) or resolved == root:
        die(f"worktree path escapes the repository: {supplied}")
    if os.path.lexists(walked):
        if os.path.islink(walked):
            die(f"worktree path is a symlink: {supplied}")
        if registered is None or os.path.realpath(registered) != resolved:
            die(f"worktree path is already occupied: {supplied}")
    return resolved


def checked_out_worktrees(base_dir: str) -> dict:
    """Branch -> worktree path, for every tree git currently knows about."""
    porcelain = bounded_git(base_dir, ["worktree", "list", "--porcelain"]).decode(
        "utf-8", "replace"
    )
    trees: dict[str, str] = {}
    path = None
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):].strip()
        elif line.startswith("branch ") and path is not None:
            trees[line[len("branch "):].strip().removeprefix("refs/heads/")] = path
    return trees


def refuse_checked_out_branch(base_dir: str, run_branch: str) -> None:
    """Git holds one branch in one tree, so a second checkout cannot be created.

    Refusing by name here is what turns `git worktree add`'s own failure into a
    sentence that says which branch and which tree, before anything is written.
    """
    existing = checked_out_worktrees(base_dir).get(run_branch)
    if existing is not None:
        die(f"run branch '{run_branch}' is already checked out at {existing}")


def breadcrumb_path(base_dir: str) -> str:
    return os.path.join(state_root(base_dir), WORKTREE_FILE)


def raw_breadcrumbs(base_dir: str) -> list[str]:
    """Every run this checkout recorded, live or not, as written."""
    try:
        with open(breadcrumb_path(base_dir), encoding="utf-8") as handle:
            return sorted({line.strip() for line in handle if line.strip()})
    except OSError:
        return []


def read_breadcrumbs(base_dir: str) -> list[str]:
    """Every run this checkout started that still has state, in path order.

    One line per run rather than one line per checkout. The issue asks for two
    runs against one repository that do not contend, so a second run has to be
    recordable rather than refused, and a resume has to be able to say which
    trees it found. Entries whose state has gone are dropped on the way out, so
    a finished or reset run stops being offered.
    """
    try:
        with open(breadcrumb_path(base_dir), encoding="utf-8") as handle:
            recorded = [line.strip() for line in handle if line.strip()]
    except OSError:
        return []
    return sorted({entry for entry in recorded if os.path.exists(state_path(entry))})


def write_breadcrumbs(base_dir: str, worktree: str | None = None) -> None:
    """Leave one line in the origin checkout naming the run's tree.

    This is the only thing a run writes into the checkout it was started from. A
    resume reads it so nobody has to remember the path, and it is one line rather
    than state because two state directories for one run is the confusion the
    breadcrumb exists to avoid.
    """
    root = state_root(base_dir)
    os.makedirs(root, exist_ok=True)
    gitignore = os.path.join(root, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w", encoding="utf-8") as handle:
            handle.write("*\n")
    entries = sorted(set(read_breadcrumbs(base_dir)) | ({worktree} if worktree else set()))
    with open(breadcrumb_path(base_dir), "w", encoding="utf-8") as handle:
        handle.write("".join(f"{entry}\n" for entry in entries))


def remove_run_worktree(base_dir: str, worktree: str, force: bool = False) -> bool:
    """Take the run's tree away, and say whether it went.

    Never forced by default. Git refuses to remove a tree holding modifications,
    and that refusal is the point: the worst outcome here is a directory somebody
    has to look at, never uncommitted work that vanished.
    """
    argv = ["worktree", "remove"]
    if force:
        argv.append("--force")
    argv.append(worktree)
    bounded_tool_status(base_dir, "git", argv)
    return not os.path.exists(worktree)


def archive_name(state: dict) -> str:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    topic = re.sub(r"[^a-z0-9]+", "-", state["topic"].lower()).strip("-")[:48]
    return f"{stamp}-{topic or 'completed-run'}"


def worktree_is_clean(worktree: str) -> bool:
    """True when git has nothing to lose in this tree.

    Read before anything is moved. Removal is never forced, so a tree holding
    work is kept and named instead, and the worst outcome here is a directory
    somebody has to look at.
    """
    porcelain = bounded_git(worktree, ["status", "--porcelain"])
    return not porcelain.strip()


def contained_in(root: str, resolved: str) -> bool:
    """True when `resolved` is `root` or sits underneath it."""
    try:
        return os.path.commonpath((root, resolved)) == root
    except ValueError:
        return False


def bounded_gh(base_dir: str, argv: list[str], refusal: str | None = None) -> bytes:
    return bounded_tool(base_dir, "gh", argv, refusal)


COMMIT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
COAUTHOR_TRAILER = "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>"
ORIGIN_TRAILER = "Wildcat-Origin: shoggoth"


def tool_text(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        die(f"{label} returned non-UTF-8 output")


def resolved_commit(base_dir: str, ref: str, label: str) -> str:
    data = bounded_git(
        base_dir,
        ["rev-parse", "--verify", f"{ref}^{{commit}}"],
        f"{label} does not resolve to a commit",
    )
    lines = [line.strip() for line in tool_text(data, label).splitlines() if line.strip()]
    if len(lines) != 1 or not COMMIT_RE.fullmatch(lines[0]):
        die(f"{label} did not resolve to one full commit SHA")
    return lines[0]


def remote_branch_tip(
    base_dir: str, branch: str, label: str = "remote run branch tip"
) -> str:
    check_branch_name(branch)
    expected_ref = f"refs/heads/{branch}"
    data = bounded_git(
        base_dir,
        ["ls-remote", "--refs", "origin", expected_ref],
        f"{label} could not be read",
    )
    lines = [line for line in tool_text(data, label).splitlines() if line]
    if len(lines) != 1:
        die(f"{label} must contain exactly one ref")
    fields = lines[0].split("\t")
    if (
        len(fields) != 2
        or not COMMIT_RE.fullmatch(fields[0])
        or fields[1] != expected_ref
    ):
        die(f"{label} is malformed")
    return fields[0]


def commit_parents(base_dir: str, commit_sha: str, label: str) -> list[str]:
    commit_sha = require_full_sha(commit_sha, label)
    data = bounded_git(
        base_dir,
        ["show", "-s", "--no-show-signature", "--format=%P", commit_sha],
        f"{label} parents cannot be read",
    )
    parents = tool_text(data, f"{label} parents").strip().split()
    if any(not COMMIT_RE.fullmatch(parent) for parent in parents):
        die(f"{label} returned a malformed parent SHA")
    return parents


def exact_commit_range(base_dir: str, base_ref: str, head_ref: str, label: str) -> list[str]:
    base = resolved_commit(base_dir, base_ref, f"{label} base")
    head = resolved_commit(base_dir, head_ref, f"{label} head")
    bounded_git(
        base_dir,
        ["merge-base", "--is-ancestor", base, head],
        f"{label} head is not descended from its declared base",
    )
    data = bounded_git(
        base_dir,
        ["rev-list", "--reverse", f"--max-count={GIT_PATHS_MAX + 1}", f"{base}..{head}"],
        f"{label} commit range cannot be enumerated",
    )
    commits = [line.strip() for line in tool_text(data, label).splitlines() if line.strip()]
    if len(commits) > GIT_PATHS_MAX:
        die(f"{label} commit range exceeds {GIT_PATHS_MAX} commits")
    if any(not COMMIT_RE.fullmatch(commit) for commit in commits):
        die(f"{label} commit range returned a malformed SHA")
    if not commits or commits[-1] != head:
        die(f"{label} commit range does not end at the declared head")
    if base in commits:
        die(f"{label} commit range includes its base")
    return commits


def verify_local_commit(base_dir: str, commit_sha: str, label: str) -> str:
    """Verify one exact locally created commit and its required trailers."""
    commit_sha = require_full_sha(commit_sha, label)
    bounded_git(
        base_dir,
        ["verify-commit", commit_sha],
        f"{label} commit {commit_sha} has no valid local signature",
    )
    body = tool_text(
        bounded_git(
            base_dir,
            ["show", "-s", "--no-show-signature", "--format=%B", commit_sha],
            f"{label} commit {commit_sha} message cannot be read",
        ),
        f"{label} commit message",
    )
    lines = body.splitlines()
    coauthors = lines.count(COAUTHOR_TRAILER)
    origins = lines.count(ORIGIN_TRAILER)
    if coauthors != 1:
        die(
            f"{label} commit {commit_sha} has {coauthors} exact Shoggoth "
            "co-author trailers; expected 1"
        )
    if origins != 1:
        die(
            f"{label} commit {commit_sha} has {origins} exact Wildcat-Origin "
            "trailers; expected 1"
        )
    return commit_sha


def verify_local_range(base_dir: str, base_ref: str, head_ref: str, label: str) -> list[str]:
    """Verify every locally created commit in one exact base-to-head range."""
    commits = exact_commit_range(base_dir, base_ref, head_ref, label)
    for commit_sha in commits:
        verify_local_commit(base_dir, commit_sha, label)
    return commits


REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GITHUB_HTTPS_RE = re.compile(
    r"^https://github\.com/(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
GITHUB_SSH_RE = re.compile(
    r"^(?:git@github\.com:|ssh://git@github\.com/)(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
GITHUB_PR_RE = re.compile(
    r"^https://github\.com/(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/(?P<number>[1-9][0-9]*)/?$"
)


def require_full_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        die(f"{label} must be a full commit SHA")
    return value


def target_repository(base_dir: str) -> str:
    data = bounded_git(
        base_dir,
        ["remote", "get-url", "origin"],
        "target origin could not be resolved",
    )
    lines = [line.strip() for line in tool_text(data, "target origin").splitlines() if line.strip()]
    if len(lines) != 1:
        die("target origin does not name one GitHub repository")
    match = GITHUB_HTTPS_RE.fullmatch(lines[0]) or GITHUB_SSH_RE.fullmatch(lines[0])
    if match is None:
        die("target origin does not name one GitHub repository")
    return match.group("repo")


def github_repository(base_dir: str) -> str:
    target = target_repository(base_dir)
    data = bounded_gh(
        base_dir,
        ["repo", "view", "--json", "nameWithOwner"],
        "GitHub repository identity could not be resolved",
    )
    try:
        payload = json.loads(tool_text(data, "GitHub repository identity"))
    except ValueError:
        die("GitHub repository identity returned invalid JSON")
    repository = payload.get("nameWithOwner") if isinstance(payload, dict) else None
    if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
        die("GitHub repository identity is missing nameWithOwner")
    if repository.casefold() != target.casefold():
        die("GitHub repository identity does not match target origin")
    return target


def pull_request_repository(pr_url: object, repository: str) -> str:
    if not isinstance(pr_url, str):
        die("pull request URL is invalid")
    match = GITHUB_PR_RE.fullmatch(pr_url)
    if match is None or match.group("repo").casefold() != repository.casefold():
        die("pull request URL does not match target repository")
    return pr_url.rstrip("/")


def inspect_pull_request(
    base_dir: str,
    pr_url: object,
    *,
    expected_head: str,
    expected_base: str,
    expected_head_sha: str | None,
    expected_merge_sha: str | None,
    expected_head_label: str = "verified pushed branch tip",
) -> dict:
    head_sha = (
        require_full_sha(expected_head_sha, "pull request head")
        if expected_head_sha is not None
        else None
    )
    merge_sha = (
        require_full_sha(expected_merge_sha, "pull request merge")
        if expected_merge_sha is not None
        else None
    )
    repository = github_repository(base_dir)
    url = pull_request_repository(pr_url, repository)
    data = bounded_gh(
        base_dir,
        [
            "pr", "view", url, "--repo", repository, "--json",
            "url,state,headRefName,headRefOid,baseRefName,mergeCommit",
        ],
        "pull request topology could not be read",
    )
    try:
        payload = json.loads(tool_text(data, "pull request topology"))
    except ValueError:
        die("pull request topology returned invalid JSON")
    if not isinstance(payload, dict):
        die("pull request topology is invalid")
    returned_url = payload.get("url")
    if not isinstance(returned_url, str):
        die("pull request topology is missing its URL")
    pull_request_repository(returned_url, repository)
    if returned_url.rstrip("/") != url:
        die("pull request topology did not name the recorded pull request")
    if payload.get("headRefName") != expected_head or payload.get("baseRefName") != expected_base:
        die("pull request topology does not match the expected head and base")
    returned_head = payload.get("headRefOid")
    if not isinstance(returned_head, str) or not COMMIT_RE.fullmatch(returned_head):
        die("pull request topology has no full head SHA")
    if head_sha is not None and returned_head != head_sha:
        die(f"pull request head does not match the {expected_head_label}")
    merge = payload.get("mergeCommit")
    returned_merge = merge.get("oid") if isinstance(merge, dict) else None
    if merge_sha is not None:
        if payload.get("state") != "MERGED" or returned_merge != merge_sha:
            die("pull request is not the expected merged topology")
    elif payload.get("state") == "MERGED":
        die("step pull request was already merged before integrate")
    return {
        "url": url,
        "head": expected_head,
        "base": expected_base,
        "head_sha": returned_head,
        "state": payload.get("state"),
        "merge_sha": returned_merge,
    }


def verify_github_commits(base_dir: str, commits: list[str]) -> list[str]:
    """Require GitHub's valid verification result for each exact SHA."""
    commits = [require_full_sha(commit, "GitHub commit") for commit in commits]
    repository = github_repository(base_dir)
    verified = []
    for commit_sha in commits:
        data = bounded_gh(
            base_dir,
            ["api", "--method", "GET", f"repos/{repository}/commits/{commit_sha}"],
            f"GitHub verification for {commit_sha} could not be read",
        )
        try:
            payload = json.loads(tool_text(data, f"GitHub verification for {commit_sha}"))
        except ValueError:
            die(f"GitHub verification for {commit_sha} returned invalid JSON")
        if not isinstance(payload, dict) or payload.get("sha") != commit_sha:
            die(f"GitHub verification response did not name exact SHA {commit_sha}")
        commit = payload.get("commit")
        verification = commit.get("verification") if isinstance(commit, dict) else None
        if not isinstance(verification, dict):
            die(f"GitHub verification for {commit_sha} is missing")
        if verification.get("verified") is not True:
            die(f"GitHub verification for {commit_sha} is not verified:true")
        if verification.get("reason") != "valid":
            die(f"GitHub verification for {commit_sha} reason is not valid")
        verified.append(commit_sha)
    return verified


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
        stacked_branch = plan["branch"] + suffix
        bounded_git(
            root,
            ["check-ref-format", "--branch", stacked_branch],
            "stacked_branch is not a valid Git branch",
        )
        packet["agent"] = "warden"
        packet["brief"] = {
            "step_branch": plan["branch"],
            "stacked_branch": stacked_branch,
            "security_suite": as_dict(state.get("receipts")).get("security_suite"),
            "plugin_root": root_plugin,
            "audit_log_path": scoped_path(root, log, "audit log path"),
            "round": directive["round"],
            "risk_register": source_risk_register(study),
            "runbook_step": source_runbook_step(runbook, step),
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
    blocked = amendment_block(state)
    if blocked is not None:
        return {
            "do": "blocked",
            "reason": (
                f"study amendment marks step {blocked['step']} entry "
                f"{blocked['entry']} and exit {blocked['exit']}"
            ),
            "amendment_sha256": blocked["amendment_sha256"],
            "study_sha256": blocked["study_sha256"],
            "recovery": (
                "inspect the amendment, halt the run, or use a separately "
                "specified runbook-repair transition"
            ),
        }
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
        owed = {"elenchus_verdict": elenchus_verdict_obligation()}
        if lints_owed:
            owed["lints"] = [f"--{lint}-exit" for lint in LINTS]
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
    blocked = amendment_block(state)
    if blocked is not None:
        print(
            f"BLOCKED: study amendment marks step {blocked['step']} "
            f"entry {blocked['entry']} and exit {blocked['exit']}"
        )
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


def verify_run(base_dir: str, *, allow_pending_amendment: bool = False) -> int:
    state = load_state(
        base_dir, allow_pending_amendment=allow_pending_amendment
    )
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
    study_receipt = as_dict(as_dict(state.get("receipts")).get("study"))
    if study_receipt.get("sha256") is not None:
        receipted_source(base_dir, state, "study")
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
    """Archive a completed run, and retire the worktree it ran in.

    Retirement belongs here rather than in `done integrate`, because the
    controller's own contract has the caller run `status` and `verify` after the
    run reports done. A tree removed at integrate would take the state and the
    ledger those two commands read with it, so the last thing a run did would be
    to delete its own evidence. `reset` is already the command that means the run
    is finished and can be put away.

    A run that lived in a worktree archives into the checkout it was started
    from, because archiving inside the tree and then removing the tree would
    destroy the archive in the same breath.
    """
    count = verify_run(args.dir)
    state = load_state(args.dir)
    if state["phase"] != "done":
        die(
            f"refusing to reset an incomplete run in phase '{state['phase']}'; "
            "resume it or halt it explicitly"
        )

    root = state_root(args.dir)
    origin = state.get("origin")
    worktree = state.get("worktree")
    retiring = bool(origin and worktree and os.path.isdir(worktree)
                    and os.path.realpath(worktree) == os.path.realpath(args.dir))
    archive_root = os.path.join(state_root(origin) if retiring else root, "archive")
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
    if retiring:
        if worktree_is_clean(worktree) and remove_run_worktree(origin, worktree):
            print(f"run worktree removed: {worktree}")
        else:
            print(
                f"run worktree kept at {worktree}: it holds work git would not "
                f"discard. Nothing was forced.",
                file=sys.stderr,
            )
        write_breadcrumbs(origin)


# ---------------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hexctl", description=__doc__)
    p.add_argument("--dir", default=".", help="directory holding the state dir")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="start a run")
    sp.add_argument("--topic", required=True)
    sp.add_argument("--base", default="main")
    sp.add_argument(
        "--task-issue",
        dest="task_issue",
        help="task issue URL whose positive terminal issue number names the run",
    )
    sp.add_argument(
        "--run-branch",
        dest="run_branch",
        help="exact integration branch (default: topic slug, prefixed by task "
             "issue when supplied)",
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

    sp = sub.add_parser("amend", help="receipt a bounded mid-run amendment")
    amend = sp.add_subparsers(dest="amend_subject", required=True)
    study = amend.add_parser("study", help="receipt one append-only study amendment")
    study.add_argument("--artifact", required=True)
    study.set_defaults(fn=cmd_amend_study)

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
    sp.add_argument("--base-commit", dest="base_commit")
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
    sp.add_argument(
        "--elenchus-verdict",
        dest="elenchus_verdict",
        choices=ELENCHUS_VERDICTS,
    )
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
