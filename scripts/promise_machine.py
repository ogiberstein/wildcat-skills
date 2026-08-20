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
MAX_JSON_BYTES = 64 * 1024
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
SUPPORTED_EVIDENCE_CLASSES = {
    "checked",
    "recomputed",
    "proved",
    "measured",
    "recorded",
    "attested",
    "inferred",
    "unknown",
}
PROMISE_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


@dataclass(frozen=True)
class Finding:
    code: str
    fault: str
    path: str
    message: str
    remedy: str
    promise_id: str | None = None


@dataclass(frozen=True)
class SkillRecord:
    name: str
    path: str
    plugin: str
    governance: str
    ownership: str


@dataclass(frozen=True)
class Inventory:
    plugins: tuple[str, ...]
    skills: tuple[SkillRecord, ...]
    routers: tuple[str, ...]
    overlays: tuple[str, ...]


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


def read_json(path: Path, root: Path):
    shown = relative(path, root)
    if path.is_symlink() or not confined(path, root):
        return None, [
            Finding(
                "PM021",
                "identity",
                shown,
                "plugin manifest is a symlink or resolves outside the repository",
                "restore a regular manifest at the fixed plugin path",
            )
        ]
    if not path.is_file():
        return None, [
            Finding(
                "PM021",
                "structural",
                shown,
                "paired plugin manifest is absent",
                "restore both host manifests for the plugin",
            )
        ]
    try:
        payload = path.read_bytes()
    except OSError as exc:
        return None, [
            Finding(
                "PM021",
                "identity",
                shown,
                f"plugin manifest could not be read: {exc}",
                "restore a readable manifest inside the repository",
            )
        ]
    if len(payload) > MAX_JSON_BYTES:
        return None, [
            Finding(
                "PM022",
                "structural",
                shown,
                f"plugin manifest is {len(payload)} bytes; limit is {MAX_JSON_BYTES}",
                "reduce the manifest below the bounded-read limit",
            )
        ]
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, [
            Finding(
                "PM022",
                "structural",
                shown,
                f"plugin manifest is not valid UTF-8 JSON: {exc}",
                "restore a valid plugin manifest",
            )
        ]
    if not isinstance(document, dict):
        return None, [
            Finding(
                "PM022",
                "structural",
                shown,
                "plugin manifest root is not an object",
                "restore the manifest object",
            )
        ]
    return document, []


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
        documents = []
        for manifest in manifests:
            document, manifest_findings = read_json(manifest, root)
            findings.extend(manifest_findings)
            if document is not None:
                documents.append((manifest, document))
        for manifest, document in documents:
            if document.get("name") != entry.name:
                findings.append(
                    Finding(
                        "PM023",
                        "identity",
                        relative(manifest, root),
                        f"manifest name is {document.get('name')!r}; expected {entry.name!r}",
                        "make the manifest name match its fixed plugin directory",
                    )
                )
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


def walk_skill_files(skill_root: Path, root: Path):
    findings: list[Finding] = []
    found: list[Path] = []
    if skill_root.is_symlink() or not confined(skill_root, root):
        return found, [
            Finding(
                "PM025",
                "identity",
                relative(skill_root, root),
                "skill root is a symlink or resolves outside the repository",
                "restore a regular skills directory inside the plugin",
            )
        ]
    if not skill_root.is_dir():
        return found, findings
    for directory, names, files in os.walk(skill_root, followlinks=False):
        base = Path(directory)
        kept = []
        for name in sorted(names):
            child = base / name
            if child.is_symlink():
                findings.append(
                    Finding(
                        "PM025",
                        "identity",
                        relative(child, root),
                        "skill directory is a symlink",
                        "replace it with a regular directory inside the plugin",
                    )
                )
            else:
                kept.append(name)
        names[:] = kept
        if "SKILL.md" in files:
            candidate = base / "SKILL.md"
            if candidate.is_symlink() or not confined(candidate, root):
                findings.append(
                    Finding(
                        "PM025",
                        "identity",
                        relative(candidate, root),
                        "canonical skill is a symlink or resolves outside the repository",
                        "restore a regular canonical SKILL.md",
                    )
                )
            else:
                found.append(candidate)
    return sorted(found), findings


def ownership_for(skill_path: Path, plugin: Path, root: Path):
    evolution = skill_path.parent / "EVOLUTION.md"
    if evolution.is_symlink():
        return "unclassified", relative(evolution, root), [
            Finding(
                "PM025",
                "identity",
                relative(evolution, root),
                "evolution ownership marker is a symlink",
                "restore a regular evolution ledger",
            )
        ]
    if evolution.is_file():
        return "first-party", relative(evolution, root), []

    current = skill_path.parent
    partial = None
    while True:
        notice = current / "NOTICE.md"
        licence = current / "LICENSE"
        if notice.exists() or notice.is_symlink() or licence.exists() or licence.is_symlink():
            partial = current
            if (
                notice.is_file()
                and not notice.is_symlink()
                and licence.is_file()
                and not licence.is_symlink()
                and confined(notice, root)
                and confined(licence, root)
            ):
                loaded, read_findings = read_markdown(
                    notice, root, missing_code="PM026", unsafe_code="PM025"
                )
                if loaded is None:
                    return "unclassified", relative(notice, root), read_findings
                _, text = loaded
                required = (
                    "vendored verbatim",
                    "- Upstream:",
                    "- Release tag:",
                    "- Vendored:",
                )
                if all(item in text for item in required):
                    return "vendored", relative(notice, root), []
            break
        if current == plugin:
            break
        current = current.parent

    if partial is not None:
        return "unclassified", relative(partial, root), [
            Finding(
                "PM026",
                "structural",
                relative(skill_path, root),
                "vendored ownership binding is incomplete",
                "provide a regular licence and notice with upstream, release and vendored provenance",
            )
        ]
    return "unclassified", "", [
        Finding(
            "PM024",
            "identity",
            relative(skill_path, root),
            "canonical skill is neither first-party nor vendored",
            "add a governed evolution ledger or a complete vendored ownership binding",
        )
    ]


def skill_name(skill_path: Path, root: Path):
    loaded, findings = read_markdown(
        skill_path, root, missing_code="PM020", unsafe_code="PM025"
    )
    if loaded is None:
        return skill_path.parent.name, findings
    _, text = loaded
    match = re.search(r"(?m)^name:\s*([^\n]+)$", text)
    name = match.group(1).strip().strip("'\"") if match else ""
    if name != skill_path.parent.name:
        findings.append(
            Finding(
                "PM023",
                "identity",
                relative(skill_path, root),
                f"canonical name is {name!r}; expected {skill_path.parent.name!r}",
                "make frontmatter name match the canonical parent directory",
            )
        )
    return name or skill_path.parent.name, findings


def discover_inventory(root: Path):
    plugins, findings = discover_plugins(root)
    records: list[SkillRecord] = []
    for plugin in plugins:
        paths, walk_findings = walk_skill_files(plugin / "skills", root)
        findings.extend(walk_findings)
        for path in paths:
            name, name_findings = skill_name(path, root)
            findings.extend(name_findings)
            governance, ownership, ownership_findings = ownership_for(path, plugin, root)
            findings.extend(ownership_findings)
            records.append(
                SkillRecord(
                    name=name,
                    path=relative(path, root),
                    plugin=plugin.name,
                    governance=governance,
                    ownership=ownership,
                )
            )
    if not records:
        findings.append(
            Finding(
                "PM020",
                "structural",
                "plugins/*/skills",
                "canonical skill discovery returned an empty set",
                "restore at least one canonical SKILL.md; empty discovery never passes",
            )
        )

    router_root = root / ".agents" / "skills"
    routers: list[str] = []
    if router_root.exists() or router_root.is_symlink():
        if router_root.is_symlink() or not confined(router_root, root):
            findings.append(
                Finding(
                    "PM025",
                    "identity",
                    relative(router_root, root),
                    "portable router root is a symlink or resolves outside the repository",
                    "restore a regular .agents/skills directory",
                )
            )
        elif router_root.is_dir():
            for entry in sorted(router_root.iterdir(), key=lambda item: item.name):
                if entry.is_symlink() or not confined(entry, root):
                    findings.append(
                        Finding(
                            "PM025",
                            "identity",
                            relative(entry, root),
                            "portable router directory is a symlink or resolves outside the repository",
                            "restore a regular router directory inside .agents/skills",
                        )
                    )
                    continue
                if not entry.is_dir():
                    continue
                router = entry / "SKILL.md"
                if router.is_symlink() or not confined(router, root):
                    findings.append(
                        Finding(
                            "PM025",
                            "identity",
                            relative(router, root),
                            "portable router is a symlink or resolves outside the repository",
                            "restore a regular router SKILL.md",
                        )
                    )
                elif router.is_file():
                    routers.append(relative(router, root))
            if not routers:
                findings.append(
                    Finding(
                        "PM027",
                        "structural",
                        relative(router_root, root),
                        "portable router discovery returned an empty set",
                        "restore at least one portable router or remove the empty surface",
                    )
                )
    overlays = []
    for plugin in plugins:
        overlay = plugin / "PROMISES.md"
        if not (overlay.exists() or overlay.is_symlink()):
            continue
        if overlay.is_symlink() or not confined(overlay, root):
            findings.append(
                Finding(
                    "PM025",
                    "identity",
                    relative(overlay, root),
                    "promise overlay is a symlink or resolves outside the repository",
                    "restore a regular plugin-local PROMISES.md",
                )
            )
        elif overlay.is_file():
            overlays.append(relative(overlay, root))
        else:
            findings.append(
                Finding(
                    "PM025",
                    "structural",
                    relative(overlay, root),
                    "promise overlay is not a regular file",
                    "restore a regular plugin-local PROMISES.md",
                )
            )
    inventory = Inventory(
        plugins=tuple(relative(plugin, root) for plugin in plugins),
        skills=tuple(records),
        routers=tuple(routers),
        overlays=tuple(overlays),
    )
    return inventory, findings


def parse_contract(skill: SkillRecord, root: Path):
    path = root / skill.path
    loaded, findings = read_markdown(
        path, root, missing_code="PM020", unsafe_code="PM025"
    )
    if loaded is None:
        return [], findings
    _, text = loaded
    lines = text.splitlines()
    headings = [index for index, line in enumerate(lines) if line == "## Promise Machine contract"]
    if not headings:
        return [], findings
    if len(headings) != 1:
        findings.append(
            Finding(
                "PM030",
                "structural",
                skill.path,
                "Promise Machine contract heading must occur exactly once",
                "keep one contract section in the canonical skill",
            )
        )
        return [], findings
    start = headings[0] + 1
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    blocks = [index for index in range(start, end) if lines[index].startswith("### ")]
    if not blocks:
        findings.append(
            Finding(
                "PM031",
                "structural",
                skill.path,
                "contract section contains no promise declaration",
                "add at least one stable level-three promise block",
            )
        )
        return [], findings
    promises = []
    for offset, block_start in enumerate(blocks):
        block_end = blocks[offset + 1] if offset + 1 < len(blocks) else end
        promise_id = lines[block_start][4:].strip()
        if not PROMISE_ID.fullmatch(promise_id):
            findings.append(
                Finding(
                    "PM032",
                    "structural",
                    skill.path,
                    "promise id is not a stable lowercase hyphenated identifier",
                    "use a lowercase identifier made of letters, digits and hyphens",
                    promise_id=promise_id or None,
                )
            )
        fields: dict[str, list[str]] = {}
        for line in lines[block_start + 1 : block_end]:
            match = re.fullmatch(r"- \*\*([^*]+):\*\*\s*(.*)", line)
            if match is None:
                match = re.fullmatch(r"- ([^:]+):\s*(.*)", line)
            if match is not None:
                fields.setdefault(match.group(1).strip(), []).append(match.group(2).strip())
        unknown = sorted(set(fields) - set(REQUIRED_FIELDS))
        if unknown:
            findings.append(
                Finding(
                    "PM033",
                    "structural",
                    skill.path,
                    f"promise declaration contains unknown fields: {unknown!r}",
                    "use only the nine promise declaration fields",
                    promise_id=promise_id or None,
                )
            )
        for field in REQUIRED_FIELDS:
            values = fields.get(field, [])
            if len(values) != 1 or not values[0]:
                findings.append(
                    Finding(
                        "PM034",
                        "structural",
                        skill.path,
                        f"promise field must occur once and be non-empty: {field}",
                        f"provide exactly one non-empty {field} field",
                        promise_id=promise_id or None,
                    )
                )
        evidence_values = fields.get("Evidence classes", [])
        if len(evidence_values) == 1:
            classes = [
                item.strip().strip("`").split(":", 1)[0].strip()
                for item in re.split(r"[,;]", evidence_values[0])
                if item.strip()
            ]
            unsupported = sorted(set(classes) - SUPPORTED_EVIDENCE_CLASSES)
            if not classes or unsupported:
                findings.append(
                    Finding(
                        "PM036",
                        "structural",
                        skill.path,
                        f"unsupported evidence classes: {unsupported or ['<empty>']!r}",
                        "use a recognised base evidence class from the law",
                        promise_id=promise_id or None,
                    )
                )
        consequences = fields.get("Consequence", [])
        if len(consequences) == 1 and consequences[0] not in {"0", "1", "2", "3"}:
            findings.append(
                Finding(
                    "PM037",
                    "structural",
                    skill.path,
                    f"unsupported consequence level: {consequences[0]!r}",
                    "use consequence level 0, 1, 2 or 3",
                    promise_id=promise_id or None,
                )
            )
        exceptions = fields.get("Exceptions", [])
        if len(exceptions) == 1 and exceptions[0].lower() != "none":
            required = ("authority", "scope", "record", "expiry")
            absent = [
                item
                for item in required
                if re.search(
                    rf"(?:^|;)\s*{item}\s*(?::|=)\s*[^;\s].*?(?=;|$)",
                    exceptions[0],
                    re.IGNORECASE,
                )
                is None
            ]
            if absent:
                findings.append(
                    Finding(
                        "PM038",
                        "structural",
                        skill.path,
                        f"exception omits required attribution: {absent!r}",
                        "name authority, scope, record and expiry, or declare none",
                        promise_id=promise_id or None,
                    )
                )
        promises.append((promise_id, skill.path))
    return promises, findings


def check_structure(root: Path, inventory: Inventory):
    findings: list[Finding] = []
    promises: list[tuple[str, str]] = []
    for skill in inventory.skills:
        if skill.governance == "vendored":
            loaded, read_findings = read_markdown(
                root / skill.path,
                root,
                missing_code="PM020",
                unsafe_code="PM025",
            )
            findings.extend(read_findings)
            if loaded is not None and "## Promise Machine contract" in loaded[1].splitlines():
                findings.append(
                    Finding(
                        "PM029",
                        "structural",
                        skill.path,
                        "vendored instruction authors a Promise Machine contract",
                        "remove the local contract and bind the unchanged instruction through a first-party overlay",
                    )
                )
            continue
        if skill.governance != "first-party":
            continue
        parsed, parsed_findings = parse_contract(skill, root)
        promises.extend(parsed)
        findings.extend(parsed_findings)
    owners: dict[str, list[str]] = {}
    for promise_id, path in promises:
        owners.setdefault(promise_id, []).append(path)
    for promise_id, paths in sorted(owners.items()):
        if len(paths) > 1:
            for path in paths:
                findings.append(
                    Finding(
                        "PM035",
                        "identity",
                        path,
                        f"promise id is duplicated across canonical skills: {paths!r}",
                        "give every suite promise a unique stable id",
                        promise_id=promise_id,
                    )
                )
    return len(promises), findings


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


def report(
    command: str,
    root: Path,
    plugins: list[Path],
    findings: list[Finding],
    *,
    as_json: bool,
    written: int = 0,
    copies: int = 0,
    inventory: Inventory | None = None,
    promises: int = 0,
):
    findings = sorted(findings, key=lambda item: (item.path, item.code, item.message))
    counts = {
        "plugins": len(plugins),
        "copies": copies,
        "written": written,
        "findings": len(findings),
        "canonical_skills": len(inventory.skills) if inventory else 0,
        "governed_skills": (
            sum(item.governance == "first-party" for item in inventory.skills)
            if inventory
            else 0
        ),
        "vendored_skills": (
            sum(item.governance == "vendored" for item in inventory.skills)
            if inventory
            else 0
        ),
        "routers": len(inventory.routers) if inventory else 0,
        "overlays": len(inventory.overlays) if inventory else 0,
        "promises": promises,
    }
    document = {
        "contract": CONTRACT_ID,
        "command": command,
        "ok": not findings,
        "counts": counts,
        "findings": [asdict(item) for item in findings],
    }
    if inventory is not None:
        document["inventory"] = {
            "plugins": list(inventory.plugins),
            "skills": [asdict(item) for item in inventory.skills],
            "routers": list(inventory.routers),
            "overlays": list(inventory.overlays),
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
    elif command == "inventory":
        print(
            "clean: "
            + " ".join(
                f"{key}={counts[key]}"
                for key in (
                    "plugins",
                    "canonical_skills",
                    "governed_skills",
                    "vendored_skills",
                    "routers",
                    "overlays",
                )
            )
        )
    else:
        suffix = f"; wrote {written}" if command == "sync" else ""
        print(f"clean: {len(plugins)} plugin(s), {counts['copies']} copy/copies{suffix}")
    return 0 if not findings else 1


def repository_root(raw: str | None):
    candidate = Path(raw) if raw else Path(__file__).resolve().parents[1]
    if candidate.is_symlink():
        raise ValueError("repository root may not be a symlink")
    return candidate.resolve(strict=True)


def parse_only(raw: str):
    requested = tuple(item.strip() for item in raw.split(",") if item.strip())
    allowed = {"law", "copies", "inventory", "structure"}
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

    inventory_parser = subparsers.add_parser(
        "inventory", help="discover plugins, canonical skills, routers and overlays"
    )
    inventory_parser.add_argument("--check", action="store_true", help="validate discovery")
    inventory_parser.add_argument("--root", help=argparse.SUPPRESS)
    inventory_parser.add_argument("--json", action="store_true", help="emit canonical JSON")

    args = parser.parse_args(argv)
    try:
        root = repository_root(args.root)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.command == "inventory":
        inventory, findings = discover_inventory(root)
        plugins = [root / path for path in inventory.plugins]
        return report(
            "inventory",
            root,
            plugins,
            findings,
            as_json=args.json,
            inventory=inventory,
        )

    if args.command == "check":
        try:
            only = parse_only(args.only)
        except ValueError as exc:
            parser.error(str(exc))
        law = None
        findings: list[Finding] = []
        plugins: list[Path] = []
        inventory = None
        promises = 0
        if "law" in only or "copies" in only:
            law, law_findings = check_law(root)
            findings.extend(law_findings)
        if "copies" in only:
            plugins, discovery_findings = discover_plugins(root)
            findings.extend(discovery_findings)
            findings.extend(check_copies(root, law, plugins))
        if "inventory" in only or "structure" in only:
            inventory, inventory_findings = discover_inventory(root)
            findings.extend(inventory_findings)
            plugins = [root / path for path in inventory.plugins]
        if "structure" in only and inventory is not None:
            promises, structure_findings = check_structure(root, inventory)
            findings.extend(structure_findings)
        return report(
            "check",
            root,
            plugins,
            findings,
            as_json=args.json,
            copies=len(plugins) if "copies" in only else 0,
            inventory=inventory,
            promises=promises,
        )

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
    return report(
        "sync",
        root,
        plugins,
        findings,
        as_json=args.json,
        written=written,
        copies=len(plugins),
    )


if __name__ == "__main__":
    raise SystemExit(main())
