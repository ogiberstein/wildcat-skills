"""The Wildcat adapter, against the three synthetic borrower histories."""

import copy
import json
import os
import tempfile
import unittest

from . import support

from probitas_lib.adapters import run_adapter  # noqa: E402
from probitas_lib.adapters.wildcat import (  # noqa: E402
    WildcatShapeError,
    adapter,
    seconds_delinquent,
)

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
    with open(os.path.join(FIXTURES, case, "wildcat.json"), encoding="utf-8") as handle:
        return json.load(handle)


class TestSourcing(unittest.TestCase):
    def test_every_record_from_every_case_carries_a_transaction_hash(self):
        for case in ("clean", "cured", "defaulted"):
            records, _ = collect(case)
            self.assertTrue(records, f"{case} produced nothing")
            for record in records:
                with self.subTest(case=case, claim=record.claim):
                    self.assertEqual(record.source_kind, "transaction")

    def test_no_record_is_attributed_to_a_tier_it_was_not_given(self):
        records, _ = collect("defaulted", {BORROWER: "inferred"})
        self.assertTrue(all(r.provenance == "inferred" for r in records))


class TestCleanRecord(unittest.TestCase):
    def setUp(self):
        self.records, self.coverage = collect("clean")
        self.claims = claims(self.records)

    def test_no_delinquency_is_claimed(self):
        self.assertNotIn("delinquency_entered", self.claims)
        self.assertNotIn("delinquency_cured", self.claims)

    def test_a_negative_time_delinquent_is_not_a_delinquency(self):
        """`timeDelinquent` runs negative on healthy markets. Read as an
        unsigned duration it invents a delinquency out of a clean record."""
        market = load("clean")["markets"][0]
        self.assertLess(market["timeDelinquent"], 0)
        self.assertEqual(seconds_delinquent(market), 0)
        standing = self.claims["market_standing"][0]
        self.assertFalse(standing.values["is_delinquent_now"])
        self.assertEqual(standing.values["penalty_interest_accrued"], "0")

    def test_the_terms_the_borrower_chose_are_recorded(self):
        terms = self.claims["market_terms"][0].values
        self.assertEqual(terms["reserve_ratio_bips"], "2000")
        self.assertEqual(terms["grace_period_seconds"], "259200")
        self.assertEqual(terms["market_name"], "Acme USD Coin")

    def test_drawing_and_repaying_are_both_recorded(self):
        self.assertEqual(len(self.claims["borrow"]), 2)
        self.assertEqual(len(self.claims["repayment"]), 2)

    def test_a_settled_withdrawal_batch_is_not_reported_as_unpaid(self):
        self.assertNotIn("withdrawal_batch_expired_unpaid", self.claims)

    def test_closing_the_market_is_recorded(self):
        self.assertIn("market_closed", self.claims)


class TestCuredDelinquency(unittest.TestCase):
    def setUp(self):
        self.records, _ = collect("cured")
        self.claims = claims(self.records)

    def test_it_reads_as_entered_and_then_cured(self):
        self.assertEqual(len(self.claims["delinquency_entered"]), 1)
        self.assertEqual(len(self.claims["delinquency_cured"]), 1)

    def test_the_cure_says_how_long_and_whether_it_ran_past_the_grace_period(self):
        cured = self.claims["delinquency_cured"][0].values
        self.assertEqual(cured["seconds_delinquent"], "86400")
        self.assertFalse(cured["past_grace_period"])

    def test_no_penalty_interest_was_charged(self):
        standing = self.claims["market_standing"][0].values
        self.assertEqual(standing["penalty_interest_accrued"], "0")
        self.assertFalse(standing["is_delinquent_now"])

    def test_a_cured_record_is_not_a_default(self):
        """The distinction the whole fixture exists for."""
        self.assertNotIn("withdrawal_batch_expired_unpaid", self.claims)
        self.assertFalse(
            self.claims["market_standing"][0].values["incurring_penalties_now"]
        )


class TestDefault(unittest.TestCase):
    def setUp(self):
        self.records, _ = collect("defaulted")
        self.claims = claims(self.records)

    def test_it_is_still_delinquent(self):
        self.assertEqual(len(self.claims["delinquency_entered"]), 1)
        self.assertNotIn("delinquency_cured", self.claims)

    def test_penalty_interest_is_running(self):
        standing = self.claims["market_standing"][0].values
        self.assertTrue(standing["is_delinquent_now"])
        self.assertTrue(standing["incurring_penalties_now"])
        self.assertEqual(standing["penalty_interest_accrued"], "41000000000")

    def test_the_delinquency_has_run_past_the_grace_period(self):
        market = load("defaulted")["markets"][0]
        self.assertGreater(seconds_delinquent(market), market["delinquencyGracePeriod"])

    def test_a_lender_asked_for_money_and_did_not_get_it(self):
        batch = self.claims["withdrawal_batch_expired_unpaid"][0]
        self.assertEqual(batch.values["requested"], "1500000000000")
        self.assertEqual(batch.values["paid"], "0")
        self.assertEqual(batch.source_kind, "transaction")


class TestCoverage(unittest.TestCase):
    def test_a_borrower_with_no_markets_is_empty_and_not_an_error(self):
        records, coverage = collect("empty")
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "empty")
        self.assertNotEqual(coverage.status, "error")

    def test_coverage_names_the_source_it_read(self):
        _, coverage = collect("defaulted")
        self.assertEqual(coverage.status, "checked")
        self.assertEqual(coverage.endpoint, "fixture:defaulted")
        self.assertEqual(coverage.block_range, "fixture")

    def test_coverage_names_the_network_it_queried(self):
        """Wildcat runs on Plasma too, and this run looked at one chain."""
        for case in ("defaulted", "empty"):
            with self.subTest(case=case):
                _, coverage = collect(case)
                self.assertIn("mainnet only", coverage.note)

    def test_a_live_coverage_row_would_name_the_endpoint_and_block_range(self):
        from probitas_lib import endpoints

        mainnet = endpoints.WILDCAT_DEPLOYMENTS["mainnet"]
        self.assertTrue(mainnet["endpoint"].startswith("https://"))
        self.assertEqual(mainnet["start_block"], 18686645)


class TestAmounts(unittest.TestCase):
    def test_amounts_survive_as_integer_strings(self):
        records, _ = collect("defaulted")
        borrow = claims(records)["borrow"][0]
        self.assertEqual(borrow.values["amount"], "9000000000000")
        self.assertEqual(int(borrow.values["amount"]), 9000000000000)

    def test_no_value_anywhere_is_a_float(self):
        for case in ("clean", "cured", "defaulted"):
            records, _ = collect(case)
            for record in records:
                for key, value in record.values.items():
                    with self.subTest(case=case, key=key):
                        self.assertNotIsInstance(value, float)


class TestMalformedResponses(unittest.TestCase):
    """A schema change at the venue must not read as a borrower with no history."""

    def adapt(self, mutate):
        payload = load("defaulted")
        mutate(payload)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "wildcat.json"), "w", encoding="utf-8"
        ) as handle:
            json.dump(payload, handle)
        return adapter(SUBJECT, {"fixtures": directory.name})

    def test_a_renamed_market_field_raises(self):
        def mutate(payload):
            payload["markets"][0].pop("totalDelinquencyFeesAccrued")

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_a_missing_collection_raises(self):
        def mutate(payload):
            payload["markets"][0].pop("delinquencyRecords")

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_a_source_that_is_not_a_hash_raises(self):
        def mutate(payload):
            payload["markets"][0]["borrowRecords"][0]["transactionHash"] = "0xshort"

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_an_amount_that_is_not_a_number_raises(self):
        def mutate(payload):
            payload["markets"][0]["borrowRecords"][0]["assetAmount"] = "lots"

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_markets_not_being_a_list_raises(self):
        def mutate(payload):
            payload["markets"] = {"0x1": {}}

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_a_market_for_someone_else_raises_rather_than_being_reported(self):
        def mutate(payload):
            payload["markets"][0]["borrower"] = "0x" + "b2" * 20

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_an_id_that_is_not_an_address_raises(self):
        def mutate(payload):
            payload["markets"][0]["id"] = "Acme | **market**"

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_a_renamed_closed_event_field_raises(self):
        """Otherwise every closed market silently reads as still open."""

        def mutate(payload):
            payload["markets"][0].pop("marketClosedEvent")

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_a_renamed_expiration_field_raises(self):
        def mutate(payload):
            payload["markets"][0]["withdrawalBatches"][0].pop("expiration")

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_delinquency_records_out_of_order_still_pair_correctly(self):
        def mutate(payload):
            payload["markets"][0]["delinquencyRecords"] = [
                {
                    "isDelinquent": False,
                    "blockTimestamp": 1740000000 + 61 * 86400,
                    "blockNumber": 21900000 + 439200,
                    "transactionHash": "0x" + "cd" * 32,
                    "liquidityCoverageRequired": "1800000000000",
                    "totalAssets": "1900000000000",
                },
                {
                    "isDelinquent": True,
                    "blockTimestamp": 1740000000 + 60 * 86400,
                    "blockNumber": 21900000 + 432000,
                    "transactionHash": "0x" + "ce" * 32,
                    "liquidityCoverageRequired": "1800000000000",
                    "totalAssets": "20000000000",
                },
            ]

        records, _ = self.adapt(mutate)
        cured = claims(records)["delinquency_cured"][0].values
        self.assertEqual(cured["seconds_delinquent"], "86400")

    def test_a_repeated_entry_does_not_shorten_the_delinquency(self):
        """Understating how long a borrower was short is the dangerous direction."""

        def mutate(payload):
            start = 1740000000 + 60 * 86400
            payload["markets"][0]["delinquencyRecords"] = [
                {
                    "isDelinquent": True,
                    "blockTimestamp": start,
                    "blockNumber": 21900000 + 432000,
                    "transactionHash": "0x" + "d1" * 32,
                    "liquidityCoverageRequired": "1800000000000",
                    "totalAssets": "20000000000",
                },
                {
                    "isDelinquent": True,
                    "blockTimestamp": start + 5 * 86400,
                    "blockNumber": 21900000 + 468000,
                    "transactionHash": "0x" + "d2" * 32,
                    "liquidityCoverageRequired": "1800000000000",
                    "totalAssets": "10000000000",
                },
                {
                    "isDelinquent": False,
                    "blockTimestamp": start + 6 * 86400,
                    "blockNumber": 21900000 + 475200,
                    "transactionHash": "0x" + "d3" * 32,
                    "liquidityCoverageRequired": "1800000000000",
                    "totalAssets": "1900000000000",
                },
            ]

        records, _ = self.adapt(mutate)
        cured = claims(records)["delinquency_cured"][0].values
        self.assertEqual(cured["seconds_delinquent"], str(6 * 86400))
        self.assertTrue(cured["past_grace_period"])

    def test_a_flag_that_is_not_a_boolean_raises(self):
        """`bool("false")` is True, and a finding disappears."""
        for path in (
            ("isDelinquent",),
            ("isClosed",),
            ("isIncurringPenalties",),
        ):
            with self.subTest(field=path[0]):

                def mutate(payload, field=path[0]):
                    payload["markets"][0][field] = "false"

                with self.assertRaises(WildcatShapeError):
                    self.adapt(mutate)

    def test_a_batch_cannot_be_settled_by_a_type_change(self):
        """The worst shape of this: an unpaid batch quietly leaves the dossier."""

        def mutate(payload):
            payload["markets"][0]["withdrawalBatches"][0]["isClosed"] = "no"

        with self.assertRaises(WildcatShapeError):
            self.adapt(mutate)

    def test_a_malformed_response_never_reads_as_zero_records(self):
        """Through `run_adapter`, the failure has to surface as an error row."""

        def broken(addresses, config):
            return adapter(addresses, {"fixtures": "/nonexistent"})

        records, coverage = run_adapter("wildcat", broken, SUBJECT, {})
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "error")
        self.assertNotEqual(coverage.status, "empty")


class TestConfiguration(unittest.TestCase):
    def test_an_unknown_network_raises(self):
        with self.assertRaises(WildcatShapeError):
            adapter(SUBJECT, {"wildcat_network": "ropsten"})

    def test_the_fixture_path_does_not_leak_into_the_dossier(self):
        _, coverage = collect("clean")
        self.assertNotIn("/", coverage.endpoint)


class TestDeterminism(unittest.TestCase):
    def test_two_runs_give_the_same_records_in_the_same_order(self):
        first, _ = collect("defaulted")
        second, _ = collect("defaulted")
        self.assertEqual(
            [r.to_dict() for r in first], [r.to_dict() for r in second]
        )

    def test_the_fixtures_are_not_mutated_by_reading_them(self):
        before = copy.deepcopy(load("defaulted"))
        collect("defaulted")
        self.assertEqual(before, load("defaulted"))


if __name__ == "__main__":
    unittest.main()
