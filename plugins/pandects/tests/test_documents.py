"""The documents, against what is actually on disk.

A rendered catalogue is a second copy of the truth, and a second copy drifts.
These are the checks that make it a rendering instead: a law added without
appearing in the document fails, a document naming a law that is not there
fails, and a specimen nobody filed fails.
"""

import json
import os
import re
import unittest

from . import support  # noqa: F401  (sets sys.path)

from pandects_lib import catalogue as catalogue_module  # noqa: E402
from pandects_lib import render as render_module  # noqa: E402

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(PLUGIN_ROOT, "catalogue", "pandects.json")
RENDERED = os.path.join(PLUGIN_ROOT, "docs", "catalogue.md")

LAW_HEADING = re.compile(r"^### `([^`]+)`$", re.MULTILINE)
BACKTICKED = re.compile(r"`([^`]+\.sol)`")

#: Contracts under `specimens/` that are not specimens. The sound reference is
#: what every specimen inherits from, so no catalogue entry claims it and none
#: should.
NOT_A_SPECIMEN = {"Sound.sol"}


class RenderedCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)
        with open(RENDERED) as handle:
            self.rendered = handle.read()
        self.headings = LAW_HEADING.findall(self.rendered)

    def test_the_document_names_every_law_in_the_catalogue(self):
        missing = [law.id for law in self.catalogue.laws if law.id not in self.headings]
        self.assertEqual(missing, [], "laws filed and not rendered")

    def test_the_document_names_no_law_the_catalogue_lacks(self):
        known = {law.id for law in self.catalogue.laws}
        extra = [found for found in self.headings if found not in known]
        self.assertEqual(extra, [], "laws rendered and not filed")

    def test_the_document_renders_each_law_once(self):
        self.assertEqual(len(self.headings), len(set(self.headings)))

    def test_every_rendered_statement_matches_the_catalogue(self):
        """A rendering that paraphrases is a second source.

        The statement is the law as a reader would state it, and a document
        carrying a friendlier version of it is a document somebody will quote.
        """
        for law in self.catalogue.laws:
            self.assertIn("> %s" % law.get("statement"), self.rendered, law.id)

    def test_every_rendered_path_exists(self):
        for relative in set(BACKTICKED.findall(self.rendered)):
            self.assertTrue(
                os.path.isfile(os.path.join(PLUGIN_ROOT, relative)),
                "%s is named in the document and not on disk" % relative,
            )


class RendererTests(unittest.TestCase):
    """The document is what the renderer produces, byte for byte.

    Without this, "rendering rather than a second source" is a claim about
    intent. The drift tests above catch a document that stopped agreeing with
    the catalogue and offer no way to fix it; somebody adding a law was told the
    document was wrong and left to work out what it should have said.
    """

    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)
        with open(RENDERED) as handle:
            self.committed = handle.read()

    def test_the_committed_document_is_what_the_renderer_writes(self):
        self.assertEqual(
            self.committed,
            render_module.render(self.catalogue),
            "docs/catalogue.md differs from the renderer; run "
            "`python3 scripts/pandects.py render`",
        )

    def test_the_rendering_is_stable(self):
        once = render_module.render(self.catalogue)
        self.assertEqual(once, render_module.render(self.catalogue))

    def test_the_preamble_counts_what_was_rendered(self):
        """Rather than a figure somebody typed once.

        The drift test above cannot catch a wrong count: it compares the
        document against this renderer, so a hardcoded number makes both wrong
        the same way. This is the check that has to come from outside.
        """
        body = render_module.render(self.catalogue)

        # Spelled out here rather than imported, because a test that borrowed the
        # renderer's own word list would agree with it however wrong it was.
        # Written once and reused for both counts, since the document states the
        # law count twice and an earlier fix corrected only one of them.
        words = [
            "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve",
        ]
        laws = len(self.catalogue.laws)
        families = {law.get("family") for law in self.catalogue.laws}
        plural = "law" if laws == 1 else "laws"
        self.assertIn(
            "%s %s in %s %s"
            % (
                words[laws],
                plural,
                words[len(families)].lower(),
                "family" if len(families) == 1 else "families",
            ),
            body,
        )
        self.assertIn(
            "The corpus holds %s %s;" % (words[laws].lower(), plural), body
        )

        raw = json.loads(json.dumps(self.catalogue.raw))
        raw["laws"] = raw["laws"][:1]
        smaller = render_module.render(catalogue_module.parse(raw))
        self.assertIn("One law in one family", smaller)
        self.assertIn("The corpus holds one law;", smaller)

    def test_a_law_in_an_unfamiliar_family_is_still_rendered(self):
        """A renderer must not drop what it was not told about.

        Looping over its own vocabulary rather than the catalogue would make a
        law filed under a new family vanish from the document, and the drift
        test would not see it, because the document is what this produces.
        """
        raw = json.loads(json.dumps(self.catalogue.raw))
        raw["families"]["novel"] = "a family the renderer has no blurb for"
        raw["laws"][0]["family"] = "novel"
        body = render_module.render(catalogue_module.parse(raw))
        self.assertIn("## Novel", body)
        self.assertIn(raw["laws"][0]["id"], body)

    def test_a_family_with_no_laws_is_skipped_rather_than_printed_empty(self):
        raw = dict(self.catalogue.raw)
        raw["families"] = dict(raw["families"])
        raw["families"]["nothing-here"] = "a family nobody has filed under"
        body = render_module.render(catalogue_module.parse(raw))
        self.assertNotIn("Nothing-here", body)


class IntegrationNotesTests(unittest.TestCase):
    """Every law is spoken about where the corpus meets a real design.

    A law added to the catalogue and left out of the integration's notes is a
    law nobody has asked the applicability question about, which is the question
    that integration exists to answer.
    """

    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)
        path = os.path.join(
            PLUGIN_ROOT, "integrations", "wildcat", "APPLICABILITY.md"
        )
        with open(path) as handle:
            self.notes = handle.read()

    def test_every_law_appears_in_the_wildcat_notes(self):
        for law in self.catalogue.laws:
            self.assertIn(law.id, self.notes, "%s is unmentioned" % law.id)


class SpecimenTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)

    def test_every_specimen_on_disk_is_claimed_by_a_law(self):
        """The reverse of a missing specimen, and the easier mistake.

        A broken contract nobody filed is a broken contract with no law saying
        what it is for, sitting in a directory a reader is invited to copy from.
        """
        claimed = {
            os.path.basename(law.get("specimen") or "") for law in self.catalogue.laws
        }
        directory = os.path.join(PLUGIN_ROOT, "specimens")
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".sol") or name in NOT_A_SPECIMEN:
                continue
            self.assertIn(name, claimed, "%s is on disk and in no catalogue entry" % name)

    def test_every_claimed_specimen_says_it_is_broken(self):
        for law in self.catalogue.laws:
            path = os.path.join(PLUGIN_ROOT, law.get("specimen"))
            with open(path) as handle:
                self.assertIn("deliberately broken", handle.read().lower(), law.id)


class GuideTests(unittest.TestCase):
    """The documents a reader is sent to actually exist."""

    def test_the_guides_are_present_and_not_empty(self):
        for name in ("writing-a-law.md", "applicability.md", "catalogue.md"):
            path = os.path.join(PLUGIN_ROOT, "docs", name)
            self.assertTrue(os.path.isfile(path), name)
            with open(path) as handle:
                self.assertGreater(len(handle.read()), 500, name)


if __name__ == "__main__":
    unittest.main()
