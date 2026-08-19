#!/usr/bin/env python3
"""Metron budget check.

The mechanical subset of the skill: the part a file and a comparison can settle.
Everything else in SKILL.md stays a judgement, and nothing here measures anything.
A run arrives from whatever measured it, the same way `hexctl audit-round` takes a
lint exit the caller reports.

  check    compare a recorded run against the budgets and the baseline
  record   append a run to the ledger, and promote it to baseline when asked

A budget carries a limit and a variance, because SKILL.md asks for both. A limit
alone fails a run that is a fraction over on a noisy machine. A variance alone
never catches a value that was unacceptable from the day it was written.

Verdicts, one per declared budget:

  over-budget   worse than the limit                                fails
  regressed     worse than the baseline by more than the variance   fails
  neutral       inside the variance either way                      passes
  improved      better than the baseline by more than the variance  passes
  unmeasured    the run carries no value for a declared budget      fails
  undeclared    the run carries a value no budget declares          fails

The last two are the reason this is not a threshold script. A run that quietly
stops reporting a budget would otherwise pass, and a name nobody declared is
either a typo or a budget that was never written down.

Exit 0 when every verdict passes, 1 when any fails, 2 on a bad invocation or a
file that cannot be read.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_BYTES = 4 * 1024 * 1024
"""These files are checked in beside the code, not fetched. A cap still keeps a
mistaken path from reading something enormous into memory."""

DIRECTIONS = ("lower_is_better", "higher_is_better")
"""Wall clock and bundle size are the first. Throughput and hit rate are the
second, and a check that assumed the first would call their improvement a
regression."""

REQUIRED = ("name", "unit", "limit", "variance", "direction")

PASSING = ("neutral", "improved")
FAILING = ("over-budget", "regressed", "unmeasured", "undeclared")


class BudgetError(ValueError):
    """A file that cannot be read as budgets, with the reason a caller can act on."""


def number(value) -> bool:
    """True for a real number this check will do arithmetic on.

    `bool` is excluded deliberately. Python makes `True` an integer, so a
    measurement of `true` would be compared against a limit and reported as a
    verdict.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def read_json(path: str, what: str):
    """A JSON document from disk, or a refusal naming what was being read."""
    where = Path(path)
    try:
        size = where.stat().st_size
    except OSError as error:
        raise BudgetError(f"cannot read {what} {path}: {error}")
    if size > MAX_BYTES:
        raise BudgetError(f"{what} {path} is larger than {MAX_BYTES} bytes")
    try:
        raw = where.read_bytes()
    except OSError as error:
        raise BudgetError(f"cannot read {what} {path}: {error}")
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        raise BudgetError(f"{what} {path} is not readable JSON: {error}")


def load_budgets(path: str) -> list[dict]:
    """The declared budgets, in file order, with every field checked.

    Order is kept rather than sorted, because the file is reviewed by a person and
    the report should read the way the file does.
    """
    document = read_json(path, "budget file")
    if not isinstance(document, dict):
        raise BudgetError("budget file must hold an object")
    entries = document.get("budgets")
    if not isinstance(entries, list):
        raise BudgetError("budget file needs a budgets array")
    if not entries:
        raise BudgetError("budget file declares no budgets")

    budgets: list[dict] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"budget {index + 1}"
        if not isinstance(entry, dict):
            raise BudgetError(f"{label} must be an object")
        absent = [field for field in REQUIRED if field not in entry]
        if absent:
            raise BudgetError(f"{label} is missing {', '.join(absent)}")
        name = entry["name"]
        if not isinstance(name, str) or not name.strip():
            raise BudgetError(f"{label} must name something")
        label = name
        if name in seen:
            raise BudgetError(f"budget {name} is declared twice")
        seen.add(name)
        if not isinstance(entry["unit"], str) or not entry["unit"].strip():
            raise BudgetError(f"{label} must state a unit")
        if not number(entry["limit"]):
            raise BudgetError(f"{label} limit must be a number, got {entry['limit']!r}")
        if entry["limit"] < 0:
            raise BudgetError(f"{label} limit must not be negative")
        variance = entry["variance"]
        if not number(variance):
            raise BudgetError(f"{label} variance must be a number, got {variance!r}")
        if not 0 <= variance < 1:
            raise BudgetError(
                f"{label} variance must be a fraction of the baseline from 0 up to "
                f"but not including 1, got {variance!r}"
            )
        if entry["direction"] not in DIRECTIONS:
            raise BudgetError(
                f"{label} direction must be one of {', '.join(DIRECTIONS)}, "
                f"got {entry['direction']!r}"
            )
        unknown = sorted(set(entry) - set(REQUIRED))
        if unknown:
            raise BudgetError(f"{label} carries unknown fields: {', '.join(unknown)}")
        budgets.append(dict(entry))
    return budgets


def load_measurements(path: str, what: str) -> dict:
    """A name-to-number mapping from a run or a baseline file."""
    document = read_json(path, what)
    if not isinstance(document, dict):
        raise BudgetError(f"{what} must hold an object of budget name to value")
    values = document.get("measurements", document)
    if not isinstance(values, dict):
        raise BudgetError(f"{what} measurements must be an object")
    for name, value in sorted(values.items()):
        if not isinstance(name, str) or not name.strip():
            raise BudgetError(f"{what} names a budget with no name")
        if not number(value):
            raise BudgetError(f"{what} value for {name} must be a number, got {value!r}")
    return dict(values)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metron budget check.")
    sub = parser.add_subparsers(dest="command", required=True)

    look = sub.add_parser("check", help="compare a run against the budgets and baseline")
    look.add_argument("--budgets", required=True)
    look.add_argument("--run", required=True)
    look.add_argument("--baseline")
    look.add_argument("--format", choices=("text", "json"), default="text")

    keep = sub.add_parser("record", help="append a run to the ledger")
    keep.add_argument("--budgets", required=True)
    keep.add_argument("--run", required=True)
    keep.add_argument("--ledger", required=True)
    keep.add_argument("--baseline")
    keep.add_argument("--note")
    keep.add_argument("--promote", action="store_true",
                      help="write this run over the baseline")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_budgets(args.budgets)
        load_measurements(args.run, "run")
        if args.baseline:
            load_measurements(args.baseline, "baseline")
    except BudgetError as error:
        print(f"metron: error: {error}", file=sys.stderr)
        return 2
    print("metron: budgets and measurements read; the comparison arrives in step 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
