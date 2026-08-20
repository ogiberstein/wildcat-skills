# Study: park a blocked Kronos job instead of stalling the loop

Assuming, unless corrected:

1. Python 3.11 or later and stdlib `unittest`, matching every other checker in
   this plugin.
2. A parked job is Kronos's own working state, kept beside the scoreboard that
   shipped in `kronos-v0.3.0`, and not published.
3. Kronos keeps its hard rule that Fiat owns all repository work. Nothing here
   runs git.
4. This is generation-axis work. Kronos stays mature, the held frontier target
   and its digest are retained byte for byte, and the run passes no
   `--frontier` flag.
5. The run starts from `36f1e2e` on `main`, with both suites green at 34/34
   and 414/414.

## 1. Problem statement

Kronos today offers two responses to a Fiat run that halts on a blocker it
cannot clear:

> If Fiat halts on a genuine external blocker, preserve the durable goal and
> report that blocker; do not skip to a lower-scoring job to make the loop look
> busy.

Preserve and report, or skip and be dishonest. There is no third. So a top-
ranked job blocked on an approval nobody will grant this week stops the whole
frontier, and every other eligible skill waits behind it. The refusal to skip is
right; what is missing is a way to set the blocked job down without dropping it.

The interaction that makes this more than a prose change: `scripts/kronos.py`
refuses with K006 when the recorded `selected` is not what the tie-break picks.
A loop that continues past a blocked top candidate selects the second, so the
writer refuses the pass. Parking has to be visible to the writer or the loop
cannot record a pass at all once anything is parked.

What is built: a parked lane. A park records the halt reason verbatim against
the blocked skill's held job, selection skips parked candidates without dropping
them from the ranking, and the loop cannot declare itself complete while a park
stands.

A working prototype means all of this holds:

- `kronos.py park` appends a park carrying the skill, its held-job identity
  hash computed from the ledger, and the halt reason byte for byte as given.
- `kronos.py unpark` appends a release carrying its own reason.
- `kronos.py parked` prints the standing parks and exits non-zero while any
  stands, so a loop cannot call itself complete over one.
- A pass whose candidates carry `parked: true` is accepted with the highest
  unparked candidate selected, and still refused when the selection is not the
  highest unparked one.
- `python3 plugins/hexaemeron/tests/run_tests.py` passes with the new cases.
- The demo path: park a skill, record a pass that selects the next-ranked
  candidate, see `parked` exit non-zero, unpark, and see it exit 0.

## 2. Prior art

**In this skill.** `SKILL.md` step 4 selects the highest score and breaks ties
by impact, then readiness, then discovery order. Step 6 records the pass. The
stop text above is the whole of the current blocker handling. The hard rules
forbid altering a held Next Fiat job before its frontier job completes, which
is what keeps a park from quietly rewriting the thing it is parking.

**In the scoreboard that shipped last.** `scripts/kronos.py` holds `record` and
`show`, the axis caps, the `tie_break` function implementing step 4, the
`held_job_hash` computed from a ledger's canonical frontier line, and
`existing_passes`, which validates a JSON Lines file line by line before
appending. K006 is the check a parked lane must teach about parking.

**The identity hash decides resolution.** `VERSIONING.md` gives each ledger a
canonical frontier line whose digest changes when the held job changes. A park
recorded against that digest can therefore be told apart from a park whose job
has since moved on, without asking anyone.

**In Fiat.** `hexctl halt --reason` writes `{"reason": ..., "ts": ...}` into run
state and every progress command refuses until `resume`. That is the shape a
halt reason arrives in, and the reason string is what a park has to carry
unaltered.

**Outside.** JSON Lines again, as `.hexaemeron/ledger.jsonl` and
`.kronos/scoreboard.jsonl` already use.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `36f1e2e` on `main`.
- Python 3.11 or later, stdlib only. No new dependency.
- Nothing here runs git, and nothing written may be visible to
  `git status --short`, or Fiat's next run cannot start against a dirty tree.
- The halt reason is recorded verbatim. Summarising it loses the thing a
  maintainer needs to judge whether the blocker still stands.
- `tests/test_version_propagation.py` requires the frontmatter version and the
  ledger's current version to agree, so the bump and the row land together.
- Frontier revision `terminal-goal-loop` and digest
  `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` are
  retained byte for byte. Kronos stays mature.

**Non-goals.**

- No judgement about whether a blocker is genuine. A park is a claim the loop
  records, not one it evaluates.
- No automatic unparking. A held job that moved is reported as stale, and a
  person decides.
- No expiry, no reminders, no scheduling.
- No change to the four axes, their caps, or the tie-break among unparked
  candidates.
- No parking of a skill that was never ranked.

## 4. Design options

**A. Prose contract only.** State the parked lane in `SKILL.md` with no
machinery. Cheapest to write, and it cannot work: K006 in the shipped writer
refuses a pass whose selection is not the tie-break's pick, so a loop obeying
the new prose could not record its passes. A rule the existing code contradicts
is worse than no rule.

**B. A separate `.kronos/parked.jsonl`, and a `parked` flag on candidates.**
`park`, `unpark` and `parked` subcommands in the same `kronos.py`, appending to
their own file; `record` accepts `parked` on a candidate and applies the
tie-break to unparked candidates only. Trades away a single place to look: the
loop's state is then two files rather than one.

**C. Park records inside `scoreboard.jsonl`.** One file, one reader. Trades away
what the scoreboard is: an append-only history of passes, where each line is
what was true at that moment. Parking is current state that changes, so the
standing set would have to be replayed out of a file whose other lines are
history, and a reader could no longer take one line at face value.

**D. A separate script.** `parked.py` beside `kronos.py`. Trades away the shared
code both need, `held_job_hash` and `existing_passes` and the refusal
vocabulary, for a boundary between two things that always run together.

**Chosen: B.** The two files hold different kinds of thing, which is C's real
cost, and they share one script and one refusal vocabulary, which is D's. The
extra file is the honest price of keeping the scoreboard's lines readable on
their own. A is not on the table once K006 is read.

## 5. Risk register seed

Python reading files named on a command line and a reason string from a caller.
The audit loop should look hardest at:

- **The reason string.** It arrives from a caller, is stored verbatim by
  requirement, and is printed later. Embedded newlines would break the JSON
  Lines file for every later read if the writer were careless, and an
  unbounded reason is a caller-controlled write.
- **Replay correctness.** The standing parked set is derived by replaying park
  and unpark records in order. An unpark for a skill never parked, two parks
  for one skill, and a park after an unpark all have to resolve to something
  defined rather than to whatever the loop happens to produce.
- **The stale test.** A park is compared against the ledger's current identity
  hash. A ledger that has since been deleted, or that no longer parses, must
  not read as resolved.
- **Selection under parking.** The tie-break now runs over a subset. Every
  candidate parked has to be refused rather than silently selecting nobody.
- **Partial writes and paths.** The same append and path concerns the scoreboard
  already carries, since this is a second file in the same directory.

## 6. Glossary seeds

- **Park.** A record that a ranked candidate's held job is blocked, carrying the
  reason verbatim and the held-job identity hash at the time.
- **Standing park.** A park with no later unpark for the same skill.
- **Stale park.** A standing park whose skill's ledger now shows a different
  held-job identity hash, so the job it named has moved on.
- **Unparked candidate.** A candidate with no standing park, and the only kind
  selection may pick.

## 7. Sources

- `plugins/hexaemeron/skills/kronos/SKILL.md`, steps 4 and 6, the stop text and
  the hard rules.
- `plugins/hexaemeron/skills/kronos/scripts/kronos.py`, `tie_break`,
  `held_job_hash`, `existing_passes` and refusal K006.
- `plugins/hexaemeron/skills/kronos/EVOLUTION.md`, `kronos-v0.3.0`, `mature`.
- `plugins/hexaemeron/skills/VERSIONING.md`, the canonical frontier line and the
  generation-axis rule.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `cmd_halt`, for the shape
  a halt reason arrives in.
- The wishlist entry `kronos-2`, artifact `wishlist-grab-bag.md`.

## 8. Signals, and the questions behind them

The parked lane is a record someone reads after a long unattended loop. Two
questions:

- *Why did the loop pass over its top-ranked job?* Answered by the standing park
  for that skill, carrying the halt reason verbatim. Emitted when the park is
  made, and printed by `parked`.
- *Is anything still waiting on a person?* Answered by `parked` exiting non-zero
  while a park stands, so the loop's own completion check carries it rather than
  a human remembering.

`parked` prints to stdout and refusals go to stderr with a code, as `record`
already does. [ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what
a signal must carry.

## 9. Boundaries, per capability

- **The reason string from the caller.** Worth taking: an unbounded string, or
  one carrying newlines or control characters. Control: cap its length, refuse
  an empty one, and store it through `json.dumps`, which escapes a newline
  rather than splitting the record.
- **Appending to a second file in `.kronos/`.** Worth taking: a truncated tail
  from an interrupted run, and a symlink at the path. Control: the same ones
  `record` already applies, validating every existing line before appending and
  refusing a symlinked path before resolving it.
- **Reading a candidate's ledger to test staleness.** Worth taking: a ledger
  that has been deleted or no longer parses. Control: report it as unknown
  rather than resolved, and never let an unreadable ledger clear a park.
- **The parked flag on a pass candidate.** Worth taking: a pass claiming
  everything is parked, or claiming a park that was never recorded. Control:
  refuse a pass with no unparked candidate, and check the claimed flags against
  the standing parks rather than trusting the caller.

[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list
and the controls.

## 10. The budget, or its absence

None. A park happens at most once per halted Fiat run, and a Fiat run takes
hours. No performance claim is made and nothing here is changed for speed, so
[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) has nothing to measure.

## 11. The fail-closed posture

Every refusal exits non-zero and appends nothing. What stops the run: an empty
or oversized reason, a park for a skill with no readable ledger, an unpark with
no standing park to release, a pass whose candidates are all parked, a pass
whose parked flags disagree with the standing parks, and any of the path and
tail failures the scoreboard already refuses.

`parked` is the exception that must exit non-zero on success of a sort: a
standing park is not an error in the tool, it is the loop's reason not to finish.
That distinction goes in the skill text so nobody reads the exit code as a bug.

Guard-test convention: a fix for a failure found here adds a case to
`plugins/hexaemeron/tests/test_kronos_scoreboard.py` that fails on the unfixed
tree, following
[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md).

## 12. Decisions and their homes

Three decisions here are expensive to reverse, and all three are decisions about
a governed skill, so all three belong in
`plugins/hexaemeron/skills/kronos/EVOLUTION.md` per
[hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md):

- Parks live in their own file rather than in the scoreboard. Reversing it means
  rereading every scoreboard line as possibly-state.
- The held-job identity hash decides whether a park is stale. Reversing it means
  every recorded park loses the thing that dates it.
- A standing park blocks the loop's completion rather than warning about it.
  Reversing it turns the lane back into a note nobody has to act on.

The generation row recording all three lands in step 3, with the version bump
`tests/test_version_propagation.py` requires to agree with it.

## Boundaries

**Always.** Both suites before a commit: `python3 -m unittest discover -s tests
-p "test_*.py"` and `python3 plugins/hexaemeron/tests/run_tests.py`. The
imprimatur lint on every shipped document. The halt reason stored byte for byte
as given. Kronos's frontier revision and digest retained in any ledger edit.

**Ask first.** Adding a dependency. Changing the four axes, their caps or the
tie-break among unparked candidates. Changing the scoreboard's existing record
shape. Writing anywhere git can see. Touching CI.

**Never.** Run git from Kronos. Commit the parked file. Summarise or truncate a
halt reason. Unpark on the loop's own judgement. Select a parked candidate.
Change the held `Next Fiat job` or reopen the mature frontier. Delete a failing
test to make a suite pass. Claim a lint or a suite ran when it did not.
