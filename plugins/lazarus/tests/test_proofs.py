"""Account, storage and code claims stay tied to their trie leaves."""

import copy
import json
import unittest

from eth_hash.auto import keccak

from lazarus_lib.errors import FormatError, IntegrityError
from lazarus_lib.hexvalue import encode_hex
from lazarus_lib.proofs import (
    EMPTY_CODE_HASH,
    decode_account,
    decode_storage,
    proof_nodes,
    verify_proof_record,
)
from lazarus_lib.rlp import encode
from lazarus_lib.trieproof import EMPTY_TRIE_ROOT, verify_proof

from . import support


class ProofTests(unittest.TestCase):
    def test_synthetic_account_storage_inclusion_and_zero_slot(self):
        material = support.synthetic_fixture_material()
        record = material["proof_records"][0]
        report = verify_proof_record(
            record,
            state_root=material["state_trie"].root_hash,
            expected_block_hash=record["block_hash"],
            expected_slots=material["plan"]["proof_targets"][0]["slots"],
        )
        self.assertTrue(report["account_included"])
        self.assertEqual(report["storage_included"], 1)
        self.assertEqual(report["storage_absent"], 1)

    def test_empty_account_and_empty_storage_trie_are_proved_absent(self):
        material = support.synthetic_fixture_material()
        state_trie = material["state_trie"]
        missing = support.address("33")
        key = keccak(bytes.fromhex(missing[2:]))
        record = {
            "schema_version": 1,
            "evidence": "proof-backed",
            "block_hash": material["header"]["hash"],
            "address": missing,
            "balance": "0x0",
            "nonce": "0x0",
            "code_hash": encode_hex(EMPTY_CODE_HASH),
            "storage_hash": encode_hex(EMPTY_TRIE_ROOT),
            "code": "0x",
            "account_proof": [encode_hex(encode(node)) for node in state_trie.get_proof(key)],
            "storage_proof": [
                {"key": support.slot(), "value": "0x0", "proof": []}
            ],
        }
        report = verify_proof_record(
            record,
            state_root=state_trie.root_hash,
            expected_block_hash=record["block_hash"],
            expected_slots=[support.slot()],
        )
        self.assertFalse(report["account_included"])
        self.assertEqual(report["storage_absent"], 1)

    def test_response_fields_keys_block_hash_and_code_are_checked(self):
        material = support.synthetic_fixture_material()
        original = material["proof_records"][0]
        common = {
            "state_root": material["state_trie"].root_hash,
            "expected_block_hash": original["block_hash"],
            "expected_slots": material["plan"]["proof_targets"][0]["slots"],
        }
        mutations = (
            ("balance", "0x3", "balance"),
            ("nonce", "0x2", "nonce"),
            ("storage_hash", support.hash32("ff"), "storage hash"),
            ("code_hash", support.hash32("ff"), "code hash"),
            ("code", "0x6001", "captured code"),
            ("block_hash", support.hash32("ff"), "block hash"),
        )
        for field, value, message in mutations:
            record = copy.deepcopy(original)
            record[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(IntegrityError, message):
                verify_proof_record(record, **common)
        with self.assertRaisesRegex(IntegrityError, "keys"):
            verify_proof_record(original, **{**common, "expected_slots": [support.slot("03")]})

    def test_overwide_account_and_storage_leaf_values_fail(self):
        account = encode([b"\x01" * 33, b"", EMPTY_TRIE_ROOT, EMPTY_CODE_HASH])
        with self.assertRaisesRegex(FormatError, "256 bits"):
            decode_account(account)
        with self.assertRaisesRegex(FormatError, "256 bits"):
            decode_storage(encode(b"\x01" * 33))

    def test_execution_api_vector_verifies_account_and_storage_paths(self):
        path = support.FIXTURES / "execution-api" / "get-account-proof-with-storage.json"
        vector = json.loads(path.read_text(encoding="utf-8"))
        result = vector["response"]["result"]
        account_proof = proof_nodes(result["accountProof"])
        state_root = keccak(account_proof[0])
        address_key = keccak(bytes.fromhex(result["address"][2:]))
        account_raw = verify_proof(state_root, address_key, account_proof)
        self.assertIsNotNone(account_raw)
        account = decode_account(account_raw)
        self.assertEqual(account["balance"], int(result["balance"], 16))
        self.assertEqual(account["nonce"], int(result["nonce"], 16))
        self.assertEqual(encode_hex(account["storage_root"]), result["storageHash"])
        self.assertEqual(encode_hex(account["code_hash"]), result["codeHash"])
        storage = result["storageProof"][0]
        slot_key = keccak(int(storage["key"], 16).to_bytes(32, "big"))
        storage_raw = verify_proof(
            account["storage_root"],
            slot_key,
            proof_nodes(storage["proof"]),
        )
        self.assertEqual(decode_storage(storage_raw), int(storage["value"], 16))

    def test_every_execution_api_proof_node_mutation_fails(self):
        path = support.FIXTURES / "execution-api" / "get-account-proof-with-storage.json"
        result = json.loads(path.read_text(encoding="utf-8"))["response"]["result"]
        account_nodes = proof_nodes(result["accountProof"])
        account_root = keccak(account_nodes[0])
        account_key = keccak(bytes.fromhex(result["address"][2:]))
        self._mutations_fail(account_root, account_key, account_nodes)
        account_raw = verify_proof(account_root, account_key, account_nodes)
        storage_root = decode_account(account_raw)["storage_root"]
        storage = result["storageProof"][0]
        storage_key = keccak(int(storage["key"], 16).to_bytes(32, "big"))
        self._mutations_fail(storage_root, storage_key, proof_nodes(storage["proof"]))

    def _mutations_fail(self, root, key, nodes):
        for index, node in enumerate(nodes):
            changed = nodes.copy()
            changed[index] = node[:-1] + bytes([node[-1] ^ 1])
            with self.subTest(index=index), self.assertRaises((FormatError, IntegrityError)):
                verify_proof(root, key, changed)


if __name__ == "__main__":
    unittest.main()
