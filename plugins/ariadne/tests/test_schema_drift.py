"""The published schema and the validator, held to the same field tables.

Two things describe this predicate: `schemas/solidity-release-v1.json`, which
other producers read, and `predicates/solidity_release.py`, which decides what
this tool accepts. A field added to one and not the other is a disagreement
nobody would notice until somebody else's statement failed here for a reason
their schema said was fine.
"""

import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import core_predicate  # noqa: E402
from ariadne_lib.predicates import solidity_release as release  # noqa: E402

SCHEMA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "schemas",
    "solidity-release-v1.json",
)


def schema():
    with open(SCHEMA, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


class SchemaDriftTests(unittest.TestCase):
    def setUp(self):
        self.schema = schema()
        self.properties = self.schema["properties"]

    def test_the_schema_names_this_predicate_type(self):
        self.assertIn(release.TYPE, self.schema["description"])

    def test_the_top_level_fields_match_the_module(self):
        self.assertEqual(sorted(self.properties), sorted(release.PREDICATE_FIELDS))
        self.assertEqual(self.schema["required"], list(release.REQUIRED_FIELDS))

    def test_the_source_fields_match(self):
        self.assertEqual(
            self.properties["source"]["required"], list(release.SOURCE_REQUIRED)
        )

    def test_the_revision_pattern_matches_the_validator(self):
        """A schema that accepted `main` would send a producer straight into a
        refusal here, which is the drift this test exists to catch."""
        self.assertEqual(
            self.properties["source"]["properties"]["commit"]["pattern"],
            release.REVISION.pattern,
        )
        self.assertEqual(
            self.properties["audits"]["items"]["properties"]["covered_revision"][
                "pattern"
            ],
            release.REVISION.pattern,
        )

    def test_the_build_fields_match(self):
        self.assertEqual(
            self.properties["build"]["required"], list(release.BUILD_REQUIRED)
        )
        self.assertEqual(
            self.properties["build"]["properties"]["optimizer"]["required"],
            list(release.OPTIMIZER_REQUIRED),
        )

    def test_the_release_subject_fields_match(self):
        self.assertEqual(
            self.properties["release_subjects"]["items"]["required"],
            list(release.RELEASE_SUBJECT_REQUIRED),
        )

    def test_the_audit_and_deployment_fields_match(self):
        self.assertEqual(
            self.properties["audits"]["items"]["required"], list(release.AUDIT_REQUIRED)
        )
        self.assertEqual(
            self.properties["deployments"]["items"]["required"],
            list(release.DEPLOYMENT_REQUIRED),
        )

    def test_the_delta_sections_match(self):
        sections = set(self.properties["deltas"]["properties"])
        self.assertEqual(
            sections, set(release.DELTA_SECTIONS) | {"baseline", "current", "reason"}
        )

    def test_the_core_vocabularies_match(self):
        claims = self.properties["claims"]["items"]["properties"]
        commands = self.properties["commands"]["items"]["properties"]
        self.assertEqual(
            claims["disposition"]["enum"], list(core_predicate.DISPOSITIONS)
        )
        self.assertEqual(
            commands["determinism"]["enum"], list(core_predicate.DETERMINISM)
        )
        self.assertEqual(
            sorted(claims), sorted(core_predicate.CLAIM_FIELDS)
        )
        self.assertEqual(
            sorted(commands), sorted(core_predicate.COMMAND_FIELDS)
        )

    def test_the_schema_is_committed_as_readable_json(self):
        with open(SCHEMA, "rb") as handle:
            raw = handle.read()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(
            json.loads(raw.decode("utf-8"))["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )


if __name__ == "__main__":
    unittest.main()
