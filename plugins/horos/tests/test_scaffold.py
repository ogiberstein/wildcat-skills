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


SCOPED_ENTRY = PLUGIN / "docs" / "scoped-entry"

MODULE_IDS = (
    "change-scaffold",
    "tracked-universe",
    "boundary-currency",
    "scoped-entry",
    "demonstration",
)


class ScopedEntrySpecTests(unittest.TestCase):
    """The committed spec for this run, held to its own shape."""

    def test_the_run_commits_its_study_and_runbook(self):
        for name in ("study.md", "runbook.md"):
            with self.subTest(document=name):
                self.assertTrue((SCOPED_ENTRY / name).is_file())

    def test_the_runbook_names_every_module_in_build_order(self):
        text = (SCOPED_ENTRY / "runbook.md").read_text(encoding="utf-8")
        seen = [
            module for module in MODULE_IDS
            if f"| {module} |" in text
        ]
        self.assertEqual(seen, list(MODULE_IDS))
        order = text.index("Build order:")
        self.assertEqual(
            [module for module in MODULE_IDS if module in text[order:order + 300]],
            list(MODULE_IDS),
        )

    def test_the_study_carries_fourteen_success_criteria(self):
        text = (SCOPED_ENTRY / "study.md").read_text(encoding="utf-8")
        section = text.split("## Success criteria", 1)[1].split("\n# ", 1)[0]
        numbered = [
            line for line in section.splitlines()
            if line[:1].isdigit() and line.split(".", 1)[0].isdigit()
        ]
        self.assertEqual(len(numbered), 14)

    def test_each_step_carries_the_six_required_fields(self):
        text = (SCOPED_ENTRY / "runbook.md").read_text(encoding="utf-8")
        steps = text.split("\n## Step ")[1:]
        self.assertEqual(len(steps), 5)
        for index, body in enumerate(steps, start=1):
            for field in ("**Goal.**", "**Entry.**", "**Exit.**", "**Files.**",
                          "**Tests.**", "**Disciplines.**"):
                with self.subTest(step=index, field=field):
                    self.assertIn(field, body)


if __name__ == "__main__":
    unittest.main()
