"""Currency, retention, and hostile-input checks for Fiat audit synopses."""

from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "plugins"
    / "hexaemeron"
    / "skills"
    / "fiat"
    / "scripts"
    / "audit_synopsis.py"
)
FIXTURE = ROOT / "tests" / "fixtures" / "audit-synopsis" / "heterogeneous.md"
LIVE_SOURCES = (
    "audit/AUDIT.md",
    "plugins/ariadne/audit/AUDIT.md",
    "plugins/hexaemeron/audit/AUDIT.md",
    "plugins/pandects/audit/AUDIT.md",
    "plugins/probitas/audit/AUDIT.md",
    "plugins/tabularium/audit/AUDIT.md",
)


def synopsis_module():
    if not SCRIPT.is_file():
        return None
    spec = importlib.util.spec_from_file_location("audit_synopsis_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strict_record(verdict="null", *, omit=None, finding_row=None):
    lines = [
        "## Fixture, step 1, round 1 -- 2026-08-23T02:17:46Z",
        "",
        "Audit schema: fiat-audit-round/v1",
        "",
        "Covered: fixture-risk=reviewed",
        "",
        "Not checked: none",
        "",
        f"Elenchus verdict: {verdict}",
        "",
        "| id | severity | file | finding | status |",
        "| --- | --- | --- | --- | --- |",
        finding_row or "| -- | -- | -- | none | -- |",
        "",
        "Leads not pursued: none",
        "",
    ]
    if omit is not None:
        index = lines.index(omit)
        del lines[index:index + 2]
    return "\n".join(lines).encode()


class SynopsisFixtureTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "audit synopsis renderer is missing")
        self.module = synopsis_module()

    def test_heterogeneous_fixture_is_source_ordered_and_occurrence_preserving(self):
        source = FIXTURE.read_bytes()
        rendered = self.module.render_source("audit/AUDIT.md", source)
        source_text = source.decode("utf-8")
        source_lines = source_text.splitlines()
        headings = [line for line in source_lines if line.startswith("## ")]
        synopsis_lines = rendered["bytes"].decode("utf-8").splitlines()

        self.assertEqual(rendered["h2_count"], len(headings))
        self.assertEqual(len(synopsis_lines), len(headings) + 1)
        self.assertEqual(
            [line.split("<br>", 1)[0] for line in synopsis_lines[1:]],
            headings,
        )
        lead_lines = [line for line in source_lines if "Leads not pursued" in line]
        joined = "\n".join(synopsis_lines[1:])
        for line, count in Counter(lead_lines).items():
            self.assertEqual(joined.count(line), count, line)
        self.assertIn("continues on the next physical line.", joined)
        self.assertIn("| risk id | disposition |", joined)
        self.assertIn(
            "| risk id | status | evidence checked | disposition |", joined
        )
        self.assertIn("| id | severity | file | finding | status |", joined)
        for verdict in ("guarded", "unguarded", "passed", "inconclusive", "null"):
            self.assertIn(f"Elenchus verdict: {verdict}", joined)
        self.assertIn("[missing legacy field: audit-schema]", joined)
        self.assertIn("[missing legacy field: elenchus-verdict]", joined)
        self.assertIn("[missing legacy field: leads-not-pursued]", joined)

    def test_metadata_binds_schema_source_digest_and_h2_count_without_a_clock(self):
        source = FIXTURE.read_bytes()
        rendered = self.module.render_source("audit/AUDIT.md", source)
        metadata = rendered["bytes"].decode("utf-8").splitlines()[0]
        self.assertIn("fiat-audit-synopsis/v1", metadata)
        self.assertIn("source=audit/AUDIT.md", metadata)
        self.assertIn(f"source_sha256={hashlib.sha256(source).hexdigest()}", metadata)
        self.assertIn(f"h2_count={rendered['h2_count']}", metadata)
        self.assertNotRegex(metadata, r"20\d\d-\d\d-\d\d")

    def test_malformed_strict_records_refuse_instead_of_becoming_legacy(self):
        for omitted in (
            "Audit schema: fiat-audit-round/v1",
            "Covered: fixture-risk=reviewed",
            "Not checked: none",
            "Elenchus verdict: null",
            "| id | severity | file | finding | status |",
            "Leads not pursued: none",
        ):
            with self.subTest(omitted=omitted):
                with self.assertRaisesRegex(
                    self.module.SynopsisError, "strict record"
                ):
                    self.module.render_source(
                        "audit/AUDIT.md", strict_record(omit=omitted)
                    )

        malformed_heading = strict_record().replace(
            b"2026-08-23T02:17:46Z", b"2026-08-23"
        )
        with self.assertRaisesRegex(self.module.SynopsisError, "strict record"):
            self.module.render_source("audit/AUDIT.md", malformed_heading)

        injected_h3 = strict_record().replace(
            b"\nLeads not pursued: none\n",
            b"\n### injected non-canonical block\n\nLeads not pursued: none\n",
        )
        with self.assertRaisesRegex(self.module.SynopsisError, "strict record"):
            self.module.render_source("audit/AUDIT.md", injected_h3)

        mimicked_legacy_h3 = strict_record()
        for needle, heading in (
            (b"Covered: ", b"### Coverage\n\n"),
            (
                b"| id | severity | file | finding | status |",
                b"### Findings\n\n",
            ),
            (b"Leads not pursued: ", b"### Leads\n\n"),
        ):
            mimicked_legacy_h3 = mimicked_legacy_h3.replace(
                b"\n" + needle,
                b"\n" + heading + needle,
                1,
            )
        with self.assertRaisesRegex(self.module.SynopsisError, "strict record"):
            self.module.render_source("audit/AUDIT.md", mimicked_legacy_h3)

    def test_source_path_cannot_corrupt_synopsis_framing(self):
        for source_path in (
            "bad\nmetadata/audit/AUDIT.md",
            "bad|metadata/audit/AUDIT.md",
            "bad<br>metadata/audit/AUDIT.md",
            "bad\udcffmetadata/audit/AUDIT.md",
        ):
            with self.subTest(source_path=repr(source_path)):
                with self.assertRaisesRegex(
                    self.module.SynopsisError, "path has unsafe synopsis framing"
                ):
                    self.module.render_source(source_path, strict_record())

    def test_caps_and_integer_budget_refuse_before_output(self):
        with self.assertRaisesRegex(self.module.SynopsisError, "UTF-8"):
            self.module.render_source("audit/AUDIT.md", b"## bad\n\xff\n")
        with self.assertRaisesRegex(self.module.SynopsisError, "physical line"):
            self.module.render_source(
                "audit/AUDIT.md", b"## long\n" + b"x" * (1024 * 1024 + 1)
            )
        too_many = "".join(f"## record {index}\n\n" for index in range(10_001))
        with self.assertRaisesRegex(self.module.SynopsisError, "10,000 H2"):
            self.module.render_source("audit/AUDIT.md", too_many.encode())
        with self.assertRaisesRegex(self.module.SynopsisError, "16,777,216-byte"):
            self.module.render_source(
                "audit/AUDIT.md", b"x" * (16 * 1024 * 1024 + 1)
            )
        with self.assertRaisesRegex(self.module.SynopsisError, "15% line budget"):
            self.module.render_source("audit/AUDIT.md", b"## only line\n")
        exact_boundary = (
            "## first\n" + "filler\n" * 9 + "## second\n" + "filler\n" * 9
        )
        with self.assertRaisesRegex(self.module.SynopsisError, "15% line budget"):
            self.module.render_source("audit/AUDIT.md", exact_boundary.encode())


class SynopsisRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "audit synopsis CLI is missing")
        self.module = synopsis_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def source(self, relative="audit/AUDIT.md", verdict="null"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(strict_record(verdict))
        return path

    def test_write_check_staleness_missing_and_exact_regeneration(self):
        first = self.source()
        second = self.source("plugins/example/audit/AUDIT.md", "guarded")
        written = self.module.process_repository(str(self.root), write=True)
        self.assertEqual([item["source"] for item in written], [
            "audit/AUDIT.md", "plugins/example/audit/AUDIT.md"
        ])
        self.module.process_repository(str(self.root), write=False)

        first.write_bytes(strict_record("passed"))
        with self.assertRaisesRegex(self.module.SynopsisError, "stale"):
            self.module.process_repository(str(self.root), write=False)
        self.module.process_repository(str(self.root), write=True)
        self.module.process_repository(str(self.root), write=False)

        synopsis = second.with_name("AUDIT_SYNOPSIS.md")
        synopsis.write_bytes(synopsis.read_bytes() + b"drift\n")
        with self.assertRaisesRegex(self.module.SynopsisError, "stale"):
            self.module.process_repository(str(self.root), write=False)
        synopsis.unlink()
        with self.assertRaisesRegex(self.module.SynopsisError, "missing"):
            self.module.process_repository(str(self.root), write=False)
        self.module.process_repository(str(self.root), write=True)
        self.module.process_repository(str(self.root), write=False)

    def test_duplicate_leads_and_wrapped_tail_are_not_lossy(self):
        path = self.root / "audit" / "AUDIT.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            "## legacy -- 2026-08-23\n\n"
            "Leads not pursued: same\n"
            "wrapped reason\n"
            "Leads not pursued: same\n"
            + "\n" * 12,
            encoding="utf-8",
        )
        result = self.module.process_repository(str(self.root), write=True)[0]
        output = path.with_name("AUDIT_SYNOPSIS.md").read_text(encoding="utf-8")
        self.assertEqual(output.count("Leads not pursued: same"), 2)
        self.assertIn("wrapped reason", output)
        self.assertEqual(result["committed"], "written")

    def test_partial_temporary_write_keeps_old_complete_file_and_cleans_up(self):
        source = self.source()
        destination = source.with_name("AUDIT_SYNOPSIS.md")
        destination.write_bytes(b"old complete\n")

        def interrupted(descriptor, data):
            os.write(descriptor, data[:7])
            raise OSError("interrupted fixture write")

        with mock.patch.object(self.module, "_write_all", side_effect=interrupted):
            with self.assertRaisesRegex(self.module.SynopsisError, "temporary write"):
                self.module.process_repository(str(self.root), write=True)
        self.assertEqual(destination.read_bytes(), b"old complete\n")
        self.assertEqual(list(destination.parent.glob(".AUDIT_SYNOPSIS.md.*.tmp")), [])

    def test_mode_is_preserved_and_post_write_mismatch_is_refused(self):
        source = self.source()
        destination = source.with_name("AUDIT_SYNOPSIS.md")
        destination.write_bytes(b"old complete\n")
        destination.chmod(0o600)
        self.module.process_repository(str(self.root), write=True)
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)

        with mock.patch.object(
            self.module, "read_regular_bytes", return_value=b"post-write mismatch"
        ):
            with self.assertRaisesRegex(self.module.SynopsisError, "post-write"):
                self.module.atomic_replace(
                    str(self.root), "audit/AUDIT_SYNOPSIS.md", b"complete new\n"
                )

    def test_symlink_sources_outputs_and_escape_paths_refuse(self):
        source = self.source()
        outside = self.root / "outside.md"
        outside.write_bytes(strict_record())
        source.unlink()
        source.symlink_to(outside)
        with self.assertRaisesRegex(self.module.SynopsisError, "symlink"):
            self.module.process_repository(str(self.root), write=False)

        source.unlink()
        source.write_bytes(strict_record())
        output = source.with_name("AUDIT_SYNOPSIS.md")
        output.symlink_to(outside)
        with self.assertRaisesRegex(self.module.SynopsisError, "symlink"):
            self.module.process_repository(str(self.root), write=True)
        with self.assertRaisesRegex(self.module.SynopsisError, "escapes"):
            self.module.read_regular_bytes(str(self.root), "../outside.md", "source")

    def test_discovery_refuses_an_unreadable_subtree(self):
        self.source()
        blocked = self.root / "blocked"
        blocked.mkdir()

        def incomplete_walk(root, *, topdown, followlinks, onerror=None):
            if onerror is not None:
                onerror(PermissionError("fixture denied"))
            return iter(
                (
                    (root, ["audit", "blocked"], []),
                    (os.path.join(root, "audit"), [], ["AUDIT.md"]),
                )
            )

        with mock.patch.object(self.module.os, "walk", side_effect=incomplete_walk):
            with self.assertRaisesRegex(
                self.module.SynopsisError,
                "repository discovery cannot read a directory",
            ):
                self.module.discover_sources(str(self.root))

    def test_check_diagnostic_has_counts_ratio_and_all_digests(self):
        self.source()
        self.module.process_repository(str(self.root), write=True)
        out = StringIO()
        with redirect_stdout(out):
            code = self.module.main(["--check", str(self.root)])
        self.assertEqual(code, 0)
        line = out.getvalue()
        self.assertIn("source_lines=", line)
        self.assertIn("synopsis_lines=", line)
        self.assertIn("budget=pass", line)
        self.assertIn("source_sha256=", line)
        self.assertIn("fresh_sha256=", line)
        self.assertIn("committed_sha256=", line)
        self.assertIn("committed=match", line)


class LiveSynopsisCurrencyTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "audit synopsis renderer is missing")
        self.module = synopsis_module()

    def test_release_set_is_exact_current_and_below_budget(self):
        discovered = self.module.discover_sources(str(ROOT))
        self.assertEqual(tuple(discovered), LIVE_SOURCES)
        results = self.module.process_repository(str(ROOT), write=False)
        self.assertEqual(len(results), 6)
        for result in results:
            with self.subTest(source=result["source"]):
                self.assertEqual(result["committed"], "match")
                self.assertLess(
                    result["synopsis_lines"] * 100,
                    result["source_lines"] * 15,
                )

    def test_live_headings_leads_and_issue_327_values_survive(self):
        for relative in LIVE_SOURCES:
            with self.subTest(source=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                synopsis = (ROOT / relative).with_name(
                    "AUDIT_SYNOPSIS.md"
                ).read_text(encoding="utf-8")
                headings = [
                    line for line in source.splitlines() if line.startswith("## ")
                ]
                synopsis_records = synopsis.splitlines()[1:]
                self.assertEqual(
                    [line.split("<br>", 1)[0] for line in synopsis_records],
                    headings,
                )
                retained_lines = Counter(
                    physical
                    for record in synopsis_records
                    for physical in record.split("<br>")
                )
                for line, count in Counter(
                    line
                    for line in source.splitlines()
                    if "Leads not pursued" in line
                ).items():
                    self.assertEqual(retained_lines[line], count, line)
                for verdict in ("guarded", "unguarded", "passed", "inconclusive"):
                    field = f"Elenchus verdict: {verdict}"
                    if field in source:
                        self.assertIn(field, synopsis)

    def test_synopses_are_not_hard_classified_by_horos(self):
        boundary = json.loads((ROOT / ".horos" / "boundary.json").read_text())
        synopsis_entries = [
            entry
            for entry in boundary["entries"]
            if entry["path"].endswith("/AUDIT_SYNOPSIS.md")
            or entry["path"] == "audit/AUDIT_SYNOPSIS.md"
        ]
        self.assertEqual(synopsis_entries, [])


if __name__ == "__main__":
    unittest.main()
