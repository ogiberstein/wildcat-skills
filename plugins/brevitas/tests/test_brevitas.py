from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
SCRIPT = PLUGIN / "skills" / "brevitas" / "scripts" / "brevitas.py"
SPEC = importlib.util.spec_from_file_location("brevitas", SCRIPT)
assert SPEC and SPEC.loader
brevitas = importlib.util.module_from_spec(SPEC)
sys.modules["brevitas"] = brevitas
SPEC.loader.exec_module(brevitas)


VALID_FINDING = """[High] Claim.
Location: `src/Foo.sol:42`
Mechanism: Exact causal path.
Impact: Funds can be lost.
Fix: Reject the state.
"""


class BrevitasTests(unittest.TestCase):
    def codes(self, text: str, **kwargs) -> set[str]:
        return {issue.code for issue in brevitas.lint_text(text, **kwargs)}

    def test_valid_finding(self) -> None:
        self.assertEqual(self.codes(VALID_FINDING), set())

    def test_over_budget_finding(self) -> None:
        self.assertIn("B002", self.codes(VALID_FINDING + "Evidence: extra.\n"))

    def test_evidence_exception_allows_retention(self) -> None:
        text = (
            '<!-- brevitas: evidence-exception reason="six ordered reproduction steps" -->\n'
            + VALID_FINDING
            + "Reproduction: Step 1.\n"
        )
        self.assertNotIn("B002", self.codes(text))

    def test_evidence_exception_rejects_connective_prose(self) -> None:
        text = (
            '<!-- brevitas: evidence-exception reason="six ordered reproduction steps" -->\n'
            + VALID_FINDING
            + "This is a transition.\n"
        )
        self.assertIn("B009", self.codes(text))

    def test_evidence_exception_must_be_needed(self) -> None:
        text = '<!-- brevitas: evidence-exception reason="not needed" -->\n' + VALID_FINDING
        self.assertIn("B005", self.codes(text))

    def test_code_fence_limit(self) -> None:
        text = "```solidity\n" + "\n".join("x" for _ in range(16)) + "\n```\n"
        self.assertIn("B006", self.codes(text))

    def test_small_table(self) -> None:
        text = "| a | b | c |\n|---|---|---|\n| 1 | 2 | 3 |\n"
        self.assertIn("B011", self.codes(text))

    def test_two_sections(self) -> None:
        text = "# Title\n## One\nx\n## Two\ny\n"
        self.assertIn("B010", self.codes(text, mode="report"))

    def test_direct_answer_limit(self) -> None:
        text = "\n".join(f"line {index}" for index in range(7))
        self.assertIn("B001", self.codes(text, mode="answer"))

    def test_structural_openers_and_closers(self) -> None:
        text = "Here are the issues:\n- defect\nLet me know if you want more.\n"
        codes = self.codes(text)
        self.assertIn("B021", codes)
        self.assertIn("B026", codes)

    def test_missing_source_evidence(self) -> None:
        source = "At `src/Foo.sol:42`, 17 calls reach 0x1111111111111111111111111111111111111111."
        codes = self.codes("The path is unsafe.\n", source_text=source)
        self.assertIn("B030", codes)

    def test_host_descriptions_remain_identical(self) -> None:
        claude = json.loads(
            (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        codex = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(claude["description"], codex["description"])
        self.assertEqual(codex["description"], codex["interface"]["shortDescription"])
        self.assertGreaterEqual(len(codex["description"]), 25)
        self.assertLessEqual(len(codex["description"]), 64)

    def test_portable_entrypoint_routes_to_canonical_contract(self) -> None:
        portable = ROOT / ".agents" / "skills" / "brevitas" / "SKILL.md"
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", portable.read_text(encoding="utf-8"))
        self.assertEqual(len(links), 2)
        for link in links:
            self.assertTrue((portable.parent / link).resolve().is_file(), link)


if __name__ == "__main__":
    unittest.main()
