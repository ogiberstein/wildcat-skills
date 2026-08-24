# Runbook: a report-only dead-code baseline

Derived from `.hexaemeron/study.md` for issue
[#437](https://github.com/wildcat-finance/skills/issues/437). Seven steps, one
pull request each, stacked on
`fiat/437-establish-a-report-only-dead-code-baseline` cut from `main` at
`8de7a4bc910e398107ff2f54a4cf92a82e764a76`.

Step 3 is wider than the receipted study allows. The study lists coverage only
among its non-goals, on the grounds that the two routes to branch coverage were
each unacceptable. A probe run against Python 3.14 during the runbook phase
separated the two halves of that signal: `co_lines()` and `sys.settrace` give
line and function coverage from two documented interfaces, while the set of arcs
that could have been taken is the part that carries the cost. Line and function
coverage is a reachability signal and belongs inside this command's boundary;
branch coverage is a test-completeness signal and the issue puts test
completeness outside it. Step 1 therefore opens by amending the study to carry
that distinction, before any of its own code is written. The amendment is the
first act of the build, not a later reconciliation.

Every step inherits the study's boundaries. Two apply to all seven and are not
repeated per step: the root suite plus any plugin suite covering a changed area
runs before the commit, and `.horos/boundary.json` is regenerated last, after the
tree is otherwise final, because a boundary written before the last file lands
describes a tree that no longer exists.

Each step's `Tests` block names the Elenchus runner contract. The test command is
always `python3 tests/emit_dead_code_report.py {report}`, the report format is
`unittest-json-v1`, and the report file is the relative path
`.elenchus/dead-code.json`. Elenchus substitutes `{report}` with a canonical
absolute descendant of its own detached parent worktree, so the declaration stays
relative and the current worktree's absolute path is never passed to
`--report-file`. Warden uses those three inputs as written and does not infer a
command from `Files`.

## Step 1: Amend the study, then scaffold the command and both report formats

**Goal.** Record the coverage decision in the study, then stand up one root
command that discovers the analysed universe at a commit, joins it with the Horos
classification, and emits that inventory as equivalent text and JSON with no
analyser registered yet.

**Entry.** `fiat/437-establish-a-report-only-dead-code-baseline` at
`8de7a4bc910e398107ff2f54a4cf92a82e764a76`.

**Exit.**

```bash
hexctl amend study --artifact .hexaemeron/study.md
python3 scripts/dead_code.py report
python3 scripts/dead_code.py report --json
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
```

The amendment receipt succeeds and its `Still holding` field carries a verdict
for all seven steps. The two report commands exit 0 and report more than a
thousand analysed paths with a per-classification excluded count. The suite is
green. The report header carries the analysed commit, the universe count and the
exclusion counts. Discovery that returns nothing exits non-zero.

**Files.** `.hexaemeron/study.md`, `scripts/dead_code.py`,
`schemas/dead-code-report-v1.schema.json`, `tests/test_dead_code.py`,
`tests/emit_dead_code_report.py`, `.github/workflows/dead-code.yml`,
`docs/dead-code-study.md`, `docs/dead-code-runbook.md`, `.gitignore`,
`.horos/boundary.json`.

**Tests.** `tests/test_dead_code.py`, new, about twenty cases: universe discovery
at a commit, refusal on a dirty checkout, the classification join against a
fixture boundary, text and JSON parity over the same model, the empty-universe
refusal, path confinement on the write target, atomic write and orphan sweep, and
a malformed boundary file refused by name. Elenchus test command
`python3 tests/emit_dead_code_report.py {report}`, report format
`unittest-json-v1`, report file `.elenchus/dead-code.json`.

**Disciplines.** phylax: this step opens the tracked-tree read and the artefact
write, which are two of the study's four boundaries. ephoros: the report header
is the signal answering the study's first on-call question, so it ships with the
first report rather than later. metron: none, this step makes no speed claim and
there is nothing to measure until an analyser exists. elenchus: none, no failure
in hand. hypomnema: the finding schema is the record, written here as
`schemas/dead-code-report-v1.schema.json` rather than described in prose, and the
study amendment records the coverage decision.

## Step 2: The Python analyser

**Goal.** Report unused imports, unreachable modules and unused module-level
definitions across the Python universe, each finding carrying its analyser,
evidence, confidence and nearest false-positive boundary.

**Entry.** Step 1's exit state, on its branch.

**Exit.**

```bash
python3 scripts/dead_code.py report --analyser python --json
python3 -m unittest discover -s tests
time python3 scripts/dead_code.py report --analyser python,repository --json
```

The positive fixture tree yields at least one finding for each of the three
classes. The negative fixture tree yields no finding for a dynamically registered
plugin, a declared CLI entry point or an intentionally unused test fixture. Every
finding names a false-positive boundary. The analyser status line carries
`python` and its version. The timed run is recorded as the baseline measurement
for the study's sixty-second budget.

**Files.** `scripts/dead_code.py`,
`tests/fixtures/dead-code/python/positive/`,
`tests/fixtures/dead-code/python/negative/`, `tests/test_dead_code_python.py`,
`.horos/boundary.json`.

**Tests.** `tests/test_dead_code_python.py`, new, about twenty-five cases: the
import graph over a fixture package, unused-import detection, unreachable-module
detection, unused module-level definition detection, the entry-point exemption,
the dynamic-registration exemption and its confidence downgrade, the test-fixture
exemption, a syntax error reported as an analyser status rather than a crash, and
a case asserting no finding says a path is dead or safe to delete. Elenchus test
command `python3 tests/emit_dead_code_report.py {report}`, report format
`unittest-json-v1`, report file `.elenchus/dead-code.json`.

**Disciplines.** phylax: `ast.parse` runs over every tracked Python file, so this
step owns the untrusted-parse boundary and the rule that parsing never imports.
ephoros: it adds the first per-analyser status line. metron: the study's budget
becomes measurable here, so this step records the first number and any later
change made for speed is held against it. elenchus: none, no failure in hand.
hypomnema: none, the confidence rule lives in the schema step 1 wrote.

## Step 3: The coverage analyser

**Goal.** Report Python lines and functions that no repository suite executes, as
an opt-in analyser that runs outside the default report and outside the budget.

**Entry.** Step 2's exit state, on its branch.

**Exit.**

```bash
python3 scripts/dead_code.py report --analyser coverage --json
python3 scripts/dead_code.py report --analyser python,repository --json
python3 -m unittest discover -s tests
```

The positive fixture yields a finding for a function no suite calls. The negative
fixture yields none for a function reached only through a dynamically registered
plugin. The status line carries `coverage`, the interpreter version and the
suites that ran. A suite that fails or times out is reported as a degraded status
rather than as coverage of zero. Branch coverage appears as not established with
its reason. The second command proves the default report does not run the suites,
so the step 2 measurement still holds.

**Files.** `scripts/dead_code.py`,
`tests/fixtures/dead-code/coverage/positive/`,
`tests/fixtures/dead-code/coverage/negative/`,
`tests/test_dead_code_coverage.py`, `.horos/boundary.json`.

**Tests.** `tests/test_dead_code_coverage.py`, new, about twenty cases: the
executable-line set from `co_lines()` over a fixture module including nested
functions and class bodies, the tracer's hit set, the never-executed difference,
the rollup from lines to whole functions, a failing suite reported as degraded, a
timing-out suite reported as degraded, the tracer restored after every run, a
case asserting no branch result is ever claimed, a case proving the default
report starts no suite, and a case asserting a degraded suite never becomes a
dead-code finding. Elenchus test command
`python3 tests/emit_dead_code_report.py {report}`, report format
`unittest-json-v1`, report file `.elenchus/dead-code.json`.

**Disciplines.** phylax: this step executes the repository's own suites under a
tracer, which is the widest boundary the run opens, so it owns the timeout, the
working directory and the rule that a suite's failure never becomes a coverage
claim. ephoros: the degraded-suite status is the signal, because a suite that did
not finish and a function that never ran are otherwise indistinguishable in the
output. metron: this analyser sits outside the sixty-second budget by
construction, and the step proves the default report still meets it. elenchus:
none, no failure in hand. hypomnema: none, step 1's amendment already records why
line coverage is in scope and branch coverage is not.

## Step 4: The repository-graph analyser

**Goal.** Report orphaned fixtures, schemas, documents, generated copies,
manifest entries and command entry points that nothing in the repository reaches.

**Entry.** Step 3's exit state, on its branch.

**Exit.**

```bash
python3 scripts/dead_code.py report --analyser repository --json
python3 -m unittest discover -s tests
```

The positive fixture tree yields a finding for an orphaned fixture, a schema
nothing loads, a document nothing links and a manifest entry naming a path that
no longer exists. The negative fixture tree yields none for a generated copy
Horos classified, a fixture a test reads by a computed path, or a document
`AGENTS.md` names. The analyser status line carries `repository`.

**Files.** `scripts/dead_code.py`,
`tests/fixtures/dead-code/repository/positive/`,
`tests/fixtures/dead-code/repository/negative/`,
`tests/test_dead_code_repository.py`, `.horos/boundary.json`.

**Tests.** `tests/test_dead_code_repository.py`, new, about twenty cases: each of
the six object kinds found in the positive tree, each of the three exemptions
held in the negative tree, a manifest whose entries are read without trusting
their paths, and the retained-path join proving a Horos-classified path yields
nothing. Elenchus test command `python3 tests/emit_dead_code_report.py {report}`,
report format `unittest-json-v1`, report file `.elenchus/dead-code.json`.

**Disciplines.** phylax: this step reads the repository manifests, which is the
third of the study's four boundaries, and it validates their shape before use.
ephoros: it adds the `repository` status line. metron: it is inside the budget
step 2 recorded, and the timed command covers both analysers. elenchus: none, no
failure in hand. hypomnema: none, no decision here is expensive to reverse.

## Step 5: The Solidity analyser

**Goal.** Report Slither dead-code and unused-state findings for Foundry projects
that build, and report the analyser as not established when the toolchain is
absent.

**Entry.** Step 4's exit state, on its branch.

**Exit.**

```bash
python3 scripts/dead_code.py report --analyser solidity --json
python3 -m unittest discover -s tests
```

With Slither 0.11.6 and forge 1.7.1 present, the positive Solidity fixture yields
at least one finding and the status line carries both versions. With either
absent, the status line reads not established, no Solidity finding is emitted,
and the command exits 0. When the analyser is present and crashes, the command
exits non-zero. Forge coverage is collected where a project builds and reported
as a separate signal.

**Files.** `scripts/dead_code.py`,
`tests/fixtures/dead-code/solidity/positive/`,
`tests/fixtures/dead-code/solidity/negative/`,
`tests/test_dead_code_solidity.py`, `.horos/boundary.json`.

**Tests.** `tests/test_dead_code_solidity.py`, new, about fifteen cases: the
Foundry project discovery, the fixed argv with no shell, the timeout, the
absent-toolchain status and its zero exit, the crash and its non-zero exit, the
positive fixture's finding, the negative fixture holding a contract reached only
through an interface, and a case asserting an absent analyser is never rendered
as a clean one. The Slither and forge cases skip with a stated reason when the
toolchain is absent, and the absence-handling cases run everywhere. Elenchus test
command `python3 tests/emit_dead_code_report.py {report}`, report format
`unittest-json-v1`, report file `.elenchus/dead-code.json`.

**Disciplines.** phylax: this step spawns Slither and forge, which is the study's
subprocess boundary, and it owns the fixed argv, the timeout and the working
directory. ephoros: the not-established status is the signal answering the
study's second on-call question, and it is the one this analyser exists to get
right. metron: none, the study states why an optional toolchain carries no
budget. elenchus: none, no failure in hand. hypomnema: none, the toolchain pins
are recorded in the baseline step 6 writes.

## Step 6: The baseline and its suppressions

**Goal.** Pin a report to its analysed commit and analyser versions, and accept
declared suppressions that are themselves checked.

**Entry.** Step 5's exit state, on its branch.

**Exit.**

```bash
python3 scripts/dead_code.py baseline --write
python3 scripts/dead_code.py baseline --check
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
```

`--check` exits 0 against the commit and analyser versions it recorded, and
non-zero when the commit or any analyser version differs. A suppression without a
reason is refused. A suppression naming a finding that no longer exists is itself
reported and exits non-zero. The comparison names added and resolved findings by
analyser and path. The ADR is written and the Hypomnema lint is clean.

**Files.** `scripts/dead_code.py`, `.dead-code/baseline.json`,
`.dead-code/suppressions.json`, `docs/decisions/ADR-0NN-*.md`,
`tests/test_dead_code_baseline.py`, `.horos/boundary.json`.

**Tests.** `tests/test_dead_code_baseline.py`, new, about twenty cases: the
baseline write and its digest, the matching check, the changed-commit refusal,
the changed-analyser-version refusal, the universe-floor refusal, a suppression
without a reason, a suppression with no matching finding, an unused suppression,
the added and resolved comparison, and the atomic write of both artefacts. The
ADR number is chosen when this step is written, not before, and the step verifies
no other merged or open work has claimed it. Elenchus test command
`python3 tests/emit_dead_code_report.py {report}`, report format
`unittest-json-v1`, report file `.elenchus/dead-code.json`.

**Disciplines.** phylax: this step writes two more artefacts, so the confinement
and atomic-write controls extend to both. ephoros: the baseline comparison is the
signal answering the study's third on-call question. metron: none, the baseline
read adds no measured work to the budgeted command. elenchus: the four
fail-closed conditions become checkable here, and each lands with a test seen red
on the unfixed tree. hypomnema: the report-only decision and the choice to
consume the Horos classification are expensive to reverse, and this step writes
that ADR.

## Step 7: Register the capability, wire the lane and demonstrate

**Goal.** Register the Promise Machine capability, make the read-only CI lane
real, and run the study's demo path end to end.

**Entry.** Step 6's exit state, on its branch.

**Exit.**

```bash
python3 scripts/promise_machine.py sync
python3 scripts/promise_machine.py check
python3 -m unittest discover -s tests
python3 scripts/dead_code.py report
python3 scripts/dead_code.py report --json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/promise-machine/dead-code-v1.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/dead-code-v1.md
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
```

`promise_machine.py check` is clean with the new section and its fourteen
generated copies. The coverage row binds the runtime, documentation and fixtures
by digest. The workflow fails on a crash, a malformed report or a collapsed
universe, and passes with candidate findings outstanding. The demo path from the
study's problem statement runs and both formats carry the same findings. The
Horos boundary is regenerated last.

**Files.** `PROMISE_MACHINE.md`, `plugins/*/PROMISE_MACHINE.md`,
`tests/promise_machine_coverage.json`, `docs/promise-machine/dead-code-v1.md`,
`.github/workflows/dead-code.yml`, `tests/test_dead_code.py`,
`.horos/boundary.json`.

**Tests.** `tests/test_dead_code.py`, extended by about ten cases: the workflow
parses as YAML and its job loads, the lane fails on each of the four fail-closed
conditions, the lane passes with findings outstanding, the coverage row digests
match the files they name, and the demo path's two commands carry identical
findings. The YAML case loads the file rather than asserting on its text, because
#536 records fifteen shape tests passing against a workflow that never parsed.
Elenchus test command `python3 tests/emit_dead_code_report.py {report}`, report
format `unittest-json-v1`, report file `.elenchus/dead-code.json`.

**Disciplines.** phylax: none new, this step opens no boundary the earlier six
did not. ephoros: the job summary is where the three on-call questions are read
in CI, so this step puts the report header and the analyser statuses into it.
metron: none, the lane runs the command already measured in step 2. elenchus:
none, no failure in hand. hypomnema: the capability documentation at
`docs/promise-machine/dead-code-v1.md` is the record of what the promise covers,
and the schema written in step 1 stays its only description of the finding shape.
