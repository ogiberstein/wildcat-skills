# Runbook: Ship the protasis study schema check

Derived from `.hexaemeron/study.md`. Three steps, dependency order.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The study and runbook this run builds from are committed where the next study will find them.
**Entry.** The run branch `fiat/ship-the-protasis-study-schema-check` at `main` (`68ddc3c`), clean tree, suites at their base state.
**Exit.** `docs/protasis-study-schema-check-study.md` and `docs/protasis-study-schema-check-runbook.md` exist as committed copies; the imprimatur lint scores 100.0 on both; `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0; `python3 -m unittest discover -s tests` passes and `python3 plugins/hexaemeron/tests/run_tests.py` reports only the two recorded environment failures.
**Files.** `docs/protasis-study-schema-check-study.md`, `docs/protasis-study-schema-check-runbook.md`.
**Tests.** None written; both suites run to prove the tree stayed green.
**Disciplines.** phylax: none, a docs-only commit opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: none new this step; the run's decisions land in the ledger row in step 3 and this step commits the reasoning they point at.

## Step 2: The study mode, its fixtures and its tests

**Goal.** `protasis.py --study` fails a study missing any of the twelve items, and one whose items 8 through 12 answer with silence or a bare none.
**Entry.** Step 1's exit state.
**Exit.** `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-study-schema-check-study.md` exits 0; the same command over a fixture missing an item exits 1 naming S001; `python3 plugins/hexaemeron/tests/run_tests.py` reports the new study cases passing and only the two recorded environment failures; `python3 -m unittest discover -s tests` passes.
**Files.** `plugins/hexaemeron/skills/protasis/scripts/protasis.py`, `plugins/hexaemeron/tests/test_protasis_checker.py`, fixtures under `plugins/hexaemeron/tests/fixtures/protasis/`.
**Tests.** Study cases in `test_protasis_checker.py`: a complete study clean; each of the twelve items removed caught as S001; for items 8 through 12, an empty answer and a bare none each caught as S002 and a stated none with its reason passing; S000 on an unreadable path; S003 on a document with no item; S004 on a duplicate item number; a fenced quotation of an item heading not counted; the runbook mode's existing cases unchanged.
**Disciplines.** phylax: the check reads caller-named paths, so the existing refusals (regular files only, byte cap, no subprocess, no socket) must hold in the new mode. ephoros: none, a terminal lint has no unattended signal. metron: none, no performance claim. elenchus: any case that fails mid-step is reduced and guarded in the same test module. hypomnema: none this step; the S-code decision is recorded in step 3's ledger row.

## Step 3: Name the check in the contract, cut the evolution row, demonstrate

**Goal.** The protasis contract names its mechanical subset, the ledger closes `study-schema-check` with one evolution row holding the next frontier judgement, and the demo path from the problem statement runs.
**Entry.** Step 2's exit state.
**Exit.** `plugins/hexaemeron/skills/protasis/SKILL.md` carries a mechanical-subset section naming both modes and frontmatter `version: "3.3.0"`; `EVOLUTION.md` current version reads `protasis-v3.3.0` with one new evolution row whose digest matches the new frontier line; the demo path runs: `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-study-schema-check-study.md` exits 0, `python3 -m unittest discover -s tests` passes, `python3 plugins/hexaemeron/tests/run_tests.py` reports only the two recorded environment failures.
**Files.** `plugins/hexaemeron/skills/protasis/SKILL.md`, `plugins/hexaemeron/skills/protasis/EVOLUTION.md`.
**Tests.** None written; the evolution suite guards the row and both suites run as the proof.
**Disciplines.** phylax: none, a markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: the frontier judgement and the S-code interface decision are expensive to reverse and land in `EVOLUTION.md`, the ledger the contract names for decisions about a governed skill.
