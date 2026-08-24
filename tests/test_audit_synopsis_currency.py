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
import tracemalloc
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

    def test_leads_outside_a_raw_h2_record_refuse_instead_of_disappearing(self):
        source = (
            b"# prelude\n"
            b"Leads not pursued: hidden before the first record\n\n"
            + strict_record()
        )
        with self.assertRaisesRegex(
            self.module.SynopsisError, "outside a raw H2 record"
        ):
            self.module.render_source("audit/AUDIT.md", source)

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

        heading_only = (
            b"## Fixture, step 1, round 1 -- 2026-08-23T02:17:46Z\n\n"
            + b"not a strict field\n" * 13
        )
        with self.assertRaisesRegex(self.module.SynopsisError, "strict record"):
            self.module.render_source("audit/AUDIT.md", heading_only)

        schema_less_h3 = (
            b"## Fixture, step 1, round 1 -- 2026-08-23T02:17:46Z\n\n"
            b"### historical section\n\n"
            + b"legacy prose\n" * 11
        )
        rendered = self.module.render_source("audit/AUDIT.md", schema_less_h3)
        self.assertIn(b"[missing legacy field: audit-schema]", rendered["bytes"])

    def test_strict_record_boundaries_require_the_canonical_lf_bytes(self):
        canonical = strict_record()
        self.module.render_source("audit/AUDIT.md", canonical)

        with self.assertRaisesRegex(self.module.SynopsisError, "terminal LF"):
            self.module.render_source("audit/AUDIT.md", canonical[:-1])
        with self.assertRaisesRegex(self.module.SynopsisError, "trailing blank"):
            self.module.render_source("audit/AUDIT.md", canonical + b"\n")
        with self.assertRaisesRegex(self.module.SynopsisError, "record separator"):
            self.module.render_source("audit/AUDIT.md", canonical + canonical)

        legacy = b"## legacy\n" + b"legacy prose\n" * 13
        with self.assertRaisesRegex(self.module.SynopsisError, "record separator"):
            self.module.render_source("audit/AUDIT.md", legacy + canonical)
        self.module.render_source("audit/AUDIT.md", legacy + b"\n" + canonical)
        with self.assertRaisesRegex(self.module.SynopsisError, "record separator"):
            self.module.render_source(
                "audit/AUDIT.md", legacy + b"\n\n" + canonical
            )

        legacy_crlf = (
            b"## legacy\r\nLeads not pursued: none\r\n"
            + b"legacy prose\r\n" * 12
        )
        with self.assertRaisesRegex(self.module.SynopsisError, "LF line endings"):
            self.module.render_source("audit/AUDIT.md", legacy_crlf)

        with self.assertRaisesRegex(self.module.SynopsisError, "no raw H2"):
            self.module.render_source("audit/AUDIT.md", b"")

    def test_source_path_cannot_corrupt_synopsis_framing(self):
        for source_path in (
            "bad\nmetadata/audit/AUDIT.md",
            "bad|metadata/audit/AUDIT.md",
            "bad<br>metadata/audit/AUDIT.md",
            "bad<BR>metadata/audit/AUDIT.md",
            "bad<br />metadata/audit/AUDIT.md",
            "bad\u0085metadata/audit/AUDIT.md",
            "bad\u2028metadata/audit/AUDIT.md",
            "bad\u202emetadata/audit/AUDIT.md",
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

    def test_many_short_lines_remain_inside_the_receipted_acceptance_domain(self):
        source = b"## legacy\nLeads not pursued:\n" + b"x\n" * 200_000
        rendered = self.module.render_source("audit/AUDIT.md", source)

        self.assertEqual(rendered["source_lines"], 200_002)
        self.assertEqual(rendered["h2_count"], 1)
        self.assertLess(len(rendered["bytes"]), self.module.SYNOPSIS_BYTES_MAX)

    def test_legacy_tail_rendering_does_not_allocate_per_physical_line(self):
        source = b"## legacy\nLeads not pursued:\n" + b"x\n" * 150_000
        tracemalloc.start()
        try:
            rendered = self.module.render_source("audit/AUDIT.md", source)
            _, peak_bytes = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        self.assertEqual(
            hashlib.sha256(rendered["bytes"]).hexdigest(),
            "b07dabc87790c93359c1aeb13e765f9fe91b551de387a23726ff3866fbbb2760",
        )
        self.assertLess(
            peak_bytes,
            len(source) * 24,
            f"legacy-tail rendering peaked at {peak_bytes} bytes "
            f"for {len(source)} source bytes",
        )


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

    def test_root_resolution_refuses_an_observed_rebind(self):
        repository = self.root / "repository"
        repository.mkdir()
        moved = self.root / "moved-repository"
        outside = self.root / "outside"
        outside.mkdir()
        realpath = self.module.os.path.realpath
        rebound = False

        def rebind_before_resolution(path):
            nonlocal rebound
            if os.path.abspath(path) == str(repository) and not rebound:
                rebound = True
                repository.rename(moved)
                repository.symlink_to(outside, target_is_directory=True)
            return realpath(path)

        with mock.patch.object(
            self.module.os.path, "realpath", side_effect=rebind_before_resolution
        ):
            with self.assertRaisesRegex(
                self.module.SynopsisError, "repository root changed during access"
            ):
                self.module._root_path(str(repository))
        self.assertTrue(rebound)

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

    def test_discovery_excludes_state_sinks_and_skips_unrelated_symlink_trees(self):
        self.source()
        for hidden in (".git", ".hexaemeron"):
            hidden_source = self.root / hidden / "nested" / "audit" / "AUDIT.md"
            hidden_source.parent.mkdir(parents=True)
            hidden_source.write_bytes(strict_record())
        outside_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_tmp.cleanup)
        outside_source = Path(outside_tmp.name) / "audit" / "AUDIT.md"
        outside_source.parent.mkdir()
        outside_source.write_bytes(strict_record())
        (self.root / "linked-tree").symlink_to(
            Path(outside_tmp.name), target_is_directory=True
        )

        self.assertEqual(
            self.module.discover_sources(str(self.root)), ["audit/AUDIT.md"]
        )

    def test_discovery_skips_nested_git_worktrees_and_repositories(self):
        self.source()
        worktree = self.root / "tmp" / "fiat" / "active-run"
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        nested_source = worktree / "audit" / "AUDIT.md"
        nested_source.parent.mkdir()
        nested_source.write_bytes(strict_record())

        repository = self.root / "nested-repository"
        (repository / ".git").mkdir(parents=True)
        nested_source = repository / "audit" / "AUDIT.md"
        nested_source.parent.mkdir()
        nested_source.write_bytes(strict_record())

        self.assertEqual(
            self.module.discover_sources(str(self.root)), ["audit/AUDIT.md"]
        )

    def test_discovery_refuses_nonregular_reserved_source_names(self):
        self.source()
        reserved = self.root / "plugins" / "example" / "audit" / "AUDIT.md"
        reserved.mkdir(parents=True)
        with self.assertRaisesRegex(
            self.module.SynopsisError, "audit source is not a regular file"
        ):
            self.module.discover_sources(str(self.root))

        reserved.rmdir()
        outside = self.root / "outside-directory"
        outside.mkdir()
        reserved.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(
            self.module.SynopsisError, "audit source is a symlink"
        ):
            self.module.discover_sources(str(self.root))

    def test_descriptor_races_refuse_source_swaps_and_do_not_follow_output_swaps(self):
        source = self.source()
        outside = self.root / "outside.md"
        outside.write_bytes(strict_record("guarded"))
        open_directory = self.module._directory_descriptor
        swapped = False

        def swap_source_then_open(root, components, label):
            nonlocal swapped
            if label == "audit source" and not swapped:
                source.unlink()
                source.symlink_to(outside)
                swapped = True
            return open_directory(root, components, label)

        with mock.patch.object(
            self.module, "_directory_descriptor", side_effect=swap_source_then_open
        ):
            with self.assertRaisesRegex(self.module.SynopsisError, "cannot be read"):
                self.module.read_regular_bytes(
                    str(self.root), "audit/AUDIT.md", "audit source"
                )

        source.unlink()
        source.write_bytes(strict_record())
        destination = source.with_name("AUDIT_SYNOPSIS.md")
        destination.write_bytes(b"old complete\n")
        outside.write_bytes(b"outside unchanged\n")
        write_all = self.module._write_all

        def swap_output_after_write(descriptor, data):
            write_all(descriptor, data)
            destination.unlink()
            destination.symlink_to(outside)

        with mock.patch.object(
            self.module, "_write_all", side_effect=swap_output_after_write
        ):
            self.module.atomic_replace(
                str(self.root), "audit/AUDIT_SYNOPSIS.md", b"new complete\n"
            )
        self.assertEqual(outside.read_bytes(), b"outside unchanged\n")
        self.assertEqual(destination.read_bytes(), b"new complete\n")

    def test_descriptor_read_refuses_an_observed_in_place_rewrite(self):
        source = self.source()
        original = source.read_bytes()
        changed = original.replace(b"Not checked: none", b"Not checked: nope")
        self.assertEqual(len(original), len(changed))
        real_read = self.module.os.read
        raced = False

        def rewrite_after_read(descriptor, size):
            nonlocal raced
            chunk = real_read(descriptor, size)
            if not raced:
                source.write_bytes(changed)
                raced = True
            return chunk

        with mock.patch.object(self.module.os, "read", side_effect=rewrite_after_read):
            with self.assertRaisesRegex(self.module.SynopsisError, "changed during read"):
                self.module.read_regular_bytes(
                    str(self.root), "audit/AUDIT.md", "audit source"
                )

    def test_descriptor_read_refuses_an_observed_parent_rebind(self):
        source = self.source()
        original = source.read_bytes()
        changed = original.replace(b"Not checked: none", b"Not checked: nope")
        audit_directory = source.parent
        moved_directory = self.root / "moved-audit"
        real_read = self.module.os.read
        raced = False

        def rebind_parent_after_read(descriptor, size):
            nonlocal raced
            chunk = real_read(descriptor, size)
            if chunk and not raced:
                raced = True
                audit_directory.rename(moved_directory)
                audit_directory.mkdir()
                (audit_directory / "AUDIT.md").write_bytes(changed)
            return chunk

        with mock.patch.object(
            self.module.os, "read", side_effect=rebind_parent_after_read
        ):
            with self.assertRaisesRegex(self.module.SynopsisError, "changed during read"):
                self.module.read_regular_bytes(
                    str(self.root), "audit/AUDIT.md", "audit source"
                )

    def test_parent_rebind_cannot_redirect_atomic_replacement(self):
        source = self.source()
        destination = source.with_name("AUDIT_SYNOPSIS.md")
        destination.write_bytes(b"old complete\n")
        audit_directory = source.parent
        moved_directory = self.root / "moved-audit"
        write_all = self.module._write_all

        def rebind_parent_after_write(descriptor, data):
            write_all(descriptor, data)
            audit_directory.rename(moved_directory)
            audit_directory.mkdir()

        with mock.patch.object(
            self.module, "_write_all", side_effect=rebind_parent_after_write
        ):
            with self.assertRaisesRegex(
                self.module.SynopsisError, "directory changed during write"
            ):
                self.module.atomic_replace(
                    str(self.root), "audit/AUDIT_SYNOPSIS.md", b"new complete\n"
                )
        self.assertEqual(
            (moved_directory / "AUDIT_SYNOPSIS.md").read_bytes(),
            b"old complete\n",
        )
        self.assertEqual(
            list(moved_directory.glob(".AUDIT_SYNOPSIS.md.*.tmp")), []
        )

    def test_unsafe_discovery_path_cannot_frame_an_error(self):
        unsafe_parent = self.root / "bad\nspoof"
        unsafe_parent.mkdir()
        (unsafe_parent / "audit").symlink_to(self.root, target_is_directory=True)

        with self.assertRaises(self.module.SynopsisError) as raised:
            self.module.discover_sources(str(self.root))
        self.assertNotIn("\n", str(raised.exception))
        self.assertIn(r"bad\nspoof", str(raised.exception))

        (unsafe_parent / "audit").unlink()
        (unsafe_parent / "audit").mkdir()
        (unsafe_parent / "audit" / "AUDIT.md").symlink_to(
            self.root / "outside.md"
        )
        with self.assertRaises(self.module.SynopsisError) as raised:
            self.module.discover_sources(str(self.root))
        self.assertNotIn("\n", str(raised.exception))
        self.assertIn(r"bad\nspoof", str(raised.exception))

    def test_oversized_fresh_render_refuses_before_replacement(self):
        source = self.root / "audit" / "AUDIT.md"
        source.parent.mkdir(parents=True)
        source.write_bytes(
            b"## legacy\nLeads not pursued: none\n" + b"legacy prose\n" * 12
        )
        destination = source.with_name("AUDIT_SYNOPSIS.md")
        destination.write_bytes(b"old complete\n")

        with mock.patch.object(self.module, "SYNOPSIS_BYTES_MAX", 128):
            with self.assertRaisesRegex(self.module.SynopsisError, "synopsis exceeds"):
                self.module.process_repository(str(self.root), write=True)
        self.assertEqual(destination.read_bytes(), b"old complete\n")

    def test_write_repairs_an_oversized_committed_synopsis(self):
        source = self.source()
        destination = source.with_name("AUDIT_SYNOPSIS.md")
        destination.write_bytes(b"x" * (self.module.SYNOPSIS_BYTES_MAX + 1))

        self.module.process_repository(str(self.root), write=True)
        self.module.process_repository(str(self.root), write=False)
        self.assertLess(destination.stat().st_size, self.module.SYNOPSIS_BYTES_MAX)

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

    def test_pinned_legacy_schema_drafts_bind_path_ordinal_and_exact_bytes(self):
        source = (ROOT / "audit" / "AUDIT.md").read_bytes()
        text = source.decode("utf-8")
        lines = text.split("\n")
        if text.endswith("\n"):
            lines.pop()
        starts = [
            index for index, line in enumerate(lines) if self.module._is_h2(line)
        ]
        starts.append(len(lines))
        offsets = []
        cursor = 0
        for physical in source.splitlines(keepends=True):
            offsets.append(cursor)
            cursor += len(physical)

        self.assertEqual(
            tuple(self.module.PINNED_LEGACY_SCHEMA_DRAFTS), tuple(range(344, 354))
        )
        for ordinal, expected_digest in (
            self.module.PINNED_LEGACY_SCHEMA_DRAFTS.items()
        ):
            with self.subTest(ordinal=ordinal):
                record = lines[starts[ordinal - 1]:starts[ordinal]]
                raw = ("\n".join(record) + "\n").encode("utf-8")
                actual = source[offsets[starts[ordinal - 1]]:offsets[starts[ordinal]]]
                headings = tuple(
                    line for line in record[1:] if line.startswith("###")
                )
                self.assertEqual(raw, actual)
                self.assertTrue(actual.endswith(b"\n\n"))
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected_digest)
                self.assertTrue(
                    self.module._pinned_legacy_schema_draft(
                        record, ordinal, "audit/AUDIT.md", headings
                    )
                )
                changed = [*record[:-1], record[-1] + "x"]
                self.assertFalse(
                    self.module._pinned_legacy_schema_draft(
                        changed, ordinal, "audit/AUDIT.md", headings
                    )
                )
                self.assertFalse(
                    self.module._pinned_legacy_schema_draft(
                        record, ordinal + 100, "audit/AUDIT.md", headings
                    )
                )
                self.assertFalse(
                    self.module._pinned_legacy_schema_draft(
                        record, ordinal, "plugins/x/audit/AUDIT.md", headings
                    )
                )
                if ordinal == 344:
                    schema_index = record.index(
                        "Audit schema: fiat-audit-round/v1"
                    )
                    schema_changed = [*record]
                    schema_changed[schema_index] = (
                        "Audit scheme: fiat-audit-round/v1"
                    )
                    changed_raw = (
                        "\n".join(schema_changed) + "\n"
                    ).encode("utf-8")
                    changed_source = (
                        source[:offsets[starts[ordinal - 1]]]
                        + changed_raw
                        + source[offsets[starts[ordinal]]:]
                    )
                    with self.assertRaisesRegex(
                        self.module.SynopsisError, "strict record 344"
                    ):
                        self.module.render_source(
                            "audit/AUDIT.md", changed_source
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
