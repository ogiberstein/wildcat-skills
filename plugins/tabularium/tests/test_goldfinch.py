"""Goldfinch mapping rules, validation and the preserved real snapshot."""

import copy
import hashlib
import json
from pathlib import Path
import unittest

from . import support
from tabularium_lib.adapters.goldfinch import map_entity, map_snapshot
from tabularium_lib.core import MAX_SAFE_INTEGER, TabulariumError, jsonl_bytes


class GoldfinchAdapterTests(unittest.TestCase):
    def rows(self):
        source = support.minimal_snapshot()
        return source, source["borrows"][0], source["repays"][0]

    def test_borrow_mapping_uses_the_borrowing_family_and_qualified_action(self):
        _, borrow, _ = self.rows()
        event = map_entity("borrows", borrow)
        self.assertEqual(event["schema_version"], 1)
        self.assertEqual(event["event_family"], "borrowing")
        self.assertEqual(event["action"], "goldfinch.borrow")

    def test_repay_mapping_does_not_claim_full_settlement(self):
        _, _, repay = self.rows()
        event = map_entity("repays", repay)
        self.assertEqual(event["event_family"], "repayment")
        self.assertEqual(event["action"], "goldfinch.repay")
        self.assertNotIn("settled", event)
        self.assertNotIn("balance", event)

    def test_common_envelope_distinguishes_every_required_dimension(self):
        _, borrow, _ = self.rows()
        event = map_entity("borrows", borrow)
        for key in (
            "schema_version", "event_family", "action", "chain", "transaction",
            "parties", "instrument", "asset", "amount", "provenance", "native_record",
        ):
            self.assertIn(key, event)

    def test_native_record_and_unknown_fields_are_retained_without_mutation(self):
        _, borrow, _ = self.rows()
        original = copy.deepcopy(borrow)
        event = map_entity("borrows", borrow)
        self.assertEqual(event["native_record"], original)
        self.assertEqual(event["native_record"]["futureField"], {"kept": True})
        self.assertEqual(borrow, original)
        self.assertIsNot(event["native_record"], borrow)

    def test_source_selector_mapping_rule_and_adapter_version_are_explicit(self):
        _, borrow, _ = self.rows()
        provenance = map_entity("borrows", borrow)["provenance"]
        self.assertEqual(provenance["source_contract"], borrow["market"]["id"])
        self.assertEqual(provenance["source_selector"], "borrows[id=%s]" % borrow["id"])
        self.assertEqual(provenance["mapping_rule"], "goldfinch.borrow.v1")
        self.assertEqual(provenance["adapter_version"], "1.0.0")

    def test_log_index_is_parsed_from_the_source_identifier(self):
        _, borrow, _ = self.rows()
        self.assertEqual(map_entity("borrows", borrow)["transaction"]["log_index"], 12)

    def test_source_identifier_hash_must_match_transaction_hash(self):
        _, borrow, _ = self.rows()
        borrow["hash"] = "0x" + "3" * 64
        with self.assertRaisesRegex(TabulariumError, "does not match"):
            map_entity("borrows", borrow)

    def test_missing_required_fields_fail_closed(self):
        _, borrow, _ = self.rows()
        del borrow["market"]
        with self.assertRaisesRegex(TabulariumError, "has no 'market'"):
            map_entity("borrows", borrow)

    def test_non_decimal_amounts_fail_closed(self):
        for value in (1, "-1", "01", "1.0", "1e3"):
            _, borrow, _ = self.rows()
            borrow["amount"] = value
            with self.subTest(value=value), self.assertRaisesRegex(TabulariumError, "amount"):
                map_entity("borrows", borrow)

    def test_unsafe_log_index_and_asset_decimals_fail_closed(self):
        _, borrow, _ = self.rows()
        borrow["id"] = "%s-%d" % (borrow["hash"], MAX_SAFE_INTEGER + 1)
        with self.assertRaisesRegex(TabulariumError, "safe"):
            map_entity("borrows", borrow)
        _, borrow, _ = self.rows()
        borrow["asset"]["decimals"] = MAX_SAFE_INTEGER + 1
        with self.assertRaisesRegex(TabulariumError, "safe"):
            map_entity("borrows", borrow)

    def test_an_extremely_long_log_index_is_refused_without_integer_coercion(self):
        _, borrow, _ = self.rows()
        borrow["id"] = "%s-%s" % (borrow["hash"], "9" * 10000)
        with self.assertRaisesRegex(TabulariumError, "safe integer"):
            map_entity("borrows", borrow)

    def test_duplicate_source_identifiers_fail_across_collections(self):
        source, borrow, repay = self.rows()
        source["repays"][0] = copy.deepcopy(borrow)
        with self.assertRaisesRegex(TabulariumError, "duplicate source identifier"):
            map_snapshot(source)

    def test_output_order_is_timestamp_hash_log_index_family_and_id(self):
        result = map_snapshot(support.minimal_snapshot())
        self.assertEqual([event["event_family"] for event in result.events], ["repayment", "borrowing"])

    def test_stable_ids_and_bytes_repeat(self):
        first = map_snapshot(support.minimal_snapshot()).events
        second = map_snapshot(support.minimal_snapshot()).events
        self.assertEqual([row["id"] for row in first], [row["id"] for row in second])
        self.assertEqual(jsonl_bytes(first), jsonl_bytes(second))

    def test_unmapped_source_kinds_are_counted_and_not_emitted(self):
        result = map_snapshot(support.minimal_snapshot())
        self.assertEqual(
            result.unmapped_counts,
            {"creditLines": 1, "tranchedPools": 2, "callableLoans": 0, "_meta": 1},
        )
        self.assertEqual({e["provenance"]["source_entity"] for e in result.events}, {"borrows", "repays"})

    def test_unknown_top_level_entity_kind_is_refused_not_ignored(self):
        source = support.minimal_snapshot()
        source["mysteryEvents"] = []
        with self.assertRaisesRegex(TabulariumError, "unsupported top-level"):
            map_snapshot(source)


class RealSnapshotTests(unittest.TestCase):
    SOURCE = support.PLUGIN_ROOT / "examples" / "goldfinch-v0" / "source.json"

    @classmethod
    def setUpClass(cls):
        cls.raw = cls.SOURCE.read_bytes()
        cls.mapped = map_snapshot(json.loads(cls.raw))

    def test_preserved_source_digest_is_the_receipted_capture(self):
        self.assertEqual(
            hashlib.sha256(self.raw).hexdigest(),
            "644b706804b6e28d69b1028b87937e0e36c882f703419d0e2bf568b056892bc9",
        )

    def test_real_snapshot_emits_511_rows_in_the_two_families(self):
        self.assertEqual(len(self.mapped.events), 511)
        families = [event["event_family"] for event in self.mapped.events]
        self.assertEqual(families.count("borrowing"), 34)
        self.assertEqual(families.count("repayment"), 477)

    def test_real_snapshot_native_records_match_source_entities(self):
        source = json.loads(self.raw)
        by_selector = {
            "%s[id=%s]" % (kind, row["id"]): row
            for kind in ("borrows", "repays")
            for row in source[kind]
        }
        for event in self.mapped.events:
            self.assertEqual(
                event["native_record"],
                by_selector[event["provenance"]["source_selector"]],
            )
