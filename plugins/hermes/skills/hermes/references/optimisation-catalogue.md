# Optimisation catalogue

<!-- marketplace-context:start -->
> **Marketplace context: Hermes.** Hermes measures one Solidity gas optimisation class at a time and rejects the candidate when its Foundry evidence does not clear every gate. Use Pandects for credit-specific laws, or Hexaemeron's audit skills for a broader security review. **Current frontier:** No complete, reproducible live Wildcat evidence bundle is published.
<!-- marketplace-context:end -->

Nominate one Gate 2 class, predict its effect, then measure it. A plausible compiler story is not a result.

| Hermes class | Candidate idea | Usual risk | Checks before trying it |
| --- | --- | --- | --- |
| `storage-load-caching` | Hoist repeated `SLOAD`s into locals and reuse already-read struct fields | Low | Check that no call or state write between reads can change the value |
| `calldata-memory` | Change read-only external parameters from `memory` to `calldata`; avoid needless copies | Low | Confirm the public signature and selector stay unchanged |
| `custom-errors` | Replace revert strings with custom errors | Low | Find tests and callers that inspect revert data; record bytecode and runtime effects |
| `loop-arithmetic` | Cache `.length`, remove repeated indexing work, or use a proven-safe unchecked increment | Low-medium | Find real loops first; prove the increment bound and keep state-sensitive arithmetic rules in force |
| `constants-immutables` | Move values from storage to `constant` or `immutable` | Medium | Expect a layout change; frozen contracts cannot take this class |
| `external-call-reduction` | Collapse duplicate calls or cache stable return data | Medium | Prove the target is unchanged across intervening calls, callbacks, and state writes |
| `event-packing` | Reduce event data or indexed arguments | Medium | Confirm indexers and off-chain consumers can take the event change |
| `storage-packing` | Narrow or reorder fields to share slots | High | Use only outside the frozen set; declare and record the layout difference |
| `unchecked-arithmetic` | Remove checked arithmetic where bounds prove wraparound impossible | High | Treat persistent state, asset accounting, permissions, external-call parameters, time and rounding as sensitive; run Gate 6 |
| `control-flow` | Reorder branches, remove duplicate predicates, or change `public` to `external` | Medium | Inspect selectors and measure every affected dispatch path; one function may get cheaper while another gets dearer |
| `hashing-encoding` | Remove duplicate encoding or hashing work and prefer fixed-width operations where semantics match | Medium | Compare exact bytes, collision assumptions, and downstream signature/domain use |
| `assembly` | Replace Solidity with a small assembly section | High | Keep this class separate from unchecked arithmetic; prove memory safety, returndata handling, and revert behaviour |

## Quick source searches

Search from the Foundry root, adapting names to the repository:

```bash
rg -n 'for\s*\(|while\s*\(' src
rg -n 'delegatecall|Clone|proxy|Proxy|hook|Hook|RoleProvider|factory|Factory' src
rg -n '\bunchecked\b|\bassembly\b' src test
rg -n 'memory' src
rg -n 'require\([^,]+,\s*"|revert\("' src
```

Source search cannot distinguish an `SLOAD` from a cached local. Trace repeated reads and mark each intervening external call or write before hoisting.

## Pick in this order

Start with repeated storage reads, calldata copies and custom errors. Then try loop mechanics or duplicate external calls. Leave storage packing, unchecked arithmetic and assembly until the saving merits their proof cost.

Check stateless libraries early. They cannot break inherited storage layout, but their callers, arithmetic, ABI and tests still face every gate.

## Keep compiler settings separate

Treat a Solidity version, `optimizer_runs`, `via_ir` or EVM-version change as a separate experiment from a clean baseline. It reprices too much code to share attribution with a source-level class. Run the gas diff, full tests, layout and method checks; record deployed bytecode size with `forge build --sizes`.

## Noise and target selection

Pin the fuzz seed for comparable runs, then use the unpinned Gate 4 run to catch seed overfitting. Small deterministic unit-test deltas can be real. Remeasure `test/Fuzz.t.sol` or named-invariant deltas that move across seeds.

Declare target expressions before measurement. Inspect an unexpected saving before acceptance. Hermes rejects every regression, including rows outside the target set.
