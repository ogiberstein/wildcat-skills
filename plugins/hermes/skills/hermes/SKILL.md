---
name: hermes
description: Optimise Solidity gas usage with an executable, fail-closed Foundry loop that measures savings, re-runs behaviour tests, checks storage layouts and method identifiers, and demands targeted differential or property evidence for state-sensitive unchecked arithmetic. Use for Solidity gas work, Forge snapshot reductions, gas-report reviews, storage packing, unchecked arithmetic, or any proposed EVM gas-saving change.
metadata:
  version: "0.1.0"
---

# Hermes gas optimiser

## Frontier

Hermes owns the gas-optimisation evidence frontier, not Hexaemeron's delivery or Solidity frontier. [EVOLUTION.md](EVOLUTION.md) holds its version, target, next job and maturity. Do not recommend or run another frontier pass once the ledger is mature.

<!-- marketplace-context:start -->
## Where this sits

Hermes measures one Solidity gas optimisation class at a time and rejects the candidate unless its Foundry evidence clears every gate.

**Use another tool when.** Use Pandects for credit-specific laws or Hexaemeron's audit skills for a broader security review.

**Current frontier.** No complete, reproducible live Wildcat evidence bundle is published.
<!-- marketplace-context:end -->

Use `scripts/hermes.py` for every run. It orders the gates, seals the baseline, writes the evidence and exits non-zero at the first failure. Pick one candidate class from [references/optimisation-catalogue.md](references/optimisation-catalogue.md).

## Before touching source

1. Work from the Foundry root. If `foundry.toml` is under `build/`, pass `build/` as `--repo`.
2. Read the repository instructions and satisfy its issue or branch rules before writing.
3. Start from a clean Git tree; finish unrelated work first.
4. Pin one fuzz seed. Keep fork-test exclusions identical through Gates 1 to 4.
5. Re-derive the layout set by searching for proxies, `delegatecall`, clones, factories, hooks, role providers and contracts they call. Treat doubt as frozen layout.
6. Name gas measurements before editing. Each `--gas-target` is a regular expression and must contain a measured saving.

Set `HERMES_PY` to this skill's `scripts/hermes.py`. Keep the Gate 1 run directory for every later command.

## Gate 1: seal a green baseline

List every hook, role provider, proxied implementation, facet, factory-sensitive contract and other frozen layout with `--protected-contract`. Qualify collisions as `path:Contract`.

```bash
python3 "$HERMES_PY" baseline \
  --repo "<foundry-root>" \
  --fuzz-seed 0x5EED \
  --no-match-path "test/Fork.t.sol" \
  --protected-contract "Market=src/Market.sol:Market" \
  --protected-contract "Hooks=src/Hooks.sol:Hooks"
```

Repeat `--no-match-path` and `--protected-contract` as needed. Omit unnecessary exclusions.

### When no contract is frozen

If no frozen contract is in scope, say so explicitly:

```bash
python3 "$HERMES_PY" baseline \
  --repo "<foundry-root>" \
  --fuzz-seed 0x5EED \
  --assert-no-protected-contracts
```

Add `--layout-contract "Label=path:Contract"` when a non-frozen contract's layout still needs recording, such as for deliberate packing.

Gate 1 runs `forge snapshot` then `forge test`. It records the snapshot, green test result, Forge version, canonical Foundry config, Git revision, Solidity sources, storage layouts and method identifiers. A dirty tree, red suite, missing snapshot, failed inspect or invalid JSON ends the run.

## Gate 2: make one class of change

Choose one catalogue value and make only that source change. Do not mix cleanup, compiler settings, test edits or another gas idea into the candidate.

Read `candidate.solidity.diff` before attesting that every hunk belongs to the declared class. The harness rejects Solidity file additions or removals, test-source edits, an empty candidate, `unchecked` added outside `unchecked-arithmetic`, and assembly added outside `assembly`.

If the property test is absent, add it in a preparatory change, get green and take a fresh baseline. The candidate must use the existing fuzz suite, not change its oracle.

## Verify an ordinary candidate

Run Gates 3 to 6:

```bash
python3 "$HERMES_PY" verify \
  --run-dir "<run-dir>" \
  --optimisation-class storage-load-caching \
  --attest-single-class \
  --gas-target 'LedgerTest:test_update' \
  --gas-target 'LedgerTest:test_batch' \
  --no-sensitive-unchecked
```

## Explain non-sensitive unchecked arithmetic

For unchecked arithmetic outside state-sensitive code, add a concrete explanation:

```bash
  --no-sensitive-unchecked \
  --non-sensitive-rationale "The loop counter is bounded by the in-memory array length and cannot affect persistent state, asset balances, external call parameters, or rounding."
```

## Verify state-sensitive unchecked arithmetic

If unchecked arithmetic can affect persistent state, asset accounting, external calls, permissions or rounding, run the existing targeted differential or property test:

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

## Gate requirements

- Gate 3 runs `forge snapshot --diff <baseline>`, captures a candidate snapshot, then runs `forge test --gas-report`. Reject any positive deterministic delta, changed measurement set, unmatched target or target without a saving.
- Gate 3 records baseline and candidate means and medians for fuzz statistics whose sampled inputs can change with compiled bytecode, without calling them a regression or saving. Reject a changed fuzz-test set or run count; `invariant_callSummary()` must retain the same test set, run count, call count and revert count.
- Gate 4 runs the full `forge test` suite with the pinned seed, then a full unpinned run. Any failure rejects the candidate.
- Gate 5 re-runs `forge inspect <C> storageLayout --json --force` and `methodIdentifiers` for every recorded contract. Canonicalise solc's compilation-local AST IDs, retain raw output, abort on structural protected-layout or method-selector differences, and allow a declared layout change only for an unprotected contract under the rules below.
- Gate 6 runs the named targeted differential or property test with `--sensitive-unchecked` and records its oracle. Otherwise, record why the candidate neither introduces nor relies on state-sensitive unchecked arithmetic.

## Deliberate layout change outside the frozen set

Only `storage-packing` and `constants-immutables` may declare a change. The contract must be listed with `--layout-contract`, never `--protected-contract`.

```bash
  --allow-unprotected-layout-change \
  --layout-change-rationale "No proxy, hook, role provider, delegate call, deployed factory instance, storage-reading test, or indexer consumes this layout."
```

Hermes records the diff and rejects an undeclared difference, an absent declared difference or any difference on the frozen set.

## State-sensitive arithmetic property standard

Before accepting the Gate 6 result, inspect the named test and confirm all of the following:

- Exercise the changed unchecked operation, not a neighbouring helper.
- Compare against the original checked implementation or enforce an equivalent property oracle.
- Preserve checked overflow and underflow behaviour; a wrapped result cannot stand in for a reference revert.
- Cover applicable `0`, `1`, maxima, time deltas, input bounds, balance bounds, rounding boundaries and the exact safe and unsafe arithmetic edges.
- Avoid a `bound()` or assumption that removes the dangerous region.
- Keep the named path's fuzz or invariant configuration, such as `test/Fuzz.t.sol`, and record the baseline seed in the command.

A comment that arithmetic looks safe is context, not Gate 6 evidence.

## Accept, reject, repeat

Exit `0` with `result.json` status `accepted` signals acceptance. Rejected gates exit `10`, `20`, `30`, `40`, `50` or `60`. Keep `result.json`, command logs, gas comparison, source diff, layouts and method maps together in the run directory.

Stop after a rejection. Do not tweak tolerances, alter the target set after seeing the result, weaken a test or add another optimisation to hide the loss. Remove only the candidate, return to the last green state and restart at Gate 1.

After acceptance, promote the candidate snapshot deliberately:

```bash
python3 "$HERMES_PY" promote --run-dir "<run-dir>"
```

The accepted state becomes the next class's baseline. Never run two classes through one Hermes record.

## Refuse shortcuts

- If `forge` is unavailable, report that no gas result can be measured.
- If the baseline is red or dirty, fix that in separate work.
- If someone asks to skip the layout diff, keep the gate.
- If someone asks to bundle changes, run them in sequence.
- If the gas saving cannot be quantified, reject it.
- If a state-sensitive unchecked change lacks the targeted proof, reject it whatever the gas number says.
