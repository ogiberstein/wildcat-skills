# Runbook: Resolve ADR references made from source comments

Derived from the study of the same name. Two steps, one pull request each,
stacked on the run branch `fiat/resolve-adr-references-made-from-source-comments`
off `main` at `0d5cf1ae68fa3d1ba3a364dcd84eee28adb3beea`.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The run's spec is a reviewed artefact in the tree rather than a run-state file.
**Entry.** The run branch at `0d5cf1ae68fa3d1ba3a364dcd84eee28adb3beea`, a clean tree.
**Exit.** Both committed documents pass their checks and the tree's guards hold:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/hypomnema-source-comment-references-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/hypomnema-source-comment-references-runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `docs/hypomnema-source-comment-references-study.md`, `docs/hypomnema-source-comment-references-runbook.md`, `.horos/boundary.json` (regenerated for the two new paths).
**Tests.** None new; both suites run as the regression net.
**Disciplines.** hypomnema: the committed study is the standing source the step 2 ledger row points at. phylax: none, a markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand.

## Step 2: Widen the walk to source comments and cut the evolution row

**Goal.** The lint reports a source comment citing a record the index does not hold, and the ledger advances to `hypomnema-v3.2.0` with one evidenced successor job.
**Entry.** Step 1's exit state, on a branch cut from the step 1 branch.
**Exit.** The demo path from the study's problem statement:

```bash
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/hexaemeron/tests/fixtures/hypomnema; test $? -eq 1
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, `plugins/hexaemeron/tests/test_hypomnema_checker.py`, `plugins/hexaemeron/tests/fixtures/hypomnema/source/*` (new fixtures), `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`, `tests/promise_machine_coverage.json` (binding digest moves with its surface), `.horos/boundary.json`.
**Tests.** A source-references class in `test_hypomnema_checker.py`: a dangling reference from a `#` comment and a `//` comment, a resolving reference, a block-comment reference, string-literal and URL non-findings, the trailing-comment case, pragma suppression, fixture coverage and the tree walk staying clean. Expected around twelve new cases.
**Disciplines.** phylax: the lint now opens source files from the caller's argument list, still with no subprocess and no socket, and an unreadable file is reported rather than skipped. hypomnema: the marker rule and the successor frontier land in the ledger row this step cuts. elenchus: the PM071 binding-surface refusal is expected on the SKILL.md edit and takes the checker's own remedy if it fires. metron: none, no performance claim. ephoros: none, nothing runs unattended.
