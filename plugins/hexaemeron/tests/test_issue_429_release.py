"""Keep issue 429's checked-in release evidence reproducible."""

from pathlib import Path
import re
import shlex
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_SUITE_JOBS = (
    (".github/workflows/janus.yml", "contracts"),
    (".github/workflows/lazarus.yml", "tests"),
    (".github/workflows/pandects.yml", "catalogue"),
)
ISSUE_429_RUNBOOK = (
    REPO_ROOT
    / "plugins"
    / "hexaemeron"
    / "docs"
    / "audit-record-schema-timestamp-synopsis"
    / "runbook.md"
)
ISSUE_429_ELENCHUS_COMMAND = (
    "npx --yes --package=node@26.6.0 -- python3.12 "
    "plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}"
)


def workflow_job(path, job):
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf"(?ms)^  {re.escape(job)}:\n.*?(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        text,
    )
    if match is None:
        raise ValueError(f"{path}: workflow job {job} is missing")
    return match.group(0)


class Issue429ReleaseTests(unittest.TestCase):
    def test_root_suite_jobs_need_no_repository_history(self):
        for relative, job in ROOT_SUITE_JOBS:
            with self.subTest(path=relative, job=job):
                body = workflow_job(REPO_ROOT / relative, job)
                self.assertIn(
                    "run: python3 -m unittest discover -s tests -v", body
                )
                self.assertNotIn("fetch-depth: 0", body)

    def test_runbook_exposes_the_elenchus_report_argument(self):
        runbook = ISSUE_429_RUNBOOK.read_text(encoding="utf-8")
        self.assertEqual(runbook.count("--elenchus-report {report}"), 4)
        self.assertEqual(runbook.count(ISSUE_429_ELENCHUS_COMMAND), 4)
        self.assertEqual(
            shlex.split(ISSUE_429_ELENCHUS_COMMAND).count("{report}"), 1
        )


if __name__ == "__main__":
    unittest.main()
