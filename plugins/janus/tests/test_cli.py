"""The janus command surface imports and dispatches from the first step.

The subcommands fill in across the runbook; what this step proves is that the
module loads, the parser is built, and the two subcommands are registered so
later steps have somewhere to land their behaviour.
"""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JANUS = ROOT / "scripts" / "janus.py"


def load_janus():
    spec = importlib.util.spec_from_file_location("janus_cli", JANUS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CliSurfaceTests(unittest.TestCase):
    def test_module_is_where_this_test_expects_it(self):
        self.assertTrue(JANUS.is_file(), JANUS)

    def test_parser_registers_both_subcommands(self):
        janus = load_janus()
        parser = janus.build_parser()
        # argparse exposes registered subcommands through the subparsers action.
        choices = set()
        for action in parser._actions:
            if hasattr(action, "choices") and action.choices:
                choices.update(action.choices)
        self.assertIn("validate", choices)
        self.assertIn("report", choices)

    def test_no_command_prints_help_and_returns_two(self):
        janus = load_janus()
        self.assertEqual(janus.main([]), 2)


if __name__ == "__main__":
    unittest.main()
