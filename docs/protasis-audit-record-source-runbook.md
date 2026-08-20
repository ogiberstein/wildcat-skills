# Runbook: Protasis names the audit record as a study source

Derived from `.hexaemeron/study.md`. Two steps, dependency order. Committed copies land under `docs/` in step 1.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The study and runbook this run builds from are committed where the next study will find them.
**Entry.** The run branch `fiat/protasis-names-the-audit-record-as-a-study-sourc` at `main` (`b26181b`), clean tree, both suites green.
**Exit.** `docs/protasis-audit-record-source-study.md` and `docs/protasis-audit-record-source-runbook.md` exist as committed copies; `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` scores 100.0 on both; `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0; `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py` pass.
**Files.** `docs/protasis-audit-record-source-study.md`, `docs/protasis-audit-record-source-runbook.md`.
**Tests.** None written; both suites run to prove the tree stayed green.
**Disciplines.** phylax: none, no input path, subprocess or secret in a docs-only commit. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: none new, the decision record is the ledger row in step 2; this step only lands the reasoning the row will point at.

## Step 2: Name the audit record in item 2 and cut the generation row

**Goal.** Protasis item 2 names the audit records of every in-scope skill as a source read before design options are drawn, and the ledger records the change as one generation row.
**Entry.** Step 1's exit state: docs committed, suites green.
**Exit.** `grep -n "audit record" plugins/hexaemeron/skills/protasis/SKILL.md` shows the named source in item 2 and one pre-receipt checklist line; frontmatter reads `version: "2.3.0"`; `EVOLUTION.md` current version reads `protasis-v2.3.0` with one new generation row holding revision `study-schema-check` and digest `8ebcb385fa9725b25221f1d170ad1b88a4327154e5bab2fe85f975488b66c54e` byte for byte; `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py` pass.
**Files.** `plugins/hexaemeron/skills/protasis/SKILL.md`, `plugins/hexaemeron/skills/protasis/EVOLUTION.md`.
**Tests.** None written; the existing evolution and version-propagation tests are the guard, and both suites run as the proof.
**Disciplines.** phylax: none, a markdown diff opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: the widen-not-add decision is expensive to reverse once the schema check ships; its record is this run's generation row in `EVOLUTION.md`, pointing at the committed study.
