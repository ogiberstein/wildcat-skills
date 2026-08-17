"""Euler v2: borrowing on the EVK vaults, read as an event ledger rather than a
stale balance. Tested hard, because interest_accrued must be skipped without
dropping a borrow, and a liquidation is a price moving, not a default."""

import copy
import json
import os
import tempfile
import unittest

from . import support

from probitas_lib.adapters import euler, run_adapter  # noqa: E402
from probitas_lib.adapters.euler import EulerShapeError  # noqa: E402

FIXTURES = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")
BORROWER = "0x" + "a1" * 20
SUBJECT = {BORROWER: "declared"}


def collect(case, addresses=None):
    return euler.adapter(
        addresses if addresses is not None else SUBJECT,
        {"fixtures": os.path.join(FIXTURES, case)},
    )


def claims(records):
    out = {}
    for record in records:
        out.setdefault(record.claim, []).append(record)
    return out


def load(case, name):
    with open(os.path.join(FIXTURES, case, name), encoding="utf-8") as handle:
        return json.load(handle)


class TestItReadsTheEventLedger(unittest.TestCase):
    def test_it_records_borrows_repayments_and_liquidations(self):
        self.assertEqual(
            sorted(claims(collect("euler-borrower")[0])),
            ["borrow", "liquidation", "repayment"],
        )

    def test_interest_accrued_is_skipped_not_recorded(self):
        names = claims(collect("euler-borrower")[0])
        self.assertEqual(len(names["borrow"]), 1)
        self.assertEqual(len(names["repayment"]), 1)
        self.assertNotIn("interest_accrued", names)

    def test_it_records_under_its_own_venue_id(self):
        self.assertEqual(collect("euler-borrower")[0][0].venue, "euler")

    def test_the_registry_flag_matches_the_registered_adapter(self):
        import probitas
        from probitas_lib import registry

        self.assertIn("euler", probitas.ADAPTERS)
        self.assertEqual({v.id for v in registry.implemented()}, set(probitas.ADAPTERS))


class TestSourcing(unittest.TestCase):
    def test_every_record_cites_a_transaction(self):
        for record in collect("euler-borrower")[0]:
            with self.subTest(claim=record.claim):
                self.assertEqual(record.source_kind, "transaction")


class TestDecimalsResolveFromTheVault(unittest.TestCase):
    def test_a_borrow_renders_scaled_from_the_vault_asset(self):
        from probitas_lib import render

        borrow = claims(collect("euler-borrower")[0])["borrow"][0].to_dict()
        self.assertEqual(borrow["values"]["token_symbol"], "USDC")
        self.assertEqual(borrow["values"]["token_decimals"], "6")
        phrase = render._describe(borrow, render.decimals_by_market([borrow]))
        self.assertIn("USDC", phrase)
        self.assertNotIn("raw units", phrase)


class TestLiquidationIsNotADefault(unittest.TestCase):
    def setUp(self):
        self.liq = claims(collect("euler-borrower")[0])["liquidation"][0]

    def test_it_carries_both_legs_on_their_own_scales(self):
        values = self.liq.values
        self.assertEqual(values["token_decimals"], "6")
        self.assertEqual(values["collateral_decimals"], "18")
        self.assertNotEqual(values["repaid"], values["seized_collateral"])
        self.assertTrue(values["collateralised"])

    def test_it_is_not_recorded_as_a_default(self):
        names = claims(collect("euler-borrower")[0])
        for wrong in ("default", "default_suffered"):
            self.assertNotIn(wrong, names)


class TestAmounts(unittest.TestCase):
    def test_no_value_is_a_float(self):
        for record in collect("euler-borrower")[0]:
            for key, value in record.values.items():
                with self.subTest(key=key):
                    self.assertNotIsInstance(value, float)


class TestCoverage(unittest.TestCase):
    def test_no_borrowing_is_empty_not_error(self):
        records, coverage = collect("euler-empty")
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "empty")

    def test_coverage_names_the_chain(self):
        _, coverage = collect("euler-borrower")
        self.assertIn("mainnet", coverage.note)


class TestTimestamps(unittest.TestCase):
    def test_an_iso_timestamp_becomes_an_epoch_integer(self):
        record = claims(collect("euler-borrower")[0])["borrow"][0]
        self.assertIsInstance(record.observed_at, int)
        self.assertGreater(record.observed_at, 1_600_000_000)


class TestMalformedResponses(unittest.TestCase):
    def adapt(self, mutate_events):
        events = load("euler-borrower", "euler-events.json")
        mutate_events(events)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "euler-events.json"), "w", encoding="utf-8"
        ) as handle:
            json.dump(events, handle)
        for name in ("euler-liquidations.json", "euler-vaults.json"):
            with open(os.path.join(directory.name, name), "w", encoding="utf-8") as handle:
                json.dump(load("euler-borrower", name), handle)
        return euler.adapter(SUBJECT, {"fixtures": directory.name})

    def test_an_unknown_borrowing_type_raises(self):
        with self.assertRaises(EulerShapeError):
            self.adapt(lambda events: events["data"][0].__setitem__("type", "rehypothecate"))

    def test_a_non_borrowing_category_raises(self):
        with self.assertRaises(EulerShapeError):
            self.adapt(lambda events: events["data"][0].__setitem__("category", "lending"))

    def test_an_event_owned_by_another_address_raises(self):
        with self.assertRaises(EulerShapeError):
            self.adapt(lambda events: events["data"][0].__setitem__("owner", "0x" + "b2" * 20))

    def test_a_float_amount_raises(self):
        with self.assertRaises(EulerShapeError):
            self.adapt(lambda events: events["data"][0]["assets"][0].__setitem__("amountRaw", 1.5))

    def test_a_bad_tx_hash_raises(self):
        with self.assertRaises(EulerShapeError):
            self.adapt(lambda events: events["data"][0].__setitem__("txHash", "0xshort"))

    def test_missing_data_block_raises(self):
        with self.assertRaises(EulerShapeError):
            self.adapt(lambda events: events.pop("data"))

    def test_a_failure_surfaces_as_an_error_row(self):
        def broken(addresses, config):
            return euler.adapter(addresses, {"fixtures": "/nonexistent"})

        records, coverage = run_adapter("euler", broken, SUBJECT, {})
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "error")


class TestMutationSweep(unittest.TestCase):
    """Dropped or corrupted read fields must never change a finding silently."""

    def test_no_read_field_silently_changes_a_finding(self):
        base_events = load("euler-borrower", "euler-events.json")
        base, base_status = self._run(base_events)
        allowed = set()
        for path in self._paths(base_events):
            events = copy.deepcopy(base_events)
            target = self._at(events, path)
            if isinstance(target, (dict, list)):
                continue
            self._set(events, path, "corrupted")
            try:
                mutated, status = self._run(events)
            except Exception:
                continue
            if (mutated, status) != (base, base_status):
                self.assertIn(
                    path[-1], allowed, f"{'.'.join(map(str, path))} changed silently"
                )

    def _run(self, events):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "euler-events.json"), "w", encoding="utf-8"
        ) as handle:
            json.dump(events, handle)
        for name in ("euler-liquidations.json", "euler-vaults.json"):
            with open(os.path.join(directory.name, name), "w", encoding="utf-8") as handle:
                json.dump(load("euler-borrower", name), handle)
        records, coverage = euler.adapter(SUBJECT, {"fixtures": directory.name})
        return [record.to_dict() for record in records], coverage.status

    def _paths(self, node, prefix=()):
        if isinstance(node, dict):
            for key, value in node.items():
                yield prefix + (key,)
                yield from self._paths(value, prefix + (key,))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                yield from self._paths(value, prefix + (index,))

    def _at(self, node, path):
        for step in path:
            node = node[step]
        return node

    def _set(self, node, path, value):
        self._at(node, path[:-1])[path[-1]] = value


if __name__ == "__main__":
    unittest.main()
