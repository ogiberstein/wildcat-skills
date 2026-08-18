"""The Phylax boundary lint catches its four rules and nothing else.

Every rule carries a specimen it must flag and a neighbour it must not. The
neighbours are the point: this marketplace has a test helper named `run` and
an RPC client with a `.call`, and a lint that flags those is a lint people
learn to bypass.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "phylax" / "scripts" / "phylax.py"

spec = importlib.util.spec_from_file_location("phylax_lint", SCRIPT)
phylax = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phylax)


def codes(source, name="sample.py"):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        path.write_text(source, encoding="utf-8")
        return sorted(finding.code for finding in phylax.check(path))


class ShellInvocation(unittest.TestCase):
    def test_it_flags_a_shell_invocation(self):
        self.assertIn("P001", codes(
            "import subprocess\nsubprocess.run(['ls'], shell=True)\n"))

    def test_it_allows_an_argument_list(self):
        self.assertEqual([], codes("import subprocess\nsubprocess.run(['ls', '-l'])\n"))


class StringCommands(unittest.TestCase):
    def test_it_flags_a_string_command(self):
        self.assertIn("P002", codes("import subprocess\nsubprocess.run('git status')\n"))

    def test_it_flags_a_command_built_by_formatting(self):
        self.assertIn("P002", codes(
            "import subprocess\nref = 'main'\nsubprocess.run(f'git checkout {ref}')\n"))

    def test_it_flags_a_direct_import(self):
        self.assertIn("P002", codes("from subprocess import run\nrun('git status')\n"))

    def test_it_allows_list_concatenation(self):
        self.assertEqual([], codes(
            "import subprocess\nbase = ['git']\nsubprocess.run(base + ['status'])\n"))

    def test_it_ignores_a_local_helper_named_run(self):
        self.assertEqual([], codes(
            "def run(name):\n    return name\n\nrun('venues')\n"))

    def test_it_ignores_an_unrelated_call_method(self):
        self.assertEqual([], codes(
            "class Client:\n    def call(self, method, params):\n        return method\n\n"
            "Client().call('eth_chainId', [])\n"))


class Requirements(unittest.TestCase):
    def test_it_flags_an_unpinned_requirement(self):
        self.assertIn("P003", codes("rlp>=4.0.0\n", name="requirements.txt"))

    def test_it_allows_an_exact_pin(self):
        self.assertEqual([], codes("rlp==4.1.0\n", name="requirements.txt"))

    def test_it_skips_comments_and_includes(self):
        self.assertEqual([], codes("# a note\n-r other.txt\n\n", name="requirements.txt"))


class Credentials(unittest.TestCase):
    def test_it_flags_a_credential_literal(self):
        self.assertIn("P004", codes('API_KEY = "sk-live-9f4b2c8e1a7d"\n'))

    def test_it_flags_a_credential_written_to_output(self):
        self.assertIn("P004", codes(
            "import logging\nprivate_key = load()\nlogging.info(private_key)\n"))

    def test_it_allows_a_credential_read_from_the_environment(self):
        self.assertEqual([], codes('import os\nAPI_KEY = os.environ["API_KEY"]\n'))

    def test_it_allows_a_placeholder(self):
        self.assertEqual([], codes('API_KEY = "<your key here>"\n'))

    def test_it_allows_an_unrelated_name(self):
        self.assertEqual([], codes('MARKET_NAME = "wildcat-usdc"\n'))


class Suppression(unittest.TestCase):
    def test_a_stated_reason_suppresses_the_finding(self):
        self.assertEqual([], codes(
            'SECRET = "9f4b2c8e"  # phylax: allow scrubbing fixture, not live\n'))

    def test_a_reason_on_the_line_above_also_suppresses(self):
        self.assertEqual([], codes(
            '# phylax: allow fixture material\nSECRET = "9f4b2c8e"\n'))

    def test_a_bare_pragma_without_a_reason_does_not_suppress(self):
        self.assertIn("P004", codes('SECRET = "9f4b2c8e"  # phylax: allow\n'))


class OverTheMarketplace(unittest.TestCase):
    def test_the_shipped_tree_is_clean(self):
        findings = []
        for path in phylax.walk([str(ROOT.parent)]):
            findings.extend(phylax.check(path))
        self.assertEqual([], [str(f) for f in findings])


if __name__ == "__main__":
    unittest.main()
