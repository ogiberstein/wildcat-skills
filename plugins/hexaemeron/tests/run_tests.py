#!/usr/bin/env python3
"""Run the controller suite and print a pass count."""

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import unittest


def report_target(argv):
    """Parse one fresh report path contained by the current worktree."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--elenchus-report",
        action="append",
        metavar="PATH",
        help="write an elenchus.unittest.v1 result to a fresh worktree path",
    )
    arguments = parser.parse_args(argv)
    values = arguments.elenchus_report or []
    if len(values) > 1:
        parser.error("--elenchus-report may be supplied only once")
    if not values:
        return None

    raw = values[0]
    if not raw or "\x00" in raw:
        parser.error("--elenchus-report requires a non-empty path")
    target = Path(raw)
    try:
        target.resolve(strict=False).relative_to(Path.cwd().resolve())
    except (OSError, ValueError):
        parser.error("--elenchus-report must stay inside the current worktree")
    try:
        existing = target.lstat()
    except FileNotFoundError:
        existing = None
    except (OSError, ValueError):
        parser.error("--elenchus-report cannot be inspected")
    if existing is not None:
        parser.error("--elenchus-report target must not already exist")

    ancestor = target.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    try:
        if not ancestor.is_dir():
            parser.error("--elenchus-report parent is not a directory")
    except OSError:
        parser.error("--elenchus-report parent cannot be inspected")
    return target


def result_payload(result):
    """Return Elenchus's complete unittest counter schema."""
    return {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }


def write_report(target, payload):
    """Create the declared report without following or replacing a path."""
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(target, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("report target is not a regular file")
        body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        with os.fdopen(descriptor, "wb") as output:
            descriptor = None
            output.write(body)
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
        try:
            target.unlink()
        except OSError:
            pass
        raise


def main(argv=None):
    """Run the suite, optionally emit its report, and preserve suite exits."""
    target = report_target(sys.argv[1:] if argv is None else argv)
    here = os.path.dirname(os.path.abspath(__file__))
    suite = unittest.defaultTestLoader.discover(here, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)

    if target is not None:
        try:
            write_report(target, result_payload(result))
        except OSError:
            print("run_tests.py: report write failed", file=sys.stderr)
            return 2

    print(f"{total - failed}/{total} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
