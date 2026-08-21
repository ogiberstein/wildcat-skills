# Runbook: Require alert rules to carry a resolving runbook annotation

## Commit rule

Derived from `.hexaemeron/study.md`: two signed steps, each with one stacked
pull request. The run starts from `main` at `0bfad60bb482245dd08d9747139d26824392a2c7`.

Every Fiat-created commit in this run is made with `git commit -S` and ends,
after a blank line, with these exact trailers:

```text
Co-authored-by: Shoggoth <shoggoth@wildcat.finance>
Wildcat-Origin: shoggoth
```

Each step's exit includes local cryptographic verification and exact trailer
checks. A missing, bad or unverifiable signature is a failed exit, even when
the test suites are green.

## Step 1: Scaffold: commit the alert-runbook annotation specification

**Goal.** Put the receipted study and runbook in the tracked tree, with the
Horos boundary regenerated, before checker behaviour changes.

**Entry.** The controller-provided step-1 branch cut from
`fiat/ephoros-1-require-alert-rules-to-carry-a-resolvi`, whose entry tree is
`0bfad60bb482245dd08d9747139d26824392a2c7`, with no uncommitted files.

**Exit.** Commit byte-identical tracked copies of the study and runbook plus
the regenerated Horos boundary. Before the signed commit, all document,
focused contract, repository and tree gates exit 0:

```bash
cmp -s .hexaemeron/study.md docs/ephoros-alert-runbook-annotations-study.md
cmp -s .hexaemeron/runbook.md docs/ephoros-alert-runbook-annotations-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/ephoros-alert-runbook-annotations-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/ephoros-alert-runbook-annotations-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/ephoros-alert-runbook-annotations-study.md docs/ephoros-alert-runbook-annotations-runbook.md
for file in docs/ephoros-alert-runbook-annotations-study.md docs/ephoros-alert-runbook-annotations-runbook.md; do python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file"; done
python3 -m unittest tests.test_evolution_contract plugins.hexaemeron.tests.test_evolution
python3 scripts/promise_machine.py check
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
```

After those gates pass, stage only the three named paths and create one commit
with `git commit -S`. The exact committed head then passes:

```bash
git verify-commit HEAD
test "$(git log -1 --format=%B | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git log -1 --format=%B | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
```

**Files.** `docs/ephoros-alert-runbook-annotations-study.md`,
`docs/ephoros-alert-runbook-annotations-runbook.md`, `.horos/boundary.json`.

**Tests.** No behaviour test is added. Protasis checks both tracked documents;
Imprimatur and Brevitas check their prose; the evolution, Promise Machine,
root and Hexaemeron suites and all three tree lints provide the regression
gate. Counts are reported from the commands rather than hard-coded.

**Disciplines.** phylax: none, tracked Markdown and a regenerated boundary
open no execution path. ephoros: none, nothing runs unattended. metron: none,
no performance claim. elenchus: any failed copy, lint, suite or signature gate
stops the step and is reproduced before repair. hypomnema: the tracked study
is the source for the two generation records written in step 2.

## Step 2: Ship E004 and the generic YAML H003 handoff

**Goal.** Require each supported YAML alert entry to carry its own local
runbook annotation, resolve that pointer through H003, preserve H007's target
shape, and record both ordinary generation changes without moving either held
frontier.

**Entry.** The controller-provided step-2 branch cut from step 1's exact signed,
locally verified green commit, with the tracked study and runbook present and
no uncommitted files.

**Exit.** Implement the study's chosen bounded block-YAML design and satisfy
all of the following:

- Ephoros reports E004 once per supported alert entry lacking its own nested
  `annotations.runbook`, and no other skill emits that presence finding.
- Comments, block scalars, top-level pointers and a neighbouring alert's
  pointer do not create or satisfy an alert annotation.
- Hypomnema generically scans supported YAML `runbook:` pointers and H003
  resolves them relative to the YAML file without classifying alert entries.
- Existing H003 Markdown behaviour and H007 runbook-shape behaviour are
  unchanged; a complete alert-to-runbook fixture is clean under both checkers.
- E000 to E003 and H000 to H007 keep their numbers and prior cases.
- Ephoros becomes `ephoros-v0.2.0` and Hypomnema becomes
  `hypomnema-v4.3.0`. Each generation row retains its previous frontier
  revision, frontier digest, status and held `Next Fiat job` byte for byte.
- Promise Machine evidence and hashes describe the widened mechanical parser
  surfaces without promoting them to an observability or record-placement
  review.

Regenerate `.horos/boundary.json`, cold-read the root and Hexaemeron runtime,
README, agent-description and manifest prose, and change only a surface made
false by E004 or YAML H003. Do not alter CI or package versions merely because
the canonical skill generation labels move. The focused demonstration and all
repository gates then exit 0:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_ephoros_checker plugins.hexaemeron.tests.test_hypomnema_checker
python3 -m unittest tests.test_evolution_contract tests.test_version_propagation plugins.hexaemeron.tests.test_evolution
python3 -m unittest tests.test_marketplace_prose
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/ephoros-alert-runbook-annotations-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/ephoros-alert-runbook-annotations-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/ephoros-alert-runbook-annotations-study.md docs/ephoros-alert-runbook-annotations-runbook.md plugins/hexaemeron/skills/ephoros/SKILL.md plugins/hexaemeron/skills/ephoros/EVOLUTION.md plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/hexaemeron/skills/hypomnema/EVOLUTION.md
for file in docs/ephoros-alert-runbook-annotations-study.md docs/ephoros-alert-runbook-annotations-runbook.md plugins/hexaemeron/skills/ephoros/SKILL.md plugins/hexaemeron/skills/ephoros/EVOLUTION.md plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/hexaemeron/skills/hypomnema/EVOLUTION.md; do python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file"; done
python3 scripts/promise_machine.py check
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
```

After every gate passes, stage only the declared step-2 files and any reviewed
prose surface actually made stale, then create one commit with `git commit -S`.
The exact committed head then passes:

```bash
git verify-commit HEAD
test "$(git log -1 --format=%B | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git log -1 --format=%B | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
```

**Files.** `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`,
`plugins/hexaemeron/tests/test_ephoros_checker.py`,
`plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`,
`plugins/hexaemeron/tests/test_hypomnema_checker.py`,
`plugins/hexaemeron/tests/fixtures/ephoros/alert-rules/*`,
`plugins/hexaemeron/skills/ephoros/SKILL.md`,
`plugins/hexaemeron/skills/ephoros/EVOLUTION.md`,
`plugins/hexaemeron/skills/hypomnema/SKILL.md`,
`plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`,
`tests/promise_machine_coverage.json`, `.horos/boundary.json`; plus only those
first-party README, runtime, agent-description or manifest files the cold read
proves stale.

**Tests.** Extend the Ephoros checker tests with missing, complete,
multi-alert isolation, top-level-pointer, comment, block-scalar, unsupported
shape, suppression and clean-tree cases. Extend the Hypomnema checker tests
with dangling and restored YAML pointers, relative-base resolution, unchanged
Markdown H003, unchanged H007 and one complete end-to-end fixture. Keep every
existing case. The focused test count increases by the added cases; the exact
total is reported by the focused command.

**Disciplines.** phylax: caller-named YAML is untrusted text, so decoding,
bounded reads, paths and non-execution stay visible and guarded. ephoros: owns
only alert classification and E004 presence. metron: none, no performance
claim or speed-motivated edit. elenchus: any parser, PM071, evolution, tree,
suite or signature failure is reproduced and guarded before the step resumes.
hypomnema: owns generic H003 resolution, unchanged H007 shape and the two
generation records in their established skill ledgers.
