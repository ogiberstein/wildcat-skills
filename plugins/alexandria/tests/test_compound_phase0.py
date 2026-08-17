"""Pinned registry, bounded capture and offline Compound Phase 0 checks."""

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
EXAMPLE = PLUGIN / "examples" / "compound-v3-phase0-v0"
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.compound_phase0 import build, capture, check_phase0  # noqa: E402
from alexandria_lib.compound_registry import (  # noqa: E402
    COMET_COMMIT, COMET_TREE, DEPLOYMENTS_TREE, EXPECTED_MARKETS,
    validate_registry,
)
from alexandria_lib.errors import AlexandriaError  # noqa: E402


class _Response:
    status = 200

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit):
        return self.data[:limit]


class _Opener:
    def open(self, request, timeout):
        envelope = json.loads(request.data)
        return _Response(canonical_bytes({"id": envelope["id"], "jsonrpc": "2.0", "result": None}))


def tree(root):
    return {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*") if path.is_file()
    }


class CompoundRegistryTests(unittest.TestCase):
    def registry(self):
        return json.loads((EXAMPLE / "source" / "registry.json").read_text())

    def test_checked_registry_has_exact_pin_and_production_set(self):
        registry = self.registry()
        validate_registry(registry)
        self.assertEqual(registry["source"]["commit"], COMET_COMMIT)
        self.assertEqual(registry["source"]["tree"], COMET_TREE)
        self.assertEqual(registry["source"]["deployments_tree"], DEPLOYMENTS_TREE)
        self.assertEqual(
            tuple("%s/%s" % (item["network"], item["market"]) for item in registry["entries"]),
            EXPECTED_MARKETS,
        )
        self.assertEqual(len({item["chain_id"] for item in registry["entries"]}), 10)
        ethereum = next(item for item in registry["entries"] if item["network"] == "mainnet" and item["market"] == "usdc")
        self.assertEqual(ethereum["proxy"], "0xc3d688b66703497daa19211eedff47f25384cdc3")

    def test_registry_rejects_unknown_or_reordered_source_files(self):
        for mutate in (
            lambda value: value["entries"][0].update({"surprise": True}),
            lambda value: value["entries"][0]["files"].reverse(),
            lambda value: value["entries"][0]["files"][0].update({"sha256": "0" * 63}),
        ):
            value = deepcopy(self.registry())
            mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(AlexandriaError):
                validate_registry(value)


class CompoundReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_checked_release_records_every_method_gate_offline(self):
        release = EXAMPLE / "release"
        before = tree(release)
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            receipt = check_phase0(release)
        self.assertEqual(receipt["release_id"], "sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab")
        self.assertEqual(set(receipt["gates"].values()), {"passed", "unsupported"})
        self.assertEqual([item["label"] for item in receipt["transactions"]], ["old", "recent"])
        self.assertEqual(tree(release), before)

    def test_two_rebuilds_match_the_committed_release(self):
        first = self.root / "first"
        second = self.root / "second"
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.assertEqual(build(EXAMPLE / "input", first), build(EXAMPLE / "input", second))
        self.assertEqual(tree(first), tree(second))
        self.assertEqual(tree(first), tree(EXAMPLE / "release"))

    def test_semantic_tamper_fails_before_output_is_installed(self):
        source = self.root / "input"
        shutil.copytree(EXAMPLE / "input", source)
        response = source / "responses" / "recent-transaction.json"
        value = json.loads(response.read_text())
        value["result"]["blockHash"] = "0x" + "00" * 32
        response.write_bytes(canonical_bytes(value))
        output = self.root / "release"
        with self.assertRaisesRegex(AlexandriaError, "transaction does not match"):
            build(source, output)
        self.assertFalse(output.exists())

    def test_malformed_rpc_result_is_a_controlled_refusal(self):
        source = self.root / "input"
        shutil.copytree(EXAMPLE / "input", source)
        response = source / "responses" / "recent-block.json"
        value = json.loads(response.read_text())
        value["result"] = []
        response.write_bytes(canonical_bytes(value))
        output = self.root / "release"
        with self.assertRaisesRegex(AlexandriaError, "block is not an object"):
            build(source, output)
        self.assertFalse(output.exists())

    def test_malformed_nested_trace_and_prestate_are_controlled_refusals(self):
        for filename, mutate, message in (
            ("recent-opcode-trace.json", lambda value: value["result"]["structLogs"].__setitem__(0, []), "opcode trace is incomplete"),
            ("recent-prestate-trace.json", lambda value: value["result"].__setitem__("pre", []), "prestate diff is incomplete"),
        ):
            source = self.root / ("input-" + filename)
            shutil.copytree(EXAMPLE / "input", source)
            response = source / "responses" / filename
            value = json.loads(response.read_text())
            mutate(value)
            response.write_text(
                json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.subTest(filename=filename), self.assertRaisesRegex(AlexandriaError, message):
                build(source, self.root / ("release-" + filename))

    def test_trace_filter_frame_must_belong_to_the_selected_transaction(self):
        source = self.root / "input"
        shutil.copytree(EXAMPLE / "input", source)
        response = source / "responses" / "recent-trace-filter.json"
        value = json.loads(response.read_text())
        for frame in value["result"]:
            frame["transactionHash"] = "0x" + "11" * 32
        response.write_bytes(canonical_bytes(value))
        with self.assertRaisesRegex(AlexandriaError, "nested proxy call"):
            build(source, self.root / "release")

    def test_expected_error_cannot_also_carry_a_result(self):
        source = self.root / "input"
        shutil.copytree(EXAMPLE / "input", source)
        response = source / "responses" / "rpc-modules-unsupported.json"
        value = json.loads(response.read_text())
        value["result"] = {}
        response.write_bytes(canonical_bytes(value))
        with self.assertRaisesRegex(AlexandriaError, "expected error"):
            build(source, self.root / "release")

    def test_fake_capture_never_persists_endpoint_credentials(self):
        output = self.root / "capture"
        registry_bytes = (EXAMPLE / "source" / "registry.json").read_bytes()
        upstream = {
            path.name: path.read_bytes()
            for path in (EXAMPLE / "input" / "upstream").iterdir()
        }
        endpoint = "https://secret-user:secret-token@example.invalid/rpc?key=hidden"
        with (
            mock.patch.dict(os.environ, {"TEST_COMPOUND_RPC": endpoint}),
            mock.patch("alexandria_lib.compound_phase0.registry_bytes", return_value=registry_bytes),
            mock.patch("alexandria_lib.compound_phase0.deployment_source_bytes", return_value=upstream),
            mock.patch("alexandria_lib.compound_phase0.urllib.request.build_opener", return_value=_Opener()),
        ):
            capture(
                EXAMPLE / "source" / "registry.json",
                EXAMPLE / "source" / "corpus.json",
                self.root,
                output,
                endpoint_env="TEST_COMPOUND_RPC",
            )
        self.assertNotIn(endpoint.encode(), b"".join(path.read_bytes() for path in output.rglob("*") if path.is_file()))


if __name__ == "__main__":
    unittest.main()
