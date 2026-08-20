import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promise_machine.py"
LAW = ROOT / "PROMISE_MACHINE.md"
FIXTURE = ROOT / "tests" / "fixtures" / "promise-machine" / "divergent-copy"
FIXTURES = ROOT / "tests" / "fixtures" / "promise-machine"
PROMISE_FIELDS = (
    "Promise",
    "Evidence",
    "Evidence classes",
    "Boundary",
    "Authorises",
    "Consequence",
    "Refuses",
    "Recovery",
    "Exceptions",
)


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_plugin(root, name="example"):
    plugin = root / "plugins" / name
    for host in (".claude-plugin", ".codex-plugin"):
        manifest = plugin / host / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps({"name": name, "version": "0.0.0"}) + "\n",
            encoding="utf-8",
        )
    return plugin


def write_skill(plugin, name="example", *, promise_id="example-check", fields=None):
    directory = plugin / "skills" / name
    directory.mkdir(parents=True)
    values = {
        "Promise": "The named check accepted the subject.",
        "Evidence": "example check record",
        "Evidence classes": "checked",
        "Boundary": "No claim beyond the named rule.",
        "Authorises": "Use of the checked result.",
        "Consequence": "1",
        "Refuses": "Use of a missing or failed result.",
        "Recovery": "Repair the input and rerun the check.",
        "Exceptions": "none",
    }
    if fields is not None:
        values = fields
    rows = "\n".join(f"- {field}: {value}" for field, value in values.items())
    (directory / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: A fixture skill.\n"
        "---\n\n"
        f"# {name}\n\n"
        "## Promise Machine contract\n\n"
        f"### {promise_id}\n\n"
        f"{rows}\n",
        encoding="utf-8",
    )
    (directory / "EVOLUTION.md").write_text("# Evolution\n", encoding="utf-8")
    return directory


class PromiseLawTests(unittest.TestCase):
    def test_repository_law_and_copies_are_clean(self):
        completed = run_cli("check", "--only", "law,copies")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("clean: 14 plugin(s), 14 copy/copies", completed.stdout)

    def test_sync_check_is_read_only_and_clean(self):
        before = {path: path.read_bytes() for path in ROOT.glob("plugins/*/PROMISE_MACHINE.md")}
        completed = run_cli("sync", "--check")
        after = {path: path.read_bytes() for path in ROOT.glob("plugins/*/PROMISE_MACHINE.md")}
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(before, after)

    def test_all_plugin_copies_are_exact_and_marked(self):
        law = LAW.read_bytes()
        copies = sorted(ROOT.glob("plugins/*/PROMISE_MACHINE.md"))
        self.assertEqual(len(copies), 14)
        for copy in copies:
            with self.subTest(copy=copy):
                self.assertEqual(copy.read_bytes(), law)
                self.assertTrue(
                    any(
                        b"copies=generated" in line
                        for line in copy.read_bytes().splitlines()[:5]
                    )
                )

    def test_json_report_matches_the_text_result(self):
        completed = run_cli("check", "--only", "law,copies", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["contract"], "promise-machine/v1")
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["plugins"], 14)
        self.assertEqual(report["findings"], [])

    def test_divergent_copy_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            shutil.copytree(FIXTURE / "plugins", target / "plugins")
            completed = run_cli("check", "--root", target, "--only", "law,copies", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual([item["code"] for item in report["findings"]], ["PM014"])

    def test_empty_plugin_set_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            (target / "plugins").mkdir()
            completed = run_cli("check", "--root", target, "--only", "law,copies", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM010", [item["code"] for item in report["findings"]])

    def test_copy_only_refuses_an_absent_root_law(self):
        completed = run_cli(
            "check", "--root", FIXTURE, "--only", "copies", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(report["ok"])
        self.assertIn("PM001", [item["code"] for item in report["findings"]])

    def test_law_only_does_not_require_a_plugin_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            completed = run_cli(
                "check", "--root", target, "--only", "law", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["plugins"], 0)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_copy_is_refused_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            shutil.copy2(LAW, target / LAW.name)
            plugin = make_plugin(target)
            outside = Path(directory) / "outside.md"
            outside.write_bytes(LAW.read_bytes())
            (plugin / LAW.name).symlink_to(outside)
            completed = run_cli("sync", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM013", [item["code"] for item in report["findings"]])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_plugin_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            shutil.copy2(LAW, target / LAW.name)
            (target / "plugins").mkdir()
            outside = Path(directory) / "outside"
            make_plugin(outside)
            (target / "plugins" / "escape").symlink_to(outside / "plugins" / "example")
            completed = run_cli("sync", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM011", [item["code"] for item in report["findings"]])

    def test_sync_repairs_a_divergent_fixed_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            plugin = make_plugin(target)
            destination = plugin / LAW.name
            destination.write_text("drift\n", encoding="utf-8")
            completed = run_cli("sync", "--root", target, "--json")
            leftovers = list(plugin.glob(f".{LAW.name}.*"))
            repaired = destination.read_bytes()
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["written"], 1)
        self.assertEqual(repaired, LAW.read_bytes())
        self.assertEqual(leftovers, [])


class PromiseInventoryTests(unittest.TestCase):
    def test_repository_inventory_is_derived_from_disk(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["plugins"], 14)
        self.assertEqual(report["counts"]["canonical_skills"], 28)
        self.assertEqual(report["counts"]["governed_skills"], 23)
        self.assertEqual(report["counts"]["vendored_skills"], 5)
        self.assertEqual(report["counts"]["routers"], 1)

    def test_nested_fizz_subsidiaries_are_discovered(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        paths = {item["path"] for item in report["inventory"]["skills"]}
        self.assertIn(
            "plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md", paths
        )
        self.assertIn(
            "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md", paths
        )

    def test_inventory_text_and_json_results_agree(self):
        json_run = run_cli("inventory", "--json")
        text_run = run_cli("inventory")
        report = json.loads(json_run.stdout)
        self.assertEqual(json_run.returncode, text_run.returncode)
        for key in ("plugins", "canonical_skills", "governed_skills", "vendored_skills"):
            self.assertIn(f"{key}={report['counts'][key]}", text_run.stdout)

    def test_empty_canonical_skill_set_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            make_plugin(target)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM020", [item["code"] for item in report["findings"]])

    def test_unclassified_skill_fixture_is_refused(self):
        completed = run_cli(
            "inventory", "--root", FIXTURES / "unclassified-skill", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM024", [item["code"] for item in report["findings"]])

    def test_vendored_skill_without_complete_ownership_binding_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = plugin / "skills" / "upstream"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: upstream\ndescription: fixture\n---\n", encoding="utf-8"
            )
            (skill / "NOTICE.md").write_text(
                "This skill is vendored verbatim.\n\n- Upstream: https://example.invalid\n"
                "- Release tag: v1\n- Vendored: today\n",
                encoding="utf-8",
            )
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM026", [item["code"] for item in report["findings"]])

    def test_inventory_does_not_claim_copy_checks_it_did_not_run(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["copies"], 0)
        checked = run_cli("check", "--only", "inventory,structure")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("0 copy/copies", checked.stdout)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_router_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            plugin = make_plugin(target)
            write_skill(plugin)
            router_root = target / ".agents" / "skills"
            router_root.mkdir(parents=True)
            outside = Path(directory) / "outside" / "router"
            outside.mkdir(parents=True)
            (outside / "SKILL.md").write_text(
                "---\nname: router\ndescription: fixture\n---\n", encoding="utf-8"
            )
            (router_root / "router").symlink_to(outside, target_is_directory=True)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM025", [item["code"] for item in report["findings"]])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_overlay_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            plugin = make_plugin(target)
            write_skill(plugin)
            outside = Path(directory) / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (plugin / "PROMISES.md").symlink_to(outside)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM025", [item["code"] for item in report["findings"]])


class PromiseStructureTests(unittest.TestCase):
    def test_repository_structure_is_clean_before_contract_population(self):
        completed = run_cli("check", "--only", "inventory,structure", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["promises"], 0)

    def test_missing_contract_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "missing-contract",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM031", [item["code"] for item in report["findings"]])

    def test_each_missing_promise_field_is_refused(self):
        for missing in PROMISE_FIELDS:
            with self.subTest(field=missing), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                plugin = make_plugin(target)
                values = {
                    field: "none" if field == "Exceptions" else "fixture value"
                    for field in PROMISE_FIELDS
                    if field != missing
                }
                if "Evidence classes" in values:
                    values["Evidence classes"] = "checked"
                if "Consequence" in values:
                    values["Consequence"] = "1"
                write_skill(plugin, fields=values)
                completed = run_cli(
                    "check", "--root", target, "--only", "inventory,structure", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("PM034", [item["code"] for item in report["findings"]])

    def test_unsupported_evidence_class_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unsupported-evidence-class",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM036", [item["code"] for item in report["findings"]])

    def test_no_recovery_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "no-recovery",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM034", [item["code"] for item in report["findings"]])

    def test_duplicate_promise_ids_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin, "one", promise_id="same-promise")
            write_skill(plugin, "two", promise_id="same-promise")
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM035", [item["code"] for item in report["findings"]])

    def test_unattributed_exception_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unattributed-exception",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM038", [item["code"] for item in report["findings"]])

    def test_exception_keywords_without_structured_attribution_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            fields = {
                "Promise": "The named check accepted the subject.",
                "Evidence": "example record",
                "Evidence classes": "checked",
                "Boundary": "No claim beyond the named rule.",
                "Authorises": "Use of the checked result.",
                "Consequence": "1",
                "Refuses": "Use of a failed result.",
                "Recovery": "Repair and rerun.",
                "Exceptions": (
                    "Authority is absent, scope is unknown, no record exists and expiry never applies."
                ),
            }
            write_skill(plugin, fields=fields)
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM038", [item["code"] for item in report["findings"]])

    def test_vendored_instruction_cannot_author_its_own_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = write_skill(plugin, "upstream")
            (skill / "EVOLUTION.md").unlink()
            (skill / "LICENSE").write_text("fixture licence\n", encoding="utf-8")
            (skill / "NOTICE.md").write_text(
                "This skill is vendored verbatim.\n\n- Upstream: https://example.invalid\n"
                "- Release tag: v1\n- Vendored: today\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM029", [item["code"] for item in report["findings"]])


class PromiseIdentityTests(unittest.TestCase):
    def test_repository_identity_router_versions_and_hosts_are_clean(self):
        completed = run_cli(
            "check", "--only", "identity,routers,versions,hosts", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["canonical_skills"], 28)
        self.assertEqual(report["counts"]["routers"], 1)
        self.assertEqual(report["counts"]["claude_plugins"], 14)
        self.assertEqual(report["counts"]["codex_plugins"], 14)
        self.assertEqual(report["counts"]["package_versions"], 14)
        self.assertEqual(report["counts"]["skill_versions"], 23)

    def test_unresolved_router_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unresolved-router",
            "--only",
            "routers",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM041", [item["code"] for item in report["findings"]])

    def test_duplicate_canonical_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "duplicate-canonical",
            "--only",
            "identity",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM044", [item["code"] for item in report["findings"]])

    def test_package_as_skill_version_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "package-as-skill-version",
            "--only",
            "versions",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM046", [item["code"] for item in report["findings"]])

    def test_router_with_a_behavioural_version_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin)
            router = target / ".agents" / "skills" / "promise-machine" / "SKILL.md"
            router.parent.mkdir(parents=True)
            router.write_text(
                "---\nname: promise-machine\ndescription: fixture\n"
                "metadata:\n  version: \"1.0.0\"\n---\n\n"
                "# Promise Machine\n\n[Root](../../../AGENTS.md)\n",
                encoding="utf-8",
            )
            (target / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "routers", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM043", [item["code"] for item in report["findings"]])


if __name__ == "__main__":
    unittest.main()
