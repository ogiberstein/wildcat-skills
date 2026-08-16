"""The shipped examples, including the one that carries its gaps."""

import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, registry, verify  # noqa: E402

EXAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"
)
TAMPERED = os.path.join(EXAMPLES, "tampered")

BREACHES = {
    "escrow-v1.1.0-claim-repointed.json": 1,
    "escrow-v1.1.0-with-gaps-reason-removed.json": 3,
}


def report_for(path):
    with open(path, "rb") as handle:
        document = envelope.read(handle.read())
    return verify.report(document, registry.DEFAULT)


def examples():
    return sorted(
        name for name in os.listdir(EXAMPLES) if name.endswith(".json")
    )


class ExampleTests(unittest.TestCase):
    def test_both_examples_verify_with_nothing_unchecked(self):
        found = examples()
        self.assertEqual(len(found), 2, found)
        for name in found:
            with self.subTest(example=name):
                report = report_for(os.path.join(EXAMPLES, name))
                self.assertTrue(
                    report.ok,
                    "\n".join(g.line() for g in report.gates if not g.passed),
                )
                self.assertEqual(report.unchecked, [])

    def test_the_unhappy_example_carries_its_timed_out_campaign(self):
        with open(os.path.join(EXAMPLES, "escrow-v1.1.0-with-gaps.json"), "rb") as f:
            predicate = json.loads(f.read().decode("utf-8"))["predicate"]
        claims = {entry["name"]: entry for entry in predicate["claims"]}
        campaign = claims["fuzz campaign"]
        self.assertEqual(campaign["disposition"], "timed_out")
        self.assertIn("properties outstanding", campaign["reason"])

    def test_the_unhappy_example_says_its_audit_covered_another_revision(self):
        report = report_for(
            os.path.join(EXAMPLES, "escrow-v1.1.0-with-gaps.json")
        )
        audits = [gate for gate in report.gates if gate.name == "audits"][0]
        self.assertTrue(audits.passed)
        self.assertIn("other than the released commit", audits.detail)

    def test_the_clean_example_says_its_audit_covered_the_release(self):
        report = report_for(os.path.join(EXAMPLES, "escrow-v1.1.0.json"))
        audits = [gate for gate in report.gates if gate.name == "audits"][0]
        self.assertNotIn("other than the released commit", audits.detail)

    def test_every_example_records_its_deployment_as_unconfirmed(self):
        for name in examples():
            with open(os.path.join(EXAMPLES, name), "rb") as handle:
                predicate = json.loads(handle.read().decode("utf-8"))["predicate"]
            for deployment in predicate.get("deployments", []):
                self.assertFalse(deployment["confirmed_against_chain"], name)


class FreshnessTests(unittest.TestCase):
    """The examples quote digests from the committed fixture.

    Rebuild the fixture and forget the examples, and they would go on claiming
    bytecode that no longer exists. This catches that.
    """

    def test_the_examples_still_describe_the_committed_fixture(self):
        from ariadne_lib.capture import foundry

        fixtures = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures", "forge-project"
        )
        current = foundry.capture(
            os.path.join(fixtures, "v2"),
            repository="https://github.com/wildcat-finance/example-escrow",
            commit="9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a",
            previous=os.path.join(fixtures, "v1"),
            previous_name="v1.0.0",
        )
        expected = current["predicate"]["release_subjects"]
        for name in examples():
            with open(os.path.join(EXAMPLES, name), "rb") as handle:
                found = json.loads(handle.read().decode("utf-8"))
            with self.subTest(example=name):
                self.assertEqual(found["predicate"]["release_subjects"], expected)


class TamperTests(unittest.TestCase):
    def test_every_tampered_copy_fails_the_gate_it_is_meant_to(self):
        found = sorted(
            name for name in os.listdir(TAMPERED) if name.endswith(".json")
        )
        self.assertEqual(sorted(BREACHES), found)
        for name, expected in BREACHES.items():
            with self.subTest(tampered=name):
                report = report_for(os.path.join(TAMPERED, name))
                self.assertFalse(report.ok)
                broken = [gate.number for gate in report.gates if not gate.passed]
                self.assertEqual(broken, [expected])

    def test_each_tampered_copy_differs_from_its_example_in_one_place(self):
        """A tamper that changed several things would pass for the wrong reason."""
        for name in BREACHES:
            source = name.replace("-claim-repointed", "").replace(
                "-reason-removed", ""
            )
            with open(os.path.join(EXAMPLES, source), "rb") as handle:
                original = json.loads(handle.read().decode("utf-8"))
            with open(os.path.join(TAMPERED, name), "rb") as handle:
                changed = json.loads(handle.read().decode("utf-8"))
            with self.subTest(tampered=name):
                self.assertNotEqual(original, changed)
                self.assertEqual(original["subject"], changed["subject"])
                self.assertEqual(
                    original["predicate"]["build"], changed["predicate"]["build"]
                )


if __name__ == "__main__":
    unittest.main()
