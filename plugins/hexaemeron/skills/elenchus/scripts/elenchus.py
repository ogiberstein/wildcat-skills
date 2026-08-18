#!/usr/bin/env python3
"""Elenchus guard check.

A fix is guarded when it carries a test that fails without it. This puts that
claim to the parent tree instead of taking it on trust.

For a commit: take the test files it changed, apply them to its parent, and run
them there. A guard must fail on the parent by assertion. A test that passes
there proves nothing, and one that dies importing something the parent has not
got yet is inconclusive rather than proof.

  guarded       a changed test failed on the parent by assertion
  unguarded     the commit changed no test files
  passed        a changed test passed on the parent, so it guards nothing
  inconclusive  the run died before asserting, usually an import or build error

Exit 0 unless --require-guard is set and the result is not `guarded`.

The test command is yours to supply, so this runs anywhere git and a test
runner do. Nothing here assumes a particular project, language or CI.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_NAMES = ("test_", "_test.", ".test.", ".spec.", ".t.sol")
TEST_DIRS = ("test", "tests", "spec", "__tests__")

# A run that died before it could assert anything. Distinguishing this from a
# real failure is the whole difficulty: a new test dropped on the parent often
# cannot import the thing it tests, and calling that a passing guard would let
# every unguarded fix through.
BROKEN_RUN = (
    "importerror", "modulenotfounderror", "cannot find module",
    "no module named", "collection error", "errors while importing",
    "compiler run failed", "error ts", "syntaxerror", "cannot find name",
    "unable to resolve", "failed to compile",
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def is_test(path: str) -> bool:
    name = Path(path).name
    if any(marker in name for marker in TEST_NAMES):
        return True
    return any(part in TEST_DIRS for part in Path(path).parts[:-1])


def changed_tests(repo: Path, ref: str) -> list[str]:
    out = git(repo, "diff-tree", "--no-commit-id", "--name-only", "--diff-filter=AM", "-r", ref)
    return sorted(p for p in out.splitlines() if p and is_test(p))


def parent_of(repo: Path, ref: str) -> str | None:
    try:
        return git(repo, "rev-parse", f"{ref}^").strip()
    except RuntimeError:
        return None


def broken_run(output: str) -> bool:
    lowered = output.lower()
    return any(marker in lowered for marker in BROKEN_RUN)


def check(repo: Path, ref: str, command: list[str], timeout: int = 900) -> dict:
    tests = changed_tests(repo, ref)
    if not tests:
        return {"ref": ref, "status": "unguarded", "tests": [],
                "detail": "the commit changed no test files"}

    parent = parent_of(repo, ref)
    if parent is None:
        return {"ref": ref, "status": "inconclusive", "tests": tests,
                "detail": "the commit has no parent to compare against"}

    workdir = Path(tempfile.mkdtemp(prefix="elenchus-"))
    tree = workdir / "tree"
    try:
        git(repo, "worktree", "add", "--quiet", "--detach", str(tree), parent)
        for relative in tests:
            blob = git(repo, "show", f"{ref}:{relative}")
            target = tree / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(blob, encoding="utf-8")

        run = subprocess.run(command, cwd=tree, capture_output=True,
                             text=True, check=False, timeout=timeout)
        output = run.stdout + run.stderr

        if run.returncode == 0:
            status, detail = "passed", "the guard passed on the parent, so it guards nothing"
        elif broken_run(output):
            status, detail = "inconclusive", "the run died before asserting; read the output"
        else:
            status, detail = "guarded", "the guard failed on the parent, as a guard should"
        return {"ref": ref, "status": status, "tests": tests, "detail": detail,
                "exit_code": run.returncode, "output": output[-4000:]}
    except subprocess.TimeoutExpired:
        return {"ref": ref, "status": "inconclusive", "tests": tests,
                "detail": f"the run did not finish inside {timeout}s"}
    finally:
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(tree)],
                       capture_output=True, check=False)
        shutil.rmtree(workdir, ignore_errors=True)


def audit_line(result: dict) -> str:
    """The line to carry into the audit file's leads-not-pursued list."""
    return (f"Guard check on `{result['ref'][:12]}`: {result['status']} "
            f"-- {result['detail']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Elenchus guard check.")
    parser.add_argument("--repo", default=".", help="repository to inspect")
    parser.add_argument("--ref", default="HEAD", help="commit carrying the fix")
    parser.add_argument("--test-command", required=True,
                        help="how to run the tests, e.g. 'python3 -m unittest discover -s tests'")
    parser.add_argument("--require-guard", action="store_true",
                        help="exit 1 unless the fix is guarded")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        result = check(Path(args.repo).resolve(), args.ref,
                       args.test_command.split(), args.timeout)
    except RuntimeError as err:
        print(f"could not inspect the repository: {err}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(audit_line(result))
        for path in result["tests"]:
            print(f"  test: {path}")

    return 1 if args.require_guard and result["status"] != "guarded" else 0


if __name__ == "__main__":
    sys.exit(main())
