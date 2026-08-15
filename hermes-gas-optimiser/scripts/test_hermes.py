#!/usr/bin/env python3
"""Hermetic tests for the Hermes verification harness."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import hermes  # noqa: E402


FAKE_FORGE = r'''#!/usr/bin/env python3
import json
import sys
from pathlib import Path

repo = Path.cwd()
args = sys.argv[1:]

def read_int(name, default):
    path = repo / name
    return int(path.read_text().strip()) if path.exists() else default

if args == ["--version"]:
    print("forge Version: hermes-test")
    raise SystemExit(0)

if args == ["config", "--json"]:
    print(json.dumps({"profile": "default", "optimizer": True, "optimizer_runs": 200}))
    raise SystemExit(0)

if args and args[0] == "snapshot":
    baseline = read_int(".baseline-gas", 100)
    candidate = read_int(".candidate-gas", baseline)
    if "--diff" in args:
        arrow = "↓" if candidate < baseline else ("↑" if candidate > baseline else "━")
        delta = candidate - baseline
        percentage = (delta / baseline) * 100
        print(f"{arrow} CTest::testGas_target() (gas: {baseline} → {candidate} | {delta:+d} {percentage:+.3f}%)")
        print(f"Total tests: 1, ↑ {int(delta > 0)}, ↓ {int(delta < 0)}, ━ {int(delta == 0)}")
        raise SystemExit(0)
    if "--snap" in args:
        output = Path(args[args.index("--snap") + 1])
        gas = candidate
    else:
        output = repo / ".gas-snapshot"
        gas = baseline
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f"CTest:testGas_target() (gas: {gas})\n")
    print("snapshot ok")
    raise SystemExit(0)

if args and args[0] == "test":
    if "--gas-report" in args and (repo / ".fail-gas-report").exists():
        print("gas report failed", file=sys.stderr)
        raise SystemExit(1)
    if "--match-path" in args and (repo / ".fail-targeted").exists():
        print("targeted property failed", file=sys.stderr)
        raise SystemExit(1)
    if "--gas-report" not in args and "--match-path" not in args and (repo / ".fail-full-test").exists():
        print("full suite failed", file=sys.stderr)
        raise SystemExit(1)
    print("Suite result: ok. 1 passed; 0 failed; 0 skipped")
    raise SystemExit(0)

if args and args[0] == "inspect":
    if args[2] == "methodIdentifiers":
        print(json.dumps({"read()": "57de26a4", "value()": "3fa4f245"}))
        raise SystemExit(0)
    slot = read_int(".layout-slot", 0)
    print(json.dumps({"storage": [{"astId": 1, "contract": args[1], "label": "value", "offset": 0, "slot": str(slot), "type": "t_uint256"}], "types": {"t_uint256": {"encoding": "inplace", "label": "uint256", "numberOfBytes": "32"}}}))
    raise SystemExit(0)

print(f"unsupported fake forge invocation: {args}", file=sys.stderr)
raise SystemExit(64)
'''


SOURCE_BASELINE = """// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.25;

contract C {
    uint256 public value;

    function read() external view returns (uint256) {
        return value;
    }
}
"""


SOURCE_CACHED = """// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.25;

contract C {
    uint256 public value;

    function read() external view returns (uint256 result) {
        result = value;
    }
}
"""


SOURCE_UNCHECKED = """// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.25;

contract C {
    uint256 public value;

    function read() external view returns (uint256 result) {
        unchecked { result = value + 1; }
    }
}
"""


class HermesHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="hermes-tests-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.run_dir = self.root / "evidence"
        self.bin_dir = self.root / "bin"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "test").mkdir()
        self.bin_dir.mkdir()
        (self.repo / "foundry.toml").write_text("[profile.default]\noptimizer = true\n")
        (self.repo / "src" / "C.sol").write_text(SOURCE_BASELINE)
        (self.repo / "test" / "C.t.sol").write_text(
            "// SPDX-License-Identifier: UNLICENSED\npragma solidity ^0.8.25;\ncontract CTest { function testGas_target() public {} }\n"
        )
        forge = self.bin_dir / "forge"
        forge.write_text(FAKE_FORGE)
        forge.chmod(0o755)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Hermes Tests"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "hermes@example.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "add", "foundry.toml", "src/C.sol", "test/C.t.sol"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=self.repo, check=True)
        self.environment = os.environ.copy()
        self.environment["PATH"] = f"{self.bin_dir}{os.pathsep}{self.environment['PATH']}"
        self.path_patch = mock.patch.dict(os.environ, self.environment, clear=True)
        self.path_patch.start()

    def tearDown(self) -> None:
        self.path_patch.stop()
        self.temporary.cleanup()

    def baseline(self, protected: bool = True) -> None:
        contract_args = (
            ["--protected-contract", "C=src/C.sol:C"]
            if protected
            else ["--assert-no-protected-contracts", "--layout-contract", "C=src/C.sol:C"]
        )
        code = hermes.main(
            [
                "baseline",
                "--repo",
                str(self.repo),
                "--evidence-dir",
                str(self.run_dir),
                "--fuzz-seed",
                "0x5EED",
                *contract_args,
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((self.run_dir / "state.json").read_text())["status"], "baseline_ready")

    def verify(self, *extra: str, optimisation_class: str = "storage-load-caching") -> int:
        return hermes.main(
            [
                "verify",
                "--run-dir",
                str(self.run_dir),
                "--optimisation-class",
                optimisation_class,
                "--attest-single-class",
                "--gas-target",
                "testGas_target",
                *extra,
            ]
        )

    def prepare_candidate(self, source: str = SOURCE_CACHED, gas: int = 90) -> None:
        (self.repo / "src" / "C.sol").write_text(source)
        (self.repo / ".candidate-gas").write_text(str(gas))

    def test_accepts_and_promotes_a_fully_verified_candidate(self) -> None:
        self.baseline()
        self.prepare_candidate()
        self.assertEqual(self.verify("--no-accrual-unchecked"), 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["status"], "accepted")
        self.assertEqual([gate["id"] for gate in result["gates"]], [1, 2, 3, 4, 5, 6])
        self.assertEqual(result["storage_layouts"][0]["status"], "identical")
        self.assertEqual(result["method_identifiers"][0]["status"], "identical")
        self.assertEqual(hermes.main(["promote", "--run-dir", str(self.run_dir)]), 0)
        self.assertIn("(gas: 90)", (self.repo / ".gas-snapshot").read_text())

    def test_rejects_any_gas_regression_at_gate_three(self) -> None:
        self.baseline()
        self.prepare_candidate(gas=101)
        self.assertEqual(self.verify("--no-accrual-unchecked"), 30)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["failed_gate"], 3)
        self.assertIn("gas regression", result["reason"])

    def test_rejects_full_suite_failure_at_gate_four(self) -> None:
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".fail-full-test").write_text("1")
        self.assertEqual(self.verify("--no-accrual-unchecked"), 40)
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 4)

    def test_hard_aborts_on_protected_layout_change(self) -> None:
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".layout-slot").write_text("1")
        self.assertEqual(self.verify("--no-accrual-unchecked"), 50)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["failed_gate"], 5)
        self.assertIn("storage layout changed", result["reason"])

    def test_records_declared_layout_change_on_non_frozen_contract(self) -> None:
        self.baseline(protected=False)
        self.prepare_candidate()
        (self.repo / ".layout-slot").write_text("1")
        code = self.verify(
            "--no-accrual-unchecked",
            "--allow-unprotected-layout-change",
            "--layout-change-rationale",
            "No proxy, hook, role provider, delegate call, factory deployment, or indexer reads this layout.",
            optimisation_class="storage-packing",
        )
        self.assertEqual(code, 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["storage_layouts"][0]["status"], "changed_permitted")

    def test_rejects_unchecked_hidden_inside_another_class(self) -> None:
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        self.assertEqual(
            self.verify(
                "--no-accrual-unchecked",
                "--non-accrual-rationale",
                "This arithmetic is unrelated to every accrual input and output.",
            ),
            20,
        )
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 2)

    def test_requires_and_runs_targeted_accrual_property_test(self) -> None:
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        code = self.verify(
            "--accrual-unchecked",
            "--targeted-match-path",
            "test/C.t.sol",
            "--targeted-match-test",
            "testFuzz_accrualDifferential",
            "--property-proof",
            "Compare checked and unchecked accrual results across the bounded timestamp and rate domains.",
            optimisation_class="unchecked-arithmetic",
        )
        self.assertEqual(code, 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertTrue(result["accrual_unchecked"]["applicable"])
        self.assertEqual(result["accrual_unchecked"]["status"], "passed")

    def test_targeted_accrual_property_failure_rejects_gate_six(self) -> None:
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        (self.repo / ".fail-targeted").write_text("1")
        code = self.verify(
            "--accrual-unchecked",
            "--targeted-match-path",
            "test/C.t.sol",
            "--targeted-match-test",
            "testFuzz_accrualDifferential",
            "--property-proof",
            "Compare checked and unchecked accrual results across the bounded timestamp and rate domains.",
            optimisation_class="unchecked-arithmetic",
        )
        self.assertEqual(code, 60)
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
