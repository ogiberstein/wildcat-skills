"""The controller-currency gate suite, in its own module.

`test_hexctl.py` is cited as authored law by the promise machine, whose
bounded read refuses a contract over 262144 bytes; the gate suite did not
fit in the file's remaining headroom. The class drives the same CLI surface
through the same fixtures -- `HexctlCase` and its fake delivery tools -- so
only the file boundary moved, not the arrangement under test.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from unittest import mock

try:
    from plugins.hexaemeron.tests.test_hexctl import (
        HEXCTL,
        HexctlCase,
        hexctl_module,
        run_target,
    )
except ModuleNotFoundError:
    from test_hexctl import (
        HEXCTL,
        HexctlCase,
        hexctl_module,
        run_target,
    )


PROVENANCE_FIELDS = {
    "ledger_version",
    "route",
    "pin",
    "observed_head",
    "verdict",
    "warning",
    "waiver",
}
"""Every key the controller-currency receipt and init transition carry."""


class TestControllerCurrency(HexctlCase):
    """The init gate on the running controller's pin-versus-upstream verdict.

    The pre-fix red these guards captured: the entry controller recorded only
    topic, base and run branch at init, so a fabricated behind pin started a
    run silently. Each test here fails when the `observe_controller_currency`
    call is removed from `cmd_init`.
    """

    PIN = "b" * 40
    HEAD = "a" * 40

    def install_layout(self, pin=PIN, head="ref: refs/heads/main\n",
                       registry=None, clone=True, ledger=True):
        """A fabricated host install around a cache copy of the controller.

        Builds `<root>/cache/<marketplace>/<plugin>/<version>/skills/fiat/
        scripts/hexctl.py` with the registry and marketplace clone beside it,
        so the copy observes the git-backed route with no real install and no
        network: the fake `git` on PATH answers the one `ls-remote`.
        """
        root = os.path.join(self.dir, "plugins-root")
        install = os.path.join(root, "cache", "wildcat-labs", "hexaemeron",
                               "1.5.9")
        scripts = os.path.join(install, "skills", "fiat", "scripts")
        os.makedirs(scripts)
        controller = os.path.join(scripts, "hexctl.py")
        shutil.copyfile(HEXCTL, controller)
        if ledger:
            with open(os.path.join(install, "skills", "fiat", "EVOLUTION.md"),
                      "w", encoding="utf-8") as handle:
                handle.write("- Current version: `fiat-vTEST`\n")
        if registry is None:
            registry = json.dumps({
                "version": 2,
                "plugins": {
                    "hexaemeron@wildcat-labs": [{
                        "scope": "user",
                        "installPath": install + os.sep,
                        "version": "1.5.9",
                        "installedAt": "2026-08-24T00:00:00Z",
                        "gitCommitSha": pin,
                    }],
                },
            })
        if registry is not False:
            with open(os.path.join(root, "installed_plugins.json"), "w",
                      encoding="utf-8") as handle:
                handle.write(registry)
        if clone:
            clone_git = os.path.join(root, "marketplaces", "wildcat-labs",
                                     ".git")
            os.makedirs(clone_git)
            if head is not None:
                with open(os.path.join(clone_git, "HEAD"), "w",
                          encoding="utf-8") as handle:
                    handle.write(head)
        return controller

    def run_installed_ctl(self, controller, *args, expect=0, extra_env=None):
        """Drive one cache copy of the controller against this checkout."""
        env = dict(self.env)
        env["FAKE_GIT_REFS"] = json.dumps({"main": self.HEAD})
        env["FAKE_GIT_PARENTS"] = "{}"
        env["FAKE_GH_PRS"] = "{}"
        if extra_env:
            env.update(extra_env)
        proc = subprocess.run(
            [sys.executable, controller, *args],
            cwd=self.dir,
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.returncode != expect:
            raise AssertionError(
                f"installed hexctl {' '.join(args)} -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\n"
                f"stderr: {proc.stderr}"
            )
        return proc

    def provenance(self):
        """The controller-currency receipt and init transition, read back."""
        target = run_target(self.dir)
        with open(os.path.join(target, ".hexaemeron", "state.json"),
                  encoding="utf-8") as handle:
            state = json.load(handle)
        with open(os.path.join(target, ".hexaemeron", "ledger.jsonl"),
                  encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        receipt = state["receipts"]["controller_currency"]
        transition = entries[0]["data"]["controller_currency"]
        self.assertEqual(entries[0]["event"], "init")
        self.assertEqual(receipt, transition)
        self.assertEqual(set(receipt), PROVENANCE_FIELDS)
        return receipt

    def porcelain(self):
        """The target tree's untracked and modified paths, lock aside.

        The lock file under `.hexaemeron/` is excluded: every refused init
        leaves it, with or without this gate, because the lock is taken
        before the command runs.
        """
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.dir, capture_output=True, text=True, check=True,
        )
        return sorted(line for line in status.stdout.splitlines()
                      if line.strip() and ".hexaemeron" not in line)

    def assert_tree_untouched(self, before):
        """No worktree, state, ledger or breadcrumb after a refusal."""
        state_root = os.path.join(self.dir, ".hexaemeron")
        for name in ("state.json", "ledger.jsonl", "worktree"):
            self.assertFalse(os.path.exists(os.path.join(state_root, name)),
                             f"a refused init recorded {name}")
        self.assertFalse(os.path.exists(os.path.join(self.dir, "tmp")))
        self.assertEqual(self.porcelain(), before,
                         "a refused init changed the target tree")
        trees = subprocess.run(
            ["git", "worktree", "list"],
            cwd=self.dir, capture_output=True, text=True, check=True,
        )
        self.assertEqual(len(trees.stdout.strip().splitlines()), 1,
                         "a refused init left a worktree behind")

    # ------------------------------------------------- git-backed route

    def test_init_refuses_a_proven_behind_pin_before_any_mutation(self):
        controller = self.install_layout()
        before = self.porcelain()
        proc = self.run_installed_ctl(controller, "init", "--topic", "t",
                                      expect=1)
        self.assertIn("controller currency", proc.stderr)
        self.assertIn(self.PIN, proc.stderr)
        self.assertIn(self.HEAD, proc.stderr)
        self.assertIn("installer", proc.stderr)
        self.assertIn("--controller-currency-waiver", proc.stderr)
        self.assertNotIn("https://", proc.stderr)
        self.assert_tree_untouched(before)

    def test_init_waiver_proceeds_on_behind_and_records_the_reason(self):
        controller = self.install_layout()
        self.run_installed_ctl(
            controller, "init", "--topic", "t",
            "--controller-currency-waiver", "pin refresh needs the operator",
        )
        receipt = self.provenance()
        self.assertEqual(receipt["ledger_version"], "fiat-vTEST")
        self.assertEqual(receipt["route"], "git-backed")
        self.assertEqual(receipt["pin"], self.PIN)
        self.assertEqual(receipt["observed_head"], self.HEAD)
        self.assertEqual(receipt["verdict"], "behind")
        self.assertIsNone(receipt["warning"])
        self.assertEqual(receipt["waiver"], "pin refresh needs the operator")

    def test_init_refuses_an_empty_waiver_reason(self):
        controller = self.install_layout()
        before = self.porcelain()
        proc = self.run_installed_ctl(
            controller, "init", "--topic", "t",
            "--controller-currency-waiver", "   ", expect=2,
        )
        self.assertIn("reason", proc.stderr)
        self.assert_tree_untouched(before)

    def test_init_current_pin_proceeds_with_provenance(self):
        controller = self.install_layout(pin=self.HEAD)
        proc = self.run_installed_ctl(controller, "init", "--topic", "t")
        self.assertNotIn("warning", proc.stderr)
        receipt = self.provenance()
        self.assertEqual(receipt["route"], "git-backed")
        self.assertEqual(receipt["verdict"], "current")
        self.assertEqual(receipt["pin"], self.HEAD)
        self.assertEqual(receipt["observed_head"], self.HEAD)
        self.assertIsNone(receipt["waiver"])

    def test_init_remote_url_confined_to_the_marketplace_clone(self):
        """A hostile target repository cannot steer where the read goes.

        The target's own config carries a URL rewrite; the observation must
        run inside the marketplace clone and name the remote `origin`, so the
        rewrite never applies and no URL string passes through the
        controller at all.
        """
        subprocess.run(
            ["git", "config", "url.https://evil.example/.insteadOf",
             "https://github.com/"],
            cwd=self.dir, check=True, capture_output=True,
        )
        controller = self.install_layout(pin=self.HEAD)
        log = os.path.join(self.dir, "ls-remote.log")
        self.run_installed_ctl(controller, "init", "--topic", "t",
                               extra_env={"FAKE_GIT_LS_REMOTE_LOG": log})
        with open(log, encoding="utf-8") as handle:
            calls = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(len(calls), 1, "exactly one upstream read at init")
        clone = os.path.realpath(
            os.path.join(self.dir, "plugins-root", "marketplaces",
                         "wildcat-labs"))
        self.assertEqual(os.path.realpath(calls[0]["cwd"]), clone)
        self.assertEqual(
            calls[0]["args"],
            ["ls-remote", "--refs", "origin", "refs/heads/main"],
        )
        self.assertNotIn("evil.example", json.dumps(self.provenance()))

    # ------------------------------------------- managed and in-repo routes

    def test_init_managed_route_proceeds_without_a_network_read(self):
        """Managed means the registry records no pin; nothing is read remote.

        The marketplace clone is present in this fixture on purpose: the
        managed route is decided by the absent pin, and even an available
        clone is not read.
        """
        controller = self.install_layout(pin=None)
        log = os.path.join(self.dir, "ls-remote.log")
        self.run_installed_ctl(controller, "init", "--topic", "t",
                               extra_env={"FAKE_GIT_LS_REMOTE_LOG": log})
        self.assertFalse(os.path.exists(log),
                         "the managed route made a network read")
        receipt = self.provenance()
        self.assertEqual(receipt["route"], "managed")
        self.assertEqual(receipt["verdict"], "managed")
        self.assertIsNone(receipt["pin"])
        self.assertIsNone(receipt["observed_head"])

    def test_init_pinned_install_with_missing_clone_reads_unknown(self):
        """Deleting the marketplace clone must not read as `managed` (S2-R1-02).

        A registry pin makes the install git-backed; with the clone gone the
        head is unobservable, so the verdict is `unknown` with a named warning
        and the pin still recorded -- never a warning-free `managed` that
        silences the gate.
        """
        controller = self.install_layout(clone=False)
        log = os.path.join(self.dir, "ls-remote.log")
        receipt = self.assert_unknown_proceeds(
            controller, "clone-missing",
            extra_env={"FAKE_GIT_LS_REMOTE_LOG": log})
        self.assertFalse(os.path.exists(log),
                         "a missing clone still made a network read")
        self.assertEqual(receipt["route"], "git-backed")
        self.assertEqual(receipt["pin"], self.PIN)

    def test_init_in_repo_route_records_nulls_and_no_pin(self):
        log = os.path.join(self.dir, "ls-remote.log")
        self.env["FAKE_GIT_LS_REMOTE_LOG"] = log
        try:
            self.init()
        finally:
            self.env.pop("FAKE_GIT_LS_REMOTE_LOG", None)
        self.assertFalse(os.path.exists(log),
                         "the in-repo route made a network read")
        receipt = self.provenance()
        self.assertEqual(receipt["route"], "in-repo-source")
        self.assertEqual(receipt["verdict"], "no-pin")
        self.assertIsNone(receipt["pin"])
        self.assertIsNone(receipt["observed_head"])
        self.assertTrue(receipt["ledger_version"].startswith("fiat-v"))

    # ------------------------------------------------- hostile registry

    def assert_unknown_proceeds(self, controller, warning, extra_env=None):
        proc = self.run_installed_ctl(controller, "init", "--topic", "t",
                                      extra_env=extra_env)
        self.assertIn("controller currency", proc.stderr)
        self.assertIn(warning, proc.stderr)
        receipt = self.provenance()
        self.assertEqual(receipt["verdict"], "unknown")
        self.assertEqual(receipt["warning"], warning)
        self.assertIsNone(receipt["observed_head"])
        return receipt

    def test_init_missing_registry_is_unknown_and_warns(self):
        controller = self.install_layout(registry=False)
        receipt = self.assert_unknown_proceeds(controller, "registry-missing")
        self.assertEqual(receipt["route"], "unknown")
        self.assertIsNone(receipt["pin"])

    def test_init_malformed_registry_json_is_unknown(self):
        controller = self.install_layout(registry="{not json")
        self.assert_unknown_proceeds(controller, "registry-malformed")

    def test_init_wrong_kind_registry_is_unknown(self):
        controller = self.install_layout(
            registry=json.dumps({"version": 2, "plugins": [1, 2]}))
        self.assert_unknown_proceeds(controller, "registry-wrong-kind")

    def test_init_oversized_registry_is_unknown(self):
        controller = self.install_layout(
            registry="x" * (1024 * 1024 + 1))
        self.assert_unknown_proceeds(controller, "registry-oversized")

    def test_init_unmatched_install_path_is_unknown(self):
        controller = self.install_layout(registry=json.dumps({
            "version": 2,
            "plugins": {
                "hexaemeron@wildcat-labs": [{
                    "installPath": os.path.join(self.dir, "elsewhere") + os.sep,
                    "gitCommitSha": self.PIN,
                }],
            },
        }))
        self.assert_unknown_proceeds(controller, "registry-unmatched")

    def test_init_malformed_remote_line_is_unknown(self):
        controller = self.install_layout(pin=self.HEAD)
        self.assert_unknown_proceeds(
            controller, "remote-malformed",
            extra_env={"FAKE_GIT_MODE": "remote-malformed"},
        )

    # ----------------------------------------------------- old-state compat

    def test_old_state_without_the_receipt_stays_loadable(self):
        """A run recorded before this change loads, reports and verifies."""
        self.init()
        module = hexctl_module()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        self.assertIn("controller_currency", state["receipts"])
        del state["receipts"]["controller_currency"]
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        del entries[0]["data"]["controller_currency"]
        entries[0]["state"] = module.state_fingerprint(state)
        entries[0]["hash"] = hashlib.sha256(
            module.canonical(
                {
                    "ts": entries[0]["ts"],
                    "event": entries[0]["event"],
                    "data": entries[0]["data"],
                    "prev": entries[0]["prev"],
                    "state": entries[0]["state"],
                }
            ).encode()
        ).hexdigest()
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        self.run_ctl("status")
        self.run_ctl("verify")
        self.run_ctl("next")

    # --------------------------------------------------- receipt integrity

    def test_record_refuses_to_rewrite_the_currency_receipt(self):
        """`hexctl record` cannot replace init's observation (S2-R1-01).

        The receipt is init's own evidence, protected like `task_issue`: a
        later `record controller_currency` would replace the recorded verdict
        and waiver with a value nothing observed, while the honest copy
        survived only in the init transition.
        """
        self.init()
        receipt = self.provenance()
        proc = self.run_ctl(
            "record", "controller_currency",
            json.dumps({"verdict": "current", "route": "git-backed"}),
            expect=2,
        )
        self.assertIn("only `hexctl init` writes it", proc.stderr)
        self.assertEqual(self.provenance(), receipt,
                         "a refused record changed the currency receipt")

    # ------------------------------------------------- observation units

    def test_observation_seam_confines_remote_reader_inputs(self):
        """The reader receives only the clone path and branch derived from
        the controller's own file; a verdict follows from its answer."""
        module = hexctl_module()
        controller = self.install_layout()
        calls = []

        def reader(clone_dir, branch):
            calls.append((clone_dir, branch))
            return self.HEAD, None

        observation = module.observe_controller_currency(
            controller_file=controller, remote_reader=reader)
        clone = os.path.join(self.dir, "plugins-root", "marketplaces",
                             "wildcat-labs")
        self.assertEqual(
            [(os.path.realpath(path), branch) for path, branch in calls],
            [(os.path.realpath(clone), "main")],
        )
        self.assertEqual(observation["verdict"], "behind")
        self.assertEqual(observation["pin"], self.PIN)
        self.assertEqual(observation["observed_head"], self.HEAD)

    def test_remote_head_parsing_refuses_hostile_output(self):
        """Anything but exactly one well-formed ref line reads as a warning."""
        module = hexctl_module()
        fake_bin = os.path.join(self.dir, "parse-bin")
        os.makedirs(fake_bin)
        script = os.path.join(fake_bin, "git")
        cases = {
            "absent": "",
            "duplicate": f"{self.HEAD}\\trefs/heads/main\\n" * 2,
            "not-a-sha": "not-a-sha\\trefs/heads/main\\n",
            "wrong-ref": f"{self.HEAD}\\trefs/heads/other\\n",
        }
        clone = os.path.join(self.dir, "clone")
        os.makedirs(clone)
        path = fake_bin + os.pathsep + os.environ.get("PATH", "")
        for name, output in cases.items():
            with open(script, "w", encoding="utf-8") as handle:
                handle.write(
                    "#!/usr/bin/env python3\n"
                    f"import sys; sys.stdout.write('{output}')\n"
                )
            os.chmod(script, 0o755)
            with mock.patch.dict(os.environ, {"PATH": path}):
                head, warning = module.currency_remote_head(clone, "main")
            self.assertIsNone(head, name)
            self.assertEqual(warning, "remote-malformed", name)
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                f"import sys; sys.stdout.write('{self.HEAD}\\trefs/heads/main\\n')\n"
            )
        os.chmod(script, 0o755)
        with mock.patch.dict(os.environ, {"PATH": path}):
            head, warning = module.currency_remote_head(clone, "main")
        self.assertEqual(head, self.HEAD)
        self.assertIsNone(warning)

    def test_observe_currency_timeout_reads_unknown(self):
        """A stalled upstream read is a named warning, never a verdict."""
        module = hexctl_module()
        controller = self.install_layout()
        fake_bin = os.path.join(self.dir, "slow-bin")
        os.makedirs(fake_bin)
        script = os.path.join(fake_bin, "git")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write("#!/usr/bin/env python3\nimport time\ntime.sleep(5)\n")
        os.chmod(script, 0o755)
        path = fake_bin + os.pathsep + os.environ.get("PATH", "")
        with mock.patch.object(module, "GIT_TIMEOUT", 0.2), \
                mock.patch.dict(os.environ, {"PATH": path}):
            observation = module.observe_controller_currency(
                controller_file=controller)
        self.assertEqual(observation["route"], "git-backed")
        self.assertEqual(observation["pin"], self.PIN)
        self.assertIsNone(observation["observed_head"])
        self.assertEqual(observation["verdict"], "unknown")
        self.assertEqual(observation["warning"], "remote-timeout")

    def test_prompts_are_disabled_on_the_upstream_read(self):
        """The one network call runs with credential prompts turned off."""
        module = hexctl_module()
        fake_bin = os.path.join(self.dir, "env-bin")
        os.makedirs(fake_bin)
        script = os.path.join(fake_bin, "git")
        witness = os.path.join(self.dir, "prompt-env.json")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                f"with open({witness!r}, 'w') as out:\n"
                "    json.dump(os.environ.get('GIT_TERMINAL_PROMPT'), out)\n"
                f"sys.stdout.write('{self.HEAD}\\trefs/heads/main\\n')\n"
            )
        os.chmod(script, 0o755)
        clone = os.path.join(self.dir, "clone")
        os.makedirs(clone)
        path = fake_bin + os.pathsep + os.environ.get("PATH", "")
        with mock.patch.dict(os.environ, {"PATH": path}):
            head, warning = module.currency_remote_head(clone, "main")
        self.assertEqual(head, self.HEAD)
        self.assertIsNone(warning)
        with open(witness, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), "0")
