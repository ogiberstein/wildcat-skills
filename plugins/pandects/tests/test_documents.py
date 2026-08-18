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


class ShippedAdapterTests(unittest.TestCase):
    """Every law reaches the adapter an integrator actually inherits.

    `adapters/CorpusBase.sol` names its laws one by one, in Solidity, with no
    view of the catalogue. So a law added to the catalogue does not arrive there,
    and nothing about a green suite says it did not: the adapter compiles, every
    test passes, and an integrator runs one law fewer than the document they read
    promises. This is the check that has to exist for the same reason the
    integration-notes check does.
    """

    #: Every shipped file that names laws for somebody else to inherit. Round 4
    #: of this step gated the first and missed the second, which is the argument
    #: for a list rather than a path: `CorpusBase` holds the law objects and
    #: `CorpusInvariants` decides which of them a Foundry run actually asserts,
    #: so a law in the first and not the second is still a law nobody asks.
    BASE = os.path.join(PLUGIN_ROOT, "adapters", "CorpusBase.sol")

    #: The shipped files that decide which of the bound laws a run actually asks,
    #: one per engine an integrator might reach for. Rounds 4 and 5 of this step
    #: each gated one file and each missed the next, so this is a list of every
    #: such surface rather than the one that happened to be in hand.
    ASSERTING = (
        os.path.join(PLUGIN_ROOT, "adapters", "foundry", "CorpusInvariants.sol"),
        os.path.join(PLUGIN_ROOT, "adapters", "echidna", "CorpusEchidna.sol"),
        os.path.join(PLUGIN_ROOT, "adapters", "medusa", "CorpusMedusa.sol"),
    )

    #: The plugin's own campaign harness. Not something a third party extends, so
    #: it is not in `ASSERTING`, but it has the same shape and the same hazard:
    #: it binds its own law objects and declares one property per law under each
    #: engine's prefix, so a law added to the catalogue does not arrive in it and
    #: nothing about a green campaign says which laws were searched.
    CAMPAIGN = os.path.join(PLUGIN_ROOT, "src", "campaigns", "Specimens.sol")

    #: The prefixes the two engines read, which is why every property is declared
    #: twice. A harness carrying one of them searches under one engine and is
    #: silent under the other.
    PREFIXES = ("echidna_", "property_")

    ADAPTERS = (BASE,) + ASSERTING + (CAMPAIGN,)

    #: Compares two systems advanced over the same span by different routes, so
    #: an adapter holding one target cannot offer it and does not pretend to.
    #: `adapters/foundry/PathIndependenceProbe.sol` is where it lives instead.
    #: Pinned as an exact set rather than a skip list, so a second exclusion has
    #: to be argued for here rather than added quietly.
    NOT_IN_ADAPTER = {"accrual/path-independent/v1"}

    #: The campaign harness leaves it out for a different reason from the
    #: adapters', and the reason is worth keeping separate. An adapter cannot
    #: offer it because it holds one target; a campaign cannot search it because a
    #: campaign drives one system along one route. It is covered deterministically
    #: in `test/Pairs.t.sol` and reduced in `test/counterexamples/Accrual.t.sol`.
    NOT_IN_CAMPAIGN = {"accrual/path-independent/v1"}

    def setUp(self):
        with open(SHIPPED, encoding="utf-8") as handle:
            self.catalogue = catalogue_module.parse(json.load(handle))
        self.sources = {}
        for path in self.ADAPTERS:
            with open(path, encoding="utf-8") as handle:
                self.sources[path] = handle.read()

    def test_every_law_the_adapter_can_offer_is_in_it(self):
        """`CorpusBase` names the law objects an integrator inherits."""
        source = self.sources[self.BASE]
        for law in self.catalogue.laws:
            if law.id in self.NOT_IN_ADAPTER:
                continue
            component = os.path.basename(law["component"]).replace(".sol", "")
            with self.subTest(law=law.id):
                self.assertIn(
                    component,
                    source,
                    "%s is catalogued and the shipped adapter does not carry it"
                    % law.id,
                )

    def test_every_one_state_law_is_asserted_by_every_engine_adapter(self):
        """And each engine adapter decides which of them a run asks.

        Carrying a law object and never asserting it is the same silence as not
        carrying it, arriving one file later. So this maps the variable names
        `CorpusBase` binds its components to, then checks that every shipped
        adapter which asserts laws asserts the one-state ones.
        """
        bound = dict(
            re.findall(
                r"Law internal immutable (\w+) = new (\w+)\(\)",
                self.sources[self.BASE],
            )
        )
        for law in self.catalogue.laws:
            if law.id in self.NOT_IN_ADAPTER:
                continue
            component = os.path.basename(law["component"]).replace(".sol", "")
            variables = [name for name, made in bound.items() if made == component]
            with self.subTest(law=law.id):
                self.assertEqual(
                    len(variables),
                    1,
                    "%s is not bound exactly once in %s"
                    % (law.id, os.path.basename(self.BASE)),
                )
            if not self._is_one_state(component):
                continue
            for path in self.ASSERTING:
                asserted = set(
                    re.findall(r"judge\((\w+)\)", self.sources[path])
                ) | set(
                    re.findall(r"(\w+)\.check\(target\(\)\)", self.sources[path])
                )
                with self.subTest(law=law.id, adapter=os.path.basename(path)):
                    self.assertIn(
                        variables[0],
                        asserted,
                        "%s is carried by the adapter and asked by nothing in %s"
                        % (law.id, os.path.basename(path)),
                    )

    def test_the_explanation_is_as_wide_as_the_one_state_laws(self):
        """`explainOneState` returns one reason per one-state law.

        The width is a second copy of a number the catalogue already holds, so it
        needs checking from outside the file that states it. An adapter one entry
        short returns an integrator fewer reasons than the document promises, and
        the entry it drops is the one added last.
        """
        source = self.sources[self.BASE]
        signature = re.search(
            r"function explainOneState\(\)\s*public\s*view\s*"
            r"returns \(string\[(\d+)\] memory",
            source,
        )
        self.assertIsNotNone(signature, "explainOneState is not declared as expected")
        width = int(signature.group(1))

        one_state = [
            law
            for law in self.catalogue.laws
            if law.id not in self.NOT_IN_ADAPTER
            and self._is_one_state(os.path.basename(law["component"]).replace(".sol", ""))
        ]
        self.assertEqual(
            width,
            len(one_state),
            "explainOneState returns %d reasons for %d one-state laws"
            % (width, len(one_state)),
        )

        body = source[source.index("function explainOneState()") :]
        body = body[: body.index("\n    }")]
        bound = dict(
            re.findall(
                r"Law internal immutable (\w+) = new (\w+)\(\)", source
            )
        )
        explained = set(re.findall(r"details\[\d+\]\) = (\w+)\.check", body))
        for law in one_state:
            component = os.path.basename(law["component"]).replace(".sol", "")
            variable = next(n for n, made in bound.items() if made == component)
            with self.subTest(law=law.id):
                self.assertIn(
                    variable,
                    explained,
                    "%s is one-state and explainOneState gives no reason for it"
                    % law.id,
                )

    def test_every_one_state_law_is_a_campaign_property_under_both_prefixes(self):
        """The harness the engines actually drive, under both engines.

        A law bound here and given no property is a law no campaign searches, and
        a property declared under one prefix only is a law one engine searches and
        the other does not. Both read as a clean campaign.
        """
        source = self.sources[self.CAMPAIGN]
        bound = dict(
            re.findall(r"Law internal immutable (\w+) = new (\w+)\(\)", source)
        )
        bound.update(
            re.findall(r"PairLaw internal immutable (\w+) = new (\w+)\(\)", source)
        )
        for law in self.catalogue.laws:
            if law.id in self.NOT_IN_CAMPAIGN:
                continue
            component = os.path.basename(law["component"]).replace(".sol", "")
            variables = [name for name, made in bound.items() if made == component]
            with self.subTest(law=law.id):
                self.assertEqual(
                    len(variables),
                    1,
                    "%s is not bound exactly once in the campaign harness" % law.id,
                )
            for prefix in self.PREFIXES:
                # `judge` for a one-state law and `judgePair` for a pair law. Both,
                # because the harness declares both and a check reading one of them
                # would leave the other family exactly as unheld as this check was
                # written to stop.
                declared = re.findall(
                    r"function %s(\w+)\(\) external view returns \(bool\) \{\n"
                    r"\s*return judge(?:Pair)?\((\w+)\);" % prefix,
                    source,
                )
                asked = {variable for _, variable in declared}
                with self.subTest(law=law.id, prefix=prefix):
                    self.assertIn(
                        variables[0],
                        asked,
                        "%s has no %s property, so one engine never searches it"
                        % (law.id, prefix),
                    )

    def test_every_specimen_has_a_campaign_driving_it(self):
        """A specimen no engine drives is a law proven by hand only.

        The corpus's claim about a law rests on its specimen being caught. A
        specimen with a property to fail and no harness to fail it under is caught
        by the deterministic suite and by no search, and nothing about a green
        campaign run says which specimens were in it.
        """
        source = self.sources[self.CAMPAIGN]
        campaigns = set(re.findall(r"(?m)^contract (\w+)Campaign is Campaign", source))
        for law in self.catalogue.laws:
            specimen = os.path.basename(law["specimen"]).replace(".sol", "")
            with self.subTest(law=law.id, specimen=specimen):
                self.assertIn(
                    specimen,
                    campaigns,
                    "%s is the specimen for %s and no campaign drives it"
                    % (specimen, law.id),
                )

    def test_the_campaign_explanation_is_as_wide_as_the_laws_it_carries(self):
        """`explain` gives one reason per law the harness carries.

        The third place in this plugin where a law count is written twice, after
        the rendered catalogue and the adapter's `explainOneState`. A campaign that
        falsifies a property and then returns a reason short sends the reader back
        to the call trace, which is what `explain` exists to avoid.
        """
        source = self.sources[self.CAMPAIGN]
        signature = re.search(
            r"function explain\(\)\s*external\s*view\s*returns \(string\[(\d+)\] memory",
            source,
        )
        self.assertIsNotNone(signature, "explain is not declared as expected")
        width = int(signature.group(1))
        carried = [
            law for law in self.catalogue.laws if law.id not in self.NOT_IN_CAMPAIGN
        ]
        self.assertEqual(
            width,
            len(carried),
            "explain returns %d reasons for %d laws in the harness"
            % (width, len(carried)),
        )

        body = source[source.index("function explain()") :]
        body = body[: body.index("\n    }")]
        bound = dict(
            re.findall(r"Law internal immutable (\w+) = new (\w+)\(\)", source)
        )
        bound.update(
            re.findall(r"PairLaw internal immutable (\w+) = new (\w+)\(\)", source)
        )
        explained = set(re.findall(r"details\[\d+\]\) = (\w+)\.check", body))
        for law in carried:
            component = os.path.basename(law["component"]).replace(".sol", "")
            variable = next(n for n, made in bound.items() if made == component)
            with self.subTest(law=law.id):
                self.assertIn(
                    variable,
                    explained,
                    "%s is carried by the harness and explain gives no reason for it"
                    % law.id,
                )

    def test_the_harness_counts_the_campaigns_it_declares(self):
        """The header states two numbers and both are written by hand.

        "Nine of these eleven are expected to fail one property" is a count of
        campaigns and a count of the ones whose law the harness carries. Both move
        when a specimen is added, and this plugin has already shipped four wrong
        counts written twice, so neither is left to be noticed.

        A campaign fails a property when the law its specimen was built to break is
        one the harness asks. `SoundCampaign` breaks nothing by construction, and
        `CompoundsPerStepCampaign` breaks path independence, which no campaign can
        search.
        """
        source = self.sources[self.CAMPAIGN]
        words = [
            "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve",
        ]
        campaigns = re.findall(r"(?m)^contract (\w+)Campaign is Campaign", source)
        specimens = {
            os.path.basename(law["specimen"]).replace(".sol", ""): law.id
            for law in self.catalogue.laws
        }
        breaking = [
            name
            for name in campaigns
            if name in specimens and specimens[name] not in self.NOT_IN_CAMPAIGN
        ]
        header = source[: source.index("abstract contract Campaign")]
        self.assertIn(
            "%s of these %s are expected to fail one property"
            % (words[len(breaking)], words[len(campaigns)].lower()),
            header,
            "the file declares %d campaigns, %d of them breaking a law the harness "
            "asks, so the header should read '%s of these %s'"
            % (
                len(campaigns),
                len(breaking),
                words[len(breaking)],
                words[len(campaigns)].lower(),
            ),
        )

    def _is_one_state(self, component):
        """A one-state law extends `Law`; a pair law extends `PairLaw`.

        Read from the component rather than from a list here, so a law filed
        under a shape nobody wrote down still gets classified.
        """
        path = os.path.join(PLUGIN_ROOT, "src", "laws", "%s.sol" % component)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        return re.search(r"contract\s+%s\s+is\s+Law\b" % component, source) is not None


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
