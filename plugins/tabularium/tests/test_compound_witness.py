"""Compound Phase 0 witness reconstruction and hostile refusal tests."""

import hashlib
import json
from pathlib import Path
import shutil
import socket
import tempfile
import unittest
from unittest import mock

from . import support
from tabularium_lib.compound_witness import (
    build_compound_witness,
    decode_principal,
    debt_transfer_conformance,
    verify_compound_witness,
)
from tabularium_lib.core import TabulariumError
from tabularium_lib.keccak import keccak256, mapping_slot


EXAMPLE = support.PLUGIN_ROOT / "examples" / "compound-v3-phase0-v0"
ALEXANDRIA = support.REPO_ROOT / "plugins" / "alexandria" / "examples" / "compound-v3-phase0-v0" / "release"
FIXTURE = support.PLUGIN_ROOT / "tests" / "fixtures" / "compound-debt-transfer.json"


class CompoundWitnessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def build(self, prefix="one"):
        facts = self.root / (prefix + "-facts.jsonl")
        manifest = self.root / (prefix + "-witness.json")
        report = build_compound_witness(ALEXANDRIA, facts, manifest)
        return facts, manifest, report

    def test_ethereum_keccak_and_mapping_slot_vectors(self):
        self.assertEqual(keccak256(b"").hex(), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
        self.assertEqual(
            mapping_slot("0x56105c17bef06455e1066f7c455ff28f15c7283e", 5),
            "0xcd0f529d81158ba9167238f24519db12c14ccee8db94d025c74b9a693804a040",
        )

    def test_signed_int104_boundaries(self):
        mask = (1 << 104) - 1
        for value in (0, 1, (1 << 103) - 1, -(1 << 103), -1, -6349137978):
            encoded = value & mask
            self.assertEqual(decode_principal("0x" + format(encoded, "064x")), value)

    def test_checked_witness_has_fixed_bytes_and_expected_semantics(self):
        facts = EXAMPLE / "facts.jsonl"
        manifest = EXAMPLE / "witness.json"
        self.assertEqual(hashlib.sha256(facts.read_bytes()).hexdigest(), "08cc6cac67fb8ec9070d32c97b712047cecbcd255e4218245c3593f7df53d6fe")
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            report = verify_compound_witness(ALEXANDRIA, facts, manifest)
        rows = [json.loads(line) for line in facts.read_text().splitlines()]
        self.assertEqual(report["row_count"], 11)
        self.assertEqual([row["call_path"] for row in rows if row["kind"] == "call"], [[0], [1]])
        storage = [row for row in rows if row["kind"] == "storage-write"]
        self.assertEqual([row["opcode_index"] for row in storage], sorted(row["opcode_index"] for row in storage))
        self.assertEqual(storage[0]["call_path"], [0])
        self.assertTrue(all(row["call_path"] == [1] for row in storage[1:]))
        principal = next(row for row in rows if row["kind"] == "principal-transition")
        self.assertEqual((principal["principal_before"], principal["principal_after"]), (0, -6349137978))

    def test_two_builds_are_identical_and_idempotent(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            first = self.build("first")
            second = self.build("second")
            build_compound_witness(ALEXANDRIA, first[0], first[1])
        self.assertEqual(first[0].read_bytes(), second[0].read_bytes())
        self.assertEqual(first[1].read_bytes(), second[1].read_bytes())

    def test_fact_or_manifest_tamper_fails(self):
        facts, manifest, _ = self.build()
        facts.write_bytes(facts.read_bytes() + b"\n")
        with self.assertRaisesRegex(TabulariumError, "do not match"):
            verify_compound_witness(ALEXANDRIA, facts, manifest)

    def test_outputs_cannot_alias_or_enter_the_alexandria_release(self):
        target = self.root / "same"
        with self.assertRaisesRegex(TabulariumError, "alias"):
            build_compound_witness(ALEXANDRIA, target, target)
        with self.assertRaisesRegex(TabulariumError, "outside"):
            build_compound_witness(ALEXANDRIA, ALEXANDRIA / "facts.jsonl", self.root / "manifest.json")

    def test_synthetic_debt_transfer_fixture_is_explicit_and_hostile(self):
        fixture = json.loads(FIXTURE.read_text())
        self.assertEqual(fixture["evidence_class"], "synthetic-conformance")
        legs = debt_transfer_conformance(
            fixture["principal_source_before"], fixture["principal_source_after"],
            fixture["principal_destination_before"], fixture["principal_destination_after"],
        )
        self.assertEqual(legs, {"source_principal_delta": -600, "destination_principal_delta": 600})
        with self.assertRaises(TabulariumError):
            debt_transfer_conformance(-1000, -900, -900, -300)

    def test_tampered_alexandria_object_is_refused(self):
        copied = self.root / "alexandria"
        shutil.copytree(ALEXANDRIA, copied)
        manifest = json.loads((copied / "manifest.json").read_text())
        component = next(item for item in manifest["components"] if item["name"] == "response-recent-call-trace")
        object_path = copied / component["object_path"]
        object_path.write_bytes(object_path.read_bytes() + b"\n")
        with self.assertRaisesRegex(TabulariumError, "failed verification"):
            build_compound_witness(copied, self.root / "facts.jsonl", self.root / "witness.json")


if __name__ == "__main__":
    unittest.main()
