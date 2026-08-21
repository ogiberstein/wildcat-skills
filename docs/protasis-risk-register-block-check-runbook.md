# Runbook: Check the risk-register block the study contract fixes

Derived from the study of the same name. Two steps, one pull request each,
stacked on the run branch `fiat/check-the-risk-register-block-the-study-contract`
off `main` at `3c061c2e15df085cf300220250b421bbd03f664c`.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The run's spec is a reviewed artefact in the tree rather than a run-state file.
**Entry.** The run branch at `3c061c2e15df085cf300220250b421bbd03f664c`, a clean tree.
**Exit.** Both committed documents pass their checks and the tree's guards hold:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-risk-register-block-check-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/protasis-risk-register-block-check-runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `docs/protasis-risk-register-block-check-study.md`, `docs/protasis-risk-register-block-check-runbook.md`, `.horos/boundary.json` (regenerated for the two new paths).
**Tests.** None new; both suites run as the regression net.
**Disciplines.** hypomnema: the committed study is the standing source the step 2 ledger row points at. phylax: none, a markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand.

## Step 2: Ship the register check, its fixtures and the evolution row

**Goal.** `--study` fails a study whose risk-register seed does not carry the fixed shape, and the ledger advances to `protasis-v4.5.0` with one evidenced successor job.
**Entry.** Step 1's exit state, on a branch cut from the step 1 branch.
**Exit.** The demo path from the study's problem statement:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/hexaemeron/tests/fixtures/protasis/malformed-register-study.md; test $? -eq 1
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-risk-register-block-study.md docs/protasis-risk-register-block-check-study.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/protasis/scripts/protasis.py`, `plugins/hexaemeron/tests/test_protasis_checker.py`, `plugins/hexaemeron/tests/fixtures/protasis/malformed-register-study.md`, `plugins/hexaemeron/skills/protasis/SKILL.md`, `plugins/hexaemeron/skills/protasis/EVOLUTION.md`, `docs/protasis-study-schema-check-study.md` (allow pragma on item 5), `.horos/boundary.json`.
**Tests.** A register class in `test_protasis_checker.py`: one case per fault (no block, empty block, wrong field count high and low, non-kebab id, duplicate id, empty boundary, empty check), the fence and duplicate-item no-verdict guards, suppression, fixture coverage, and the two shipped studies passing. Expected around fourteen new cases.
**Disciplines.** phylax: the checker reads caller-named paths, and the new scanner keeps the bounded read, no subprocess and no socket. hypomnema: the code numbering and the successor frontier land in the ledger row this step cuts. metron: none, no performance claim. ephoros: none, nothing runs unattended. elenchus: none, no failure in hand.
