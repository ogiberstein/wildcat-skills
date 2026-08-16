"""The five versioned formats validate before they reach fixture logic."""

import copy
import unittest
from unittest import mock

from lazarus_lib.errors import FormatError, IntegrityError
from lazarus_lib.records import make_rpc_record
from lazarus_lib.schemas import SCHEMAS, validate_builtin_schemas, validate_document

from . import support


class SchemaTests(unittest.TestCase):
    def test_every_registered_schema_is_valid_and_digest_pinned(self):
        validate_builtin_schemas()
        self.assertEqual(
            {kind for kind, version in SCHEMAS if version == 1},
            {"plan", "header", "rpc-record", "proof-record", "manifest"},
        )

    def test_valid_plan_header_rpc_and_proof_documents_pass(self):
        validate_document("plan", support.sample_plan())
        validate_document("header", support.sample_header())
        validate_document(
            "rpc-record",
            make_rpc_record(
                "eth_chainId", [], required=True, evidence="recorded-rpc", result="0x1"
            ),
        )
        validate_document("proof-record", support.sample_proof_record())

    def test_unknown_schema_versions_fail_closed(self):
        for kind, document in (
            ("plan", support.sample_plan()),
            ("header", support.sample_header()),
            ("proof-record", support.sample_proof_record()),
        ):
            document["schema_version"] = 2
            with self.subTest(kind=kind), self.assertRaisesRegex(FormatError, "unsupported"):
                validate_document(kind, document)

    def test_quantities_and_addresses_keep_exact_ethereum_shapes(self):
        plan = support.sample_plan()
        plan["block"]["number"] = "0x00"
        with self.assertRaisesRegex(FormatError, "number"):
            validate_document("plan", plan)
        plan = support.sample_plan()
        plan["proof_targets"][0]["address"] = "0x1234"
        with self.assertRaisesRegex(FormatError, "address"):
            validate_document("plan", plan)
        proof = support.sample_proof_record()
        proof["balance"] = "1"
        with self.assertRaisesRegex(FormatError, "balance"):
            validate_document("proof-record", proof)
        proof = support.sample_proof_record()
        proof["balance"] = "0x1" + "0" * 64
        with self.assertRaisesRegex(FormatError, "balance"):
            validate_document("proof-record", proof)

    def test_plan_rejects_duplicate_requests_targets_and_unsorted_slots(self):
        plan = support.sample_plan()
        plan["requests"].append(copy.deepcopy(plan["requests"][0]))
        plan["requests"][1]["name"] = "same-request"
        with self.assertRaisesRegex(FormatError, "duplicate exact request"):
            validate_document("plan", plan)
        plan = support.sample_plan()
        plan["proof_targets"].append(copy.deepcopy(plan["proof_targets"][0]))
        with self.assertRaisesRegex(FormatError, "proof target address"):
            validate_document("plan", plan)
        plan = support.sample_plan()
        plan["proof_targets"][0]["slots"] = [support.slot("02"), support.slot("01")]
        with self.assertRaisesRegex(FormatError, "sorted and unique"):
            validate_document("plan", plan)

    def test_plan_enforces_its_request_limit(self):
        plan = support.sample_plan()
        plan["limits"]["max_requests"] = 1
        second = copy.deepcopy(plan["requests"][0])
        second.update({"name": "block", "method": "eth_blockNumber"})
        plan["requests"].append(second)
        with self.assertRaisesRegex(FormatError, "max_requests"):
            validate_document("plan", plan)

    def test_plan_accepts_only_bounded_integer_capture_time(self):
        plan = support.sample_plan()
        plan["limits"]["max_elapsed_seconds"] = 60
        validate_document("plan", plan)
        for value in (0, 86401, 1.5):
            changed = copy.deepcopy(plan)
            changed["limits"]["max_elapsed_seconds"] = value
            with self.subTest(value=value), self.assertRaisesRegex(
                FormatError, "max_elapsed_seconds"
            ):
                validate_document("plan", changed)

    def test_header_identity_must_match_raw_rpc_result(self):
        header = support.sample_header()
        header["rpc_result"]["hash"] = support.hash32("ff")
        with self.assertRaisesRegex(FormatError, "disagrees"):
            validate_document("header", header)
        header = support.sample_header()
        del header["rpc_result"]["stateRoot"]
        with self.assertRaisesRegex(FormatError, "stateRoot"):
            validate_document("header", header)

    def test_storage_proof_keys_are_sorted_and_unique(self):
        proof = support.sample_proof_record()
        proof["storage_proof"] = [
            {"key": support.slot("02"), "value": "0x0", "proof": ["0xc0"]},
            {"key": support.slot("01"), "value": "0x0", "proof": ["0xc0"]},
        ]
        with self.assertRaisesRegex(FormatError, "sorted and unique"):
            validate_document("proof-record", proof)

    def test_registry_digest_detects_schema_substitution(self):
        filename, _ = SCHEMAS[("plan", 1)]
        with mock.patch.dict(SCHEMAS, {("plan", 1): (filename, "0" * 64)}):
            with self.assertRaisesRegex(IntegrityError, "digest mismatch"):
                validate_document("plan", support.sample_plan())


if __name__ == "__main__":
    unittest.main()
