"""The Lazarus shell keeps every host and document on one contract."""

import re
import unittest

from . import support
from lazarus_lib import __version__


class ScaffoldTests(unittest.TestCase):
    def test_host_manifests_parse_and_agree(self):
        claude = support.load_json(".claude-plugin/plugin.json")
        codex = support.load_json(".codex-plugin/plugin.json")
        for manifest in (claude, codex):
            self.assertEqual(manifest["name"], "lazarus")
            self.assertEqual(manifest["version"], "0.1.0")
            self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(claude["description"], codex["description"])
        self.assertEqual(claude["license"], "MIT")

    def test_versions_agree_across_package_skill_and_manifests(self):
        versions = {
            __version__,
            support.skill_version(),
            support.load_json(".claude-plugin/plugin.json")["version"],
            support.load_json(".codex-plugin/plugin.json")["version"],
        }
        self.assertEqual(versions, {"0.1.0"})

    def test_skill_is_canonical_and_has_no_readme_shadow(self):
        self.assertTrue(support.SKILL.is_file())
        self.assertFalse((support.SKILL.parent / "README.md").exists())

    def test_portable_entrypoint_routes_to_the_runtime_contract(self):
        path = support.REPO_ROOT / ".agents" / "skills" / "lazarus" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
        self.assertIn("../../../plugins/lazarus/AGENTS.md", links)
        self.assertTrue(all((path.parent / link).resolve().is_file() for link in links))
        for alias in ("/lazarus:lazarus", "$lazarus"):
            self.assertIn(alias, text)

    def test_runtime_contract_documents_planned_entrypoints_and_boundaries(self):
        contract = (support.PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("skills/lazarus/SKILL.md", contract)
        self.assertIn("scripts/lazarus.py", contract)
        for command in ("capture", "verify", "replay"):
            self.assertIn(f"`{command}`", contract)
        self.assertIn("implements format validation", contract)
        self.assertIn("no provider, proxy or fallback", contract)

    def test_requirements_are_exact_direct_pins(self):
        requirements = (support.PLUGIN_ROOT / "requirements.txt").read_text().splitlines()
        pins = [line for line in requirements if line and not line.startswith("#")]
        self.assertEqual(len(pins), 4)
        self.assertEqual(
            {re.split(r"(?:\[.*\])?==", pin, maxsplit=1)[0] for pin in pins},
            {"eth-hash", "jsonschema", "rlp", "trie"},
        )
        for pin in pins:
            self.assertRegex(pin, r"^[a-z0-9-]+(?:\[[a-z0-9-]+\])?==\d+\.\d+\.\d+$")

    def test_transitive_runtime_environment_is_locked(self):
        direct = {
            re.split(r"(?:\[.*\])?==", line, maxsplit=1)[0]
            for line in (support.PLUGIN_ROOT / "requirements.txt").read_text().splitlines()
            if line and not line.startswith("#")
        }
        lines = (support.PLUGIN_ROOT / "requirements.lock").read_text().splitlines()
        locked = [line for line in lines if line and not line.startswith("#")]
        names = {re.split(r"(?:\[.*\])?==", line, maxsplit=1)[0] for line in locked}
        self.assertTrue(direct.issubset(names))
        self.assertTrue({"eth-utils", "pydantic-core", "rpds-py"}.issubset(names))
        self.assertEqual(len(names), len(locked))
        for pin in locked:
            self.assertRegex(pin, r"^[a-z0-9-]+(?:\[[a-z0-9-]+\])?==\d+\.\d+\.\d+$")

    def test_reviewed_design_documents_are_committed(self):
        study = (support.PLUGIN_ROOT / "docs" / "study.md").read_text(encoding="utf-8")
        runbook = (support.PLUGIN_ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
        self.assertTrue(study.startswith("# Lazarus study\n"))
        self.assertIn("## Selected format and verification details", study)
        self.assertTrue(runbook.startswith("# Lazarus implementation runbook\n"))
        self.assertIn("## Step 6: Ship and run the Goldfinch demonstration", runbook)

    def test_cli_and_step_five_modules_exist(self):
        self.assertTrue((support.PLUGIN_ROOT / "scripts" / "lazarus.py").is_file())
        package_files = {
            path.name
            for path in (support.PLUGIN_ROOT / "scripts" / "lazarus_lib").glob("*.py")
        }
        self.assertEqual(
            package_files,
            {
                "__init__.py",
                "canonical.py",
                "capture.py",
                "errors.py",
                "header.py",
                "hexvalue.py",
                "limits.py",
                "manifest.py",
                "paths.py",
                "proofs.py",
                "records.py",
                "replay.py",
                "rlp.py",
                "rpc.py",
                "schemas.py",
                "scrub.py",
                "server.py",
                "trieproof.py",
                "verifier.py",
                "version.py",
            },
        )


if __name__ == "__main__":
    unittest.main()
