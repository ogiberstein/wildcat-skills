"""Contract checks for Fiat's host-directed workflow."""

from pathlib import Path
import importlib.util
import json
import subprocess
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FIAT = ROOT / "skills" / "fiat" / "SKILL.md"
MARKETPLACE = ROOT / "skills" / "fiat" / "references" / "wildcat-marketplace.md"
CONTRIBUTOR_CHECK = ROOT / "skills" / "fiat" / "scripts" / "check_wildcat_contributor.py"
PUSH_DISCIPLINE = ROOT / "skills" / "fiat" / "references" / "push-discipline.md"
PLUGIN_CURRENCY = ROOT / "skills" / "fiat" / "references" / "plugin-currency.md"


def load_contributor_check():
    spec = importlib.util.spec_from_file_location("check_wildcat_contributor", CONTRIBUTOR_CHECK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FiatSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fiat = FIAT.read_text(encoding="utf-8")
        cls.marketplace = MARKETPLACE.read_text(encoding="utf-8")
        cls.push_discipline = PUSH_DISCIPLINE.read_text(encoding="utf-8")

    def test_marketplace_reference_is_linked(self):
        self.assertIn("[wildcat-marketplace.md](references/wildcat-marketplace.md)", self.fiat)
        self.assertTrue(MARKETPLACE.is_file())

    def test_failed_identity_check_is_silent_and_non_persistent(self):
        self.assertIn("do not record a receipt", self.marketplace)
        self.assertRegex(self.marketplace, r"say nothing about the\s+check")
        self.assertIn("do not ask a follow-up question", self.marketplace)

    def test_supported_contributor_signals_and_acknowledgement_are_explicit(self):
        self.assertIn("`@wildcat.finance`", self.marketplace)
        self.assertIn("active membership in the `wildcat-finance`", self.marketplace)
        self.assertIn("exact normalised display name or login", self.marketplace)
        self.assertIn("Acknowledge that this is a Wildcat Labs run", self.marketplace)
        self.assertIn("List every other available plugin separately", self.marketplace)

    def test_authenticated_github_does_not_require_a_connector(self):
        self.assertIn("Do not require a connector", self.marketplace)
        self.assertIn("already-authenticated local GitHub account", self.marketplace)
        self.assertIn("under-permissioned\nconnector is not itself a failed check", self.marketplace)
        self.assertIn("a GitHub connector is optional", self.fiat)
        self.assertTrue(CONTRIBUTOR_CHECK.is_file())

    def test_private_discovery_does_not_fetch_or_disclose_references(self):
        self.assertIn("discover\n   private plugin descriptors", self.marketplace)
        self.assertIn("must not fetch its image\n   references", self.marketplace)
        self.assertIn("Do not name a\n   source repository", self.marketplace)
        self.assertIn("`.wildcat-labs/private-plugin.json`", self.marketplace)
        self.assertIn("`fiat-contributor-check`", self.marketplace)
        self.assertIn("fetch its declared plugin subtree", self.marketplace)
        self.assertIn("Delete staging afterwards", self.marketplace)
        self.assertIn("Never\n   clone or copy its source repository root", self.marketplace)

    def test_installation_waits_for_completed_study(self):
        completed = self.marketplace.index("The spec is complete only after `hexctl done study ...` succeeds")
        install = self.marketplace.index("Install each relevant missing plugin now")
        refresh = self.marketplace.index("Finish every selected install before any skill or plugin refresh")
        self.assertLess(completed, install)
        self.assertLess(install, refresh)
        self.assertIn("Never install a wider-marketplace plugin before the study receipt exists", self.fiat)

    def test_success_receipts_omit_identity_data(self):
        self.assertIn("Never record the account email, name, login, or matching evidence", self.marketplace)
        self.assertIn("hexctl record labs_marketplace", self.marketplace)

    def test_ai_origin_markers_are_required_for_delivery_artifacts(self):
        self.assertIn("`origin:ai`", self.push_discipline)
        self.assertIn("<!-- wildcat-origin: shoggoth -->", self.push_discipline)
        self.assertIn(
            "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>",
            self.push_discipline,
        )
        self.assertIn("Wildcat-Origin: shoggoth", self.push_discipline)

    def test_provenance_is_verified_without_reclassifying_human_work(self):
        # Flattened: these assert what the instruction says, and a reflow of the
        # same sentence is not a change to it. Pinning the line breaks made an
        # edit that only rewrapped the paragraph look like a removed rule.
        flat = " ".join(self.push_discipline.split())
        self.assertIn("Read the pull request back from GitHub", flat)
        self.assertIn("same `gh pr create` command", flat)
        self.assertIn("pre-existing human commit", flat)
        self.assertIn("pre-existing human pull request", flat)

    def test_publish_phase_merges_and_closes_its_own_work(self):
        flat = " ".join(self.push_discipline.split())
        self.assertIn("permitted merge method", flat)
        self.assertIn("close that exact issue", flat)
        self.assertIn(
            "hexctl done integrate --pr-url <url> --merge-commit <sha>",
            self.push_discipline,
        )
        self.assertNotIn("Never merge it", self.push_discipline)
        self.assertIn(
            "routine publish or closure action is not a handoff",
            " ".join(self.fiat.split()),
        )

    def test_steps_stack_and_only_the_run_branch_merges_into_the_base(self):
        flat = " ".join(self.push_discipline.split())
        fiat = " ".join(self.fiat.split())
        # A step's pull request targets the step below it, never the base.
        self.assertIn("gh pr create --base <pr_base> --head <branch>", self.push_discipline)
        self.assertIn("hexctl done push --pr-url <url> --head-commit <sha> --pr-base <ref>",
                      self.push_discipline)
        self.assertIn("never point one at the recorded base", flat)
        self.assertIn("only merge into the base in the whole run", flat)
        # The stack comes down in order, in its own phase.
        self.assertIn("hexctl done merge-step --step <n> --merge-commit <sha>",
                      self.push_discipline)
        self.assertIn("Merges belong to `integrate`", self.push_discipline)
        # And the loop itself says so.
        self.assertIn("Never target the base or the repository default branch with a step pull",
                      self.fiat)
        self.assertIn("Never merge into the base more than once in a run", self.fiat)
        self.assertIn("nothing merges while the steps run", fiat.lower())


class StackBringDownTests(unittest.TestCase):
    """The order the stack comes down in, and why deleting early is fatal.

    A run merged step 1 with --delete-branch. GitHub did not retarget the pull
    request stacked on it; it closed it, and a closed pull request whose base ref
    is gone can be neither reopened nor retargeted. The instructions' own
    recovery path was unreachable from the state the instructions produced.
    """

    @classmethod
    def setUpClass(cls):
        cls.push_discipline = PUSH_DISCIPLINE.read_text(encoding="utf-8")
        cls.flat = " ".join(cls.push_discipline.split())

    def test_the_next_pull_request_is_retargeted_before_the_merge(self):
        self.assertIn("gh pr edit <next pr> --base <run branch>", self.push_discipline)
        self.assertIn("before this", self.flat)
        # Retargeting must come first in the numbered procedure.
        bring_down = self.push_discipline.split("## Bringing the stack down")[1]
        retarget = bring_down.index("gh pr edit <next pr>")
        merge = bring_down.index("Merge that step's pull request")
        self.assertLess(retarget, merge)

    def test_step_merges_do_not_delete_branches(self):
        self.assertIn("Do not pass", self.flat)
        self.assertIn("--delete-branch", self.push_discipline)
        self.assertIn("do not delete the branch here", self.flat)

    def test_the_closed_pull_request_failure_mode_is_written_down(self):
        self.assertIn("GitHub closes", self.flat)
        self.assertIn("neither reopened nor retargeted", self.flat)

    def test_cleanup_belongs_to_integrate(self):
        integration = self.push_discipline.split("## The integration pull request")[1]
        self.assertIn("delete the run branch and every step branch", " ".join(integration.split()))
        self.assertIn("one place branch cleanup happens", " ".join(integration.split()))


class OriginLabelTests(unittest.TestCase):
    """The provenance label, and not trusting a query that failed.

    A run reported the label missing and created one that already existed: the
    check ran moments after a rate-limit error, so an empty result read as an
    empty repository. A gh query shaped `list | grep -q` cannot tell absence from
    failure.
    """

    @classmethod
    def setUpClass(cls):
        cls.flat = " ".join(PUSH_DISCIPLINE.read_text(encoding="utf-8").split())

    def test_the_label_is_created_when_absent(self):
        self.assertIn("gh label create origin:ai", self.flat)

    def test_the_label_is_read_back_rather_than_assumed(self):
        self.assertIn("Read it back", self.flat)
        self.assertIn("rather than trusting that `gh pr create` applied it", self.flat)

    def test_a_failed_query_is_not_an_answer(self):
        self.assertIn("A failed query is not an answer", self.flat)
        self.assertIn("Check the exit status separately from the match", self.flat)


class BaseSyncTests(unittest.TestCase):
    """A run inherits every mistake in the ref it was cut from.

    A session began with the local base a hundred and forty-six commits behind
    the remote. Nothing in the loop said to sync it, so the study would have
    cited a starting ref that was already history.
    """

    @classmethod
    def setUpClass(cls):
        cls.fiat = FIAT.read_text(encoding="utf-8")
        cls.flat = " ".join(cls.fiat.split())

    def test_the_base_is_synced_before_any_branch_is_cut(self):
        self.assertIn("Sync the base first", self.fiat)
        self.assertIn("git merge --ff-only origin/<base>", self.fiat)
        self.assertIn("bring the base up to date before anything is cut from it", self.flat)

    def test_the_sync_is_fast_forward_only_and_refuses_a_dirty_tree(self):
        self.assertIn("Fast-forward only", self.fiat)
        self.assertIn("If the tree is dirty, stop", self.flat)

    def test_the_starting_sha_reaches_the_study(self):
        self.assertIn("state the starting SHA in the study's constraints", self.flat)


class PluginCurrencyTests(unittest.TestCase):
    """Directing the update, rather than noting the version and carrying on.

    A run drove a controller a whole evolution behind the repository it was
    editing and recorded its lint results as prose, because the installed
    audit-round did not accept flags its own ledger documented.
    """

    @classmethod
    def setUpClass(cls):
        cls.doc = PLUGIN_CURRENCY.read_text(encoding="utf-8")
        cls.flat = " ".join(cls.doc.split())
        cls.fiat = " ".join(FIAT.read_text(encoding="utf-8").split())
        cls.market = " ".join(
            MARKETPLACE.read_text(encoding="utf-8").split()
        )

    def test_preflight_directs_the_update_rather_than_noting_it(self):
        self.assertIn("plugin-currency.md", self.fiat)
        self.assertIn("Do not run the loop under a controller you have noticed is behind",
                      self.fiat)

    def test_the_host_mechanism_lives_here_only(self):
        # Both callers need it; two copies of a host list drift.
        self.assertIn("/reload-plugins", self.doc)
        self.assertIn("plugin-currency.md", self.market)
        self.assertNotIn("/reload-plugins", self.market)

    def test_the_install_route_is_established_not_assumed(self):
        self.assertIn("Do not assume", self.flat)
        self.assertIn("git-backed marketplace", self.flat)
        self.assertIn("managed marketplace", self.flat)
        self.assertIn("the agent cannot do it", self.flat)

    def test_the_two_repositories_and_the_mirror_delay_are_stated(self):
        self.assertIn("wildcat-finance/skills-marketplace", self.doc)
        self.assertIn("every five minutes", self.flat)
        self.assertIn("chain rather than a step", self.flat)

    def test_an_unfixable_gap_becomes_a_receipt(self):
        self.assertIn("hexctl record controller_version", self.doc)
        self.assertIn("say so out loud", self.flat)

    def test_hand_editing_a_plugin_cache_is_refused(self):
        self.assertIn("Do not hand-edit a plugin cache", self.flat)

    def test_the_self_hosting_case_is_excluded(self):
        self.assertIn("is not a problem", self.flat)
        self.assertIn("skips that by identity", self.flat)

    def test_a_run_cannot_enforce_what_it_just_shipped(self):
        self.assertIn("cannot take effect for the very run that made it", self.flat)


class ContributorCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_contributor_check()

    @staticmethod
    def completed(returncode=0, payload=None):
        stdout = "" if payload is None else json.dumps(payload)
        return subprocess.CompletedProcess(["gh"], returncode, stdout=stdout, stderr="")

    def test_active_org_membership_passes(self):
        responses = [
            self.completed(),
            self.completed(payload={"login": "member", "email": None}),
            self.completed(payload={"state": "active"}),
        ]
        with mock.patch.object(self.module, "_gh", side_effect=responses):
            self.assertTrue(self.module.authenticated_github_user_is_contributor())

    def test_verified_wildcat_email_passes_when_membership_is_unavailable(self):
        responses = [
            self.completed(),
            self.completed(payload={"login": "member", "email": None}),
            self.completed(returncode=1),
            self.completed(payload=[{"email": "member@wildcat.finance", "verified": True}]),
        ]
        with mock.patch.object(self.module, "_gh", side_effect=responses):
            self.assertTrue(self.module.authenticated_github_user_is_contributor())

    def test_missing_auth_fails_without_output(self):
        with mock.patch.object(self.module, "_gh", return_value=self.completed(returncode=1)):
            with mock.patch("sys.stdout") as stdout, mock.patch("sys.stderr") as stderr:
                self.assertEqual(self.module.main(), 1)
                stdout.write.assert_not_called()
                stderr.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()


class PhaseSkillInventoryTests(unittest.TestCase):
    """The README counts how many phase skills ship an executable check.

    It said four while five did. A prose count goes stale the next time one is added, and
    this run added one, so the count is derived here rather than trusted.
    """

    PHASES = ("protasis", "elenchus", "phylax", "ephoros", "metron", "hypomnema")
    WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}

    def test_the_readme_counts_the_checks_that_exist(self):
        root = Path(__file__).resolve().parents[1]
        with_script = [
            name for name in self.PHASES
            if (root / "skills" / name / "scripts" / f"{name}.py").is_file()
        ]
        readme = (root / "README.md").read_text(encoding="utf-8")
        expected = (
            f"six more skills holding each phase to a standard, "
            f"{self.WORDS[len(with_script)]} of them with an executable check:"
        )
        self.assertIn(expected, readme,
                      f"{len(with_script)} phase skills ship a check: {with_script}")

    def test_every_named_phase_skill_exists(self):
        root = Path(__file__).resolve().parents[1]
        for name in self.PHASES:
            with self.subTest(skill=name):
                self.assertTrue((root / "skills" / name / "SKILL.md").is_file())

