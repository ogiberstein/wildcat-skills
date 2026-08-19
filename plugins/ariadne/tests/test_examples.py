"""The shipped examples, including the one that carries its gaps."""

import json
import os
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, registry, verify  # noqa: E402
import ariadne_lib.predicates  # noqa: F401,E402  (registers the shipped predicates)
"""Imported for the side effect, as `test_conformance.py` does.

Without it this module passes only when something else has already registered the
predicates, which under `unittest discover` happens to be true and on its own is
not: every example reported gates 2 and 5 unchecked and the assertions that they
were checked failed. It was passing for a reason other than the one it states.
"""

EXAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"
)
TAMPERED = os.path.join(EXAMPLES, "tampered")

BREACHES = {
    "escrow-v1.1.0-claim-repointed.json": 1,
    "escrow-v1.1.0-with-gaps-reason-removed.json": 3,
    "goldfinch-v0-fixture-state-root-removed.json": "evidence",
}
"""What each tampered copy is meant to breach: a gate number, or the name of a
check that carries no number.

The third is the rule the state-fixture predicate exists for. Its state root is
gone and its proof-backed count is not, so the statement counts records with
nothing to have proved them against."""


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
        self.assertEqual(len(found), 3, found)
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

    def test_the_solidity_examples_still_describe_the_committed_fixture(self):
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
        found = 0
        for name in examples():
            with open(os.path.join(EXAMPLES, name), "rb") as handle:
                document = json.loads(handle.read().decode("utf-8"))
            if "release_subjects" not in document["predicate"]:
                continue
            found += 1
            with self.subTest(example=name):
                self.assertEqual(
                    document["predicate"]["release_subjects"], expected
                )
        self.assertTrue(found)

    def test_the_state_fixture_example_still_describes_the_lazarus_fixture(self):
        """The same guard for the other kind. The example is a real capture over
        `plugins/lazarus/examples/goldfinch-v0`, so a change there without a
        recapture would leave it describing components that no longer exist."""
        from ariadne_lib.capture import state_fixture

        root = os.path.abspath(__file__)
        for _ in range(4):  # tests -> ariadne -> plugins -> the checkout
            root = os.path.dirname(root)
        goldfinch = os.path.join(
            root, "plugins", "lazarus", "examples", "goldfinch-v0"
        )
        if not os.path.isdir(goldfinch):
            self.skipTest("Lazarus is not beside this plugin in this checkout")
        with open(os.path.join(EXAMPLES, "goldfinch-v0-fixture.json"), "rb") as handle:
            shipped = json.loads(handle.read().decode("utf-8"))
        current = state_fixture.capture(
            goldfinch,
            name="goldfinch-v0",
            capture_tool="lazarus",
            capture_command=[
                "python3", "scripts/lazarus.py", "verify", "examples/goldfinch-v0",
            ],
            parameters={"fixture": "goldfinch-v0"},
            first_capture_reason=(
                "first preservation release of this fixture; there is no earlier "
                "capture of this block to compare against"
            ),
        )
        self.assertEqual(current, shipped)


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
                broken = [
                    gate.number if gate.number is not None else gate.name
                    for gate in report.gates
                    if not gate.passed
                ]
                self.assertEqual(broken, [expected])

    def test_each_tampered_copy_differs_from_its_example_in_one_place(self):
        """A tamper that changed several things would pass for the wrong reason."""
        for name in BREACHES:
            source = (
                name.replace("-claim-repointed", "")
                .replace("-reason-removed", "")
                .replace("-state-root-removed", "")
            )
            with open(os.path.join(EXAMPLES, source), "rb") as handle:
                original = json.loads(handle.read().decode("utf-8"))
            with open(os.path.join(TAMPERED, name), "rb") as handle:
                changed = json.loads(handle.read().decode("utf-8"))
            with self.subTest(tampered=name):
                self.assertNotEqual(original, changed)
                self.assertEqual(original["subject"], changed["subject"])
                # Whichever block this type carries as its build record stays
                # identical, so the tamper is the one thing the name says.
                for field in ("build", "capture"):
                    if field in original["predicate"]:
                        self.assertEqual(
                            original["predicate"][field],
                            changed["predicate"][field],
                        )


if __name__ == "__main__":
    unittest.main()
