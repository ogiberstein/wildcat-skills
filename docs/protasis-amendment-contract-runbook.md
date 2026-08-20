# Runbook: The mid-run spec amendment contract

Derived from `.hexaemeron/study.md`. Two steps, dependency order.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The study and runbook this run builds from are committed where the next study will find them.
**Entry.** The run branch `fiat/the-mid-run-spec-amendment-contract` at `main` (`54431ba`), clean tree.
**Exit.** `docs/protasis-amendment-contract-study.md` and `docs/protasis-amendment-contract-runbook.md` exist as committed copies; the imprimatur lint scores 100.0 on both; `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-amendment-contract-study.md` exits 0; `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0; both suites pass at their base state.
**Files.** `docs/protasis-amendment-contract-study.md`, `docs/protasis-amendment-contract-runbook.md`.
**Tests.** None written; both suites run to prove the tree stayed green.
**Disciplines.** phylax: none, a docs-only commit opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: none new this step; the run's decision lands in the ledger row in step 2 and this step commits the reasoning it points at.

## Step 2: State the amendment contract and cut the generation row

**Goal.** "The spec stays alive" states the dated delta block, the refusal, and where the forcing decision is recorded, and the ledger records the change as one generation row.
**Entry.** Step 1's exit state.
**Exit.** `grep -n "Amendment" plugins/hexaemeron/skills/protasis/SKILL.md` shows the dated block and its four fields in "The spec stays alive"; frontmatter reads `version: "3.5.0"`; `EVOLUTION.md` current version reads `protasis-v3.5.0` with one new generation row holding revision `risk-register-block-check` and digest `07e36d6220ef941bb35f82419f0491489a24e3b265bc86ec90a2ee7aa9137aef` byte for byte; `python3 -m unittest discover -s tests` passes and `python3 plugins/hexaemeron/tests/run_tests.py` reports only the two recorded environment failures.
**Files.** `plugins/hexaemeron/skills/protasis/SKILL.md`, `plugins/hexaemeron/skills/protasis/EVOLUTION.md`.
**Tests.** None written; the evolution and shipped-prose suites are the guard, and both suites run as the proof.
**Disciplines.** phylax: none, a markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: the append-only convention is expensive to reverse once studies carry blocks; the record is this run's generation row in `EVOLUTION.md`, pointing at the committed study.
