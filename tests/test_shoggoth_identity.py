"""Checks the durable entry points for the Shoggoth identity contract."""

from pathlib import Path
import hashlib
import unittest


ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "SHOGGOTH.md"
CONTRACT = "shoggoth-collective/v1"
EXPECTED_SHA256 = "00d516fdd46f5cbfbed8a3f49b8299641a396531467319b5b042e8eb28c1f4fa"


class ShoggothIdentityTests(unittest.TestCase):
    def test_identity_contract_is_source_bound(self):
        text = IDENTITY.read_text(encoding="utf-8")
        self.assertIn(f"contract={CONTRACT}", text)
        self.assertIn("canonical=https://github.com/wildcat-finance/skills/blob/main/SHOGGOTH.md", text)
        self.assertIn("copies=byte-identical", text)
        self.assertEqual(
            hashlib.sha256(IDENTITY.read_bytes()).hexdigest(), EXPECTED_SHA256
        )

    def test_agent_and_human_entries_link_the_contract(self):
        for name in ("AGENTS.md", "README.md"):
            with self.subTest(name=name):
                self.assertIn("SHOGGOTH.md", (ROOT / name).read_text(encoding="utf-8"))

    def test_identity_does_not_claim_operating_authority(self):
        text = IDENTITY.read_text(encoding="utf-8")
        for boundary in (
            "does not activate a skill",
            "grant a permission",
            "override an instruction from a target repository",
        ):
            self.assertIn(boundary, text)

    def test_creator_reference_stays_role_bounded(self):
        text = IDENTITY.read_text(encoding="utf-8")
        self.assertIn("Use `the Creator` only when the role matters", text)
        self.assertIn("by\npersonal name", text)


if __name__ == "__main__":
    unittest.main()
