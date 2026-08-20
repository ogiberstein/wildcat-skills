#!/usr/bin/env python3
"""Protasis runbook and study schema checks.

A runbook step that omits a field is not caught by reading, because the phase
that reads it carefully is the one that has already started building. The same
holds for a study missing one of its twelve items. This settles the part a
parser can.

Runbook mode (the default):

  P000  a path that cannot be read as a runbook
  P001  a step missing a required field
  P002  a step whose exit states no command
  P003  a document in which no step was found
  P004  more steps than the check will track, so the tail went unchecked

Study mode (`--study`):

  S000  a path that cannot be read as a study
  S001  one of the twelve study items is missing
  S002  an answer to items 8 through 12 is neither content nor a stated
        none carrying its reason
  S003  a document in which no study item was found
  S004  a study item number appears more than once, so no verdict on its
        answer is earned

Exit 0 clean, 1 findings, 2 bad invocation.

Deliberate exceptions state a reason: `<!-- protasis: allow <why> -->` on the
step heading line or the line above it.

What this does not do. It reads whether a field is present, not whether the
answer is any good: a Disciplines line naming the wrong gates and an Exit whose
command proves nothing both pass. Judging an answer is the reviewer's job, and
the study's non-goals say so. P002 is the closest to a judgement, and it is
still only presence: a step carrying no code at all cannot have named a command,
while a step carrying one may still have named the wrong one. The study mode
holds the same line: S002 refuses silence and a bare none, never a weak reason,
and items 1 through 7 are checked for presence only, because "none, and here is
why" is a complete answer solely for items 8 through 12.

The trust boundary is the argument list. Paths are read as given, so the caller
decides what is opened; the checker refuses anything that is not a regular file,
caps what it will read, and caps how many steps it will track. It starts no
subprocess and opens no socket.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# "## Step 3: Ship the checker". The number is required: a heading reading
# "## Steps" is prose about steps, not a step.
STEP = re.compile(r"^##\s+Step\s+(?P<n>\d+)\s*:\s*(?P<title>.*?)\s*$")
FIELD = re.compile(r"^\*\*(?P<name>[A-Za-z]+)\.\*\*")
HEADING = re.compile(r"^#{1,2}\s+")
# Backtick or tilde, three or more, per CommonMark. The marker is captured so a
# fence is closed only by its own kind: ``` inside a ~~~ block is content.
FENCE = re.compile(r"^\s*(?P<mark>`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`[^`\n]+`")
ALLOW = re.compile(r"<!--\s*protasis:\s*allow\s+(?P<reason>\S[^>]*?)\s*-->")

REQUIRED = ("Goal", "Entry", "Exit", "Files", "Tests", "Disciplines")

# "## 2. Prior art". The number is required and the dot ends it: a heading
# reading "## Sources" is prose, not an item.
ITEM = re.compile(r"^##\s+(?P<n>\d{1,3})\.\s*(?P<title>.*?)\s*$")

# The twelve items the study contract mandates, by number.
ITEMS = {
    1: "Problem statement",
    2: "Prior art",
    3: "Constraints and non-goals",
    4: "Design options",
    5: "Risk register seed",
    6: "Glossary seeds",
    7: "Sources",
    8: "Signals, and the questions behind them",
    9: "Boundaries, per capability",
    10: "The budget, or its absence",
    11: "The fail-closed posture",
    12: "Decisions and their homes",
}

# The five whose answer may be a stated none, and only with its reason.
ANSWERED = range(8, 13)

# An answer that asserts none and stops. Punctuation-stripped, lowercased,
# whole-answer matches only: "none, and here is why: ..." carries more words
# and passes, while judging whether the reason is any good stays the
# reviewer's job.
BARE = {"none", "n/a", "na", "no", "tbd"}

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# A runbook is a document somebody handed over. Bound both axes.
MAX_BYTES = 2 * 1024 * 1024
MAX_STEPS = 500


class Finding:
    __slots__ = ("path", "line", "code", "message")

    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path, self.line, self.code, self.message = path, line, code, message

    def as_dict(self) -> dict:
        return {"path": str(self.path), "line": self.line, "code": self.code,
                "message": self.message}

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def _scan(lines: list[str]):
    """Yield (1-indexed number, line, inside_a_fence) for every line.

    One tracker for all three scans. Keeping three copies is what let the tail
    scan ship without fence tracking at all, so a runbook quoting a step heading
    truncated itself.
    """
    open_mark: str | None = None
    for number, line in enumerate(lines, start=1):
        match = FENCE.match(line)
        if match:
            mark = match.group("mark")[0]
            if open_mark is None:
                open_mark = mark
                yield number, line, True
                continue
            if mark == open_mark:
                open_mark = None
            yield number, line, True
            continue
        yield number, line, open_mark is not None


def suppressed(lines: list[str], line: int) -> bool:
    """An allow comment on the heading line or the line above it."""
    for number in (line, line - 1):
        if 1 <= number <= len(lines) and ALLOW.search(lines[number - 1]):
            return True
    return False


def _read(path: Path) -> list[str] | None:
    """The document, or None when it is not one we will read."""
    try:
        if not path.is_file():
            return None
        if path.stat().st_size > MAX_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None


def _spans(lines: list[str]) -> tuple[list[tuple[int, str, int, int]], int]:
    """Steps as (heading line, title, body start, body end), and how many were
    left untracked by the cap.

    A step owns the lines after its heading up to the next step heading or the
    next heading of the same or higher level, so a trailing section does not
    get read as part of the last step.

    The cap bounds the work, and the count of what it dropped is returned rather
    than discarded: a check that stops early and still reports clean is the
    false confidence this whole module exists to avoid.
    """
    starts: list[tuple[int, str]] = []
    dropped = 0
    for index, line, in_fence in _scan(lines):
        if in_fence:
            continue
        match = STEP.match(line)
        if match:
            if len(starts) >= MAX_STEPS:
                dropped += 1
                continue
            starts.append((index, match.group("title")))

    spans = []
    for position, (line_number, title) in enumerate(starts):
        if position + 1 < len(starts):
            end = starts[position + 1][0] - 1
        else:
            end = len(lines)
            # Any heading of this level ends the last step, a further step
            # heading included. Excluding step headings here let a step dropped
            # by the cap donate its fields to the last tracked step, which then
            # passed while missing its own. Fenced lines are not headings, or a
            # runbook quoting a step heading would truncate itself.
            for index, line, in_fence in _scan(lines):
                if index <= line_number or in_fence:
                    continue
                if HEADING.match(line):
                    end = index - 1
                    break
        spans.append((line_number, title, line_number + 1, end))
    return spans, dropped


def _field_span(body: list[str], name: str) -> list[str]:
    """The lines belonging to one field: its own line up to the next field.

    Scoped deliberately. Searching the whole step for a command means any other
    field carrying backticks answers for the exit, and `**Files.** `a.py`` is
    almost universal, so a step-wide search makes P002 unfirable in practice.
    """
    start = None
    for index, line in enumerate(body):
        match = FIELD.match(line)
        if match and match.group("name") == name:
            start = index
            break
    if start is None:
        return []

    span = [body[start]]
    for index, line, in_fence in _scan(body[start + 1:]):
        if not in_fence and FIELD.match(line):
            break
        span.append(line)
    return span


def _has_command(lines: list[str]) -> bool:
    """A command is a fenced block or an inline code span."""
    for line in lines:
        if FENCE.match(line) or INLINE_CODE.search(line):
            return True
    return False


def check(path: Path) -> list[Finding]:
    lines = _read(path)
    if lines is None:
        return [Finding(path, 1, "P000", "cannot be read as a runbook")]

    findings: list[Finding] = []
    spans, dropped = _spans(lines)
    if not spans:
        return [Finding(path, 1, "P003", "no step found; expected a '## Step N: title' heading")]
    if dropped:
        findings.append(Finding(
            path, 1, "P004",
            f"{dropped} step(s) past the {MAX_STEPS}-step cap were not checked; "
            f"split the runbook rather than trusting this result"))

    for heading_line, title, body_start, body_end in spans:
        if suppressed(lines, heading_line):
            continue
        body = lines[body_start - 1:body_end]
        present = {match.group("name") for match in
                   (FIELD.match(line) for line in body) if match}
        for name in REQUIRED:
            if name not in present:
                findings.append(Finding(
                    path, heading_line, "P001",
                    f"step {title!r} is missing **{name}.**"))
        if "Exit" in present and not _has_command(_field_span(body, "Exit")):
            findings.append(Finding(
                path, heading_line, "P002",
                f"step {title!r} states an exit but names no command"))
    return findings


def _item_spans(lines: list[str]) -> dict[int, list[tuple[int, int, int]]]:
    """Item spans keyed by number: (heading line, body start, body end).

    A list per number, because a duplicate is a fact to report rather than a
    copy to silently prefer. An item owns the lines after its heading up to
    the next level-two heading; fenced lines are content, so a study quoting
    an item heading does not gain or truncate an item.
    """
    headings: list[tuple[int, int | None]] = []
    for index, line, in_fence in _scan(lines):
        if in_fence or not HEADING.match(line):
            continue
        match = ITEM.match(line)
        number = int(match.group("n")) if match else None
        headings.append((index, number if number in ITEMS else None))

    spans: dict[int, list[tuple[int, int, int]]] = {}
    for position, (line_number, number) in enumerate(headings):
        if number is None:
            continue
        if position + 1 < len(headings):
            end = headings[position + 1][0] - 1
        else:
            end = len(lines)
        spans.setdefault(number, []).append((line_number, line_number + 1, end))
    return spans


def _answer(lines: list[str], start: int, end: int) -> str:
    """The answer's text with comments and whitespace stripped."""
    body = "\n".join(lines[start - 1:end])
    body = COMMENT.sub(" ", body)
    return " ".join(body.split())


def check_study(path: Path) -> list[Finding]:
    lines = _read(path)
    if lines is None:
        return [Finding(path, 1, "S000", "cannot be read as a study")]

    spans = _item_spans(lines)
    if not spans:
        return [Finding(path, 1, "S003",
                        "no study item found; expected '## N. Title' headings, 1 to 12")]

    findings: list[Finding] = []
    for number in sorted(ITEMS):
        name = ITEMS[number]
        occurrences = spans.get(number, [])
        if not occurrences:
            findings.append(Finding(
                path, 1, "S001", f"study item {number} ({name}) is missing"))
            continue
        if len(occurrences) > 1:
            first = occurrences[0][0]
            findings.append(Finding(
                path, first, "S004",
                f"study item {number} ({name}) appears {len(occurrences)} times, "
                f"so no verdict on its answer is earned"))
            continue
        heading_line, body_start, body_end = occurrences[0]
        if number not in ANSWERED or suppressed(lines, heading_line):
            continue
        answer = _answer(lines, body_start, body_end)
        stripped = answer.strip(" .,!:;-").lower()
        if not answer or stripped in BARE:
            findings.append(Finding(
                path, heading_line, "S002",
                f"item {number} ({name}) carries neither content nor a stated "
                f"none with its reason"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Protasis runbook and study schema checks.")
    parser.add_argument("paths", nargs="+", help="documents to check")
    parser.add_argument("--study", action="store_true",
                        help="check studies against the twelve-item contract "
                             "instead of runbooks against the step schema")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    checker = check_study if args.study else check
    findings: list[Finding] = []
    for name in args.paths:
        findings.extend(checker(Path(name)))

    if args.format == "json":
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
