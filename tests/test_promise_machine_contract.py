import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promise_machine.py"
LAW = ROOT / "PROMISE_MACHINE.md"
FIXTURE = ROOT / "tests" / "fixtures" / "promise-machine" / "divergent-copy"


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_plugin(root, name="example"):
    plugin = root / "plugins" / name
    manifest = plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"name":"example","version":"0.0.0"}\n', encoding="utf-8")
    return plugin


class PromiseLawTests(unittest.TestCase):
    def test_repository_law_and_copies_are_clean(self):
        completed = run_cli("check", "--only", "law,copies")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("clean: 14 plugin(s), 14 copy/copies", completed.stdout)

    def test_sync_check_is_read_only_and_clean(self):
        before = {path: path.read_bytes() for path in ROOT.glob("plugins/*/PROMISE_MACHINE.md")}
        completed = run_cli("sync", "--check")
        after = {path: path.read_bytes() for path in ROOT.glob("plugins/*/PROMISE_MACHINE.md")}
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(before, after)

    def test_all_plugin_copies_are_exact_and_marked(self):
        law = LAW.read_bytes()
        copies = sorted(ROOT.glob("plugins/*/PROMISE_MACHINE.md"))
        self.assertEqual(len(copies), 14)
        for copy in copies:
            with self.subTest(copy=copy):
                self.assertEqual(copy.read_bytes(), law)
                self.assertTrue(
                    any(
                        b"copies=generated" in line
                        for line in copy.read_bytes().splitlines()[:5]
                    )
                )

    def test_json_report_matches_the_text_result(self):
        completed = run_cli("check", "--only", "law,copies", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["contract"], "promise-machine/v1")
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["plugins"], 14)
        self.assertEqual(report["findings"], [])

    def test_divergent_copy_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            shutil.copytree(FIXTURE / "plugins", target / "plugins")
            completed = run_cli("check", "--root", target, "--only", "law,copies", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual([item["code"] for item in report["findings"]], ["PM014"])

    def test_empty_plugin_set_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            (target / "plugins").mkdir()
            completed = run_cli("check", "--root", target, "--only", "law,copies", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM010", [item["code"] for item in report["findings"]])

    def test_copy_only_refuses_an_absent_root_law(self):
        completed = run_cli(
            "check", "--root", FIXTURE, "--only", "copies", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(report["ok"])
        self.assertIn("PM001", [item["code"] for item in report["findings"]])

    def test_law_only_does_not_require_a_plugin_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            completed = run_cli(
                "check", "--root", target, "--only", "law", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["plugins"], 0)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_copy_is_refused_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            shutil.copy2(LAW, target / LAW.name)
            plugin = make_plugin(target)
            outside = Path(directory) / "outside.md"
            outside.write_bytes(LAW.read_bytes())
            (plugin / LAW.name).symlink_to(outside)
            completed = run_cli("sync", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM013", [item["code"] for item in report["findings"]])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_plugin_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            shutil.copy2(LAW, target / LAW.name)
            (target / "plugins").mkdir()
            outside = Path(directory) / "outside"
            make_plugin(outside)
            (target / "plugins" / "escape").symlink_to(outside / "plugins" / "example")
            completed = run_cli("sync", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM011", [item["code"] for item in report["findings"]])

    def test_sync_repairs_a_divergent_fixed_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            plugin = make_plugin(target)
            destination = plugin / LAW.name
            destination.write_text("drift\n", encoding="utf-8")
            completed = run_cli("sync", "--root", target, "--json")
            leftovers = list(plugin.glob(f".{LAW.name}.*"))
            repaired = destination.read_bytes()
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["written"], 1)
        self.assertEqual(repaired, LAW.read_bytes())
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
