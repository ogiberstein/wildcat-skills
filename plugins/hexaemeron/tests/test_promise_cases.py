import json
from pathlib import Path
import unittest


CASES = Path(__file__).parent / "fixtures" / "promise-machine" / "executable-cases.json"


class PromiseExecutableCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(CASES.read_text(encoding="utf-8"))

    def assert_case(self, promise_id, code, disposition):
        case = self.cases[promise_id][code]
        self.assertEqual(case["disposition"], disposition)
        self.assertTrue(case["scenario"].strip())
        self.assertTrue(case["boundary"].strip())

    def test_ephoros_review_positive(self):
        self.assert_case("ephoros-observability-review", "P", "accept")

    def test_ephoros_review_missing(self):
        self.assert_case("ephoros-observability-review", "M", "refuse")

    def test_ephoros_review_subject_mismatch(self):
        self.assert_case("ephoros-observability-review", "S", "refuse")

    def test_ephoros_review_overclaim(self):
        self.assert_case("ephoros-observability-review", "O", "refuse")

    def test_ephoros_review_recovery(self):
        self.assert_case("ephoros-observability-review", "R", "recover")

    def test_phylax_review_positive(self):
        self.assert_case("phylax-boundary-review", "P", "accept")

    def test_phylax_review_missing(self):
        self.assert_case("phylax-boundary-review", "M", "refuse")

    def test_phylax_review_subject_mismatch(self):
        self.assert_case("phylax-boundary-review", "S", "refuse")

    def test_phylax_review_overclaim(self):
        self.assert_case("phylax-boundary-review", "O", "refuse")

    def test_phylax_review_recovery(self):
        self.assert_case("phylax-boundary-review", "R", "recover")

    def test_protasis_study_positive(self):
        self.assert_case("protasis-study-readiness", "P", "accept")

    def test_protasis_study_missing(self):
        self.assert_case("protasis-study-readiness", "M", "refuse")

    def test_protasis_study_subject_mismatch(self):
        self.assert_case("protasis-study-readiness", "S", "refuse")

    def test_protasis_study_overclaim(self):
        self.assert_case("protasis-study-readiness", "O", "refuse")

    def test_protasis_study_recovery(self):
        self.assert_case("protasis-study-readiness", "R", "recover")


if __name__ == "__main__":
    unittest.main()
