#!/usr/bin/env python3
"""Janus command-line surface: manifest validation and report rendering.

This module is built across the Fiat runbook. Step 1 establishes the module and
its command dispatch; `validate` lands in step 2 and `report` in step 6. Each
subcommand is registered here and raises `NotImplementedError` until its step
lands, so the module imports cleanly from the first step and the test suite can
grow with it.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional


VERSION = "0.1.0"


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate hook manifests against the schema. Lands in step 2."""
    raise NotImplementedError("janus validate lands in runbook step 2")


def cmd_report(args: argparse.Namespace) -> int:
    """Render human and SARIF reports from a findings file. Lands in step 6."""
    raise NotImplementedError("janus report lands in runbook step 6")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="janus",
        description="Hook-conformance manifest validation and report rendering.",
    )
    parser.add_argument("--version", action="version", version=f"janus {VERSION}")
    sub = parser.add_subparsers(dest="command")

    validate = sub.add_parser("validate", help="validate hook manifests")
    validate.add_argument("manifests", nargs="+", help="manifest JSON files")
    validate.set_defaults(func=cmd_validate)

    report = sub.add_parser("report", help="render human and SARIF reports")
    report.add_argument("--findings", required=True, help="findings JSON file")
    report.add_argument("--md", help="human-readable Markdown output path")
    report.add_argument("--sarif", help="SARIF 2.1.0 output path")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
