#!/usr/bin/env python3
"""Fail-closed Foundry gas-optimisation verification harness."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA = "hermes/v1"
SKILL_NAME = "hermes"
OPTIMISATION_CLASSES = (
    "assembly",
    "calldata-memory",
    "constants-immutables",
    "control-flow",
    "custom-errors",
    "external-call-reduction",
    "event-packing",
    "hashing-encoding",
    "loop-arithmetic",
    "storage-load-caching",
    "storage-packing",
    "unchecked-arithmetic",
)
SNAPSHOT_RE = re.compile(r"^(?P<name>.+) \(gas: (?P<gas>[0-9]+)\)$")
INVARIANT_SNAPSHOT_RE = re.compile(
    r"^(?P<name>.+) \(runs: (?P<runs>[0-9]+), calls: (?P<calls>[0-9]+), reverts: (?P<reverts>[0-9]+)\)$"
)
FUZZ_SNAPSHOT_RE = re.compile(
    r"^(?P<name>.+) \(runs: (?P<runs>[0-9]+), μ: (?P<mean>[0-9]+), ~: (?P<median>[0-9]+)\)$"
)
LABEL_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
# solc appends compilation-local AST IDs to user-defined type references in the
# storage-layout JSON. Those IDs are not part of storage semantics and can move
# after an unrelated source edit.
SOLC_TYPE_AST_ID_RE = re.compile(r"(?<=\))\d+(?=(?:_storage)?(?:\)|$))")


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass
class SnapshotMeasurements:
    gas: dict[str, int]
    fuzz: dict[str, dict[str, int]]
    invariants: dict[str, dict[str, int]]


class GateFailure(RuntimeError):
    def __init__(self, gate: int, message: str, exit_code: int):
        super().__init__(message)
        self.gate = gate
        self.exit_code = exit_code


class SingleValueAction(argparse.Action):
    """Reject duplicate scalar flags instead of silently taking the last value."""

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[override]
        if getattr(namespace, self.dest, None) is not None:
            parser.error(f"{option_string} must be supplied exactly once")
        setattr(namespace, self.dest, values)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def quote_command(command: Sequence[str]) -> str:
    import shlex

    return " ".join(shlex.quote(part) for part in command)


def run_command(
    command: Sequence[str],
    cwd: Path,
    log_path: Path,
    env: dict[str, str] | None = None,
    echo: bool = True,
) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    log = [f"$ {quote_command(command)}\n", completed.stdout]
    if completed.stderr:
        log.extend(["\n[stderr]\n", completed.stderr])
    log.append(f"\n[exit {completed.returncode}]\n")
    write_text(log_path, "".join(log))
    if echo and completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if echo and completed.stderr:
        print(completed.stderr, file=sys.stderr, end="" if completed.stderr.endswith("\n") else "\n")
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def require_success(result: CommandResult, gate: int, description: str, exit_code: int) -> None:
    if result.returncode != 0:
        raise GateFailure(gate, f"{description} exited {result.returncode}", exit_code)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def default_evidence_dir(repo: Path) -> Path:
    codex_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    return codex_root / "hermes-runs" / f"{repo.name}-{stamp}-{uuid.uuid4().hex[:8]}"


def prepare_evidence_dir(repo: Path, requested: str | None) -> Path:
    run_dir = Path(requested).expanduser().resolve() if requested else default_evidence_dir(repo).resolve()
    if is_within(run_dir, repo):
        raise GateFailure(1, "evidence directory must be outside the target repository", 10)
    if run_dir.exists() and any(run_dir.iterdir()):
        raise GateFailure(1, f"evidence directory is not empty: {run_dir}", 10)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def git(repo: Path, arguments: Sequence[str], log_path: Path) -> CommandResult:
    return run_command(["git", *arguments], repo, log_path, echo=False)


def require_git_repository(repo: Path, log_path: Path, gate: int = 1) -> str:
    result = git(repo, ["rev-parse", "HEAD"], log_path)
    require_success(result, gate, "git rev-parse HEAD", 10 if gate == 1 else 20)
    return result.stdout.strip()


def canonical_json(raw: str, description: str, gate: int, exit_code: int) -> tuple[Any, str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GateFailure(gate, f"{description} did not return valid JSON: {exc}", exit_code) from exc
    canonical = json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"
    return value, canonical


def canonical_storage_layout(value: Any, gate: int, exit_code: int) -> Any:
    """Remove solc's non-semantic AST IDs while preserving layout structure.

    `forge inspect storageLayout` represents user-defined types by generated
    names such as `t_contract(Token)1234`. The numeric suffix changes with the
    compiler AST numbering, even when every slot, offset, member, and type
    shape is unchanged. The raw output remains in the command log; this value
    is solely the fail-closed comparison form.
    """

    def normalise(node: Any) -> Any:
        if isinstance(node, list):
            return [normalise(item) for item in node]
        if isinstance(node, dict):
            result: dict[str, Any] = {}
            for key, item in node.items():
                # This is a compiler AST reference, not a storage property.
                if key == "astId":
                    continue
                normalised_key = SOLC_TYPE_AST_ID_RE.sub("", key)
                if normalised_key in result:
                    raise ValueError(f"normalising solc type IDs collides at key {normalised_key!r}")
                result[normalised_key] = normalise(item)
            return result
        if isinstance(node, str):
            return SOLC_TYPE_AST_ID_RE.sub("", node)
        return node

    try:
        return normalise(value)
    except ValueError as exc:
        raise GateFailure(gate, f"could not canonicalise storage layout: {exc}", exit_code) from exc


def parse_protected_contract(raw: str) -> dict[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("expected LABEL=PATH:CONTRACT")
    label, identifier = raw.split("=", 1)
    if not label or not LABEL_RE.fullmatch(label):
        raise argparse.ArgumentTypeError("contract label may contain only letters, digits, dot, dash, underscore")
    if not identifier or ":" not in identifier:
        raise argparse.ArgumentTypeError("contract identifier must be PATH:CONTRACT")
    return {"label": label, "identifier": identifier}


def list_solidity_files(repo: Path, log_path: Path, gate: int, exit_code: int) -> list[str]:
    result = git(repo, ["ls-files", "-co", "--exclude-standard", "-z", "--", "*.sol"], log_path)
    require_success(result, gate, "git ls-files for Solidity sources", exit_code)
    paths = sorted(item for item in result.stdout.split("\0") if item)
    if not paths:
        raise GateFailure(gate, "no tracked or unignored Solidity files found", exit_code)
    unsafe = [path for path in paths if Path(path).is_absolute() or ".." in Path(path).parts]
    if unsafe:
        raise GateFailure(gate, f"unsafe Solidity paths returned by git: {unsafe}", exit_code)
    return paths


def snapshot_sources(repo: Path, run_dir: Path) -> dict[str, str]:
    paths = list_solidity_files(repo, run_dir / "logs" / "gate1.git-solidity-files.log", 1, 10)
    snapshot_dir = run_dir / "baseline-sources"
    manifest: dict[str, str] = {}
    for relative in paths:
        source = repo / relative
        if not source.is_file():
            raise GateFailure(1, f"Solidity source is not a regular file: {relative}", 10)
        destination = snapshot_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        manifest[relative] = sha256_file(destination)
    write_json(run_dir / "baseline-source-manifest.json", manifest)
    return manifest


def source_diff(repo: Path, run_dir: Path, baseline_manifest: dict[str, str]) -> tuple[list[str], str, set[str]]:
    current_paths = list_solidity_files(repo, run_dir / "logs" / "gate2.git-solidity-files.log", 2, 20)
    if set(current_paths) != set(baseline_manifest):
        added = sorted(set(current_paths) - set(baseline_manifest))
        removed = sorted(set(baseline_manifest) - set(current_paths))
        raise GateFailure(2, f"Solidity file set changed; added={added}, removed={removed}", 20)

    changed: list[str] = []
    sections: list[str] = []
    tokens: set[str] = set()
    for relative in current_paths:
        current = repo / relative
        if sha256_file(current) == baseline_manifest[relative]:
            continue
        changed.append(relative)
        before_path = run_dir / "baseline-sources" / relative
        before = before_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        after = current.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        lines = list(
            difflib.unified_diff(
                before,
                after,
                fromfile=f"baseline/{relative}",
                tofile=f"candidate/{relative}",
            )
        )
        sections.extend(lines)
        for line in lines:
            if not line.startswith("+") or line.startswith("+++"):
                continue
            if re.search(r"\bunchecked\b", line):
                tokens.add("unchecked")
            if re.search(r"\bassembly\b", line):
                tokens.add("assembly")

    diff_text = "".join(sections)
    write_text(run_dir / "candidate.solidity.diff", diff_text)
    if not changed:
        raise GateFailure(2, "candidate contains no Solidity source change", 20)
    changed_tests = [
        path
        for path in changed
        if path.endswith(".t.sol") or any(part.lower() in {"test", "tests"} for part in Path(path).parts)
    ]
    if changed_tests:
        raise GateFailure(2, f"candidate changes test sources: {changed_tests}; prepare tests in a separate loop", 20)
    return changed, diff_text, tokens


def inspect_layout(
    repo: Path,
    run_dir: Path,
    contract: dict[str, str],
    suffix: str,
    gate: int,
    exit_code: int,
) -> tuple[Path, Any]:
    label = contract["label"]
    result = run_command(
        ["forge", "inspect", contract["identifier"], "storageLayout", "--json", "--force"],
        repo,
        run_dir / "logs" / f"gate{gate}.layout.{label}.{suffix}.log",
        echo=False,
    )
    require_success(result, gate, f"storage layout inspection for {contract['identifier']}", exit_code)
    raw_value, raw_canonical = canonical_json(result.stdout, f"storage layout for {contract['identifier']}", gate, exit_code)
    if not isinstance(raw_value, dict) or not raw_value:
        raise GateFailure(gate, f"empty storage layout for {contract['identifier']}", exit_code)
    value = canonical_storage_layout(raw_value, gate, exit_code)
    canonical = json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"
    path = run_dir / "storage-layout" / f"{label}.{suffix}.json"
    write_text(run_dir / "storage-layout" / f"{label}.{suffix}.raw.json", raw_canonical)
    write_text(path, canonical)
    return path, value


def inspect_methods(
    repo: Path,
    run_dir: Path,
    contract: dict[str, str],
    suffix: str,
    gate: int,
    exit_code: int,
) -> tuple[Path, Any]:
    label = contract["label"]
    result = run_command(
        ["forge", "inspect", contract["identifier"], "methodIdentifiers", "--json", "--force"],
        repo,
        run_dir / "logs" / f"gate{gate}.methods.{label}.{suffix}.log",
        echo=False,
    )
    require_success(result, gate, f"method identifier inspection for {contract['identifier']}", exit_code)
    value, canonical = canonical_json(result.stdout, f"method identifiers for {contract['identifier']}", gate, exit_code)
    if not isinstance(value, dict):
        raise GateFailure(gate, f"invalid method identifier map for {contract['identifier']}", exit_code)
    path = run_dir / "method-identifiers" / f"{label}.{suffix}.json"
    write_text(path, canonical)
    return path, value


def forge_test_arguments(seed: str | None, excluded_paths: Sequence[str]) -> list[str]:
    arguments: list[str] = []
    for path in excluded_paths:
        arguments.extend(["--no-match-path", path])
    if seed:
        arguments.extend(["--fuzz-seed", seed])
    return arguments


def parse_gas_snapshot(path: Path, gate: int = 3) -> SnapshotMeasurements:
    gas: dict[str, int] = {}
    fuzz: dict[str, dict[str, int]] = {}
    invariants: dict[str, dict[str, int]] = {}
    if not path.is_file() or path.stat().st_size == 0:
        raise GateFailure(gate, f"missing or empty gas snapshot: {path}", 30 if gate == 3 else 10)
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        gas_match = SNAPSHOT_RE.fullmatch(stripped)
        if gas_match:
            name = gas_match.group("name")
            if name in gas:
                raise GateFailure(gate, f"duplicate gas snapshot measurement: {name}", 30 if gate == 3 else 10)
            gas[name] = int(gas_match.group("gas"))
            continue
        invariant_match = INVARIANT_SNAPSHOT_RE.fullmatch(stripped)
        if invariant_match:
            name = invariant_match.group("name")
            if name in invariants:
                raise GateFailure(
                    gate, f"duplicate invariant snapshot measurement: {name}", 30 if gate == 3 else 10
                )
            invariants[name] = {
                "runs": int(invariant_match.group("runs")),
                "calls": int(invariant_match.group("calls")),
                "reverts": int(invariant_match.group("reverts")),
            }
            continue
        fuzz_match = FUZZ_SNAPSHOT_RE.fullmatch(stripped)
        if fuzz_match:
            name = fuzz_match.group("name")
            if name in fuzz:
                raise GateFailure(gate, f"duplicate fuzz snapshot measurement: {name}", 30 if gate == 3 else 10)
            fuzz[name] = {
                "runs": int(fuzz_match.group("runs")),
                "mean": int(fuzz_match.group("mean")),
                "median": int(fuzz_match.group("median")),
            }
            continue
        raise GateFailure(gate, f"unrecognised gas snapshot line {line_number}: {line}", 30 if gate == 3 else 10)
    if not gas and not fuzz and not invariants:
        raise GateFailure(gate, "gas snapshot contains no measurements", 30 if gate == 3 else 10)
    return SnapshotMeasurements(gas=gas, fuzz=fuzz, invariants=invariants)


def compare_gas(
    baseline: SnapshotMeasurements, candidate: SnapshotMeasurements, target_patterns: Sequence[str]
) -> dict[str, Any]:
    if set(baseline.gas) != set(candidate.gas):
        missing = sorted(set(baseline.gas) - set(candidate.gas))
        added = sorted(set(candidate.gas) - set(baseline.gas))
        raise GateFailure(3, f"gas snapshot measurement set changed; missing={missing}, added={added}", 30)
    if set(baseline.invariants) != set(candidate.invariants):
        missing = sorted(set(baseline.invariants) - set(candidate.invariants))
        added = sorted(set(candidate.invariants) - set(baseline.invariants))
        raise GateFailure(3, f"invariant snapshot measurement set changed; missing={missing}, added={added}", 30)

    changed_invariants = sorted(
        name for name in baseline.invariants if baseline.invariants[name] != candidate.invariants[name]
    )
    if changed_invariants:
        raise GateFailure(3, f"invariant snapshot changed in: {changed_invariants}", 30)
    if set(baseline.fuzz) != set(candidate.fuzz):
        missing = sorted(set(baseline.fuzz) - set(candidate.fuzz))
        added = sorted(set(candidate.fuzz) - set(baseline.fuzz))
        raise GateFailure(3, f"fuzz snapshot measurement set changed; missing={missing}, added={added}", 30)
    changed_fuzz_runs = sorted(
        name for name in baseline.fuzz if baseline.fuzz[name]["runs"] != candidate.fuzz[name]["runs"]
    )
    if changed_fuzz_runs:
        raise GateFailure(3, f"fuzz snapshot run count changed in: {changed_fuzz_runs}", 30)

    rows: list[dict[str, Any]] = []
    regressions: list[str] = []
    improvements: set[str] = set()
    for name in sorted(baseline.gas):
        before = baseline.gas[name]
        after = candidate.gas[name]
        delta = after - before
        percentage = (delta / before * 100.0) if before else None
        rows.append(
            {
                "measurement": name,
                "baseline": before,
                "candidate": after,
                "delta": delta,
                "percentage": percentage,
            }
        )
        if delta > 0:
            regressions.append(name)
        elif delta < 0:
            improvements.add(name)
    if regressions:
        raise GateFailure(3, f"gas regression detected in: {regressions}", 30)
    if not improvements:
        raise GateFailure(3, "candidate has no quantified gas reduction", 30)

    target_results: list[dict[str, Any]] = []
    for pattern_text in target_patterns:
        try:
            pattern = re.compile(pattern_text)
        except re.error as exc:
            raise GateFailure(3, f"invalid gas target regex {pattern_text!r}: {exc}", 30) from exc
        matched = sorted(name for name in baseline.gas if pattern.search(name))
        if not matched:
            raise GateFailure(3, f"gas target matched no measurements: {pattern_text}", 30)
        improved = sorted(name for name in matched if name in improvements)
        if not improved:
            raise GateFailure(3, f"gas target has no improved measurement: {pattern_text}", 30)
        target_results.append({"pattern": pattern_text, "matched": matched, "improved": improved})
    invariant_rows = [
        {"measurement": name, **baseline.invariants[name], "status": "identical"}
        for name in sorted(baseline.invariants)
    ]
    fuzz_statistics = []
    for name in sorted(baseline.fuzz):
        fuzz_statistics.append(
            {
                "measurement": name,
                "runs": baseline.fuzz[name]["runs"],
                "baseline_mean": baseline.fuzz[name]["mean"],
                "candidate_mean": candidate.fuzz[name]["mean"],
                "mean_delta": candidate.fuzz[name]["mean"] - baseline.fuzz[name]["mean"],
                "baseline_median": baseline.fuzz[name]["median"],
                "candidate_median": candidate.fuzz[name]["median"],
                "median_delta": candidate.fuzz[name]["median"] - baseline.fuzz[name]["median"],
                "status": "informational_not_comparable",
            }
        )
    return {
        "measurements": rows,
        "fuzz_statistics": fuzz_statistics,
        "invariants": invariant_rows,
        "targets": target_results,
    }


def artifact_hashes(run_dir: Path, paths: Iterable[Path]) -> dict[str, str]:
    return {str(path.relative_to(run_dir)): sha256_file(path) for path in sorted(paths)}


def verify_artifact_hashes(run_dir: Path, expected: dict[str, str]) -> None:
    for relative, digest in expected.items():
        path = run_dir / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise GateFailure(2, f"baseline evidence changed or is missing: {relative}", 20)


def mark_failure(run_dir: Path | None, state: dict[str, Any] | None, failure: GateFailure) -> None:
    if run_dir is None:
        return
    result = {
        "schema": SCHEMA,
        "skill": SKILL_NAME,
        "status": "rejected",
        "failed_gate": failure.gate,
        "exit_code": failure.exit_code,
        "reason": str(failure),
        "finished_at": utc_now(),
    }
    write_json(run_dir / "result.json", result)
    if state is not None:
        state["status"] = "rejected"
        state["result"] = result
        write_json(run_dir / "state.json", state)


def baseline_command(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    run_dir: Path | None = None
    state: dict[str, Any] | None = None
    try:
        if not repo.is_dir():
            raise GateFailure(1, f"repository does not exist: {repo}", 10)
        run_dir = prepare_evidence_dir(repo, args.evidence_dir)
        protected = args.protected_contract or []
        recorded = args.layout_contract or []
        layout_contracts = [
            *[{**contract, "protected": True} for contract in protected],
            *[{**contract, "protected": False} for contract in recorded],
        ]
        state = {
            "schema": SCHEMA,
            "skill": SKILL_NAME,
            "run_id": run_dir.name,
            "repo": str(repo),
            "run_dir": str(run_dir),
            "status": "baseline_running",
            "created_at": utc_now(),
            "protected_contracts": protected,
            "layout_contracts": layout_contracts,
            "asserted_no_protected_contracts": bool(args.assert_no_protected_contracts),
            "execution": {
                "fuzz_seed": args.fuzz_seed,
                "no_match_paths": args.no_match_path,
            },
            "gates": [],
        }
        write_json(run_dir / "state.json", state)

        git_head = require_git_repository(repo, run_dir / "logs" / "gate1.git-head.log")
        clean = git(
            repo,
            ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
            run_dir / "logs" / "gate1.git-clean.log",
        )
        require_success(clean, 1, "git status", 10)
        if clean.stdout:
            raise GateFailure(1, "baseline working tree is not clean", 10)
        version = run_command(
            ["forge", "--version"], repo, run_dir / "logs" / "gate1.forge-version.log", echo=False
        )
        require_success(version, 1, "forge --version", 10)
        config = run_command(
            ["forge", "config", "--json"], repo, run_dir / "logs" / "gate1.forge-config.log", echo=False
        )
        require_success(config, 1, "forge config --json", 10)
        _, canonical_config = canonical_json(config.stdout, "forge config", 1, 10)
        config_path = run_dir / "baseline.forge-config.json"
        write_text(config_path, canonical_config)
        version_path = run_dir / "baseline.forge-version.txt"
        write_text(version_path, version.stdout)

        test_arguments = forge_test_arguments(args.fuzz_seed, args.no_match_path)
        snapshot = run_command(
            ["forge", "snapshot", *test_arguments], repo, run_dir / "logs" / "gate1.forge-snapshot.log"
        )
        require_success(snapshot, 1, "forge snapshot", 10)
        project_snapshot = repo / ".gas-snapshot"
        parse_gas_snapshot(project_snapshot, gate=1)
        baseline_snapshot = run_dir / "baseline.gas-snapshot"
        shutil.copy2(project_snapshot, baseline_snapshot)

        tests = run_command(["forge", "test", *test_arguments], repo, run_dir / "logs" / "gate1.forge-test.log")
        require_success(tests, 1, "forge test", 10)

        layout_paths: list[Path] = []
        method_paths: list[Path] = []
        for contract in layout_contracts:
            path, _ = inspect_layout(repo, run_dir, contract, "before", 1, 10)
            layout_paths.append(path)
            method_path, _ = inspect_methods(repo, run_dir, contract, "before", 1, 10)
            method_paths.append(method_path)

        source_manifest = snapshot_sources(repo, run_dir)
        status = git(repo, ["status", "--porcelain=v1", "-z"], run_dir / "logs" / "gate1.git-status.log")
        require_success(status, 1, "git status", 10)
        status_path = run_dir / "baseline.git-status.bin"
        status_path.write_bytes(status.stdout.encode("utf-8"))

        protected_paths = [
            baseline_snapshot,
            config_path,
            version_path,
            status_path,
            run_dir / "baseline-source-manifest.json",
            *layout_paths,
            *method_paths,
        ]
        hashes = artifact_hashes(run_dir, protected_paths)
        state.update(
            {
                "status": "baseline_ready",
                "baseline": {
                    "git_head": git_head,
                    "forge_version_sha256": sha256_bytes(version.stdout.encode()),
                    "forge_config_sha256": sha256_bytes(canonical_config.encode()),
                    "gas_snapshot": str(baseline_snapshot.relative_to(run_dir)),
                    "source_manifest": source_manifest,
                    "artifact_hashes": hashes,
                },
                "gates": [
                    {
                        "id": 1,
                        "name": "baseline",
                        "status": "passed",
                        "commands": [
                            quote_command(["forge", "snapshot", *test_arguments]),
                            quote_command(["forge", "test", *test_arguments]),
                        ],
                        "passed_at": utc_now(),
                    }
                ],
            }
        )
        write_json(run_dir / "state.json", state)
        write_json(
            run_dir / "result.json",
            {
                "schema": SCHEMA,
                "skill": SKILL_NAME,
                "status": "baseline_ready",
                "exit_code": 0,
                "run_dir": str(run_dir),
            },
        )
        print(json.dumps({"status": "baseline_ready", "run_dir": str(run_dir)}))
        return 0
    except GateFailure as failure:
        mark_failure(run_dir, state, failure)
        print(f"Hermes rejected at Gate {failure.gate}: {failure}", file=sys.stderr)
        return failure.exit_code


def verify_command(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    state: dict[str, Any] | None = None
    try:
        state_path = run_dir / "state.json"
        if not state_path.is_file():
            raise GateFailure(2, f"missing run state: {state_path}", 20)
        state = read_json(state_path)
        if state.get("schema") != SCHEMA or state.get("status") != "baseline_ready":
            raise GateFailure(2, f"run is not baseline_ready: {state.get('status')}", 20)
        repo = Path(state["repo"]).resolve()
        verify_artifact_hashes(run_dir, state["baseline"]["artifact_hashes"])

        current_head = require_git_repository(repo, run_dir / "logs" / "gate2.git-head.log", gate=2)
        if current_head != state["baseline"]["git_head"]:
            raise GateFailure(2, "git HEAD changed after baseline", 20)
        version = run_command(
            ["forge", "--version"], repo, run_dir / "logs" / "gate2.forge-version.log", echo=False
        )
        require_success(version, 2, "forge --version", 20)
        if sha256_bytes(version.stdout.encode()) != state["baseline"]["forge_version_sha256"]:
            raise GateFailure(2, "Forge version changed after baseline", 20)
        config = run_command(
            ["forge", "config", "--json"], repo, run_dir / "logs" / "gate2.forge-config.log", echo=False
        )
        require_success(config, 2, "forge config --json", 20)
        _, canonical_config = canonical_json(config.stdout, "forge config", 2, 20)
        if sha256_bytes(canonical_config.encode()) != state["baseline"]["forge_config_sha256"]:
            raise GateFailure(2, "Foundry configuration changed after baseline", 20)

        changed_files, _, added_tokens = source_diff(repo, run_dir, state["baseline"]["source_manifest"])
        optimisation_class = args.optimisation_class
        if "unchecked" in added_tokens and optimisation_class != "unchecked-arithmetic":
            raise GateFailure(2, "candidate adds unchecked code outside the unchecked-arithmetic class", 20)
        if "assembly" in added_tokens and optimisation_class != "assembly":
            raise GateFailure(2, "candidate adds assembly outside the assembly class", 20)
        if {"unchecked", "assembly"}.issubset(added_tokens):
            raise GateFailure(2, "candidate combines unchecked arithmetic and assembly", 20)
        if args.no_sensitive_unchecked and ("unchecked" in added_tokens or optimisation_class == "unchecked-arithmetic"):
            if not args.non_sensitive_rationale or len(args.non_sensitive_rationale.strip()) < 20:
                raise GateFailure(2, "non-sensitive unchecked classification requires a substantive rationale", 20)

        state["candidate"] = {
            "optimisation_class": optimisation_class,
            "single_class_attested": True,
            "changed_files": changed_files,
            "added_sensitive_tokens": sorted(added_tokens),
            "sensitive_unchecked": bool(args.sensitive_unchecked),
            "non_sensitive_rationale": args.non_sensitive_rationale,
        }
        state["gates"].append(
            {
                "id": 2,
                "name": "single_optimisation_class",
                "status": "passed",
                "optimisation_class": optimisation_class,
                "changed_files": changed_files,
                "passed_at": utc_now(),
            }
        )
        write_json(state_path, state)

        execution = state["execution"]
        test_arguments = forge_test_arguments(execution["fuzz_seed"], execution["no_match_paths"])
        baseline_snapshot_path = run_dir / state["baseline"]["gas_snapshot"]
        gas_diff = run_command(
            ["forge", "snapshot", "--diff", str(baseline_snapshot_path), *test_arguments],
            repo,
            run_dir / "logs" / "gate3.forge-snapshot-diff.log",
        )
        require_success(gas_diff, 3, "forge snapshot --diff", 30)
        candidate_snapshot_path = run_dir / "candidate.gas-snapshot"
        candidate_snapshot = run_command(
            ["forge", "snapshot", "--snap", str(candidate_snapshot_path), *test_arguments],
            repo,
            run_dir / "logs" / "gate3.candidate-snapshot.log",
        )
        require_success(candidate_snapshot, 3, "candidate gas snapshot capture", 30)
        gas = compare_gas(
            parse_gas_snapshot(baseline_snapshot_path),
            parse_gas_snapshot(candidate_snapshot_path),
            args.gas_target,
        )
        gas_report = run_command(
            ["forge", "test", "--gas-report", *test_arguments],
            repo,
            run_dir / "logs" / "gate3.forge-gas-report.log",
        )
        require_success(gas_report, 3, "forge test --gas-report", 30)
        gas_path = run_dir / "gas-comparison.json"
        write_json(gas_path, gas)
        state["gates"].append(
            {
                "id": 3,
                "name": "quantified_gas_saving",
                "status": "passed",
                "commands": [
                    quote_command(["forge", "snapshot", "--diff", str(baseline_snapshot_path), *test_arguments]),
                    quote_command(["forge", "test", "--gas-report", *test_arguments]),
                ],
                "evidence": str(gas_path.relative_to(run_dir)),
                "passed_at": utc_now(),
            }
        )
        write_json(state_path, state)

        full_tests = run_command(
            ["forge", "test", *test_arguments], repo, run_dir / "logs" / "gate4.forge-test-pinned.log"
        )
        require_success(full_tests, 4, "full forge test re-run", 40)
        unpinned_arguments = forge_test_arguments(None, execution["no_match_paths"])
        unpinned_tests = run_command(
            ["forge", "test", *unpinned_arguments],
            repo,
            run_dir / "logs" / "gate4.forge-test-unpinned.log",
        )
        require_success(unpinned_tests, 4, "unpinned full forge test re-run", 40)
        state["gates"].append(
            {
                "id": 4,
                "name": "full_test_rerun",
                "status": "passed",
                "commands": [
                    quote_command(["forge", "test", *test_arguments]),
                    quote_command(["forge", "test", *unpinned_arguments]),
                ],
                "passed_at": utc_now(),
            }
        )
        write_json(state_path, state)

        layouts: list[dict[str, Any]] = []
        methods: list[dict[str, Any]] = []
        permitted_layout_change_seen = False
        for contract in state["layout_contracts"]:
            after_path, _ = inspect_layout(repo, run_dir, contract, "after", 5, 50)
            before_path = run_dir / "storage-layout" / f"{contract['label']}.before.json"
            before = before_path.read_bytes()
            after = after_path.read_bytes()
            diff_path = run_dir / "storage-layout" / f"{contract['label']}.diff"
            layout_changed = before != after
            if layout_changed:
                before_lines = before.decode().splitlines(keepends=True)
                after_lines = after.decode().splitlines(keepends=True)
                write_text(
                    diff_path,
                    "".join(
                        difflib.unified_diff(
                            before_lines,
                            after_lines,
                            fromfile=f"{contract['label']}.before.json",
                            tofile=f"{contract['label']}.after.json",
                        )
                    ),
                )
                if contract["protected"]:
                    raise GateFailure(5, f"protected storage layout changed: {contract['identifier']}", 50)
                if not args.allow_unprotected_layout_change:
                    raise GateFailure(5, f"undeclared storage layout change: {contract['identifier']}", 50)
                if optimisation_class not in {"storage-packing", "constants-immutables"}:
                    raise GateFailure(
                        5,
                        f"storage layout changed outside a layout-changing optimisation class: {contract['identifier']}",
                        50,
                    )
                permitted_layout_change_seen = True
            else:
                write_text(diff_path, "")
            layouts.append(
                {
                    **contract,
                    "status": "changed_permitted" if layout_changed else "identical",
                    "before_sha256": sha256_bytes(before),
                    "after_sha256": sha256_bytes(after),
                    "diff": str(diff_path.relative_to(run_dir)),
                    "rationale": args.layout_change_rationale if layout_changed else None,
                }
            )
            methods_after_path, _ = inspect_methods(repo, run_dir, contract, "after", 5, 50)
            methods_before_path = run_dir / "method-identifiers" / f"{contract['label']}.before.json"
            methods_before = methods_before_path.read_bytes()
            methods_after = methods_after_path.read_bytes()
            methods_diff_path = run_dir / "method-identifiers" / f"{contract['label']}.diff"
            if methods_before != methods_after:
                write_text(
                    methods_diff_path,
                    "".join(
                        difflib.unified_diff(
                            methods_before.decode().splitlines(keepends=True),
                            methods_after.decode().splitlines(keepends=True),
                            fromfile=f"{contract['label']}.before.json",
                            tofile=f"{contract['label']}.after.json",
                        )
                    ),
                )
                raise GateFailure(5, f"public method identifiers changed: {contract['identifier']}", 50)
            write_text(methods_diff_path, "")
            methods.append(
                {
                    **contract,
                    "status": "identical",
                    "before_sha256": sha256_bytes(methods_before),
                    "after_sha256": sha256_bytes(methods_after),
                    "diff": str(methods_diff_path.relative_to(run_dir)),
                }
            )
        if args.allow_unprotected_layout_change and not permitted_layout_change_seen:
            raise GateFailure(5, "declared unprotected layout change did not occur", 50)
        state["gates"].append(
            {
                "id": 5,
                "name": "protected_storage_layout",
                "status": "passed",
                "contracts": layouts,
                "method_identifiers": methods,
                "asserted_no_protected_contracts": state["asserted_no_protected_contracts"],
                "passed_at": utc_now(),
            }
        )
        write_json(state_path, state)

        sensitive_evidence: dict[str, Any]
        if args.sensitive_unchecked:
            if not args.property_proof or len(args.property_proof.strip()) < 40:
                raise GateFailure(6, "state-sensitive unchecked verification requires a substantive property proof description", 60)
            targeted_command = [
                "forge",
                "test",
                "--match-path",
                args.targeted_match_path,
                "--match-test",
                args.targeted_match_test,
            ]
            targeted_command.extend(["--fuzz-seed", execution["fuzz_seed"]])
            targeted = run_command(
                targeted_command,
                repo,
                run_dir / "logs" / "gate6.targeted-property-test.log",
            )
            require_success(targeted, 6, "targeted state-sensitive differential/property test", 60)
            sensitive_evidence = {
                "applicable": True,
                "command": quote_command(targeted_command),
                "property_proof": args.property_proof,
                "status": "passed",
            }
        else:
            sensitive_evidence = {
                "applicable": False,
                "reason": args.non_sensitive_rationale or "candidate does not introduce, expand, or rely on state-sensitive unchecked arithmetic",
                "status": "not_applicable",
            }
        state["gates"].append(
            {
                "id": 6,
                "name": "sensitive_unchecked_property",
                **sensitive_evidence,
                "passed_at": utc_now(),
            }
        )

        result = {
            "schema": SCHEMA,
            "skill": SKILL_NAME,
            "status": "accepted",
            "exit_code": 0,
            "run_id": state["run_id"],
            "repo": str(repo),
            "optimisation_class": optimisation_class,
            "changed_files": changed_files,
            "gates": state["gates"],
            "gas": gas,
            "storage_layouts": layouts,
            "method_identifiers": methods,
            "sensitive_unchecked": sensitive_evidence,
            "candidate_snapshot": str(candidate_snapshot_path.relative_to(run_dir)),
            "candidate_snapshot_sha256": sha256_file(candidate_snapshot_path),
            "finished_at": utc_now(),
        }
        state["status"] = "accepted"
        state["result"] = {"status": "accepted", "path": "result.json"}
        write_json(state_path, state)
        write_json(run_dir / "result.json", result)
        print(json.dumps({"status": "accepted", "result": str(run_dir / "result.json")}))
        return 0
    except GateFailure as failure:
        mark_failure(run_dir if run_dir.exists() else None, state, failure)
        print(f"Hermes rejected at Gate {failure.gate}: {failure}", file=sys.stderr)
        return failure.exit_code


def promote_command(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    state_path = run_dir / "state.json"
    result_path = run_dir / "result.json"
    if not state_path.is_file() or not result_path.is_file():
        print("Hermes promote: missing state or result", file=sys.stderr)
        return 2
    state = read_json(state_path)
    result = read_json(result_path)
    if state.get("status") != "accepted" or result.get("status") != "accepted":
        print("Hermes promote: run is not accepted", file=sys.stderr)
        return 2
    run_snapshot = run_dir / result["candidate_snapshot"]
    if not run_snapshot.is_file() or sha256_file(run_snapshot) != result["candidate_snapshot_sha256"]:
        print("Hermes promote: candidate snapshot is missing or changed", file=sys.stderr)
        return 2
    repo = Path(state["repo"]).resolve()
    shutil.copy2(run_snapshot, repo / ".gas-snapshot")
    state["promoted"] = {"at": utc_now(), "gas_snapshot_sha256": sha256_file(repo / ".gas-snapshot")}
    write_json(state_path, state)
    print(json.dumps({"status": "promoted", "gas_snapshot": str(repo / ".gas-snapshot")}))
    return 0


def status_command(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    path = run_dir / "result.json"
    if not path.is_file():
        print(f"missing result: {path}", file=sys.stderr)
        return 2
    print(path.read_text(encoding="utf-8"), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hermes.py",
        description="Run a fail-closed Foundry gas-optimisation verification loop.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline = subparsers.add_parser("baseline", help="Run Gate 1 and seal baseline evidence")
    baseline.add_argument("--repo", required=True, help="Foundry repository root")
    baseline.add_argument("--evidence-dir", help="Empty evidence directory outside the repository")
    baseline.add_argument("--fuzz-seed", required=True, help="Pinned Foundry fuzz seed used for gas comparison")
    baseline.add_argument(
        "--no-match-path",
        action="append",
        default=[],
        metavar="GLOB",
        help="Test path to exclude consistently from baseline and verification; repeat as needed",
    )
    baseline.add_argument(
        "--protected-contract",
        action="append",
        type=parse_protected_contract,
        metavar="LABEL=PATH:CONTRACT",
        help="Hook, role provider, proxied implementation, facet, or other layout-sensitive contract; repeat as needed",
    )
    baseline.add_argument(
        "--layout-contract",
        action="append",
        type=parse_protected_contract,
        metavar="LABEL=PATH:CONTRACT",
        help="Non-frozen contract whose layout and method identifiers must still be recorded; repeat as needed",
    )
    baseline.add_argument(
        "--assert-no-protected-contracts",
        action="store_true",
        help="Explicitly assert that no protected/layout-sensitive contract is in scope",
    )
    baseline.set_defaults(handler=baseline_command)

    verify = subparsers.add_parser("verify", help="Run Gates 2-6 against a sealed baseline")
    verify.add_argument("--run-dir", required=True, help="Evidence directory emitted by baseline")
    verify.add_argument(
        "--optimisation-class",
        choices=OPTIMISATION_CLASSES,
        required=True,
        default=None,
        action=SingleValueAction,
        help="The one and only optimisation class in this candidate",
    )
    verify.add_argument(
        "--attest-single-class",
        action="store_true",
        required=True,
        help="Attest that candidate.solidity.diff contains exactly the declared class",
    )
    verify.add_argument(
        "--gas-target",
        action="append",
        required=True,
        metavar="REGEX",
        help="Expected gas measurement regex; repeat as needed and require an improvement in each group",
    )
    sensitive = verify.add_mutually_exclusive_group(required=True)
    sensitive.add_argument(
        "--sensitive-unchecked",
        action="store_true",
        help="Candidate introduces, expands, or relies on unchecked arithmetic that can affect persistent state or asset accounting",
    )
    sensitive.add_argument(
        "--no-sensitive-unchecked",
        action="store_true",
        help="Candidate has no state-sensitive unchecked change",
    )
    verify.add_argument("--non-sensitive-rationale", help="Required for an unchecked candidate classified as non-sensitive")
    verify.add_argument(
        "--allow-unprotected-layout-change",
        action="store_true",
        help="Permit and record a declared layout change only on --layout-contract entries",
    )
    verify.add_argument("--layout-change-rationale", help="Explain who can read the changed layout and why it is safe")
    verify.add_argument("--targeted-match-path", help="Existing targeted fuzz/property test path")
    verify.add_argument("--targeted-match-test", help="Existing targeted differential/property test regex")
    verify.add_argument("--property-proof", help="Describe the oracle, exercised path, and overflow/underflow bounds")
    verify.set_defaults(handler=verify_command)

    promote = subparsers.add_parser("promote", help="Promote an accepted candidate gas snapshot")
    promote.add_argument("--run-dir", required=True)
    promote.set_defaults(handler=promote_command)

    status = subparsers.add_parser("status", help="Print the mesh-readable result JSON")
    status.add_argument("--run-dir", required=True)
    status.set_defaults(handler=status_command)
    return parser


def validate_cross_arguments(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.command == "baseline":
        protected = args.protected_contract or []
        recorded = args.layout_contract or []
        if protected and args.assert_no_protected_contracts:
            parser.error("--assert-no-protected-contracts conflicts with --protected-contract")
        if not protected and not args.assert_no_protected_contracts:
            parser.error("supply --protected-contract or explicitly use --assert-no-protected-contracts")
        labels = [contract["label"] for contract in [*protected, *recorded]]
        if len(labels) != len(set(labels)):
            parser.error("contract labels must be unique across layout inspections")
        return
    if args.command != "verify":
        return
    targeted = [args.targeted_match_path, args.targeted_match_test, args.property_proof]
    if args.sensitive_unchecked and not all(targeted):
        parser.error(
            "--sensitive-unchecked requires --targeted-match-path, --targeted-match-test, and --property-proof"
        )
    if args.no_sensitive_unchecked and any(targeted):
        parser.error("targeted property options require --sensitive-unchecked")
    if args.allow_unprotected_layout_change:
        if not args.layout_change_rationale or len(args.layout_change_rationale.strip()) < 40:
            parser.error("--allow-unprotected-layout-change requires a substantive --layout-change-rationale")
    elif args.layout_change_rationale:
        parser.error("--layout-change-rationale requires --allow-unprotected-layout-change")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_cross_arguments(parser, args)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
