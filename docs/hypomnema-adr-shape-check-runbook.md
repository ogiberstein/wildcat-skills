# Runbook: Lint the shape of the decision records

Derived from the study of the same name. Three steps, one pull request each,
stacked on the run branch `fiat/lint-the-shape-of-the-decision-records`
off `main` at `8d5079b43276d6e4f26df58e9e32411ae2898c43`.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The run's spec is a reviewed artefact in the tree rather than a run-state file.
**Entry.** The run branch at `8d5079b43276d6e4f26df58e9e32411ae2898c43`, a clean tree.
**Exit.** Both committed documents pass their checks and the tree's guards hold:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/hypomnema-adr-shape-check-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/hypomnema-adr-shape-check-runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `docs/hypomnema-adr-shape-check-study.md`, `docs/hypomnema-adr-shape-check-runbook.md`, `.horos/boundary.json` (regenerated for the two new paths).
**Tests.** None new; both suites run as the regression net.
**Disciplines.** hypomnema: the committed study is the standing source the step 3 ledger row points at. phylax: none, a markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand.

## Step 2: Fill the two alternatives sections from the authorship trail

**Goal.** ADR-002 and ADR-004 carry the alternatives their authorship trail records, so the tree passes the rule step 3 ships.
**Entry.** Step 1's exit state, on a branch cut from the step 1 branch.
**Exit.** Both records carry all five sections with their content otherwise untouched:

```bash
grep -c '^## Alternatives' docs/decisions/ADR-002-use-one-portable-promise-machine-router.md docs/decisions/ADR-004-release-the-promise-machine-without-moving-skill-frontiers.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `docs/decisions/ADR-002-use-one-portable-promise-machine-router.md`, `docs/decisions/ADR-004-release-the-promise-machine-without-moving-skill-frontiers.md`.
**Tests.** None new; the lint and both suites prove the records still resolve.
**Disciplines.** hypomnema: the sections record another run's rejected options, lifted from `docs/promise-machine/study.md` rather than invented. phylax: none, a markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand.

## Step 3: Ship the shape rule, its fixtures and the evolution row

**Goal.** The lint fails a record missing the dated status or one of the five sections, and the ledger advances to `hypomnema-v2.2.0` with one evidenced successor job.
**Entry.** Step 2's exit state, on a branch cut from the step 2 branch.
**Exit.** The demo path from the study's problem statement:

```bash
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/hexaemeron/tests/fixtures/hypomnema/decisions; test $? -eq 1
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, `plugins/hexaemeron/tests/test_hypomnema_checker.py`, `plugins/hexaemeron/tests/fixtures/hypomnema/decisions/*` (new fixtures), `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`, `.horos/boundary.json`.
**Tests.** A record-shape class in `test_hypomnema_checker.py`: one case per omission (each of the five sections, undated status), the non-record and fenced-heading false-positive guards, suppression, fixture coverage, and the tree's six records passing. Expected around twelve new cases.
**Disciplines.** phylax: the lint keeps reading caller-named trees with no subprocess and no socket. hypomnema: the code numbering and the successor frontier land in the ledger row this step cuts. elenchus: the PM071 binding-surface refusal from the prior run is expected on the SKILL.md edit and is worked with the checker's own remedy if it fires. metron: none, no performance claim. ephoros: none, nothing runs unattended.
