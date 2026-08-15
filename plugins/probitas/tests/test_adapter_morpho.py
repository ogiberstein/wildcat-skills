"""Morpho Blue, where the collateral answered and a liquidation is not a default."""

import json
import os
import tempfile
import unittest

from . import support

from probitas_lib.adapters import run_adapter  # noqa: E402
from probitas_lib.adapters.morpho import MorphoShapeError, adapter  # noqa: E402

FIXTURES = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")
BORROWER = "0x" + "a1" * 20
SUBJECT = {BORROWER: "declared"}


def collect(case, addresses=None):
    return adapter(
        addresses if addresses is not None else SUBJECT,
        {"fixtures": os.path.join(FIXTURES, case)},
    )


def claims(records):
    out = {}
    for record in records:
        out.setdefault(record.claim, []).append(record)
    return out


def load(case):
    with open(os.path.join(FIXTURES, case, "morpho.json"), encoding="utf-8") as handle:
        return json.load(handle)


class TestSourcing(unittest.TestCase):
    def test_every_record_cites_a_transaction(self):
        for case in ("morpho-clean", "morpho-liquidated", "morpho-bad-debt"):
            records, _ = collect(case)
            self.assertTrue(records, f"{case} produced nothing")
            for record in records:
                with self.subTest(case=case, claim=record.claim):
                    self.assertEqual(record.source_kind, "transaction")


class TestALiquidationIsNotADefault(unittest.TestCase):
    """The distinction this whole adapter exists to hold."""

    def setUp(self):
        self.records, _ = collect("morpho-liquidated")
        self.claims = claims(self.records)

    def test_it_is_recorded_as_a_liquidation(self):
        self.assertIn("liquidation", self.claims)

    def test_it_is_not_recorded_as_a_default_or_a_delinquency(self):
        for wrong in ("default", "delinquency_entered", "bad_debt"):
            self.assertNotIn(wrong, self.claims)

    def test_the_record_says_the_position_was_collateralised(self):
        self.assertTrue(self.claims["liquidation"][0].values["collateralised"])

    def test_it_carries_what_was_repaid_and_seized(self):
        values = self.claims["liquidation"][0].values
        self.assertEqual(values["repaid"], "1200000920")
        self.assertEqual(values["seized_collateral"], "115730723260805373169")

    def test_the_loan_and_the_collateral_keep_their_own_decimals(self):
        """They are different assets. One scale for both is a wrong number."""
        values = self.claims["liquidation"][0].values
        self.assertEqual(values["token_symbol"], "USDC")
        self.assertEqual(values["token_decimals"], "6")
        self.assertEqual(values["collateral_symbol"], "WETH")
        self.assertEqual(values["collateral_decimals"], "18")

    def test_a_market_with_no_collateral_asset_still_records_the_seizure(self):
        import json, tempfile

        payload = load("morpho-liquidated")
        for item in payload["items"]:
            item["market"]["collateralAsset"] = None
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "morpho.json"), "w", encoding="utf-8"
        ) as handle:
            json.dump(payload, handle)
        records, _ = adapter(SUBJECT, {"fixtures": directory.name})
        values = claims(records)["liquidation"][0].values
        self.assertIn("seized_collateral", values)
        self.assertNotIn("collateral_decimals", values)


class TestBadDebtIsTheSignalThatCounts(unittest.TestCase):
    def setUp(self):
        self.records, _ = collect("morpho-bad-debt")
        self.claims = claims(self.records)

    def test_bad_debt_gets_its_own_record(self):
        self.assertIn("bad_debt", self.claims)
        self.assertEqual(self.claims["bad_debt"][0].values["amount"], "1450000000")

    def test_it_cites_the_same_transaction_as_the_liquidation(self):
        self.assertEqual(
            self.claims["bad_debt"][0].source, self.claims["liquidation"][0].source
        )

    def test_a_liquidation_that_covered_the_debt_raises_no_bad_debt(self):
        self.assertNotIn("bad_debt", claims(collect("morpho-liquidated")[0]))


class TestCleanAndEmpty(unittest.TestCase):
    def test_drawing_and_repaying_are_both_recorded(self):
        found = claims(collect("morpho-clean")[0])
        self.assertEqual(len(found["borrow"]), 1)
        self.assertEqual(len(found["repayment"]), 1)
        self.assertNotIn("liquidation", found)

    def test_no_activity_is_empty_and_not_an_error(self):
        records, coverage = collect("morpho-empty")
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "empty")
        self.assertNotEqual(coverage.status, "error")

    def test_coverage_names_where_it_looked(self):
        _, coverage = collect("morpho-clean")
        self.assertEqual(coverage.endpoint, "fixture:morpho-clean")
        self.assertEqual(coverage.block_range, "fixture")

    def test_a_live_run_would_name_the_first_market_block(self):
        from probitas_lib import endpoints

        self.assertEqual(endpoints.MORPHO_BLUE_FIRST_MARKET_BLOCK, 18919623)
        self.assertTrue(endpoints.MORPHO_BLUE_ENDPOINT.startswith("https://"))


class TestSupplySideIsIgnored(unittest.TestCase):
    def test_supplying_to_a_market_produces_no_record(self):
        """Lending says nothing about whether this counterparty repays."""
        records, _ = self.adapt(
            lambda payload: payload["items"].append(
                {
                    "txHash": "0x" + "c1" * 32,
                    "timestamp": 1740500000,
                    "blockNumber": 21950000,
                    "type": "Supply",
                    "user": {"address": BORROWER},
                    "market": {
                        "marketId": "0x" + "ae" * 32,
                        "loanAsset": {"symbol": "USDC", "decimals": 6},
                    },
                    "data": {
                        "__typename": "MarketTransactionTransferData",
                        "assets": "500",
                        "shares": "500",
                    },
                }
            )
        )
        self.assertEqual(len(records), 2)

    def adapt(self, mutate, case="morpho-clean"):
        payload = load(case)
        mutate(payload)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "morpho.json"), "w", encoding="utf-8"
        ) as handle:
            json.dump(payload, handle)
        return adapter(SUBJECT, {"fixtures": directory.name})


class TestMalformedResponses(unittest.TestCase):
    def adapt(self, mutate, case="morpho-bad-debt"):
        payload = load(case)
        mutate(payload)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "morpho.json"), "w", encoding="utf-8"
        ) as handle:
            json.dump(payload, handle)
        return adapter(SUBJECT, {"fixtures": directory.name})

    def test_a_float_amount_raises_rather_than_being_rounded(self):
        """`int(1.5)` is 1 without complaint, and that is a wrong figure with
        a citation attached."""

        def mutate(payload):
            payload["items"][0]["data"]["assets"] = 1.5

        with self.assertRaises(MorphoShapeError):
            self.adapt(mutate)

    def test_an_unknown_transaction_type_raises_rather_than_vanishing(self):
        """A renamed type would otherwise empty the record and read as clean."""

        def mutate(payload):
            payload["items"][0]["type"] = "MarketBorrow"

        with self.assertRaises(MorphoShapeError):
            self.adapt(mutate)

    def test_a_type_this_adapter_ignores_on_purpose_does_not_raise(self):
        def mutate(payload):
            payload["items"][0]["type"] = "SupplyCollateral"

        records, _ = self.adapt(mutate)
        self.assertEqual(len(records), 2)

    def test_a_dropped_field_raises(self):
        def mutate(payload):
            payload["items"][0]["market"].pop("loanAsset")

        with self.assertRaises(MorphoShapeError):
            self.adapt(mutate)

    def test_a_hash_that_is_not_a_hash_raises(self):
        def mutate(payload):
            payload["items"][0]["txHash"] = "0xshort"

        with self.assertRaises(MorphoShapeError):
            self.adapt(mutate)

    def test_a_market_id_that_is_not_one_raises(self):
        def mutate(payload):
            payload["items"][0]["market"]["marketId"] = "Acme | market"

        with self.assertRaises(MorphoShapeError):
            self.adapt(mutate)

    def test_a_transaction_for_someone_else_raises(self):
        def mutate(payload):
            payload["items"][0]["user"]["address"] = "0x" + "b2" * 20

        with self.assertRaises(MorphoShapeError):
            self.adapt(mutate)

    def test_items_not_being_a_list_raises(self):
        def mutate(payload):
            payload["items"] = {"a": 1}

        with self.assertRaises(MorphoShapeError):
            self.adapt(mutate)

    def test_a_failure_surfaces_as_an_error_row_and_not_an_empty_one(self):
        def broken(addresses, config):
            return adapter(addresses, {"fixtures": "/nonexistent"})

        records, coverage = run_adapter("morpho-blue", broken, SUBJECT, {})
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "error")
        self.assertNotEqual(coverage.status, "empty")


class TestTheInterfaceHeld(unittest.TestCase):
    """Adding a second venue should not have moved anything shared."""

    def test_the_adapter_returns_records_and_one_coverage_row(self):
        records, coverage = collect("morpho-clean")
        self.assertIsInstance(records, list)
        self.assertEqual(coverage.venue, "morpho-blue")

    def test_the_registry_flag_matches_the_registered_adapter(self):
        import probitas
        from probitas_lib import registry

        self.assertIn("morpho-blue", probitas.ADAPTERS)
        self.assertEqual(
            {v.id for v in registry.implemented()}, set(probitas.ADAPTERS)
        )


if __name__ == "__main__":
    unittest.main()
