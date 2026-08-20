"""Checks for the single host-neutral Promise Machine router."""

from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
ROUTER = ROOT / ".agents" / "skills" / "promise-machine" / "SKILL.md"


def canonical_skills(plugin):
    return sorted(plugin.glob("skills/**/SKILL.md"))


class PortableSkillTests(unittest.TestCase):
    def test_plugin_manifests_name_the_public_repository(self):
        repository = "https://github.com/wildcat-finance/skills"
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        for name in sorted(entry["name"] for entry in marketplace["plugins"]):
            plugin = PLUGINS / name
            for host in (".claude-plugin", ".codex-plugin"):
                manifest = json.loads(
                    (plugin / host / "plugin.json").read_text(encoding="utf-8")
                )
                with self.subTest(plugin=plugin.name, host=host):
                    self.assertEqual(manifest["repository"], repository)
                    self.assertEqual(
                        manifest["homepage"],
                        "%s/tree/main/plugins/%s" % (repository, plugin.name),
                    )

    def test_promise_machine_is_the_only_portable_entrypoint(self):
        entries = sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md"))
        self.assertEqual(entries, [ROUTER])
        text = ROUTER.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^name:\s*promise-machine$")
        self.assertRegex(text, r"(?m)^description:\s*\S")
        self.assertNotRegex(text, r"(?m)^\s*version:\s*")

    def test_router_reaches_each_plugin_runtime_contract_once(self):
        text = ROUTER.read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
        resolved = [(ROUTER.parent / link).resolve() for link in links]
        expected = {(ROOT / "AGENTS.md").resolve()}
        expected.update((plugin / "AGENTS.md").resolve() for plugin in PLUGINS.iterdir() if plugin.is_dir())
        self.assertEqual(set(resolved), expected)
        self.assertEqual(len(resolved), len(expected))
        for target in resolved:
            self.assertTrue(target.is_file(), target)
            self.assertTrue(target.is_relative_to(ROOT), target)

    def test_plugin_runtime_contracts_resolve_every_canonical_skill(self):
        for plugin in sorted(path for path in PLUGINS.iterdir() if path.is_dir()):
            contract = (plugin / "AGENTS.md").read_text(encoding="utf-8")
            linked = {
                (plugin / relative).resolve()
                for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract)
            }
            expected = {path.resolve() for path in canonical_skills(plugin)}
            with self.subTest(plugin=plugin.name):
                self.assertEqual(linked, expected)
                for target in linked:
                    self.assertTrue(target.is_file(), target)
                    self.assertTrue(target.is_relative_to(plugin), target)

    def test_canonical_skill_names_match_parent_directories_and_are_unique(self):
        names = {}
        for skill in sorted(PLUGINS.glob("*/skills/**/SKILL.md")):
            text = skill.read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*([^\n]+)$", text)
            with self.subTest(skill=skill.relative_to(ROOT)):
                self.assertIsNotNone(match)
                name = match.group(1).strip()
                self.assertEqual(name, skill.parent.name)
                self.assertNotIn(name, names, f"{name} also owned by {names.get(name)}")
                names[name] = skill.relative_to(ROOT)


if __name__ == "__main__":
    unittest.main()
