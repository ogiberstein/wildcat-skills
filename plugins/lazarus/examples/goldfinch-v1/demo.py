#!/usr/bin/env python3
"""Demonstrate the Goldfinch receipt-root relations without a provider."""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
from io import StringIO
from pathlib import Path
import shutil
import socket
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable
from unittest import mock


FIXTURE = Path(__file__).resolve().parent
PLUGIN_ROOT = FIXTURE.parents[1]
REPOSITORY = PLUGIN_ROOT.parents[1]
SHIPPED_RELEASE = PLUGIN_ROOT / "examples" / "goldfinch-v1-release"
LEGACY_FIXTURE = PLUGIN_ROOT / "examples" / "goldfinch-v0"
LEGACY_RELEASE = PLUGIN_ROOT / "examples" / "goldfinch-v0-release"
ARIADNE = REPOSITORY / "plugins" / "ariadne" / "scripts" / "ariadne.py"
SCRIPTS = PLUGIN_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lazarus_lib.canonical import dump, dumps, load
from lazarus_lib.capture import _atomic_no_replace
from lazarus_lib.errors import IntegrityError, LazarusError, PathError
from lazarus_lib.manifest import (
    build_manifest,
    component_claim,
    fixture_digest,
    write_manifest,
)
from lazarus_lib.paths import read_confined_bytes
from lazarus_lib.records import (
    read_rpc_records,
    request_key,
    write_rpc_records,
)
from lazarus_lib.release import RELEASE_NAME, release_digest, verify_release, write_release
from lazarus_lib.verifier import verify_fixture
from lazarus_lib.version import __version__


BLOCK_NUMBER = "0xc7da16"
BLOCK_HASH = "0x41119192a8acdaae5ab06ca8f1d5943fd7ca2fb0a14323642dd6daf74eed2cfc"
TARGET_SELECTOR = "0xa46a744d6d52528a660c1d99a4edde403504fe7a308118c7cc947819583ce699"
RECEIPTS_ROOT = "0xaf03b0508121deb9ed0282a8961dc0ea695a97244a42ed2b0af04cb9bbc6226e"
TARGET_INDEX = 0xBF
STATEMENT_TYPE = "https://ariadne.wildcat.finance/state-fixture/v2"
CORRELATION_ID = "goldfinch-v1-offline-demo"
SOURCE_FIXTURE = PLUGIN_ROOT / "tests" / "fixtures" / "receipt-proof-v1"
SOURCE_FIXTURE_DIGEST = (
    "a88218e27b979a67941bd66f04eec9e0d1208178697c0c3f59a245f22dba0eec"
)
SOURCE_COMPONENTS = (
    "anchors.jsonl",
    "header.json",
    "plan.json",
    "proofs.jsonl",
    "receipt-witness.json",
    "rpc.jsonl",
)
FIXTURE_COMPONENTS = SOURCE_COMPONENTS + ("demo.py",)
PRODUCER_COMMAND = (
    "python3",
    "plugins/lazarus/examples/goldfinch-v1/demo.py",
    "build-fixture",
    "--out",
    "tmp/goldfinch-v1-rebuild",
)
LEGACY_DIGESTS = {
    "fixture": "d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49",
    "manifest": "c37cd789e5386a1347abd4dff24c8b1db96cdab771df4eb4d63056ba56145fa9",
    "statement": "d8b262278ffd4db76e449a2bfce4629903a70e7f4ad7c1f3a6ebbfb1f112555e",
    "release": "ec5c9b8091286de8713b6daf6cfdeaa7e9cfa6177b96c10a2ed20ffd6654bcff",
}


def _ariadne_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("goldfinch_v1_ariadne", ARIADNE)
    if spec is None or spec.loader is None:
        raise AssertionError("Ariadne CLI could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_ariadne(module: ModuleType, arguments: list[str]) -> None:
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        code = module.main(arguments)
    if code != 0:
        raise AssertionError(
            f"Ariadne stage {arguments[0]} exited {code}: {output.getvalue()}"
        )


def _capture_statement(module: ModuleType, fixture: Path, out: Path) -> None:
    command_arguments: list[str] = []
    for word in PRODUCER_COMMAND:
        if word.startswith("-"):
            command_arguments.append(f"--capture-command={word}")
        else:
            command_arguments.extend(("--capture-command", word))
    _run_ariadne(
        module,
        [
            "capture-state-fixture",
            "--fixture",
            str(fixture),
            "--name",
            "goldfinch-v1",
            "--capture-tool",
            "lazarus",
            "--capture-version",
            "0.2.0",
            *command_arguments,
            "--first-capture-reason",
            "first receipts-root-proved Goldfinch fixture",
            "--out",
            str(out),
        ],
    )
    _run_ariadne(module, ["verify", str(out)])


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def build_fixture(output: str | Path) -> dict[str, Any]:
    """Materialise the published fixture from its pinned source components."""

    source_report = verify_fixture(SOURCE_FIXTURE)
    if source_report["fixture_digest"] != SOURCE_FIXTURE_DIGEST:
        raise IntegrityError("pinned receipt-proof-v1 fixture changed")
    source_claims = source_report["manifest"]["components"]
    if tuple(item["path"] for item in source_claims) != SOURCE_COMPONENTS:
        raise IntegrityError("pinned receipt-proof-v1 component inventory changed")

    requested = Path(output)
    if not requested.name or requested.name in {".", ".."}:
        raise PathError("fixture output must name a new directory")
    try:
        intended_destination = requested.resolve(strict=False)
    except (OSError, RuntimeError):
        raise PathError("fixture output cannot be resolved") from None
    source_roots = (FIXTURE.resolve(), SOURCE_FIXTURE.resolve())
    for source_root in source_roots:
        if (
            intended_destination == source_root
            or source_root in intended_destination.parents
        ):
            raise PathError("fixture output cannot be inside a source fixture")

    parent_path = requested.parent
    created_parent = False
    try:
        parent = parent_path.resolve(strict=True)
    except FileNotFoundError:
        try:
            parent_path.mkdir(mode=0o700)
            created_parent = True
            parent = parent_path.resolve(strict=True)
        except OSError:
            if created_parent:
                try:
                    parent_path.rmdir()
                except OSError:
                    pass
            raise PathError("fixture output parent cannot be created") from None
    except OSError:
        raise PathError("fixture output parent cannot be resolved") from None
    if not parent.is_dir():
        raise PathError("fixture output parent is not a directory")
    destination = parent / requested.name
    if destination.exists() or destination.is_symlink():
        raise PathError("fixture output already exists")
    for source_root in source_roots:
        if destination == source_root or source_root in destination.parents:
            if created_parent:
                try:
                    parent.rmdir()
                except OSError:
                    pass
            raise PathError("fixture output cannot be inside a source fixture")

    stage: Path | None = None
    published = False
    try:
        try:
            stage = Path(
                tempfile.mkdtemp(prefix=f".{destination.name}.stage-", dir=parent)
            )
        except OSError:
            raise PathError("fixture stage cannot be created") from None
        for claim in source_claims:
            relative = claim["path"]
            data = read_confined_bytes(
                SOURCE_FIXTURE,
                relative,
                max_bytes=claim["bytes"],
            )
            if len(data) != claim["bytes"] or hashlib.sha256(data).hexdigest() != claim[
                "sha256"
            ]:
                raise IntegrityError(
                    "pinned receipt-proof-v1 source changed during build"
                )
            (stage / relative).write_bytes(data)
        copied_claims = [
            component_claim(stage, relative) for relative in SOURCE_COMPONENTS
        ]
        if copied_claims != source_claims:
            raise IntegrityError("pinned receipt-proof-v1 source changed during build")
        demo_bytes = read_confined_bytes(FIXTURE, "demo.py", max_bytes=1024 * 1024)
        (stage / "demo.py").write_bytes(demo_bytes)

        manifest = build_manifest(
            stage,
            FIXTURE_COMPONENTS,
            chain_id="0x1",
            block_number=BLOCK_NUMBER,
            block_hash=BLOCK_HASH,
        )
        write_manifest(stage, manifest)
        report = verify_fixture(stage)
        _atomic_no_replace(stage, destination)
        published = True
        return report
    finally:
        if not published and stage is not None and stage.exists():
            shutil.rmtree(stage)
        if not published and created_parent:
            try:
                parent.rmdir()
            except OSError:
                pass


def _flip_last_hex(value: str) -> str:
    return value[:-1] + ("0" if value[-1] != "0" else "1")


def _flip_last_byte_hex(value: str) -> str:
    if not value.startswith("0x") or len(value) < 4 or len(value) % 2 != 0:
        raise AssertionError("mutation target is not a non-empty byte string")
    return value[:-2] + f"{int(value[-2:], 16) ^ 1:02x}"


def _refresh_component(root: Path, relative: str) -> None:
    manifest = load(root / "manifest.json")
    manifest["components"] = [
        component_claim(root, relative) if item["path"] == relative else item
        for item in manifest["components"]
    ]
    manifest["fixture_digest"] = fixture_digest(manifest)
    write_manifest(root, manifest)


def _mutate_witness(root: Path, change: Callable[[dict[str, Any]], None]) -> None:
    witness = load(root / "receipt-witness.json")
    change(witness)
    dump(root / "receipt-witness.json", witness)
    _refresh_component(root, "receipt-witness.json")


def _expect_fixture_rejection(
    workspace: Path,
    label: str,
    change: Callable[[Path], None],
) -> str:
    changed = workspace / f"mutated-{label}"
    shutil.copytree(FIXTURE, changed)
    change(changed)
    try:
        verify_fixture(changed)
    except LazarusError:
        return "rejected"
    raise AssertionError(f"{label} mutation was accepted")


def _receipt_mutation(root: Path) -> None:
    _mutate_witness(
        root,
        lambda witness: witness["receipts"][0].__setitem__("status", "0x0"),
    )


def _index_mutation(root: Path) -> None:
    _mutate_witness(
        root,
        lambda witness: witness["receipts"][TARGET_INDEX].__setitem__(
            "transaction_index", "0xbe"
        ),
    )


def _log_mutation(root: Path) -> None:
    def change(witness: dict[str, Any]) -> None:
        log = witness["receipts"][TARGET_INDEX]["logs"][0]
        # ephoros: allow receipt-witness field access is mutation evidence, not telemetry
        log["address"] = _flip_last_byte_hex(log["address"])

    _mutate_witness(root, change)


def _root_mutation(root: Path) -> None:
    def change(witness: dict[str, Any]) -> None:
        witness["header"]["receipts_root"] = _flip_last_hex(
            witness["header"]["receipts_root"]
        )

    _mutate_witness(root, change)


def _count_mutation(root: Path) -> None:
    manifest = load(root / "manifest.json")
    manifest["evidence_counts"]["receipt_trie_proved"] = 1
    manifest["fixture_digest"] = fixture_digest(manifest)
    write_manifest(root, manifest)


def _rewrite_recorded_target_hash(root: Path, transaction_hash: str) -> None:
    plan = load(root / "plan.json")
    header = load(root / "header.json")
    records = read_rpc_records(root / "rpc.jsonl")
    relation = plan["receipt_witness"]
    index = int(relation["target_transaction_index"], 16)
    header["rpc_result"]["transactions"][index] = transaction_hash

    request = next(
        item
        for item in plan["requests"]
        if item["name"] == relation["target_receipt_lookup_request"]
    )
    request["params"] = [transaction_hash]
    by_name = {record["name"]: record for record in records}
    target = by_name[relation["target_receipt_lookup_request"]]
    target["params"] = [transaction_hash]
    target["request_key"] = request_key(target["method"], target["params"])

    block_receipts = by_name[relation["block_receipts_request"]]["outcome"]["result"]
    for receipt in (block_receipts[index], target["outcome"]["result"]):
        receipt["transactionHash"] = transaction_hash
        for log in receipt["logs"]:
            log["transactionHash"] = transaction_hash
    filtered = by_name[relation["filtered_logs_request"]]["outcome"]["result"]
    for log in filtered:
        if int(log["transactionIndex"], 16) == index:
            log["transactionHash"] = transaction_hash

    dump(root / "plan.json", plan)
    dump(root / "header.json", header)
    write_rpc_records(root / "rpc.jsonl", records)
    for relative in ("plan.json", "header.json", "rpc.jsonl"):
        _refresh_component(root, relative)


def _hash_rewrite_evidence(workspace: Path, baseline: dict[str, Any]) -> str:
    rewritten = workspace / "coherent-hash-rewrite"
    shutil.copytree(FIXTURE, rewritten)
    _rewrite_recorded_target_hash(rewritten, "0x" + "aa" * 32)
    report = verify_fixture(rewritten)
    if report["receipts_root"] != baseline["receipts_root"]:
        raise AssertionError("recorded hash rewrite changed the receipt root")
    if report["receipt_trie_proved"] != baseline["receipt_trie_proved"]:
        raise AssertionError("recorded hash rewrite changed a proved relation")
    return "unchanged"


def _recorded_disagreement_evidence(workspace: Path) -> str:
    changed = workspace / "recorded-hash-disagreement"
    shutil.copytree(FIXTURE, changed)
    header = load(changed / "header.json")
    header["rpc_result"]["transactions"][TARGET_INDEX] = "0x" + "bb" * 32
    dump(changed / "header.json", header)
    _refresh_component(changed, "header.json")
    try:
        verify_fixture(changed)
    except LazarusError as error:
        words = str(error).lower()
        if "recorded rpc transaction hash disagreement" not in words:
            raise AssertionError("recorded-source disagreement reached the wrong gate") from error
        if "root" in words or "proved" in words:
            raise AssertionError("recorded-source disagreement was promoted") from error
        return "rejected-recorded-rpc"
    raise AssertionError("one-source recorded hash disagreement was accepted")


def _release_mutation_evidence(workspace: Path) -> str:
    changed = workspace / "mutated-release"
    shutil.copytree(SHIPPED_RELEASE, changed)
    document = load(changed / RELEASE_NAME)
    document["verified"]["receipts_root"] = _flip_last_hex(
        document["verified"]["receipts_root"]
    )
    dump(changed / RELEASE_NAME, document)
    try:
        verify_release(changed)
    except LazarusError:
        return "rejected"
    raise AssertionError("one-byte release mutation was accepted")


def _legacy_evidence() -> dict[str, str]:
    observed = {
        "fixture": verify_fixture(LEGACY_FIXTURE)["fixture_digest"],
        "manifest": hashlib.sha256(
            (LEGACY_FIXTURE / "manifest.json").read_bytes()
        ).hexdigest(),
        "statement": hashlib.sha256(
            (LEGACY_RELEASE / "statement.json").read_bytes()
        ).hexdigest(),
        "release": hashlib.sha256(
            (LEGACY_RELEASE / RELEASE_NAME).read_bytes()
        ).hexdigest(),
    }
    if observed != LEGACY_DIGESTS:
        raise AssertionError("historical Goldfinch v0 bytes changed")
    return observed


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("offline demonstration attempted a network connection")


def run_demo() -> dict[str, Any]:
    with mock.patch.object(socket.socket, "connect", side_effect=_deny_network), mock.patch.object(
        socket, "create_connection", side_effect=_deny_network
    ):
        fixture_report = verify_fixture(FIXTURE)
        release_report = verify_release(SHIPPED_RELEASE)
        relation = fixture_report["receipt_trie_proved"]
        if relation["computed_root"] != RECEIPTS_ROOT:
            raise AssertionError("Goldfinch receipt root changed")
        if (
            relation["receipt_count"],
            relation["target_transaction_index"],
            relation["target_log_count"],
            relation["filtered_log_count"],
            relation["relations"],
        ) != (224, "0xbf", 110, 5, 2):
            raise AssertionError("Goldfinch proved relation changed")
        if relation["transaction_hash_attribution"] != "recorded_rpc":
            raise AssertionError("transaction-hash attribution was promoted")

        ariadne = _ariadne_module()
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            rebuilt_fixture = workspace / "goldfinch-v1-rebuild"
            build_fixture(rebuilt_fixture)
            if _tree_bytes(rebuilt_fixture) != _tree_bytes(FIXTURE):
                raise AssertionError("shipped fixture differs from a fresh build")
            statement_a = workspace / "statement-a.json"
            statement_b = workspace / "statement-b.json"
            _capture_statement(ariadne, rebuilt_fixture, statement_a)
            _capture_statement(ariadne, rebuilt_fixture, statement_b)
            if statement_a.read_bytes() != statement_b.read_bytes():
                raise AssertionError("state-fixture/v2 capture is not deterministic")
            if statement_a.read_bytes() != (SHIPPED_RELEASE / "statement.json").read_bytes():
                raise AssertionError("shipped statement differs from a fresh capture")

            release_a = workspace / "release-a"
            release_b = workspace / "release-b"
            write_release(rebuilt_fixture, statement_a, release_a)
            write_release(rebuilt_fixture, statement_b, release_b)
            if _tree_bytes(release_a) != _tree_bytes(release_b):
                raise AssertionError("release-v2 rebuild is not deterministic")
            if _tree_bytes(release_a) != _tree_bytes(SHIPPED_RELEASE):
                raise AssertionError("shipped release differs from a fresh rebuild")

            mutations = {
                "receipt": _expect_fixture_rejection(
                    workspace, "receipt", _receipt_mutation
                ),
                "index": _expect_fixture_rejection(
                    workspace, "index", _index_mutation
                ),
                "log": _expect_fixture_rejection(workspace, "log", _log_mutation),
                "root": _expect_fixture_rejection(
                    workspace, "root", _root_mutation
                ),
                "count": _expect_fixture_rejection(
                    workspace, "count", _count_mutation
                ),
                "release": _release_mutation_evidence(workspace),
            }
            hash_rewrite = _hash_rewrite_evidence(workspace, fixture_report)
            recorded_disagreement = _recorded_disagreement_evidence(workspace)

        statement_sha256 = release_report["statement_sha256"]
        return {
            "event": "goldfinch_receipt_proof_demo",
            "correlation_id": CORRELATION_ID,
            "stage": "complete",
            "network": "denied",
            "fixture_rebuild": "identical",
            "block": {"number": BLOCK_NUMBER, "hash": BLOCK_HASH},
            "recorded_target_selector": TARGET_SELECTOR,
            "relation": {
                "receipts_root": relation["computed_root"],
                "receipt_count": relation["receipt_count"],
                "target_index": relation["target_transaction_index"],
                "target_log_count": relation["target_log_count"],
                "filtered_log_count": relation["filtered_log_count"],
                "proved_relations": relation["relations"],
                "transaction_hash_attribution": relation[
                    "transaction_hash_attribution"
                ],
            },
            "evidence_counts": fixture_report["evidence_counts"],
            "versions": {
                "writer": __version__,
                "manifest": fixture_report["manifest"]["schema_version"],
                "statement": STATEMENT_TYPE,
                "release": load(SHIPPED_RELEASE / RELEASE_NAME)["schema_version"],
            },
            "digests": {
                "fixture": fixture_report["fixture_digest"],
                "statement": statement_sha256,
                "release": release_report["release_digest"],
            },
            "mutations": mutations,
            "coherent_transaction_hash_rewrite": hash_rewrite,
            "recorded_hash_disagreement": recorded_disagreement,
            "legacy": _legacy_evidence(),
        }


def main(arguments: list[str] | None = None) -> int:
    words = list(sys.argv[1:] if arguments is None else arguments)
    if words:
        parser = argparse.ArgumentParser(
            description="Build the fixed Goldfinch fixture or run its offline demo."
        )
        commands = parser.add_subparsers(dest="command", required=True)
        builder = commands.add_parser(
            "build-fixture",
            help="materialise the byte-exact fixture from pinned local sources",
        )
        builder.add_argument("--out", required=True)
        parsed = parser.parse_args(words)
        if parsed.command == "build-fixture":
            try:
                report = build_fixture(parsed.out)
            except LazarusError as error:
                print(f"refused: {error}", file=sys.stderr)
                return 1
            print(
                dumps(
                    {
                        "event": "goldfinch_fixture_build",
                        "stage": "complete",
                        "fixture_digest": report["fixture_digest"],
                    }
                ).decode("utf-8")
            )
            return 0
        raise AssertionError("unreachable Goldfinch command")
    print(dumps(run_demo()).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
