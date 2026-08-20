# Runbook: A structured risk-register block the warden can enumerate

Derived from `.hexaemeron/study.md`. Two steps, dependency order.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The study and runbook this run builds from are committed where the next study will find them, the study carrying the first risk-register block.
**Entry.** The run branch `fiat/a-structured-risk-register-block-the-warden-can` at `main` (`75fc3d3`), clean tree.
**Exit.** `docs/protasis-risk-register-block-study.md` and `docs/protasis-risk-register-block-runbook.md` exist as committed copies; the imprimatur lint scores 100.0 on both; `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-risk-register-block-study.md` exits 0; `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0; both suites pass at their base state.
**Files.** `docs/protasis-risk-register-block-study.md`, `docs/protasis-risk-register-block-runbook.md`.
**Tests.** None written; both suites run to prove the tree stayed green.
**Disciplines.** phylax: none, a docs-only commit opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: none new this step; the run's decision lands in the ledger row in step 2 and this step commits the reasoning it points at.

## Step 2: Define the block in item 5 and cut the generation row

**Goal.** Item 5 states the fenced risk-register block's form, and the ledger records the change as one generation row.
**Entry.** Step 1's exit state.
**Exit.** `grep -n "risk-register" plugins/hexaemeron/skills/protasis/SKILL.md` shows the fenced form in item 5; frontmatter reads `version: "3.4.0"`; `EVOLUTION.md` current version reads `protasis-v3.4.0` with one new generation row holding revision `risk-register-block-check` and digest `07e36d6220ef941bb35f82419f0491489a24e3b265bc86ec90a2ee7aa9137aef` byte for byte; `python3 -m unittest discover -s tests` passes and `python3 plugins/hexaemeron/tests/run_tests.py` reports only the two recorded environment failures.
**Files.** `plugins/hexaemeron/skills/protasis/SKILL.md`, `plugins/hexaemeron/skills/protasis/EVOLUTION.md`.
**Tests.** None written; the evolution and shipped-prose suites are the guard, and both suites run as the proof.
**Disciplines.** phylax: none, a markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: the field order and separator are expensive to reverse once the held check ships; the record is this run's generation row in `EVOLUTION.md`, pointing at the committed study.
