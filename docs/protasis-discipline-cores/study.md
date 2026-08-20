# Study: the discipline cores in the contract, and the checker that reads them

## Assumptions

Assuming, unless corrected:

1. Stdlib `unittest` and no new dependency, matching every other checker in
   this plugin. The interpreter here is 3.14.6, so nothing may rely on a
   version-specific feature newer than that or removed before it.
2. The checker lives at `plugins/hexaemeron/skills/protasis/scripts/protasis.py`
   and its tests at `plugins/hexaemeron/tests/test_protasis_checker.py`, which
   is where the other five discipline checkers and their tests already sit.
3. Both suites means the two commands `AGENTS.md` documents for this area:
   `python3 -m unittest discover -s tests` for the root suite and
   `python3 plugins/hexaemeron/tests/run_tests.py` for the plugin suite, which
   has its own runner rather than a discover invocation.
4. The frontier closes in this run, so `EVOLUTION.md` gains exactly one row and
   `SKILL.md` frontmatter moves to the matching label.
5. This study and its runbook are themselves written under the grown contract,
   so the runbook carries a Disciplines line per step from the start.

## 1. Problem statement

Protasis states what a study and a runbook must contain, and every rule it
states is read by a person. Two gaps follow from that.

The first is coverage. The five discipline skills beside it (`ephoros`,
`phylax`, `metron`, `elenchus`, `hypomnema`) each own a body of rules that a
step either exercises or does not. Nothing in the study contract asks which,
so every run rediscovers them mid-flight, in the audit loop, where a missed
boundary costs a step rather than a sentence.

The second is enforcement. A step missing its exit command is invisible until
someone reads the runbook carefully, and the phase that reads it carefully is
the one that has already started building.

Both are settled here. The contract grows five mandated study answers and a
per-step Disciplines line; a checker then reads a runbook and refuses one that
omits any required field.

**What a working prototype means here.** A checker that exits non-zero on a
fixture runbook missing each field in turn, exits zero over this run's own
runbook, and leaves both suites passing.

**Demo path.**

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/protasis-discipline-cores/runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

## 2. Prior art

In this repository:

- `plugins/hexaemeron/skills/protasis/SKILL.md`, the contract being grown.
  "What a study must answer" holds seven items; "What a runbook step must
  contain" holds the step schema; "Before the runbook is receipted" holds the
  checklist those two feed.
- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, the closest
  model. A Markdown lint with coded findings, a `Finding` class carrying path,
  line, code and message, `--format text|json`, and exit 0 clean, 1 findings,
  2 bad invocation. Deliberate exceptions carry a reason in an HTML comment.
- `plugins/hexaemeron/skills/{ephoros,phylax,metron,elenchus}/scripts/`, four
  further checkers on the same shape, each with a test file named
  `test_<skill>_checker.py` under `plugins/hexaemeron/tests/`.
- `plugins/hexaemeron/skills/VERSIONING.md`, the label contract. Evolution
  increments once per completed frontier job; the row stores the SHA-256 of
  `{status}|{frontier revision}|{current frontier}|{next Fiat job}` including
  its final newline.

Outside: none needed. This is a convention-scanner over one repository's own
document shape, not an implementation of a published standard.

## 3. Constraints and non-goals

- Starting ref `main` at `2b92c6f`.
- Python 3.11, stdlib only. Adding a dependency is an ask-first boundary and
  this run does not need one.
- The five discipline cores are cited, never restated. Content rules live in
  exactly one skill under the v3.3.1 architecture, and with phase-only Kronos
  evolving all six ledgers a restated manifest would go stale continuously.
  Citations are relative paths to sibling `SKILL.md` files, which resolve from
  `PLUGIN_ROOT`.
- Non-goal: judging the *quality* of a discipline answer. The checker reads
  whether a required field is present and whether an exit names a command. It
  does not decide whether the named boundaries are the right boundaries.
- Non-goal: checking the study. The held job names the runbook, and the study
  has seven prose sections whose presence a parser can confirm but whose
  substance it cannot. Deferred, and recorded as the successor frontier.
- Non-goal: wiring the checker into Fiat's audit round. That is a Fiat change,
  not a Protasis one.

## 4. Design options

**A. Line scanner over the step-heading convention.** Walk the Markdown, split
on `## Step N:` headings, and require a labelled line per field within each
step's span. Stdlib `re`, no parser. Trade: it reads a convention, so a runbook
written in some other shape is invisible to it rather than refused. Mitigated
by stating the convention in the contract the checker enforces.

**B. Markdown AST via a dependency.** Parse properly, walk nodes. Trade: a new
dependency for a document shape this repository already fixes by convention,
and every other checker here is stdlib-only. Rejected on the dependency.

**C. Structured sidecar.** Require a JSON file per runbook and validate that.
Trade: precise, but it duplicates the human-readable runbook and the two drift.
Fiat already keeps `steps.json` for ordering; widening it into the field
carrier would move the contract out of the document people read. Rejected.

**Chosen: A.** Cheapest to comprehend, matches the five checkers already
shipped beside it, and adds nothing to install. What it trades away is
tolerance of an unconventional runbook shape, which is acceptable because the
contract states the shape.

## 5. Risk register seed

Python, so: untrusted input, subprocess and filesystem handling, secret
material, partial writes, and what happens when a long run is killed halfway.

- **Path handling.** Paths arrive on argv. A directory walk that follows links
  out of the repository, or a path that escapes an intended root, reads files
  nobody asked for. No subprocess and no network are involved, so those two
  surfaces stay closed by construction.
- **Hostile document content.** A runbook is a text file from outside the
  process. A regex over unbounded input is a denial surface; a document with
  thousands of headings should bound rather than hang.
- **Miscount as false confidence.** A checker that silently finds no steps and
  exits zero is worse than no checker: it reports clean over a file it never
  understood. An empty step set must be a finding, not a pass.
- **The ledger update.** Writing `EVOLUTION.md` more than once, or with a
  digest computed over the wrong line, corrupts the record the versioning
  contract checks. This repository has already had to reconstruct two broken
  evolutions.

## 6. Glossary seeds

- **Discipline core.** The body of rules one of the five sibling skills owns.
- **Disciplines line.** The runbook step field naming which gates apply and
  why, or `none` with a reason.
- **Required field.** One of goal, entry, exit, files, tests, disciplines.
- **Step span.** The lines that one `## Step N:` heading owns before the next.
- **Finding.** One refusal, carrying path, line, code and message.

## 7. Sources

- `plugins/hexaemeron/skills/protasis/SKILL.md`, `EVOLUTION.md`
- `plugins/hexaemeron/skills/{ephoros,phylax,metron,elenchus,hypomnema}/SKILL.md`
- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`
- `plugins/hexaemeron/skills/VERSIONING.md`
- `plugins/hexaemeron/skills/fiat/SKILL.md` and its `references/`

## 8. Ephoros: the on-call questions

No unattended surface. The checker is invoked from a terminal or from an audit
round and reports through stdout and an exit code; nothing here runs on a timer,
holds a queue, or wakes anyone at three in the morning. There are no on-call
questions to write, and emitting telemetry for a lint would be volume.

Stated explicitly rather than left blank, because the contract this run writes
requires either the questions or the reason there are none.

## 9. Phylax: boundaries per capability

| Boundary | Worth taking | Control |
| --- | --- | --- |
| Path arguments on argv | Reads outside the intended tree | Resolve, then refuse a file outside the roots given; do not follow directory links out |
| Runbook file content | Hang the run, or a wrong verdict | Treat as data, bound the read, keep patterns linear, cap the step count |
| No subprocess | none | Closed by construction; nothing shells out |
| No network | none | Closed by construction; nothing fetches |
| No secrets | none | The checker reads documents and holds no credential |

Feeds the risk register above, which is where the audit loop reads it.

## 10. Metron: the budget

No budget. The checker reads a handful of Markdown files in one pass; there is
no performance requirement to hold and no measurement to record. Stated
explicitly, per the contract.

## 11. Elenchus: the fail-closed posture

**What stops the run.** A non-zero exit from either suite. The checker
reporting a finding over this run's own runbook. A `verify` failure on the
controller ledger.

**Guard-test convention.** Every fix lands with a test in
`plugins/hexaemeron/tests/test_protasis_checker.py` that fails on the tree
without the fix and passes with it. A fix arriving without one is unguarded and
goes to the audit file's leads-not-pursued list rather than being waved
through.

## 12. Hypomnema: decisions and where each lives

| Anticipated decision | Expensive to reverse because | Home |
| --- | --- | --- |
| The finding-code vocabulary `P001` onward | Audit rounds and any later Fiat integration cite codes; renumbering breaks every citation | `plugins/hexaemeron/skills/protasis/EVOLUTION.md` |
| The step-heading and field-label convention | Every runbook written after this is shaped by it | `SKILL.md`, as the stated contract |
| Closing this frontier and naming its successor | The ledger is the authority the versioning contract checks | `plugins/hexaemeron/skills/protasis/EVOLUTION.md`, one row |

A decision about a governed skill belongs in that skill's ledger, not under
`docs/decisions/`, per hypomnema's own placement rule.

## Boundaries

**Always.** Both suites before a commit. The imprimatur lint on every shipped
document. Cite a sibling contract rather than restating it.

**Ask first.** Adding a dependency. Changing the finding-code vocabulary once
published. Touching CI. Widening what the checker reads beyond the paths it was
given.

**Never.** Commit key material or a credential. Delete a failing test to make a
suite pass. Claim a lint, a suite or an audit round ran when it did not. Write
the ledger more than once in a run.
