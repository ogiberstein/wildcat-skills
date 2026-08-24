"""Tests for the report-only dead-code command's universe, rendering and writes."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dead_code.py"
SCHEMA_PATH = ROOT / "schemas" / "dead-code-report-v1.schema.json"

SPEC = importlib.util.spec_from_file_location("dead_code", SCRIPT)
dead_code = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = dead_code
SPEC.loader.exec_module(dead_code)


def git(directory, *arguments):
    subprocess.run(
        ["git", "-C", str(directory), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def build_repository(directory, files, boundary_entries, commit=True):
    """Create a git repository holding `files` and a Horos boundary document."""
    git(directory, "init", "--quiet", "--initial-branch=main")
    git(directory, "config", "user.email", "test@example.invalid")
    git(directory, "config", "user.name", "Test")
    git(directory, "config", "commit.gpgsign", "false")
    for relative, content in files.items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    boundary = directory / ".horos" / "boundary.json"
    boundary.parent.mkdir(parents=True, exist_ok=True)
    boundary.write_text(
        json.dumps({"schema": 2, "tool": "horos", "universe": "tracked", "counts": {}, "entries": boundary_entries}),
        encoding="utf-8",
    )
    git(directory, "add", "-A")
    if commit:
        git(directory, "commit", "--quiet", "-m", "fixture")
    return directory


def entry(path, category="generated", evidence="marker 'do not edit'", grade="hard"):
    return {"path": path, "category": category, "evidence": evidence, "grade": grade, "bytes": 1}


class TemporaryRepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.root = Path(self._directory.name).resolve()


class UniverseDiscoveryTests(TemporaryRepositoryTestCase):
    def test_the_universe_is_the_tracked_tree_at_the_analysed_commit(self):
        build_repository(
            self.root,
            {"a.py": "x = 1\n", "pkg/b.py": "y = 2\n"},
            [],
        )
        universe = dead_code.discover(self.root)
        self.assertIn("a.py", universe.analysed)
        self.assertIn("pkg/b.py", universe.analysed)
        self.assertEqual(universe.commit, dead_code.resolve_commit(self.root))
        self.assertEqual(len(universe.commit), 40)

    def test_an_untracked_file_is_neither_analysed_nor_a_refusal(self):
        build_repository(self.root, {"a.py": "x = 1\n"}, [])
        (self.root / "scratch.txt").write_text("ignore me", encoding="utf-8")
        universe = dead_code.discover(self.root)
        self.assertNotIn("scratch.txt", universe.analysed)

    def test_a_modified_tracked_file_refuses_and_names_the_count(self):
        build_repository(self.root, {"a.py": "x = 1\n"}, [])
        (self.root / "a.py").write_text("x = 2\n", encoding="utf-8")
        with self.assertRaises(dead_code.Refusal) as caught:
            dead_code.discover(self.root)
        self.assertIn("modified tracked file", str(caught.exception))

    def test_a_collapsed_universe_stops_rather_than_reporting_zero_findings(self):
        build_repository(
            self.root,
            {"generated.md": "x\n"},
            [entry("generated.md"), entry(".horos/boundary.json")],
        )
        with self.assertRaises(dead_code.Refusal) as caught:
            dead_code.discover(self.root)
        self.assertIn("collapsed walk", str(caught.exception))

    def test_discovery_refuses_outside_a_git_worktree(self):
        with self.assertRaises(dead_code.Refusal):
            dead_code.repository_root(self.root)


class ClassificationJoinTests(TemporaryRepositoryTestCase):
    def test_a_hard_classified_path_leaves_the_universe_carrying_its_evidence(self):
        build_repository(
            self.root,
            {"a.py": "x = 1\n", "CONTRIBUTORS.md": "generated\n"},
            [entry("CONTRIBUTORS.md", evidence="marker 'do not edit' in the first 4096 bytes")],
        )
        universe = dead_code.discover(self.root)
        self.assertNotIn("CONTRIBUTORS.md", universe.analysed)
        excluded = {item.path: item for item in universe.excluded}
        self.assertEqual(excluded["CONTRIBUTORS.md"].category, "generated")
        self.assertIn("do not edit", excluded["CONTRIBUTORS.md"].evidence)

    def test_a_candidate_grade_does_not_exclude_because_the_boundary_is_fail_open(self):
        build_repository(
            self.root,
            {"a.py": "x = 1\n", "blob.json": "{}\n"},
            [entry("blob.json", category="blob", grade="candidate")],
        )
        universe = dead_code.discover(self.root)
        self.assertIn("blob.json", universe.analysed)
        self.assertEqual(universe.excluded, ())

    def test_a_boundary_entry_for_an_absent_path_excludes_nothing(self):
        build_repository(self.root, {"a.py": "x = 1\n"}, [entry("gone.md")])
        universe = dead_code.discover(self.root)
        self.assertEqual(universe.excluded, ())

    def test_the_excluded_counts_group_by_category(self):
        build_repository(
            self.root,
            {"a.py": "x\n", "g1.md": "x\n", "g2.md": "x\n", "v.js": "x\n"},
            [entry("g1.md"), entry("g2.md"), entry("v.js", category="vendored")],
        )
        universe = dead_code.discover(self.root)
        self.assertEqual(universe.excluded_by_category(), {"generated": 2, "vendored": 1})


class BoundaryRefusalTests(TemporaryRepositoryTestCase):
    def _repository_with_boundary(self, text):
        build_repository(self.root, {"a.py": "x = 1\n"}, [])
        (self.root / ".horos" / "boundary.json").write_text(text, encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "--quiet", "-m", "boundary")

    def test_an_absent_boundary_is_refused_by_name(self):
        build_repository(self.root, {"a.py": "x = 1\n"}, [])
        (self.root / ".horos" / "boundary.json").unlink()
        git(self.root, "add", "-A")
        git(self.root, "commit", "--quiet", "-m", "drop boundary")
        with self.assertRaises(dead_code.Refusal) as caught:
            dead_code.load_boundary(self.root)
        self.assertIn(".horos/boundary.json", str(caught.exception))

    def test_a_boundary_that_is_not_json_is_refused_by_name(self):
        self._repository_with_boundary("{not json")
        with self.assertRaises(dead_code.Refusal) as caught:
            dead_code.load_boundary(self.root)
        self.assertIn("not valid JSON", str(caught.exception))

    def test_a_boundary_without_an_entries_list_is_refused(self):
        self._repository_with_boundary(json.dumps({"tool": "horos"}))
        with self.assertRaises(dead_code.Refusal) as caught:
            dead_code.load_boundary(self.root)
        self.assertIn("no entries list", str(caught.exception))

    def test_a_boundary_entry_missing_evidence_is_refused_rather_than_read_as_empty(self):
        broken = {"path": "a.py", "category": "generated", "grade": "hard"}
        self._repository_with_boundary(json.dumps({"entries": [broken]}))
        with self.assertRaises(dead_code.Refusal) as caught:
            dead_code.load_boundary(self.root)
        self.assertIn("evidence", str(caught.exception))


class RenderingTests(TemporaryRepositoryTestCase):
    def _report(self):
        build_repository(
            self.root,
            {"a.py": "x = 1\n", "b.py": "y = 2\n", "gen.md": "x\n"},
            [entry("gen.md")],
        )
        return dead_code.build_report(self.root)

    def test_the_json_rendering_validates_against_the_committed_schema_shape(self):
        document = json.loads(dead_code.render_json(self._report()))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        for name in schema["required"]:
            self.assertIn(name, document)
        self.assertEqual(document["schema"], schema["properties"]["schema"]["const"])
        self.assertEqual(document["tool"], schema["properties"]["tool"]["const"])

    def test_both_renderings_read_one_model_and_agree_on_the_counts(self):
        report = self._report()
        document = json.loads(dead_code.render_json(report))
        text = dead_code.render_text(report)
        self.assertIn(document["commit"], text)
        self.assertIn(f"{document['universe']['analysed_count']} analysed", text)
        self.assertIn(f"{document['universe']['excluded_count']} excluded", text)
        self.assertIn(f"findings  {len(document['findings'])}", text)

    def test_the_text_report_names_every_finding_the_json_carries(self):
        report = self._report()
        finding = dead_code.Finding(
            analyser="python",
            path="pkg/orphan.py",
            symbol="never_called",
            evidence="no module imports pkg.orphan",
            confidence="medium",
            false_positive_boundary="a plugin loader could import it by computed name",
        )
        report = dead_code.Report(
            commit=report.commit,
            universe=report.universe,
            statuses=report.statuses,
            findings=(finding,),
        )
        text = dead_code.render_text(report)
        document = json.loads(dead_code.render_json(report))
        self.assertEqual(len(document["findings"]), 1)
        for value in (finding.path, finding.symbol, finding.evidence, finding.false_positive_boundary):
            self.assertIn(value, text)

    def test_a_report_with_no_analyser_says_it_establishes_nothing(self):
        text = dead_code.render_text(self._report())
        self.assertIn("none registered", text)
        self.assertIn("establishes no reachability result", text)

    def test_no_rendering_calls_a_candidate_dead_or_safe_to_delete(self):
        report = self._report()
        text = dead_code.render_text(report).lower()
        rendered_json = dead_code.render_json(report).lower()
        for forbidden in ("is dead", "safe to delete", "unused code", "can be removed"):
            self.assertNotIn(forbidden, text)
            self.assertNotIn(forbidden, rendered_json)


class WriteTargetTests(TemporaryRepositoryTestCase):
    def setUp(self):
        super().setUp()
        build_repository(self.root, {"a.py": "x = 1\n", "b.py": "y = 2\n"}, [])

    def test_a_path_outside_the_repository_is_refused(self):
        with self.assertRaises(dead_code.Refusal) as caught:
            dead_code.confine(self.root, "../escape.json")
        self.assertIn("escapes the repository root", str(caught.exception))

    def test_an_absolute_path_outside_the_repository_is_refused(self):
        with self.assertRaises(dead_code.Refusal):
            dead_code.confine(self.root, str(Path(tempfile.gettempdir()) / "escape.json"))

    def test_the_repository_root_itself_is_not_a_write_target(self):
        with self.assertRaises(dead_code.Refusal):
            dead_code.confine(self.root, ".")

    def test_a_null_byte_in_the_path_is_refused(self):
        with self.assertRaises(dead_code.Refusal):
            dead_code.confine(self.root, "out\x00.json")

    def test_a_descendant_path_resolves_inside_the_repository(self):
        resolved = dead_code.confine(self.root, "reports/out.json")
        self.assertEqual(resolved, (self.root / "reports" / "out.json").resolve())

    def test_the_write_is_atomic_and_leaves_no_temporary_behind(self):
        target = self.root / "reports" / "out.json"
        dead_code.atomic_write(target, "payload\n")
        self.assertEqual(target.read_text(encoding="utf-8"), "payload\n")
        leftovers = [item.name for item in target.parent.iterdir() if item.name.startswith(dead_code.TEMP_PREFIX)]
        self.assertEqual(leftovers, [])

    def test_the_sweep_removes_this_command_s_orphans_and_spares_a_bystander(self):
        directory = self.root / "reports"
        directory.mkdir()
        orphan = directory / f"{dead_code.TEMP_PREFIX}abandoned"
        bystander = directory / "keep.json"
        orphan.write_text("half", encoding="utf-8")
        bystander.write_text("{}", encoding="utf-8")
        dead_code.sweep_orphans(directory)
        self.assertFalse(orphan.exists())
        self.assertTrue(bystander.exists())


class CommandLineTests(TemporaryRepositoryTestCase):
    def _run(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--directory", str(self.root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def setUp(self):
        super().setUp()
        build_repository(
            self.root,
            {"a.py": "x = 1\n", "b.py": "y = 2\n", "gen.md": "x\n"},
            [entry("gen.md")],
        )

    def test_the_text_report_exits_zero_and_names_the_commit(self):
        completed = self._run("report")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("dead-code report", completed.stdout)
        self.assertIn("universe  3 analysed, 1 excluded", completed.stdout)

    def test_the_json_report_exits_zero_and_parses(self):
        completed = self._run("report", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        document = json.loads(completed.stdout)
        self.assertEqual(document["schema"], "dead-code-report/v1")
        self.assertEqual(document["universe"]["analysed_count"], 3)

    def test_a_refusal_exits_two_and_says_why_on_stderr(self):
        (self.root / "a.py").write_text("x = 3\n", encoding="utf-8")
        completed = self._run("report")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("modified tracked file", completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_the_output_flag_writes_the_report_inside_the_repository(self):
        completed = self._run("report", "--json", "--output", "reports/out.json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        written = json.loads((self.root / "reports" / "out.json").read_text(encoding="utf-8"))
        self.assertEqual(written["universe"]["analysed_count"], 3)

    def test_the_output_flag_refuses_a_path_outside_the_repository(self):
        completed = self._run("report", "--output", "../escape.json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("escapes the repository root", completed.stderr)


class SurfaceTests(unittest.TestCase):
    def test_the_command_never_removes_a_source_path(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("shutil.rmtree", "os.remove(", "shell=True"):
            self.assertNotIn(forbidden, source)

    def test_the_only_unlink_is_the_command_s_own_temporary_sweep(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(source.count(".unlink()"), 2)
        self.assertIn("TEMP_PREFIX", source)

    def test_the_workflow_parses_and_declares_a_read_only_token(self):
        workflow = ROOT / ".github" / "workflows" / "dead-code.yml"
        self.assertTrue(workflow.is_file())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)

    def test_the_committed_study_and_runbook_are_present(self):
        self.assertTrue((ROOT / "docs" / "dead-code-study.md").is_file())
        self.assertTrue((ROOT / "docs" / "dead-code-runbook.md").is_file())

    def test_the_temporary_prefix_is_ignored_by_git(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(dead_code.TEMP_PREFIX, ignore)


if __name__ == "__main__":
    unittest.main()
