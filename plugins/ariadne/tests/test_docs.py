"""The shipped documents, held against the code they describe.

A tool whose whole claim is that a document should not drift from what produced
it is a poor advertisement for itself if its own README does. These checks turn
the drift into a test failure rather than something a reader finds first.
"""

import os
import re
import unittest

from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import core_predicate, gates, registry  # noqa: E402
from ariadne_lib.predicates import solidity_release as release  # noqa: E402

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_VERSIONING = os.path.normpath(
    os.path.join(PLUGIN, "..", "hexaemeron", "skills", "VERSIONING.md")
)

SKILL = os.path.join(PLUGIN, "skills", "ariadne", "SKILL.md")
README = os.path.join(PLUGIN, "README.md")
CONTRACT = os.path.join(PLUGIN, "AGENTS.md")
CONFORMANCE = os.path.join(PLUGIN, "docs", "conformance.md")
PREDICATE_DOC = os.path.join(PLUGIN, "docs", "solidity-release.md")
EXAMPLES = os.path.join(PLUGIN, "examples")


def read(path):
    with open(path, "rb") as handle:
        return handle.read().decode("utf-8")


def subcommands():
    """Every subcommand the parser actually offers."""
    parser = ariadne.build_parser()
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        return sorted(action.choices)
    raise AssertionError("the parser offers no subcommands")


class SubcommandTests(unittest.TestCase):
    def test_every_subcommand_is_named_in_the_skill_and_the_readme(self):
        found = subcommands()
        self.assertTrue(found)
        for path in (SKILL, README):
            text = read(path)
            for name in found:
                self.assertIn(
                    "ariadne.py %s" % name,
                    text,
                    "%s does not show the %s subcommand" % (path, name),
                )

    def test_the_module_docstring_lists_the_same_subcommands(self):
        listed = re.findall(r"(?m)^    (\w[\w-]*)\s{2,}", ariadne.__doc__)
        self.assertEqual(sorted(listed), subcommands())


class GateTests(unittest.TestCase):
    def test_the_skill_table_carries_every_gate(self):
        text = read(SKILL)
        numbers = sorted(
            [number for number, _ in gates.CORE_GATES] + list(gates.PREDICATE_GATES)
        )
        for number in numbers:
            self.assertRegex(
                text,
                r"(?m)^\| %d [A-Z]" % number,
                "the gate table has no row for gate %d" % number,
            )

    def test_the_skill_names_the_core_and_predicate_split_correctly(self):
        text = read(SKILL)
        for number, _ in gates.CORE_GATES:
            row = re.search(r"(?m)^\| %d [^|]+\| (\w+) \|" % number, text)
            self.assertIsNotNone(row, number)
            self.assertEqual(row.group(1), "core", "gate %d" % number)
        for number in gates.PREDICATE_GATES:
            row = re.search(r"(?m)^\| %d [^|]+\| (\w+) \|" % number, text)
            self.assertIsNotNone(row, number)
            self.assertEqual(row.group(1), "predicate", "gate %d" % number)


class VocabularyTests(unittest.TestCase):
    def test_the_skill_names_every_disposition(self):
        text = read(SKILL)
        for disposition in core_predicate.DISPOSITIONS:
            self.assertIn("`%s`" % disposition, text)

    def test_the_skill_names_both_determinism_classes(self):
        text = read(SKILL)
        for entry in core_predicate.DETERMINISM:
            self.assertIn("`%s`" % entry, text)


class PredicateTests(unittest.TestCase):
    def test_the_registered_type_is_the_one_the_documents_quote(self):
        registered = [type_uri for type_uri, _ in registry.DEFAULT.entries()]
        self.assertEqual(registered, [release.TYPE])
        for path in (SKILL, PREDICATE_DOC):
            self.assertIn(release.TYPE, read(path))

    def test_the_predicate_document_names_every_field(self):
        text = read(PREDICATE_DOC)
        for field in release.PREDICATE_FIELDS:
            self.assertIn(
                "`%s`" % field, text, "the predicate document omits %s" % field
            )


class FixtureTests(unittest.TestCase):
    def test_the_conformance_document_names_every_fixture(self):
        text = read(CONFORMANCE)
        directory = os.path.join(PLUGIN, "tests", "fixtures", "conformance")
        for name in sorted(os.listdir(directory)):
            if name.endswith(".json"):
                self.assertIn(
                    name, text, "docs/conformance.md does not list %s" % name
                )

    def test_the_examples_document_names_every_example(self):
        text = read(os.path.join(EXAMPLES, "README.md"))
        for directory in (EXAMPLES, os.path.join(EXAMPLES, "tampered")):
            for name in sorted(os.listdir(directory)):
                if name.endswith(".json"):
                    self.assertIn(
                        name, text, "examples/README.md does not list %s" % name
                    )


class ContractTests(unittest.TestCase):
    def test_the_runtime_contract_points_at_the_skill_that_exists(self):
        for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", read(CONTRACT)):
            self.assertTrue(os.path.isfile(os.path.join(PLUGIN, relative)), relative)

    def test_no_shipped_document_links_outside_the_plugin(self):
        """The directory is published on its own, so a link that leaves it
        breaks wherever it lands."""
        for directory, _, names in os.walk(PLUGIN):
            if "__pycache__" in directory:
                continue
            for name in names:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(directory, name)
                for link in re.findall(r"\]\((\.[^)]+)\)", read(path)):
                    target = os.path.normpath(os.path.join(directory, link))
                    with self.subTest(document=os.path.relpath(path, PLUGIN)):
                        self.assertTrue(
                            os.path.commonpath([PLUGIN, target]) == PLUGIN
                            or target == SHARED_VERSIONING,
                            "%s links to %s, outside the plugin" % (path, link),
                        )
                        self.assertTrue(
                            os.path.exists(target), "%s links to a missing %s"
                            % (path, link),
                        )


if __name__ == "__main__":
    unittest.main()
