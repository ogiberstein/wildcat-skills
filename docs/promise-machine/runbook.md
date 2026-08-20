# Runbook: establish the Promise Machine

Derived from `docs/promise-machine/study.md`. Ten dependency-ordered steps.
Step 1 commits the specification. Step 10 runs the study's demo path and the
supported-host demonstrations. Every step is one pull request, starts from the
previous green exit and changes one reviewable boundary.

Step 1 landed before this implementation run in PR #283 at `d577b88`. The
controller preserves it as reviewed history and executes Steps 2 through 10 as
nine stacked implementation steps.

## Step 1: Commit the specification

**Goal.** Put the complete study and runbook in the repository before any
Promise Machine implementation begins.

**Entry.** Clean run branch cut from exact Fiat entry ref `9c7692d` on `main`,
the merged result of Berean repair PR #282. If Berean reports absent
`release/corpus` or passing-fixture corpus files, the phase is blocked: run the
failure through Elenchus and establish a new green `main` entry ref before
`hexctl init`.

**Modules.** `promise-law` scaffolding.

**Exit.** Both documents are committed, Protasis `2.2.0` accepts the runbook,
Imprimatur accepts both documents and the 38-test root baseline remains green.
The step record says that PRs #270, #279, #281, #282 and #283 were read and carries
forward the Berean, Janus and mirror limits named in the study. Berean's
complete 151-test suite, Janus's 14 Python tests and Janus's 24 Foundry tests
also pass from the recorded entry ref.

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/promise-machine/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/promise-machine/study.md docs/promise-machine/runbook.md
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/berean/tests -t plugins/berean
python3 -m unittest discover -s plugins/janus/tests -t plugins/janus
(cd plugins/janus/harness && forge build && forge test -vv)
```

**Files.** `docs/promise-machine/study.md`,
`docs/promise-machine/runbook.md`.

**Tests.** No new tests. Record the existing root, Berean, Janus Python and
Janus Foundry counts and the two document-lint exits.

**Disciplines.** hypomnema: the study and runbook establish the durable build
contract and live under the existing `docs/<topic>/` convention. phylax: none,
no process gains a new input. ephoros: none, nothing runs unattended. metron:
none, no implementation performance claim. elenchus: any lint or root-suite
failure stops the step and is fixed with a reproducing test when it exposes a
checker defect.

## Step 2: Write the law and installation binding

**Goal.** Author the one normative Promise Machine contract, bind root and
plugin runtime policy to it, and generate exact plugin-local copies for
standalone installation.

**Entry.** Step 1's green exit.

**Modules.** `promise-law`.

**Exit.** `PROMISE_MACHINE.md` contains the settled principle, the shared
`promise-machine/v1` contract identity, vocabulary, per-promise schema,
consequence levels, composition rules and exception rules.
All 14 plugins have a byte-identical generated copy and a local runtime
binding. Horos gains the runtime contract its plugin currently lacks. The law
includes evidence inheritance and bounded-conformance rules that preserve
Berean and Janus boundaries without importing their domain formats. Editing one
copy makes the drift check fail.

```bash
python3 scripts/promise_machine.py sync --check
python3 scripts/promise_machine.py check --only law,copies
python3 -m unittest tests.test_promise_machine_contract.PromiseLawTests
python3 -m unittest discover -s tests
```

**Files.** `PROMISE_MACHINE.md`, `AGENTS.md`,
`plugins/*/PROMISE_MACHINE.md`, `plugins/*/AGENTS.md`,
`scripts/promise_machine.py`, `tests/test_promise_machine_contract.py`,
`tests/fixtures/promise-machine/divergent-copy/`, and a decision record under
`docs/decisions/` for generated install-local copies.

**Tests.** Law headings and required definitions; one shared contract version;
exact copy equality; generated-marker and fixed-destination enforcement; a
divergent-copy fixture; empty-plugin-set and symlink/path-escape refusals.

**Disciplines.** phylax: the sync/check command walks paths and writes generated
copies, so it confines roots, rejects symlinks and writes atomically. hypomnema:
the authored/generated boundary is expensive to reverse and receives a decision
record. metron: the full checker budget is measured in step 10; no performance
claim yet. elenchus: mutation fixtures guard every discovered parser or copy
failure. ephoros: terminal JSON diagnostics answer the four questions in study
item 8; no unattended telemetry.

## Step 3: Discover and structurally check the complete universe

**Goal.** Make the checker derive plugins, canonical and nested skills,
governance class, routers and overlays from disk and reject every structurally
unbound promise.

**Entry.** Step 2's law and copy API.

**Modules.** `promise-inventory`.

**Exit.** `inventory --json` reports 14 plugin directories, 28 canonical
skills, 23 governed skills and 5 vendored skills at this starting ref. The
checker rejects missing fields, unsupported evidence classes, empty discovery,
unclassified skills, unbound vendored files, duplicate promise ids, missing
recovery and malformed exceptions. Counts are observations derived from disk,
not constants defining the universe.

```bash
python3 scripts/promise_machine.py inventory --json
python3 scripts/promise_machine.py check --only inventory,structure
python3 -m unittest \
  tests.test_promise_machine_contract.PromiseInventoryTests \
  tests.test_promise_machine_contract.PromiseStructureTests
python3 -m unittest discover -s tests
```

**Files.** `scripts/promise_machine.py`,
`tests/test_promise_machine_contract.py`,
`tests/fixtures/promise-machine/{missing-contract,unclassified-skill,unsupported-evidence-class,no-recovery,unattributed-exception}/`.

**Tests.** One named mutation case per required field and evidence class; nested
Fizz subsidiary discovery; empty-set rejection; first-party/vendored exhaustive
classification; JSON and text output parity.

**Disciplines.** phylax: untrusted Markdown and fixture trees are bounded,
confined and parsed without execution. elenchus: every accepted malformed shape
becomes a fixture that fails without the fix. hypomnema: finding codes are a
public checker interface and are documented beside their definitions. ephoros:
stable codes, paths and promise ids make terminal diagnostics inspectable.
metron: linear filesystem work only; final timing waits for the full checker.

## Step 4: Establish one canonical identity and one portable router

**Goal.** Remove the duplicate portable catalogue, preserve host-neutral reach
through one suite router and validate host exposure and version layers.

**Entry.** Step 3's inventory can identify every canonical target and router.

**Modules.** `promise-identity`.

**Exit.** `.agents/skills/` contains only `promise-machine/SKILL.md`. The router
has no behavioural version, selects through root and plugin runtime contracts,
and resolves one canonical skill per request. The 20 old entrypoints are gone.
Every canonical logical id is unique. Package versions and skill versions are
reported separately. Horos is either present in both marketplaces as selected
by this study or an explicit maintainer-approved exclusion blocks the step.

```bash
python3 scripts/promise_machine.py check --only identity,routers,versions,hosts
python3 -m unittest \
  tests.test_portable_skills \
  tests.test_version_propagation \
  tests.test_promise_machine_contract.PromiseIdentityTests
python3 -m unittest discover -s tests
```

**Files.** `.agents/skills/promise-machine/SKILL.md`, the 20 removed portable
entrypoints, `AGENTS.md`, `README.md`, `.agents/plugins/marketplace.json`,
`.claude-plugin/marketplace.json`, `tests/test_portable_skills.py`,
`tests/test_version_propagation.py`, `tests/test_promise_machine_contract.py`,
`tests/fixtures/promise-machine/{unresolved-router,duplicate-canonical,package-as-skill-version}/`,
and a decision record for the portable identity change.

**Tests.** One router reaches every canonical skill through the selection
tables; unresolved, multi-target and versioned routers fail; duplicate logical
ids fail; a package version presented as a skill version fails; all manifest
paths resolve; Claude and Codex host sets are explicit.

**Disciplines.** hypomnema: removing direct portable entrypoints is a durable
compatibility decision and gets a record naming the one-hop trade. phylax:
router links and manifest sources remain confined inside the repository.
elenchus: the supplied duplicate Protasis state becomes the regression specimen.
ephoros: none, discovery is session-local and has no unattended operator.
metron: none, no performance claim.

## Step 5: Declare promises for standalone first-party plugins

**Goal.** Add exact domain promises to Alexandria, Ariadne, Berean, Brevitas,
Hermes, Horos, Janus, Lazarus, Lemma/Chunk, Pandects, Probitas, Sapheneia and
Tabularium without widening any existing boundary.

**Entry.** Step 4's identity and section schema are fixed.

**Modules.** `promise-contracts`.

**Exit.** Each canonical skill has exactly one Promise Machine section and one
or more stable promise ids covering operations with different claims. Every
field is substantive. The declarations cite current commands and evidence and
state the nearest overclaims already refused by canonical instructions.
Berean separates corpus, answer, evaluation and promotion claims so a level-3
promotion cannot borrow a citation check's narrower meaning. Janus separates
manifest validation, bounded hook conformance and report rendering so an
observed adapter result cannot become a general safety claim.

```bash
python3 scripts/promise_machine.py check --only structure,contracts
python3 -m unittest tests.test_promise_machine_contract.PromiseContractTests
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria
python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne
python3 -m unittest discover -s plugins/berean/tests -t plugins/berean
python3 -m unittest discover -s plugins/brevitas/tests -t plugins/brevitas
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
python3 -m unittest discover -s plugins/janus/tests -t plugins/janus
(cd plugins/janus/harness && forge build && forge test -vv)
python3 plugins/lemma/tests/test_markdown.py
python3 plugins/lemma/tests/test_solidity.py
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
python3 -m unittest discover -s plugins/pandects/tests -t plugins/pandects
python3 -m unittest discover -s plugins/probitas/tests -t plugins/probitas
python3 -m unittest discover -s plugins/sapheneia/tests -t plugins/sapheneia
python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium
```

**Files.** The 13 canonical standalone skill files named in the goal and
`tests/test_promise_machine_contract.py`.

**Tests.** Structural parsing over all declarations and the existing plugin
suites. A declaration that only exposes existing behaviour is prose-only and
does not move a skill ledger. If satisfying the schema changes a gate, output,
ordering or decision, stop and apply that skill's generation rule before the
step exits.

**Disciplines.** hypomnema: semantic changes, if any, are recorded in the
affected skill ledger; restatements do not manufacture history. phylax: none,
the step adds no runtime input and Berean remains offline. ephoros: none, no
unattended behaviour changes. metron: none, no performance change. elenchus:
plugin-suite or Janus harness failures stop the step and receive local
regression evidence. Any required Janus Solidity change first amends the study
and incurs the Solidity audit; it is not hidden inside a declaration step.

## Step 6: Declare Hexaemeron promises and bind vendored overlays

**Goal.** Add domain promises to the ten first-party Hexaemeron skills and
digest-bound first-party overlays for Fizz, Fizz Convert, Fizz Sync, X-Ray and
Solidity Auditor without editing vendored instructions.

**Entry.** Step 5 has proved the declaration shape across standalone plugins.

**Modules.** `promise-contracts`.

**Exit.** All ten first-party Hexaemeron skills satisfy the contract.
`plugins/hexaemeron/PROMISES.md` covers the five vendored paths, records their
SHA-256 digests and states promises no broader than their upstream workflows.
A one-byte vendored mutation makes overlay verification fail. `git diff` shows
no vendored instruction edit in this step.

```bash
python3 scripts/promise_machine.py check --only contracts,overlays
git diff --exit-code HEAD^ -- \
  plugins/hexaemeron/skills/fizz/SKILL.md \
  plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md \
  plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md \
  plugins/hexaemeron/skills/x-ray/SKILL.md \
  plugins/hexaemeron/skills/solidity-auditor/SKILL.md
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
```

**Files.** The ten governed `plugins/hexaemeron/skills/*/SKILL.md` files,
`plugins/hexaemeron/PROMISES.md`, `plugins/hexaemeron/AGENTS.md`, and overlay
fixtures/tests under `tests/fixtures/promise-machine/` and
`tests/test_promise_machine_contract.py`.

**Tests.** Overlay exhaustiveness and digest drift; no overlay for a first-party
skill; no vendored skill without overlay; receipt and report boundaries for
Fiat, Fizz, X-Ray and Solidity Auditor; no router or overlay broadening.

**Disciplines.** hypomnema: the vendoring boundary receives its required
decision record. phylax: overlay paths are confined and digests are recomputed,
not trusted from prose. elenchus: vendored drift is a named failure with a
mutation guard. ephoros: none, no unattended path. metron: none, no performance
claim.

## Step 7: Classify and close executable-skill conformance gaps

**Goal.** Map existing domain-native evidence for executable skills and add
only the material P/M/S/O/R/X cases the inventory proves absent.

**Entry.** Steps 5 and 6 have stable promise ids.

**Modules.** `promise-conformance`, `promise-composition`.

**Exit.** `tests/promise_machine_coverage.json` has one row per discovered
promise. Alexandria, Ariadne, Berean, Hermes, Elenchus, Ephoros, Fiat, Horos,
Janus, Lazarus, Chunk, Metron, Pandects, Phylax, Probitas, Protasis and
Tabularium have referenced positive, missing, mismatch, overclaim and recovery
evidence or an explicit inapplicability reason. Supported exceptions have a
case. Every path and test selector resolves, and every material gap found at
entry is closed. Berean rows preserve source/read class and time-domain
conflicts through promotion and Ariadne handoff cases. Janus rows bind the
adapter, manifest, recorder and bounded search, fail unknown effects, and map
each hostile hook to its owning gate.

```bash
python3 scripts/promise_machine.py coverage --check \
  --group executable
python3 -m unittest tests.test_promise_machine_contract.PromiseCoverageTests
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s plugins/berean/tests -t plugins/berean
python3 -m unittest discover -s plugins/janus/tests -t plugins/janus
(cd plugins/janus/harness && forge test -vv)
```

Run each plugin suite named by a changed coverage row using the exact commands
from root `AGENTS.md`; no unrun suite receives a coverage citation.

**Files.** `tests/promise_machine_coverage.json`, relevant existing plugin test
files and fixtures, and `tests/test_promise_machine_contract.py`.

**Tests.** Coverage-row exhaustiveness; selector existence; one test cannot
silently satisfy incompatible categories; `not_applicable` requires a reason;
level-2/3 promises cannot leave material negative or recovery gaps; a Berean
recorded read cannot be reclassified by its consumer; promotion does not prove
answer truth; a Janus unknown delta fails; a Wildcat-adapter result cannot
satisfy a cross-host or safety claim.

**Disciplines.** elenchus: missing behavioural evidence is closed by a specimen
that fails without the intended boundary. hypomnema: the coverage inventory is
the durable map, not a claim that every test proves everything. phylax:
fixtures, Berean answers and Janus findings remain local and are treated as
data. ephoros: none, test execution is not an unattended service. metron: none,
no performance change.

## Step 8: Classify prompt, transformation and vendored conformance

**Goal.** Cover the promises whose evidence is evaluation-shaped rather than a
deterministic runtime predicate, without pretending model judgement is proof.

**Entry.** Step 7 has fixed the coverage schema and executable standard.

**Modules.** `promise-conformance`.

**Exit.** Brevitas, Hypomnema, Imprimatur, Kronos, Sapheneia, Vulgate and the
five vendored overlays have classified P/M/S/O/R/X evidence. Deterministic
checks cover structure and protected content where possible. Labelled cases
cover nearby overclaims and recovery. Forward-testing gaps remain visible as
`recorded` or `unknown`, never promoted to `proved`.

```bash
python3 scripts/promise_machine.py coverage --check \
  --group prompt,vendored
python3 -m unittest tests.test_promise_machine_contract.PromiseCoverageTests
python3 -m unittest discover -s plugins/brevitas/tests -t plugins/brevitas
python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py
python3 -m unittest discover -s plugins/sapheneia/tests -t plugins/sapheneia
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
```

**Files.** `tests/promise_machine_coverage.json`, labelled cases or fixtures in
the owning plugin, and affected tests.

**Tests.** Brevitas preserves evidence; Imprimatur does not erase a licensed
term or scope qualifier; Vulgate preserves intended content; Sapheneia does not
diagnose; Fiat/Kronos distinguish skipped or failed work from success; vendored
overlays reject audit, invariant-completeness and security overclaims.

**Disciplines.** elenchus: only observed instruction failures become fixes;
unknown cross-model behaviour stays unknown. hypomnema: each evaluation records
model, prompt, corpus and disposition where available. phylax: model output is
untrusted evidence and never executes itself. ephoros: none, no production
telemetry. metron: none, evaluation quality is not expressed as a performance
budget.

## Step 9: Bind runtime, evolution, release and public prose

**Goal.** Ensure consequential durable results carry enough information to
inspect their promise, reconcile public claims and publish every changed plugin
under a new package version without advancing unrelated skill frontiers.

**Entry.** Steps 7 and 8 establish what each promise currently proves.

**Modules.** `promise-runtime`, `promise-evolution`.

**Exit.** Existing level-2/3 result formats either bind promise id, subject,
scope, evidence references/classes, unknowns, transition and exception, or the
coverage inventory names the existing fields that already do so. Any actual
behavioural change receives the affected skill's generation bump; prose-only
declarations do not. No `Next Fiat job` changes. Public README, runtime and
marketplace prose agree. Every changed plugin package has a new explicit
version in its Claude manifest, Codex manifest and Claude marketplace entry;
the exact targets are the delivery-package values recorded in the study and
must differ from every recorded entry value.
The root README begins exactly with `# Wildcat Labs Skills`, a blank line and
`## The Promise Machine`; the latter names the architecture beneath the retained
suite identity rather than renaming the repository.

```bash
python3 - <<'PY'
from pathlib import Path

text = Path("README.md").read_text(encoding="utf-8")
assert text.startswith("# Wildcat Labs Skills\n\n## The Promise Machine\n")
PY
python3 scripts/promise_machine.py check
python3 -m unittest \
  tests.test_evolution_contract \
  tests.test_version_propagation \
  tests.test_marketplace_prose \
  tests.test_promise_machine_contract
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs PROMISE_MACHINE.md
```

**Files.** Relevant result schemas/writers only where the evidence inventory
finds a real binding gap; affected `SKILL.md` and `EVOLUTION.md` pairs;
`README.md`, `AGENTS.md`, plugin runtime and landing prose; all changed plugin
manifests and `.claude-plugin/marketplace.json`.

**Tests.** Exact root README title and following architecture heading; runtime
binding fixtures; no receipt-, promotion- or conformance-as-truth claim; no
held-frontier digest change on a generation or prose-only edit; three-way
package version propagation to every delivery-package value; Promise Machine
public-prose reconciliation; stale package version mutation fails. Berean's
Wildcat-grounded release and Janus's second adapter remain held rather than
being advanced by this suite-wide delivery.

**Disciplines.** hypomnema: version and representation changes live in the
existing ledgers and decision records, with frontiers untouched. phylax: any
schema or writer change preserves confined paths, atomic writes and untrusted
input handling. ephoros: durable results carry inspectable evidence rather than
new telemetry. metron: no runtime performance claim. elenchus: every binding
gap fixed here has a negative fixture that fails without the fix.

## Step 10: Demonstrate the Promise Machine against itself

**Goal.** Run the complete deterministic suite and the three named discovery
demonstrations, then verify Fiat's ledger without overstating the result.

**Entry.** Step 9's release surfaces, versions and public prose are green.

**Modules.** `promise-demonstration`.

**Exit.** The checker reports the complete discovered universe with no breach;
all root and changed-plugin suites pass; tree and prose checks pass; the timing
budget passes; the Codex UI shows one authoritative Protasis while this
repository is open and the refreshed marketplace plugin is installed; Claude
resolves `/hexaemeron:protasis`; a host-neutral Agent Skills discovery sees the
single Promise Machine router and reaches canonical `protasis-v2.2.0` without a
router version. Berean's release verifier/evaluation and Janus's Python and
Foundry gates run from their shipped plugin boundaries. Fiat's final controller
ledger verifies. Each manual result is recorded as observed evidence with host
version and screenshot or transcript.

```bash
python3 scripts/promise_machine.py inventory --check
/usr/bin/time -p python3 scripts/promise_machine.py check
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria
python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne
python3 -m unittest discover -s plugins/berean/tests -t plugins/berean
python3 -m unittest discover -s plugins/brevitas/tests -t plugins/brevitas
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
python3 -m unittest discover -s plugins/janus/tests -t plugins/janus
(cd plugins/janus/harness && forge build && forge test -vv)
python3 plugins/lemma/tests/test_markdown.py
python3 plugins/lemma/tests/test_solidity.py
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
python3 -m unittest discover -s plugins/pandects/tests -t plugins/pandects
(cd plugins/pandects && forge build && forge test)
python3 -m unittest discover -s plugins/probitas/tests -t plugins/probitas
python3 -m unittest discover -s plugins/sapheneia/tests -t plugins/sapheneia
python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs PROMISE_MACHINE.md
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py verify
git diff --check
```

The Solidity audit suite is waived only after `git diff --name-only` confirms
no Solidity file changed. Janus and Pandects Foundry builds and tests still run
because their plugin instructions and evidence integration changed. Any
Solidity diff cancels the waiver and runs the bundled audit before closure.

Manual demonstrations:

1. **Codex.** Upgrade `wildcat-labs`, restart the desktop app, open this
   repository in a new task, type `/prot`, and record the picker showing the
   installed canonical Protasis but no workspace Protasis competitor. Repeat a
   name search for every removed collision using the generated identity report,
   including Berean and Janus.
2. **Claude Code.** Update the marketplace and Hexaemeron package, reload
   plugins, invoke `/hexaemeron:protasis`, and record the canonical version from
   its ledger. Confirm no project skill claims another Protasis identity.
3. **Host-neutral.** Point an Agent Skills implementation at `.agents/skills`,
   record that it discovers only `promise-machine`, invoke it for Protasis and
   record the resolved canonical path and `protasis-v2.2.0`. Route one Berean
   request and one Janus request, and record that they reach
   `berean-v0.1.0` and `janus-v0.1.0` without assigning a version to the router.

**Files.** Demonstration records under `docs/promise-machine/evidence/`, final
audit records, and only the version/evolution files justified by actual changes.

**Tests.** No new behaviour begins here. A failure returns to the owning step
and lands with a guard before the demonstration is rerun.

**Disciplines.** hypomnema: manual and command evidence is recorded at stable
paths, and the final claim stays narrower than suite correctness. phylax: host
updates use supported installers; caches are never hand-edited. ephoros:
terminal reports and Fiat receipts answer what ran and what failed. metron: the
full checker is measured against the 5-second budget under the recorded
environment. elenchus: any failure stops closure and returns to its causal step.
