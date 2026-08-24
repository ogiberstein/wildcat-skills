"""Keep issue 429's checked-in release evidence reproducible."""

from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_SUITE_JOBS = (
    (".github/workflows/janus.yml", "contracts"),
    (".github/workflows/lazarus.yml", "tests"),
    (".github/workflows/pandects.yml", "catalogue"),
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


if __name__ == "__main__":
    unittest.main()
