"""The fixture command joins digest, header and proof checks offline."""

import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from lazarus_lib.canonical import dump
from lazarus_lib.errors import IntegrityError
from lazarus_lib.manifest import build_manifest, write_manifest
from lazarus_lib.records import make_rpc_record, write_proof_records, write_rpc_records
from lazarus_lib.verifier import verify_fixture

from . import support


COMPONENTS = ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl")


def write_fixture(root: Path, material=None, *, counts=None):
    material = material or support.synthetic_fixture_material()
    dump(root / "plan.json", material["plan"])
    dump(root / "header.json", material["header"])
    write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
    write_proof_records(root / "proofs.jsonl", material["proof_records"])
    manifest = build_manifest(
        root,
        COMPONENTS,
        chain_id="0x1",
        block_number=material["header"]["number"],
        block_hash=material["header"]["hash"],
        evidence_counts=counts
        or {"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
    )
    write_manifest(root, manifest)
    return material


class VerifierTests(unittest.TestCase):
    def test_whole_fixture_reports_each_evidence_class_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            report = verify_fixture(root)
            self.assertEqual(
                report["evidence_counts"],
                {"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
            )
            self.assertEqual(report["proof_backed"]["accounts_included"], 1)
            self.assertEqual(report["proof_backed"]["storage_included"], 1)
            self.assertEqual(report["proof_backed"]["storage_absent"], 1)
            self.assertFalse(report["header_bound"]["canonical_chain_claim"])

    def test_cli_verify_runs_the_full_verifier_and_prints_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            result = subprocess.run(
                [sys.executable, str(support.SCRIPTS / "lazarus.py"), "verify", str(root)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("proof-backed: 3", result.stdout)
            self.assertIn("header-bound: 1", result.stdout)
            self.assertIn("recorded-rpc: 1", result.stdout)

    def test_raw_component_mutation_fails_before_interpretation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            with (root / "proofs.jsonl").open("ab") as handle:
                handle.write(b"\n")
            with self.assertRaisesRegex(IntegrityError, "size mismatch"):
                verify_fixture(root)

    def test_proof_mutation_fails_even_after_manifest_is_rebuilt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = write_fixture(root)
            changed = copy.deepcopy(material["proof_records"])
            node = changed[0]["account_proof"][0]
            changed[0]["account_proof"][0] = node[:-1] + ("0" if node[-1] != "0" else "1")
            write_proof_records(root / "proofs.jsonl", changed)
            rebuilt = build_manifest(
                root,
                COMPONENTS,
                chain_id="0x1",
                block_number=material["header"]["number"],
                block_hash=material["header"]["hash"],
                evidence_counts={"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
            )
            write_manifest(root, rebuilt)
            with self.assertRaisesRegex(IntegrityError, "root"):
                verify_fixture(root)

    def test_proved_rpc_results_cannot_disagree_after_manifest_rebinding(self):
        base = support.synthetic_fixture_material()
        proof = base["proof_records"][0]
        account = proof["address"]
        block = base["header"]["number"]
        present_slot = proof["storage_proof"][0]["key"]
        get_proof_result = {
            "address": account,
            "balance": proof["balance"],
            "nonce": proof["nonce"],
            "codeHash": proof["code_hash"],
            "storageHash": proof["storage_hash"],
            "accountProof": proof["account_proof"],
            "storageProof": [
                {
                    "key": proof["storage_proof"][0]["key"],
                    "value": proof["storage_proof"][0]["value"],
                    "proof": proof["storage_proof"][0]["proof"],
                }
            ],
        }
        changed_get_proof = copy.deepcopy(get_proof_result)
        changed_get_proof["balance"] = "0x3"
        cases = (
            ("eth_getBalance", [account, block], proof["balance"], "0x3"),
            ("eth_getTransactionCount", [account, block], proof["nonce"], "0x2"),
            ("eth_getCode", [account, block], proof["code"], "0x6001"),
            (
                "eth_getProof",
                [account, [present_slot], block],
                get_proof_result,
                changed_get_proof,
            ),
            (
                "eth_getStorageAt",
                [account, present_slot, block],
                "0x" + "00" * 31 + "38",
                "0x" + "00" * 32,
            ),
        )
        for method, params, correct, changed in cases:
            with self.subTest(method=method), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                material = copy.deepcopy(base)
                name = f"proved-{method.lower()}"
                material["plan"]["requests"] = [
                    {
                        "name": name,
                        "method": method,
                        "params": params,
                        "required": True,
                        "evidence": "recorded-rpc",
                    }
                ]
                material["rpc_records"] = [
                    make_rpc_record(
                        method,
                        params,
                        required=True,
                        evidence="recorded-rpc",
                        result=correct,
                        name=name,
                    )
                ]
                write_fixture(root, material)
                verify_fixture(root)
                material["rpc_records"][0]["outcome"]["result"] = changed
                write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
                rebuilt = build_manifest(
                    root,
                    COMPONENTS,
                    chain_id="0x1",
                    block_number=material["header"]["number"],
                    block_hash=material["header"]["hash"],
                    evidence_counts={
                        "proof_backed": 3,
                        "header_bound": 1,
                        "recorded_rpc": 1,
                    },
                )
                write_manifest(root, rebuilt)
                with self.assertRaisesRegex(IntegrityError, "proof-backed RPC"):
                    verify_fixture(root)

    def test_proved_rpc_selector_must_name_the_fixture_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = support.synthetic_fixture_material()
            proof = material["proof_records"][0]
            params = [proof["address"], proof["storage_proof"][0]["key"], "0x1"]
            material["plan"]["requests"] = [
                {
                    "name": "wrong-block-slot",
                    "method": "eth_getStorageAt",
                    "params": params,
                    "required": True,
                    "evidence": "recorded-rpc",
                }
            ]
            material["rpc_records"] = [
                make_rpc_record(
                    "eth_getStorageAt",
                    params,
                    required=True,
                    evidence="recorded-rpc",
                    result="0x" + "00" * 31 + "38",
                    name="wrong-block-slot",
                )
            ]
            write_fixture(root, material)
            with self.assertRaisesRegex(IntegrityError, "selector names another block"):
                verify_fixture(root)

    def test_recorded_block_fields_remain_header_bound_after_rebinding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = support.synthetic_fixture_material()
            transaction = support.hash32("77")
            params = [transaction]
            result = {
                "transactionHash": transaction,
                "blockHash": material["header"]["hash"],
                "blockNumber": material["header"]["number"],
            }
            material["plan"]["requests"] = [
                {
                    "name": "receipt",
                    "method": "eth_getTransactionReceipt",
                    "params": params,
                    "required": True,
                    "evidence": "recorded-rpc",
                }
            ]
            material["rpc_records"] = [
                make_rpc_record(
                    "eth_getTransactionReceipt",
                    params,
                    required=True,
                    evidence="recorded-rpc",
                    result=result,
                    name="receipt",
                )
            ]
            write_fixture(root, material)
            verify_fixture(root)
            material["rpc_records"][0]["outcome"]["result"]["blockHash"] = (
                support.hash32("99")
            )
            write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
            rebuilt = build_manifest(
                root,
                COMPONENTS,
                chain_id="0x1",
                block_number=material["header"]["number"],
                block_hash=material["header"]["hash"],
                evidence_counts={
                    "proof_backed": 3,
                    "header_bound": 1,
                    "recorded_rpc": 1,
                },
            )
            write_manifest(root, rebuilt)
            with self.assertRaisesRegex(IntegrityError, "another block hash"):
                verify_fixture(root)

    def test_manifest_counts_and_rpc_coverage_are_not_trusted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(IntegrityError, "evidence counts"):
                write_fixture(
                    root,
                    counts={"proof_backed": 2, "header_bound": 1, "recorded_rpc": 1},
                )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = support.synthetic_fixture_material()
            material["plan"]["requests"][0]["method"] = "eth_blockNumber"
            dump(root / "plan.json", material["plan"])
            dump(root / "header.json", material["header"])
            write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
            write_proof_records(root / "proofs.jsonl", material["proof_records"])
            with self.assertRaisesRegex(IntegrityError, "requests are missing"):
                build_manifest(
                    root,
                    COMPONENTS,
                    chain_id="0x1",
                    block_number=material["header"]["number"],
                    block_hash=material["header"]["hash"],
                    evidence_counts={
                        "proof_backed": 3,
                        "header_bound": 1,
                        "recorded_rpc": 1,
                    },
                )

    def test_missing_or_extra_proof_targets_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = support.synthetic_fixture_material()
            material["plan"]["proof_targets"] = []
            with self.assertRaisesRegex(IntegrityError, "unplanned proof targets"):
                write_fixture(root, material)

    def test_components_remain_digest_bound_after_manifest_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            from lazarus_lib import verifier as verifier_module

            original_verify = verifier_module.verify_manifest

            def verify_then_mutate(fixture):
                manifest = original_verify(fixture)
                path = root / "rpc.jsonl"
                data = path.read_bytes()
                path.write_bytes(data.replace(b'"0x1"', b'"0x2"', 1))
                return manifest

            with mock.patch(
                "lazarus_lib.verifier.verify_manifest",
                side_effect=verify_then_mutate,
            ):
                with self.assertRaisesRegex(IntegrityError, "changed after"):
                    verify_fixture(root)


if __name__ == "__main__":
    unittest.main()
