"""The Alexandria scaffold is portable and makes no operational claim."""

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
COMMAND = PLUGIN_ROOT / "scripts" / "alexandria.py"
COMPOUND_COMMAND = PLUGIN_ROOT / "scripts" / "compound_v3_phase0.py"
SKILL = PLUGIN_ROOT / "skills" / "alexandria" / "SKILL.md"
PLANNED = ("ingest", "verify", "derive", "index", "query")


def run(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class AlexandriaScaffoldTests(unittest.TestCase):
    def test_help_names_every_planned_operation(self):
        result = run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("offline lending-data archive", result.stdout)
        for command in PLANNED:
            with self.subTest(command=command):
                self.assertIn(command, result.stdout)

    def test_compound_phase0_cli_keeps_network_capture_explicit(self):
        result = subprocess.run(
            [sys.executable, str(COMPOUND_COMMAND), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("registry", "capture", "build", "check"):
            self.assertIn(command, result.stdout)

    def test_no_command_is_a_controlled_usage_error(self):
        result = run()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_subcommand_help_succeeds_without_running_an_operation(self):
        for command in PLANNED:
            with self.subTest(command=command):
                result = run(command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)
                self.assertNotIn("not implemented", result.stderr)

    def test_implemented_operations_require_their_inputs(self):
        for command in ("ingest", "verify", "derive", "index", "query"):
            with self.subTest(command=command):
                result = run(command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("required", result.stderr)

    def test_unknown_operation_is_a_controlled_parser_error(self):
        result = run("harvest")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_skill_is_canonical_and_has_no_browsable_readme_shadow(self):
        self.assertTrue(SKILL.is_file())
        self.assertFalse((SKILL.parent / "README.md").exists())

    def test_skill_frontmatter_matches_its_directory(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        match = re.search(r"(?m)^name:\s*([^\n]+)$", text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), SKILL.parent.name)
        self.assertIn("Raw release and registered", text)

    def test_package_metadata_agrees_and_points_at_the_skill(self):
        manifests = []
        for host in (".claude-plugin", ".codex-plugin"):
            path = PLUGIN_ROOT / host / "plugin.json"
            manifests.append(json.loads(path.read_text(encoding="utf-8")))
        marketplace = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        package = next(
            item["version"]
            for item in marketplace["plugins"]
            if item["name"] == "alexandria"
        )
        self.assertEqual([item["name"] for item in manifests], ["alexandria"] * 2)
        self.assertEqual([item["version"] for item in manifests], [package] * 2)
        self.assertEqual(package, "0.2.1")
        self.assertEqual([item["skills"] for item in manifests], ["./skills/"] * 2)
        self.assertTrue(SKILL.is_file())

    def test_promise_machine_router_resolves_to_runtime_contract(self):
        entrypoint = REPO_ROOT / ".agents" / "skills" / "promise-machine" / "SKILL.md"
        text = entrypoint.read_text(encoding="utf-8")
        self.assertIn("name: promise-machine", text)
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
        self.assertIn("../../../plugins/alexandria/AGENTS.md", links)
        contract = (PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("`skills/alexandria/SKILL.md`", contract)

    def test_marketplaces_use_the_local_plugin_path(self):
        claude = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text()
        )
        codex = json.loads(
            (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text()
        )
        claude_entry = next(p for p in claude["plugins"] if p["name"] == "alexandria")
        codex_entry = next(p for p in codex["plugins"] if p["name"] == "alexandria")
        self.assertEqual(claude_entry["source"], "./plugins/alexandria")
        self.assertEqual(codex_entry["source"]["path"], "./plugins/alexandria")

    def test_design_records_are_committed(self):
        study = (PLUGIN_ROOT / "docs" / "study.md").read_text(encoding="utf-8")
        runbook = (PLUGIN_ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
        self.assertTrue(study.startswith("# Alexandria study\n"))
        self.assertTrue(runbook.startswith("# Alexandria implementation runbook\n"))
        self.assertEqual(runbook.count("## Step "), 5)
        self.assertIn("83fef6634a560860b930a532861dbfff8cbb3442", runbook)

    def test_scaffold_directories_and_licence_are_present(self):
        for relative in (
            "schemas",
            "examples",
            "docs",
            "scripts/alexandria_lib",
            "skills/alexandria/agents",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((PLUGIN_ROOT / relative).is_dir())
        licence = (PLUGIN_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", licence)
        self.assertIn("Copyright 2026 Wildcat Labs", licence)

    def test_all_plugin_json_files_parse(self):
        paths = list(PLUGIN_ROOT.rglob("*.json"))
        self.assertGreaterEqual(len(paths), 5)
        for path in paths:
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))

    def test_tabularium_schema_defines_mapping_coverage_and_counts(self):
        schema = json.loads(
            (PLUGIN_ROOT / "schemas" / "tabularium-view-v1.schema.json").read_text()
        )
        self.assertEqual(
            schema["properties"]["mappings"]["items"],
            {"$ref": "#/$defs/mapping"},
        )
        self.assertEqual(
            schema["properties"]["counts"],
            {"$ref": "#/$defs/counts"},
        )
        self.assertFalse(schema["$defs"]["mapping"]["additionalProperties"])
        self.assertFalse(schema["$defs"]["counts"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
