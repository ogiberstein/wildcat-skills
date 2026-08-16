"""Delta arithmetic: what changed, with both sides named."""

import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import deltas  # noqa: E402


def function(name, inputs=(), mutability="nonpayable", outputs=()):
    return {
        "type": "function",
        "name": name,
        "inputs": [{"name": "a%d" % i, "type": t} for i, t in enumerate(inputs)],
        "outputs": [{"name": "", "type": t} for t in outputs],
        "stateMutability": mutability,
    }


def slot(label, number, offset=0, kind="t_uint256", contract="Escrow"):
    return {
        "label": label,
        "slot": str(number),
        "offset": offset,
        "type": kind,
        "contract": contract,
    }


class SignatureTests(unittest.TestCase):
    def test_a_function_signature_reads_as_solc_writes_it(self):
        self.assertEqual(
            deltas.abi_signature(function("transfer", ("address", "uint256"))),
            "transfer(address,uint256)",
        )

    def test_a_tuple_argument_expands(self):
        entry = {
            "type": "function",
            "name": "settle",
            "inputs": [
                {
                    "name": "order",
                    "type": "tuple",
                    "components": [
                        {"name": "who", "type": "address"},
                        {"name": "amount", "type": "uint256"},
                    ],
                }
            ],
        }
        self.assertEqual(deltas.abi_signature(entry), "settle((address,uint256))")

    def test_an_array_of_tuples_keeps_its_suffix(self):
        entry = {
            "type": "function",
            "name": "settleMany",
            "inputs": [
                {
                    "name": "orders",
                    "type": "tuple[]",
                    "components": [{"name": "who", "type": "address"}],
                }
            ],
        }
        self.assertEqual(deltas.abi_signature(entry), "settleMany((address)[])")

    def test_fallback_and_receive_carry_their_own_names(self):
        self.assertEqual(deltas.abi_signature({"type": "fallback"}), "fallback")
        self.assertEqual(deltas.abi_signature({"type": "receive"}), "receive")


class AbiDeltaTests(unittest.TestCase):
    def test_an_added_function_shows_up(self):
        found = deltas.abi_delta([function("a")], [function("a"), function("b")])
        self.assertEqual(found["added"], ["b()"])
        self.assertEqual(found["removed"], [])

    def test_a_removed_function_shows_up(self):
        found = deltas.abi_delta([function("a"), function("b")], [function("a")])
        self.assertEqual(found["removed"], ["b()"])

    def test_a_changed_entry_carries_both_sides(self):
        found = deltas.abi_delta(
            [function("a", mutability="nonpayable")],
            [function("a", mutability="payable")],
        )
        self.assertEqual(len(found["changed"]), 1)
        change = found["changed"][0]
        self.assertEqual(change["signature"], "a()")
        self.assertEqual(change["baseline"]["stateMutability"], "nonpayable")
        self.assertEqual(change["current"]["stateMutability"], "payable")

    def test_an_unchanged_abi_produces_an_empty_delta(self):
        found = deltas.abi_delta([function("a")], [function("a")])
        self.assertTrue(deltas.empty(found))

    def test_the_delta_reverses_when_the_sides_do(self):
        forward = deltas.abi_delta([function("a")], [function("a"), function("b")])
        backward = deltas.abi_delta([function("a"), function("b")], [function("a")])
        self.assertEqual(forward["added"], backward["removed"])


class MethodIdentifierTests(unittest.TestCase):
    def test_a_selector_that_moved_under_an_unchanged_signature_is_reported(self):
        found = deltas.method_identifier_delta(
            {"transfer(address,uint256)": "a9059cbb"},
            {"transfer(address,uint256)": "deadbeef"},
        )
        self.assertEqual(found["moved"][0]["baseline"], "a9059cbb")
        self.assertEqual(found["moved"][0]["current"], "deadbeef")

    def test_added_and_removed_signatures_are_listed(self):
        found = deltas.method_identifier_delta({"a()": "0badc0de"}, {"b()": "0badc0de"})
        self.assertEqual(found["added"], ["b()"])
        self.assertEqual(found["removed"], ["a()"])


class StorageDeltaTests(unittest.TestCase):
    def test_a_moved_slot_carries_both_positions(self):
        found = deltas.storage_delta([slot("owner", 0)], [slot("owner", 1)])
        self.assertEqual(found["moved"][0]["variable"], "Escrow:owner")
        self.assertEqual(found["moved"][0]["baseline"]["slot"], "0")
        self.assertEqual(found["moved"][0]["current"]["slot"], "1")

    def test_a_variable_that_kept_its_slot_and_changed_type_is_reported(self):
        found = deltas.storage_delta(
            [slot("owner", 0, kind="t_address")],
            [slot("owner", 0, kind="t_uint256")],
        )
        self.assertEqual(found["moved"], [])
        self.assertEqual(found["retyped"][0]["baseline"], "t_address")
        self.assertEqual(found["retyped"][0]["current"], "t_uint256")

    def test_an_added_and_a_removed_variable_are_listed(self):
        found = deltas.storage_delta([slot("a", 0)], [slot("b", 0)])
        self.assertEqual(found["added"], ["Escrow:b"])
        self.assertEqual(found["removed"], ["Escrow:a"])

    def test_an_offset_change_within_a_slot_counts_as_a_move(self):
        found = deltas.storage_delta(
            [slot("packed", 0, offset=0)], [slot("packed", 0, offset=20)]
        )
        self.assertEqual(found["moved"][0]["current"]["offset"], 20)

    def test_an_unchanged_layout_produces_an_empty_delta(self):
        self.assertTrue(deltas.empty(deltas.storage_delta([slot("a", 0)], [slot("a", 0)])))


class SideTests(unittest.TestCase):
    def test_a_side_carries_a_name_and_a_checked_digest(self):
        found = deltas.side("v1.0.0", {"sha256": "ab" * 32})
        self.assertEqual(found["name"], "v1.0.0")
        self.assertIn("sha256", found["digest"])

    def test_a_side_with_a_broken_digest_raises(self):
        with self.assertRaises(Exception):
            deltas.side("v1.0.0", {"sha256": "nope"})


if __name__ == "__main__":
    unittest.main()
