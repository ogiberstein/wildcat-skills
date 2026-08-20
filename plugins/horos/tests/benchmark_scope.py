"""Record what a boundary check costs, whole-tree and scoped.

Emits one JSON object so a before-and-after pair can be compared without
reading prose, per `plugins/hexaemeron/skills/metron/SKILL.md`. It asserts
nothing: a machine-specific threshold in a test would fail on a different
machine rather than on a regression. The scoped figures are null until the
scoped check exists, and `scope_status` says why.

    python3 plugins/horos/tests/benchmark_scope.py --root . --scope plugins/alexandria --runs 5
"""

from pathlib import Path
import argparse
import io
import json
import os
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402


def timed_check(target, runs):
    """Return (median milliseconds, last exit code, last output)."""
    samples = []
    code = None
    text = ""
    for _ in range(runs):
        out = io.StringIO()
        started = time.perf_counter()
        code = horos.check_tree(target, out=out)
        samples.append((time.perf_counter() - started) * 1000.0)
        text = out.getvalue()
    return statistics.median(samples), code, text


def main(argv=None):
    parser = argparse.ArgumentParser(prog="benchmark_scope", description=__doc__)
    parser.add_argument("--root", default=".", help="repository root to check")
    parser.add_argument("--scope", required=True, help="descendant path to check")
    parser.add_argument("--runs", type=int, default=5, help="samples per target")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    scope = os.path.join(root, args.scope)

    full_median, full_code, full_text = timed_check(root, args.runs)
    scope_median, scope_code, scope_text = timed_check(scope, args.runs)

    def report(median, code, text):
        """A duration beside a refused check reads as a fast check. Null it."""
        if code == 2:
            return None, "unavailable: " + text.strip().splitlines()[0]
        return round(median, 3), "measured"

    full_report, full_status = report(full_median, full_code, full_text)
    scope_report, scope_status = report(scope_median, scope_code, scope_text)

    record = {
        "runs": args.runs,
        "root": args.root,
        "scope": args.scope,
        "full_tree_median_ms": full_report,
        "full_tree_exit": full_code,
        "full_tree_status": full_status,
        "scope_median_ms": scope_report,
        "scope_exit": scope_code,
        "scope_status": scope_status,
        "tracked_files_inspected_outside_scope": None,
    }
    json.dump(record, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
