"""The repository-owned unittest emitter produces bounded fresh reports."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "emit_unittest_report.py"

SPEC = importlib.util.spec_from_file_location("emit_unittest_report", SCRIPT)
emitter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(emitter)


FIXTURE = """\
import unittest


class Outcomes(unittest.TestCase):
    def test_assertion_failure(self):
        self.assertEqual(1, 2)

    def test_error(self):
        raise RuntimeError("broken fixture")

    @unittest.skip("fixture skip")
    def test_skip(self):
        pass

    def test_clean(self):
        self.assertEqual(1 + 1, 2)

    def test_interrupt(self):
        raise KeyboardInterrupt()
"""


class EmitUnittestReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="unittest-emitter-")
        self.root = Path(self.temporary.name) / "worktree"
        self.root.mkdir()
        (self.root / "test_outcomes.py").write_text(
            textwrap.dedent(FIXTURE), encoding="utf-8"
        )
        (self.root / "empty_module.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.report = self.root / ".elenchus" / "report.json"

    def tearDown(self):
        self.temporary.cleanup()

    def run_emitter(self, *selectors: str, report: Path | None = None):
        target = report or self.report
        run = subprocess.run(
            [sys.executable, str(SCRIPT), str(target), *selectors],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
        return run, payload

    def test_assertion_failure_is_counted(self):
        run, payload = self.run_emitter(
            "test_outcomes.Outcomes.test_assertion_failure"
        )
        self.assertEqual(1, run.returncode)
        self.assertEqual(1, payload["testsRun"])
        self.assertEqual(1, payload["failures"])
        self.assertEqual(0, payload["errors"])
        self.assertTrue(payload["complete"])

    def test_infrastructure_error_is_counted(self):
        run, payload = self.run_emitter("test_outcomes.Outcomes.test_error")
        self.assertEqual(1, run.returncode)
        self.assertEqual(1, payload["testsRun"])
        self.assertEqual(0, payload["failures"])
        self.assertEqual(1, payload["errors"])

    def test_skip_is_counted(self):
        run, payload = self.run_emitter("test_outcomes.Outcomes.test_skip")
        self.assertEqual(0, run.returncode)
        self.assertEqual(1, payload["testsRun"])
        self.assertEqual(1, payload["skipped"])

    def test_clean_selector_writes_the_exact_schema(self):
        run, payload = self.run_emitter("test_outcomes.Outcomes.test_clean")
        self.assertEqual(0, run.returncode)
        self.assertEqual(
            {
                "schema": "elenchus.unittest.v1",
                "complete": True,
                "testsRun": 1,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "expectedFailures": 0,
                "unexpectedSuccesses": 0,
            },
            payload,
        )

    def test_zero_test_selector_is_recorded(self):
        run, payload = self.run_emitter("empty_module")
        self.assertEqual(0, run.returncode)
        self.assertEqual(0, payload["testsRun"])
        self.assertTrue(payload["complete"])

    def test_interrupted_completion_is_incomplete(self):
        run, payload = self.run_emitter("test_outcomes.Outcomes.test_interrupt")
        self.assertEqual(130, run.returncode)
        self.assertEqual(1, payload["testsRun"])
        self.assertFalse(payload["complete"])

    def test_invalid_selector_is_an_error_report(self):
        run, payload = self.run_emitter("test_outcomes.Outcomes.test_absent")
        self.assertEqual(1, run.returncode)
        self.assertEqual(1, payload["testsRun"])
        self.assertEqual(1, payload["errors"])
        self.assertTrue(payload["complete"])

    def test_existing_output_is_replaced(self):
        self.report.parent.mkdir()
        self.report.write_text("stale report", encoding="utf-8")
        run, payload = self.run_emitter("test_outcomes.Outcomes.test_clean")
        self.assertEqual(0, run.returncode)
        self.assertEqual("elenchus.unittest.v1", payload["schema"])
        self.assertNotIn("stale report", self.report.read_text(encoding="utf-8"))

    def test_write_is_bounded_and_preserves_the_previous_file(self):
        self.report.parent.mkdir()
        self.report.write_text("previous\n", encoding="utf-8")
        with mock.patch.object(emitter, "MAX_REPORT_BYTES", 1), mock.patch(
            "pathlib.Path.cwd", return_value=self.root
        ):
            with self.assertRaises(emitter.ReportWriteError):
                emitter._write_report(str(self.report), {"large": "payload"})
        self.assertEqual("previous\n", self.report.read_text(encoding="utf-8"))

    def test_output_is_confined_to_the_current_worktree(self):
        outside = Path(self.temporary.name) / "outside.json"
        run, payload = self.run_emitter(
            "test_outcomes.Outcomes.test_clean", report=outside
        )
        self.assertEqual(2, run.returncode)
        self.assertIsNone(payload)
        self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
