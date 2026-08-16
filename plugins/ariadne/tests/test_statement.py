"""Statement v1: what it refuses, and that subjects match by digest."""

import hashlib
import json
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import safejson, statement  # noqa: E402

DIGEST_A = hashlib.sha256(b"a").hexdigest()
DIGEST_B = hashlib.sha256(b"b").hexdigest()
TYPE = "https://ariadne.wildcat.finance/example/v1"


def raw(subject=None, predicate_type=TYPE, predicate=None, type_field=None):
    out = {
        "_type": statement.STATEMENT_TYPE if type_field is None else type_field,
        "subject": subject
        if subject is not None
        else [{"name": "a", "digest": {"sha256": DIGEST_A}}],
        "predicateType": predicate_type,
    }
    if predicate is not None:
        out["predicate"] = predicate
    return out


class ParsingTests(unittest.TestCase):
    def test_a_well_formed_statement_parses(self):
        found = statement.Statement.from_dict(raw(predicate={"any": "thing"}))
        self.assertEqual(found.predicate_type, TYPE)
        self.assertEqual(found.predicate, {"any": "thing"})
        self.assertEqual(len(found.subjects), 1)

    def test_the_type_must_be_the_in_toto_statement_v1_uri(self):
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(
                raw(type_field="https://in-toto.io/Statement/v0.1")
            )
        self.assertIn("_type", str(caught.exception))

    def test_a_subject_without_a_digest_is_refused(self):
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(raw(subject=[{"name": "a"}]))
        self.assertIn("no digest", str(caught.exception))

    def test_a_subject_with_a_short_digest_is_refused(self):
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(
                raw(subject=[{"name": "a", "digest": {"sha256": DIGEST_A[:20]}}])
            )
        self.assertIn("expected 64", str(caught.exception))

    def test_a_subject_with_an_uppercase_digest_is_refused(self):
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(
                raw(subject=[{"name": "a", "digest": {"sha256": DIGEST_A.upper()}}])
            )
        self.assertIn("lowercase", str(caught.exception))

    def test_a_subject_with_an_empty_digest_set_is_refused(self):
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(raw(subject=[{"name": "a", "digest": {}}]))
        self.assertIn("empty", str(caught.exception))

    def test_an_empty_subject_array_is_refused(self):
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(raw(subject=[]))
        self.assertIn("non-empty", str(caught.exception))

    def test_a_predicate_type_that_is_not_a_uri_is_refused(self):
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(raw(predicate_type="solidity-release"))
        self.assertIn("type URI", str(caught.exception))

    def test_a_predicate_that_is_not_an_object_is_refused(self):
        with self.assertRaises(statement.StatementError):
            statement.Statement.from_dict(raw(predicate=["not", "an", "object"]))

    def test_broken_json_is_refused_with_a_message(self):
        with self.assertRaises(safejson.InputError) as caught:
            statement.Statement.from_json(b"{not json")
        self.assertIn("not valid JSON", str(caught.exception))

    def test_non_utf8_bytes_are_refused(self):
        with self.assertRaises(safejson.InputError) as caught:
            statement.Statement.from_json(b"\xff\xfe{}")
        self.assertIn("UTF-8", str(caught.exception))


class UnknownFieldTests(unittest.TestCase):
    def test_a_field_statement_v1_does_not_define_is_refused(self):
        document = raw()
        document["predicate_type"] = "https://example.test/typo/v1"
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(document)
        self.assertIn("predicate_type", str(caught.exception))

    def test_a_subject_field_outside_the_descriptor_shape_is_refused(self):
        with self.assertRaises(statement.StatementError) as caught:
            statement.Statement.from_dict(
                raw(
                    subject=[
                        {"name": "a", "digest": {"sha256": DIGEST_A}, "verdict": "safe"}
                    ]
                )
            )
        self.assertIn("verdict", str(caught.exception))

    def test_descriptor_fields_this_tool_ignores_are_carried_not_dropped(self):
        """Re-emitting a subject without its uri would hand on a different
        document from the one that was signed."""
        subject = {
            "name": "a",
            "digest": {"sha256": DIGEST_A},
            "uri": "pkg:github/wildcat-finance/ariadne@v1",
            "mediaType": "application/json",
        }
        found = statement.Statement.from_dict(raw(subject=[subject]))
        self.assertEqual(found.to_dict()["subject"][0], subject)


class MatchingTests(unittest.TestCase):
    def test_subjects_match_by_digest_across_differing_names(self):
        found = statement.Statement.from_dict(
            raw(subject=[{"name": "out/Escrow.sol/Escrow.json", "digest": {"sha256": DIGEST_A}}])
        )
        matched = found.subject_for({"sha256": DIGEST_A})
        self.assertIsNotNone(matched)
        self.assertEqual(matched.name, "out/Escrow.sol/Escrow.json")

    def test_the_same_name_with_a_different_digest_does_not_match(self):
        found = statement.Statement.from_dict(
            raw(subject=[{"name": "a", "digest": {"sha256": DIGEST_A}}])
        )
        self.assertIsNone(found.subject_for({"sha256": DIGEST_B}))
        self.assertFalse(found.covers({"sha256": DIGEST_B}))

    def test_an_unnamed_subject_is_allowed(self):
        found = statement.Statement.from_dict(
            raw(subject=[{"digest": {"sha256": DIGEST_A}}])
        )
        self.assertTrue(found.covers({"sha256": DIGEST_A}))
        self.assertIsNone(found.subjects[0].name)


class SerialisationTests(unittest.TestCase):
    def test_round_trip_preserves_the_document(self):
        original = raw(predicate={"claims": []})
        found = statement.Statement.from_dict(original)
        self.assertEqual(json.loads(found.to_json()), original)

    def test_a_predicate_absent_stays_absent(self):
        found = statement.Statement.from_dict(raw())
        self.assertNotIn("predicate", found.to_dict())


if __name__ == "__main__":
    unittest.main()
