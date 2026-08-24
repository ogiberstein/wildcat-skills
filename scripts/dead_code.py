#!/usr/bin/env python3
"""Report dead-code candidates across this repository without deleting anything.

The command discovers the tracked universe at one commit, joins it with the
Horos reading boundary so a classified sink is excluded carrying the evidence
that classified it, runs whichever analysers are registered over what remains,
and renders one finding model as either text or JSON.

Nothing here deletes, rewrites or authorises the deletion of source. A finding
is a candidate carrying the evidence that produced it and the nearest reason
that evidence could be wrong. An analyser that did not run is reported as such
and never as an analyser that found nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SCHEMA = "dead-code-report/v1"
TOOL = "dead-code"

BOUNDARY_PATH = Path(".horos") / "boundary.json"

# Discovery that returns fewer paths than this has collapsed rather than found
# an empty repository, and the study makes that a stop rather than a report of
# zero findings.
UNIVERSE_FLOOR = 1

# Every temporary this command writes carries this prefix so the sweep is
# anchored to its own litter and `.gitignore` can name it. `scripts/contributors.py`
# finding S3-R2-01 is the record of what an unswept orphan costs.
TEMP_PREFIX = ".dead-code-tmp-"

GIT_TIMEOUT_SECONDS = 60

# Only a hard-graded Horos entry excludes a path. A candidate is advisory: the
# boundary is fail-open and what it merely suspects stays in the universe.
EXCLUDING_GRADE = "hard"

# Analysers register here. Each value is a callable taking the universe and the
# repository root and returning a pair of an AnalyserStatus and a tuple of
# Findings. Step 1 registers none, and a report with an empty registry says so
# rather than presenting itself as a clean result.
ANALYSERS: dict[str, object] = {}


class Refusal(Exception):
    """A named condition that stops the command before it reports."""


@dataclass(frozen=True)
class ClassifiedPath:
    """One path the Horos boundary excluded, with the evidence that did it."""

    path: str
    category: str
    evidence: str
    grade: str


@dataclass(frozen=True)
class Universe:
    """What was analysed at one commit, and what was excluded from it."""

    commit: str
    analysed: tuple[str, ...]
    excluded: tuple[ClassifiedPath, ...]

    def excluded_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.excluded:
            counts[entry.category] = counts.get(entry.category, 0) + 1
        return counts

    def as_dict(self) -> dict:
        return {
            "analysed_count": len(self.analysed),
            "analysed": list(self.analysed),
            "excluded_count": len(self.excluded),
            "excluded_by_category": self.excluded_by_category(),
            "excluded": [
                {
                    "path": entry.path,
                    "category": entry.category,
                    "evidence": entry.evidence,
                    "grade": entry.grade,
                }
                for entry in self.excluded
            ],
        }


@dataclass(frozen=True)
class AnalyserStatus:
    """Whether one analyser ran, and under what version.

    `state` is one of `ran`, `absent`, `not-established` or `failed`. The last
    three each mean the analyser produced no finding for a reason that is not
    the absence of dead code, and the report has to keep them apart from a
    clean run.
    """

    name: str
    state: str
    version: str | None
    detail: str

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "state": self.state,
            "version": self.version,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class Finding:
    """One dead-code candidate and the reason it might not be one."""

    analyser: str
    path: str
    symbol: str | None
    evidence: str
    confidence: str
    false_positive_boundary: str

    def as_dict(self) -> dict:
        return {
            "analyser": self.analyser,
            "path": self.path,
            "symbol": self.symbol,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "false_positive_boundary": self.false_positive_boundary,
        }


@dataclass(frozen=True)
class Report:
    """The whole result. Both renderings read this and nothing else."""

    commit: str
    universe: Universe
    statuses: tuple[AnalyserStatus, ...]
    findings: tuple[Finding, ...]

    def as_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "tool": TOOL,
            "commit": self.commit,
            "universe": self.universe.as_dict(),
            "analysers": [status.as_dict() for status in self.statuses],
            "findings": [finding.as_dict() for finding in self.findings],
        }


def run_git(root: Path, *arguments: str) -> str:
    """Run one git command with a fixed argv and no shell."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as error:
        raise Refusal("git is not available on PATH") from error
    except subprocess.TimeoutExpired as error:
        raise Refusal(f"git {arguments[0]} timed out after {GIT_TIMEOUT_SECONDS}s") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise Refusal(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout


def repository_root(start: Path) -> Path:
    """Resolve the worktree root that contains `start`."""
    output = run_git(start, "rev-parse", "--show-toplevel").strip()
    if not output:
        raise Refusal(f"{start} is not inside a git worktree")
    return Path(output).resolve()


def resolve_commit(root: Path) -> str:
    commit = run_git(root, "rev-parse", "HEAD").strip()
    if not commit:
        raise Refusal("HEAD does not resolve to a commit")
    return commit


def require_clean_tree(root: Path) -> None:
    """Refuse a tracked modification.

    Untracked files are not consulted. The universe is the tracked tree at the
    commit, so a file git has never seen cannot change what was analysed, and
    refusing on one would make the command unusable beside any scratch file.
    """
    porcelain = run_git(root, "status", "--porcelain", "--untracked-files=no")
    changed = [line[3:] for line in porcelain.splitlines() if line.strip()]
    if changed:
        listed = ", ".join(sorted(changed)[:5])
        more = "" if len(changed) <= 5 else f" and {len(changed) - 5} more"
        raise Refusal(
            f"the checkout has {len(changed)} modified tracked file(s): {listed}{more}; "
            "commit or stash before analysing, because a report names one commit"
        )


def tracked_paths(root: Path, commit: str) -> tuple[str, ...]:
    """Every path tracked at the analysed commit, in sorted order."""
    listing = run_git(root, "ls-tree", "-r", "--name-only", "-z", commit)
    paths = tuple(sorted(entry for entry in listing.split("\0") if entry))
    return paths


def load_boundary(root: Path) -> dict[str, ClassifiedPath]:
    """Read the Horos boundary and return its hard entries by path.

    The document is validated before use. A malformed boundary is refused by
    name rather than silently read as an empty classification, because an empty
    classification would put every generated and vendored path back into the
    analysed universe and produce a report full of confident nonsense.
    """
    location = root / BOUNDARY_PATH
    try:
        raw = location.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise Refusal(f"{BOUNDARY_PATH.as_posix()} is absent; run horos scan first") from error
    except OSError as error:
        raise Refusal(f"{BOUNDARY_PATH.as_posix()} cannot be read: {error}") from error
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        raise Refusal(f"{BOUNDARY_PATH.as_posix()} is not valid JSON: {error}") from error
    if not isinstance(document, dict):
        raise Refusal(f"{BOUNDARY_PATH.as_posix()} is not a JSON object")
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise Refusal(f"{BOUNDARY_PATH.as_posix()} has no entries list")

    classified: dict[str, ClassifiedPath] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise Refusal(f"{BOUNDARY_PATH.as_posix()} entry {index} is not an object")
        fields = {}
        for name in ("path", "category", "evidence", "grade"):
            value = entry.get(name)
            if not isinstance(value, str) or not value:
                raise Refusal(
                    f"{BOUNDARY_PATH.as_posix()} entry {index} has no usable {name}"
                )
            fields[name] = value
        if fields["grade"] != EXCLUDING_GRADE:
            continue
        classified[fields["path"]] = ClassifiedPath(**fields)
    return classified


def discover(root: Path) -> Universe:
    """Build the analysed universe at HEAD, minus the classified sinks."""
    require_clean_tree(root)
    commit = resolve_commit(root)
    tracked = tracked_paths(root, commit)
    classified = load_boundary(root)

    analysed = tuple(path for path in tracked if path not in classified)
    excluded = tuple(classified[path] for path in tracked if path in classified)

    if len(analysed) < UNIVERSE_FLOOR:
        raise Refusal(
            f"discovery returned {len(analysed)} analysable paths from "
            f"{len(tracked)} tracked; this is a collapsed walk, not an empty repository"
        )
    return Universe(commit=commit, analysed=analysed, excluded=excluded)


def collect(root: Path, universe: Universe) -> tuple[tuple[AnalyserStatus, ...], tuple[Finding, ...]]:
    """Run every registered analyser and gather its status and findings."""
    statuses: list[AnalyserStatus] = []
    findings: list[Finding] = []
    for name in sorted(ANALYSERS):
        analyser = ANALYSERS[name]
        status, produced = analyser(root, universe)  # type: ignore[operator]
        statuses.append(status)
        findings.extend(produced)
    findings.sort(key=lambda item: (item.analyser, item.path, item.symbol or "", item.evidence))
    return tuple(statuses), tuple(findings)


def build_report(root: Path) -> Report:
    universe = discover(root)
    statuses, findings = collect(root, universe)
    return Report(
        commit=universe.commit,
        universe=universe,
        statuses=statuses,
        findings=findings,
    )


def render_json(report: Report) -> str:
    return json.dumps(report.as_dict(), sort_keys=True, indent=2) + "\n"


def render_text(report: Report) -> str:
    """Render the same model the JSON renders. Neither reads the other."""
    document = report.as_dict()
    universe = document["universe"]
    lines = [
        f"{TOOL} report  schema {document['schema']}",
        f"commit    {document['commit']}",
        f"universe  {universe['analysed_count']} analysed, "
        f"{universe['excluded_count']} excluded",
    ]
    by_category = universe["excluded_by_category"]
    if by_category:
        summary = ", ".join(f"{name} {by_category[name]}" for name in sorted(by_category))
        lines.append(f"excluded  {summary}")
    lines.append("")

    lines.append("analysers")
    if not document["analysers"]:
        lines.append("  none registered; this report establishes no reachability result")
    for status in document["analysers"]:
        version = f" {status['version']}" if status["version"] else ""
        lines.append(f"  {status['name']}{version}  {status['state']}  {status['detail']}")
    lines.append("")

    findings = document["findings"]
    lines.append(f"findings  {len(findings)}")
    if not findings:
        lines.append("  none")
    for finding in findings:
        symbol = f" {finding['symbol']}" if finding["symbol"] else ""
        lines.append(f"  [{finding['confidence']}] {finding['analyser']}  {finding['path']}{symbol}")
        lines.append(f"      saw     {finding['evidence']}")
        lines.append(f"      but     {finding['false_positive_boundary']}")
    return "\n".join(lines) + "\n"


def sweep_orphans(directory: Path) -> None:
    """Remove this command's own abandoned temporaries and nothing else."""
    try:
        candidates = list(directory.iterdir())
    except OSError:
        return
    for candidate in candidates:
        if not candidate.name.startswith(TEMP_PREFIX):
            continue
        try:
            if candidate.is_file() and not candidate.is_symlink():
                candidate.unlink()
        except OSError:
            continue


def confine(root: Path, candidate: str) -> Path:
    """Resolve a write target inside the repository root or refuse it."""
    if "\x00" in candidate:
        raise Refusal("the output path contains a null byte")
    supplied = Path(candidate)
    lexical = supplied if supplied.is_absolute() else root / supplied
    resolved = lexical.resolve()
    root_resolved = root.resolve()
    if resolved == root_resolved or root_resolved not in resolved.parents:
        raise Refusal(f"the output path {candidate} escapes the repository root")
    return resolved


def atomic_write(target: Path, payload: str) -> None:
    """Write through a temporary in the target's own directory, then replace."""
    directory = target.parent
    directory.mkdir(parents=True, exist_ok=True)
    sweep_orphans(directory)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=directory,
        prefix=TEMP_PREFIX,
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def command_report(arguments: argparse.Namespace) -> int:
    root = repository_root(Path(arguments.directory).resolve())
    report = build_report(root)
    rendered = render_json(report) if arguments.json else render_text(report)
    if arguments.output is None:
        sys.stdout.write(rendered)
    else:
        atomic_write(confine(root, arguments.output), rendered)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dead_code.py", description=__doc__)
    parser.add_argument(
        "--directory",
        default=".",
        help="a path inside the repository to analyse (default: the current directory)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    report = subparsers.add_parser("report", help="report the universe and its candidates")
    report.add_argument("--json", action="store_true", help="emit the report as JSON")
    report.add_argument(
        "--output",
        default=None,
        help="write the report to this path inside the repository instead of stdout",
    )
    report.set_defaults(handler=command_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return arguments.handler(arguments)
    except Refusal as refusal:
        print(f"dead_code.py: {refusal}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
