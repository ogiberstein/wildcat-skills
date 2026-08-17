"""Euler v1: exact credit events from the canonical mainnet proxy log."""

import copy
import json
import os
import tempfile
import unittest

from . import support

from probitas_lib.adapters import euler_v1, run_adapter  # noqa: E402


FIXTURES = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")
BORROWER = "0x" + "a1" * 20
SUBJECT = {BORROWER: "declared"}


def collect(case="euler-borrower", addresses=None):
    return euler_v1.adapter(
        addresses if addresses is not None else SUBJECT,
        {"fixtures": os.path.join(FIXTURES, case)},
    )


def claims(records):
    return {record.claim: record for record in records}


def fixture():
    with open(
        os.path.join(FIXTURES, "euler-borrower", "euler-v1.json"),
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def mutated(payload):
    directory = tempfile.TemporaryDirectory()
    with open(
        os.path.join(directory.name, "euler-v1.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(payload, handle)
    return directory


class TestItReadsTheCanonicalLog(unittest.TestCase):
    def test_it_records_borrows_repayments_and_liquidations(self):
        records, _ = collect()
        self.assertEqual(
            [record.claim for record in records],
            ["borrow", "repayment", "liquidation"],
        )

    def test_it_preserves_exact_integer_amounts_and_token_scales(self):
        found = claims(collect()[0])
        self.assertEqual(found["borrow"].values["amount"], "1000")
        self.assertEqual(found["repayment"].values["amount"], "400")
        self.assertEqual(found["liquidation"].values["repaid"], "600")
        self.assertEqual(found["liquidation"].values["seized_collateral"], "700")
        self.assertEqual(found["borrow"].values["debt_decimals"], "6")
        self.assertEqual(found["liquidation"].values["collateral_decimals"], "18")

    def test_every_record_cites_its_own_transaction(self):
        records, _ = collect()
        self.assertEqual(
            [record.source for record in records],
            ["0x" + "11" * 32, "0x" + "22" * 32, "0x" + "33" * 32],
        )
        self.assertTrue(all(record.source_kind == "transaction" for record in records))

    def test_liquidation_keeps_both_assets_and_the_liquidator(self):
        liquidation = claims(collect()[0])["liquidation"]
        self.assertEqual(liquidation.values["debt_token"], "0x" + "a2" * 20)
        self.assertEqual(liquidation.values["collateral_token"], "0x" + "a3" * 20)
        self.assertEqual(liquidation.values["liquidator"], "0x" + "a4" * 20)
        self.assertTrue(liquidation.values["collateralised"])

    def test_block_hashes_bind_logs_to_timestamped_blocks(self):
        records, _ = collect()
        self.assertEqual([record.block for record in records], [14531589, 14531590, 14531591])
        self.assertEqual(
            [record.observed_at for record in records],
            [1649170000, 1649170012, 1649170024],
        )

    def test_empty_is_a_checked_finding(self):
        records, coverage = collect("euler-empty")
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "empty")
        self.assertIn("finalized block 18000000", coverage.note)

    def test_registry_and_cli_ship_the_adapter(self):
        import probitas
        from probitas_lib import registry

        self.assertTrue(registry.BY_ID["euler-v1"].implemented)
        self.assertIn("euler-v1", probitas.ADAPTERS)


class TestItFailsClosed(unittest.TestCase):
    def assert_rejected(self, payload, text):
        directory = mutated(payload)
        self.addCleanup(directory.cleanup)
        records, coverage = run_adapter(
            "euler-v1",
            euler_v1.adapter,
            SUBJECT,
            {"fixtures": directory.name},
        )
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "error")
        self.assertIn(text, coverage.note)

    def test_a_removed_log_is_not_evidence(self):
        payload = fixture()
        payload["logs"][0]["removed"] = True
        self.assert_rejected(payload, "removed")

    def test_a_log_for_another_account_is_not_silently_skipped(self):
        payload = fixture()
        payload["logs"][0]["topics"][2] = "0x" + "00" * 12 + "b1" * 20
        self.assert_rejected(payload, "unrequested account")

    def test_a_proxy_mismatch_is_rejected(self):
        payload = fixture()
        payload["logs"][0]["address"] = "0x" + "b2" * 20
        self.assert_rejected(payload, "not emitted by the Euler v1 proxy")

    def test_a_block_hash_mismatch_is_rejected(self):
        payload = fixture()
        payload["blocks"][0]["hash"] = "0x" + "dd" * 32
        self.assert_rejected(payload, "block hash disagrees")

    def test_missing_token_metadata_is_rejected(self):
        payload = fixture()
        payload["tokens"] = []
        self.assert_rejected(payload, "no token metadata")

    def test_duplicate_transaction_log_identity_is_rejected(self):
        payload = fixture()
        payload["logs"].append(copy.deepcopy(payload["logs"][0]))
        self.assert_rejected(payload, "duplicate Euler v1 log")

    def test_a_partial_liquidation_payload_is_rejected(self):
        payload = fixture()
        payload["logs"][2]["data"] = payload["logs"][2]["data"][:-64]
        self.assert_rejected(payload, "exactly 6 ABI word")


class TestAbiMetadata(unittest.TestCase):
    def test_symbol_accepts_bytes32_and_dynamic_strings(self):
        bytes32 = "0x" + b"USDC".ljust(32, b"\0").hex()
        dynamic = "0x" + (32).to_bytes(32, "big").hex()
        dynamic += (4).to_bytes(32, "big").hex() + b"WETH".ljust(32, b"\0").hex()
        self.assertEqual(euler_v1._decode_symbol(bytes32, "symbol"), "USDC")
        self.assertEqual(euler_v1._decode_symbol(dynamic, "symbol"), "WETH")

    def test_decimals_refuses_values_outside_uint8(self):
        with self.assertRaises(euler_v1.EulerV1ShapeError):
            euler_v1._decode_decimals("0x" + f"{256:064x}", "decimals")


if __name__ == "__main__":
    unittest.main()
