# Runbook: The first decision records and their convention

Derived from `.hexaemeron/study.md`. Three steps, dependency order.

## Step 1: Scaffold: commit the study and runbook

**Goal.** The study and runbook this run builds from are committed where the next study will find them.
**Entry.** The run branch `fiat/the-first-decision-records-and-their-convention` at `main` (`f12f23f`), clean tree.
**Exit.** `docs/hypomnema-first-records-study.md` and `docs/hypomnema-first-records-runbook.md` exist as committed copies; the imprimatur lint scores 100.0 on both; `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/hypomnema-first-records-study.md` exits 0; `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0; both suites pass at their base state.
**Files.** `docs/hypomnema-first-records-study.md`, `docs/hypomnema-first-records-runbook.md`.
**Tests.** None written; both suites run to prove the tree stayed green.
**Disciplines.** phylax: none, a docs-only commit opens no boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: none new this step; the run's decisions land in the records and the ledger row of later steps.

## Step 2: The two records, and one shape across all six

**Goal.** ADR-005 records the Pashov vendoring boundary, ADR-006 records why skill ledgers are not SemVer, and the four existing records carry the template's headings with their content unchanged.
**Entry.** Step 1's exit state.
**Exit.** `docs/decisions/ADR-005-vendor-the-pashov-suite-whole-and-ungoverned.md` and `docs/decisions/ADR-006-skill-ledgers-are-not-semver.md` exist under the template; `grep -c "^## Status" docs/decisions/*.md` reports one per record; `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0; the imprimatur lint scores 100.0 on each changed record; both suites pass.
**Files.** `docs/decisions/ADR-005-vendor-the-pashov-suite-whole-and-ungoverned.md`, `docs/decisions/ADR-006-skill-ledgers-are-not-semver.md`, `docs/decisions/ADR-002-use-one-portable-promise-machine-router.md`, `docs/decisions/ADR-003-bind-vendored-promises-with-digests.md`, `docs/decisions/ADR-004-release-the-promise-machine-without-moving-skill-frontiers.md`, `docs/decisions/ADR-001-generate-install-local-promise-machine-copies.md`.
**Tests.** None written; the hypomnema lint and both suites run as the proof, and the round diffs each normalisation for content drift.
**Disciplines.** phylax: none, markdown only. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: this step is the skill's own discipline applied -- two expensive-to-reverse choices get their records, and the records follow the one convention in the tree.

## Step 3: Name the convention in the contract, cut the evolution row, demonstrate

**Goal.** The contract's "match what is already there" names the live directory, the ledger closes `recorded-reasons-and-their-homes` with one evolution row holding the next frontier judgement, and the demo path runs.
**Entry.** Step 2's exit state.
**Exit.** `plugins/hexaemeron/skills/hypomnema/SKILL.md` names `docs/decisions/` as a running convention and frontmatter reads `version: "1.1.0"`; `EVOLUTION.md` current version reads `hypomnema-v1.1.0` with one new evolution row whose digest matches the new frontier line; the demo path runs: `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0, `python3 -m unittest discover -s tests` passes, `python3 plugins/hexaemeron/tests/run_tests.py` reports only the two recorded environment failures.
**Files.** `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`.
**Tests.** None written; the evolution suite guards the row and both suites run as the proof.
**Disciplines.** phylax: none, markdown only. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: the frontier judgement is expensive to reverse and lands in `EVOLUTION.md`, the ledger the contract names for decisions about a governed skill.
