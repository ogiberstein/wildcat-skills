"""Merkle Patricia proofs cover inclusion, absence and node reference forms."""

from eth_hash.auto import keccak
from trie import HexaryTrie
import unittest

from lazarus_lib.errors import FormatError, IntegrityError
from lazarus_lib.rlp import encode
from lazarus_lib.trieproof import compact_path, verify_proof


def encoded_proof(trie, key):
    return [encode(node) for node in trie.get_proof(key)]


class TrieProofTests(unittest.TestCase):
    def test_leaf_inclusion_and_divergent_leaf_absence(self):
        trie = HexaryTrie({})
        trie[b"a"] = b"value"
        self.assertEqual(verify_proof(trie.root_hash, b"a", encoded_proof(trie, b"a")), b"value")
        self.assertIsNone(verify_proof(trie.root_hash, b"b", encoded_proof(trie, b"b")))

    def test_embedded_nodes_may_be_present_or_omitted(self):
        trie = HexaryTrie({})
        trie[b"\x12"] = b"x"
        trie[b"\x13"] = b"y"
        proof = encoded_proof(trie, b"\x12")
        self.assertGreater(len(proof), 1)
        self.assertEqual(verify_proof(trie.root_hash, b"\x12", proof), b"x")
        self.assertEqual(verify_proof(trie.root_hash, b"\x12", proof[:1]), b"x")

    def test_hashed_nodes_require_every_referenced_node(self):
        trie = HexaryTrie({})
        trie[b"\x12"] = b"x" * 40
        trie[b"\x13"] = b"y" * 40
        proof = encoded_proof(trie, b"\x12")
        self.assertGreater(len(proof), 1)
        self.assertEqual(verify_proof(trie.root_hash, b"\x12", proof), b"x" * 40)
        with self.assertRaisesRegex(IntegrityError, "missing"):
            verify_proof(trie.root_hash, b"\x12", proof[:-1])

    def test_each_mutated_node_and_wrong_root_fail(self):
        trie = HexaryTrie({})
        trie[b"\x12"] = b"x" * 40
        trie[b"\x13"] = b"y" * 40
        proof = encoded_proof(trie, b"\x12")
        for index in range(len(proof)):
            changed = proof.copy()
            changed[index] = changed[index][:-1] + bytes([changed[index][-1] ^ 1])
            with self.subTest(index=index), self.assertRaises((FormatError, IntegrityError)):
                verify_proof(trie.root_hash, b"\x12", changed)
        with self.assertRaisesRegex(IntegrityError, "root"):
            verify_proof(b"\xff" * 32, b"\x12", proof)

    def test_bad_compact_paths_duplicate_and_trailing_nodes_fail(self):
        for raw in (b"", b"\x40", b"\x01"):
            with self.subTest(raw=raw), self.assertRaises(FormatError):
                compact_path(raw)
        trie = HexaryTrie({})
        trie[b"a"] = b"value"
        proof = encoded_proof(trie, b"a")
        with self.assertRaisesRegex(FormatError, "duplicate"):
            verify_proof(trie.root_hash, b"a", proof + proof)
        with self.assertRaisesRegex(FormatError, "trailing"):
            verify_proof(trie.root_hash, b"b", proof + [encode([b" ", b"x"])])

    def test_malformed_rlp_node_fails(self):
        malformed = b"\x81\x00"
        with self.assertRaises(FormatError):
            verify_proof(keccak(malformed), b"a", [malformed])


if __name__ == "__main__":
    unittest.main()
