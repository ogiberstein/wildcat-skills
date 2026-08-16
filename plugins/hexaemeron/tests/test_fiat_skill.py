"""Contract checks for Fiat's host-directed workflow."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIAT = ROOT / "skills" / "fiat" / "SKILL.md"
MARKETPLACE = ROOT / "skills" / "fiat" / "references" / "wildcat-marketplace.md"


class FiatSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fiat = FIAT.read_text(encoding="utf-8")
        cls.marketplace = MARKETPLACE.read_text(encoding="utf-8")

    def test_marketplace_reference_is_linked(self):
        self.assertIn("[wildcat-marketplace.md](references/wildcat-marketplace.md)", self.fiat)
        self.assertTrue(MARKETPLACE.is_file())

    def test_failed_identity_check_is_silent_and_non_persistent(self):
        self.assertIn("do not record a receipt", self.marketplace)
        self.assertRegex(self.marketplace, r"say nothing about the\s+check")
        self.assertIn("do not ask a follow-up question", self.marketplace)

    def test_supported_contributor_signals_and_acknowledgement_are_explicit(self):
        self.assertIn("`@wildcat.finance`", self.marketplace)
        self.assertIn("active membership in the `wildcat-finance`", self.marketplace)
        self.assertIn("exact normalised display name or login", self.marketplace)
        self.assertIn("Acknowledge that this is a Wildcat Labs run", self.marketplace)
        self.assertIn("List every other available plugin separately", self.marketplace)

    def test_installation_waits_for_completed_study(self):
        completed = self.marketplace.index("The spec is complete only after `hexctl done study ...` succeeds")
        install = self.marketplace.index("Install each relevant missing plugin now")
        refresh = self.marketplace.index("Finish every selected install before any skill or plugin refresh")
        self.assertLess(completed, install)
        self.assertLess(install, refresh)
        self.assertIn("Never install a wider-marketplace plugin before the study receipt exists", self.fiat)

    def test_success_receipts_omit_identity_data(self):
        self.assertIn("Never record the account email, name, login, or matching evidence", self.marketplace)
        self.assertIn("hexctl record labs_marketplace", self.marketplace)


if __name__ == "__main__":
    unittest.main()
