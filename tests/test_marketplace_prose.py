"""Keep the public marketplace prose pointed at the shipped boundaries."""

from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"


def discovered_plugins():
    """The universe is what ships, not what a list here remembers.

    A hand-maintained tuple lets a new plugin land with every one of these
    cases passing while none of them looked at it. Discovery makes the
    omission the failure it should be.
    """
    return tuple(
        sorted(
            path.parent.parent.name
            for path in (ROOT / "plugins").glob("*/.claude-plugin/plugin.json")
        )
    )


PLUGINS = discovered_plugins()
# The canonical skill takes the plugin's own name, with one recorded exception:
# Hexaemeron's entry point is Fiat, because the plugin ships a phase suite
# rather than a single agent.
CANONICAL_SKILL_NAMES = {"hexaemeron": "fiat"}
CANONICAL_SKILLS = {
    name: ROOT
    / "plugins"
    / name
    / "skills"
    / CANONICAL_SKILL_NAMES.get(name, name)
    / "SKILL.md"
    for name in PLUGINS
}


NEXT_JOB_PREFIX = "**Next Fiat job.** Use /hexaemeron:fiat to "
NEXT_JOB_SUFFIX = (
    "Before the run finishes, cold-read and reconcile all mutable first-party "
    "marketplace prose. Change a skill's Next Fiat job only when that exact "
    "frontier job completed; otherwise leave it unchanged."
)
MARKETPLACE_CONTEXT_START = "<!-- marketplace-context:start -->"
MARKETPLACE_CONTEXT_END = "<!-- marketplace-context:end -->"


def marketplace_entries():
    payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    return {entry["name"]: entry for entry in payload["plugins"]}


def plugin_landing_readmes():
    return {
        path.parent.name: path
        for path in (ROOT / "plugins").glob("*/README.md")
        if re.search(r"(?m)^## In one line$", path.read_text(encoding="utf-8"))
    }


def marketplace_frontiers(path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(
        re.escape(MARKETPLACE_CONTEXT_START)
        + r"(.*?)"
        + re.escape(MARKETPLACE_CONTEXT_END),
        text,
        flags=re.DOTALL,
    )
    frontiers = []
    for block in blocks:
        match = re.search(r"\*\*Current frontier(?:\.|:)\*\*\s*([^\n]+)", block)
        if match is None:
            raise AssertionError(f"marketplace context has no current frontier: {path}")
        frontiers.append(match.group(1).strip())
    return frontiers


class MarketplaceProseTests(unittest.TestCase):
    def test_wildcat_labs_identity_contains_the_promise_machine_architecture(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith('<p align="center">\n'))
        self.assertLess(
            readme.index("./assets/characters/shoggoth.png"),
            readme.index("# The Shoggoth"),
        )
        self.assertIn("## What Is It?", readme)
        self.assertIn("## The Promise Machine", readme)
        self.assertIn("24 members: 15 domain agents and\n9 phase agents", readme)

        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertIn("Wildcat Labs Skills", marketplace["description"])
        self.assertIn("Promise Machine", marketplace["description"])

        for name in PLUGINS:
            runtime = ROOT / "plugins" / name / "AGENTS.md"
            with self.subTest(plugin=name):
                text = runtime.read_text(encoding="utf-8")
                self.assertIn("## Promise Machine binding", text)
                self.assertIn("promise-machine/v1", text)

    def test_marketplace_names_exactly_the_shipped_plugins(self):
        self.assertEqual(set(marketplace_entries()), set(PLUGINS))

    def test_short_descriptions_agree_across_hosts(self):
        entries = marketplace_entries()
        for name in PLUGINS:
            expected = entries[name]["description"]
            plugin = ROOT / "plugins" / name
            for host in (".claude-plugin", ".codex-plugin"):
                manifest = json.loads(
                    (plugin / host / "plugin.json").read_text(encoding="utf-8")
                )
                with self.subTest(plugin=name, host=host):
                    self.assertEqual(manifest["description"], expected)
            codex = json.loads(
                (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(codex["interface"]["shortDescription"], expected)

            agent = plugin / "skills" / name / "agents" / "openai.yaml"
            if agent.is_file():
                match = re.search(
                    r'(?m)^  short_description: ["\']?([^"\'\n]+)',
                    agent.read_text(encoding="utf-8"),
                )
                self.assertIsNotNone(match, agent)
                self.assertEqual(match.group(1), expected)

    def test_fiat_public_prose_names_the_state_container_gate(self):
        plugin = ROOT / "plugins" / "hexaemeron"
        skill = (plugin / "skills" / "fiat" / "SKILL.md").read_text(encoding="utf-8")
        readme = (plugin / "README.md").read_text(encoding="utf-8")
        agent = (plugin / "skills" / "fiat" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        codex = json.loads(
            (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertIn("validates the required version-1 container", skill)
        self.assertIn("checks the required\nversion-1 container spine", readme)
        self.assertIn("validating the controller state containers", agent)
        self.assertIn("validates its required state containers", codex["interface"]["longDescription"])

    def test_fiat_public_prose_binds_a_known_task_issue_during_init(self):
        plugin = ROOT / "plugins" / "hexaemeron"
        skill = (plugin / "skills" / "fiat" / "SKILL.md").read_text(encoding="utf-8")
        readme = (plugin / "README.md").read_text(encoding="utf-8")
        push = (plugin / "skills" / "fiat" / "references" / "push-discipline.md").read_text(
            encoding="utf-8"
        )
        codex = json.loads(
            (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertIn("init --task-issue <url>", " ".join(skill.split()))
        self.assertIn("--task-issue", readme)
        self.assertIn("fiat/<issue>-", push)
        self.assertIn("issue number in its run branch", codex["interface"]["longDescription"])

    def test_root_readme_maps_every_plugin(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Meet the Shoggoth", readme)
        self.assertNotIn("## Current status", readme)
        for name in PLUGINS:
            with self.subTest(plugin=name):
                self.assertIn("[", readme)
                self.assertIn("./plugins/%s" % name, readme)

    def test_root_readme_documents_how_to_publish(self):
        """Install was documented for three hosts and publishing for none.

        The two routes take different commands, and only one of them has a
        publishing step at all, so an operator who guessed wrong either ran an
        update that does nothing or waited for a sync that was never involved.
        """
        readme = s_readme = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        flat = " ".join(readme.split())
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("## Publish", root_readme)
        self.assertIn("## Publish", readme)
        # Both routes, named.
        self.assertIn("claude plugin marketplace update wildcat-labs", readme)
        self.assertIn("Organization settings > Plugins", readme)
        # The constraint that forces the second repository.
        self.assertIn("has to be private", flat)
        self.assertIn("wildcat-finance/skills-marketplace", readme)
        # Measured, not declared: the cron says five minutes and GitHub has
        # been delivering closer to twenty, so the section must not promise
        # an interval somebody would wait on.
        self.assertIn("observed rather than declared", flat)
        self.assertIn("gh workflow run sync-skills-marketplace.yml", s_readme)
        # Nothing is packaged by hand.
        self.assertIn("nothing to package or upload", flat)
        # The relative-source rule that keeps sync able to package.
        self.assertIn("stay relative paths", flat)

    def test_the_publish_section_sits_under_its_own_heading(self):
        readme = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        install = readme.index("## Install")
        publish = readme.index("## Publish")
        self.assertLess(install, publish)
        self.assertLess(readme.index("### Local agents"), publish)
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("## Install", root_readme)
        self.assertNotIn("## Publish", root_readme)

    def test_plugin_landing_readmes_publish_unique_rolling_fiat_jobs(self):
        landings = plugin_landing_readmes()
        self.assertEqual(set(landings), set(PLUGINS))
        self.assertEqual(len(landings), len(marketplace_entries()))

        topics = {}
        for name, path in landings.items():
            text = path.read_text(encoding="utf-8")
            lines = [line for line in text.splitlines() if line.startswith(NEXT_JOB_PREFIX)]
            with self.subTest(plugin=name):
                self.assertEqual(text.count(NEXT_JOB_PREFIX), 1, path)
                self.assertEqual(len(lines), 1, path)
                self.assertTrue(lines[0].startswith(NEXT_JOB_PREFIX), path)
                self.assertTrue(lines[0].endswith(NEXT_JOB_SUFFIX), path)
                context = re.search(
                    re.escape(MARKETPLACE_CONTEXT_START)
                    + r"(.*?)"
                    + re.escape(MARKETPLACE_CONTEXT_END),
                    text,
                    flags=re.DOTALL,
                )
                self.assertIsNotNone(context, path)
                self.assertIn(lines[0], context.group(1), path)
                topic = lines[0][len(NEXT_JOB_PREFIX) : -len(NEXT_JOB_SUFFIX)].strip()
                self.assertTrue(topic, path)
                self.assertTrue(topic.endswith("."), path)
                topics[name] = topic

        self.assertEqual(len(set(topics.values())), len(PLUGINS))

    def test_rolling_fiat_jobs_exist_only_in_plugin_landing_readmes(self):
        allowed = set(plugin_landing_readmes().values())
        found = set()
        for path in ROOT.rglob("*.md"):
            relative = path.relative_to(ROOT)
            # `.claude` holds git worktrees of this same repository, so a
            # sweep that descends into it finds every landing README twice and
            # reports the copies as strays. Nothing shipped lives under a dot
            # directory here.
            if relative.parts[0] in {".git", ".hexaemeron", ".claude"}:
                continue
            if "**Next Fiat job.**" in path.read_text(encoding="utf-8"):
                found.add(path)
        self.assertEqual(found, allowed)

    def test_current_frontiers_agree_with_each_plugin_landing_readme(self):
        landings = plugin_landing_readmes()
        self.assertEqual(set(landings), set(PLUGINS))
        for name in PLUGINS:
            landing_frontiers = marketplace_frontiers(landings[name])
            with self.subTest(plugin=name, surface="landing"):
                self.assertEqual(len(landing_frontiers), 1)
            expected = landing_frontiers[0]

            surfaces = [path for path in (ROOT / "plugins" / name).rglob("*.md")
                        if ".claude" not in path.parts]
            portable = ROOT / ".agents" / "skills" / name / "SKILL.md"
            if portable.is_file():
                surfaces.append(portable)
            for path in surfaces:
                text = path.read_text(encoding="utf-8")
                if MARKETPLACE_CONTEXT_START not in text:
                    continue
                with self.subTest(plugin=name, surface=path.relative_to(ROOT)):
                    frontiers = marketplace_frontiers(path)
                    self.assertTrue(frontiers, path)
                    self.assertEqual(frontiers, [expected] * len(frontiers))

        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("**Current frontier.**", root_readme)

    def test_canonical_skills_state_where_they_sit_and_their_frontier(self):
        """The sibling-handoff paragraph is deliberately absent.

        Every canonical skill used to carry a `Use another tool when.` line
        naming siblings to reach for instead, and the landing READMEs carried
        the same sentence under `Try something else when.`. Both were removed:
        a reader who does not already know what Ariadne or Fizz are learns
        nothing from being sent to one by name, and the marketplace boundaries
        in `AGENTS.md` are where that routing belongs. This case asserts the
        absence so neither label returns a paragraph at a time.
        """
        self.assertTrue(PLUGINS)
        for name, skill in CANONICAL_SKILLS.items():
            self.assertTrue(skill.is_file(), skill)
            text = skill.read_text(encoding="utf-8")
            with self.subTest(plugin=name):
                self.assertIn("## Where this sits", text)
                self.assertIn("**Current frontier.**", text)
                self.assertNotIn("**Use another tool when.**", text)
                self.assertNotIn("**Try something else when.**", text)

    def test_no_shipped_document_carries_a_sibling_handoff_label(self):
        strays = []
        for path in ROOT.rglob("*.md"):
            relative = path.relative_to(ROOT)
            if relative.parts[0] in {".git", ".hexaemeron", ".claude"}:
                continue
            text = path.read_text(encoding="utf-8")
            for label in ("**Use another tool when.**", "**Try something else when.**"):
                if label in text:
                    strays.append(f"{relative}: {label}")
        self.assertEqual(strays, [])

    def test_canonical_skill_directories_have_no_browsing_readme_mirrors(self):
        skills = sorted((ROOT / "plugins").glob("*/skills/**/SKILL.md"))
        self.assertTrue(skills)
        for skill in skills:
            with self.subTest(skill=skill.relative_to(ROOT)):
                self.assertFalse(
                    (skill.parent / "README.md").exists(),
                    "canonical skills must not carry shadow README.md mirrors",
                )

    def test_pandects_prose_counts_the_laws_the_catalogue_holds(self):
        """Two documents state the corpus size in prose and neither derives it.

        The rendered catalogue derives both of its counts and the adapters are held
        to theirs by the plugin's own suite. These two are hand-written sentences in
        browsing prose, and a frontier run that adds a law has to remember them. The
        withdrawal-batch-fee run corrected five such counts and missed a sixth, which
        is the argument for anchoring them here.
        """
        words = [
            "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve",
        ]
        catalogue = json.loads(
            (ROOT / "plugins" / "pandects" / "catalogue" / "pandects.json").read_text(
                encoding="utf-8"
            )
        )
        laws = catalogue["laws"]
        total = words[len(laws)].lower()
        exact = words[len([law for law in laws if law["bounds"] == "exact"])]
        families = words[len({law["family"] for law in laws})].lower()

        landing = (ROOT / "plugins" / "pandects" / "README.md").read_text(encoding="utf-8")
        for claim in (
            "%s laws in %s families." % (words[len(laws)], families),
            "%s of the %s laws are exact." % (exact, total),
            "`laws` prints %s laws with their applicability." % total,
        ):
            with self.subTest(document="plugins/pandects/README.md", claim=claim):
                self.assertIn(claim, landing)

    def test_lazarus_release_readme_remains_digest_bound(self):
        manifest = json.loads(
            (ROOT / "plugins" / "lazarus" / "examples" / "goldfinch-v0" / "manifest.json").read_text(encoding="utf-8")
        )
        files = {entry["path"]: entry["sha256"] for entry in manifest["components"]}
        readme = ROOT / "plugins" / "lazarus" / "examples" / "goldfinch-v0" / "README.md"
        import hashlib

        self.assertEqual(hashlib.sha256(readme.read_bytes()).hexdigest(), files["README.md"])


if __name__ == "__main__":
    unittest.main()
