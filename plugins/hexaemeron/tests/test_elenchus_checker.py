"""Elenchus classifies guards from real runner-owned reports."""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "elenchus" / "scripts" / "elenchus.py"

spec = importlib.util.spec_from_file_location("elenchus_guard", SCRIPT)
elenchus = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = elenchus
spec.loader.exec_module(elenchus)

REPORT_FILE = ".elenchus/report"

UNITTEST_EMITTER = '''\
import json
import os
from pathlib import Path
import sys
import unittest

suite = unittest.defaultTestLoader.discover(".", pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=1).run(suite)
payload = {
    "schema": "elenchus.unittest.v1",
    "complete": True,
    "testsRun": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skipped": len(result.skipped),
    "expectedFailures": len(result.expectedFailures),
    "unexpectedSuccesses": len(result.unexpectedSuccesses),
}
target = Path(os.environ["ELENCHUS_REPORT_FILE"])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload), encoding="utf-8")
if "--exit-zero" not in sys.argv:
    raise SystemExit(not result.wasSuccessful())
'''

FORGE_EMITTER = '''\
import os
from pathlib import Path
import subprocess

run = subprocess.run(["forge", "test", "--junit"], capture_output=True, check=False)
target = Path(os.environ["ELENCHUS_REPORT_FILE"])
if run.stdout:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(run.stdout)
raise SystemExit(run.returncode)
'''

NODE_EMITTER = '''\
import { run } from "node:test";
import { writeFile } from "node:fs/promises";

console.error("ModuleNotFoundError AssertionError");
const counts = { executed: 0, assertionFailures: 0, errors: 0, skipped: 0 };
const stream = run({ files: ["test_adder.mjs"], isolation: "none" });
stream.on("test:pass", (data) => {
  if (data.skip || data.todo) counts.skipped += 1;
  else counts.executed += 1;
});
stream.on("test:fail", (data) => {
  counts.executed += 1;
  const wrapped = data.details?.error;
  const cause = wrapped?.cause ?? wrapped;
  if (cause?.code === "ERR_ASSERTION" || cause?.name === "AssertionError") {
    counts.assertionFailures += 1;
  } else {
    counts.errors += 1;
  }
});
const finished = new Promise((resolve, reject) => {
  stream.on("end", resolve);
  stream.on("error", reject);
});
stream.resume();
await finished;
await writeFile(process.env.ELENCHUS_REPORT_FILE, JSON.stringify({
  schema: "elenchus.node-test.v1",
  complete: true,
  ...counts,
}));
process.exitCode = counts.assertionFailures + counts.errors > 0 ? 1 : 0;
'''


class Fixture:
    """A real temporary git history with independent children of one base."""

    def __init__(self, base_files):
        self.path = Path(tempfile.mkdtemp(prefix="elenchus-fixture-"))
        self.run("init", "--quiet", "-b", "main")
        self.run("config", "user.email", "fixture@example.org")
        self.run("config", "user.name", "Fixture")
        self.base = self.commit("base", base_files)

    def run(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def commit(self, message, files):
        for name, body in files.items():
            target = self.path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        self.run("add", "-A")
        self.run("commit", "--quiet", "-m", message)
        return self.run("rev-parse", "HEAD").strip()

    def child(self, message, files):
        self.run("checkout", "--quiet", "--detach", self.base)
        return self.commit(message, files)

    def status(self):
        return self.run("status", "--short")

    def worktrees(self):
        return self.run("worktree", "list", "--porcelain")

    def destroy(self):
        shutil.rmtree(self.path, ignore_errors=True)


class RunnerCase(unittest.TestCase):
    fixture = None
    command = None
    report_format = None

    @classmethod
    def tearDownClass(cls):
        if cls.fixture is not None:
            cls.fixture.destroy()

    def outcome(self, ref, command=None, **kwargs):
        before = self.fixture.status()
        result = elenchus.check(
            self.fixture.path,
            ref,
            command or self.command,
            timeout=kwargs.pop("timeout", 120),
            report_format=kwargs.pop("report_format", self.report_format),
            report_file=kwargs.pop("report_file", REPORT_FILE),
            **kwargs,
        )
        self.assertEqual(before, self.fixture.status())
        return result


class UnittestReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.command = [sys.executable, "emit_unittest.py"]
        cls.report_format = "unittest-json-v1"
        cls.fixture = Fixture({
            "adder.py": "def add(a, b):\n    return a - b\n",
            "emit_unittest.py": UNITTEST_EMITTER,
        })
        f = cls.fixture
        cls.guarded = f.child("guarded", {
            "test_adder.py": (
                "import unittest\nfrom adder import add\n\n"
                "class T(unittest.TestCase):\n"
                "    def test_it_adds(self):\n"
                "        self.assertEqual(add(2, 2), 4, 'ModuleNotFoundError')\n"
            ),
        })
        cls.passed = f.child("passed", {
            "test_arithmetic.py": (
                "import unittest\n\nclass T(unittest.TestCase):\n"
                "    def test_arithmetic(self):\n        self.assertEqual(1 + 1, 2)\n"
            ),
        })
        cls.broken = f.child("broken", {
            "test_broken.py": "raise RuntimeError('AssertionError')\n",
        })
        cls.unguarded = f.child("unguarded", {"adder.py": "def add(a, b):\n    return a + b\n"})

    def test_runner_categories_distinguish_all_three_outcomes(self):
        self.assertEqual("guarded", self.outcome(self.guarded)["status"])
        self.assertEqual("passed", self.outcome(self.passed)["status"])
        self.assertEqual("inconclusive", self.outcome(self.broken)["status"])

    def test_diagnostic_poisoning_and_exit_code_do_not_change_the_report(self):
        ordinary = self.outcome(self.guarded)
        forced_zero = self.outcome(
            self.guarded, [sys.executable, "emit_unittest.py", "--exit-zero"]
        )
        self.assertEqual("guarded", ordinary["status"])
        self.assertEqual("guarded", forced_zero["status"])
        self.assertNotEqual(ordinary["exit_code"], forced_zero["exit_code"])
        self.assertIn("ModuleNotFoundError", ordinary["output"])
        self.assertIn("AssertionError", self.outcome(self.broken)["output"])

    def test_legacy_no_report_is_inconclusive(self):
        result = elenchus.check(
            self.fixture.path, self.guarded, self.command, timeout=120
        )
        self.assertEqual("inconclusive", result["status"])

    def test_legacy_cli_is_nonfatal_by_default_and_fails_when_required(self):
        argv = [
            "--repo", str(self.fixture.path), "--ref", self.guarded,
            "--test-command", f"{sys.executable} emit_unittest.py",
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, elenchus.main(argv))
            self.assertEqual(1, elenchus.main(argv + ["--require-guard"]))

    def test_unsafe_and_tracked_report_paths_fail_closed(self):
        traversal = self.outcome(self.guarded, report_file="../report")
        tracked = self.outcome(self.guarded, report_file="adder.py")
        self.assertEqual("inconclusive", traversal["status"])
        self.assertEqual("inconclusive", tracked["status"])

    def test_no_changed_test_is_still_unguarded(self):
        self.assertEqual("unguarded", self.outcome(self.unguarded)["status"])


class ForgeReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.runner_version = subprocess.run(
            ["forge", "--version"], capture_output=True, text=True, check=True
        ).stdout.splitlines()[0]
        cls.command = [sys.executable, "emit_forge.py"]
        cls.report_format = "forge-junit-v1"
        cls.fixture = Fixture({
            "foundry.toml": (
                "[profile.default]\nsrc = 'src'\ntest = 'test'\n"
                "solc_version = '0.8.28'\n"
            ),
            "src/Adder.sol": (
                "// SPDX-License-Identifier: UNLICENSED\npragma solidity 0.8.28;\n"
                "contract Adder { function add(uint a, uint b) external pure returns (uint) "
                "{ return a - b; } }\n"
            ),
            "emit_forge.py": FORGE_EMITTER,
        })
        f = cls.fixture
        cls.guarded = f.child("guarded", {
            "test/Adder.t.sol": (
                "// SPDX-License-Identifier: UNLICENSED\npragma solidity 0.8.28;\n"
                "import {Adder} from '../src/Adder.sol';\n"
                "contract AdderTest { function testModuleNotFoundError() public { "
                "assert(new Adder().add(2, 2) == 4); } }\n"
            ),
        })
        cls.passed = f.child("passed", {
            "test/Arithmetic.t.sol": (
                "// SPDX-License-Identifier: UNLICENSED\npragma solidity 0.8.28;\n"
                "contract ArithmeticTest { function testArithmetic() public pure { "
                "assert(uint(1) + 1 == 2); } }\n"
            ),
        })
        cls.broken = f.child("broken", {
            "test/Broken.t.sol": (
                "// SPDX-License-Identifier: UNLICENSED\npragma solidity 0.8.28;\n"
                "import {Missing} from '../src/AssertionError.sol';\n"
                "contract BrokenTest {}\n"
            ),
        })

    def test_native_junit_distinguishes_all_three_outcomes(self):
        self.assertEqual("guarded", self.outcome(self.guarded)["status"])
        self.assertEqual("passed", self.outcome(self.passed)["status"])
        self.assertEqual("inconclusive", self.outcome(self.broken)["status"])

    def test_fixture_exercised_the_declared_forge_version(self):
        self.assertIn("1.7.1", self.runner_version)


class NodeReports(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.runner_version = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        cls.command = ["node", "emit_node.mjs"]
        cls.report_format = "node-test-json-v1"
        cls.fixture = Fixture({
            "adder.mjs": "export const add = (a, b) => a - b;\n",
            "emit_node.mjs": NODE_EMITTER,
        })
        f = cls.fixture
        cls.guarded = f.child("guarded", {
            "test_adder.mjs": (
                "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
                "import { add } from './adder.mjs';\n"
                "test('ModuleNotFoundError', () => assert.equal(add(2, 2), 4));\n"
            ),
        })
        cls.passed = f.child("passed", {
            "test_adder.mjs": (
                "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
                "test('arithmetic', () => assert.equal(1 + 1, 2));\n"
            ),
        })
        cls.broken = f.child("broken", {
            "test_adder.mjs": (
                "import test from 'node:test';\n"
                "import './AssertionError.mjs';\n"
                "test('unreachable', () => {});\n"
            ),
        })

    def test_testsstream_distinguishes_all_three_outcomes(self):
        self.assertEqual("guarded", self.outcome(self.guarded)["status"])
        self.assertEqual("passed", self.outcome(self.passed)["status"])
        self.assertEqual("inconclusive", self.outcome(self.broken)["status"])

    def test_fixture_exercised_the_declared_node_version(self):
        self.assertEqual("v26.6.0", self.runner_version)


class ReportValidation(unittest.TestCase):
    def payload(self, **changes):
        value = {
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }
        value.update(changes)
        return json.dumps(value).encode()

    def test_malformed_incomplete_zero_and_contradictory_reports_fail_closed(self):
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(b"{")
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(self.payload(complete=False))
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(self.payload(testsRun=1, failures=2))
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_unittest_report(self.payload(testsRun=True))
        zero = elenchus.parse_unittest_report(self.payload(testsRun=0))
        self.assertEqual("inconclusive", elenchus.classify(zero)[0])

    def test_mixed_assertion_and_infrastructure_errors_are_inconclusive(self):
        report = elenchus.RunnerReport(True, 2, 1, 1, 0)
        self.assertEqual("inconclusive", elenchus.classify(report)[0])

    def test_oversized_and_stale_reports_are_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report"
            path.write_bytes(b"x" * (elenchus.MAX_REPORT_BYTES + 1))
            with self.assertRaises(elenchus.ReportError):
                elenchus.read_report(path, "unittest-json-v1", 0)
            path.write_bytes(self.payload())
            os.utime(path, (1, 1))
            with self.assertRaises(elenchus.ReportError):
                elenchus.read_report(path, "unittest-json-v1", time.time_ns())

    def test_xml_entities_and_contradictory_cases_are_rejected(self):
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_forge_report(
                b'<!DOCTYPE x [<!ENTITY y "z">]><testsuites />'
            )
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_forge_report(
                b'<testsuites><testcase><failure/><error/></testcase></testsuites>'
            )
        with self.assertRaises(elenchus.ReportError):
            elenchus.parse_forge_report(b'<testsuites tests="1">')

    def test_absolute_traversal_and_symlink_report_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            (tree / "real").mkdir()
            (tree / "link").symlink_to(tree / "real", target_is_directory=True)
            for path in ("/tmp/report", "../report", "link/report"):
                with self.subTest(path=path), self.assertRaises(elenchus.ReportError):
                    elenchus.prepare_report_path(tree, path)


class LaunchFailures(RunnerCase):
    @classmethod
    def setUpClass(cls):
        cls.report_format = "unittest-json-v1"
        cls.fixture = Fixture({"value.py": "VALUE = 1\n"})
        cls.changed = cls.fixture.child("test", {
            "test_value.py": "import unittest\nclass T(unittest.TestCase):\n    pass\n"
        })

    def test_missing_report_timeout_and_executable_failure_are_inconclusive_and_clean(self):
        before = self.fixture.worktrees()
        missing = self.outcome(self.changed, [sys.executable, "-c", "pass"])
        timeout = self.outcome(
            self.changed,
            [sys.executable, "-c", "import time; time.sleep(3)"],
            timeout=1,
        )
        absent = self.outcome(self.changed, ["elenchus-command-does-not-exist"])
        interrupted = self.outcome(
            self.changed,
            [sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"],
        )
        self.assertEqual(["inconclusive"] * 4, [
            missing["status"], timeout["status"], absent["status"], interrupted["status"],
        ])
        self.assertEqual(before, self.fixture.worktrees())


class Severity(unittest.TestCase):
    def test_unguarded_passes_by_default_and_fails_when_required(self):
        fixture = Fixture({"thing.py": "value = 1\n"})
        try:
            ref = fixture.child("second", {"thing.py": "value = 2\n"})
            argv = ["--repo", str(fixture.path), "--ref", ref,
                    "--test-command", "python3 -c pass"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, elenchus.main(argv))
                self.assertEqual(1, elenchus.main(argv + ["--require-guard"]))
        finally:
            fixture.destroy()


class TestFileDetection(unittest.TestCase):
    def test_it_recognises_the_conventions_this_marketplace_meets(self):
        for path in (
            "tests/test_index.py", "src/thing_test.py", "app/Button.test.ts",
            "app/Button.spec.ts", "test/Market.t.sol", "__tests__/route.ts",
        ):
            self.assertTrue(elenchus.is_test(path), path)

    def test_it_leaves_ordinary_source_alone(self):
        for path in ("src/adder.py", "scripts/hexctl.py", "app/Button.tsx", "src/Market.sol"):
            self.assertFalse(elenchus.is_test(path), path)


if __name__ == "__main__":
    unittest.main()
