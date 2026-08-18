#!/usr/bin/env python3
"""Phylax boundary lint.

The mechanical subset of the skill: the rules a parser can settle without
reading intent. Everything else in SKILL.md stays a judgement.

  P001  a shell invocation, which invites a command built from data
  P002  a subprocess command passed as a string rather than an argument list
  P003  a requirement with no exact pin
  P004  a credential in source, or handed to something that writes output

Exit 0 clean, 1 findings, 2 bad invocation.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

RUNNERS = {"run", "call", "check_call", "check_output", "Popen"}
WRITERS = {"print", "debug", "info", "warning", "warn", "error", "critical", "exception"}

CREDENTIAL = re.compile(
    r"(?:^|_)(?:priv(?:ate)?_?key|secret|passwd|password|mnemonic|seed_?phrase"
    r"|api_?key|access_?token|auth_?token|bearer|credential)s?(?:_|$)",
    re.IGNORECASE,
)
# A value that is plainly not a live credential.
PLACEHOLDER = re.compile(r"^(?:|x{3,}|\.{3}|<[^>]*>|\{[^}]*\}|\$\{?[A-Z_]+\}?|changeme|todo)$", re.I)
PIN = re.compile(r"(==|@(?:git\+)?[0-9a-f]{40})")
SKIP_REQ = re.compile(r"^\s*(?:#|-r\s|--|$)")


ALLOW = re.compile(r"#\s*phylax:\s*allow\s+(?P<reason>\S.*)$")


def suppressed(text: str, line: int) -> bool:
    """True when the finding's line, or the one above it, states a reason."""
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


def _attr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _is_str_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _is_formatted(node: ast.AST) -> bool:
    """A string built at runtime rather than written out whole.

    `a + b` is only string building when one side is plainly a string.
    Concatenating two lists to assemble an argument list is the correct
    construction, and flagging it teaches people to ignore the tool.
    """
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return any(_is_str_literal(side) or isinstance(side, ast.JoinedStr)
                   for side in (node.left, node.right))
    if isinstance(node, ast.Call) and _attr_name(node.func) in {"format", "join"}:
        return True
    return False


def _is_string(node: ast.AST) -> bool:
    return _is_str_literal(node) or _is_formatted(node)


class Visitor(ast.NodeVisitor):
    """Flag only calls that resolve to subprocess.

    A bare name match is worthless here: this marketplace has a test helper
    called `run` and an RPC client with a `.call`, and neither starts a
    process.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[Finding] = []
        self.modules: set[str] = set()
        self.direct: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "subprocess":
                self.modules.add(alias.asname or "subprocess")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "subprocess":
            for alias in node.names:
                if alias.name in RUNNERS:
                    self.direct.add(alias.asname or alias.name)
        self.generic_visit(node)

    def _starts_process(self, func: ast.AST) -> bool:
        if isinstance(func, ast.Attribute):
            base = func.value
            return (isinstance(base, ast.Name) and base.id in self.modules
                    and func.attr in RUNNERS)
        return isinstance(func, ast.Name) and func.id in self.direct

    def _add(self, node: ast.AST, code: str, message: str) -> None:
        self.findings.append(Finding(self.path, node.lineno, code, message))

    def visit_Call(self, node: ast.Call) -> None:
        if self._starts_process(node.func):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self._add(node, "P001", "shell invocation; pass an argument list instead")
            if node.args and _is_string(node.args[0]):
                built = " built by formatting" if _is_formatted(node.args[0]) else ""
                self._add(node, "P002", f"command passed as a string{built}; pass a list")

        if _attr_name(node.func) in WRITERS:
            for arg in node.args + [kw.value for kw in node.keywords]:
                if isinstance(arg, ast.Name) and CREDENTIAL.search(arg.id):
                    self._add(node, "P004", f"credential-named value `{arg.id}` written to output")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            if not PLACEHOLDER.match(node.value.value):
                for target in node.targets:
                    label = _attr_name(target)
                    if label and CREDENTIAL.search(label):
                        self._add(node, "P004", f"credential `{label}` assigned a literal")
        self.generic_visit(node)


def check_python(path: Path, text: str) -> list[Finding]:
    try:
        tree = ast.parse(text)
    except SyntaxError as err:
        return [Finding(path, err.lineno or 1, "P000", f"could not parse: {err.msg}")]
    visitor = Visitor(path)
    visitor.visit(tree)
    return visitor.findings


def check_requirements(path: Path, text: str) -> list[Finding]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        if SKIP_REQ.match(line):
            continue
        if not PIN.search(line.split("#", 1)[0]):
            findings.append(Finding(path, number, "P003",
                                    f"requirement `{line.strip()}` has no exact pin"))
    return findings


def check(path: Path) -> list[Finding]:
    requirements = path.name.startswith("requirements") and path.suffix == ".txt"
    if not requirements and path.suffix != ".py":
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [Finding(path, 1, "P000", f"unreadable: {err}")]
    found = check_requirements(path, text) if requirements else check_python(path, text)
    return [f for f in found if not suppressed(text, f.line)]


def walk(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        root = Path(raw)
        if root.is_dir():
            for child in sorted(root.rglob("*")):
                if child.is_file() and "__pycache__" not in child.parts:
                    out.append(child)
        else:
            out.append(root)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phylax boundary lint.")
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
