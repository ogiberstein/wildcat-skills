"""Fixed Euler release bytes, rebuilds and offline tamper checks."""

import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from . import support
from tabularium_lib.core import TabulariumError, canonical_json, sha256_bytes
from tabularium_lib.verifier import verify


EXAMPLES = support.PLUGIN_ROOT / "examples"
RELEASES = {
    "euler-v1-v0": {
        "source.json": "1241cbed85189e79f9b0f8418e6838b297b4b661ad3e9f2d8a86903e22a6e790",
        "capture.json": "6f8d4cfb1a07cda441def7295e40d028b341e5eb62324cfa905435cb1bdc033d",
        "events.jsonl": "4034622f8b34147dead8a87d7c16b2a7c7197ed6417809fec41716a8028552aa",
        "coverage.json": "3c3d3043bb11ab8b5a3baa64b3659900ad0201a9f19f33ff96ba643598fd5e70",
    },
    "euler-v2-v0": {
        "source.json": "10f5c8e8242ef3745fbd69c4d8aed458f31b165fc4526f638e76df59a69a18cc",
        "capture.json": "bcf2c85907243ccb40bc79234e30457d2e7e8b7dc3addc32d7301f804c772b9e",
        "events.jsonl": "f563baa00c737384a3901f1bb3a7ae977f68f52a813eae9d02071eb2f4d0a5fe",
        "coverage.json": "9892768315484ff05771e998f301b30daebd079a445e4226c9e55b12323c2a4b",
    },
}


class EulerReleaseTests(unittest.TestCase):
    def test_all_eight_release_artifact_hashes_are_fixed(self):
        for release, expected in RELEASES.items():
            for name, digest in expected.items():
                self.assertEqual(hashlib.sha256((EXAMPLES / release / name).read_bytes()).hexdigest(), digest, "%s/%s" % (release, name))

    def test_both_releases_verify_without_network_or_writes(self):
        for release in RELEASES:
            root = EXAMPLES / release
            paths = tuple(root / name for name in RELEASES[release])
            before = {path: path.read_bytes() for path in paths}
            with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
                report = verify(root / "coverage.json")
            self.assertGreater(report.rows, 0)
            self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_both_documented_rebuilds_match_committed_bytes(self):
        for release in RELEASES:
            result = subprocess.run([sys.executable, str(EXAMPLES / release / "rebuild.py")], cwd=support.REPO_ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("rebuild matches", result.stdout)

    def copied_release(self, release):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / release
        shutil.copytree(EXAMPLES / release, root)
        return root

    def test_source_tamper_fails_declared_digest(self):
        root = self.copied_release("euler-v2-v0")
        (root / "source.json").write_bytes((root / "source.json").read_bytes() + b"\n")
        with self.assertRaisesRegex(TabulariumError, "source digest"):
            verify(root / "coverage.json")

    def test_canonical_tamper_fails_offline_rebuild_after_rebinding(self):
        root = self.copied_release("euler-v1-v0")
        events = root / "events.jsonl"
        row = json.loads(events.read_text())
        row["amounts"][0]["base_units"] = "1"
        events.write_bytes(canonical_json(row) + b"\n")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["canonical"]["sha256"] = sha256_bytes(events.read_bytes())
        manifest["canonical"]["bytes"] = len(events.read_bytes())
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "offline source rebuild"):
            verify(manifest_path)

    def test_protocol_and_source_version_mismatch_fails(self):
        root = self.copied_release("euler-v2-v0")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["source"]["protocol_generation"] = "euler-v1"
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "version fields"):
            verify(manifest_path)

    def test_capture_request_drift_fails_after_rebinding(self):
        root = self.copied_release("euler-v2-v0")
        capture_path = root / "capture.json"
        capture = json.loads(capture_path.read_text())
        capture["request"]["query"]["limit"] = "99"
        capture_path.write_bytes(canonical_json(capture) + b"\n")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["capture_manifest"]["sha256"] = sha256_bytes(capture_path.read_bytes())
        manifest["capture_manifest"]["bytes"] = len(capture_path.read_bytes())
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "request does not match"):
            verify(manifest_path)

    def test_capture_timestamp_must_match_preserved_response(self):
        root = self.copied_release("euler-v2-v0")
        capture_path = root / "capture.json"
        capture = json.loads(capture_path.read_text())
        capture["captured_at"] = "2026-08-17T02:32:00.000Z"
        capture_path.write_bytes(canonical_json(capture) + b"\n")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["capture_manifest"]["sha256"] = sha256_bytes(capture_path.read_bytes())
        manifest["capture_manifest"]["bytes"] = len(capture_path.read_bytes())
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "timestamp does not match"):
            verify(manifest_path)


if __name__ == "__main__":
    unittest.main()
