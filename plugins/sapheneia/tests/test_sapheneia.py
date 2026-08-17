from pathlib import Path
import json
import re
import unittest


PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
SKILL = PLUGIN / "skills" / "sapheneia" / "SKILL.md"


class SapheneiaContractTests(unittest.TestCase):
    def test_canonical_description_fits_shared_upload_limit(self):
        text = SKILL.read_text(encoding="utf-8")
        description = re.search(r"(?m)^description: (.+)$", text).group(1)
        self.assertLessEqual(len(description), 200)

    def test_ranked_contract_has_exactly_ten_rules(self):
        text = SKILL.read_text(encoding="utf-8")
        rules = [int(value) for value in re.findall(r"(?m)^### ([0-9]+)\. ", text)]
        self.assertEqual(rules, list(range(1, 11)))

    def test_contract_applies_to_agent_replies_and_persists(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Apply this skill to the agent itself.", text)
        self.assertIn("commentary, progress updates", text)
        self.assertIn("Keep it active for the rest of the session.", text)
        self.assertIn("The reader's stated preference outranks this default.", text)

    def test_host_descriptions_remain_identical(self):
        claude = json.loads(
            (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        codex = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(claude["description"], codex["description"])
        self.assertEqual(
            codex["description"], codex["interface"]["shortDescription"]
        )
        self.assertGreaterEqual(len(codex["description"]), 25)
        self.assertLessEqual(len(codex["description"]), 64)

    def test_portable_entrypoint_routes_to_canonical_contract(self):
        portable = ROOT / ".agents" / "skills" / "sapheneia" / "SKILL.md"
        text = portable.read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
        self.assertEqual(len(links), 2)
        for link in links:
            self.assertTrue((portable.parent / link).resolve().is_file(), link)


if __name__ == "__main__":
    unittest.main()
