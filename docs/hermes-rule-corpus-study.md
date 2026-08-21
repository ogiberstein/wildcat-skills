# Study: A pinned gas-rule corpus Hermes enforces

Assuming, unless corrected:

1. This is a frontier advance, and the held `live-evidence-bundle` target is displaced rather than completed. The ledger takes two rows: an epoch row `hermes-v0.1.1` cut in step 1, carrying the new frontier revision, gap and digest and stating that the evidence-bundle target is reopened rather than closed; then an evolution row `hermes-v1.1.1` cut in the last step when the corpus job completes, carrying its successor. The epoch row's change text has to contain the word `reopen`, which is what the root evolution suite checks when an epoch row moves the digest. That arithmetic, the header agreement and the reopen guard were run against `tests/test_evolution_contract.py`'s own helpers before this study was written, so the construction is checked rather than assumed.
2. The reading behind assumption 1 is worth one look, because the contract's reopening paragraph is written for a frontier that has gone `mature`, and this one is `open`. Two readings are available: the epoch mechanism generalises, so a maintainer-supplied requirement can displace an open target as long as the boundary is recorded, which is the reading this study takes; or nothing may displace an open target, in which case the corpus cannot become the frontier until the evidence bundle ships and this run is a generation advance instead. The second reading changes the ledger rows and the two prose sweeps, and nothing else in this study.
3. Being a frontier run, this owes the reconciliation the versioning contract states: a cold read of all mutable first-party marketplace prose across the checkout before the job is recorded as done, not only the six Hermes surfaces that carry the frontier sentence.
4. `--rule` becomes required on `verify`. That deliberately breaks every existing Hermes invocation, which is the second half of what makes the epoch row honest. A candidate with no corpus rule cannot run; the corpus gains the rule in a separate change first, the way a missing property test already gets added in a preparatory change before the candidate is measured.
5. The reference document supplied for this run, SHA-256 `297c926dc0a2e011e31da5245273c136273b8faa390f3691910c22c870068449`, is the only source for the corpus. Every record traces to one of its sections, and this run adds no rule of its own invention.
6. The corpus ships as JSON data with generated prose beside it. The document scores 35.3/100 with 168 imprimatur defects, and the root suite holds every tracked `.md` outside `audit/` and `docs/` clean, so the document itself cannot ship under `plugins/`.
7. Python 3.11 and stdlib unittest, matching the existing Hermes suite. The harness stays dependency-free, so the document's YAML schema is transcribed into JSON rather than parsed as YAML.
8. `forge config --json` supplies `solc`, `evm_version` and `via_ir`, and `baseline` already seals that output as `baseline.forge-config.json` with its digest. The scope gate reads the sealed record rather than shelling out again.
9. The run starts from `main` at `87e213c19e64687406d7ba7601e093929bb3d813`.

## 1. Problem statement

Hermes has gates and no knowledge. Six gates measure a candidate, refuse a regression, hold a storage layout and demand a property test for state-sensitive unchecked arithmetic, and the whole judgement of whether the candidate's idea is sound for this compiler and this fork sits outside the harness in twelve rows of catalogue prose. Two consequences are visible in the checkout today. The catalogue's `loop-arithmetic` row offers "a proven-safe unchecked increment", which the document's MYTH-02 rejects for every compiler at or above 0.8.22, and nothing in the run records which body of advice judged an accepted candidate.

This run gives Hermes a corpus it enforces: 120 rules with their evidence grade, automation level, preconditions and proof obligations, 28 rejected universal rules, and 40 citations, transcribed into a JSON corpus whose digest `baseline` seals beside the Foundry configuration and which `verify` consults before any Forge test or snapshot runs. Rule selection becomes required, so the corpus is the way in rather than an option beside it.

Done means a rule id selects the candidate; the harness refuses an unknown id, a rejected universal rule, a rule whose class disagrees with the declared class, a rule outside the scope the sealed configuration resolves, an unresolvable scope, an unanswered proof obligation, and a corpus whose digest moved after the baseline, each before Gate 3 spends a Forge run; an accepted `result.json` carries the corpus digest, the rule id and the recorded obligation answers; the six Hermes surfaces and the root selection table carry one agreed successor frontier; and the demo path holds:

```bash
python3 plugins/hermes/skills/hermes/scripts/hermes.py corpus --validate
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s tests
```

## 2. Prior art

- `plugins/hermes/skills/hermes/scripts/hermes.py` owns the run: `baseline`, `verify`, `promote`, `status`, the six gates, exit codes `10` to `60`, the twelve `OPTIMISATION_CLASSES`, the evidence directory and `result.json`. `baseline` writes `baseline.forge-config.json` and records its SHA-256; `verify` already refuses a changed Forge version or Foundry configuration. That is the record the scope gate reads and the pattern the corpus digest follows.
- `references/optimisation-catalogue.md` holds the twelve classes as prose with per-class risk and pre-checks. It stays the reading surface; the corpus becomes the machine surface beneath it.
- The last two merged pull requests that changed the target: [skills#95](https://github.com/wildcat-finance/skills/pull/95) compressed the six Hermes Markdown surfaces and states that the gates, the exit codes `0/10/20/30/40/50/60`, the layout checks and the arithmetic refusals stay intact, which item 3 turns into a bounded constraint rather than a blanket one now that the command surface breaks on purpose; and [skills#22](https://github.com/wildcat-finance/skills/pull/22) normalised compilation-local AST identifiers in the Gate 5 layout comparison and removed the incomplete `v2-protocol` example. Both closed their issues with every box ticked ([skills#21](https://github.com/wildcat-finance/skills/issues/21), [skills#23](https://github.com/wildcat-finance/skills/issues/23)), so neither carries unfinished work forward. The one open item they leave behind is the held frontier, which assumption 1 reopens rather than drops.
- `audit/AUDIT.md` holds no Hermes round. It was read before design options were drawn, and there is no accepted lead and no prior finding bearing on this work.
- Sibling precedent in this checkout: Imprimatur ships `lexicon/hard.json`, `gated.json` and `structural.json` as data behind one script, which is the shape this corpus takes. Alexandria, Berean and Lazarus each pin a schema file rather than a script in `tests/promise_machine_coverage.json`, so a corpus schema is an accepted subject for a promise.
- `plugins/pandects/` is a Foundry root in this checkout at `solc_version = "0.8.28"` and `evm_version = "cancun"`, available as a real smoke target beside the hermetic fake-Forge fixture the Hermes suite already uses.
- `.agents/skills/` now holds only the portable Promise Machine router, so the Hermes copy that skills#95 also had to edit no longer exists and is not a surface this run reconciles.
- Outside: the document's own evidence corpus, meaning Aave v3, Uniswap v3 and v4, Permit2, Seaport, Solady and OpenZeppelin v5.0.2, plus EIP-1153, EIP-2929, EIP-2200, EIP-3529, EIP-3860, EIP-6780, EIP-170 and the versioned Solidity 0.8.25 documentation.

## 3. Constraints and non-goals

- Starting ref: `main` at `87e213c19e64687406d7ba7601e093929bb3d813`, clean tree.
- Exit codes `10` to `60` keep their published per-gate meanings, and no seventh code is minted. The command surface is what breaks: `verify` gains a required flag, and every documented invocation moves with it.
- The six gates, their order, and the twelve class names do not move. A corpus rule maps onto one existing class or onto none.
- Six surfaces carry the frontier sentence and are held in agreement by the root suite: `plugins/hermes/README.md`, which also carries the single rolling-job line the root suite allows nowhere else, `plugins/hermes/AGENTS.md`, `plugins/hermes/skills/hermes/SKILL.md`, `references/optimisation-catalogue.md`, `EVOLUTION.md`, and the root `README.md` selection table. The landing README's job topic has to stay unique across all fourteen plugins and end with a full stop. Both the epoch row and the evolution row move that sentence, so the prose sweep happens twice.
- `tests/promise_machine_coverage.json` pins the SHA-256 of `hermes.py`, so the coverage digest moves in the same commit as the source. A new authorising transition earns a promise heading in `SKILL.md`, which also touches `tests/test_promise_machine_contract.py`.
- `tests/test_version_propagation.py` pins the Hermes package version at `0.1.1`, separately from the skill label. The package version moves only if that test moves with it.
- `.horos/boundary.json` is regenerated for every added path, and the corpus stays pretty-printed so it is readable rather than classified as a blob.
- Every rule record cites the document section it came from. A record with no traceable source is a defect, not a judgement call.
- Non-goal: detectors. The document's `detector_signals` ship as recorded data, not as an engine that nominates candidates. Hermes measures what a human nominated, and the document's own section 16 says a detector still needs the artifact benchmark.
- Non-goal: publishing the live Wildcat evidence bundle. The epoch row reopens that target; this run does not deliver it.
- Non-goal: L2 and non-Ethereum fee models, which the document scopes out itself.
- Non-goal: implementing CMP-12. Custom optimizer step sequences are transcribed as a rule with automation `never` and nothing more.
- Non-goal: rewriting the reference document into house register. It is preserved as a source of record.

The topic stays one study rather than a decomposition. The corpus, its validator and the required Gate 2 binding cannot be verified apart: a corpus nobody consults proves nothing, a validator with no corpus has nothing to hold, and the binding with neither has no rule to resolve. One demo path exercises all three, so the criteria do not cluster into separately shippable groups.

Boundaries this run works under:

- Always. Both the Hermes suite and the root suite before a commit. The imprimatur lint on every changed document. The three tree-reading skill lints from the root. A regenerated `.horos/boundary.json` for every added path. A recorded measurement before any claim about the budget in item 10.
- Ask first. Adding a dependency of any kind, including a YAML parser. Changing an exit code, a gate order or a class name. Moving the package version pinned in `tests/test_version_propagation.py`. Adding or amending a Promise Machine heading. Choosing the successor frontier the evolution row carries.
- Never. Commit an RPC credential or key material. Rewrite the pinned source document. Delete or weaken a failing Hermes test to make the suite pass. Fetch a citation URL from the harness. Invent a rule, a scope bound or a citation the source document does not carry. Move the held target without the epoch row that records the boundary. Report a gate as passed when its command did not run.

## 4. Design options

1. **Ship the document as a reference and cite it from the catalogue.** Cheapest, and it fails on two counts: the document carries 168 lint defects so it cannot ship under `plugins/`, and it leaves every one of its disciplines as advice the run may skip. Hermes exists because the ideas are cheap and the evidence is the job, and a second document adds ideas.
2. **Corpus and validator, advisory to the harness.** The rules become JSON records with the document's schema, and a validator holds the schema, unique ids, resolvable citations and the class mapping. Better, and the gates still cannot see it: a candidate justified by MYTH-02 passes every gate it passed yesterday.
3. **Corpus, validator, and a required Gate 2 binding, with the corpus digest sealed at Gate 1.** Chosen. `verify` requires `--rule <ID>`, resolves it in the corpus the baseline sealed, and refuses seven ways before Gate 3 spends a Forge run: an unknown id, a rejected universal rule, a class disagreement, a rule outside the resolved scope, a scope that cannot be resolved, a proof obligation with no recorded answer, and a corpus whose digest moved since the baseline. `result.json` gains the corpus digest, the rule id and the obligation answers. It trades away the automatic candidate discovery of option 4 and every existing invocation script, and it accepts a real hazard: obligation answers are recorded judgement, not proof, so the run can produce a well-filled form. The mitigation is that the six hard gates are untouched, the obligations are per-rule and few, and the record says plainly which fields are judgement.
4. **A detector engine over the source.** Rejected, and rejected again after the run was reframed as a frontier advance, since the reframing changes none of its costs. Executable `detector_signals` make Hermes propose candidates, which inverts the discipline the skill is built on, and it is a second product with a false-positive budget nobody has asked for.

A fifth option was considered and dropped inside option 3: an escape hatch for a candidate with no corpus rule, taking a rationale the way the layout-change and non-sensitive-unchecked flags already do. It loses because a rationale flag is the one refusal every operator can satisfy by typing, which would leave the required binding required in name only.

## 5. Risk register seed

```risk-register
frontier-displacement | the epoch row against the versioning contract and the public job text | the row states that the evidence-bundle target is reopened rather than completed, contains the word reopen, carries a new revision and digest, and lands before the frontier job starts
cli-break | the required rule flag against every documented invocation | every command in the six surfaces moves with the flag, and the suite covers a verify call that omits it
successor-judgement | the evolution row's next job against the run's own evidence | the successor is chosen at the end of the run, not assumed here, and the reopened evidence bundle is the default the row has to argue against
corpus-schema-drift | the corpus file against its validator | every record validates, ids are unique, an unknown field is refused, and each rule's class resolves to one of the twelve or to none
transcription-fidelity | 120 rules, 28 myths and 40 citations against the pinned source document | each record cites its source section, each citation id resolves to exactly one URL, and the counts 120, 28 and 40 are asserted
citation-shape | a citation written at the start of a line against a footnote definition | the validator counts definitions rather than line-initial markers, since REF-25 appears both ways in the source
myth-as-justification | the candidate's declared rule and rationale text against the 28 rejected rules | a myth id named as a rule is refused, and a rationale citing one is refused with the myth's correction quoted
scope-false-refusal | a rule's declared range against the configuration the baseline sealed | a fork ordering decides cancun against osaka rather than string equality, a null solc refuses the scope claim instead of assuming one, and an unknown fork name refuses
corpus-digest-drift | the corpus at verify against the corpus the baseline sealed | a corpus edited between the two commands refuses rather than judging the candidate under advice nobody sealed
obligation-theatre | the recorded obligation answers against the six hard gates | a blank or whitespace answer is refused, the six gates are unchanged, and result.json marks obligation answers as recorded judgement
exit-code-interface | the corpus refusals against the published codes 10 to 60 | corpus refusals exit 20 with a structured reason field, and the existing per-gate codes keep their firing conditions under the current tests
binding-digest | hermes.py against its pinned SHA-256 in the Promise Machine coverage | the coverage digest and any new promise heading land in the same commit as the source change
citation-network | the 40 reference URLs against the harness boundary | citations are recorded data, never fetched, and the harness opens no socket
class-mapping-error | each rule's declared Hermes class against what the rule actually changes | the mapping is reviewed rule by rule in the audit round, and a rule with no source-level candidate maps to none and is refused as a candidate with that reason
```

The audit loop should look hardest at frontier-displacement, scope-false-refusal and class-mapping-error. The first is the one a later reader will most easily mistake for a rolling target, since the marketplace's own published sentence tells them a job changes only when that exact job completed, and the epoch row is the only thing that makes this run's move legible instead. The other two are authored fields rather than transcribed ones, so no schema check can catch a wrong value, and both fail in the direction that refuses a correct candidate or admits one the target's compiler cannot support.

## 6. Glossary seeds

- Rule id: one of the document's 120 identifiers, such as `STO-09`, adopted verbatim as the public selector.
- Myth id: one of the 28 `MYTH-NN` entries in the document's rejected-rules table, refusable as a justification and never selectable as a rule.
- Hermes class: one of the twelve existing `OPTIMISATION_CLASSES`, or none for a rule that constrains the run rather than changing source.
- Declared scope: the compiler range, fork floor and pipeline set over which a rule's mechanism holds, each with a stated reason, as distinct from the single 0.8.25 and Cancun pins the document was written against.
- Fork order: the authored ordering of EVM fork names the scope gate compares against, with an unknown name refusing rather than passing.
- Obligation answer: the recorded text answering one of a rule's proof obligations, marked in the evidence as judgement rather than measurement.
- Corpus digest: the SHA-256 of the corpus file, sealed at Gate 1 and written into `result.json`, so an accepted candidate names the advice that judged it.
- Displaced target: a held frontier job that a maintainer decision moves off the frontier without completing it, recorded as an epoch boundary and reopened as a candidate successor.

## 7. Sources

- The reference document supplied for this run, SHA-256 `297c926dc0a2e011e31da5245273c136273b8faa390f3691910c22c870068449`, 1188 lines, 120 rules, 28 rejected rules, 40 citations.
- `plugins/hermes/skills/hermes/SKILL.md`, `scripts/hermes.py`, `scripts/test_hermes.py`, `references/optimisation-catalogue.md`, `EVOLUTION.md`, `plugins/hermes/AGENTS.md`, `plugins/hermes/README.md`
- `plugins/hexaemeron/skills/VERSIONING.md`, for the axis definitions, the frontier-hold rule and the reopening boundary
- `tests/promise_machine_coverage.json`, `tests/test_promise_machine_contract.py`, `tests/test_evolution_contract.py`, `tests/test_marketplace_prose.py`, `tests/test_shipped_prose_lints.py`, `tests/test_version_propagation.py`
- `audit/AUDIT.md`, which holds no Hermes round
- [skills#95](https://github.com/wildcat-finance/skills/pull/95), [skills#22](https://github.com/wildcat-finance/skills/pull/22), [skills#21](https://github.com/wildcat-finance/skills/issues/21), [skills#23](https://github.com/wildcat-finance/skills/issues/23)
- `forge config --json` observed in `plugins/pandects` and in an unpinned scratch root, which is where assumption 8 and the scope-false-refusal risk come from

## 8. Signals, and the questions behind them

Two questions, both asked of a run that already finished, and both answered by the step that adds the Gate 2 binding.

- Which corpus and which rule judged this accepted candidate? Answered by the corpus digest and rule id in `result.json`, beside the existing class and target set.
- Why did this run refuse before any Forge test or snapshot ran? Answered by the structured refusal reason in `result.json` and the same text on stderr, naming the rule and the failed condition.

No alert and no unattended path: Hermes is invoked from a terminal in the user's target repository and writes its record there. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal carries.

## 9. Boundaries, per capability

- Reading the corpus. The path is fixed relative to the script rather than taken from the caller, the content is schema-validated before use, and no record is imported or evaluated as code.
- Rule ids and obligation text reaching the process. Ids are matched against a strict pattern before they select anything, obligation and rationale text is recorded as JSON data and never interpolated into a command, and the existing list-form subprocess calls are unchanged.
- The 40 citation URLs. Recorded data only. The harness fetches nothing and opens no socket, and this run adds no dependency that would.
- The scope gate's input. It reads the Foundry configuration the baseline already sealed, so it opens no boundary the run did not already have.

[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary rules, and its lint runs each round.

## 10. The budget, or its absence

One budget, because the corpus is the first data file the harness loads on every `verify`, and a slow gate gets skipped.

```bash
time python3 plugins/hermes/skills/hermes/scripts/hermes.py corpus --validate
time python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
```

Full corpus validation stays under one second, and the Hermes suite stays under 25 seconds against the 10.7 seconds it takes today. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns how a budget is measured and what a breach costs.

## 11. The fail-closed posture

Seven new refusals stop the run at Gate 2 with exit `20` and a structured reason: an unknown rule id, a myth cited as justification, a declared class disagreeing with the rule's class, a rule outside the resolved scope, a scope that cannot be resolved because `solc` is null or the fork name is unknown, a proof obligation with no substantive answer, and a corpus digest that moved since the baseline sealed it. A corpus that fails its own validation refuses the same way, so a corrupt corpus cannot admit a candidate. Each refusal ships with the test that fails without its check, which is the guard convention [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns, and the standing guards are the Hermes suite, the evolution suite over both new ledger rows, the marketplace-prose suite over the six frontier surfaces, the Promise Machine contract test over the promise headings, and the shipped-prose lint over every changed document.

## 12. Decisions and their homes

Five decisions are expensive to reverse, and the first two are the ones a later reader will most need explained.

- The held `live-evidence-bundle` target is displaced by maintainer decision rather than completed, and the corpus becomes the frontier. Recorded as a decision record under `docs/decisions/`, and as the epoch row's change text, because the marketplace publishes the opposite default in every landing README and a displacement with no record reads later as a rolling target.
- `--rule` becomes required, breaking every existing invocation. Recorded in the same decision record as the compatibility half of the same boundary, with the dropped escape hatch from item 4 named as the rejected alternative.
- The corpus adopts the document's identifiers verbatim as its public namespace, and scope becomes a declared range with a stated reason rather than the document's literal 0.8.25 and Cancun pins. Recorded in a second decision record, because the namespace is what every later citation depends on and the scope model is the part a reader would otherwise reconstruct wrongly from the document's own header.
- Corpus refusals keep exit code `20` and carry a structured reason rather than minting a seventh code. Recorded in that second record, with the rejected alternative stated: a new code would read as a seventh gate that does not exist.
- The corpus is data with generated prose rather than a shipped document. Recorded in the evolution row and in this study, since the reason is the lint scope stated in assumption 6 rather than a design preference.

[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where each one lives.

### Amendment -- 2026-08-21

**What changed.** Three things, all settled by reading the controller rather than the contract prose. First, the ledger takes one row, not two: an epoch row `hermes-v0.1.1` whose change text records the reopening, carrying the new revision, gap, next job and digest. The evolution counter stays where it is, because the contract reserves it for completing a held job and the held evidence-bundle job is not what this run completes. Second, the starting ref moves from `87e213c19e64687406d7ba7601e093929bb3d813` to `0bfad60bb482245dd08d9747139d26824392a2c7`. Third, the frontier sentence moves once rather than twice, since one row means one prose sweep.

**Why.** `hexctl`'s `frontier_close_fault` refuses a declared ledger that gained other than exactly one history row, and refuses an epoch row that moves the digest without the word `reopen` in its evidence or change text. Fiat's hard rules also state that an epoch is the axis that may replace a held next job, which settles the reading assumption 2 left open in favour of the epoch and against a generation. On the base: `origin/main` advanced nine commits ahead of the local ref while this study was being written, all of them Hypomnema's H007 alert-runbook shape check. None of them touches Hermes, `VERSIONING.md`, or the four root suites this study depends on, and the `hermes.py` digest pinned in `tests/promise_machine_coverage.json` still matches the file, so every other fact on this page survives the move. The local `main` is checked out in another worktree and cannot be fast-forwarded from here without disturbing it, so the run branch is cut from `origin/main` at that SHA and `main` stays the base the run merges into once.

**Steps touched.** None. No step exists yet; the runbook is derived from this amended study, and assumptions 1, 2 and 3 above are read as amended here.

**Still holding.** Every other item. The problem statement, the chosen design and its rejected alternatives, the seven Gate 2 refusals, the corpus digest sealed at Gate 1, the required rule flag and the dropped escape hatch, the risk register, the boundary tiers, the budget, and the six frontier surfaces are unchanged. The `frontier-displacement` and `successor-judgement` risk lines still apply and now read against one row rather than two.
