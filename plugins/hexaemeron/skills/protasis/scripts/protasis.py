#!/usr/bin/env python3
"""Protasis runbook schema check.

A runbook step that omits a field is not caught by reading, because the phase
that reads it carefully is the one that has already started building. This
settles the part a parser can.

  P000  a path that cannot be read as a runbook
  P001  a step missing a required field
  P002  a step whose exit states no command
  P003  a document in which no step was found
  P004  more steps than the check will track, so the tail went unchecked

Exit 0 clean, 1 findings, 2 bad invocation.

Deliberate exceptions state a reason: `<!-- protasis: allow <why> -->` on the
step heading line or the line above it.

What this does not do. It reads whether a field is present, not whether the
answer is any good: a Disciplines line naming the wrong gates and an Exit whose
command proves nothing both pass. Judging an answer is the reviewer's job, and
the study's non-goals say so. P002 is the closest to a judgement, and it is
still only presence: a step carrying no code at all cannot have named a command,
while a step carrying one may still have named the wrong one.

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
FENCE = re.compile(r"^\s*```")
INLINE_CODE = re.compile(r"`[^`\n]+`")
ALLOW = re.compile(r"<!--\s*protasis:\s*allow\s+(?P<reason>\S[^>]*?)\s*-->")

REQUIRED = ("Goal", "Entry", "Exit", "Files", "Tests", "Disciplines")

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
    in_fence = False
    for index, line in enumerate(lines, start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
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
            tail_fence = False
            for index in range(line_number + 1, len(lines) + 1):
                line = lines[index - 1]
                if FENCE.match(line):
                    tail_fence = not tail_fence
                    continue
                # Any heading of this level ends the last step, a further step
                # heading included. Excluding step headings here let a step
                # dropped by the cap donate its fields to the last tracked
                # step, which then passed while missing its own. Fenced lines
                # are not headings, or a runbook quoting a step heading in an
                # example would truncate itself.
                if not tail_fence and HEADING.match(line):
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
    in_fence = False
    for line in body[start + 1:]:
        if FENCE.match(line):
            in_fence = not in_fence
            span.append(line)
            continue
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Protasis runbook schema check.")
    parser.add_argument("paths", nargs="+", help="runbook files to check")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    for name in args.paths:
        findings.extend(check(Path(name)))

    if args.format == "json":
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
