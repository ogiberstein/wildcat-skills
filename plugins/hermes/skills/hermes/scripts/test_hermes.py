#!/usr/bin/env python3
"""Hermetic tests for the Hermes verification harness."""

from __future__ import annotations

import json
import os
import shutil
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
    snapshot = f"CTest:testGas_target() (gas: {gas})\n"
    if (repo / ".include-invariant").exists():
        calls = read_int(".candidate-invariant-calls", 60000) if (repo / ".candidate-gas").exists() else 60000
        snapshot += f"InvariantTest:invariant_callSummary() (runs: 2000, calls: {calls}, reverts: 0)\n"
    if (repo / ".include-fuzz").exists():
        mean = read_int(".candidate-fuzz-mean", 120)
        runs = read_int(".candidate-fuzz-runs", 1000)
        snapshot += f"CTest:testFuzz_stat(uint256) (runs: {runs}, μ: {mean}, ~: 115)\n"
    output.write_text(snapshot)
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
    ast_id = read_int(".layout-ast-id", 1)
    type_ast_id = read_int(".layout-type-ast-id", 1234)
    type_name = f"t_contract(Token){type_ast_id}"
    print(json.dumps({"storage": [{"astId": ast_id, "contract": args[1], "label": "value", "offset": 0, "slot": str(slot), "type": type_name}], "types": {type_name: {"encoding": "inplace", "label": "contract Token", "numberOfBytes": "20"}}}))
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
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
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
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 30)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["failed_gate"], 3)
        self.assertIn("gas regression", result["reason"])

    def test_accepts_unchanged_invariant_snapshot_rows(self) -> None:
        (self.repo / ".include-invariant").write_text("1")
        subprocess.run(["git", "add", ".include-invariant"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable invariant snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        comparison = json.loads((self.run_dir / "gas-comparison.json").read_text())
        self.assertEqual(
            comparison["invariants"],
            [
                {
                    "calls": 60000,
                    "measurement": "InvariantTest:invariant_callSummary()",
                    "reverts": 0,
                    "runs": 2000,
                    "status": "identical",
                }
            ],
        )

    def test_rejects_changed_invariant_snapshot_rows(self) -> None:
        (self.repo / ".include-invariant").write_text("1")
        subprocess.run(["git", "add", ".include-invariant"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable invariant snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".candidate-invariant-calls").write_text("59999")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 30)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["failed_gate"], 3)
        self.assertIn("invariant snapshot changed", result["reason"])

    def test_accepts_fuzz_statistic_snapshot_rows(self) -> None:
        (self.repo / ".include-fuzz").write_text("1")
        subprocess.run(["git", "add", ".include-fuzz"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable fuzz snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        comparison = json.loads((self.run_dir / "gas-comparison.json").read_text())
        self.assertEqual(comparison["fuzz_statistics"][0]["runs"], 1000)
        self.assertEqual(comparison["fuzz_statistics"][0]["status"], "informational_not_comparable")

    def test_records_changed_fuzz_statistics_without_calling_them_a_regression(self) -> None:
        (self.repo / ".include-fuzz").write_text("1")
        subprocess.run(["git", "add", ".include-fuzz"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable fuzz snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".candidate-fuzz-mean").write_text("121")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        comparison = json.loads((self.run_dir / "gas-comparison.json").read_text())
        self.assertEqual(comparison["fuzz_statistics"][0]["mean_delta"], 1)

    def test_rejects_changed_fuzz_run_count(self) -> None:
        (self.repo / ".include-fuzz").write_text("1")
        subprocess.run(["git", "add", ".include-fuzz"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable fuzz snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".candidate-fuzz-runs").write_text("999")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 30)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertIn("fuzz snapshot run count changed", result["reason"])

    def test_rejects_full_suite_failure_at_gate_four(self) -> None:
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".fail-full-test").write_text("1")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 40)
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 4)

    def test_hard_aborts_on_protected_layout_change(self) -> None:
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".layout-slot").write_text("1")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 50)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["failed_gate"], 5)
        self.assertIn("storage layout changed", result["reason"])

    def test_accepts_compiler_ast_id_only_layout_difference(self) -> None:
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".layout-ast-id").write_text("99")
        (self.repo / ".layout-type-ast-id").write_text("5678")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["storage_layouts"][0]["status"], "identical")
        before_raw = self.run_dir / "storage-layout" / "C.before.raw.json"
        after_raw = self.run_dir / "storage-layout" / "C.after.raw.json"
        self.assertNotEqual(before_raw.read_bytes(), after_raw.read_bytes())

    def test_records_declared_layout_change_on_non_frozen_contract(self) -> None:
        self.baseline(protected=False)
        self.prepare_candidate()
        (self.repo / ".layout-slot").write_text("1")
        code = self.verify(
            "--no-sensitive-unchecked",
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
                "--no-sensitive-unchecked",
                "--non-sensitive-rationale",
                "This arithmetic cannot affect persistent state, asset balances, or external call parameters.",
            ),
            20,
        )
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 2)

    def test_requires_and_runs_targeted_sensitive_property_test(self) -> None:
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        code = self.verify(
            "--sensitive-unchecked",
            "--targeted-match-path",
            "test/C.t.sol",
            "--targeted-match-test",
            "testFuzz_stateDifferential",
            "--property-proof",
            "Compare checked and unchecked state transitions across the complete bounded input domain.",
            optimisation_class="unchecked-arithmetic",
        )
        self.assertEqual(code, 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertTrue(result["sensitive_unchecked"]["applicable"])
        self.assertEqual(result["sensitive_unchecked"]["status"], "passed")

    def test_targeted_sensitive_property_failure_rejects_gate_six(self) -> None:
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        (self.repo / ".fail-targeted").write_text("1")
        code = self.verify(
            "--sensitive-unchecked",
            "--targeted-match-path",
            "test/C.t.sol",
            "--targeted-match-test",
            "testFuzz_stateDifferential",
            "--property-proof",
            "Compare checked and unchecked state transitions across the complete bounded input domain.",
            optimisation_class="unchecked-arithmetic",
        )
        self.assertEqual(code, 60)
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 6)


class CorpusValidationTests(unittest.TestCase):
    """The corpus is what judges a candidate, so a corpus that cannot be
    trusted has to refuse rather than pass a candidate under advice nobody
    checked. Each case here mutates one field of the shipped corpus in a
    temporary directory; nothing writes into the skill's own references."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="hermes-corpus-")
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.shipped, self.schema_path = hermes.corpus_paths()
        shutil.copy(self.shipped, self.directory / self.shipped.name)
        shutil.copy(self.schema_path, self.directory / self.schema_path.name)

    def load(self) -> tuple[dict, dict]:
        corpus, schema, _ = hermes.load_corpus(self.directory)
        return corpus, schema

    def faults(self, mutate) -> list[str]:
        corpus, schema = self.load()
        mutate(corpus, schema)
        return hermes.validate_corpus(corpus, schema)

    def test_the_shipped_corpus_validates(self) -> None:
        corpus, schema = self.load()
        self.assertEqual(hermes.validate_corpus(corpus, schema), [])

    def test_the_shipped_corpus_carries_the_source_counts(self) -> None:
        corpus, _ = self.load()
        self.assertEqual(len(corpus["myths"]), 28)
        self.assertEqual(len(corpus["references"]), 40)
        self.assertEqual(corpus["source"]["sha256"],
                         "297c926dc0a2e011e31da5245273c136273b8faa390f3691910c22c870068449")

    def test_every_citation_id_resolves_exactly_once(self) -> None:
        """REF-25 appears in the source at the start of a line as a citation
        and again as a footnote definition, which is the shape that turns one
        reference into two during transcription."""
        corpus, _ = self.load()
        identifiers = [entry["id"] for entry in corpus["references"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(identifiers.count("REF-25"), 1)

    def test_a_duplicate_record_id_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"].append(dict(corpus["myths"][0]))
        self.assertIn("duplicate id", " ".join(self.faults(mutate)))

    def test_an_unknown_field_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"][0]["severity"] = "high"
        self.assertIn("unknown field 'severity'", " ".join(self.faults(mutate)))

    def test_a_missing_field_is_refused(self) -> None:
        def mutate(corpus, _schema):
            del corpus["myths"][0]["correction"]
        self.assertIn("missing field 'correction'", " ".join(self.faults(mutate)))

    def test_an_empty_correction_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"][0]["correction"] = "   "
        self.assertIn("expected non-empty text", " ".join(self.faults(mutate)))

    def test_a_citation_that_no_reference_defines_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"][0]["references"] = ["REF-99"]
        self.assertIn("cites 'REF-99'", " ".join(self.faults(mutate)))

    def test_a_malformed_source_digest_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["source"]["sha256"] = "297C926D"
        self.assertIn("expected a lowercase sha256 digest", " ".join(self.faults(mutate)))

    def test_a_wrong_schema_declaration_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["schema"] = "hermes/gas-rule-corpus/v2"
        faults = self.faults(mutate)
        self.assertEqual(len(faults), 1, faults)
        self.assertIn("expected 'hermes/gas-rule-corpus/v1'", faults[0])

    def test_an_id_outside_its_pattern_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"][0]["id"] = "MYTH-1"
        self.assertIn("does not match", " ".join(self.faults(mutate)))

    def test_a_type_token_this_build_cannot_check_is_a_fault(self) -> None:
        """A schema that grew a token the validator does not implement must
        fail loudly. The alternative is a field nobody checks and no sign of
        it."""
        def mutate(_corpus, schema):
            schema["records"]["myths"]["required"]["claim"] = "sonnet"
        self.assertIn("cannot check", " ".join(self.faults(mutate)))

    def test_a_rule_class_outside_the_twelve_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["rules"].append(_rule_record(hermes_class="storage-golf"))
        self.assertIn("neither null nor a Hermes class", " ".join(self.faults(mutate)))

    def test_a_rule_scope_naming_an_unknown_fork_is_refused(self) -> None:
        def mutate(corpus, _schema):
            record = _rule_record()
            record["scope"]["evm_floor"] = "verkle"
            corpus["rules"].append(record)
        self.assertIn("is not a name in fork_order", " ".join(self.faults(mutate)))

    def test_a_fully_formed_rule_record_validates(self) -> None:
        """The rule shape steps three and four fill in, proved against the
        schema before any of those records exist."""
        def mutate(corpus, _schema):
            corpus["rules"].append(_rule_record())
        self.assertEqual(self.faults(mutate), [])

    def test_a_schema_class_the_header_does_not_name_is_still_a_record_class(self) -> None:
        """Round 1 finding: the header check named the three record classes
        itself, so a schema that grew a fourth reported it as an unknown
        top-level field instead of validating it."""
        def mutate(corpus, schema):
            schema["records"]["gates"] = {
                "id_pattern": "^GATE-[0-9]{2}$",
                "required": {"id": "id", "title": "text"},
                "optional": {},
            }
            corpus["gates"] = [{"id": "GATE-01", "title": "pin the build"}]
        self.assertEqual(self.faults(mutate), [])

    def test_the_command_reports_clean_and_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "hermes.py"), "corpus", "--validate", "--json"],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["status"], "clean")
        self.assertEqual(summary["counts"]["myths"], 28)
        self.assertEqual(summary["counts"]["references"], 40)
        self.assertEqual(summary["faults"], [])

    def test_the_command_refuses_without_validate(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "hermes.py"), "corpus"],
            capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--validate", result.stderr)


def _rule_record(**overrides) -> dict:
    """A minimal rule record in the shape the schema declares."""
    record = {
        "id": "STO-09",
        "title": "cache repeated storage reads",
        "kind": "technique",
        "category": "state-model-and-storage",
        "priority": "P1",
        "evidence_grade": "A",
        "automation": "safe",
        "hermes_class": "storage-load-caching",
        "summary": "Copy a storage value to a stack local when it is read repeatedly.",
        "mechanism": "Even a warm SLOAD costs more than a stack operation.",
        "recommendation": "Load once after the last preceding mutation.",
        "detector_signals": ["same storage expression read more than once"],
        "preconditions": ["no internal write invalidates the cached value"],
        "proof_obligations": ["every use observes the same version of the value"],
        "failure_modes": ["stale state after a callback"],
        "validation": ["success and failure gas snapshots"],
        "references": ["REF-10"],
        "source_section": "5",
        "verified_on": {"compiler": "0.8.25", "evm": "cancun"},
        "scope": {
            "compiler_min": "0.8.0",
            "compiler_max_exclusive": "0.9.0",
            "compiler_reason": "SLOAD pricing is an EVM property, not a compiler one.",
            "evm_floor": "berlin",
            "evm_reason": "EIP-2929 introduced the warm and cold distinction the saving rests on.",
            "pipelines": ["legacy", "via-ir"],
            "pipeline_reason": "Neither pipeline removes a repeated storage read.",
        },
    }
    record.update(overrides)
    return record

if __name__ == "__main__":
    unittest.main(verbosity=2)
