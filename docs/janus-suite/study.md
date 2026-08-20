# Study: Build the Janus hook-conformance suite against the Wildcat v2.5 hooks

**Run branch:** `claude/janus-wildcat-skill-bejdy0`, cut from `main` at
`1fc9f6a7a649fd0d1c495d639d6b971e1055a050`. That SHA is the run's real start.

**Anchor commit:** `wildcat-finance/v2-protocol` branch
`feat/v2.5-events-data-model`, HEAD
`9716e78e345a84fa1491c794aa5ae162790ce378`, the likely head of the V2.5
release. All hook mechanics cited below are read from that tree.

Assuming, unless corrected:

1. "Build the Janus skill" means shipping a real, installable Janus plugin
   whose Foundry harness runs and enforces the seven gates, not another
   specification document. The delivered `docs/commons/janus.md` is the
   anchor and is deleted at the end of the run, as instructed.
2. Janus does not compile the live v2-protocol. That tree's `lib/`
   submodules are unpopulated in a shallow clone and its own `forge build`
   fails without eight submodule fetches. Janus instead models the v2.5
   market-to-hook seam faithfully in-tree and cites the exact source
   `file:line` for every modeled behaviour. This is also the correct design:
   a suite that needs the whole host to compile cannot serve "any host", which
   is the stated public goal.
3. Foundry and solc are available. This environment blocks the usual
   installer domains, so `forge` 1.5.1 and `solc` 0.8.25 were fetched from
   GitHub release assets; both work. CI uses `foundry-rs/foundry-toolchain`,
   which fetches solc normally.
4. Janus ships with no external Solidity dependency, matching Pandects:
   `libs = []`, no `forge-std`. It declares the minimal `Vm` cheatcode
   interface it needs (`record`, `accesses`, `getRecordedLogs`,
   `snapshotState`, `revertToState`, `readFile`, `writeFile`, `parseJson`)
   in-tree.
5. Python 3.9+ and stdlib only for the manifest validator and the reporter,
   matching the repository's other Python tools and its 3.9/3.13 CI matrix.
6. Janus becomes the repository's thirteenth plugin. The first janus run
   deliberately kept it a spec because it was unbuilt; building it is exactly
   the condition under which it earns an install surface.
7. This runtime has no `gh`; pull requests and merges use the GitHub MCP
   tools. The `origin:ai` label exists and HTML comments are stripped from PR
   bodies, so the `wildcat-origin: shoggoth` marker is stated as a visible
   line.

## 1. Problem statement

Wildcat's v2.5 markets call a configured hooks contract around eleven market
actions. The interface (`src/access/IHooks.sol`) says which functions exist. It does not say what a hook may observe, what it may change, what it must
never touch, or that a user can still exit after a credential lapses or a
provider is removed. That policy is spread across implementation code, comments, and
the assumptions of whoever wrote the first template. A new hook can satisfy
the ABI and still redirect value, grief gas, re-enter, or strand a lender.

Janus is a conformance suite that states, in a machine-readable manifest,
what a hook may observe and change before and after a host action, and a
harness that drives ordinary and hostile sequences, records the real
state delta at each threshold, and fails when the delta exceeds the manifest.
The first host adapter is Wildcat's v2.5 seam; the format is host-neutral so
another host can declare its own boundary without either host claiming the
other's guarantees.

A working prototype here means: the Janus plugin installs like the other
twelve, its harness runs offline, an honest Wildcat-shaped hook passes every
applicable gate, and each of five hostile reference hooks is caught by the
gate that owns its failure. The demo path proves it:

```text
# in plugins/janus/harness
forge build
forge test -vv
# from repo root
python3 plugins/janus/scripts/janus.py validate plugins/janus/harness/manifests/*.json
python3 plugins/janus/scripts/janus.py report --findings plugins/janus/examples/findings.sample.json \
  --md /tmp/janus.md --sarif /tmp/janus.sarif
python3 -m unittest discover -s plugins/janus/tests -t plugins/janus
python3 -m unittest discover -s tests
```

## 2. Prior art

In v2-protocol at the anchor commit:

- `src/access/IHooks.sol`: eleven action callbacks, `onDeposit`,
  `onQueueWithdrawal`, `onExecuteWithdrawal`, `onTransfer`, `onBorrow`,
  `onRepay`, `onCloseMarket`, `onNukeFromOrbit`, `onSetMaxTotalSupply`,
  `onSetAnnualInterestAndReserveRatioBips`, `onSetProtocolFeeBips`, plus
  `onCreateMarket`, `version()`, `config()`.
- `src/types/HooksConfig.sol`: the hand-built calldata for each hook.
  `_callHook` (lines 88-106) forwards all remaining gas with `call(gas(),
  target, 0, ...)`, sends zero value, discards success return data, and
  re-reverts the hook's exact revert bytes. `onSetAnnualInterestAndReserve
  RatioBips` (741-808) is the one value-returning hook: it requires
  `returndatasize() >= 0x40`, masks each returned word to `uint16`, and the
  market applies them within bounds (`WildcatMarketConfig.sol:131-168`).
- `src/access/OpenTermHooks.sol`, `FixedTermHooks.sol`,
  `PeriodicTermHooks.sol`, `BaseAccessControls.sol`,
  `MarketConstraintHooks.sol`: the maintained templates. Storage written
  during hooks is in the hooks contract, keyed by lender or market
  (`_lenderStatus`, `isKnownLenderOnMarket`, `_hookedMarkets`,
  `temporaryExcessReserveRatio`). The known-lender bit is monotone: set on a
  credentialled deposit or a received transfer, never cleared. It is the exit
  key, because `onExecuteWithdrawal` is never enabled by any template.
- The exit path: `onQueueWithdrawal` gates on known-lender-or-credential;
  `onExecuteWithdrawal` is an empty body in every template. So once a
  withdrawal is queued, execution is not hook-gated.
- Re-entry: every market entry point is `nonReentrant` on a single global
  transient flag (`src/ReentrancyGuard.sol`), and market views are
  `nonReentrantView`. A hook cannot re-enter the market. It can re-enter the
  hooks contract and call other contracts through role-provider calls
  (`BaseAccessControls._tryValidateCredential`, an all-gas `call` to a
  caller-influenced provider address).
- Value: no market function is `payable`; no ETH, token, or approval ever
  flows to a hook; the hook is never granted a market role. The hook's only
  powers are veto and the returned APR/reserve pair.
- The v2.5 ABI cut: `onExecuteWithdrawal` now takes the exact batch `expiry`
  (`docs/v2.5-audit-delta.md`, `docs/hooks/How Hooks Work.md:20`). A separate
  one-method interface `IPeriodicTermAprReductionHooks`
  (`WildcatMarketConfig.sol:7-11`) is called from the permissionless
  `executePendingAnnualInterestBipsReduction`, gated by config bit 84.
- Existing tests: `test/shared/mocks/MockHooks.sol` records `keccak256(msg.
  data)` and emits per-hook events; `RevertingHooks.sol` toggles a revert.
  There is no reentrant hook, no gas-grief hook, no authority-escalation
  hook, and no hostile hook inside a stateful fuzz loop. That absence is Janus's
  reason to exist beyond the host's own suite.

In this repository:

- `plugins/pandects/`: the model for a Solidity plugin here, `foundry.toml`
  with `libs = []`, tests that import only its own contracts, and a
  `.github/workflows/pandects.yml` with a Python job and a Foundry job.
- `docs/commons/janus.md`: the anchor spec, deleted at run end.
- `tests/test_marketplace_prose.py`, `test_portable_skills.py`,
  `test_version_propagation.py`, `test_evolution_contract.py`,
  `test_shipped_prose_lints.py`: the packaging contracts a new plugin must
  satisfy. Notably `PLUGINS` is a hardcoded 12-tuple and
  `test_plugin_landing_readmes...` asserts `len(landings) == 12`; both bump to
  13.

Outside: [ERC-7579](https://eips.ethereum.org/EIPS/eip-7579), the second hook
architecture named by the spec, deferred and explicitly not sharing claims
with Wildcat's hooks. SARIF 2.1.0 for the machine-readable report.

## 3. Constraints and non-goals

Constraints: run base `1fc9f6a` on `main`; anchor `9716e78` on v2-protocol;
Foundry with `solc = 0.8.25`, `evm_version = cancun`; `libs = []`; Python
stdlib only; every shipped document lint-clean; the harness and Python tests
green in a new CI workflow mirroring Pandects; the repository's twelve
packaging tests updated to thirteen and kept green.

Non-goals, deferred past this prototype and recorded in Janus's `EVOLUTION.md`
as the held frontier: a second host adapter (the spec says one ships "only
after the generic boundary survives the Wildcat implementation"); an
ERC-7579 adapter; binding the harness to a live-compiled v2-protocol;
`Pandects`-driven economic properties across hook transitions and `Fizz`
sequence generation (named as future integration, not built now); an Ariadne
release statement for a manifest revision.

## 4. Design options

The topic is one capability, a conformance harness, so it is one module and
goes straight to a study; the runbook slices it into stepped pull requests.
The design choice is how the harness reaches the host.

1. **Compile and drive the live v2-protocol.** Highest fidelity: tests run
   against the real market and templates. Trades away the stated public goal
   and this environment's reach. It couples Janus to one host's full build,
   needs eight submodule fetches that fail offline, and makes "any host can
   declare its boundary" false. Rejected.
2. **Model the v2.5 seam in-tree behind a host-adapter interface, manifest in
   JSON, recorder and harness in Solidity, reporter in Python.** The harness
   drives a faithful minimal market that calls hooks exactly as
   `HooksConfig.sol` does, all-gas `call`, zero value, bubbled revert, the
   value-returning APR hook with its `>= 0x40` return contract, the appended
   `extraData` tail, the global `nonReentrant` guard, the monotone
   known-lender exit bit. Every modeled behaviour cites its source line, and a
   fidelity test pins the call primitive against the documented convention.
   Trades away catching a drift between the model and the real contracts;
   mitigated by the citations and the fidelity test, and honestly recorded.
   Chosen: it is the cheapest construction to comprehend that still meets the
   problem statement and the host-neutral goal, and it runs offline like every
   other plugin here.
3. **Pure Python simulation of the seam.** No Foundry, no real EVM. Rejected:
   the spec names a "stateful Foundry harness", gas grief and re-entry are EVM
   behaviours a Python model would fake, and the recorder needs real
   cheatcodes (`vm.record`, `vm.accesses`) to observe storage writes.
4. **Manifest as Solidity structs rather than JSON.** Rejected: the spec names
   a "hook-manifest schema" and a machine-readable report; JSON Schema gives a
   host-neutral, validator-checkable format the reporter can also consume, and
   Foundry reads it through `vm.parseJson`.

## 5. Risk register seed

What the audit loop should look hardest at. The worst outcome of a
conformance tool is a false pass: a hook that violates the boundary while
Janus reports conformant.

- **Recorder blind spots.** If the state-delta recorder misses a storage
  write, an external call, or a value movement, a hostile hook passes. The
  recorder is what every gate trusts, so its own tests must prove it catches
  each effect class, and each hostile hook must be caught by the specific gate that owns
  its failure, not incidentally by another.
- **Model infidelity.** If the modeled seam diverges from the real v2.5 call
  convention, a gate proven here need not hold on Wildcat. The fidelity test
  pins the call primitive (gas, value, revert bubbling, return-data contract,
  extraData tail) against the cited source.
- **Manifest under-specification.** A manifest that permits "any storage
  write" makes gate 1 vacuous. The schema must force enumeration; an omitted
  slot, target, or movement is forbidden, not implicitly allowed (gate 1).
- **Liveness overclaim.** A bounded exit test does not prove an exit always
  completes. The report must state exit liveness as "held over the tested
  scenarios", never as a proof (open question 4 in the spec).
- **FFI and filesystem.** The harness reads manifests and writes findings
  through cheatcodes. `fs_permissions` must be scoped to the plugin's own
  directories; no `vm.ffi`, no network, no absolute paths.
- **Packaging regressions.** Adding a thirteenth plugin touches the
  marketplace manifests, the README's five tables, the portable layer, and
  four packaging tests. A missed surface fails CI; the audit look covers every
  surface the tests enumerate.

## 6. Glossary seeds

- Host action: a market operation a hook runs around, such as deposit or
  queueWithdrawal.
- Threshold: the before-and-after boundary of one host action, where the hook
  runs and where Janus snapshots state.
- Hook manifest: the JSON declaration of what a hook may observe and change at
  each threshold, plus its rollback rule, gas budget, and exit liveness
  conditions.
- Host adapter: the piece that exposes one host's actions, state readers, and
  economic roles to the harness, and that limits every result to that host.
- State delta: the recorded difference across a threshold, storage writes,
  external call targets, value movements, gas consumed.
- Gate: one of the seven conformance properties the harness checks.
- Hostile reference hook: a deliberately non-conformant hook that exercises
  one failure class so the matching gate is proven to catch it.
- Known-lender bit: Wildcat's monotone per-market flag that keeps the
  withdrawal exit open after a credential lapses.

## 7. Sources

- v2-protocol `feat/v2.5-events-data-model` @ `9716e78`:
  `src/access/IHooks.sol`, `src/types/HooksConfig.sol`,
  `src/access/{OpenTermHooks,FixedTermHooks,PeriodicTermHooks,BaseAccessControls,MarketConstraintHooks}.sol`,
  `src/market/{WildcatMarket,WildcatMarketWithdrawals,WildcatMarketConfig,WildcatMarketToken,WildcatMarketBase}.sol`,
  `src/{HooksFactory,HooksFactoryRevolving}.sol`, `src/ReentrancyGuard.sol`,
  `docs/hooks/*`, `docs/v2.5 Event Model.md`, `docs/v2.5-audit-delta.md`,
  `test/shared/mocks/{MockHooks,RevertingHooks,MockHookCaller}.sol`,
  `foundry.toml`.
- This repo: `plugins/pandects/foundry.toml`,
  `.github/workflows/pandects.yml`, `plugins/hexaemeron/skills/VERSIONING.md`,
  `tests/test_*.py`, `docs/commons/janus.md`.
- SARIF 2.1.0 (OASIS). ERC-7579 (deferred).

## 8. Signals, and the questions behind them

The harness is a developer tool run from a terminal and in CI; it has no
unattended runtime and no on-call. What it must emit instead is evidence a
reviewer reads after a run:

- "Which gate failed and on what trace?" Every finding names the gate, the
  manifest rule, the host action, and the recorded delta that broke it, in
  both the human report and the SARIF. A pass emits the manifest revision and
  the sequence count it held over.
- "Did the suite actually run, or vacuously pass?" The harness reports the
  number of ordinary and hostile sequences exercised and asserts it is
  non-zero; a conformance run that drove nothing is a failure, not a pass.

[ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal
must carry; these are report fields, not telemetry, because nothing here runs
unattended.

## 9. Boundaries, per capability

- **Manifest ingestion.** The harness reads JSON manifests and the validator
  parses them. Worth taking: a malformed or over-broad manifest that makes a
  gate vacuous. Control: JSON Schema validation with `additionalProperties:
  false` and required enumerations; the validator rejects an unparseable or
  under-specified manifest before any run.
- **Filesystem.** Cheatcode `readFile`/`writeFile` for manifests and findings.
  Worth taking: a path escape or a write outside the plugin. Control:
  `fs_permissions` scoped to the plugin's `manifests/` and an output dir; no
  absolute paths; no `vm.ffi`.
- **The modeled external-call surface.** The seam model makes an all-gas call
  to a hook and the hook may call back. Worth taking: unbounded gas, return-
  data expansion, cross-action re-entry. Control: gates 5 and 6 exercise
  exactly these; the model's reentrancy guard mirrors the host's.

[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary
list and the controls; each audit round runs its lint over the changed tree so
a claim of "no boundary opened" is checked, not trusted.

## 10. The budget, or its absence

No wall-clock or gas budget is a success criterion of the prototype, so
`metron` has nothing to hold. Gas is instead a conformance dimension: gate 5
asserts a hook stays within the manifest's declared gas budget, and that
budget is a manifest field the harness reads, not a performance target for
Janus itself. [metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns
budgets where one is a target; here there is none.

## 11. The fail-closed posture

A red `forge test`, a red `forge build`, a failing manifest validation, or a
red repository suite stops the step: no commit, no push while any is red. A
false pass is the outcome that matters most, so the harness fails closed
on ambiguity, an unrecognised effect in a delta is a violation, not an
ignored unknown; a conformance run that exercised zero sequences fails. Any
failure surfaced mid-step is worked to its cause under
[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md), and its guard
lands in the harness or the Python suite where the regression would recur.

## 12. Decisions and their homes

- The held frontier and the maturity posture live in Janus's own
  `EVOLUTION.md` at `plugins/janus/skills/janus/EVOLUTION.md`, governed by the
  [versioning contract](../../plugins/hexaemeron/skills/VERSIONING.md). This
  run creates it at baseline `janus-v0.1.0`, status `open`, with the second
  adapter as the held next job.
- The design decisions that are expensive to reverse, modeling the seam
  rather than compiling the host, JSON manifest, `libs = []`, the gate-to-test
  mapping, are recorded in this study's Design options and Risk sections,
  committed under `docs/` in step 1, and summarised in the plugin's design
  doc. No `docs/decisions/` scheme is introduced:
  [hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) warns against
  a second decision-record scheme beside the existing per-skill ledgers, and
  unmerged branches show that scheme was tried and rolled back here.

## Boundaries the study must state

- **Always.** The repository suite and the plugin's `forge test` and Python
  suite before every commit. The imprimatur lint on every shipped document.
  The full Pashov audit suite each round, since the run ships Solidity.
- **Ask first.** Changing the modeled seam's call convention away from the
  cited v2.5 source. Adding an external Solidity dependency. Widening
  `fs_permissions`. Editing an exact sentence a packaging test asserts.
  Introducing a `docs/decisions/` scheme.
- **Never.** Claim a hook is conformant on a delta the recorder did not fully
  capture. Weaken a gate to make a hostile hook pass. Commit a hostile hook
  that is not caught by its owning gate. Edit a vendored directory. Delete a
  failing test to go green. Claim a command ran when it did not.
