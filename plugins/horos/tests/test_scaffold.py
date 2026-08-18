"""Scaffold contracts for the Horos plugin."""

from pathlib import Path
import json
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]


def marketplace_entry():
    payload = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    entries = [entry for entry in payload["plugins"] if entry["name"] == "horos"]
    if len(entries) != 1:
        raise AssertionError(f"expected one horos marketplace entry, found {len(entries)}")
    return entries[0]


class ScaffoldTests(unittest.TestCase):
    def test_host_manifests_agree_with_the_marketplace_entry(self):
        entry = marketplace_entry()
        for host in (".claude-plugin", ".codex-plugin"):
            manifest = json.loads(
                (PLUGIN / host / "plugin.json").read_text(encoding="utf-8")
            )
            with self.subTest(host=host):
                self.assertEqual(manifest["description"], entry["description"])
                self.assertEqual(manifest["version"], entry["version"])
                self.assertEqual(manifest["homepage"], entry["homepage"])

    def test_the_skill_links_its_ledger(self):
        text = (PLUGIN / "skills" / "horos" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("[EVOLUTION.md](EVOLUTION.md)", text)

    def test_the_docs_carry_the_study_and_runbook(self):
        for name in ("study.md", "runbook.md"):
            with self.subTest(document=name):
                self.assertTrue((PLUGIN / "docs" / name).is_file())

    def test_the_security_review_rule_is_present(self):
        rule = "No reading boundary applies during security review."
        text = (PLUGIN / "skills" / "horos" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(rule, text)


if __name__ == "__main__":
    unittest.main()
