"""The Euler source capture must not overstate what Goldsky can answer."""

import hashlib
import json
import os
import unittest

from . import support

from probitas_lib import registry  # noqa: E402


SCHEMA = os.path.join(support.PLUGIN_ROOT, "docs", "euler-v2-goldsky-schema.graphql")
SAMPLE = os.path.join(support.PLUGIN_ROOT, "docs", "euler-v2-goldsky-sample.json")
DISCOVERY = os.path.join(support.PLUGIN_ROOT, "docs", "euler-goldsky-discovery.md")
V1_SCHEMA = os.path.join(support.PLUGIN_ROOT, "docs", "euler-v1-thegraph-schema.graphql")
V1_CAPTURE = os.path.join(support.PLUGIN_ROOT, "docs", "euler-v1-thegraph-capture.json")


class TestEulerGoldskyDiscovery(unittest.TestCase):
    def test_the_preserved_schema_is_the_minimal_three_entity_schema(self):
        with open(SCHEMA, encoding="utf-8") as handle:
            schema = handle.read()
        self.assertEqual(schema.count("type "), 3)
        for entity in ("Vault", "TrackingActiveAccount", "TrackingVaultBalance"):
            self.assertIn(f"type {entity} ", schema)
        for event in ("Borrow", "Repay", "Liquidate"):
            self.assertNotIn(f"type {event} ", schema)

    def test_the_sample_carries_a_clean_capture_boundary(self):
        with open(SAMPLE, encoding="utf-8") as handle:
            payload = json.load(handle)
        meta = payload["data"]["_meta"]
        self.assertFalse(meta["hasIndexingErrors"])
        self.assertIsInstance(meta["block"]["number"], int)
        self.assertRegex(meta["block"]["hash"], r"\A0x[0-9a-f]{64}\Z")
        self.assertTrue(meta["deployment"])

    def test_every_sample_position_keeps_exact_integers_and_a_transaction(self):
        with open(SAMPLE, encoding="utf-8") as handle:
            rows = json.load(handle)["data"]["trackingVaultBalances"]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(id=row["id"]):
                self.assertIsInstance(row["debt"], str)
                self.assertGreater(int(row["debt"]), 0)
                self.assertIsInstance(row["blockNumber"], str)
                self.assertIsInstance(row["blockTimestamp"], str)
                self.assertRegex(row["transactionHash"], r"\A0x[0-9a-f]{64}\Z")
                self.assertTrue(row["account"].startswith(row["addressPrefix"]))

    def test_both_versions_have_separate_history_sources(self):
        self.assertTrue(registry.BY_ID["euler"].implemented)
        self.assertTrue(registry.BY_ID["euler-v1"].implemented)
        with open(DISCOVERY, encoding="utf-8") as handle:
            document = handle.read()
        self.assertIn("cannot distinguish never borrowed from fully repaid", document)
        self.assertIn("95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr", document)
        self.assertIn("0x27182842E098f60e3D576794A5bFFb0777E025d3", document)
        self.assertIn("mainnet.gateway.tenderly.co", document)

    def test_the_v1_schema_has_exact_credit_events(self):
        with open(V1_SCHEMA, encoding="utf-8") as handle:
            schema = handle.read()
        for entity in ("Borrow", "Repay", "Liquidate", "Market", "Token"):
            self.assertIn(f"type {entity} ", schema)
        self.assertIn("Amount of token borrowed in native units", schema)
        self.assertIn("Amount of token repaid in native units", schema)

    def test_the_v1_capture_binds_schema_and_current_deployment(self):
        with open(V1_CAPTURE, encoding="utf-8") as handle:
            capture = json.load(handle)
        with open(V1_SCHEMA, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(capture["schemaSha256"], digest)
        self.assertEqual(
            capture["deploymentId"],
            "QmfTzwSoE3krDFMfYT9XTdwLcdMYBmMwyPqA1FHTMkmsVs",
        )
        self.assertNotEqual(capture["deploymentId"], capture["reportedDeploymentId"])
        self.assertEqual(capture["gatewayProbe"]["status"], "error")
        self.assertIsNone(capture["gatewayProbe"]["data"])


if __name__ == "__main__":
    unittest.main()
