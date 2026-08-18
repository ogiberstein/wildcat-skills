"""The Elenchus guard check puts a fix's test to the parent tree.

Built against a fixture repository rather than a mock, because the thing under
test is git behaviour and a runner's exit code, and a mock of those proves
nothing.
"""

import contextlib
import importlib.util
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "elenchus" / "scripts" / "elenchus.py"

spec = importlib.util.spec_from_file_location("elenchus_guard", SCRIPT)
elenchus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(elenchus)

TEST_COMMAND = [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"]


class Fixture:
    """A repository with one commit per outcome the check reports."""

    def __init__(self):
        self.path = Path(tempfile.mkdtemp(prefix="elenchus-fixture-"))
        self.run("init", "--quiet", "-b", "main")
        self.run("config", "user.email", "fixture@example.org")
        self.run("config", "user.name", "Fixture")

    def run(self, *args):
        subprocess.run(["git", "-C", str(self.path), *args],
                       capture_output=True, text=True, check=True)

    def commit(self, message, files):
        for name, body in files.items():
            target = self.path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        self.run("add", "-A")
        self.run("commit", "--quiet", "-m", message)
        return subprocess.run(["git", "-C", str(self.path), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()

    def destroy(self):
        shutil.rmtree(self.path, ignore_errors=True)


class GuardCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Fixture()
        f = cls.fixture

        # A defect, shipped with no test.
        f.commit("add the adder", {"adder.py": "def add(a, b):\n    return a - b\n"})

        # A fix carrying a test that catches the defect.
        cls.guarded = f.commit("fix the sign, with a guard", {
            "adder.py": "def add(a, b):\n    return a + b\n",
            "test_adder.py": (
                "import unittest\nfrom adder import add\n\n"
                "class T(unittest.TestCase):\n"
                "    def test_it_adds(self):\n"
                "        self.assertEqual(add(2, 2), 4)\n"),
        })

        # A change with no test at all.
        cls.unguarded = f.commit("tidy the adder", {
            "adder.py": "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\n"})

        # A test that would have passed before the change too.
        cls.passes = f.commit("add a test that guards nothing", {
            "test_arithmetic.py": (
                "import unittest\n\n"
                "class T(unittest.TestCase):\n"
                "    def test_arithmetic_still_works(self):\n"
                "        self.assertEqual(1 + 1, 2)\n"),
        })

        # A test importing something the parent has not got.
        cls.inconclusive = f.commit("add a module and its test", {
            "subtractor.py": "def subtract(a, b):\n    return a - b\n",
            "test_subtractor.py": (
                "import unittest\nfrom subtractor import subtract\n\n"
                "class T(unittest.TestCase):\n"
                "    def test_it_subtracts(self):\n"
                "        self.assertEqual(subtract(4, 2), 2)\n"),
        })

    @classmethod
    def tearDownClass(cls):
        cls.fixture.destroy()

    def outcome(self, ref):
        return elenchus.check(self.fixture.path, ref, TEST_COMMAND, timeout=120)

    def test_a_real_guard_fails_on_the_parent(self):
        result = self.outcome(self.guarded)
        self.assertEqual("guarded", result["status"], result.get("output", ""))
        self.assertIn("test_adder.py", result["tests"])

    def test_a_commit_with_no_test_is_unguarded(self):
        result = self.outcome(self.unguarded)
        self.assertEqual("unguarded", result["status"])
        self.assertEqual([], result["tests"])

    def test_a_test_that_passes_on_the_parent_guards_nothing(self):
        self.assertEqual("passed", self.outcome(self.passes)["status"])

    def test_a_test_that_cannot_import_is_inconclusive(self):
        result = self.outcome(self.inconclusive)
        self.assertEqual("inconclusive", result["status"], result.get("output", ""))

    def test_the_working_tree_is_left_alone(self):
        before = subprocess.run(["git", "-C", str(self.fixture.path), "status", "--short"],
                                capture_output=True, text=True, check=True).stdout
        self.outcome(self.guarded)
        after = subprocess.run(["git", "-C", str(self.fixture.path), "status", "--short"],
                               capture_output=True, text=True, check=True).stdout
        self.assertEqual(before, after)


class Severity(unittest.TestCase):
    def test_unguarded_passes_by_default_and_fails_when_required(self):
        fixture = Fixture()
        try:
            fixture.commit("first", {"thing.py": "value = 1\n"})
            fixture.commit("second", {"thing.py": "value = 2\n"})
            argv = ["--repo", str(fixture.path), "--test-command", "python3 -c pass"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, elenchus.main(argv))
                self.assertEqual(1, elenchus.main(argv + ["--require-guard"]))
        finally:
            fixture.destroy()


class TestFileDetection(unittest.TestCase):
    def test_it_recognises_the_conventions_this_marketplace_meets(self):
        for path in ("tests/test_index.py", "src/thing_test.py", "app/Button.test.ts",
                     "app/Button.spec.ts", "test/Market.t.sol", "__tests__/route.ts"):
            self.assertTrue(elenchus.is_test(path), path)

    def test_it_leaves_ordinary_source_alone(self):
        for path in ("src/adder.py", "scripts/hexctl.py", "app/Button.tsx", "src/Market.sol"):
            self.assertFalse(elenchus.is_test(path), path)


if __name__ == "__main__":
    unittest.main()
