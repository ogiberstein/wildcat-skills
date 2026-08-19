"""Whether a statement describes this fixture, and whether it claims more.

The evidence tests carry the weight. Everything else here keeps a statement from
being bound to the wrong capture; those keep it from being bound to the right one
while saying something the records do not support.
"""

import copy
import unittest

from lazarus_lib.binding import CHECKS, EVIDENCE_CLASSES, STATE_FIXTURE_TYPE, bind
from lazarus_lib.errors import FormatError, IntegrityError

BLOCK_HASH = "0x" + "41" * 32


def sample_manifest():
    return {
        "components": [
            {"path": "header.json", "bytes": 17204, "sha256": "a" * 64},
            {"path": "plan.json", "bytes": 1418, "sha256": "b" * 64},
            {"path": "proofs.jsonl", "bytes": 8688, "sha256": "c" * 64},
        ]
    }


def sample_report():
    """What `verify_fixture` returns, in the shape it returns it."""
    return {
        "fixture_digest": "d" * 64,
        "block_hash": BLOCK_HASH,
        "evidence_counts": {"proof_backed": 2, "header_bound": 1, "recorded_rpc": 4},
        "proof_backed": {
            "accounts_included": 1,
            "accounts_absent": 0,
            "storage_included": 1,
            "storage_absent": 0,
        },
        "header_bound": {"headers": 1, "canonical_chain_claim": False},
        "recorded_rpc": {"records": 4, "optional_failures": 0},
    }


def sample_statement():
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": STATE_FIXTURE_TYPE,
        "predicate": {
            "chain": {
                "chain_id": 1,
                "block_number": 13097494,
                "block_hash": BLOCK_HASH,
                "state_root": "0x" + "0f" * 32,
            },
            "evidence": {
                "proof_backed": 2,
                "header_bound": 1,
                "recorded_rpc": 4,
            },
            "replay": {"reaches_network": False, "canonical_chain_claim": False},
            "fixture_subjects": [
                {
                    "name": "header.json",
                    "path": "header.json",
                    "digest": {"sha256": "a" * 64},
                    "bytes": 17204,
                },
                {
                    "name": "plan.json",
                    "path": "plan.json",
                    "digest": {"sha256": "b" * 64},
                    "bytes": 1418,
                },
                {
                    "name": "proofs.jsonl",
                    "path": "proofs.jsonl",
                    "digest": {"sha256": "c" * 64},
                    "bytes": 8688,
                },
            ],
        },
    }


def bound(statement=None, manifest=None, report=None):
    return bind(
        statement if statement is not None else sample_statement(),
        manifest if manifest is not None else sample_manifest(),
        report if report is not None else sample_report(),
    )


class CleanBindingTests(unittest.TestCase):
    def test_a_statement_over_this_fixture_binds(self):
        self.assertEqual(bound(), list(CHECKS))

    def test_the_checks_it_returns_are_the_ones_it_names(self):
        """The names go into the release document, so a reader learns which
        questions were asked rather than inferring them from the release."""
        made = bound()
        self.assertEqual(made, list(CHECKS))
        self.assertEqual(len(set(made)), len(made))
        for name in made:
            self.assertTrue(name and name.strip())

    def test_a_block_hash_in_the_other_case_still_binds(self):
        """Two spellings of one value. Lazarus writes lowercase and a producer
        may not."""
        statement = sample_statement()
        statement["predicate"]["chain"]["block_hash"] = BLOCK_HASH.upper().replace(
            "0X", "0x"
        )
        self.assertEqual(bound(statement), list(CHECKS))


class EvidenceTests(unittest.TestCase):
    """The rule this module exists for."""

    def test_a_statement_claiming_more_proved_records_is_refused(self):
        """The study's case, and the one the held job names. Four recorded RPC
        responses moved into the proved column."""
        statement = sample_statement()
        statement["predicate"]["evidence"] = {
            "proof_backed": 6,
            "header_bound": 1,
            "recorded_rpc": 0,
        }
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        message = str(caught.exception)
        self.assertIn("proof_backed", message)
        self.assertIn("6", message)
        self.assertIn("2", message)
        self.assertIn("more than the records support", message)

    def test_each_class_disagreeing_upward_is_refused(self):
        for name in EVIDENCE_CLASSES:
            statement = sample_statement()
            statement["predicate"]["evidence"][name] += 1
            with self.subTest(evidence_class=name), self.assertRaises(IntegrityError):
                bound(statement)

    def test_each_class_disagreeing_downward_is_refused(self):
        """Understating is wrong too. It describes a fixture nobody has, and the
        next reader cannot tell which of the two documents is the mistake."""
        for name in EVIDENCE_CLASSES:
            statement = sample_statement()
            statement["predicate"]["evidence"][name] -= 1
            with self.subTest(evidence_class=name), self.assertRaises(
                IntegrityError
            ) as caught:
                bound(statement)
            self.assertIn("fewer than the records support", str(caught.exception))

    def test_a_class_left_out_is_refused(self):
        for name in EVIDENCE_CLASSES:
            statement = sample_statement()
            del statement["predicate"]["evidence"][name]
            with self.subTest(evidence_class=name), self.assertRaises(
                IntegrityError
            ) as caught:
                bound(statement)
            self.assertIn(name, str(caught.exception))

    def test_a_class_the_fixture_does_not_have_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["evidence"]["trusted_oracle"] = 3
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("trusted_oracle", str(caught.exception))

    def test_a_boolean_count_is_refused(self):
        """`True` is an integer in Python and equals 1, so a header-bound count
        of `true` would compare equal to the verified 1 and bind."""
        statement = sample_statement()
        statement["predicate"]["evidence"]["header_bound"] = True
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("whole number", str(caught.exception))

    def test_a_float_count_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["evidence"]["proof_backed"] = 2.0
        with self.assertRaises(IntegrityError):
            bound(statement)

    def test_zero_everywhere_binds_when_the_fixture_proved_nothing(self):
        statement = sample_statement()
        report = sample_report()
        for name in EVIDENCE_CLASSES:
            statement["predicate"]["evidence"][name] = 0
            report["evidence_counts"][name] = 0
        self.assertEqual(bound(statement, report=report), list(CHECKS))

    def test_the_counts_come_from_the_report_and_not_the_manifest(self):
        """The whole point. A manifest carrying inflated counts changes nothing,
        because the binding never reads them."""
        manifest = sample_manifest()
        manifest["evidence_counts"] = {
            "proof_backed": 6,
            "header_bound": 1,
            "recorded_rpc": 0,
        }
        self.assertEqual(bound(manifest=manifest), list(CHECKS))

    def test_an_evidence_block_that_is_not_an_object_is_refused(self):
        for value in (None, [], "2", 2, True):
            statement = sample_statement()
            statement["predicate"]["evidence"] = value
            with self.subTest(evidence=value), self.assertRaises(FormatError):
                bound(statement)


class PredicateTypeTests(unittest.TestCase):
    def test_another_type_is_refused(self):
        statement = sample_statement()
        statement["predicateType"] = "https://ariadne.wildcat.finance/dataset/v1"
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("has not read", str(caught.exception))

    def test_a_type_that_names_nothing_is_refused(self):
        for value in (None, "", "   ", 12345, [], "​"):
            statement = sample_statement()
            statement["predicateType"] = value
            with self.subTest(predicate_type=repr(value)), self.assertRaises(
                FormatError
            ):
                bound(statement)

    def test_a_statement_with_no_type_is_refused(self):
        statement = sample_statement()
        del statement["predicateType"]
        with self.assertRaises(FormatError):
            bound(statement)


class BlockTests(unittest.TestCase):
    def test_a_different_block_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["chain"]["block_hash"] = "0x" + "99" * 32
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("different capture", str(caught.exception))

    def test_a_block_hash_that_is_not_a_string_is_refused(self):
        for value in (None, 12345, [], {}, True):
            statement = sample_statement()
            statement["predicate"]["chain"]["block_hash"] = value
            with self.subTest(block_hash=value), self.assertRaises(IntegrityError):
                bound(statement)

    def test_a_statement_with_no_chain_is_refused(self):
        statement = sample_statement()
        del statement["predicate"]["chain"]
        with self.assertRaises(FormatError):
            bound(statement)


class CanonicalChainTests(unittest.TestCase):
    def test_a_statement_claiming_the_canonical_chain_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["replay"]["canonical_chain_claim"] = True
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("canonical", str(caught.exception))

    def test_a_claim_that_is_not_a_boolean_is_refused(self):
        """`0` is falsey and is not the recorded decision the field carries."""
        for value in (0, 1, "false", None, [], "no"):
            statement = sample_statement()
            statement["predicate"]["replay"]["canonical_chain_claim"] = value
            with self.subTest(claim=value), self.assertRaises(IntegrityError):
                bound(statement)

    def test_a_report_claiming_the_canonical_chain_is_refused(self):
        """No Lazarus build establishes it, so a report saying otherwise is not
        one this binding will build a release on."""
        report = sample_report()
        report["header_bound"]["canonical_chain_claim"] = True
        with self.assertRaises(IntegrityError):
            bound(report=report)

    def test_a_statement_with_no_replay_block_is_refused(self):
        statement = sample_statement()
        del statement["predicate"]["replay"]
        with self.assertRaises(FormatError):
            bound(statement)


class ComponentTests(unittest.TestCase):
    def test_a_component_the_fixture_does_not_hold_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"].append(
            {
                "name": "extra.json",
                "path": "extra.json",
                "digest": {"sha256": "e" * 64},
                "bytes": 10,
            }
        )
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("extra.json", str(caught.exception))
        self.assertIn("does not hold", str(caught.exception))

    def test_a_component_the_statement_omits_is_refused(self):
        """The silent absence this plugin refuses everywhere else."""
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"] = [
            entry
            for entry in statement["predicate"]["fixture_subjects"]
            if entry["path"] != "plan.json"
        ]
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("plan.json", str(caught.exception))
        self.assertIn("does not name", str(caught.exception))

    def test_a_digest_that_disagrees_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"][1]["digest"]["sha256"] = "f" * 64
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("plan.json", str(caught.exception))

    def test_a_byte_count_that_disagrees_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"][1]["bytes"] += 1
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("bytes", str(caught.exception))

    def test_a_boolean_byte_count_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"][1]["bytes"] = True
        with self.assertRaises(IntegrityError):
            bound(statement)

    def test_a_component_named_twice_is_refused(self):
        statement = sample_statement()
        statement["predicate"]["fixture_subjects"].append(
            copy.deepcopy(statement["predicate"]["fixture_subjects"][0])
        )
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("twice", str(caught.exception))

    def test_a_path_that_names_nothing_is_refused(self):
        for value in ("", "   ", None, 12345, "​"):
            statement = sample_statement()
            statement["predicate"]["fixture_subjects"][0]["path"] = value
            with self.subTest(path=repr(value)), self.assertRaises(FormatError):
                bound(statement)

    def test_no_components_at_all_is_refused(self):
        for value in ([], None, {}, "header.json"):
            statement = sample_statement()
            statement["predicate"]["fixture_subjects"] = value
            with self.subTest(subjects=value), self.assertRaises(FormatError):
                bound(statement)

    def test_a_digest_block_that_is_not_an_object_is_refused(self):
        for value in (None, "a" * 64, [], 12345):
            statement = sample_statement()
            statement["predicate"]["fixture_subjects"][0]["digest"] = value
            with self.subTest(digest=value), self.assertRaises(FormatError):
                bound(statement)


class ShapeTests(unittest.TestCase):
    def test_a_statement_that_is_not_an_object_is_refused(self):
        """`bind` is called directly here. The helper above substitutes the
        sample when it is handed `None`, so going through it would have tested
        the helper rather than the rule."""
        for value in (None, [], "statement", 12345, True):
            with self.subTest(statement=value), self.assertRaises(FormatError):
                bind(value, sample_manifest(), sample_report())

    def test_a_predicate_that_is_not_an_object_is_refused(self):
        for value in (None, [], "predicate", 12345):
            statement = sample_statement()
            statement["predicate"] = value
            with self.subTest(predicate=value), self.assertRaises(FormatError):
                bound(statement)

    def test_a_statement_with_no_predicate_is_refused(self):
        statement = sample_statement()
        del statement["predicate"]
        with self.assertRaises(FormatError):
            bound(statement)

    def test_it_refuses_at_the_first_disagreement(self):
        """A statement that disagrees about the block it pins is not a document
        whose component list is worth reading."""
        statement = sample_statement()
        statement["predicate"]["chain"]["block_hash"] = "0x" + "99" * 32
        statement["predicate"]["fixture_subjects"] = []
        with self.assertRaises(IntegrityError) as caught:
            bound(statement)
        self.assertIn("different capture", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
