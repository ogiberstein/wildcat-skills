---
name: hermes
description: Optimise Solidity gas usage with an executable, fail-closed Foundry loop that measures savings, re-runs behaviour tests, checks storage layouts and method identifiers, and demands targeted differential or property evidence for state-sensitive unchecked arithmetic. Use for Solidity gas work, Forge snapshot reductions, gas-report reviews, storage packing, unchecked arithmetic, or any proposed EVM gas-saving change.
---

# hermes gas optimiser

<!-- marketplace-context:start -->
## Where this sits

Hermes measures one Solidity gas optimisation class at a time and rejects the candidate when its Foundry evidence does not clear every gate.

**Use another tool when.** Use Pandects for credit-specific laws, or Hexaemeron's audit skills for a broader security review.

**Current frontier.** No complete, reproducible live Wildcat evidence bundle is published.
<!-- marketplace-context:end -->

The ideas are cheap. The evidence is the job.

Use `scripts/hermes.py` for every run. It owns the order, seals the baseline, writes the evidence, and exits non-zero at the first bad gate. Use [references/optimisation-catalogue.md](references/optimisation-catalogue.md) to pick a candidate class.

## Day to day

**Developers.** A gas change shaves a few hundred units off a hot path and nobody can say whether behaviour moved with it. Run Hermes on that one optimisation class and the review arrives with the snapshot diff, both fuzz passes, the storage layout comparison and a `result.json`, rather than a number and an assurance.

**Security and audit.** A gas change arrives from outside the team. Instead of reading it for intent, put it through Gate 5 to see whether any protected contract's storage layout or method identifiers moved, and Gate 6 for unchecked arithmetic that reaches persistent state.

## Before touching source

1. Work from the Foundry root. If the repository keeps `foundry.toml` under `build/`, pass `build/` as `--repo`.
2. Read the repository instructions and satisfy its issue or branch rules before writing.
3. Start from a clean Git tree. Finish unrelated work first.
4. Pin one fuzz seed for the run. Keep any fork-test exclusions identical through Gates 1 to 4.
5. Re-derive the layout set. Search for proxies, `delegatecall`, clones, factories, hooks, role providers, and contracts called by them. Treat doubt as frozen layout.
6. Name the intended gas measurements before editing. Each `--gas-target` is a regular expression and must contain a measured saving.

Set `HERMES_PY` to this skill's `scripts/hermes.py` path. Keep the run directory printed by Gate 1; every later command uses it.

## Gate 1: seal a green baseline

List every hook, role provider, proxied implementation, facet, factory-sensitive contract, and other frozen layout with `--protected-contract`. Use a qualified `path:Contract` identifier when names collide.

```bash
python3 "$HERMES_PY" baseline \
  --repo "<foundry-root>" \
  --fuzz-seed 0x5EED \
  --no-match-path "test/Fork.t.sol" \
  --protected-contract "Market=src/Market.sol:Market" \
  --protected-contract "Hooks=src/Hooks.sol:Hooks"
```

Repeat `--no-match-path` and `--protected-contract` as needed. Omit exclusions that the repository does not need.

If no frozen contract is in scope, say so explicitly:

```bash
python3 "$HERMES_PY" baseline \
  --repo "<foundry-root>" \
  --fuzz-seed 0x5EED \
  --assert-no-protected-contracts
```

Add `--layout-contract "Label=path:Contract"` for a non-frozen contract whose layout still needs recording. This is useful for a deliberate packing change.

Gate 1 runs `forge snapshot` and then `forge test`, in that order. It records the snapshot, green test result, Forge version, canonical Foundry config, Git revision, Solidity sources, storage layouts, and method identifiers. A dirty tree, red suite, missing snapshot, failed inspect, or invalid JSON ends the run.

## Gate 2: make one class of change

Choose one value from the catalogue and make only that kind of source change. Do not mix cleanup, compiler settings, test edits, or a second gas idea into the candidate.

Review `candidate.solidity.diff` before attesting. The harness rejects Solidity file additions or removals, test-source edits, an empty candidate, added `unchecked` outside `unchecked-arithmetic`, and added assembly outside `assembly`. The attestation remains a judgement: read the diff and confirm that every hunk belongs to the declared class.

If the required property test is absent, add it in a preparatory change, get green, and take a fresh baseline. The optimisation candidate uses the existing fuzz suite rather than changing its own oracle.

## Gates 3 to 6: verify the candidate

For an ordinary candidate:

```bash
python3 "$HERMES_PY" verify \
  --run-dir "<run-dir>" \
  --optimisation-class storage-load-caching \
  --attest-single-class \
  --gas-target 'LedgerTest:test_update' \
  --gas-target 'LedgerTest:test_batch' \
  --no-sensitive-unchecked
```

For unchecked arithmetic outside state-sensitive code, add a real explanation:

```bash
  --no-sensitive-unchecked \
  --non-sensitive-rationale "The loop counter is bounded by the in-memory array length and cannot affect persistent state, asset balances, external call parameters, or rounding."
```

For unchecked arithmetic that can affect persistent state, asset accounting, external calls, permissions, or rounding, run the existing targeted differential or property test:

```bash
python3 "$HERMES_PY" verify \
  --run-dir "<run-dir>" \
  --optimisation-class unchecked-arithmetic \
  --attest-single-class \
  --gas-target 'LedgerTest:test_update' \
  --sensitive-unchecked \
  --targeted-match-path 'test/StateDifferential.t.sol' \
  --targeted-match-test 'testFuzz_diff_stateTransition' \
  --property-proof "Compare the checked reference and candidate across the complete reachable input domain; assert equal state transitions and equal overflow reverts at the arithmetic boundaries."
```

### Gate 3: quantify the gas change

Run `forge snapshot --diff <baseline>` and capture a candidate snapshot. Reject a positive deterministic delta anywhere, a changed measurement set, a target with no match, or a target with no saving. Then run `forge test --gas-report`.

Historical Foundry snapshots also contain fuzz statistics whose sampled inputs can change when the compiled bytecode changes. Hermes records their baseline and candidate means and medians, but does not call those aggregates a gas regression or saving. It still rejects a changed fuzz-test set or run count. Foundry `invariant_callSummary()` rows are stricter: their test set, run count, call count, and revert count must stay identical.

### Gate 4: prove behaviour is unchanged

Run the full `forge test` suite with the pinned seed, followed by a full unpinned run. Any failure rejects the candidate.

### Gate 5: preserve layouts and selectors

Re-run `forge inspect <C> storageLayout --json --force` and `methodIdentifiers` for every recorded contract. The layout comparison canonicalises solc's compilation-local AST IDs, while retaining raw inspector output in evidence; it hard-aborts on any structural protected-layout difference or method-selector difference. A declared layout change is allowed only for an unprotected contract under the rules below.

### Gate 6: prove state-sensitive unchecked arithmetic

When `--sensitive-unchecked` applies, run the named targeted differential or property test and record its oracle. Otherwise, record why the candidate does not introduce or rely on state-sensitive unchecked arithmetic.

## Deliberate layout change outside the frozen set

Only `storage-packing` and `constants-immutables` may declare one. The contract must have been listed with `--layout-contract`, never `--protected-contract`.

```bash
  --allow-unprotected-layout-change \
  --layout-change-rationale "No proxy, hook, role provider, delegate call, deployed factory instance, storage-reading test, or indexer consumes this layout."
```

Hermes records the diff. It rejects an undeclared difference, a declared difference that never occurred, or any difference on the frozen set.

## State-sensitive arithmetic property standard

Before accepting the Gate 6 result, inspect the named test and confirm all of the following:

- Exercise the changed unchecked operation rather than a neighbouring helper.
- Compare against the original checked implementation or enforce an equivalent property oracle.
- Preserve checked overflow and underflow behaviour; a wrapped result cannot stand in for a reference revert.
- Cover applicable `0`, `1`, maxima, time deltas, input bounds, balance bounds, rounding boundaries, plus the exact safe and unsafe arithmetic edges.
- Avoid a `bound()` or assumption that removes the dangerous region.
- Keep the existing fuzz or invariant configuration from the named test path, such as `test/Fuzz.t.sol`, with the baseline seed recorded in the command.

A comment explaining why arithmetic looks safe is useful review context. It is not Gate 6 evidence.

## Accept, reject, repeat

Exit `0` plus `result.json` status `accepted` is the acceptance signal. Exit codes identify the rejected gate: `10`, `20`, `30`, `40`, `50`, or `60`. `result.json`, the command logs, gas comparison, source diff, layouts, and method maps stay together in the run directory.

Stop after any rejection. Do not tweak tolerances, alter the target set after seeing the result, weaken a test, or add another optimisation to cover the loss. Remove only the candidate changes, return to the last green state, and begin again at Gate 1.

After acceptance, promote the candidate snapshot deliberately:

```bash
python3 "$HERMES_PY" promote --run-dir "<run-dir>"
```

That accepted state becomes the baseline for the next class. Never run two classes through one Hermes record.

## Refuse shortcuts

- If `forge` is unavailable, report that no gas result can be measured.
- If the baseline is red or dirty, fix that in separate work.
- If someone asks to skip the layout diff, keep the gate.
- If someone asks to bundle changes, run them in sequence.
- If the gas saving cannot be quantified, reject it.
- If a state-sensitive unchecked change lacks the targeted proof, reject it whatever the gas number says.
