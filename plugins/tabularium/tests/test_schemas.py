"""The versioned JSON Schema documents carry the intended envelope."""

import json
import unittest

from . import support


class SchemaDocumentTests(unittest.TestCase):
    def load(self, name):
        return json.loads((support.PLUGIN_ROOT / "schemas" / name).read_text())

    def test_event_schema_is_draft_2020_12_and_requires_every_dimension(self):
        schema = self.load("canonical-event-v1.json")
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        for key in ("event_family", "action", "chain", "transaction", "parties", "instrument", "asset", "amount", "provenance", "native_record"):
            self.assertIn(key, schema["required"])
        provenance = schema["properties"]["provenance"]
        self.assertIn("source_contract", provenance["required"])
        self.assertEqual(
            provenance["properties"]["source_contract"]["pattern"],
            "^0x[0-9a-f]{40}$",
        )

    def test_coverage_schema_binds_all_three_artifacts_and_unsupported_kinds(self):
        schema = self.load("coverage-manifest-v1.json")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("capture_manifest", schema["required"])
        self.assertIn("unsupported_entities", schema["properties"]["coverage"]["required"])
        unsupported = schema["properties"]["coverage"]["properties"]["unsupported_entities"]
        self.assertEqual(
            set(unsupported["required"]),
            {"_meta", "callableLoans", "creditLines", "tranchedPools"},
        )
        gaps = schema["properties"]["known_gaps"]["const"]
        self.assertEqual(len(gaps), 4)
        self.assertIn(
            "the release is unsigned; offline verification proves internal consistency, not publisher identity or authenticity",
            gaps,
        )

    def test_event_schema_v2_separates_protocol_and_source_api(self):
        schema = self.load("canonical-event-v2.json")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        provenance = schema["properties"]["provenance"]
        self.assertIn("protocol_generation", provenance["required"])
        self.assertIn("source_api", provenance["required"])
        self.assertIn("amounts", schema["required"])
        self.assertIn("debt-transfer", schema["properties"]["event_family"]["enum"])
        self.assertIn("interest-accrual", schema["properties"]["event_family"]["enum"])

    def test_coverage_schema_v2_binds_capture_scope_and_versions(self):
        schema = self.load("coverage-manifest-v2.json")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        self.assertIn("scope", schema["properties"]["source"]["required"])
        self.assertIn("included_events", schema["properties"]["coverage"]["required"])
        self.assertEqual(schema["properties"]["versions"]["properties"]["event_schema"]["const"], 2)
