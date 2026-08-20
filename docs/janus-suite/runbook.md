# Runbook: Build the Janus hook-conformance suite against the Wildcat v2.5 hooks

Derived from the study beside this file. One module, the `janus` plugin,
sliced into six stacked steps. Each is one pull request, green at both ends.
Step 1 scaffolds the plugin, its Foundry harness, and every packaging
contract, and commits the study and runbook. The last step runs the whole
demo path from the study's problem statement and deletes the anchor spec.

Dependency order: packaging and toolchain first, then the manifest format,
then the recorder that reads real deltas, then the faithful host model that an
honest hook passes, then the hostile hooks and the gate engine that catch
each failure, then the reports and the end-to-end demonstration.

Each Solidity step incurs the full audit suite because the run ships
Solidity. The Disciplines line on each step names why the five phase skills
apply.

## Step 1: Scaffold the janus plugin, harness, and packaging

**Goal.** A thirteenth plugin `janus` exists with every host manifest,
portable entry, ledger, landing prose, and a compiling Foundry harness that
runs one trivial passing test; the repository suite and the new CI workflow
are green.

**Entry.** Run branch `claude/janus-wildcat-skill-bejdy0` at `1fc9f6a`.

**Exit.** `python3 -m unittest discover -s tests` passes with `janus` added to
every packaging surface; `forge build` and `forge test` pass in
`plugins/janus/harness`; `python3 -m unittest discover -s plugins/janus/tests
-t plugins/janus` passes; the imprimatur lint scores every new document clean;
`.github/workflows/janus.yml` mirrors the Pandects Python-and-Foundry shape.

**Files.** `plugins/janus/.claude-plugin/plugin.json`,
`plugins/janus/.codex-plugin/plugin.json`, `plugins/janus/AGENTS.md`,
`plugins/janus/README.md`, `plugins/janus/skills/janus/SKILL.md`,
`plugins/janus/skills/janus/EVOLUTION.md`, `plugins/janus/tests/` (a Python
placeholder suite), `plugins/janus/harness/foundry.toml`,
`plugins/janus/harness/src/Vm.sol` (minimal cheatcode interface),
`plugins/janus/harness/src/JanusBase.sol` (test base, no forge-std),
`plugins/janus/harness/test/Scaffold.t.sol`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `.agents/skills/janus/SKILL.md`,
`AGENTS.md`, `README.md`, `.github/workflows/janus.yml`,
`tests/test_marketplace_prose.py` (PLUGINS 12 to 13, landings count),
plus `docs/janus-suite/study.md` and `docs/janus-suite/runbook.md`.

**Tests.** No new gates yet: one trivial `forge test` proving the harness
compiles and the minimal `Vm` interface links, and a Python placeholder suite
that imports the (empty) validator module. The repository packaging suite is
the real check that the thirteenth plugin is wired on every surface.

**Disciplines.** phylax: the harness declares `fs_permissions` and a cheatcode
surface; this step opens that boundary and must scope it. ephoros: none, the
scaffold emits no signals yet. metron: none, no performance claim. elenchus:
any packaging-test failure is worked to cause here. hypomnema: the ledger is
created at baseline and the design decisions get their home in the committed
study and the plugin design doc.

## Step 2: Hook-manifest schema and validator

**Goal.** A JSON Schema for a hook manifest and a Python validator that
accepts a well-formed manifest and rejects an under-specified or malformed
one.

**Entry.** Step 1 exit state, on a branch from step 1.

**Exit.** `python3 plugins/janus/scripts/janus.py validate <manifest>` exits 0
on the example honest manifest and non-zero with a named reason on each
malformed fixture; `python3 -m unittest discover -s plugins/janus/tests -t
plugins/janus` passes; both repository and harness suites stay green.

**Files.** `plugins/janus/harness/schemas/hook-manifest.schema.json`,
`plugins/janus/scripts/janus.py` (the `validate` subcommand),
`plugins/janus/harness/manifests/wildcat-open-term.json` (example honest
manifest), `plugins/janus/tests/test_validator.py`,
`plugins/janus/tests/fixtures/` (malformed manifests).

**Tests.** Python unit tests: one valid manifest passes; fixtures that omit a
required enumeration, permit an unbounded effect, or break the JSON each fail
with a distinct code.

**Disciplines.** phylax: the validator parses untrusted JSON; this is the
manifest-ingestion boundary. ephoros: none. metron: none. elenchus: a
validator verdict it did not earn is worked to cause. hypomnema: the schema's
enumerations are the manifest format other tools will cite; the field set is
recorded in the design doc.

## Step 3: Host-adapter interface and state-delta recorder

**Goal.** A Solidity host-adapter interface and a state-delta recorder that
captures storage writes, external call targets, value movements, and gas
across a threshold, proven by unit tests against a fixture host.

**Entry.** Step 2 exit state, on a branch from step 2.

**Exit.** `forge test` in the harness passes recorder unit tests that show
each effect class is captured and that an unrecorded effect fails closed;
repository and Python suites stay green.

**Files.** `plugins/janus/harness/src/HostAdapter.sol` (abstract interface),
`plugins/janus/harness/src/StateDeltaRecorder.sol`,
`plugins/janus/harness/test/StateDeltaRecorder.t.sol`, a small fixture host
under `plugins/janus/harness/test/fixtures/`.

**Tests.** Recorder tests: a write inside the threshold is captured; an
external call target is captured; a value movement is captured; a gas figure
is recorded; an effect the recorder cannot classify is reported as a
violation, not ignored.

**Disciplines.** phylax: the recorder is the boundary between observed reality
and the gate verdict; a blind spot is a false pass. ephoros: the recorder is
where the per-finding delta fields originate. metron: none. elenchus: a missed
effect is the failure to guard against. hypomnema: the recorder's captured
effect classes are recorded, since a later effect class not captured is a
silent hole.

## Step 4: Wildcat host model and the honest-hook conformance path

**Goal.** A faithful in-tree model of the v2.5 market-to-hook seam, an honest
Wildcat-shaped hook, its manifest, and a conformance run in which the honest
hook passes every applicable gate, including exit liveness.

**Entry.** Step 3 exit state, on a branch from step 3.

**Exit.** `forge test` passes: a fidelity test pins the model's call primitive
against the cited v2.5 convention (all-gas call, zero value, bubbled revert,
the value-returning APR hook's `>= 0x40` return contract, the appended
extraData tail, the global reentrancy guard); the honest hook passes gates 1
through 7 over ordinary sequences; an exit-liveness scenario shows a
known-lender can still queue and execute a withdrawal after a credential
lapses and after a provider is removed. Repository and Python suites stay
green.

**Files.** `plugins/janus/harness/src/wildcat/WildcatHostModel.sol`,
`plugins/janus/harness/src/wildcat/HonestAccessHook.sol`,
`plugins/janus/harness/manifests/wildcat-open-term.json` (completed),
`plugins/janus/harness/test/WildcatConformance.t.sol`,
`plugins/janus/harness/src/JanusHarness.sol` (the gate engine, honest path).

**Tests.** The fidelity test; the honest-hook pass over each applicable gate;
the exit-liveness scenarios (credential expiry, provider removal). Every
modeled behaviour cites its source line in a comment.

**Disciplines.** phylax: the model opens the external-call surface a hook can
abuse; the honest path establishes the baseline the hostile hooks violate.
ephoros: the pass report emits the manifest revision and sequence count.
metron: none. elenchus: a fidelity gap is worked to the cited source.
hypomnema: model-versus-host divergence risk is recorded beside the fidelity
test.

## Step 5: Hostile reference hooks and the gate engine

**Goal.** Five hostile reference hooks, one per failure class, and the gate
engine that catches each with the gate that owns it.

**Entry.** Step 4 exit state, on a branch from step 4.

**Exit.** `forge test` passes: each hostile hook is caught, and by the correct
gate. Callback re-entry is caught by gate 6; gas grief by gate 5; value
redirection by gate 2; storage mutation outside declared slots by gate 1;
stale authorisation by gate 3 or 4 as the manifest declares. A conformance run
that exercised zero sequences fails. Repository and Python suites stay green.

**Files.** `plugins/janus/harness/src/hostile/ReentryHook.sol`,
`GasGriefHook.sol`, `ValueRedirectHook.sol`, `StorageMutationHook.sol`,
`StaleAuthHook.sol`, `plugins/janus/harness/test/HostileHooks.t.sol`,
`plugins/janus/harness/src/JanusHarness.sol` (gate engine completed),
findings emission via `writeFile`.

**Tests.** One test per hostile hook asserting the specific gate id fires and
no other gate fires incidentally; a non-zero-sequence assertion; a
stateful-fuzz handler that keeps a hostile hook in the loop and asserts the
gate holds.

**Disciplines.** phylax: the hostile hooks are the boundary probes; each must
fail closed. ephoros: each finding names gate, rule, action, and delta.
metron: none. elenchus: a hostile hook that passes, or is caught by the wrong
gate, is worked to cause. hypomnema: the gate-to-failure-class mapping is
recorded, since it is the suite's contract.

## Step 6: Reports, the demo path, and retiring the anchor

**Goal.** Human-readable and SARIF reports from the findings artifact, the
full demo path passing end to end, and the anchor `docs/commons/janus.md`
deleted with the Commons pointer updated.

**Entry.** Step 5 exit state, on a branch from step 5.

**Exit.** `python3 plugins/janus/scripts/janus.py report` produces a human
markdown report and a SARIF 2.1.0 file from the sample findings, each finding
linking a gate and manifest rule to a trace; the Python suite validates the
SARIF shape; the whole study demo path passes; `docs/commons/janus.md` is
removed and the README Commons entry points at the shipped plugin instead;
`docs/commons/` is deleted if empty; repository, harness, and Python suites
all green.

**Files.** `plugins/janus/scripts/janus.py` (the `report` subcommand),
`plugins/janus/examples/findings.sample.json`,
`plugins/janus/tests/test_reporter.py`, `plugins/janus/README.md` and
`docs/janus-suite/` (final prose), `README.md` (Commons entry retargeted),
removal of `docs/commons/janus.md`.

**Tests.** Reporter tests: the sample findings render to human markdown and to
schema-valid SARIF; a clean run renders an empty-findings report that states
the manifest revision and sequence count.

**Disciplines.** phylax: the reporter writes files; the output path is scoped.
ephoros: the report is the run's evidence surface; this step finalises its
fields. metron: none. elenchus: a malformed SARIF is worked to cause.
hypomnema: retiring the anchor and repointing the Commons entry is the last
recorded decision; the plugin's landing prose replaces the spec as the
reader's entry point.
