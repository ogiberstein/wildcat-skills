"""Gates 2 and 5, and the two checks that come with them.

The evidence check gets the most attention here, because it is the one carrying a
rule no other predicate has: a count of proved records is refused when there was
nothing to prove them against.
"""

import hashlib
import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import statement  # noqa: E402
from ariadne_lib.predicates import state_fixture as fixture  # noqa: E402

HEADER = {"sha256": hashlib.sha256(b"header").hexdigest()}
PROOFS = {"sha256": hashlib.sha256(b"proofs").hexdigest()}
RPC = {"sha256": hashlib.sha256(b"rpc").hexdigest()}
ELSEWHERE = {"sha256": hashlib.sha256(b"some other fixture").hexdigest()}
PARAMETERS = {"sha256": hashlib.sha256(b"parameters").hexdigest()}
BLOCK_HASH = "0x" + hashlib.sha256(b"block").hexdigest()
STATE_ROOT = "0x" + hashlib.sha256(b"root").hexdigest()

LAZARUS_MANIFEST_SCHEMA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))),
    "plugins", "lazarus", "schemas", "manifest-v1.json",
)
"""Lazarus's published manifest schema, read by one test below.

A path out of this plugin, which nothing else here does. It resolves only inside
the marketplace checkout; an installed copy of Ariadne alone skips that test
rather than failing it.
"""


def predicate(**overrides):
    out = {
        "chain": {
            "chain_id": 1,
            "block_number": 13097494,
            "block_hash": BLOCK_HASH,
            "state_root": STATE_ROOT,
        },
        "capture": {
            "tool": "lazarus",
            "tool_version": "0.1.0",
            "command": ["python3", "scripts/lazarus.py", "capture"],
            "parameters_digest": PARAMETERS,
        },
        "fixture_subjects": [
            {
                "name": "the captured block header",
                "path": "header.json",
                "digest": HEADER,
                "bytes": 17204,
            },
            {
                "name": "the state proofs",
                "path": "proofs.jsonl",
                "digest": PROOFS,
                "bytes": 8688,
            },
        ],
        "evidence": {"proof_backed": 2, "header_bound": 1, "recorded_rpc": 4},
        "replay": {"reaches_network": False, "canonical_chain_claim": False},
        "deltas": {
            "baseline": None,
            "reason": "first capture of this block; nothing earlier to compare",
        },
        "claims": [],
        "commands": [],
    }
    out.update(overrides)
    return out


def built(body, subject=None):
    return statement.Statement.from_dict(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": subject
            or [
                {"name": "header.json", "digest": HEADER},
                {"name": "proofs.jsonl", "digest": PROOFS},
            ],
            "predicateType": fixture.TYPE,
            "predicate": body,
        }
    )


def gate(number, body, subject=None):
    for found in fixture.check(built(body, subject)):
        if found.number == number:
            return found
    raise AssertionError("no gate %r" % number)


def named(name, body, subject=None):
    for found in fixture.check(built(body, subject)):
        if found.name == name:
            return found
    raise AssertionError("no check named %r" % name)


class GateTwoTests(unittest.TestCase):
    def test_a_complete_pin_and_capture_record_passes(self):
        found = gate(2, predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("chain 1 block 13097494", found.detail)
        self.assertIn("lazarus 0.1.0", found.detail)

    def test_each_pin_field_absent_fails(self):
        for field in fixture.CHAIN_REQUIRED:
            body = predicate()
            del body["chain"][field]
            with self.subTest(field=field):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn(field, found.detail)

    def test_a_hex_block_number_fails(self):
        """The wire form. `"0xc7da16" < "0x2"` is true, because that orders text."""
        body = predicate()
        body["chain"]["block_number"] = "0xc7da16"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("whole number", found.detail)

    def test_a_hex_chain_id_fails(self):
        body = predicate()
        body["chain"]["chain_id"] = "0x1"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("chain_id", found.detail)

    def test_a_boolean_block_number_fails(self):
        """`True` is an integer in Python and would read as block one."""
        body = predicate()
        body["chain"]["block_number"] = True
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("whole number", found.detail)

    def test_genesis_is_a_block(self):
        """`0` lands in `missing()` as though the field were absent."""
        body = predicate()
        body["chain"]["block_number"] = 0
        found = gate(2, body)
        self.assertTrue(found.passed, found.detail)

    def test_an_uppercased_block_hash_fails(self):
        body = predicate()
        body["chain"]["block_hash"] = BLOCK_HASH.upper().replace("0X", "0x")
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("block_hash", found.detail)

    def test_a_block_hash_of_the_wrong_length_fails(self):
        body = predicate()
        body["chain"]["block_hash"] = "0xdeadbeef"
        found = gate(2, body)
        self.assertFalse(found.passed)

    def test_a_state_root_that_is_present_and_malformed_fails(self):
        body = predicate()
        body["chain"]["state_root"] = "0xnope"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("state_root", found.detail)

    def test_a_pin_with_no_state_root_passes_the_gate(self):
        """Whether a fixture needs one depends on what it claims, which is the
        evidence check's rule rather than this gate's."""
        body = predicate()
        del body["chain"]["state_root"]
        body["evidence"] = {"proof_backed": 0, "header_bound": 1, "recorded_rpc": 4}
        found = gate(2, body)
        self.assertTrue(found.passed, found.detail)

    def test_a_pin_carrying_an_undefined_field_fails(self):
        body = predicate()
        body["chain"]["difficulty"] = "0x0"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("difficulty", found.detail)

    def test_each_capture_field_absent_fails(self):
        for field in fixture.CAPTURE_REQUIRED:
            body = predicate()
            del body["capture"][field]
            with self.subTest(field=field):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn(field, found.detail)

    def test_a_capture_command_that_is_a_string_fails(self):
        body = predicate()
        body["capture"]["command"] = "python3 scripts/lazarus.py capture"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("argv", found.detail)

    def test_a_component_digest_the_statement_does_not_cover_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["digest"] = ELSEWHERE
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_no_components_fails(self):
        body = predicate()
        body["fixture_subjects"] = []
        found = gate(2, body)
        self.assertFalse(found.passed)

    def test_an_empty_component_is_a_component(self):
        body = predicate()
        body["fixture_subjects"][1]["bytes"] = 0
        found = gate(2, body)
        self.assertTrue(found.passed, found.detail)

    def test_a_negative_byte_count_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["bytes"] = -1
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("bytes", found.detail)

    def test_a_byte_count_over_the_ceiling_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["bytes"] = fixture.MAX_BYTES + 1
        found = gate(2, body)
        self.assertFalse(found.passed)

    def test_a_component_path_leaving_the_fixture_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["path"] = "../outside.jsonl"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("fixture-relative", found.detail)

    def test_one_path_listed_twice_fails(self):
        body = predicate()
        body["fixture_subjects"][1]["path"] = "header.json"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("listed twice", found.detail)


class EvidenceTests(unittest.TestCase):
    def test_the_three_counts_are_reported(self):
        found = named("evidence", predicate())
        self.assertTrue(found.passed, found.detail)
        for name in fixture.EVIDENCE_CLASSES:
            self.assertIn(name, found.detail)

    def test_each_class_key_absent_fails(self):
        for name in fixture.EVIDENCE_CLASSES:
            body = predicate()
            del body["evidence"][name]
            with self.subTest(evidence_class=name):
                found = named("evidence", body)
                self.assertFalse(found.passed)
                self.assertIn(name, found.detail)

    def test_no_evidence_block_fails(self):
        body = predicate()
        del body["evidence"]
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("records a zero in each class", found.detail)

    def test_a_fixture_that_proved_nothing_records_zeroes(self):
        body = predicate()
        body["evidence"] = {"proof_backed": 0, "header_bound": 0, "recorded_rpc": 0}
        found = named("evidence", body)
        self.assertTrue(found.passed, found.detail)

    def test_a_negative_count_fails(self):
        body = predicate()
        body["evidence"]["recorded_rpc"] = -1
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("from 0 to", found.detail)

    def test_a_boolean_count_fails(self):
        """`True` is an integer in Python, so a check that only asked whether the
        value was a number would read a producer's mistake as one record."""
        for name in fixture.EVIDENCE_CLASSES:
            for value in (True, False):
                body = predicate()
                body["evidence"][name] = value
                with self.subTest(evidence_class=name, value=value):
                    found = named("evidence", body)
                    self.assertFalse(found.passed)
                    self.assertIn(name, found.detail)

    def test_a_count_over_the_ceiling_fails(self):
        """The ceiling comes from Lazarus's manifest schema, and it was in this
        type's published schema before it was in the module. A sweep found the
        gap: a count of 10**30 verified clean and the schema refused it."""
        body = predicate()
        body["evidence"]["recorded_rpc"] = fixture.MAX_COUNT + 1
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("recorded_rpc", found.detail)

    def test_a_count_at_the_ceiling_passes(self):
        body = predicate()
        body["evidence"]["recorded_rpc"] = fixture.MAX_COUNT
        found = named("evidence", body)
        self.assertTrue(found.passed, found.detail)

    def test_a_float_count_fails(self):
        body = predicate()
        body["evidence"]["proof_backed"] = 2.0
        found = named("evidence", body)
        self.assertFalse(found.passed)

    def test_an_undefined_evidence_class_fails(self):
        body = predicate()
        body["evidence"]["trusted_oracle"] = 3
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("trusted_oracle", found.detail)

    def test_proved_records_with_no_state_root_fails(self):
        """The rule this predicate exists for."""
        body = predicate()
        del body["chain"]["state_root"]
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("no state root", found.detail)

    def test_the_rule_reaches_statements_gate_two_accepts(self):
        """Gate 2 used to require the root, which made this rule unreachable: a
        statement it would refuse had already failed the gate. The split is what
        gives the rule something to decide."""
        body = predicate()
        del body["chain"]["state_root"]
        self.assertTrue(gate(2, body).passed, "gate 2 should accept a rootless pin")
        self.assertFalse(named("evidence", body).passed)

    def test_no_proved_records_needs_no_state_root(self):
        body = predicate()
        del body["chain"]["state_root"]
        body["evidence"]["proof_backed"] = 0
        found = named("evidence", body)
        self.assertTrue(found.passed, found.detail)

    def test_proved_records_against_a_malformed_state_root_fails(self):
        """A root that does not parse is not a root to have proved anything
        against, even though gate 2 reports that fault separately."""
        body = predicate()
        body["chain"]["state_root"] = "0xnope"
        found = named("evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("no state root", found.detail)

    def test_a_chain_block_that_is_not_an_object_does_not_raise(self):
        body = predicate()
        body["chain"] = "block 13097494"
        found = named("evidence", body)
        self.assertFalse(found.passed)


class ReplayTests(unittest.TestCase):
    def test_a_closed_boundary_with_no_chain_claim_passes(self):
        found = named("replay", predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("reaches no network", found.detail)

    def test_each_field_absent_fails(self):
        for field in fixture.REPLAY_REQUIRED:
            body = predicate()
            del body["replay"][field]
            with self.subTest(field=field):
                found = named("replay", body)
                self.assertFalse(found.passed)
                self.assertIn(field, found.detail)

    def test_no_replay_block_fails(self):
        body = predicate()
        del body["replay"]
        found = named("replay", body)
        self.assertFalse(found.passed)
        self.assertIn("recorded rather than assumed", found.detail)

    def test_either_field_true_fails_with_the_reason(self):
        for field in fixture.REPLAY_REQUIRED:
            body = predicate()
            body["replay"][field] = True
            with self.subTest(field=field):
                found = named("replay", body)
                self.assertFalse(found.passed)
                self.assertIn(fixture.REFUSALS[field], found.detail)

    def test_a_zero_is_not_a_recorded_decision(self):
        """`0` is falsey and is not in the field's vocabulary. A producer writing
        it has not made the decision the field records."""
        body = predicate()
        body["replay"]["reaches_network"] = 0
        found = named("replay", body)
        self.assertFalse(found.passed)
        self.assertIn("must be false", found.detail)

    def test_a_string_false_fails(self):
        body = predicate()
        body["replay"]["canonical_chain_claim"] = "false"
        found = named("replay", body)
        self.assertFalse(found.passed)

    def test_an_undefined_replay_field_fails(self):
        body = predicate()
        body["replay"]["verified_against_chain"] = False
        found = named("replay", body)
        self.assertFalse(found.passed)
        self.assertIn("verified_against_chain", found.detail)


class GateFiveTests(unittest.TestCase):
    def test_a_first_capture_with_a_null_baseline_passes(self):
        found = gate(5, predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("no baseline", found.detail)

    def test_a_comparison_naming_both_sides_passes(self):
        body = predicate()
        body["deltas"] = {
            "baseline": {"name": "goldfinch-v0", "digest": ELSEWHERE},
            "current": {"name": "goldfinch-v1", "digest": PROOFS},
            "components": {"added": ["traces.jsonl"], "removed": [], "changed": []},
        }
        found = gate(5, body)
        self.assertTrue(found.passed, found.detail)
        self.assertIn("goldfinch-v1 against goldfinch-v0", found.detail)

    def test_an_unnamed_current_side_on_a_null_baseline_fails(self):
        """The branch step 1 of this run closed on the Solidity predicate. This
        type was written over the fixed shape, and the test is here so it stays
        fixed for both."""
        body = predicate()
        body["deltas"]["current"] = {"name": "", "digest": PROOFS}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("current side has no name", found.detail)

    def test_a_current_side_outside_the_statement_fails(self):
        body = predicate()
        body["deltas"]["current"] = {"name": "goldfinch-v1", "digest": ELSEWHERE}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_component_changes_against_a_null_baseline_fail(self):
        body = predicate()
        body["deltas"]["components"] = {"added": ["traces.jsonl"]}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("against a null baseline", found.detail)

    def test_a_changed_entry_naming_one_side_fails(self):
        body = predicate()
        body["deltas"] = {
            "baseline": {"name": "goldfinch-v0", "digest": ELSEWHERE},
            "current": {"name": "goldfinch-v1", "digest": PROOFS},
            "components": {"changed": [{"baseline": "rpc.jsonl"}]},
        }
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("names no current", found.detail)

    def test_an_unknown_delta_section_fails(self):
        body = predicate()
        body["deltas"]["storage"] = {"added": []}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("storage", found.detail)


class ShapeTests(unittest.TestCase):
    def test_a_field_outside_the_shape_fails(self):
        body = predicate()
        body["archive_endpoint"] = "https://example.invalid/rpc"
        found = named("predicate-fields", body)
        self.assertFalse(found.passed)
        self.assertIn("archive_endpoint", found.detail)

    def test_check_returns_a_gate_for_each_thing_it_looks_at(self):
        found = fixture.check(built(predicate()))
        self.assertEqual(
            [(g.number, g.name) for g in found],
            [
                (2, "environment"),
                (5, "deltas"),
                (None, "predicate-fields"),
                (None, "evidence"),
                (None, "replay"),
            ],
        )


class LazarusAgreementTests(unittest.TestCase):
    """The class names are copied from Lazarus. This is what checks the copy.

    Ariadne imports nothing from another plugin at run time, so the names are a
    tuple in this module rather than a shared constant. A rename in Lazarus would
    otherwise go unnoticed here until somebody compared two documents by hand.
    """

    def test_the_class_names_are_the_ones_lazarus_publishes(self):
        if not os.path.isfile(LAZARUS_MANIFEST_SCHEMA):
            self.skipTest("Lazarus is not beside this plugin in this checkout")
        with open(LAZARUS_MANIFEST_SCHEMA, "rb") as handle:
            schema = json.loads(handle.read().decode("utf-8"))
        counts = schema["properties"]["evidence_counts"]
        self.assertEqual(
            sorted(counts["required"]), sorted(fixture.EVIDENCE_CLASSES)
        )
        self.assertEqual(
            sorted(counts["properties"]), sorted(fixture.EVIDENCE_CLASSES)
        )

    def test_the_proved_class_is_one_of_them(self):
        self.assertIn(fixture.PROVED, fixture.EVIDENCE_CLASSES)

    def test_the_ceilings_match_the_ones_lazarus_sets(self):
        if not os.path.isfile(LAZARUS_MANIFEST_SCHEMA):
            self.skipTest("Lazarus is not beside this plugin in this checkout")
        with open(LAZARUS_MANIFEST_SCHEMA, "rb") as handle:
            schema = json.loads(handle.read().decode("utf-8"))
        component = schema["properties"]["components"]["items"]["properties"]
        self.assertEqual(component["bytes"]["maximum"], fixture.MAX_BYTES)
        counts = schema["properties"]["evidence_counts"]["properties"]
        for name in fixture.EVIDENCE_CLASSES:
            with self.subTest(evidence_class=name):
                self.assertEqual(counts[name]["maximum"], fixture.MAX_COUNT)


if __name__ == "__main__":
    unittest.main()
