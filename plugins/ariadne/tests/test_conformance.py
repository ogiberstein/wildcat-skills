"""The conformance fixtures, run as the test suite that keeps them honest.

The fixture directory is the artefact another implementation checks itself
against, and the suite reads the names of the files: `pass-*` verifies clean and
`fail-gate<n>-*` fails that gate and no other. A gate added without a fixture
fails the completeness test below rather than shipping unexercised.
"""

import json
import os
import re
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, gates, registry, verify  # noqa: E402

FIXTURES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "conformance"
)
BREACH = re.compile(r"^fail-gate(\d+)-")


def fixtures():
    return sorted(name for name in os.listdir(FIXTURES) if name.endswith(".json"))


def report_for(name):
    with open(os.path.join(FIXTURES, name), "rb") as handle:
        document = envelope.read(handle.read())
    return verify.report(document, registry.DEFAULT)


class FixtureTests(unittest.TestCase):
    def test_every_passing_fixture_verifies_clean(self):
        found = 0
        for name in fixtures():
            if not name.startswith("pass-"):
                continue
            with self.subTest(fixture=name):
                report = report_for(name)
                self.assertTrue(
                    report.ok,
                    "\n".join(g.line() for g in report.gates if not g.passed),
                )
            found += 1
        self.assertTrue(found)

    def test_every_breaching_fixture_fails_the_gate_it_is_named_for(self):
        found = 0
        for name in fixtures():
            match = BREACH.match(name)
            if not match:
                continue
            expected = int(match.group(1))
            with self.subTest(fixture=name):
                report = report_for(name)
                failed = [gate.number for gate in report.gates if not gate.passed]
                self.assertEqual(
                    failed,
                    [expected],
                    "%s should breach gate %d alone, breached %s"
                    % (name, expected, failed),
                )
                self.assertFalse(report.ok)
            found += 1
        self.assertTrue(found)

    def test_every_core_gate_has_a_breaching_fixture(self):
        """A gate with no fixture is a gate nobody else can test against."""
        covered = set()
        for name in fixtures():
            match = BREACH.match(name)
            if match:
                covered.add(int(match.group(1)))
        expected = {number for number, _ in gates.CORE_GATES}
        self.assertEqual(
            expected - covered,
            set(),
            "core gates with no breaching fixture: %s" % sorted(expected - covered),
        )

    def test_every_fixture_follows_the_naming_convention(self):
        for name in fixtures():
            with self.subTest(fixture=name):
                self.assertTrue(
                    name.startswith("pass-") or BREACH.match(name),
                    "%s is neither a pass- nor a fail-gate<n>- fixture" % name,
                )

    def test_the_envelope_fixture_reads_through_its_envelope(self):
        with open(
            os.path.join(FIXTURES, "pass-in-an-unsigned-envelope.json"), "rb"
        ) as handle:
            document = envelope.read(handle.read())
        self.assertIsNotNone(document.envelope)
        self.assertIn("unsigned", document.signature_state)

    def test_the_fixtures_are_formatted_as_committed_json(self):
        """They are read by other people's tools; keep them parseable and tidy."""
        for name in fixtures():
            path = os.path.join(FIXTURES, name)
            with open(path, "rb") as handle:
                raw = handle.read()
            with self.subTest(fixture=name):
                json.loads(raw.decode("utf-8"))
                self.assertTrue(raw.endswith(b"\n"), "%s has no trailing newline" % name)


if __name__ == "__main__":
    unittest.main()
