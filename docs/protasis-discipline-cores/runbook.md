# Runbook: the discipline cores in the contract, and the checker that reads them

Derived from `.hexaemeron/study.md`. Four steps, dependency ordered. Step 1
scaffolds by committing the spec; step 4 demonstrates by running the demo path
from the study's problem statement.

Every step carries a Disciplines line. Step 2 adds that field to the contract
and step 3 teaches the checker to require it. So this document is the first
runbook written under the grown contract, and step 4 proves the checker
accepts it.

## Step 1: Commit the spec

**Goal.** Put the study and the runbook in the repository so every later step
builds against a committed spec rather than controller state.

**Entry.** The run branch cut from `main` at `2b92c6f`, clean tree.

**Exit.** Both documents committed under `docs/`, and the imprimatur lint clean
over each.

```bash
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/protasis-discipline-cores/study.md \
  docs/protasis-discipline-cores/runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `docs/protasis-discipline-cores/study.md`,
`docs/protasis-discipline-cores/runbook.md`.

**Tests.** No new tests. Both existing suites run and stay green.

**Disciplines.** hypomnema: two new documents need a stated home, and `docs/`
is the convention this repository already uses for a run's spec. ephoros: none,
nothing runs unattended. phylax: none, no new input reaches a process. metron:
none, no performance claim. elenchus: none, no failure in hand.

## Step 2: Grow the contract

**Goal.** Add the five discipline answers to "What a study must answer", add
the Disciplines field to the runbook step schema, and add the matching rows to
"Before the runbook is receipted", citing each sibling contract by relative
path rather than restating it.

**Entry.** Step 1's exit state.

**Exit.** `SKILL.md` states twelve study items, a six-field step schema, and a
checklist covering the new field. The five citations resolve as files on disk,
and the lint is clean.

```bash
python3 - <<'EOF'
import pathlib, re, sys
root = pathlib.Path("plugins/hexaemeron/skills")
text = (root / "protasis/SKILL.md").read_text()
missing = [s for s in ("ephoros", "phylax", "metron", "elenchus", "hypomnema")
           if not (root / s / "SKILL.md").is_file()
           or f"../{s}/SKILL.md" not in text]
assert not missing, missing
assert "**Disciplines.**" in text
sys.exit(0)
EOF
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  plugins/hexaemeron/skills/protasis/SKILL.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/protasis/SKILL.md`.

**Tests.** No new tests here; the root suite already checks marketplace prose
and portable skills, and step 3 is where the new field gains a checker.

**Disciplines.** hypomnema: the contract text is itself the record, and the
decision about a governed skill belongs in that skill's files. phylax: none, a
prose change opens no boundary. ephoros: none, nothing runs unattended. metron:
none, no performance claim. elenchus: none, no failure in hand.

## Step 3: Ship the checker

**Goal.** A checker that reads a runbook and refuses a step missing goal,
entry, exit, files, tests or disciplines, refuses an exit that names no
command, and refuses a document in which it finds no steps at all.

**Entry.** Step 2's exit state, so the field the checker requires is already
the stated contract.

**Exit.** The checker reports a finding for each omission in the fixture
runbooks and exits 1; it exits 0 over a complete fixture; the new test file
passes and both suites stay green.

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  plugins/hexaemeron/tests/fixtures/protasis/incomplete-runbook.md; \
  test $? -eq 1
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  plugins/hexaemeron/tests/fixtures/protasis/complete-runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/protasis/scripts/protasis.py`,
`plugins/hexaemeron/tests/test_protasis_checker.py`,
`plugins/hexaemeron/tests/fixtures/protasis/incomplete-runbook.md`,
`plugins/hexaemeron/tests/fixtures/protasis/complete-runbook.md`.

**Tests.** `plugins/hexaemeron/tests/test_protasis_checker.py`. One case per
finding code, one per required field, one for an exit with no command, one for
a document with no steps, one for the allow-comment suppression, and one that
runs the checker over this run's committed runbook and asserts clean. Expect
roughly sixteen cases.

**Disciplines.** phylax: the checker takes paths on argv and reads document
content from outside the process, so it validates its paths, bounds what it
reads, keeps its patterns linear, and never shells out or fetches. elenchus:
any failure found while building this step stops the line and lands with a
test that fails without the fix. hypomnema: the finding-code vocabulary is an
interface others will cite, so it is documented in the module docstring beside
the codes themselves. ephoros: none, a lint invoked from a terminal has no
unattended surface and no on-call question. metron: none, no budget.

## Step 4: Demonstrate, then close the frontier

**Goal.** Run the demo path from the study over the committed runbook, then
record the completed frontier job in the ledger exactly once.

**Entry.** Step 3's exit state.

**Exit.** The checker exits 0 over the committed runbook. `EVOLUTION.md`
carries exactly one new row whose frontier digest matches the line it
describes, `SKILL.md` frontmatter matches the new label, and both suites pass.

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/protasis-discipline-cores/runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`plugins/hexaemeron/skills/protasis/SKILL.md`.

**Tests.** No new test file. `tests/test_evolution_contract.py` and
`plugins/hexaemeron/tests/test_evolution.py` already hold the ledger shape and
the digest rule, and they must pass over the new row.

**Disciplines.** hypomnema: the ledger row is the decision record for a
governed skill, and it is written once. elenchus: a non-zero exit from the
checker over its own runbook stops the step rather than being explained away.
phylax: none, no new boundary. ephoros: none, nothing runs unattended. metron:
none, no performance claim.
