#!/usr/bin/env python3
"""Ephoros signal lint.

The mechanical subset of the skill: the rules a parser can settle without
reading intent. Everything else in SKILL.md stays a judgement.

  E001  a log message assembled by formatting, so its values cannot be queried
  E002  a metric label drawn from an unbounded source
  E003  a duration summarised as a mean

Exit 0 clean, 1 findings, 2 bad invocation.

Deliberate exceptions state a reason: `# ephoros: allow <why>`.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

LOG_METHODS = {"debug", "info", "warning", "warn", "error", "critical", "exception", "log"}
# A logger, not any object with an `info` method, and deliberately not `print`:
# command-line output is not telemetry, and this marketplace writes plenty of it.
LOGGER_NAME = re.compile(r"(?:^|_|\.)(?:log|logger|logging)$", re.IGNORECASE)

LABEL_KWARGS = {"labels", "labelnames", "label_names", "tags", "attributes"}
UNBOUNDED = re.compile(
    r"(?:^|_)(?:address|wallet|hash|tx|txid|txhash|nonce|url|uri|path|email|user"
    r"|userid|account|request_?id|run_?id|trace_?id|session|error|message|id)s?(?:_|$)",
    re.IGNORECASE,
)

DURATION = re.compile(
    r"(?:^|_)(?:duration|latency|elapsed|seconds|secs|millis|ms|runtime|response_?time"
    r"|took|wait|time)s?(?:_|$)",
    re.IGNORECASE,
)
MEAN_FUNCS = {"mean", "fmean", "average", "avg"}

ALLOW = re.compile(r"#\s*ephoros:\s*allow\s+(?P<reason>\S.*)$")


def suppressed(text: str, line: int) -> bool:
    lines = text.splitlines()
    for number in (line, line - 1):
        if 1 <= number <= len(lines) and ALLOW.search(lines[number - 1]):
            return True
    return False


class Finding:
    __slots__ = ("path", "line", "code", "message")

    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path, self.line, self.code, self.message = path, line, code, message

    def as_dict(self) -> dict:
        return {"path": str(self.path), "line": self.line, "code": self.code,
                "message": self.message}

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def _name_of(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name_of(node.value)}.{node.attr}".lstrip(".")
    return ""


def _is_str_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _built_by_formatting(node: ast.AST) -> bool:
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return any(_is_str_literal(s) or isinstance(s, ast.JoinedStr)
                   for s in (node.left, node.right))
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
        and node.func.attr == "format" and _is_str_literal(node.func.value)


def _is_mean_call(node: ast.AST) -> bool:
    """statistics.mean(x), np.average(x), or the sum(x) / len(x) idiom."""
    if isinstance(node, ast.Call):
        func = node.func
        attr = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        return attr in MEAN_FUNCS
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left, right = node.left, node.right
        return (isinstance(left, ast.Call) and getattr(left.func, "id", "") == "sum"
                and isinstance(right, ast.Call) and getattr(right.func, "id", "") == "len")
    return False


def _mentions_duration(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and DURATION.search(child.id):
            return True
        if isinstance(child, ast.Attribute) and DURATION.search(child.attr):
            return True
        if _is_str_literal(child) and DURATION.search(child.value):
            return True
    return False


class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[Finding] = []

    def _add(self, node: ast.AST, code: str, message: str) -> None:
        self.findings.append(Finding(self.path, node.lineno, code, message))

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in LOG_METHODS \
                and LOGGER_NAME.search(_name_of(func.value)):
            if node.args and _built_by_formatting(node.args[0]):
                self._add(node, "E001",
                          "log message built by formatting; use a stable name and fields")

        for keyword in node.keywords:
            if keyword.arg in LABEL_KWARGS:
                for label in self._label_names(keyword.value):
                    if UNBOUNDED.search(label):
                        self._add(node, "E002",
                                  f"metric label `{label}` is unbounded; put it in an event")
        self.generic_visit(node)

    @staticmethod
    def _label_names(node: ast.AST) -> list[str]:
        if isinstance(node, ast.Dict):
            return [k.value for k in node.keys if _is_str_literal(k)]
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return [e.value for e in node.elts if _is_str_literal(e)]
        return []

    def visit_Assign(self, node: ast.Assign) -> None:
        if _is_mean_call(node.value):
            names = [_name_of(t) for t in node.targets]
            if any(DURATION.search(n) for n in names if n) or _mentions_duration(node.value):
                self._add(node, "E003",
                          "duration summarised as a mean; record a histogram and read p95")
        self.generic_visit(node)


def check(path: Path) -> list[Finding]:
    if path.suffix != ".py":
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [Finding(path, 1, "E000", f"unreadable: {err}")]
    try:
        tree = ast.parse(text)
    except SyntaxError as err:
        return [Finding(path, err.lineno or 1, "E000", f"could not parse: {err.msg}")]
    visitor = Visitor(path)
    visitor.visit(tree)
    return [f for f in visitor.findings if not suppressed(text, f.line)]


def walk(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        root = Path(raw)
        if root.is_dir():
            out.extend(c for c in sorted(root.rglob("*.py")) if "__pycache__" not in c.parts)
        else:
            out.append(root)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ephoros signal lint.")
    parser.add_argument("paths", nargs="*", default=["."])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    for path in walk(args.paths or ["."]):
        findings.extend(check(path))

    if args.format == "json":
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
