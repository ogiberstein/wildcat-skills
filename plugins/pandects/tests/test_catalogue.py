"""The catalogue's shape, and the bounds on reading it."""

import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

from pandects_lib import catalogue as catalogue_module  # noqa: E402
from pandects_lib import safejson  # noqa: E402

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(PLUGIN_ROOT, "catalogue", "pandects.json")


def document(**overrides):
    raw = {
        "version": "0.1.0",
        "observables": "ICreditObservables",
        "families": {"conservation": "held against each other"},
        "laws": [],
    }
    raw.update(overrides)
    return raw


class ShapeTests(unittest.TestCase):
    def test_a_well_formed_catalogue_parses(self):
        found = catalogue_module.parse(document())
        self.assertEqual(found.version, "0.1.0")
        self.assertEqual(found.laws, [])

    def test_a_missing_top_level_field_is_refused(self):
        raw = document()
        del raw["families"]
        with self.assertRaises(catalogue_module.CatalogueError) as caught:
            catalogue_module.parse(raw)
        self.assertIn("families", str(caught.exception))

    def test_families_must_not_be_empty(self):
        with self.assertRaises(catalogue_module.CatalogueError):
            catalogue_module.parse(document(families={}))

    def test_laws_must_be_an_array(self):
        with self.assertRaises(catalogue_module.CatalogueError):
            catalogue_module.parse(document(laws={"a": 1}))

    def test_a_law_without_an_id_is_refused_at_parse_time(self):
        """Without an id there is nothing to name in any later message."""
        with self.assertRaises(catalogue_module.CatalogueError) as caught:
            catalogue_module.parse(document(laws=[{"statement": "something"}]))
        self.assertIn("no id", str(caught.exception))

    def test_two_laws_sharing_an_id_are_refused(self):
        with self.assertRaises(catalogue_module.CatalogueError) as caught:
            catalogue_module.parse(
                document(laws=[{"id": "a/b/v1"}, {"id": "a/b/v1"}])
            )
        self.assertIn("share the id", str(caught.exception))

    def test_a_field_a_law_does_not_define_is_refused(self):
        with self.assertRaises(catalogue_module.CatalogueError) as caught:
            catalogue_module.parse(
                document(laws=[{"id": "a/b/v1", "severity": "high"}])
            )
        self.assertIn("severity", str(caught.exception))

    def test_a_law_can_be_found_by_id(self):
        found = catalogue_module.parse(document(laws=[{"id": "a/b/v1"}]))
        self.assertIsNotNone(found.law("a/b/v1"))
        self.assertIsNone(found.law("nothing/here/v1"))


class BoundedReadingTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, body):
        path = os.path.join(self.root, "catalogue.json")
        with open(path, "w") as handle:
            handle.write(body)
        return path

    def test_a_document_that_is_not_json_is_refused(self):
        with self.assertRaises(catalogue_module.CatalogueError) as caught:
            catalogue_module.load(self.write("{not json"))
        self.assertIn("not valid JSON", str(caught.exception))

    def test_a_repeated_key_is_refused(self):
        path = self.write('{"version":"1","version":"2"}')
        with self.assertRaises(catalogue_module.CatalogueError) as caught:
            catalogue_module.load(path)
        self.assertIn("duplicate key", str(caught.exception))

    def test_nesting_past_the_cap_is_refused_before_parsing(self):
        path = self.write("[" * 200 + "]" * 200)
        with self.assertRaises(catalogue_module.CatalogueError) as caught:
            catalogue_module.load(path)
        self.assertIn("refused before parsing", str(caught.exception))

    def test_a_missing_file_is_refused(self):
        with self.assertRaises(catalogue_module.CatalogueError):
            catalogue_module.load(os.path.join(self.root, "absent.json"))

    def test_a_document_over_the_size_cap_is_refused(self):
        with self.assertRaises(safejson.InputError):
            safejson.loads(b'{"a":"' + b"x" * 500 + b'"}', max_bytes=64)

    def test_brackets_inside_strings_do_not_count_as_depth(self):
        self.assertIn("a", safejson.loads(json.dumps({"a": "[[[[[[" * 40}), max_depth=8))


class ShippedCatalogueTests(unittest.TestCase):
    def test_the_shipped_catalogue_parses(self):
        found = catalogue_module.load(SHIPPED)
        self.assertTrue(found.families)
        self.assertTrue(found.laws, "the shipped catalogue carries no laws")

    def test_every_shipped_law_is_findable_by_its_id(self):
        found = catalogue_module.load(SHIPPED)
        for law in found.laws:
            self.assertIsNotNone(found.law(law.id))

    def test_every_law_declares_a_family_the_catalogue_lists(self):
        found = catalogue_module.load(SHIPPED)
        for law in found.laws:
            self.assertIn(law.get("family"), found.families, law.id)


class AccrualAndClaimsTests(unittest.TestCase):
    """The step-3 families, as the shipped catalogue records them.

    Generic shape tests pass over an empty catalogue and over a wrong one. These
    are about the six entries themselves: that the one inexact law is the one
    that divides, that every law needing the queue extension says so, and that
    the two families are filed where the reader is told to look.
    """

    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)

    def family(self, name):
        found = [law for law in self.catalogue.laws if law.get("family") == name]
        self.assertTrue(found, "no law is filed under %r" % name)
        return found

    def test_exactly_one_law_in_the_corpus_carries_a_tolerance(self):
        """A second tolerance would need its own argument, not this one's."""
        inexact = [law for law in self.catalogue.laws if law.get("bounds") != "exact"]
        self.assertEqual([law.id for law in inexact], ["accrual/path-independent/v1"])

    def test_the_one_tolerance_names_the_arithmetic_that_produces_it(self):
        law = self.catalogue.law("accrual/path-independent/v1")
        bounds = law.get("bounds")
        self.assertIn("subdivision", bounds["tolerance"])
        self.assertIn("truncates", bounds["arithmetic"])

    def test_every_claims_law_declares_the_queue_it_reads(self):
        """The extension is optional, so a law that needs it must say so.

        A claims law whose applicability listed only core observables would be
        checkable against a target with no queue, which it is not: the read
        reverts.
        """
        for law in self.family("claims"):
            required = law.get("applicability")["requires"]
            self.assertTrue(
                any(name.startswith("withdrawalQueue.") for name in required),
                "%s reads the queue and does not say so" % law.id,
            )

    def test_no_law_outside_the_claims_family_needs_the_queue(self):
        for law in self.catalogue.laws:
            if law.get("family") == "claims":
                continue
            required = law.get("applicability")["requires"]
            for name in required:
                self.assertFalse(
                    name.startswith("withdrawalQueue."),
                    "%s is filed away from the claims family and reads the queue" % law.id,
                )

    def test_every_accrual_law_reads_debt(self):
        for law in self.family("accrual"):
            self.assertIn("totalDebt", law.get("applicability")["requires"], law.id)

    def test_every_law_over_a_pair_says_which_kind_of_pair_it_means(self):
        """One of these compares two systems; three compare one with its past.

        Reading them the wrong way round is the mistake available to a user of
        this corpus, so the assumption is not optional prose.
        """
        pairs = {
            "accrual/debt-falls-only-against-payment/v1": "its own past",
            "accrual/no-accrual-at-rest/v1": "its own past",
            "claims/recorded-claim-never-shrinks/v1": "its own past",
            "accrual/path-independent/v1": "two systems",
        }
        for law_id, expected in pairs.items():
            law = self.catalogue.law(law_id)
            self.assertIsNotNone(law, law_id)
            assumes = " ".join(law.get("applicability")["assumes"])
            self.assertIn(expected, assumes, law_id)


if __name__ == "__main__":
    unittest.main()
