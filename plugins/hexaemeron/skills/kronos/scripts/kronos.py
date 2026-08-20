#!/usr/bin/env python3
"""Kronos ranking scoreboard.

Kronos scores every eligible held Fiat job out of 100, prints the result, runs
the winner, and then reranks from scratch. Nothing carries between passes, so a
job can score 62 in one pass and 78 three passes later with nothing about it
changed. This appends each pass to a file so that movement is visible.

  record  read a pass on stdin, validate it, append exactly one JSON line
  show    print the recorded passes and mark every axis score that moved for a
          candidate whose held job did not

  K000  a path that cannot be read
  K001  stdin that is not a JSON object
  K002  a required field that is missing
  K003  a field the record does not carry
  K004  an axis outside its range
  K005  a stated total that disagrees with the axes
  K006  a selection that is not what the tie-break picks
  K007  a candidate ledger that cannot be used
  K008  an existing scoreboard line that cannot be read
  K009  more candidates than the check will track
  K010  a scoreboard directory that is not a real directory
  K011  a halt reason that is empty or over the cap
  K012  a park for a skill that is already parked
  K013  an unpark with no standing park to release
  K014  a parked flag that disagrees with the standing parks
  K015  a pass in which every candidate is parked

Exit 0 clean, 1 a refusal, 2 bad invocation, and 3 from `parked` alone while a
park stands. That last is not an error in the tool. It is the loop's reason not
to declare itself finished, which is why it needs a code of its own rather than
the one argparse already spends on a bad invocation. A refusal appends nothing:
a pass, a park and an unpark are each recorded whole or not at all.

The held-job identity hash is not supplied by the caller. It is computed here
from the candidate's ledger, as the SHA-256 of the canonical frontier line that
VERSIONING.md already defines, which is the same digest each ledger stores in
its own history row. A line written here can therefore be checked against the
ledger it describes.

What this does not do. It records a judgement; it does not make one. An axis
score is a number the ranking agent supplies, and a basis is prose nobody
parses. It also cannot tell that a pass went unrecorded, because a loop that
skips this writer leaves a shorter file and nothing else.

The trust boundary is stdin and the argument list. The pass document arrives
from a caller and is read with a byte cap, an unknown field is refused rather
than stored, and the candidate count is capped. Each candidate names a ledger
path the caller chose, so that path is resolved, required to be a regular file
under the scoreboard's root, and read under a cap. An existing scoreboard is
validated line by line before anything is appended, so a run interrupted
mid-append is refused rather than written past. Nothing here starts a
subprocess or opens a socket.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Kronos SKILL.md step 3. The caps sum to 100, which is what "out of 100" means.
AXES = (("impact", 40), ("urgency", 25), ("readiness", 20), ("unblocks", 15))

CANDIDATE_FIELDS = frozenset(
    {"skill", "ledger", "basis", "total", "parked"} | {name for name, _ in AXES}
)
CANDIDATE_REQUIRED = ("skill", "ledger", "basis") + tuple(name for name, _ in AXES)
PASS_FIELDS = frozenset({"scope", "mode", "candidates", "selected", "run"})
PASS_REQUIRED = ("scope", "mode", "candidates", "selected")
MODES = ("full", "phase-only")

# Documents somebody handed over. Bound every axis that a caller controls.
MAX_STDIN_BYTES = 1024 * 1024
MAX_LEDGER_BYTES = 1024 * 1024
MAX_SCOREBOARD_BYTES = 16 * 1024 * 1024
MAX_CANDIDATES = 200
MAX_REASON_BYTES = 4096
STANDS = 3

LEDGER_FIELDS = ("Frontier status", "Frontier revision", "Current frontier", "Next Fiat job")

PARK_EVENTS = ("park", "unpark")
PARKED_NAME = "parked.jsonl"


class Refusal(Exception):
    """A validation failure, carrying the code that names it."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def ledger_field(text: str, name: str) -> str:
    """One `- Name: value` line from a ledger, matching the contract test."""
    match = re.search(rf"(?m)^- {re.escape(name)}: (.+)$", text)
    if match is None:
        raise Refusal("K007", f"ledger has no {name!r} field")
    return match.group(1).strip().strip("`")


def held_job_hash(ledger: Path) -> str:
    """SHA-256 of the canonical frontier line VERSIONING.md defines."""
    text = read_capped(ledger, MAX_LEDGER_BYTES, "K007")
    canonical = "|".join(ledger_field(text, name) for name in LEDGER_FIELDS) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def read_capped(path: Path, cap: int, code: str) -> str:
    """Read a regular file under a byte cap, or refuse with the given code."""
    if not path.is_file():
        raise Refusal(code, f"{path} is not a regular file")
    size = path.stat().st_size
    if size > cap:
        raise Refusal(code, f"{path} is {size} bytes, over the {cap} byte cap")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal(code, f"{path} could not be read: {exc}") from exc


def resolved_under(root: Path, candidate: str) -> Path:
    """Resolve a caller-supplied path and require it to sit under the root."""
    path = (root / candidate).resolve() if not Path(candidate).is_absolute() else Path(candidate).resolve()
    if path != root and root not in path.parents:
        raise Refusal("K007", f"{candidate} resolves outside {root}")
    return path


def check_fields(obj: dict, allowed: frozenset, required: tuple, where: str) -> None:
    if not isinstance(obj, dict):
        raise Refusal("K001", f"{where} is not an object")
    for name in required:
        if name not in obj:
            raise Refusal("K002", f"{where} has no {name!r}")
    for name in obj:
        if name not in allowed:
            raise Refusal("K003", f"{where} carries {name!r}, which the record does not hold")


def score(candidate: dict, root: Path, where: str) -> dict:
    """Validate one candidate and return the line it contributes."""
    check_fields(candidate, CANDIDATE_FIELDS, CANDIDATE_REQUIRED, where)
    axes = {}
    for name, cap in AXES:
        value = candidate[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise Refusal("K004", f"{where} {name} is {value!r}, not an integer")
        if not 0 <= value <= cap:
            raise Refusal("K004", f"{where} {name} is {value}, outside 0 to {cap}")
        axes[name] = value
    total = sum(axes.values())
    stated = candidate.get("total")
    if stated is not None and stated != total:
        raise Refusal("K005", f"{where} states a total of {stated}, but the axes sum to {total}")
    for name in ("skill", "basis"):
        if not isinstance(candidate[name], str) or not candidate[name].strip():
            raise Refusal("K002", f"{where} {name} is empty")
    if not isinstance(candidate["ledger"], str) or not candidate["ledger"].strip():
        raise Refusal("K002", f"{where} ledger is empty")
    ledger = resolved_under(root, candidate["ledger"])
    return {
        "skill": candidate["skill"],
        "ledger": str(ledger.relative_to(root)),
        "held_job": held_job_hash(ledger),
        **axes,
        "total": total,
        "basis": candidate["basis"],
    }


def tie_break(scored: list) -> str:
    """Kronos SKILL.md step 4: total, then impact, then readiness, then order."""
    ordered = sorted(
        enumerate(scored),
        key=lambda pair: (-pair[1]["total"], -pair[1]["impact"], -pair[1]["readiness"], pair[0]),
    )
    return ordered[0][1]["skill"]


def checked_path(given: Path) -> Path:
    """Resolve a write target, refusing a symlink at the file or its directory.

    Before resolving anything: a symlink at either end would put the file and
    the `*` gitignore beside it somewhere the caller did not name, and resolve()
    erases the link on the way past.
    """
    holder = given.parent
    if given.is_symlink():
        raise Refusal("K010", f"{given} is a symlink")
    if holder.is_symlink() or (holder.exists() and not holder.is_dir()):
        raise Refusal("K010", f"{holder} is not a real directory")
    return given.resolve()


def append_line(path: Path, entry: dict) -> None:
    """Create the gitignored directory if needed, then append one JSON line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    gitignore = path.parent / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def json_lines(path: Path, marker: str) -> list:
    """Every line already recorded, refusing a tail that cannot be read."""
    if not path.exists():
        return []
    text = read_capped(path, MAX_SCOREBOARD_BYTES, "K008")
    if text and not text.endswith("\n"):
        raise Refusal("K008", f"{path} does not end in a newline, so its last line is partial")
    entries = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise Refusal("K008", f"{path} line {number} is blank")
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Refusal("K008", f"{path} line {number} is not JSON: {exc}") from exc
        if not isinstance(entry, dict) or marker not in entry:
            raise Refusal("K008", f"{path} line {number} is not a {marker} record")
        entries.append(entry)
    return entries


def standing_parks(parked_file: Path) -> dict:
    """Replay park and unpark records in order into the set that still stands."""
    standing = {}
    for entry in json_lines(parked_file, "event"):
        if entry["event"] not in PARK_EVENTS:
            raise Refusal("K008", f"{parked_file} carries event {entry['event']!r}")
        if entry["event"] == "park":
            standing[entry["skill"]] = entry
        else:
            standing.pop(entry["skill"], None)
    return standing


def checked_reason(reason) -> str:
    if not isinstance(reason, str) or not reason.strip():
        raise Refusal("K011", "the reason is empty")
    size = len(reason.encode("utf-8"))
    if size > MAX_REASON_BYTES:
        raise Refusal("K011", f"the reason is {size} bytes, over the {MAX_REASON_BYTES} cap")
    return reason


def existing_passes(scoreboard: Path) -> list:
    """Every pass already recorded, refusing a tail that cannot be read."""
    return json_lines(scoreboard, "pass")


def record(args: argparse.Namespace) -> int:
    scoreboard = checked_path(Path(args.scoreboard))
    root = Path(args.root).resolve() if args.root else scoreboard.parent.parent
    raw = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    if len(raw) > MAX_STDIN_BYTES:
        raise Refusal("K001", f"stdin is over the {MAX_STDIN_BYTES} byte cap")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Refusal("K001", f"stdin is not JSON: {exc}") from exc

    check_fields(document, PASS_FIELDS, PASS_REQUIRED, "the pass")
    if document["mode"] not in MODES:
        raise Refusal("K002", f"mode is {document['mode']!r}, not one of {', '.join(MODES)}")
    candidates = document["candidates"]
    if not isinstance(candidates, list) or not candidates:
        raise Refusal("K002", "the pass has no candidates")
    if len(candidates) > MAX_CANDIDATES:
        raise Refusal("K009", f"{len(candidates)} candidates, over the {MAX_CANDIDATES} cap")

    scored = [score(c, root, f"candidate {n}") for n, c in enumerate(candidates, start=1)]
    names = [c["skill"] for c in scored]
    if len(set(names)) != len(names):
        raise Refusal("K002", "two candidates name the same skill")

    # A parked candidate keeps its score and its place in the record. It is only
    # barred from being selected, because the loop already knows why it stalled.
    standing = standing_parks(scoreboard.parent / PARKED_NAME)
    for candidate, given in zip(scored, candidates):
        claimed = given.get("parked", False)
        if not isinstance(claimed, bool):
            raise Refusal("K004", f"{candidate['skill']} parked is {claimed!r}, not a boolean")
        if claimed != (candidate["skill"] in standing):
            raise Refusal(
                "K014",
                f"{candidate['skill']} is marked parked={claimed}, "
                f"but the standing parks say {candidate['skill'] in standing}",
            )
        candidate["parked"] = claimed

    unparked = [c for c in scored if not c["parked"]]
    if not unparked:
        raise Refusal("K015", "every candidate is parked, so the pass selects nobody")
    if document["selected"] not in names:
        raise Refusal("K006", f"selected {document['selected']!r} is not among the candidates")
    expected = tie_break(unparked)
    if document["selected"] != expected:
        raise Refusal("K006", f"selected {document['selected']!r}, but the tie-break picks {expected!r}")

    run = document.get("run")
    if run is not None and not isinstance(run, str):
        raise Refusal("K002", f"run is {run!r}, which is neither a string nor absent")

    previous = existing_passes(scoreboard)
    entry = {
        "pass": len(previous) + 1,
        "scope": document["scope"],
        "mode": document["mode"],
        "selected": document["selected"],
        "run": run,
        "candidates": scored,
    }
    append_line(scoreboard, entry)
    parked_note = f", {len(scored) - len(unparked)} parked" if len(unparked) != len(scored) else ""
    print(
        f"pass {entry['pass']} recorded: {len(scored)} candidate(s){parked_note}, "
        f"selected {entry['selected']}"
    )
    return 0


def park(args: argparse.Namespace) -> int:
    parked_file = checked_path(Path(args.scoreboard_dir) / PARKED_NAME)
    root = Path(args.root).resolve() if args.root else parked_file.parent.parent
    reason = checked_reason(args.reason)
    ledger = resolved_under(root, args.ledger)
    held = held_job_hash(ledger)
    standing = standing_parks(parked_file)
    if args.skill in standing:
        raise Refusal("K012", f"{args.skill} is already parked; unpark it before parking it again")
    entry = {
        "event": "park",
        "skill": args.skill,
        "ledger": str(ledger.relative_to(root)),
        "held_job": held,
        "reason": reason,
    }
    append_line(parked_file, entry)
    print(f"parked {args.skill} on its held job {held[:12]}")
    return 0


def unpark(args: argparse.Namespace) -> int:
    parked_file = checked_path(Path(args.scoreboard_dir) / PARKED_NAME)
    reason = checked_reason(args.reason)
    standing = standing_parks(parked_file)
    if args.skill not in standing:
        raise Refusal("K013", f"{args.skill} is not parked, so there is nothing to release")
    append_line(parked_file, {"event": "unpark", "skill": args.skill, "reason": reason})
    print(f"released {args.skill}")
    return 0


def park_state(entry: dict, root: Path) -> str:
    """Whether the held job a park named is still the one on disk."""
    try:
        ledger = resolved_under(root, entry["ledger"])
        return "standing" if held_job_hash(ledger) == entry["held_job"] else "stale"
    except Refusal:
        # An unreadable ledger is not evidence that the blocker cleared.
        return "unknown"


def parked(args: argparse.Namespace) -> int:
    parked_file = Path(args.scoreboard_dir) / PARKED_NAME
    root = Path(args.root).resolve() if args.root else parked_file.resolve().parent.parent
    standing = standing_parks(parked_file)
    if not standing:
        print("no parks standing")
        return 0
    for skill in sorted(standing):
        entry = standing[skill]
        state = park_state(entry, root)
        note = {
            "standing": "held job unchanged",
            "stale": "held job has moved on since; a person decides whether the park still applies",
            "unknown": "ledger could not be read, so the park stands",
        }[state]
        print(f"{skill}  {entry['held_job'][:12]}  {note}")
        print(f"  reason: {entry['reason']}")
    print(f"{len(standing)} park(s) standing; the loop is not complete")
    return STANDS


def drift(passes: list) -> dict:
    """Axis scores that moved for a skill whose held job did not, by pass."""
    seen = {}
    moved = {}
    for entry in passes:
        for candidate in entry["candidates"]:
            key = (candidate["skill"], candidate["held_job"])
            before = seen.get(key)
            if before is not None:
                changed = [name for name, _ in AXES if candidate[name] != before[name]]
                if changed:
                    moved[(entry["pass"], candidate["skill"])] = [
                        (name, before[name], candidate[name]) for name in changed
                    ]
            seen[key] = candidate
    return moved


def show(args: argparse.Namespace) -> int:
    scoreboard = Path(args.scoreboard).resolve()
    if not scoreboard.exists():
        print(f"no scoreboard at {scoreboard}")
        return 0
    passes = existing_passes(scoreboard)
    moved = drift(passes)
    for entry in passes:
        run = entry.get("run") or "no run recorded"
        print(f"pass {entry['pass']}  {entry['mode']}  {entry['scope']}  ({run})")
        for candidate in sorted(entry["candidates"], key=lambda c: -c["total"]):
            mark = "*" if candidate["skill"] == entry["selected"] else " "
            axes = " ".join(f"{name}={candidate[name]}" for name, _ in AXES)
            print(f"  {mark} {candidate['total']:3d}  {candidate['skill']:<24} {axes}")
            print(f"      {candidate['basis']}")
            for name, before, after in moved.get((entry["pass"], candidate["skill"]), []):
                print(f"      drift: {name} {before} -> {after}, held job unchanged")
    print(f"{len(passes)} pass(es), {len(moved)} with drift")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    writer = sub.add_parser("record", help="append one validated pass read from stdin")
    writer.add_argument("--scoreboard", required=True, help="path to the scoreboard file")
    writer.add_argument("--root", help="checkout root each ledger must sit under")
    writer.set_defaults(handler=record)

    reader = sub.add_parser("show", help="print the recorded passes and any drift")
    reader.add_argument("--scoreboard", required=True, help="path to the scoreboard file")
    reader.set_defaults(handler=show)

    parker = sub.add_parser("park", help="record a blocked held job and why")
    parker.add_argument("--scoreboard-dir", required=True, help="the .kronos directory")
    parker.add_argument("--skill", required=True, help="the blocked skill")
    parker.add_argument("--ledger", required=True, help="that skill's EVOLUTION.md")
    parker.add_argument("--reason", required=True, help="the halt reason, stored as given")
    parker.add_argument("--root", help="checkout root the ledger must sit under")
    parker.set_defaults(handler=park)

    releaser = sub.add_parser("unpark", help="release a standing park")
    releaser.add_argument("--scoreboard-dir", required=True, help="the .kronos directory")
    releaser.add_argument("--skill", required=True, help="the parked skill")
    releaser.add_argument("--reason", required=True, help="why it is released, stored as given")
    releaser.set_defaults(handler=unpark)

    lister = sub.add_parser("parked", help="print standing parks; exits 3 while any stands")
    lister.add_argument("--scoreboard-dir", required=True, help="the .kronos directory")
    lister.add_argument("--root", help="checkout root the ledgers sit under")
    lister.set_defaults(handler=parked)

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except Refusal as refusal:
        print(refusal, file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"K000: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
