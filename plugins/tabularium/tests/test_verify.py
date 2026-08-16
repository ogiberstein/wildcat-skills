"""Offline release gates and every tamper or path failure in issue 82."""

from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

from . import support
from tabularium_lib.builder import build
from tabularium_lib.core import (
    TabulariumError,
    canonical_json,
    jsonl_bytes,
    sha256_bytes,
)
from tabularium_lib.verifier import verify


SOURCE_FIXTURE = support.FIXTURES / "minimal-snapshot.json"
CAPTURE_FIXTURE = support.FIXTURES / "minimal-capture-manifest.json"


class OfflineVerificationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.json"
        self.capture = self.root / "capture.json"
        self.canonical = self.root / "events.jsonl"
        self.manifest_path = self.root / "coverage.json"
        self.source.write_bytes(SOURCE_FIXTURE.read_bytes())
        self.capture.write_bytes(CAPTURE_FIXTURE.read_bytes())
        build(
            self.source,
            self.capture,
            self.canonical,
            self.manifest_path,
            "fixture-v1",
        )

    def manifest(self):
        return json.loads(self.manifest_path.read_text())

    def write_manifest(self, manifest):
        self.manifest_path.write_bytes(canonical_json(manifest) + b"\n")

    def update_claim(self, manifest, name, path):
        data = path.read_bytes()
        manifest[name]["sha256"] = sha256_bytes(data)
        manifest[name]["bytes"] = len(data)

    def rows(self):
        return [json.loads(line) for line in self.canonical.read_text().splitlines()]

    def write_rows(self, rows, row_claim=None):
        self.canonical.write_bytes(jsonl_bytes(rows))
        manifest = self.manifest()
        self.update_claim(manifest, "canonical", self.canonical)
        if row_claim is not None:
            manifest["canonical"]["rows"] = row_claim
        self.write_manifest(manifest)

    def test_valid_release_verifies_fully_offline(self):
        with mock.patch.object(
            socket, "create_connection", side_effect=AssertionError("network used")
        ):
            report = verify(self.manifest_path)
        self.assertEqual(report.release, "fixture-v1")
        self.assertEqual(report.rows, 2)

    def test_altered_source_bytes_fail_the_declared_digest(self):
        self.source.write_bytes(self.source.read_bytes() + b"\n")
        with self.assertRaisesRegex(TabulariumError, "source digest"):
            verify(self.manifest_path)

    def test_altered_capture_manifest_bytes_fail_the_declared_digest(self):
        self.capture.write_bytes(self.capture.read_bytes() + b"\n")
        with self.assertRaisesRegex(TabulariumError, "capture manifest digest"):
            verify(self.manifest_path)

    def test_altered_canonical_bytes_fail_even_with_an_updated_digest(self):
        rows = self.rows()
        rows[0]["amount"]["base_units"] = "999"
        self.write_rows(rows)
        with self.assertRaisesRegex(TabulariumError, "offline source rebuild"):
            verify(self.manifest_path)

    def test_included_count_drift_fails(self):
        manifest = self.manifest()
        manifest["coverage"]["included_entities"]["borrows"] = 2
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "included entity counts"):
            verify(self.manifest_path)

    def test_unsupported_count_drift_fails(self):
        manifest = self.manifest()
        manifest["coverage"]["unsupported_entities"]["creditLines"] = 0
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "unsupported entity counts"):
            verify(self.manifest_path)

    def test_omitted_source_kind_fails_manifest_shape(self):
        manifest = self.manifest()
        del manifest["coverage"]["unsupported_entities"]["_meta"]
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "missing field"):
            verify(self.manifest_path)

    def test_duplicate_source_selectors_fail(self):
        rows = self.rows()
        rows[1] = deepcopy(rows[0])
        self.write_rows(rows)
        with self.assertRaisesRegex(TabulariumError, "duplicate source selectors"):
            verify(self.manifest_path)

    def test_reordered_rows_fail(self):
        rows = self.rows()
        self.write_rows(list(reversed(rows)))
        with self.assertRaisesRegex(TabulariumError, "deterministic order"):
            verify(self.manifest_path)

    def test_unsupported_event_schema_version_fails(self):
        rows = self.rows()
        rows[0]["schema_version"] = 2
        self.write_rows(rows)
        with self.assertRaisesRegex(TabulariumError, "unsupported event schema"):
            verify(self.manifest_path)

    def test_unsupported_row_mapping_version_fails(self):
        rows = self.rows()
        rows[0]["provenance"]["mapping_rule"] = "goldfinch.repay.v2"
        self.write_rows(rows)
        with self.assertRaisesRegex(TabulariumError, "unsupported mapping-rule"):
            verify(self.manifest_path)

    def test_unsupported_manifest_event_version_fails(self):
        manifest = self.manifest()
        manifest["versions"]["event_schema"] = 2
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "unsupported event schema"):
            verify(self.manifest_path)

    def test_unsupported_manifest_mapping_versions_fail(self):
        manifest = self.manifest()
        manifest["versions"]["mapping_rules"] = ["goldfinch.borrow.v2"]
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "unsupported mapping-rule"):
            verify(self.manifest_path)

    def test_absolute_artifact_path_fails(self):
        manifest = self.manifest()
        manifest["source"]["path"] = str(self.source.resolve())
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "safe relative path"):
            verify(self.manifest_path)

    def test_parent_traversal_fails(self):
        manifest = self.manifest()
        manifest["source"]["path"] = "../source.json"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "safe relative path"):
            verify(self.manifest_path)

    def test_nul_in_artifact_path_fails_on_the_controlled_error_path(self):
        manifest = self.manifest()
        manifest["source"]["path"] = "source\x00.json"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "safe relative path"):
            verify(self.manifest_path)

    def test_symlink_escape_fails(self):
        outside = tempfile.NamedTemporaryFile(delete=False)
        self.addCleanup(lambda: os.unlink(outside.name) if os.path.exists(outside.name) else None)
        outside.write(b"outside")
        outside.close()
        escape = self.root / "escape.json"
        escape.symlink_to(outside.name)
        manifest = self.manifest()
        manifest["source"]["path"] = "escape.json"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "uses a symlink"):
            verify(self.manifest_path)

    def test_missing_artifact_fails(self):
        manifest = self.manifest()
        manifest["canonical"]["path"] = "missing.jsonl"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "canonical path is missing"):
            verify(self.manifest_path)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO files are not supported")
    def test_fifo_coverage_manifest_is_refused_without_opening_it(self):
        fifo = self.root / "coverage.fifo"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(TabulariumError, "not a regular file"):
            verify(fifo)

    def test_malformed_manifest_json_fails_closed(self):
        self.manifest_path.write_bytes(b"{not json}\n")
        with self.assertRaisesRegex(TabulariumError, "not valid JSON"):
            verify(self.manifest_path)

    def test_duplicate_manifest_keys_fail_closed(self):
        self.manifest_path.write_bytes(b'{"schema_version":1,"schema_version":1}\n')
        with self.assertRaisesRegex(TabulariumError, "duplicate JSON key"):
            verify(self.manifest_path)

    def test_nonfinite_manifest_number_fails_closed(self):
        self.manifest_path.write_bytes(b'{"schema_version":NaN}\n')
        with self.assertRaisesRegex(TabulariumError, "non-finite JSON number"):
            verify(self.manifest_path)

    def test_extra_manifest_field_fails_closed(self):
        manifest = self.manifest()
        manifest["surprise"] = True
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "extra field"):
            verify(self.manifest_path)

    def test_malformed_canonical_json_fails_closed(self):
        self.canonical.write_bytes(b"{not json}\n")
        manifest = self.manifest()
        self.update_claim(manifest, "canonical", self.canonical)
        manifest["canonical"]["rows"] = 1
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "not valid JSON"):
            verify(self.manifest_path)

    def test_duplicate_canonical_keys_fail_closed(self):
        self.canonical.write_bytes(b'{"id":"one","id":"two"}\n')
        manifest = self.manifest()
        self.update_claim(manifest, "canonical", self.canonical)
        manifest["canonical"]["rows"] = 1
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "duplicate JSON key"):
            verify(self.manifest_path)

    def test_nonfinite_canonical_number_fails_closed(self):
        self.canonical.write_bytes(b'{"value":NaN}\n')
        manifest = self.manifest()
        self.update_claim(manifest, "canonical", self.canonical)
        manifest["canonical"]["rows"] = 1
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "non-finite JSON number"):
            verify(self.manifest_path)

    def test_capture_source_digest_is_checked_after_capture_rebinding(self):
        capture = json.loads(self.capture.read_text())
        capture["sha256"] = "0" * 64
        self.capture.write_bytes(canonical_json(capture) + b"\n")
        manifest = self.manifest()
        self.update_claim(manifest, "capture_manifest", self.capture)
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "source digest"):
            verify(self.manifest_path)

    def test_indexed_block_must_match_source_metadata(self):
        capture = json.loads(self.capture.read_text())
        capture["captured"]["indexed_block"] = 101
        self.capture.write_bytes(canonical_json(capture) + b"\n")
        manifest = self.manifest()
        self.update_claim(manifest, "capture_manifest", self.capture)
        manifest["source"]["indexed_block"] = 101
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "indexed block"):
            verify(self.manifest_path)

    def test_indexed_block_timestamp_must_match_source_metadata(self):
        capture = json.loads(self.capture.read_text())
        capture["captured"]["indexed_block_timestamp"] = 201
        self.capture.write_bytes(canonical_json(capture) + b"\n")
        manifest = self.manifest()
        self.update_claim(manifest, "capture_manifest", self.capture)
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "indexed block timestamp"):
            verify(self.manifest_path)

    def test_deployment_must_match_source_metadata(self):
        capture = json.loads(self.capture.read_text())
        capture["captured"]["deployment"] = "other-deployment"
        self.capture.write_bytes(canonical_json(capture) + b"\n")
        manifest = self.manifest()
        self.update_claim(manifest, "capture_manifest", self.capture)
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "deployment"):
            verify(self.manifest_path)

    def test_known_gap_omission_fails(self):
        manifest = self.manifest()
        manifest["known_gaps"].pop()
        self.write_manifest(manifest)
        with self.assertRaisesRegex(TabulariumError, "known semantic gaps"):
            verify(self.manifest_path)

    def test_verification_never_rewrites_release_bytes(self):
        paths = (self.source, self.capture, self.canonical, self.manifest_path)
        before = {path: path.read_bytes() for path in paths}
        verify(self.manifest_path)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
