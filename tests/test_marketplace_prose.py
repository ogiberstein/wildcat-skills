"""Keep the public marketplace prose pointed at the shipped boundaries."""

from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS = (
    "alexandria",
    "ariadne",
    "hermes",
    "hexaemeron",
    "lemma",
    "lazarus",
    "pandects",
    "probitas",
    "tabularium",
)
MIRRORED_SKILLS = (
    "alexandria",
    "ariadne",
    "hermes",
    "lazarus",
    "pandects",
    "probitas",
    "tabularium",
)


def marketplace_entries():
    payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    return {entry["name"]: entry for entry in payload["plugins"]}


class MarketplaceProseTests(unittest.TestCase):
    def test_marketplace_names_exactly_the_shipped_plugins(self):
        self.assertEqual(set(marketplace_entries()), set(PLUGINS))

    def test_short_descriptions_agree_across_hosts(self):
        entries = marketplace_entries()
        for name in PLUGINS:
            expected = entries[name]["description"]
            plugin = ROOT / "plugins" / name
            for host in (".claude-plugin", ".codex-plugin"):
                manifest = json.loads(
                    (plugin / host / "plugin.json").read_text(encoding="utf-8")
                )
                with self.subTest(plugin=name, host=host):
                    self.assertEqual(manifest["description"], expected)
            codex = json.loads(
                (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(codex["interface"]["shortDescription"], expected)

            agent = plugin / "skills" / name / "agents" / "openai.yaml"
            if agent.is_file():
                match = re.search(
                    r'(?m)^  short_description: ["\']?([^"\'\n]+)',
                    agent.read_text(encoding="utf-8"),
                )
                self.assertIsNotNone(match, agent)
                self.assertEqual(match.group(1), expected)

    def test_root_readme_maps_every_plugin(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Choose the job, then the plugin", readme)
        for name in PLUGINS:
            with self.subTest(plugin=name):
                self.assertIn("[", readme)
                self.assertIn("./plugins/%s" % name, readme)

    def test_canonical_skills_state_handoff_and_frontier(self):
        for name in MIRRORED_SKILLS:
            skill = ROOT / "plugins" / name / "skills" / name / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            with self.subTest(plugin=name):
                self.assertIn("## Where this sits", text)
                self.assertIn("**Use another tool when.**", text)
                self.assertIn("**Current frontier.**", text)

    def test_required_skill_readmes_are_canonical_mirrors(self):
        for name in MIRRORED_SKILLS:
            directory = ROOT / "plugins" / name / "skills" / name
            with self.subTest(plugin=name):
                self.assertEqual(
                    (directory / "README.md").read_bytes(),
                    (directory / "SKILL.md").read_bytes(),
                )

    def test_lazarus_release_readme_remains_digest_bound(self):
        manifest = json.loads(
            (ROOT / "plugins" / "lazarus" / "examples" / "goldfinch-v0" / "manifest.json").read_text(encoding="utf-8")
        )
        files = {entry["path"]: entry["sha256"] for entry in manifest["components"]}
        readme = ROOT / "plugins" / "lazarus" / "examples" / "goldfinch-v0" / "README.md"
        import hashlib

        self.assertEqual(hashlib.sha256(readme.read_bytes()).hexdigest(), files["README.md"])


if __name__ == "__main__":
    unittest.main()
