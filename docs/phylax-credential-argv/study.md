# Study: flag credential-named values in subprocess argv

## assumptions

Assuming, unless corrected:

1. The run starts from `main` at
   `4408597bcd0130b0cee8bd7aab0b55d64ff957c7`; `HEAD` and local `main`
   both resolved to that commit before this study.
2. A `RUNNERS` call's argument list means the value passed as subprocess
   `args`: its first positional argument, or explicit `args=` when there is no
   positional argument. `env=` and the other process options are not argv.
3. P004 keeps its existing name-based evidence. The new check follows
   `ast.Name` nodes within the source-local argv expression, including list
   and tuple literals, nested expressions and list concatenation. It does not
   follow a command assigned to another name or infer a credential from a flag
   such as `--token`.
4. A credential transported only through `env=` stays outside this finding.
   Phylax currently recommends environment transport; broadening P004 to
   environments would contradict that documented policy and mislabel the
   exposure as argv.
5. The checker remains standard-library-only and compatible with Python 3.9
   and 3.12.13. The final demonstration uses uv's Python 3.12.13, matching the
   approved run's toolchain.
6. Issue #325 is generation work against a mature skill. Phylax advances from
   `phylax-v1.1.0` to `phylax-v1.2.0`; its frontier status, revision, current
   frontier, next job and frontier digest remain byte-identical.
7. The failed predecessor run is evidence, not an implementation source. This
   study retains its approved source-local design but is a new initial spec,
   with no amendment block. Its Brevitas gate invokes the one-draft CLI once
   per file.
8. This is one independently verifiable lint capability, so module
   decomposition would add ceremony without separating any shippable result.

The issue, current source, versioning contract and reproduced failure settle
these readings. No unresolved ambiguity changes the design or build order.

## 1. problem statement

Phylax's P004 currently reports credential literals and credential-named
values handed to `print` or a logger. The skill also forbids credentials in
command lines, but `Visitor.visit_Call` checks resolved subprocess calls only
for P001 and P002. This input therefore passes today:

```python
import subprocess

API_TOKEN = load()
subprocess.run(["curl", "--token", API_TOKEN])
```

The users are contributors running Phylax and reviewers treating its named
mechanical boundary as a gate. A working prototype reports P004 when an
`ast.Name` matching `CREDENTIAL` appears inside the argv expression of a call
accepted by `_starts_process`, keeps close non-subprocess and non-argv cases
clean, and changes no existing finding contract.

The final demo path is:

```bash
uv run --python 3.12.13 python -m unittest plugins.hexaemeron.tests.test_phylax_checker
uv run --python 3.12.13 python plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
uv run --python 3.12.13 python plugins/hexaemeron/tests/run_tests.py
uv run --python 3.12.13 python -m unittest discover -s tests
uv run --python 3.12.13 python -m unittest tests.test_evolution_contract
uv run --python 3.12.13 python scripts/promise_machine.py check
uv run --python 3.12.13 python plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/phylax-credential-argv/study.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/phylax-credential-argv/runbook.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/phylax-credential-argv/*.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md
(
  for file in docs/phylax-credential-argv/study.md docs/phylax-credential-argv/runbook.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md; do
    uv run --python 3.12.13 python plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file" || exit
  done
)
uv run --python 3.12.13 python plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
uv run --python 3.12.13 python plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
uv run --python 3.12.13 python plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The subshell around the Brevitas loop preserves a failing file's non-zero
status without exiting the operator's parent shell. Each `brevitas.py`
process receives exactly one `draft` positional, matching its CLI.

The prototype is demonstrated only when:

- module, module-alias, direct-import and direct-import-alias subprocess calls
  report P004 for a credential-named argv value;
- positional `args`, explicit keyword `args=` and inline list concatenation
  report, while concatenation does not acquire P002;
- an ordinary argv value, a local `run`, an unrelated `.call`, and a
  credential present only in `env=` remain clean;
- reason-bearing suppression clears the new finding and a bare pragma does
  not;
- P001 and P002 classifications retain their existing behavior;
- text and JSON output never repeat the fixture credential value; and
- every command above exits zero.

Before the build, the sample above returned `[]`. The focused suite passed
46/46 tests on Python 3.9.6 and 46/46 on Python 3.12.13, so the missing P004
finding is reproduced without an existing red test.

## 2. prior art

### in this repository

- `plugins/hexaemeron/skills/phylax/scripts/phylax.py` already supplies
  `RUNNERS`, `CREDENTIAL`, import-alias tracking, `_starts_process`, P001/P002,
  the P004 finding path and reason-bearing suppression. The smallest seam is
  the resolved-runner branch in `Visitor.visit_Call`.
- `plugins/hexaemeron/tests/test_phylax_checker.py` pairs each reported case
  with safe neighbours. Its subprocess fixtures already protect list
  concatenation, a local helper named `run` and an unrelated `.call` method.
- `plugins/ariadne/scripts/ariadne_lib/scrub.py` and
  `plugins/ariadne/tests/test_capture_scrubbing.py` redact argv values after
  secret flags from captured command records. That is post-execution record
  hygiene, not permission for source to put credentials in argv.
- `plugins/hexaemeron/skills/phylax/SKILL.md` already states the no-credential
  argv policy. Its mechanical-subset paragraph currently documents only
  source and output, so the implementation and governed prose must move
  together.
- `plugins/hexaemeron/skills/phylax/EVOLUTION.md` and
  `plugins/hexaemeron/skills/VERSIONING.md` require a generation row to retain
  the mature frontier revision and digest. Recomputing the canonical frontier
  line produced
  `3d0057bb195f303c0e40b5782bf59ab0cba53e3172478c6a331d5990236ac604`,
  matching the ledger.
- `plugins/brevitas/skills/brevitas/scripts/brevitas.py --help` exposes one
  optional `draft` positional. The blocked predecessor's multi-file call
  exited 2; this study's per-file subshell loop is the corrected gate.

The last two merged pull requests that changed the Python checker and its
fixtures were read before choosing a design:

- PR #193, `Add TypeScript boundary checks to Phylax`, kept the Python visitor
  and added a bounded TypeScript surface. Its audit found one unbounded file
  read, fixed it with a 1 MiB cap, then closed with no lead.
- PR #103, `Add six practice skills to Hexaemeron`, introduced P001-P004. Its
  first Phylax pass established why runner names must resolve through imports
  and why list-plus-list is not a string command. Its known CI gap remains in
  `.github/workflows/`; issue #325 does not authorize a CI change.

The two latest merged pull requests touching the wider Phylax skill surface
were also checked. PR #441 added the ADR-010 boundary pointer and carried no
unfinished Phylax work. PR #426 removed duplicated sibling-routing prose and
left marketplace-context text alone. Neither changes the argv design.

The Phylax entries in `audit/AUDIT.md` were read before the options below.
Round 1 found the TypeScript input-size gap; round 2 closed it with no further
finding or lead. `plugins/hexaemeron/audit/AUDIT.md` contains no Phylax round.
Nothing carried there widens or narrows issue #325.

### in the organisation

Issue #325 identifies this as the second stated never-rule the lint does not
mechanically enforce and names the existing subprocess visitor as the cheap
seam. Public organisation searches found ordinary subprocess use but no
separate source analyser or argv-credential detector to reuse. That search is
not proof about private or unindexed repositories.

### outside the organisation

- MITRE CWE-214 identifies sensitive process invocation data, including
  command-line arguments, as information other processes may observe:
  <https://cwe.mitre.org/data/definitions/214.html>.
- Python 3.12's `subprocess` documentation defines `args` separately from the
  `env` mapping and recommends a sequence for program arguments:
  <https://docs.python.org/3.12/library/subprocess.html#popen-constructor>.

These sources support the exposure boundary. They do not choose Phylax's
source-local, identifier-based heuristic.

## 3. constraints and non-goals

### constraints

- Start at `4408597bcd0130b0cee8bd7aab0b55d64ff957c7` and stay within issue
  #325.
- Preserve P000-P007, CLI arguments, output schemas, exit codes, import
  resolution, suppression syntax and every existing safe neighbour.
- Reuse `_starts_process`; a bare `run`, `call` or `Popen` spelling is not
  enough evidence that the call starts a process.
- Walk only the selected argv expression. Do not classify `env=`, `cwd=`,
  `input=` or other process configuration as command-line exposure.
- Emit the identifier, path, line, code and fixed explanation, never the value
  associated with the identifier.
- Add no dependency, shell execution, network call, target-source execution or
  filesystem write to the checker.
- Keep Python 3.9 and 3.12.13 support.
- Update Phylax's mechanical prose and recompute the Promise Machine coverage
  digest for any changed canonical bytes.
- Record `phylax-v1.2.0` on the `generation` axis while retaining frontier
  status `mature`, revision `off-chain-boundary-controls`, current-frontier
  text, next job `None -- mature` and digest
  `3d0057bb195f303c0e40b5782bf59ab0cba53e3172478c6a331d5990236ac604`.
- Invoke Brevitas once per file. No command may pass it multiple draft paths,
  and the loop must propagate any file's non-zero result.

Expected implementation and record paths are:

- `plugins/hexaemeron/skills/phylax/scripts/phylax.py`
- `plugins/hexaemeron/tests/test_phylax_checker.py`
- `plugins/hexaemeron/skills/phylax/SKILL.md`
- `plugins/hexaemeron/skills/phylax/EVOLUTION.md`
- `tests/promise_machine_coverage.json`
- `docs/phylax-credential-argv/study.md`
- `docs/phylax-credential-argv/runbook.md`
- `.horos/boundary.json`
- `audit/AUDIT.md` when the audit loop records its rounds

### non-goals

- Inter-statement or interprocedural dataflow, including following an argv
  list assigned before the subprocess call.
- Secret-shaped literal detection, flag-name interpretation, or evaluation of
  a call that produces an argv element.
- Widening P004's writer analysis to attributes, containers, formatted strings
  or logger templates.
- Treating environment transport as argv exposure or changing the existing
  credential-storage policy.
- A new finding code, any P001/P002 redesign, another language surface, or CI
  work for the known Hexaemeron-suite gap.
- Reopening the mature frontier, changing its digest, advancing evolution or
  epoch, or creating a held job.
- Applying the predecessor stash to this run. Mason may implement the accepted
  design from this study and the current tree only.

### operating boundaries

**Always.** Add the hostile P004 fixture before the visitor change; run the
focused suite, both repository suites, Phylax over `plugins tests`, Promise
Machine checks and each required prose check before committing. Run Brevitas
once for each named file.

**Ask first.** Add a dependency; widen analysis beyond the source-local argv
expression; change P004's identifier grammar, public message shape or
suppression behavior; touch CI; or alter any mature-frontier field.

**Never.** Put a real credential in a fixture, diagnostic, command, commit or
receipt; weaken runner resolution; delete a safe neighbour; apply unreceipted
predecessor code; edit vendored source; or claim an unrun command passed.

## 4. design options

### option A: walk the resolved call's argv expression (chosen)

Select the first positional argument, or explicit `args=` when no positional
argument exists. For a call accepted by `_starts_process`, walk only that AST
subtree and report P004 for each `ast.Name` matching `CREDENTIAL`. Keep the
existing P001/P002 logic, suppression filter and renderers.

This handles inline lists, tuples, nested syntax and list concatenation with a
small local change. It deliberately misses argv assembled in another
statement. That source-local miss is legible and testable.

### option B: follow argv assignments within a scope

Track assignments whose value contains a credential-named node, then follow
the assigned name into a later runner call. This catches `argv = [...]`, but
it opens rebinding, ordering, branch, alias and scope questions. A partial
dataflow engine costs more to understand and can imply coverage it has not
earned.

### option C: walk the whole subprocess call

Inspect every positional and keyword value after resolving the runner. This is
shorter than choosing `args`, but it reports credentials in `env=`, `cwd=` and
unrelated options as command-line exposure. The message would make a claim
the inspected syntax does not support.

Option A is the lowest-comprehension-cost construction that meets the issue.
It trades away separately assembled argv and preserves an exact boundary
between process arguments and process configuration.

## 5. risk register seed

```risk-register
runner-identity | imported call binding at the subprocess boundary | only calls accepted by existing module and direct-import resolution receive the new check
argv-selection | the subprocess args parameter | only first positional args or explicit args keyword is walked and env remains outside the finding
name-recursion | untrusted Python syntax inside the argv expression | ast names are visited without executing source or following statement-level dataflow
safe-neighbour | local run and unrelated call methods beside resolved runners | negative fixtures remain clean while module and direct-import aliases report
secret-diagnostic | credential-bearing source crossing text and JSON rendering | findings name the identifier but never reproduce the associated value
suppression-location | the new P004 finding crossing the existing line filter | a reason on the line or line above suppresses while a bare pragma does not
classification-drift | new P004 logic beside existing P001 and P002 checks | shell and string-command specimens retain their prior codes
prose-gate-arity | changed prose crossing the Brevitas CLI | one process receives one file and any failed file makes the subshell fail
partial-run | an interrupted lint or test before its final status | no clean result or receipt is accepted from incomplete or non-zero commands
ledger-integrity | generation bookkeeping at the mature Phylax frontier | only generation advances while the revision current text next job and digest remain unchanged
```

There is no funds arithmetic, blockchain call, upgrade path or signing-key
custody in this checker. Secret custody is limited to reading source that may
name a credential and ensuring its value does not enter findings. The checker
adds no subprocess or write; existing bounded reads and P000 failure behavior
remain unchanged.

## 6. glossary seeds

- `argv expression`: the AST node passed as a subprocess runner's `args`,
  either first positional or explicit `args=`.
- `credential-named value`: an `ast.Name` whose identifier matches the
  existing `CREDENTIAL` expression; it is name evidence, not proof of a live
  secret.
- `resolved runner`: a call `_starts_process` ties to `subprocess` through a
  module import, module alias, direct import or direct-import alias.
- `safe neighbour`: nearby syntax that must remain clean and fixes the
  false-positive boundary.
- `source-local`: decided within the current call expression without following
  earlier assignments, imported values or runtime state.
- `generation row`: a behavior change that increments the second skill counter
  while retaining the frontier revision and digest.
- `per-file prose gate`: one Brevitas process with one draft positional,
  repeated for each changed prose file with failure propagated.

## 7. sources and checks

Primary sources:

- Issue #325: <https://github.com/wildcat-finance/skills/issues/325>.
- Starting ref: `4408597bcd0130b0cee8bd7aab0b55d64ff957c7`.
- Issue census ref named by #325:
  `3c061c2e15df085cf300220250b421bbd03f664c`.
- `plugins/hexaemeron/skills/phylax/scripts/phylax.py`, especially
  `RUNNERS`, `CREDENTIAL`, `_starts_process` and `Visitor.visit_Call`.
- `plugins/hexaemeron/tests/test_phylax_checker.py`, especially
  `ShellInvocation`, `StringCommands`, `Credentials` and `Suppression`.
- `plugins/hexaemeron/skills/phylax/SKILL.md`, `EVOLUTION.md`, and
  `plugins/hexaemeron/skills/VERSIONING.md`.
- `plugins/brevitas/skills/brevitas/scripts/brevitas.py --help`.
- `plugins/ariadne/scripts/ariadne_lib/scrub.py` and
  `plugins/ariadne/tests/test_capture_scrubbing.py`.
- `audit/AUDIT.md`, `Phylax TypeScript boundaries`, rounds 1 and 2.
- Pull requests #103, #193, #426 and #441 in `wildcat-finance/skills`.
- MITRE CWE-214 and Python 3.12 `subprocess` documentation linked above.

Checks run during this study:

- `git rev-parse HEAD` and `git rev-parse main` both returned the starting
  commit above; the worktree was clean before this file was written.
- A current public read found issue #325 open, unassigned, with no comments or
  linked development branch.
- The inline `API_TOKEN` specimen returned `[]` before implementation.
- `python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker` passed
  46/46 on Python 3.9.6.
- The same focused command passed 46/46 through uv Python 3.12.13.
- `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
  exited zero and printed `clean`.
- The frontier digest was recomputed from the exact canonical line and matched
  the `phylax-v1.1.0` history row.
- The preserved predecessor patch was inspected to confirm the accepted option
  and fixture boundary, then left unapplied. Its failed multi-file Brevitas
  command was checked against the current one-positional CLI.
- Public organisation search found no reusable analyser; this is negative
  search evidence, not proof of absence.

These observations establish the current gap and a buildable boundary. They
do not establish that Option A is implemented correctly or that its future
tests and audit rounds pass.

## 8. signals and the questions behind them

`plugins/hexaemeron/skills/ephoros/SKILL.md` does not add an implementation
gate because this change introduces no unattended service, route, persistent
job or alert. The existing CLI already answers the two operator questions:

1. Which source location failed? Text exposes `path:line`, P004 and its fixed
   message; JSON exposes the same fields separately.
2. Did the selected scan complete cleanly? Exit zero and final `clean` answer
   yes. A finding, parse failure, bad invocation or interruption cannot supply
   that clean completion evidence.

No new event, metric, trace, correlation id or alert is warranted. The runbook
should test the present signal shape rather than invent telemetry for a local
lint.

## 9. boundaries per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` applies to the new capability:
untrusted Python source crosses the AST visitor and influences a P004 result.
What is worth taking is the credential value and confidence in a clean lint.
Controls are parse-only inspection, existing import-based runner resolution,
argv-only selection, source-local AST walking, safe-neighbour tests,
secret-free output and fail-closed commands. The risk ids `runner-identity`,
`argv-selection`, `name-recursion`, `safe-neighbour`, `secret-diagnostic` and
`partial-run` enumerate the review.

Changed prose also crosses the Brevitas CLI. `prose-gate-arity` closes that
boundary with one file per process and failure propagation from the subshell.
No new host, dependency, launched subprocess in Phylax, output path, agent tool,
network input or checker filesystem write is introduced.

## 10. budget or its absence

`plugins/hexaemeron/skills/metron/SKILL.md` has no performance gate here. Issue
#325 makes no speed, memory or latency claim, and Option A walks one subtree of
an AST already built for the file. No speed-motivated change is authorized, so
there is no baseline or budget to manufacture. The focused suite is a
correctness gate, not a benchmark.

## 11. fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` governs the reproduced miss and
any new failure. The hostile fixture must be observed red against the current
visitor and green after the cause-level change. A safe-neighbour finding,
secret value in output, changed P001/P002 classification, ledger mismatch,
Brevitas file failure or any non-zero required command stops the step. The
focused guard and both suites must be green before work resumes. Existing P000
parse and read failures keep their fail-closed behavior.

## 12. decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` places this skill-local behavior
decision in `plugins/hexaemeron/skills/phylax/EVOLUTION.md`. Its generation row
should record the source-local argv walk, the deliberately rejected dataflow
scope and pointers to the shipped study and tests while leaving the mature
frontier unchanged.

Exact copies of the receipted study and runbook belong at
`docs/phylax-credential-argv/study.md` and
`docs/phylax-credential-argv/runbook.md`; audit rounds append their evidence to
`audit/AUDIT.md`. No repository-wide ADR is justified because the change adds
no shared schema, dependency, storage layout or cross-skill trust boundary.
If implementation needs a wider analysis boundary, change this study before
the code; a generation row cannot smuggle in a frontier change.
