#!/usr/bin/env python3
"""Check and synchronise the Promise Machine law at fixed repository paths."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import tempfile


CONTRACT_ID = "promise-machine/v1"
LAW_NAME = "PROMISE_MACHINE.md"
MARKER = (
    "<!-- promise-machine: contract=promise-machine/v1; "
    "canonical=PROMISE_MACHINE.md; copies=generated -->"
)
MAX_MARKDOWN_BYTES = 256 * 1024
REQUIRED_HEADINGS = (
    "# Promise Machine contract",
    "## Contract identity",
    "## Governing principle",
    "## Scope",
    "## Vocabulary",
    "## Evidence classes",
    "## Promise declarations",
    "## Consequence levels",
    "## Composition",
    "## Refusal and recovery",
    "## Exceptions",
    "## Conformance",
    "## Installation copies",
)
REQUIRED_FIELDS = (
    "Promise",
    "Evidence",
    "Evidence classes",
    "Boundary",
    "Authorises",
    "Consequence",
    "Refuses",
    "Recovery",
    "Exceptions",
)
PLUGIN_MANIFESTS = (
    Path(".claude-plugin/plugin.json"),
    Path(".codex-plugin/plugin.json"),
)


@dataclass(frozen=True)
class Finding:
    code: str
    fault: str
    path: str
    message: str
    remedy: str
    promise_id: str | None = None


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def confined(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False


def read_markdown(path: Path, root: Path, *, missing_code: str, unsafe_code: str):
    findings: list[Finding] = []
    shown = relative(path, root)
    if path.is_symlink() or not confined(path, root):
        findings.append(
            Finding(
                unsafe_code,
                "identity",
                shown,
                "contract path is a symlink or resolves outside the repository",
                "replace it with a regular file at the fixed destination",
            )
        )
        return None, findings
    if not path.is_file():
        findings.append(
            Finding(
                missing_code,
                "drift",
                shown,
                "required contract file is absent",
                "run scripts/promise_machine.py sync",
            )
        )
        return None, findings
    try:
        payload = path.read_bytes()
    except OSError as exc:
        findings.append(
            Finding(
                unsafe_code,
                "identity",
                shown,
                f"contract file could not be read: {exc}",
                "restore a readable regular file inside the repository",
            )
        )
        return None, findings
    if len(payload) > MAX_MARKDOWN_BYTES:
        findings.append(
            Finding(
                "PM003",
                "structural",
                shown,
                f"contract is {len(payload)} bytes; limit is {MAX_MARKDOWN_BYTES}",
                "reduce the authored law below the bounded-read limit",
            )
        )
        return None, findings
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        findings.append(
            Finding(
                "PM004",
                "structural",
                shown,
                "contract is not UTF-8",
                "write the contract as UTF-8 Markdown",
            )
        )
        return None, findings
    return (payload, text), findings


def check_law(root: Path):
    law_path = root / LAW_NAME
    loaded, findings = read_markdown(
        law_path, root, missing_code="PM001", unsafe_code="PM002"
    )
    if loaded is None:
        return None, findings
    payload, text = loaded
    lines = text.splitlines()
    if MARKER not in lines[:5]:
        findings.append(
            Finding(
                "PM005",
                "identity",
                LAW_NAME,
                "generated-copy marker is absent from the law header",
                "restore the promise-machine/v1 canonical/copies marker",
            )
        )
    for heading in REQUIRED_HEADINGS:
        if lines.count(heading) != 1:
            findings.append(
                Finding(
                    "PM006",
                    "structural",
                    LAW_NAME,
                    f"required heading must occur once: {heading}",
                    "restore the one normative section with that exact heading",
                )
            )
    versions = set(re.findall(r"promise-machine/v[0-9]+", text))
    if versions != {CONTRACT_ID}:
        findings.append(
            Finding(
                "PM007",
                "version",
                LAW_NAME,
                f"contract identities are {sorted(versions)!r}; expected only {CONTRACT_ID}",
                "use the shared contract identity and remove competing identities",
            )
        )
    for field in REQUIRED_FIELDS:
        if f"`{field}`" not in text:
            findings.append(
                Finding(
                    "PM008",
                    "structural",
                    LAW_NAME,
                    f"promise declaration field is absent: {field}",
                    "restore the field in the per-promise schema",
                )
            )
    principle = (
        "No skill may claim more than its evidence establishes, or authorise a more\n"
        "> consequential transition than that evidence warrants."
    )
    if principle not in text:
        findings.append(
            Finding(
                "PM009",
                "structural",
                LAW_NAME,
                "the governing principle is absent or changed",
                "restore the settled suite-wide principle exactly",
            )
        )
    return payload, findings


def discover_plugins(root: Path):
    findings: list[Finding] = []
    plugins_root = root / "plugins"
    if plugins_root.is_symlink() or not confined(plugins_root, root):
        findings.append(
            Finding(
                "PM011",
                "identity",
                "plugins",
                "plugin root is a symlink or resolves outside the repository",
                "restore plugins as a regular directory beneath the repository",
            )
        )
        return [], findings
    if not plugins_root.is_dir():
        findings.append(
            Finding(
                "PM010",
                "structural",
                "plugins",
                "no plugin directory exists",
                "restore the repository plugin tree",
            )
        )
        return [], findings

    plugins: list[Path] = []
    for entry in sorted(plugins_root.iterdir(), key=lambda item: item.name):
        if entry.is_symlink():
            findings.append(
                Finding(
                    "PM011",
                    "identity",
                    relative(entry, root),
                    "plugin directory is a symlink",
                    "replace it with a regular directory inside plugins",
                )
            )
            continue
        if not entry.is_dir():
            continue
        manifests = [entry / item for item in PLUGIN_MANIFESTS]
        present = [item for item in manifests if item.exists() or item.is_symlink()]
        if not present:
            continue
        unsafe = [item for item in present if item.is_symlink() or not confined(item, root)]
        if unsafe:
            findings.append(
                Finding(
                    "PM011",
                    "identity",
                    relative(unsafe[0], root),
                    "plugin manifest is a symlink or resolves outside the repository",
                    "restore a regular manifest at the fixed plugin path",
                )
            )
            continue
        plugins.append(entry)
    if not plugins:
        findings.append(
            Finding(
                "PM010",
                "structural",
                "plugins",
                "plugin discovery returned an empty set",
                "restore at least one manifested plugin; empty discovery never passes",
            )
        )
    return plugins, findings


def check_copies(root: Path, law: bytes | None, plugins: list[Path]):
    findings: list[Finding] = []
    if law is None:
        return findings
    for plugin in plugins:
        copy = plugin / LAW_NAME
        loaded, read_findings = read_markdown(
            copy, root, missing_code="PM012", unsafe_code="PM013"
        )
        findings.extend(read_findings)
        if loaded is None:
            continue
        payload, _ = loaded
        if payload != law:
            findings.append(
                Finding(
                    "PM014",
                    "drift",
                    relative(copy, root),
                    "plugin-local law differs from the authored root law",
                    "run scripts/promise_machine.py sync",
                )
            )
    return findings


def atomic_write(path: Path, payload: bytes):
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def sync_copies(root: Path, law: bytes, plugins: list[Path]):
    findings: list[Finding] = []
    written = 0
    for plugin in plugins:
        destination = plugin / LAW_NAME
        if destination.is_symlink() or not confined(destination, root):
            findings.append(
                Finding(
                    "PM013",
                    "identity",
                    relative(destination, root),
                    "copy destination is a symlink or resolves outside the repository",
                    "replace it with a regular fixed destination before synchronising",
                )
            )
            continue
        current = destination.read_bytes() if destination.is_file() else None
        if current == law:
            continue
        try:
            atomic_write(destination, law)
            written += 1
        except OSError as exc:
            findings.append(
                Finding(
                    "PM015",
                    "drift",
                    relative(destination, root),
                    f"atomic copy write failed: {exc}",
                    "restore a writable plugin directory and rerun sync",
                )
            )
    return written, findings


def report(command: str, root: Path, plugins: list[Path], findings: list[Finding], *, as_json: bool, written: int = 0):
    findings = sorted(findings, key=lambda item: (item.path, item.code, item.message))
    document = {
        "contract": CONTRACT_ID,
        "command": command,
        "ok": not findings,
        "counts": {
            "plugins": len(plugins),
            "copies": len(plugins),
            "written": written,
            "findings": len(findings),
        },
        "findings": [asdict(item) for item in findings],
    }
    if as_json:
        print(json.dumps(document, sort_keys=True, separators=(",", ":")))
    elif findings:
        for item in findings:
            promise = f" promise={item.promise_id}" if item.promise_id else ""
            print(
                f"{item.code} fault={item.fault} path={item.path}{promise}: "
                f"{item.message}; repair: {item.remedy}"
            )
        print(f"refused: {len(findings)} finding(s)")
    else:
        suffix = f"; wrote {written}" if command == "sync" else ""
        print(f"clean: {len(plugins)} plugin(s), {len(plugins)} copy/copies{suffix}")
    return 0 if not findings else 1


def repository_root(raw: str | None):
    candidate = Path(raw) if raw else Path(__file__).resolve().parents[1]
    if candidate.is_symlink():
        raise ValueError("repository root may not be a symlink")
    return candidate.resolve(strict=True)


def parse_only(raw: str):
    requested = tuple(item.strip() for item in raw.split(",") if item.strip())
    allowed = {"law", "copies"}
    unknown = sorted(set(requested) - allowed)
    if unknown or not requested:
        raise ValueError(f"unsupported --only value(s): {unknown or ['<empty>']}")
    return set(requested)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="write or check fixed plugin copies")
    sync_parser.add_argument("--check", action="store_true", help="check without writing")
    sync_parser.add_argument("--root", help=argparse.SUPPRESS)
    sync_parser.add_argument("--json", action="store_true", help="emit canonical JSON")

    check_parser = subparsers.add_parser("check", help="check the law and plugin copies")
    check_parser.add_argument("--only", default="law,copies")
    check_parser.add_argument("--root", help=argparse.SUPPRESS)
    check_parser.add_argument("--json", action="store_true", help="emit canonical JSON")

    args = parser.parse_args(argv)
    try:
        root = repository_root(args.root)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.command == "check":
        try:
            only = parse_only(args.only)
        except ValueError as exc:
            parser.error(str(exc))
        law, law_findings = check_law(root)
        findings = list(law_findings)
        plugins: list[Path] = []
        if "copies" in only:
            plugins, discovery_findings = discover_plugins(root)
            findings.extend(discovery_findings)
            findings.extend(check_copies(root, law, plugins))
        return report("check", root, plugins, findings, as_json=args.json)

    law, law_findings = check_law(root)
    plugins, discovery_findings = discover_plugins(root)
    findings = list(law_findings) + list(discovery_findings)
    written = 0
    if args.check:
        findings.extend(check_copies(root, law, plugins))
    elif not findings and law is not None:
        written, write_findings = sync_copies(root, law, plugins)
        findings.extend(write_findings)
        findings.extend(check_copies(root, law, plugins))
    return report("sync", root, plugins, findings, as_json=args.json, written=written)


if __name__ == "__main__":
    raise SystemExit(main())
