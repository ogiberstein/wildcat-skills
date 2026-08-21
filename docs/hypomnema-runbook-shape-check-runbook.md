# Runbook: Hold alert runbooks to the three-line shape

Derived from the study of the same name. Two steps, one pull request each,
stacked on `fiat/hypomnema-2-check-runbook-files-carry-the-three` off `main`
at `87e213c19e64687406d7ba7601e093929bb3d813`.

## Step 1: Scaffold: commit the study and runbook

**Goal.** Put the reviewed specification in the tracked tree before behaviour changes.
**Entry.** The run branch at `87e213c19e64687406d7ba7601e093929bb3d813`, with a clean tree.
**Exit.** The two committed documents pass their checks and the tree remains green:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/hypomnema-runbook-shape-check-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/hypomnema-runbook-shape-check-runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `docs/hypomnema-runbook-shape-check-study.md`, `docs/hypomnema-runbook-shape-check-runbook.md`, `.horos/boundary.json` regenerated for the two tracked paths.
**Tests.** No new behaviour test; the document checks and both suites are the regression net.
**Disciplines.** hypomnema: the tracked study is the standing source for the frontier row. phylax: none, Markdown opens no execution boundary. ephoros: none, nothing runs unattended. metron: none, no performance claim. elenchus: none, no failure is in hand.

## Step 2: Ship H007, reconcile prose and advance the frontier

**Goal.** Reject each missing or empty alert-runbook answer, preserve the adjoining interfaces and record the completed frontier job once.
**Entry.** Step 1's green exit state, on the exact branch the controller cuts from step 1.
**Exit.** The fixture demo names H007 faults, the complete specimen and first-party tree are clean, mutable first-party marketplace prose has been cold-read and reconciled, and every repository gate passes:

```bash
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/hexaemeron/tests/fixtures/hypomnema/runbooks; test $? -eq 1
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/hypomnema-runbook-shape-check-study.md docs/hypomnema-runbook-shape-check-runbook.md plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/hexaemeron/skills/hypomnema/EVOLUTION.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/hypomnema-runbook-shape-check-study.md docs/hypomnema-runbook-shape-check-runbook.md plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/hexaemeron/skills/hypomnema/EVOLUTION.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
```

**Files.** `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, `plugins/hexaemeron/tests/test_hypomnema_checker.py`, `plugins/hexaemeron/tests/fixtures/hypomnema/runbooks/*`, `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`, `tests/promise_machine_coverage.json` if the binding digest moves, and `.horos/boundary.json`. Mutable first-party prose is reviewed suite-wide; only stale surfaces are changed.
**Tests.** Add one case per absent heading, empty-body cases, a complete specimen, path-scope false-positive guards, fence handling, reasoned suppression, fixture coverage and a clean tree walk; retain every existing case.
**Disciplines.** phylax: the scan stays within caller-named files and reports unreadable input. ephoros: the division of labour with issue 319 stays explicit and H007 does not parse alert rules. metron: none, no performance claim. elenchus: any PM071 or test failure is reproduced, localised and guarded before the receipt. hypomnema: the heading shape, code and successor are recorded once in the ledger row.
