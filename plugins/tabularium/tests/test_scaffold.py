"""Discovery, packaging and public-document checks for Tabularium."""

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
COMMAND = PLUGIN_ROOT / "scripts" / "tabularium.py"
SKILL = PLUGIN_ROOT / "skills" / "tabularium" / "SKILL.md"


def run(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TabulariumPackagingTests(unittest.TestCase):
    def test_help_names_both_commands(self):
        result = run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("build", result.stdout)
        self.assertIn("verify", result.stdout)
        self.assertIn("deterministic", result.stdout)

    def test_verify_help_requires_a_coverage_manifest(self):
        result = run("verify", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("coverage manifest", result.stdout)
        self.assertIn("offline", result.stdout)

    def test_skill_is_canonical_and_has_no_browsable_readme_shadow(self):
        self.assertTrue(SKILL.is_file())
        self.assertFalse((SKILL.parent / "README.md").exists())

    def test_package_metadata_agrees_and_points_at_the_skill(self):
        manifests = []
        for host in (".claude-plugin", ".codex-plugin"):
            path = PLUGIN_ROOT / host / "plugin.json"
            manifests.append(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual([item["name"] for item in manifests], ["tabularium"] * 2)
        self.assertEqual([item["version"] for item in manifests], ["0.2.0"] * 2)
        self.assertEqual([item["skills"] for item in manifests], ["./skills/"] * 2)
        self.assertEqual(manifests[0]["description"], manifests[1]["description"])
        self.assertEqual(
            [item["repository"] for item in manifests],
            ["https://github.com/wildcat-finance/skills"] * 2,
        )
        self.assertTrue(SKILL.is_file())

    def test_public_documents_and_audit_log_are_present(self):
        for relative in (
            "README.md",
            "docs/adding-an-adapter.md",
            "docs/compound-v3-preservation.md",
            "docs/release-policy.md",
            "audit/AUDIT.md",
            "examples/goldfinch-v0/README.md",
            "examples/goldfinch-v0/DATA-DICTIONARY.md",
        ):
            self.assertTrue((PLUGIN_ROOT / relative).is_file(), relative)

    def test_public_document_links_resolve_inside_the_plugin(self):
        for path in PLUGIN_ROOT.rglob("*.md"):
            if "__pycache__" in path.parts:
                continue
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if link.startswith(("#", "https://", "http://", "mailto:")):
                    continue
                target = (path.parent / link.split("#", 1)[0]).resolve()
                with self.subTest(document=path.relative_to(PLUGIN_ROOT), link=link):
                    self.assertIn(PLUGIN_ROOT, target.parents)
                    self.assertTrue(target.exists())

    def test_marketplace_entries_use_the_local_plugin_path(self):
        claude = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text()
        )
        codex = json.loads(
            (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text()
        )
        claude_entry = next(p for p in claude["plugins"] if p["name"] == "tabularium")
        codex_entry = next(p for p in codex["plugins"] if p["name"] == "tabularium")
        self.assertEqual(claude_entry["source"], "./plugins/tabularium")
        self.assertEqual(codex_entry["source"]["path"], "./plugins/tabularium")
        self.assertEqual(
            claude_entry["description"],
            json.loads(
                (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text()
            )["interface"]["shortDescription"],
        )

    def test_compound_spec_fails_closed_and_keeps_collection_offline(self):
        spec = " ".join(
            (PLUGIN_ROOT / "docs" / "compound-v3-preservation.md")
            .read_text()
            .split()
        )
        for phrase in (
            "Do not build from logs alone",
            "successful call frames whose destination is the Comet proxy",
            "Coverage fails closed",
            "It makes no RPC request",
            "not an independent confirmation source",
            "28 production market",
        ):
            self.assertIn(phrase, spec)


if __name__ == "__main__":
    unittest.main()
