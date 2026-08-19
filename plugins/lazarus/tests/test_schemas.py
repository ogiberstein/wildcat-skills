"""The six versioned formats validate before they reach fixture logic."""

import copy
import unittest
from unittest import mock

from lazarus_lib.errors import FormatError, IntegrityError, PathError
from lazarus_lib.records import make_rpc_record
from lazarus_lib.schemas import SCHEMAS, validate_builtin_schemas, validate_document

from . import support


class SchemaTests(unittest.TestCase):
    def test_every_registered_schema_is_valid_and_digest_pinned(self):
        validate_builtin_schemas()
        self.assertEqual(
            {kind for kind, version in SCHEMAS if version == 1},
            {"plan", "header", "rpc-record", "proof-record", "manifest", "release"},
        )

    def test_a_well_formed_release_document_passes(self):
        validate_document("release", support.sample_release())

    def test_a_release_missing_any_required_field_fails(self):
        for field in (
            "schema_version",
            "tool_version",
            "fixture",
            "statement",
            "verified",
            "binding",
            "release_digest",
        ):
            document = support.sample_release()
            del document[field]
            with self.subTest(field=field), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_a_release_carrying_an_undefined_field_fails(self):
        document = support.sample_release()
        document["signed_by"] = "somebody"
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_claiming_the_canonical_chain_fails(self):
        """A self-consistent header is not proof that it belongs to Ethereum's
        canonical chain, and nothing in a release establishes that it does. The
        field is pinned to false rather than merely required."""
        document = support.sample_release()
        document["verified"]["canonical_chain_claim"] = True
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_missing_a_verified_count_fails(self):
        for name in ("proof_backed", "header_bound", "recorded_rpc"):
            document = support.sample_release()
            del document["verified"]["evidence_counts"][name]
            with self.subTest(evidence_class=name), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_a_release_with_a_boolean_count_fails(self):
        """`True` is an integer in Python and JSON Schema separates the two, so
        this is the schema being asked rather than assumed."""
        document = support.sample_release()
        document["verified"]["evidence_counts"]["proof_backed"] = True
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_with_no_named_binding_check_fails(self):
        """A release that establishes nothing should not be able to say so by
        omission."""
        document = support.sample_release()
        document["binding"]["checks"] = []
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_release_with_a_malformed_digest_fails(self):
        for value in ("", "beef", "0x" + "a" * 64, "A" * 64, 12345):
            document = support.sample_release()
            document["release_digest"] = value
            with self.subTest(release_digest=value), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_a_release_path_that_leaves_the_release_fails(self):
        for value in ("../elsewhere", "/etc/passwd", "a\\b", "a/../b", "", "./a"):
            document = support.sample_release()
            document["statement"]["path"] = value
            with self.subTest(path=value), self.assertRaises(
                (FormatError, PathError)
            ):
                validate_document("release", document)

    def test_a_release_string_that_renders_as_nothing_fails(self):
        """Every string field in a release is read by somebody. A value that
        satisfies a length check and displays as empty is the shape this
        marketplace keeps meeting, so the schema asks for one visible
        character rather than one character."""
        BLANK = ("   ", " ", "\t", "\u200b")
        for value in BLANK:
            for dotted in (
                ("fixture", "path"),
                ("statement", "path"),
                ("statement", "predicate_type"),
            ):
                document = support.sample_release()
                document[dotted[0]][dotted[1]] = value
                with self.subTest(field="/".join(dotted), value=value):
                    with self.assertRaises((FormatError, PathError)):
                        validate_document("release", document)
            document = support.sample_release()
            document["binding"]["checks"] = [value]
            with self.subTest(field="binding/checks", value=value):
                with self.assertRaises(FormatError):
                    validate_document("release", document)

    def test_a_predicate_type_that_is_not_a_uri_fails(self):
        for value in ("state-fixture", "   ", "//x", "1https://x", "https:"):
            document = support.sample_release()
            document["statement"]["predicate_type"] = value
            with self.subTest(predicate_type=value), self.assertRaises(FormatError):
                validate_document("release", document)

    def test_a_path_with_a_space_inside_it_is_still_a_path(self):
        """Refusing every space would refuse a legitimate filename."""
        document = support.sample_release()
        document["statement"]["path"] = "a statement.json"
        validate_document("release", document)

    def test_a_release_whose_statement_is_its_fixture_fails(self):
        document = support.sample_release()
        document["statement"]["path"] = document["fixture"]["path"]
        with self.assertRaises(FormatError):
            validate_document("release", document)

    def test_a_statement_inside_the_fixture_fails(self):
        """The fixture digest would otherwise cover the statement made about
        it, which makes the statement part of its own subject."""
        document = support.sample_release()
        document["statement"]["path"] = "fixture/statement.json"
        with self.assertRaises(FormatError):
            validate_document("release", document)

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
