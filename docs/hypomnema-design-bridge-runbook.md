# Runbook: Each study's chosen design becomes a standing record

Derived from `.hexaemeron/study.md`. Two steps, dependency order.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The study and runbook this run builds from are committed where the next study will find them.
**Entry.** The run branch `fiat/each-study-s-chosen-design-becomes-a-standing-re` at `main` (`f004754`), clean tree.
**Exit.** `docs/hypomnema-design-bridge-study.md` and `docs/hypomnema-design-bridge-runbook.md` exist as committed copies; the imprimatur lint scores 100.0 on both; `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/hypomnema-design-bridge-study.md` exits 0; `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0; both suites pass at their base state.
**Files.** `docs/hypomnema-design-bridge-study.md`, `docs/hypomnema-design-bridge-runbook.md`.
**Tests.** None written; both suites run to prove the tree stayed green.
**Disciplines.** phylax: none, a docs-only commit opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: none new this step; the run's decision lands in the ledger row in step 2 and this step commits the reasoning it points at.

## Step 2: State the bridge, cut the generation row

**Goal.** The contract states the prose-phase bridge rule and its checklist line, and the ledger records the change as one generation row.
**Entry.** Step 1's exit state.
**Exit.** `grep -n "chosen design" plugins/hexaemeron/skills/hypomnema/SKILL.md` shows the bridge rule and one pre-receipt checklist line; frontmatter reads `version: "1.2.0"`; `EVOLUTION.md` current version reads `hypomnema-v1.2.0` with one new generation row holding revision `adr-shape-check` and digest `5c69c143dc7adb1380e27931e5440e9772b184b96fc5964f3fb5a722d3ac59f9` byte for byte; the Promise Machine coverage digest moves with the reviewed surface and `python3 scripts/promise_machine.py check` returns clean; `python3 -m unittest discover -s tests` passes and `python3 plugins/hexaemeron/tests/run_tests.py` reports only the two recorded environment failures.
**Files.** `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`, `tests/promise_machine_coverage.json`.
**Tests.** None written; the evolution, shipped-prose and coverage suites are the guard, and both suites run as the proof.
**Disciplines.** phylax: none, markdown and one pinned digest. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: the point-or-write shape is expensive to reverse; the record is this run's generation row in `EVOLUTION.md`, pointing at the committed study.
