#!/usr/bin/env python3
"""Ephoros signal lint.

The mechanical subset of the skill: the rules a parser can settle without
reading intent. Everything else in SKILL.md stays a judgement.

  E001  a log message assembled by formatting, so its values cannot be queried
  E002  a metric label drawn from an unbounded source
  E003  a duration summarised as a mean
  E004  a supported YAML alert entry has no local runbook annotation
  E005  telemetry keyed by wallet address: a metric label, dashboard key or log index

Exit 0 clean, 1 findings, 2 bad invocation.

Deliberate exceptions state a reason: `# ephoros: allow <why>` in Python and
YAML, `// ephoros: allow <why>` in TypeScript.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from lib.typescript_lexer import lex  # noqa: E402

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

# One concern, one code: E005 claims the address-shaped labels, E002 keeps
# every other unbounded fragment.
ADDRESS_KEY = re.compile(r"(?:^|_)(?:address|wallet|addr)s?(?:_|$)", re.IGNORECASE)
HEX_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
DASHBOARD_NAME = re.compile(r"(?:^|_|\.)(?:dashboard|panel)s?$", re.IGNORECASE)

DURATION = re.compile(
    r"(?:^|_)(?:duration|latency|elapsed|seconds|secs|millis|ms|runtime|response_?time"
    r"|took|wait|time)s?(?:_|$)",
    re.IGNORECASE,
)
MEAN_FUNCS = {"mean", "fmean", "average", "avg"}

ALLOW = re.compile(r"(?:#|//)\s*ephoros:\s*allow\s+(?P<reason>\S.*)$")
YAML_SUFFIXES = {".yaml", ".yml"}
TYPESCRIPT_SUFFIXES = {".ts", ".tsx"}
TYPESCRIPT_MAX_BYTES = 1 << 20

# The TypeScript surface, read through the shared masked lexer the way phylax
# reads it. Recognition splits identifiers on underscore and camel-case
# boundaries, so `walletAddress` and `wallet_address` name the same key.
TS_IDENTIFIER = r"[A-Za-z_$][\w$]*"
TS_WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")
TS_CHAIN = re.compile(
    rf"(?<![\w$.])(?P<chain>{TS_IDENTIFIER}(?:\s*\.\s*{TS_IDENTIFIER})*)"
    r"\s*(?P<open>[\[(])")
TS_LABEL_PROPERTY = re.compile(
    r"(?<![\w$])(?:labels|labelnames|label_names|tags|attributes)"
    r"\s*:\s*(?P<open>[\[{])")
TS_INDEX_PROPERTY = re.compile(r"(?<![\w$])index\s*:\s*")
TS_ADDRESS_WORDS = frozenset({"address", "addresses", "addr", "addrs",
                              "wallet", "wallets"})
TS_METRIC_WORDS = frozenset({"metric", "metrics", "counter", "counters",
                             "gauge", "gauges", "histogram", "histograms",
                             "analytics", "telemetry", "statsd"})
TS_DASHBOARD_WORDS = frozenset({"dashboard", "dashboards", "panel", "panels"})
TS_LOG_WORDS = frozenset({"log", "logs", "logger", "logging"})
MAX_YAML_BYTES = 1 << 20
ALERT = re.compile(r"^-\s+alert\s*:")
ANNOTATIONS = re.compile(r"^annotations\s*:\s*$")
LABELS = re.compile(r"^labels\s*:\s*$")
YAML_KEY = re.compile(r"^(?P<key>[^\s:#-][^:]*?)\s*:")
RUNBOOK = re.compile(r"^runbook\s*:\s*(?P<path>.+?)\s*$", re.DOTALL)
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


def _address_key(label: str) -> bool:
    return bool(ADDRESS_KEY.search(label) or HEX_ADDRESS.fullmatch(label))


def _address_shaped(node: ast.AST) -> str:
    """Return the address-shaped name or literal in a key position, or ""."""
    if isinstance(node, ast.Name) and ADDRESS_KEY.search(node.id):
        return node.id
    if isinstance(node, ast.Attribute) and ADDRESS_KEY.search(node.attr):
        return node.attr
    if _is_str_literal(node) and _address_key(node.value):
        return node.value
    return ""


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

    def _keyed_by_address(self, node: ast.AST, position: str, key: str) -> None:
        self._add(node, "E005",
                  f"{position} `{key}` keys telemetry by wallet address; "
                  "put it in an event")

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in LOG_METHODS \
                and LOGGER_NAME.search(_name_of(func.value)):
            if node.args and _built_by_formatting(node.args[0]):
                self._add(node, "E001",
                          "log message built by formatting; use a stable name and fields")

        if isinstance(func, ast.Attribute):
            if func.attr == "labels":
                for keyword in node.keywords:
                    if keyword.arg and ADDRESS_KEY.search(keyword.arg):
                        self._keyed_by_address(node, "metric label", keyword.arg)
                for arg in node.args:
                    if _is_str_literal(arg) and HEX_ADDRESS.fullmatch(arg.value):
                        self._keyed_by_address(node, "metric label", arg.value)
            if LOGGER_NAME.search(_name_of(func.value)):
                for keyword in node.keywords:
                    if keyword.arg == "index":
                        key = _address_shaped(keyword.value)
                        if key:
                            self._keyed_by_address(node, "log index", key)

        for keyword in node.keywords:
            if keyword.arg in LABEL_KWARGS:
                for label in self._label_names(keyword.value):
                    if _address_key(label):
                        self._keyed_by_address(node, "metric label", label)
                    elif UNBOUNDED.search(label):
                        self._add(node, "E002",
                                  f"metric label `{label}` is unbounded; put it in an event")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        key = _address_shaped(node.slice)
        if key:
            target = _name_of(node.value)
            if DASHBOARD_NAME.search(target):
                self._keyed_by_address(node, "dashboard key", key)
            elif LOGGER_NAME.search(target):
                self._keyed_by_address(node, "log index", key)
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


def _yaml_quote_starts(line: str, index: int) -> bool:
    """Return whether a quote occupies a supported quoted-scalar start."""
    prefix = line[:index]
    stripped = prefix.strip()
    separated = bool(prefix) and prefix[-1] in " \t"
    return not stripped or (separated and (
        stripped == "-" or prefix.rstrip().endswith(":")))


def _yaml_plain_scalar_indent(content: str) -> int | None:
    """Return the key indent for a supported inline plain scalar."""
    indent = len(content) - len(content.lstrip(" "))
    stripped = content[indent:]
    sequence = stripped.startswith("- ")
    if sequence:
        stripped = stripped[2:]
    match = re.match(r"^[^:#][^:]*:[ \t]+(?P<value>\S.*)$", stripped)
    if not match or match.group("value")[0] in "'\"|>[{&*!%@`":
        return None
    return indent + 2 if sequence else indent


def _yaml_plain_continuation(line: str) -> str:
    """Return folded plain-scalar text before a separated YAML comment."""
    for index, character in enumerate(line):
        if character == "#" and (index == 0 or line[index - 1] in " \t"):
            return line[:index].strip()
    return line.strip()


def _split_yaml_comment(
        line: str, quote: str | None = None) -> tuple[str, str, str | None]:
    """Split YAML content and comment while carrying a quoted scalar."""
    active = quote
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue
        if active == '"':
            if character == "\\":
                escaped = True
            elif character == '"':
                active = None
            continue
        if active == "'":
            if character == "'" and index + 1 < len(line) \
                    and line[index + 1] == "'":
                escaped = True
            elif character == "'":
                active = None
            continue
        if character in "'\"" and _yaml_quote_starts(line, index):
            active = character
        elif (character == "#"
              and (index == 0 or line[index - 1] in " \t")):
            return line[:index], line[index:], None
    return line, "", active


def _yaml_allow_lines(lines: list[str]) -> set[int]:
    """Return reasoned pragma lines that are actual YAML comments."""
    allowed: set[int] = set()
    scalar_indent: int | None = None
    plain_indent: int | None = None
    quote: str | None = None
    for number, raw in enumerate(lines, start=1):
        if scalar_indent is not None:
            if not raw.strip():
                continue
            raw_indent = len(raw) - len(raw.lstrip(" "))
            if raw_indent > scalar_indent:
                continue
            scalar_indent = None
        if plain_indent is not None:
            if not raw.strip():
                continue
            if not raw.lstrip().startswith("#"):
                raw_indent = len(raw) - len(raw.lstrip(" "))
                if raw_indent > plain_indent:
                    continue
            plain_indent = None
        started_in_quote = quote is not None
        content, comment, quote = _split_yaml_comment(raw, quote)
        if started_in_quote:
            if quote is None and ALLOW.search(comment):
                allowed.add(number)
            continue
        content = content.rstrip()
        if not content.strip():
            if not comment:
                continue
            if ALLOW.search(comment):
                allowed.add(number)
            continue
        indent = len(content) - len(content.lstrip(" "))
        if ALLOW.search(comment):
            allowed.add(number)
        if BLOCK_SCALAR.match(content[indent:]):
            scalar_indent = indent
        else:
            plain_indent = _yaml_plain_scalar_indent(content)
    return allowed


def _yaml_lines(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return significant block-YAML lines, excluding block scalar bodies."""
    out: list[tuple[int, int, str]] = []
    scalar_indent: int | None = None
    plain_indent: int | None = None
    plain_out_index: int | None = None
    plain_breaks = 0
    quote: str | None = None
    for number, raw in enumerate(lines, start=1):
        if scalar_indent is not None:
            if not raw.strip():
                continue
            raw_indent = len(raw) - len(raw.lstrip(" "))
            if raw_indent > scalar_indent:
                continue
            scalar_indent = None
        if plain_indent is not None:
            if not raw.strip():
                if plain_out_index is not None:
                    plain_breaks += 1
                continue
            if not raw.lstrip().startswith("#"):
                raw_indent = len(raw) - len(raw.lstrip(" "))
                if raw_indent > plain_indent:
                    if plain_out_index is not None:
                        continuation = _yaml_plain_continuation(raw)
                        if continuation:
                            first = out[plain_out_index]
                            separator = "\n" * plain_breaks if plain_breaks else " "
                            out[plain_out_index] = (
                                first[0], first[1],
                                f"{first[2]}{separator}{continuation}")
                            plain_breaks = 0
                    continue
            plain_indent = None
            plain_out_index = None
            plain_breaks = 0
        started_in_quote = quote is not None
        content, _, quote = _split_yaml_comment(raw, quote)
        if started_in_quote:
            continue
        content = content.rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        stripped = content[indent:]
        out.append((number, indent, stripped))
        if BLOCK_SCALAR.match(stripped):
            scalar_indent = indent
        else:
            plain_indent = _yaml_plain_scalar_indent(content)
            if plain_indent is not None and RUNBOOK.match(stripped):
                plain_out_index = len(out) - 1
    return out


def _relative_markdown(value: str) -> bool:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1].strip()
    return bool(value and value.lower().endswith(".md")
                and "\n" not in value and "\r" not in value
                and not value.startswith(("/", "\\"))
                and "://" not in value)


def _alert_label_findings(
        path: Path, significant: list[tuple[int, int, str]], allowed: set[int],
        index: int, end: int, child_indent: int | None) -> list[Finding]:
    """Return E005 findings for address-named keys under one alert's labels."""
    findings: list[Finding] = []
    cursor = index + 1
    while cursor < end:
        _, labels_indent, nested = significant[cursor]
        cursor += 1
        if labels_indent != child_indent or not LABELS.match(nested):
            continue
        key_child_indent = significant[cursor][1] if cursor < end else None
        while cursor < end:
            number, key_indent, candidate = significant[cursor]
            if key_indent <= labels_indent:
                break
            match = YAML_KEY.match(candidate)
            if key_indent == key_child_indent and match \
                    and _address_key(match.group("key")) \
                    and number not in allowed and number - 1 not in allowed:
                findings.append(Finding(
                    path, number, "E005",
                    f"alert label `{match.group('key')}` keys telemetry by "
                    "wallet address; put it in an event"))
            cursor += 1
    return findings


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
        findings.extend(_alert_label_findings(
            path, significant, allowed, index, end, alert_child_indent))
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

def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _masked(text: str, spans) -> str:
    """Blank comments, strings and other non-code while preserving offsets."""
    parts = []
    for kind, start, end in spans:
        segment = text[start:end]
        if kind == "code":
            parts.append(segment)
        else:
            parts.append("".join(ch if ch == "\n" else " " for ch in segment))
    return "".join(parts)


def _matching(mask: str, opening: int) -> int | None:
    pairs = {"(": ")", "[": "]", "{": "}"}
    if opening >= len(mask) or mask[opening] not in pairs:
        return None
    stack = [pairs[mask[opening]]]
    for index in range(opening + 1, len(mask)):
        current = mask[index]
        if current in pairs:
            stack.append(pairs[current])
        elif stack and current == stack[-1]:
            stack.pop()
            if not stack:
                return index
    return None


def _split_ranges(mask: str, start: int, end: int) -> list[tuple[int, int]]:
    """Split a comma list at lexical depth zero, retaining source offsets."""
    ranges = []
    stack = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    item = start
    for index in range(start, end):
        current = mask[index]
        if current in pairs:
            stack.append(pairs[current])
        elif stack and current == stack[-1]:
            stack.pop()
        elif current == "," and not stack:
            ranges.append((item, index))
            item = index + 1
    ranges.append((item, end))
    return ranges


def _ts_words(name: str) -> set[str]:
    return {word.lower() for word in TS_WORD.findall(name)}


def _ts_address_name(name: str) -> bool:
    return bool(_ts_words(name) & TS_ADDRESS_WORDS)


def _ts_address_string(value: str) -> bool:
    return bool(HEX_ADDRESS.fullmatch(value) or _ts_address_name(value))


def _ts_string_value(expression: str) -> str | None:
    expression = expression.strip()
    if len(expression) >= 2 and expression[0] == expression[-1] \
            and expression[0] in "'\"":
        return expression[1:-1]
    return None


def _ts_address_expression(text: str, mask: str, start: int, end: int) -> str:
    """Return the address-shaped name or literal in a key position, or ""."""
    expression = mask[start:end].strip()
    if re.fullmatch(rf"{TS_IDENTIFIER}(?:\s*\.\s*{TS_IDENTIFIER})*", expression):
        last = re.split(r"\s*\.\s*", expression)[-1]
        return last if _ts_address_name(last) else ""
    value = _ts_string_value(text[start:end])
    if value is not None and _ts_address_string(value):
        return value
    return ""


def _ts_keyed_by_address(path: Path, text: str, offset: int,
                         position: str, key: str) -> Finding:
    return Finding(path, _line_of(text, offset), "E005",
                   f"{position} `{key}` keys telemetry by wallet address; "
                   "put it in an event")


def _ts_object_keys(text: str, mask: str, opening: int,
                    closing: int) -> list[tuple[int, str]]:
    """Return (offset, key) for each address-shaped key of one object literal."""
    keys = []
    for start, end in _split_ranges(mask, opening + 1, closing):
        colon = -1
        stack = []
        pairs = {"(": ")", "[": "]", "{": "}"}
        for index in range(start, end):
            current = mask[index]
            if current in pairs:
                stack.append(pairs[current])
            elif stack and current == stack[-1]:
                stack.pop()
            elif current == ":" and not stack:
                colon = index
                break
        key_end = colon if colon != -1 else end
        key = _ts_address_expression(text, mask, start, key_end)
        if key:
            keys.append((start, key))
    return keys


def _ts_label_container(path: Path, text: str, mask: str, opening: int,
                        closing: int) -> list[Finding]:
    """E005 findings for address keys inside one label set container."""
    findings = []
    if mask[opening] == "{":
        for offset, key in _ts_object_keys(text, mask, opening, closing):
            findings.append(_ts_keyed_by_address(
                path, text, offset, "metric label", key))
    else:
        for start, end in _split_ranges(mask, opening + 1, closing):
            value = _ts_string_value(text[start:end])
            if value is not None and _ts_address_string(value):
                findings.append(_ts_keyed_by_address(
                    path, text, start, "metric label", value))
    return findings


def _ts_label_properties(path: Path, text: str, mask: str, start: int,
                         end: int) -> list[Finding]:
    """Label/tag/attribute sets inside one telemetry sink call's arguments."""
    findings = []
    for match in TS_LABEL_PROPERTY.finditer(mask, start, end):
        opening = match.start("open")
        closing = _matching(mask, opening)
        if closing is not None:
            findings.extend(_ts_label_container(path, text, mask, opening, closing))
    return findings


def _ts_labels_call(path: Path, text: str, mask: str, start: int,
                    end: int) -> list[Finding]:
    """The Prometheus instance style: `.labels({...})` or a literal address."""
    findings = []
    for arg_start, arg_end in _split_ranges(mask, start, end):
        argument = mask[arg_start:arg_end].strip()
        if argument.startswith("{"):
            opening = mask.index("{", arg_start, arg_end)
            closing = _matching(mask, opening)
            if closing is not None:
                for offset, key in _ts_object_keys(text, mask, opening, closing):
                    findings.append(_ts_keyed_by_address(
                        path, text, offset, "metric label", key))
        else:
            value = _ts_string_value(text[arg_start:arg_end])
            if value is not None and HEX_ADDRESS.fullmatch(value):
                findings.append(_ts_keyed_by_address(
                    path, text, arg_start, "metric label", value))
    return findings


def _ts_index_properties(path: Path, text: str, mask: str, start: int,
                         end: int) -> list[Finding]:
    """`index:` properties inside one logger or log-store call's arguments."""
    findings = []
    for match in TS_INDEX_PROPERTY.finditer(mask, start, end):
        value_end = match.end()
        stack = []
        pairs = {"(": ")", "[": "]", "{": "}"}
        for index in range(match.end(), end):
            current = mask[index]
            if current in pairs:
                stack.append(pairs[current])
            elif current in ")]}" and not stack:
                value_end = index
                break
            elif stack and current == stack[-1]:
                stack.pop()
            elif current == "," and not stack:
                value_end = index
                break
        else:
            value_end = end
        key = _ts_address_expression(text, mask, match.end(), value_end)
        if key:
            findings.append(_ts_keyed_by_address(
                path, text, match.start(), "log index", key))
    return findings


def check_typescript(path: Path, text: str) -> list[Finding]:
    spans, errors = lex(text)
    if errors:
        return [Finding(path, _line_of(text, offset), "E000",
                        f"could not lex: {reason}")
                for offset, reason in errors]
    mask = _masked(text, spans)
    findings: list[Finding] = []
    for match in TS_CHAIN.finditer(mask):
        segments = re.split(r"\s*\.\s*", match.group("chain"))
        if segments[0] == "console":
            continue  # command-line output is not telemetry
        opening = match.start("open")
        closing = _matching(mask, opening)
        if closing is None:
            continue
        last_words = _ts_words(segments[-1])
        if match.group("open") == "[":
            key = _ts_address_expression(text, mask, opening + 1, closing)
            if key and last_words & TS_DASHBOARD_WORDS:
                findings.append(_ts_keyed_by_address(
                    path, text, opening + 1, "dashboard key", key))
            elif key and last_words & TS_LOG_WORDS:
                findings.append(_ts_keyed_by_address(
                    path, text, opening + 1, "log index", key))
            continue
        chain_words = set().union(*(_ts_words(s) for s in segments))
        if chain_words & TS_METRIC_WORDS:
            findings.extend(_ts_label_properties(
                path, text, mask, opening + 1, closing))
        if len(segments) >= 2 and segments[-1] == "labels":
            findings.extend(_ts_labels_call(
                path, text, mask, opening + 1, closing))
        if len(segments) >= 2 and _ts_words(segments[-2]) & TS_LOG_WORDS:
            findings.extend(_ts_index_properties(
                path, text, mask, opening + 1, closing))
    return findings


def check(path: Path) -> list[Finding]:
    if path.suffix in TYPESCRIPT_SUFFIXES:
        try:
            with path.open("rb") as source:
                raw = source.read(TYPESCRIPT_MAX_BYTES + 1)
            if len(raw) > TYPESCRIPT_MAX_BYTES:
                return [Finding(path, 1, "E000",
                                "unreadable: TypeScript exceeds 1 MiB")]
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as err:
            return [Finding(path, 1, "E000", f"unreadable: {err}")]
        return [f for f in check_typescript(path, text)
                if not suppressed(text, f.line)]
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
            suffixes = (".py", *sorted(TYPESCRIPT_SUFFIXES),
                        *sorted(YAML_SUFFIXES))
            found = (child for suffix in suffixes
                     for child in root.rglob(f"*{suffix}"))
            out.extend(child for child in sorted(set(found))
                       if child.is_file()
                       and "__pycache__" not in child.parts
                       and "node_modules" not in child.parts
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
