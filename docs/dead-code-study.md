# Study: a report-only dead-code baseline

Issue [#437](https://github.com/wildcat-finance/skills/issues/437),
framework-introspection-4. Run branch
`fiat/437-establish-a-report-only-dead-code-baseline`, cut from `main` at
`8de7a4bc910e398107ff2f54a4cf92a82e764a76`.

Assuming, unless corrected:

1. Python 3.11 or later and the standard library only. The repository carries no
   third-party Python dependency today and every suite is stdlib `unittest`.
2. The analysed universe is the git-tracked tree at one commit, not the working
   tree. A dirty checkout is refused rather than analysed.
3. `.horos/boundary.json` is present and describes the current tree. The root
   suite already fails when it does not, so this command may read it as given
   and refuse when it cannot.
4. Slither 0.11.6 and forge 1.7.1 exist on a developer machine and not in CI.
   The Solidity lane has to report their absence rather than report nothing.
5. A root command that makes a checkable claim registers a Promise Machine
   capability. Both root commands that make one already do.
6. The command ships as `scripts/dead_code.py`, matching the plain names of the
   three root commands already there rather than the Greek register used for
   marketplace skills.

The issue states that Protasis decides which skill this upgrades. The answer is
none of them. Every deliverable is repository tooling at the root, no skill
ledger moves, and no frontier row is owed. Assumption 5 is the only place a
plugin tree is touched, and there only by the generated Promise copies.

## 1. Problem statement

Add one deterministic command that lists what it analysed and reports dead-code
candidates from bounded signals, each finding carrying the evidence that
produced it. It deletes nothing and authorises no deletion.

The repository is 1,512 tracked files, 355 Python files, 84 Solidity files and
sixteen separate test suites. Each suite passes on its own, which is exactly the
condition under which an abandoned function survives: nothing that runs reads
the whole tree at once. Berean finding `B3-R1-02` records a dead constant and an
unused import surviving drafting and being caught in an audit round rather than
by any check. Ariadne finding `S4-R1-02` records a manifest field that was
required and never read.

A working prototype is this, run from the repository root on a clean checkout:

```bash
python3 scripts/dead_code.py report
python3 scripts/dead_code.py report --json
```

The first prints a text report. The second prints the same findings as JSON. The
demo path proves four things a reader can check: the universe is not empty, the
two formats carry the same findings, every finding names its analyser and its
evidence, and the process exits zero with candidates outstanding.

Success criteria, each checkable by a command:

- `python3 scripts/dead_code.py report --json` exits 0 and reports a universe of
  more than a thousand analysed paths on this repository.
- `python3 -m unittest discover -s tests` stays green and gains the new tests.
- The positive fixture tree yields at least one finding from each of the three
  analyser families.
- The negative fixture tree yields no finding for a dynamically registered
  plugin, a declared CLI entry point, an intentionally unused test fixture, or a
  path Horos classified as generated or vendored.
- `python3 scripts/dead_code.py baseline --check` exits non-zero when the
  recorded commit or an analyser version no longer matches.
- `python3 scripts/dead_code.py report` exits non-zero when discovery returns an
  empty universe or an analyser crashes.
- `python3 scripts/promise_machine.py check` stays clean with the new capability
  registered.

## 2. Prior art

In this repository:

- `scripts/run_observation.py`, 2,334 lines, from issue #434. The closest
  template. It is one root command with subcommands, a `--json` flag emitting
  canonical JSON, a registered Promise capability at `PROMISE_MACHINE.md` line
  192, a schema under `schemas/`, fixtures under `tests/fixtures/run-observation/`
  and a coverage row in `tests/promise_machine_coverage.json` binding runtime and
  documentation by digest. The new command copies that shape.
- `scripts/promise_machine.py`, 2,956 lines, with `sync`, `check`, `inventory`
  and `coverage` subcommands. It owns the fourteen generated plugin copies of the
  root law, which is what makes a new promise section a fourteen-file change.
- `scripts/contributors.py`, 835 lines. Its audit history is the useful part.
  `S2-R3-01` and `S3-R2-01` are both failures of a tool reporting a degraded read
  as a normal one, which is the failure mode this command is most exposed to.
- Horos, at `plugins/horos/skills/horos/scripts/horos.py`, and its committed
  `.horos/boundary.json`. It already classifies every tracked path as generated,
  vendored, binary, lockfile or content-addressed, with an evidence string and a
  hard or candidate grade per entry. Its `map` subcommand prints a Python
  skeleton. AGENTS.md draws the marketplace boundary in one line: Horos decides
  what an agent does not read. Deciding what nothing reaches is a different job,
  which is why this is a root command and not a wider Horos.
- `audit/AUDIT.md`, 12,400 lines. Read for this study. Three records bear on the
  design. `B3-R1-02` and `S4-R1-02` are named above. The third is the Pandects
  record at line 673, where a generated harness was deliberately not produced
  because it would land in a directory the plugin documents as unreachable, and
  the round recorded that as a judgement rather than a waiver. A directory a
  plugin documents as unreachable is exactly what a naive analyser reports as
  dead, so the retained-path classification is not a nicety.

The last two merged pull requests touching the root scripts are
[#548](https://github.com/wildcat-finance/skills/pull/548) and
[#536](https://github.com/wildcat-finance/skills/pull/536). Both were read.
#548 carries two open items forward: whether the Actions token may open a pull
request, and whether a Contents API write satisfies the signed-commit ruleset.
Both belong to the contributors workflow and neither is answered here; the CI
lane this run adds is read-only and opens nothing. #536 carries forward the
finding that GitHub's native stacked-pull-request flow re-signs rewritten
commits and destroys Shoggoth signatures. That one is answered by construction:
this run lands as one integration pull request from a stack that is never
rebased.

Outside this repository, the standard tools were considered and are addressed in
item 4: `vulture`, `ruff` rules F401 and F841, `coverage.py` branch coverage,
Slither's `dead-code` and `unused-state` detectors, and `forge coverage`. None of
the Python ones is installed here.

## 3. Constraints and non-goals

Constraints:

- Starting ref `8de7a4bc910e398107ff2f54a4cf92a82e764a76` on `main`.
- Standard library only. Adding a Python dependency is an ask-first boundary and
  this run does not take it.
- Slither 0.11.6 and forge 1.7.1 are the pinned external analysers, and both are
  optional at run time.
- The command is read-only over the source tree. It writes only its own report
  and baseline artefacts.
- Two pull requests are open against `main` that touch shared manifests, #542
  and #539. `PROMISE_MACHINE.md` and `tests/promise_machine_coverage.json` are
  the collision surface, and both are rebuilt from the base at integration
  rather than resolved to one side.

Non-goals, deferred past this prototype:

- **Branch coverage.** The issue names it. Delivering it needs either
  `coverage.py`, which is a dependency this run will not add, or
  `sys.monitoring` branch events, which are available on Python 3.14 here and not
  on every version this repository supports. The command therefore reports
  coverage as a named signal that was not established, rather than omitting it.
  This is the one place where the run knowingly falls short of the issue text,
  and it is stated here rather than discovered at the acceptance check.
- Type checking. The issue mentions a type lane in passing while describing the
  gap; nothing in its acceptance list requires one.
- Any deletion, rewrite or automatic cleanup.
- Turning newly introduced findings into a diff gate. The issue defers this
  itself.
- A database, dashboard or backup service.

## 4. Design options

**A. One root command, stdlib analysers, Horos supplies classification.**
Discovery from `git ls-files` at the analysed commit; `.horos/boundary.json` read
to mark generated, vendored, binary, lockfile and content-addressed paths;
Python analysed through `ast`; Solidity through Slither when it is present;
repository-graph checks written against the manifests they read. Trades recall
for determinism, and depends on nothing that is not already here.

**B. The same command, shelling out to third-party analysers.** `vulture` and
`ruff` raise Python recall and `coverage.py` supplies the branch signal the
issue asks for. It costs the repository its first Python dependencies, makes a
report depend on which machine produced it, and forces CI to pin an install
before the lane can run at all.

**C. Widen Horos.** The classification half already exists there and the walk is
written. It breaks the marketplace boundary AGENTS.md states in one line, and it
attaches a deletion-candidate claim to a skill whose promise is about reading
cost. A skill's promise is the expensive thing to reverse.

**D. Per-plugin analysers, run by each plugin's own suite.** Each suite stays
self-contained. It cannot see across plugins, so the orphaned fixture, the stale
manifest entry and the generated copy nobody regenerates all survive, and those
are the findings the issue exists for.

**Chosen: A.** It is the cheapest to comprehend, it meets every acceptance item
except the deferred coverage signal, and it adds no dependency. What it trades
away is recall: a stdlib analyser will miss dead code that `vulture` finds. That
is acceptable only because the deliverable is a baseline that reports what it
looked at, so a missed finding reads as an unanalysed signal rather than as a
clean bill. B stays available later behind the same finding model, and the
analyser registry is built so that adding one is a registration rather than a
rewrite.

## 5. Risk register seed

The command reads every tracked file in the repository, parses untrusted source,
spawns two external analysers and writes two artefacts. The audit loop should
look hardest at the places where a degraded run could be mistaken for a clean
one, because both root-command audits above found exactly that defect.

```risk-register
discovery-collapse | the universe walk at the analysed commit | an empty or unexpectedly small universe stops the command rather than reporting zero findings
analyser-absent-as-clean | each analyser's availability check | an absent or crashed analyser is reported as not established and never as no findings
dynamic-reference-blindness | the Python reference graph | plugin discovery, importlib, getattr and decorator registration are recorded as reachability-defeating, and symbols reached only that way are not reported at high confidence
retained-path-misreport | the classification join with the Horos boundary | a generated, vendored or documented-unreachable path yields no finding, and the negative fixtures pin each case
subprocess-argv | the argv of slither and forge | arguments are a fixed list with no shell, paths come from the discovered universe, and a timeout bounds the wait
untrusted-parse | ast.parse over every tracked Python file | parsing never imports or executes the file, and a syntax error is a reported analyser status rather than a crash
path-confinement | every path the command reads or writes | paths resolve inside the repository root and anything outside is refused before the read or write
partial-write | the report and baseline files during a write | a killed run leaves no half-written artefact that a later check accepts
report-parity | the text and JSON emitters | both render from one finding model and a test asserts they carry the same findings and counts
baseline-staleness | the pinned baseline artefact | the baseline records the analysed commit and every analyser version, and a check reports a mismatch rather than comparing across them
suppression-abuse | the suppression file | each entry carries a narrow reason and a target that still exists, and an unmatched or unused suppression is itself a finding
manifest-collision | PROMISE_MACHINE.md and tests/promise_machine_coverage.json | the new rows are rebuilt from the base during integration rather than taken from either side of a merge
finding-overclaim | the wording of every emitted finding | no finding says a path is dead, unused or safe to delete; each says which analyser saw what, and names the nearest false-positive boundary
```

## 6. Glossary seeds

- **Universe.** The set of tracked paths analysed at one commit, with the reason
  any tracked path was excluded.
- **Analyser.** One bounded signal source with an identity and a version. Python
  AST, Slither, forge coverage and the repository graph are separate analysers.
- **Finding.** One candidate, carrying analyser identity, path, symbol or object,
  evidence, confidence and its nearest false-positive boundary.
- **Confidence.** High, medium or low, decided by which reachability-defeating
  constructs the analyser saw near the finding. It is never certainty.
- **False-positive boundary.** The nearest reason this finding could be wrong,
  named on the finding itself.
- **Classification.** Why a path was excluded from analysis: generated,
  vendored, content-addressed, binary or deliberately retained.
- **Retained.** A path or symbol kept on purpose, declared in the repository
  rather than inferred.
- **Suppression.** A declared, reasoned exclusion of one finding, checked for a
  target that still exists.
- **Baseline.** The report pinned to its analysed commit and analyser versions.

## 7. Sources

- Issue #437, framework-introspection-4, and the queue conventions in
  `AGENTS.md` and `docs/decisions/ADR-009-four-issue-queues-and-their-titles.md`.
- `AGENTS.md`, for the suite list, the lint list and the reading-boundary rule.
- `PROMISE_MACHINE.md` and `tests/promise_machine_coverage.json`, for what
  registering a root capability costs.
- `scripts/run_observation.py` and `docs/promise-machine/run-observation-v1.md`,
  as the template for a root command.
- `.horos/boundary.json`, `.horos/candidates.json` and
  `plugins/horos/skills/horos/scripts/horos.py`.
- `audit/AUDIT.md`, findings `B3-R1-02`, `S4-R1-02`, `S2-R3-01`, `S3-R2-01`, and
  the Pandects record at line 673.
- Pull requests #548 and #536.
- Slither detector documentation for `dead-code` and `unused-state`; the Foundry
  book for `forge coverage`.

## 8. Signals, and the questions behind them

Three questions, and the step that answers each. The command runs from a
terminal and from a scheduled CI lane, so the reader is looking at a report or a
job summary rather than a dashboard. Ephoros owns what a signal has to carry.

- *Did this run analyse anything, or did discovery quietly return nothing?* Every
  report opens with the analysed commit, the universe count and the count
  excluded per classification. Step 1 emits it and the CI lane fails on an empty
  or collapsed universe.
- *Which analysers actually ran here?* Each report carries one status line per
  analyser: ran with its version, absent, or failed with its reason. Steps 2, 3
  and 4 each add their own, and a missing status is a malformed report.
- *Did this change against the baseline, and where?* The baseline comparison
  names added and resolved findings by analyser and path. Step 5 emits it.

## 9. Boundaries, per capability

Phylax owns the boundary list and the control at each one. Four are opened here.

- **Reading every tracked source file.** Worth taking: the file is attacker-
  influenced only to the extent that a contributor wrote it, but a parse is not
  an execution. Control: `ast.parse` on bytes read from disk, never an import,
  never `eval`, and a syntax error becomes a reported analyser status.
- **Spawning Slither and forge.** Worth taking: a compiler and an analyser both
  execute project configuration. Control: a fixed argv list with no shell, a
  timeout, a working directory inside the repository, and absence handled ahead
  of the call rather than by catching a failure.
- **Reading `.horos/boundary.json` and the repository manifests.** Worth taking:
  a malformed or hostile JSON document steering the classification join. Control:
  shape validation before use, and a refusal that names the file.
- **Writing the report and baseline.** Worth taking: a path escape or a
  half-written artefact. Control: resolve inside the repository root, refuse
  outside it, and write atomically through a temporary in the same directory.
  `scripts/contributors.py` finding `S3-R2-01` is the record of what the litter
  from that pattern costs when it is not swept, and the same ignore convention
  applies.

## 10. The budget, or its absence

There is one, because a lane nobody waits for is a lane nobody keeps. The
stdlib analysers must finish over the whole repository inside sixty seconds on a
warm checkout:

```bash
time python3 scripts/dead_code.py report --analyser python,repository --json
```

Measured before and after any change made for speed, per Metron, and never
changed for speed without both numbers recorded. The Solidity lane carries no
budget: Slither and a Foundry build dominate it, both are optional, and a number
measured against an optional toolchain would not mean anything.

## 11. The fail-closed posture

Elenchus owns the triage order and the guard rule. Four conditions stop the
command with a non-zero exit rather than producing a report:

- Discovery returns an empty universe, or one smaller than the floor the
  baseline recorded.
- An analyser crashes, as distinct from being absent.
- The emitted report does not validate against its own schema.
- A suppression names a target that no longer exists.

Being absent is not one of them. An absent analyser is a status in the report
and a zero exit, because the command has to be usable on a machine without
Foundry.

Every fix in the audit loop lands with a test that is red on the unfixed tree
and green after, and the round records which test and that it was seen red.

## 12. Decisions and their homes

Hypomnema owns which decisions earn a record and where it lives. Two are
expected to be expensive to reverse:

- **That the baseline is report-only, and that classification is consumed from
  Horos rather than reimplemented.** This one gets an ADR under
  `docs/decisions/`. It settles the marketplace boundary question that option C
  raises and it is the decision a later diff gate would have to argue against.
  Its number is picked in the step that writes it, not now: ADR numbers are
  global, the tree holds up to ADR-021, and two pull requests are open that could
  claim the next one first.
- **The finding schema.** Recorded as the schema document itself under
  `schemas/`, with the capability documentation under `docs/promise-machine/`.
  A schema is its own record; a second prose copy of it would drift.

The deferred coverage signal is recorded in the integration pull request under
`## Carried forward`, not as an ADR. It is unfinished work rather than a
decision.

## Boundaries in force

**Always.** The root suite and every plugin suite covering a changed area,
before a commit. Imprimatur then Brevitas on every shipped document. Phylax,
Ephoros and Hypomnema from the root. The Horos boundary regenerated last, after
the tree is otherwise final. A recorded measurement before any change made for
speed.

**Ask first.** Adding a Python dependency. Changing the finding schema after
step 5 pins it. Touching a workflow other than the one this run adds. Editing
`PROMISE_MACHINE.md` outside the one new section. Reclassifying a path Horos
already classified.

**Never.** Delete or rewrite source from the command. Report a path as dead,
unused or safe to delete. Report an absent analyser as a clean one. Commit a
credential or an RPC endpoint. Edit a vendored directory. Delete a failing test
to make a suite pass. Claim a command ran when it did not.

### Amendment -- 2026-08-24

**What changed.** A line-and-function coverage analyser is in scope, as step 3.
Item 3 previously deferred the whole coverage signal; only branch coverage stays
deferred. Item 1 gains a criterion: the positive coverage fixture yields a
finding for a function no repository suite executes. Item 4's chosen design gains
a fourth analyser, and item 10's budget now says the coverage analyser sits
outside it and runs only when asked for by name.

**Why.** The original deferral treated coverage as one signal with two
unacceptable routes. A probe on Python 3.14 separated it into two. The executable
line set comes from `code.co_lines()` and the executed set from `sys.settrace`,
both documented and stable, and their difference identified the dead functions in
the probe correctly. What stays expensive is the set of arcs that could have been
taken, which is where a branch implementation's cost sits. The distinction also
follows the issue's own boundary: an unexercised branch of a live function is a
test-completeness fact, and the issue puts test completeness out of scope, while
a function nothing executes is a reachability fact and is exactly what this
command is for.

**Steps touched.** Step 3 is new. Steps 3 through 6 of the previous numbering
became steps 4 through 7; their content is unchanged. Step 1 gains this
amendment.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds;
exit holds.
