#!/usr/bin/env python3
"""Ephoros signal lint.

The mechanical subset of the skill: the rules a parser can settle without
reading intent. Everything else in SKILL.md stays a judgement.

  E001  a log message assembled by formatting, so its values cannot be queried
  E002  a metric label drawn from an unbounded source
  E003  a duration summarised as a mean
  E004  a supported YAML alert entry has no local runbook annotation

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
YAML_SUFFIXES = {".yaml", ".yml"}
MAX_YAML_BYTES = 1 << 20
ALERT = re.compile(r"^-\s+alert\s*:")
ANNOTATIONS = re.compile(r"^annotations\s*:\s*$")
RUNBOOK = re.compile(r"^runbook\s*:\s*(?P<path>.+?)\s*$")
BLOCK_SCALAR = re.compile(
    r"^(?:[^:#][^:]*:\s*|-\s+)[|>](?:[+-]?\d?|\d[+-]?)\s*$")


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


def _split_yaml_comment(line: str) -> tuple[str, str]:
    """Split content and comment without treating a quoted hash as a marker."""
    single = False
    double = False
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue
        if double and character == "\\":
            escaped = True
            continue
        if character == "'" and not double:
            single = not single
        elif character == '"' and not single:
            double = not double
        elif (character == "#" and not single and not double
              and (index == 0 or line[index - 1] in " \t")):
            return line[:index], line[index:]
    return line, ""


def _strip_yaml_comment(line: str) -> str:
    return _split_yaml_comment(line)[0]


def _yaml_allow_lines(lines: list[str]) -> set[int]:
    """Return reasoned pragma lines that are actual YAML comments."""
    allowed: set[int] = set()
    scalar_indent: int | None = None
    for number, raw in enumerate(lines, start=1):
        content, comment = _split_yaml_comment(raw)
        content = content.rstrip()
        if not content.strip():
            if not comment:
                continue
            comment_indent = len(raw) - len(raw.lstrip(" "))
            if scalar_indent is not None:
                if comment_indent > scalar_indent:
                    continue
                scalar_indent = None
            if ALLOW.search(comment):
                allowed.add(number)
            continue
        indent = len(content) - len(content.lstrip(" "))
        if scalar_indent is not None:
            if indent > scalar_indent:
                continue
            scalar_indent = None
        if ALLOW.search(comment):
            allowed.add(number)
        if BLOCK_SCALAR.match(content[indent:]):
            scalar_indent = indent
    return allowed


def _yaml_lines(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return significant block-YAML lines, excluding block scalar bodies."""
    out: list[tuple[int, int, str]] = []
    scalar_indent: int | None = None
    for number, raw in enumerate(lines, start=1):
        content = _strip_yaml_comment(raw).rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        stripped = content[indent:]
        if scalar_indent is not None:
            if indent > scalar_indent:
                continue
            scalar_indent = None
        out.append((number, indent, stripped))
        if BLOCK_SCALAR.match(stripped):
            scalar_indent = indent
    return out


def _relative_markdown(value: str) -> bool:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1].strip()
    return bool(value and value.lower().endswith(".md")
                and not value.startswith(("/", "\\"))
                and "://" not in value)


def _yaml_findings(path: Path, text: str) -> list[Finding]:
    lines = text.splitlines()
    significant = _yaml_lines(lines)
    allowed = _yaml_allow_lines(lines)
    findings: list[Finding] = []
    for index, (number, alert_indent, content) in enumerate(significant):
        if not ALERT.match(content):
            continue
        end = len(significant)
        for cursor in range(index + 1, len(significant)):
            _, indent, later = significant[cursor]
            if indent < alert_indent or (indent == alert_indent and later.startswith("-")):
                end = cursor
                break

        alert_child_indent = (significant[index + 1][1]
                              if index + 1 < end else None)
        annotated = False
        cursor = index + 1
        while cursor < end:
            _, annotations_indent, nested = significant[cursor]
            if (annotations_indent == alert_child_indent
                    and ANNOTATIONS.match(nested)):
                cursor += 1
                annotation_child_indent = (significant[cursor][1]
                                           if cursor < end else None)
                while cursor < end:
                    _, runbook_indent, candidate = significant[cursor]
                    if runbook_indent <= annotations_indent:
                        break
                    match = RUNBOOK.match(candidate)
                    if (runbook_indent == annotation_child_indent and match
                            and _relative_markdown(match.group("path"))):
                        annotated = True
                        break
                    cursor += 1
            if annotated:
                break
            cursor += 1

        if not annotated and number not in allowed and number - 1 not in allowed:
            findings.append(Finding(
                path, number, "E004",
                "alert entry has no nested `annotations.runbook` Markdown path"))
    return findings

def check(path: Path) -> list[Finding]:
    if path.suffix in YAML_SUFFIXES:
        try:
            with path.open("rb") as source:
                raw = source.read(MAX_YAML_BYTES + 1)
            if len(raw) > MAX_YAML_BYTES:
                return [Finding(path, 1, "E000", "unreadable: YAML exceeds 1 MiB")]
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as err:
            return [Finding(path, 1, "E000", f"unreadable: {err}")]
        return _yaml_findings(path, text)
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
            found = (child for suffix in (".py", *sorted(YAML_SUFFIXES))
                     for child in root.rglob(f"*{suffix}"))
            out.extend(child for child in sorted(set(found))
                       if "__pycache__" not in child.parts
                       and "fixtures" not in child.relative_to(root).parts[:-1])
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
