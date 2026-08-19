"""The published schemas and the validators, held to the same field tables.

Two things describe each predicate: the schema under `schemas/`, which other
producers read, and the module under `predicates/`, which decides what this tool
accepts. A field added to one and not the other is a disagreement nobody would
notice until somebody else's statement failed here for a reason their schema said
was fine.

Every shipped predicate needs a schema and a drift class. The completeness test
at the bottom fails when one ships without them.
"""

import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import core_predicate  # noqa: E402
from ariadne_lib import registry  # noqa: E402
from ariadne_lib.predicates import dataset  # noqa: E402
from ariadne_lib.predicates import solidity_release as release  # noqa: E402

SCHEMAS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas"
)
SCHEMA = os.path.join(SCHEMAS, "solidity-release-v1.json")
DATASET_SCHEMA = os.path.join(SCHEMAS, "dataset-v1.json")

SHIPPED = ((release, SCHEMA), (dataset, DATASET_SCHEMA))
"""Each shipped predicate and its published schema."""


def read_schema(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def schema():
    return read_schema(SCHEMA)


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


class DatasetSchemaDriftTests(unittest.TestCase):
    def setUp(self):
        self.schema = read_schema(DATASET_SCHEMA)
        self.properties = self.schema["properties"]

    def test_the_schema_names_this_predicate_type(self):
        self.assertIn(dataset.TYPE, self.schema["description"])

    def test_the_top_level_fields_match_the_module(self):
        self.assertEqual(sorted(self.properties), sorted(dataset.PREDICATE_FIELDS))
        self.assertEqual(self.schema["required"], list(dataset.REQUIRED_FIELDS))

    def test_the_producer_fields_match(self):
        self.assertEqual(
            self.properties["producer"]["required"], list(dataset.PRODUCER_REQUIRED)
        )

    def test_the_input_fields_match(self):
        self.assertEqual(
            self.properties["inputs"]["items"]["required"], list(dataset.INPUT_REQUIRED)
        )
        self.assertEqual(
            sorted(self.properties["inputs"]["items"]["properties"]),
            sorted(dataset.INPUT_FIELDS),
        )

    def test_the_released_file_fields_match(self):
        self.assertEqual(
            self.properties["dataset_subjects"]["items"]["required"],
            list(dataset.DATASET_SUBJECT_REQUIRED),
        )

    def test_the_coverage_and_gap_fields_match(self):
        self.assertEqual(
            self.properties["coverage"]["required"], list(dataset.COVERAGE_KEYS)
        )
        gap = self.properties["coverage"]["properties"]["gaps"]["items"]
        self.assertEqual(gap["required"], list(dataset.GAP_REQUIRED))
        self.assertEqual(sorted(gap["properties"]), sorted(dataset.GAP_FIELDS))

    def test_the_delta_sections_match(self):
        sections = set(self.properties["deltas"]["properties"])
        self.assertEqual(
            sections, set(dataset.DELTA_SECTIONS) | {"baseline", "current", "reason"}
        )

    def test_the_both_sided_sections_require_both_sides(self):
        records = self.properties["deltas"]["properties"]["records"]["properties"]
        for section in dataset.BOTH_SIDED:
            with self.subTest(section=section):
                self.assertEqual(
                    records[section]["items"]["required"], ["baseline", "current"]
                )

    def test_the_coverage_bounds_are_integers(self):
        """The module refuses a bound that is not a whole number, so a schema
        allowing a string would send a producer straight into a refusal here."""
        coverage = self.properties["coverage"]["properties"]
        for field in ("start", "end"):
            with self.subTest(field=field):
                self.assertEqual(coverage[field]["type"], "integer")
        gap = coverage["gaps"]["items"]["properties"]
        for field in ("start", "end"):
            with self.subTest(gap_field=field):
                self.assertEqual(gap[field]["type"], "integer")
        self.assertEqual(
            self.properties["dataset_subjects"]["items"]["properties"]["record_count"][
                "type"
            ],
            "integer",
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
        self.assertEqual(sorted(claims), sorted(core_predicate.CLAIM_FIELDS))
        self.assertEqual(sorted(commands), sorted(core_predicate.COMMAND_FIELDS))
        self.assertEqual(
            self.properties["inputs"]["items"]["properties"]["disposition"]["enum"],
            list(core_predicate.DISPOSITIONS),
        )

    def test_the_schema_is_committed_as_readable_json(self):
        with open(DATASET_SCHEMA, "rb") as handle:
            raw = handle.read()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(
            json.loads(raw.decode("utf-8"))["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )


class CompletenessTests(unittest.TestCase):
    def test_every_registered_predicate_ships_a_schema_this_file_checks(self):
        """A predicate registered without a published schema, or with one nothing
        compares against the module, is the drift this file exists to prevent."""
        from ariadne_lib import predicates  # noqa: F401

        registered = {type_uri for type_uri, _ in registry.DEFAULT.entries()}
        covered = {module.TYPE for module, _ in SHIPPED}
        self.assertEqual(registered, covered)
        for module, path in SHIPPED:
            with self.subTest(predicate=module.TYPE):
                self.assertTrue(os.path.isfile(path), path)
                self.assertIn(module.TYPE, read_schema(path)["description"])


if __name__ == "__main__":
    unittest.main()
