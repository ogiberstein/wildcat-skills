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
import ariadne_lib.predicates  # noqa: F401,E402  (registers the shipped predicates)

FIXTURES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "conformance"
)
BREACH = re.compile(r"^fail-gate(\d+)-")
CHECK_BREACH = "fail-check-"
"""A check with no gate number gets a fixture too.

Gates 2 and 5 are numbered and belong to a predicate. The other checks a
predicate adds -- coverage, inputs, audits, deployments, the field-shape check --
carry no number, so they cannot use the `fail-gate<n>-` name. Without a fixture
they ship unexercised, which is the gap this convention closes.

The check name is recovered by longest match against the names the registered
predicates actually return, because a name like `predicate-fields` contains the
separator.
"""


def statement_of(name):
    with open(os.path.join(FIXTURES, name), "rb") as handle:
        return envelope.read(handle.read()).statement


def passing_by_type():
    """One passing fixture per predicate type, for asking a module what it checks."""
    found = {}
    for name in fixtures():
        if not name.startswith("pass-"):
            continue
        found.setdefault(statement_of(name).predicate_type, name)
    return found


def checks_of(type_uri, fixture):
    """Every gate a predicate module returns, as (number, name) pairs."""
    module = registry.DEFAULT.get(type_uri)
    if module is None or not callable(getattr(module, "check", None)):
        return []
    return [(g.number, g.name) for g in module.check(statement_of(fixture))]


def named_checks():
    """The unnumbered check names every registered predicate exposes."""
    names = set()
    for type_uri, fixture in passing_by_type().items():
        for number, name in checks_of(type_uri, fixture):
            if number is None:
                names.add(name)
    return names


def check_name_of(fixture):
    """The check a `fail-check-` fixture is named for, or None."""
    if not fixture.startswith(CHECK_BREACH):
        return None
    rest = fixture[len(CHECK_BREACH):]
    matches = [name for name in named_checks() if rest.startswith(name + "-")]
    return max(matches, key=len) if matches else None


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
                    name.startswith("pass-")
                    or BREACH.match(name)
                    or check_name_of(name) is not None,
                    "%s is not a pass-, fail-gate<n>- or fail-check-<name>- fixture"
                    % name,
                )

    def test_every_check_breaching_fixture_fails_the_check_it_is_named_for(self):
        found = 0
        for name in fixtures():
            expected = check_name_of(name)
            if expected is None:
                continue
            with self.subTest(fixture=name):
                report = report_for(name)
                failed = [gate.name for gate in report.gates if not gate.passed]
                self.assertEqual(
                    failed,
                    [expected],
                    "%s should breach %s alone, breached %s"
                    % (name, expected, failed),
                )
                self.assertFalse(report.ok)
            found += 1
        self.assertTrue(found)

    def test_every_registered_predicate_has_a_passing_fixture(self):
        registered = {type_uri for type_uri, _ in registry.DEFAULT.entries()}
        self.assertEqual(registered - set(passing_by_type()), set())

    def test_every_predicate_gate_has_a_breaching_fixture_of_its_own_type(self):
        """Gates 2 and 5 mean different things per predicate, so one type's
        fixture does not exercise another's."""
        for type_uri, fixture in passing_by_type().items():
            owned = {n for n, _ in checks_of(type_uri, fixture) if n is not None}
            if not owned:
                continue
            covered = set()
            for name in fixtures():
                match = BREACH.match(name)
                if match and statement_of(name).predicate_type == type_uri:
                    covered.add(int(match.group(1)))
            with self.subTest(predicate=type_uri):
                self.assertEqual(
                    owned - covered,
                    set(),
                    "%s gates with no breaching fixture of that type: %s"
                    % (type_uri, sorted(owned - covered)),
                )

    def test_every_named_check_has_a_breaching_fixture(self):
        """An unnumbered check with no fixture is one nobody else can test
        against, which is how `audits` and `deployments` shipped unexercised."""
        covered = {check_name_of(name) for name in fixtures()}
        covered.discard(None)
        self.assertEqual(
            named_checks() - covered,
            set(),
            "named checks with no breaching fixture: %s"
            % sorted(named_checks() - covered),
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
