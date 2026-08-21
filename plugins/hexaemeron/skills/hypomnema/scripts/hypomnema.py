#!/usr/bin/env python3
"""Hypomnema record lint.

A record that points at something absent is worse than no record: it reads as
though the reason exists and was checked. This settles the part a parser can.

  H001  a relative link that resolves to nothing
  H002  a superseding pointer naming a record that does not exist
  H003  an alert naming a runbook file that is not there
  H004  a decision record missing one of the template's five sections
  H005  a decision record whose status is not dated

Exit 0 clean, 1 findings, 2 bad invocation.

A decision record is a markdown file named `ADR-<number>...` inside a
directory named `decisions`. The shape codes hold it to the template the
SKILL states: a Status whose first line is a status word, a comma and an
ISO date, and the five sections Status, Context, Decision, Alternatives
and Consequences. Directory walks skip `fixtures` directories relative to
the walked root, because a specimen documenting a fault is not a record;
naming a fixtures path directly still reads it.

Deliberate exceptions state a reason: `<!-- hypomnema: allow <why> -->`,
for a shape finding on the record's first line or the status heading.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

LINK = re.compile(r"(?<!!)\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
SUPERSEDE = re.compile(r"superseded\s+by\s+(?P<ref>ADR-\d+)", re.IGNORECASE)
ADR_NUMBER = re.compile(r"ADR-(\d+)", re.IGNORECASE)
# A path, not whatever word follows a colon: "a runbook: what fired" is prose.
RUNBOOK = re.compile(r"runbook:\s*[`\"']?(?P<path>[\w./-]+\.md|[\w./-]+/[\w./-]+)[`\"']?",
                     re.IGNORECASE)
ALLOW = re.compile(r"<!--\s*hypomnema:\s*allow\s+(?P<reason>\S[^>]*?)\s*-->")
SKIP_SCHEME = ("http", "https", "mailto", "tel", "ftp")
# The record template the SKILL states, held mechanically since the first
# four records stated their status in three shapes within a day.
RECORD_NAME = re.compile(r"^ADR-\d+.*\.md$", re.IGNORECASE)
SECTION = re.compile(r"^##\s+(?P<name>\S.*?)\s*$")
SECTIONS = ("Status", "Context", "Decision", "Alternatives", "Consequences")
DATED = re.compile(r"^[A-Za-z]+, \d{4}-\d{2}-\d{2}")
# The bundled Pashov suite is vendored, keeps no ledger, and documents files it
# generates in the target repository rather than files that live here.
VENDORED = {"fizz", "x-ray", "solidity-auditor"}


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
    for number in (line, line - 1):
        if 1 <= number <= len(lines) and ALLOW.search(lines[number - 1]):
            return True
    return False


def _external(target: str) -> bool:
    parsed = urlparse(target)
    return bool(parsed.scheme) and parsed.scheme in SKIP_SCHEME


def _record_findings(path: Path, lines: list[str]) -> list[Finding]:
    """The template shape: a dated status and the five sections.

    Section headings are read outside fences only, so a record quoting the
    template in an example neither gains nor loses a section.
    """
    headings: dict[str, int] = {}
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = SECTION.match(line)
        if match:
            # A pragma on the heading is a suppression, not part of the name.
            name = ALLOW.sub("", match.group("name")).strip()
            if name in SECTIONS:
                headings.setdefault(name, number)

    findings = [Finding(path, 1, "H004",
                        f"decision record is missing its `## {name}` section")
                for name in SECTIONS if name not in headings]

    status_line = headings.get("Status")
    if status_line is not None:
        first = ""
        for line in lines[status_line:]:
            if SECTION.match(line) or line.startswith("#"):
                break
            if line.strip():
                first = line.strip()
                break
        if not DATED.match(first):
            findings.append(Finding(
                path, status_line, "H005",
                "status is not dated; the shape is a status word, a comma "
                "and an ISO date"))
    return findings


def check(path: Path, adr_numbers: set[str] | None = None) -> list[Finding]:
    if path.suffix != ".md":
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [Finding(path, 1, "H000", f"unreadable: {err}")]

    lines = text.splitlines()
    findings: list[Finding] = []
    if RECORD_NAME.match(path.name) and "decisions" in path.parts:
        findings.extend(_record_findings(path, lines))
    in_fence = False

    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        for match in LINK.finditer(line):
            target = match.group("target")
            if target.startswith("#") or _external(target):
                continue
            relative = unquote(target.split("#", 1)[0])
            if not relative:
                continue
            if not (path.parent / relative).exists():
                findings.append(Finding(path, number, "H001",
                                        f"link `{target}` resolves to nothing"))

        for match in SUPERSEDE.finditer(line):
            reference = match.group("ref").upper()
            if adr_numbers is not None and reference not in adr_numbers:
                findings.append(Finding(path, number, "H002",
                                        f"superseded by `{reference}`, which does not exist"))

        for match in RUNBOOK.finditer(line):
            target = match.group("path").strip("`\"'")
            if not _external(target) and not (path.parent / target).exists():
                findings.append(Finding(path, number, "H003",
                                        f"alert names runbook `{target}`, which is not there"))

    return [f for f in findings if not suppressed(lines, f.line)]


def adr_index(paths: list[Path]) -> set[str]:
    found = set()
    for path in paths:
        match = ADR_NUMBER.search(path.name)
        if match:
            found.add(f"ADR-{match.group(1)}")
    return found


def walk(paths: list[str], include_vendored: bool = False) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        root = Path(raw)
        if root.is_dir():
            for child in sorted(root.rglob("*.md")):
                if ".git" in child.parts:
                    continue
                if not include_vendored and VENDORED & set(child.parts):
                    continue
                # A specimen documenting a fault is not a record. Relative to
                # the walked root, so naming a fixtures path still reads it.
                if "fixtures" in child.relative_to(root).parts[:-1]:
                    continue
                out.append(child)
        else:
            out.append(root)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hypomnema record lint.")
    parser.add_argument("paths", nargs="*", default=["."])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--include-vendored", action="store_true",
                        help="also check the bundled third-party skills")
    args = parser.parse_args(argv)

    files = walk(args.paths or ["."], include_vendored=args.include_vendored)
    index = adr_index(files)
    findings: list[Finding] = []
    for path in files:
        findings.extend(check(path, index))

    if args.format == "json":
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
