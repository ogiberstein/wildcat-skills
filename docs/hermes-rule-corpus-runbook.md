# Runbook: A pinned gas-rule corpus Hermes enforces

Derived from the study of the same name, as amended on 2026-08-21. Six steps,
one pull request each, stacked on the run branch
`fiat/a-pinned-gas-rule-corpus-hermes-enforces` cut from `origin/main` at
`0bfad60bb482245dd08d9747139d26824392a2c7`, with `main` as the single merge
target at the end.

Steps 3 and 4 split the 120-rule transcription in half on purpose. Each half is
one audit round of the same kind of review, rule by rule, against the two
authored fields the study's risk register calls out; one round of 120 records
is the shape that gets skimmed.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The run's spec is a reviewed artefact in the tree rather than a controller state file.
**Entry.** The run branch at `0bfad60bb482245dd08d9747139d26824392a2c7`, a clean tree.
**Exit.** Both committed documents pass their checks and the tree's guards hold:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/hermes-rule-corpus-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/hermes-rule-corpus-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 -m unittest discover -s tests
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
```

**Files.** `docs/hermes-rule-corpus-study.md`, `docs/hermes-rule-corpus-runbook.md`, `.horos/boundary.json` (regenerated for the two new paths).
**Tests.** None new; the root suite and the Hermes suite run as the regression net.
**Disciplines.** hypomnema: the committed study is the standing source the step 6 ledger row and both decision records point at. phylax: none, a Markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand.

## Step 2: The schema, the validator, and the refusal data

**Goal.** `hermes.py corpus --validate` holds a corpus file to a pinned schema, and the 28 rejected universal rules and 40 citations are in the tree with the source document they came from.
**Entry.** Step 1's exit state, on a branch cut from the step 1 branch.
**Exit.** The validator passes over the refusal data and refuses a corrupted copy:

```bash
python3 plugins/hermes/skills/hermes/scripts/hermes.py corpus --validate
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
shasum -a 256 docs/hermes-rule-corpus/reference-solidity-0.8.25.md
```

The last command has to print `297c926dc0a2e011e31da5245273c136273b8faa390f3691910c22c870068449`.
The document commits byte for byte, including the two lines that end in whitespace. No committed check runs `git diff --check` here, and tidying those lines would break the digest the corpus cites, so the round leaves them alone.

**Files.** `plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json`, `plugins/hermes/skills/hermes/references/gas-rule-corpus.json` (myths, references, and an empty rule list), `plugins/hermes/skills/hermes/scripts/hermes.py` (the `corpus` subcommand), `plugins/hermes/skills/hermes/scripts/test_hermes.py`, `docs/hermes-rule-corpus/reference-solidity-0.8.25.md` (the pinned source, byte for byte), `tests/promise_machine_coverage.json` (the `hermes.py` digest moves with the source), `.horos/boundary.json`.
**Tests.** A corpus class in `test_hermes.py`: schema acceptance, an unknown field refused, a duplicate id refused, a myth id whose correction is empty refused, a citation id that resolves to two URLs refused, the 28 and 40 counts asserted, and a citation written at the start of a line counted as a use rather than a definition. Expected around ten new cases, on top of the existing fourteen.
**Disciplines.** phylax: this step opens the corpus read, so the path is fixed relative to the script, the content is schema-validated before use, and no record is imported or evaluated. hypomnema: the schema file is the interface a later promise pins, and its shape is recorded in the study rather than invented here. elenchus: the Promise Machine binding-digest refusal is expected on the `hermes.py` edit and takes the checker's own remedy if it fires. ephoros: none, nothing runs unattended. metron: none, the budget claim belongs to step 5 where the corpus is loaded on every verify.

## Step 3: The first 61 rules

**Goal.** The `CMP`, `STO`, `TRN` and `MEM` rules are in the corpus, each tracing to its source section, each carrying its Hermes class or none, and each carrying a declared scope with the reason for its bounds.
**Entry.** Step 2's exit state, on a branch cut from the step 2 branch.
**Exit.** The validator passes over the larger corpus and the counts are asserted:

```bash
python3 plugins/hermes/skills/hermes/scripts/hermes.py corpus --validate
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s tests
```

**Files.** `plugins/hermes/skills/hermes/references/gas-rule-corpus.json`, `plugins/hermes/skills/hermes/scripts/test_hermes.py`, `.horos/boundary.json`.
**Tests.** Per-section counts asserted at 12, 27, 7 and 16; every rule's class resolving to one of the twelve or to none; every rule carrying a source section, a scope range, a fork floor and a stated reason per bound; every automation value inside `safe`, `guarded`, `never`; every evidence grade inside `A`, `B`, `C`, `X`. Expected around six new cases.
**Disciplines.** hypomnema: the identifier namespace becomes public here, and the decision record naming it is cut in step 6 against this data. elenchus: a transcription fault found in the round is worked to its cause in the source section rather than patched in the record. phylax: none beyond step 2's corpus read, which this step only feeds. ephoros: none, nothing runs unattended. metron: none, no performance claim.

## Step 4: The remaining 58 rules

**Goal.** The `CTL`, `EXT`, `DEP` and `YUL` rules complete the corpus at 120.
**Entry.** Step 3's exit state, on a branch cut from the step 3 branch.
**Exit.** The complete corpus validates and the total is asserted:

```bash
python3 plugins/hermes/skills/hermes/scripts/hermes.py corpus --validate
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s tests
```

**Files.** `plugins/hermes/skills/hermes/references/gas-rule-corpus.json`, `plugins/hermes/skills/hermes/scripts/test_hermes.py`, `.horos/boundary.json`.
**Tests.** Per-section counts asserted at 18, 14, 12 and 14, the total asserted at 120, and every rule id in the source document present in the corpus exactly once. Expected around five new cases.
**Disciplines.** hypomnema: same namespace decision as step 3, now complete. elenchus: as step 3, a transcription fault goes back to its source section. phylax: none beyond the corpus read. ephoros: none, nothing runs unattended. metron: none, no performance claim.

## Step 5: Seal the corpus at Gate 1 and require a rule at Gate 2

**Goal.** `baseline` seals the corpus digest beside the Foundry configuration, `verify` requires `--rule`, and the seven refusals in the study's item 11 each stop the run at Gate 2 with a structured reason before any Forge test or snapshot runs.
**Entry.** Step 4's exit state, on a branch cut from the step 4 branch.
**Exit.** The refusals fire, the accepted record carries the corpus fields, and the budget holds:

```bash
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
time python3 plugins/hermes/skills/hermes/scripts/hermes.py corpus --validate
```

The timed command stays under one second and the Hermes suite stays under 25 seconds, both compared against the recorded 10.7 seconds the suite takes at the run's base.

**Files.** `plugins/hermes/skills/hermes/scripts/hermes.py`, `plugins/hermes/skills/hermes/scripts/test_hermes.py`, `plugins/hermes/skills/hermes/SKILL.md` (the command contract, the required flag, and the new promise heading), `tests/promise_machine_coverage.json`, `tests/test_promise_machine_contract.py`, `.horos/boundary.json`.
**Tests.** One case per refusal: unknown rule id, myth cited as justification, declared class disagreeing with the rule's class, rule outside the resolved scope, scope unresolvable because `solc` is null, scope unresolvable because the fork name is unknown, obligation answer blank, corpus digest moved since the baseline, and a `verify` call omitting `--rule` altogether. Plus an accepted run whose `result.json` carries the corpus digest, the rule id and the obligation answers, and a case proving a fork floor of `cancun` is satisfied by `osaka` rather than refused. Expected around eleven new cases.
**Disciplines.** phylax: rule ids and obligation text reach the process here, so ids are pattern-matched before they select anything and text is recorded as JSON data, never interpolated into a command. metron: the budget in the study's item 10 is claimed by this step, so it is measured before and after rather than asserted. ephoros: `result.json` gains the two fields that answer the study's item 8 questions. hypomnema: the exit-code decision and the required-flag decision are cut in step 6 against this implementation. elenchus: the Promise Machine coverage and contract refusals are expected on this diff and take their own remedies.

## Step 6: Record the decisions, close the frontier, and demonstrate

**Goal.** Two decision records stand, the catalogue points at the corpus, the six frontier surfaces carry one agreed successor, the ledger gains its single epoch row, and the demo path from the study runs clean.
**Entry.** Step 5's exit state, on a branch cut from the step 5 branch.
**Exit.** The demo path from the study's problem statement, plus every guard the changed surfaces incur:

```bash
python3 plugins/hermes/skills/hermes/scripts/hermes.py corpus --validate
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
```

**Files.** `docs/decisions/ADR-007-displace-the-hermes-evidence-bundle-target.md`, `docs/decisions/ADR-008-adopt-the-source-document-rule-namespace.md`, `plugins/hermes/skills/hermes/EVOLUTION.md` (the epoch row `hermes-v0.1.1`), `plugins/hermes/skills/hermes/SKILL.md`, `plugins/hermes/skills/hermes/references/optimisation-catalogue.md`, `plugins/hermes/AGENTS.md`, `plugins/hermes/README.md`, `README.md`, `.horos/boundary.json`.
**Tests.** No new test file; the standing guards are the evolution suite over the epoch row, the marketplace-prose suite over the six frontier surfaces and the uniqueness of the landing README's job topic, the shipped-prose lint over every changed document, and the hypomnema shape codes over both decision records.
**Disciplines.** hypomnema: this step is the record, so the two decision records and the ledger row are its whole subject, and each takes the template shape the record lint holds. ephoros: none, nothing runs unattended. phylax: none, a prose and ledger diff opens no boundary. metron: none, the budget was measured in step 5. elenchus: the evolution row arithmetic and the frontier-agreement suite are the two most likely failures here, and each is worked to its cause rather than by adjusting a row until a test passes.
