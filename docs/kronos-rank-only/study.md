# Study: add a rank-only reporting mode to Kronos

Assuming, unless corrected:

1. Python 3.11 or later and stdlib `unittest`, matching every other checker in
   this plugin.
2. A rank-only pass is worth recording. It is a ranking that happened, and the
   drift check exists to compare rankings.
3. Kronos keeps its hard rule that Fiat owns all repository work. Rank-only
   changes nothing about that; it stops before Fiat is invoked at all.
4. This is generation-axis work. Kronos stays mature, the held frontier target
   and its digest are retained byte for byte, and the run passes no
   `--frontier` flag.
5. The run starts from `0998786` on `main`, with both suites green at 34/34
   and 437/437.

## 1. Problem statement

Steps 1 to 4 of the Kronos loop produce the most decision-useful thing in the
plugin: every governed skill's held job, scored across four axes, with a
one-sentence basis each and a selection. Steps 5 to 8 then spend a week of Fiat
on the winner.

There is no way to ask for the first without buying the second. Worse, the
skill's own description tells anyone who wants only the ranking to go away:

> Use only when the user explicitly asks for Kronos or for a repeated ranked
> Fiat frontier loop. Do not use it for one ordinary Fiat delivery.

A maintainer deciding what next quarter looks like wants the table, not the
delivery. Today they either commit to the loop or rebuild the ranking by hand.

Two shipped mechanisms complicate this. The scoreboard records a pass at step 6
with a `run` naming the Fiat run it launched, and a rank-only pass launches
none. The parked lane bars a parked candidate from selection and blocks the
loop's completion, and a rank-only pass selects without completing anything.

What is built: a rank-only invocation that stops after selection and hands back
the table, a record that says a pass was rank-only rather than leaving a reader
to guess from a missing run link, and the ungoverned-skill report carried in
that record instead of evaporating with the chat.

A working prototype means all of this holds:

- `SKILL.md` states a rank-only invocation that stops after step 4, and the
  description admits it as a reason to invoke Kronos.
- A pass carrying `rank_only: true` is recorded with no `run`, and one carrying
  `rank_only: true` beside a `run` is refused, because a rank-only pass by
  definition launched nothing.
- A pass carries `ungoverned`, the in-scope skills found with no ledger, so the
  report step 2 already owes survives in the record.
- `show` marks a rank-only pass and prints its ungoverned list.
- `python3 plugins/hexaemeron/tests/run_tests.py` passes with the new cases.
- The demo path: record a rank-only pass over this checkout's real ledgers with
  an ungoverned skill named, then `show` marking it as rank-only and listing
  that skill.

## 2. Prior art

**In this skill.** Step 2 says to report an in-scope skill carrying no ledger
as ungoverned rather than dropping it, and that report exists only in chat.
Steps 3 and 4 score and select. Step 6 records the pass once Fiat's `init` has
named the run. The stop text and the parked lane both concern completing a
loop, which rank-only never claims to do.

**In the script.** `PASS_FIELDS` is `scope`, `mode`, `candidates`, `selected`
and `run`; `MODES` is `full` and `phase-only`. `record` already accepts a `run`
that is absent or null, so a pass with no run is representable today. It is not
distinguishable: a rank-only pass and a pass whose run link was never filled in
look identical.

**The field-drift guard.** `kronos-v0.3.0` shipped a check that every field the
script accepts is named in `SKILL.md`'s Scoreboard section. A new field and its
documentation therefore land in the same step, which the runbook has to
respect.

**The parked lane.** `kronos-v0.4.0` bars parked candidates from selection and
exits 3 from `parked` while any stands. Selection under rank-only is the same
selection, so parks apply to it unchanged.

**Outside.** Nothing. This is a contract change to one skill and two fields on
a record it already writes.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `0998786` on `main`.
- Python 3.11 or later, stdlib only. No new dependency.
- The field-drift guard means each new field is named in `SKILL.md` in the same
  step that adds it to the script.
- Nothing here runs git or writes anywhere git can see.
- `tests/test_version_propagation.py` requires the frontmatter version and the
  ledger's current version to agree.
- Frontier revision `terminal-goal-loop` and digest
  `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` are
  retained byte for byte. Kronos stays mature.

**Non-goals.**

- No change to the four axes, their caps, the tie-break, or the parked lane.
- No rank-only pass over an empty market. With no eligible candidate there is
  nothing to rank and nothing to select, and the answer is the sentence "no
  eligible frontier remains" rather than a record.
- No scheduling, no recurring report, no diff between two rank-only passes
  beyond the drift the scoreboard already computes.
- No second renderer. `show` gains two marks; it does not gain a report format.
- No judgement about whether a maintainer should then run the winner.

## 4. Design options

**A. Prose contract only.** Add the rank-only invocation to `SKILL.md` and stop.
Cheapest. Trades away the record: a rank-only pass would be indistinguishable
from a pass whose run link was never filled in, so the scoreboard could no
longer tell a ranking that stopped from a delivery that lost its link. The
ungoverned report still evaporates with the chat that carried it.

**B. Two fields on the pass, and two marks in `show`.** `rank_only` and
`ungoverned` join the record; `record` refuses a `rank_only` pass carrying a
`run`; `show` marks the pass and prints the list. Trades away record width: a
pass line already carries six fields and this makes eight.

**C. A separate `report` subcommand.** A renderer producing the rank-only table
from a recorded pass. Trades away one renderer for two, both printing the same
candidates, which drift apart the first time one is changed.

**D. A third value of `mode`.** `MODES` becomes `full`, `phase-only`,
`rank-only`. Trades away a distinction the record needs: `mode` says how wide
the scope was, and rank-only says whether the loop continued. A rank-only pass
over the six phase skills is both, and this option makes it impossible to say
so.

**Chosen: B.** D is the option that looks tidiest and quietly loses information,
which is worth writing down because the field name invites it. C builds a second
thing that prints what `show` already prints. A leaves the scoreboard unable to
answer the question the mode creates.

## 5. Risk register seed

Python validating two more fields on a document that arrives on stdin. The
audit loop should look hardest at:

- **The rank_only and run interaction.** These two contradict each other, and a
  caller can send both. The refusal has to fire on the combination rather than
  on either alone, and a pass with neither has to keep working exactly as it
  does today.
- **The ungoverned list.** It is caller-supplied, unbounded, and made of names
  that reach the record and later the terminal. It needs a cap, a type check on
  every element, and no path handling, since an ungoverned skill is named rather
  than opened.
- **Backward compatibility.** Every scoreboard written under `v0.3.0` and
  `v0.4.0` lacks both fields, and `show` reads them. The previous run found this
  class of fault twice; the fields have to be read with a default.
- **The record's meaning.** A rank-only pass sits in the same file as passes
  that launched deliveries. If the mark is lost, the drift check silently
  compares rankings that were never acted on with ones that were.

## 6. Glossary seeds

- **Rank-only pass.** A run of steps 1 to 4 that stops after selection and
  invokes no Fiat.
- **Ungoverned skill.** An in-scope skill with no `EVOLUTION.md`, reported
  rather than scored.
- **The table.** The scored candidate list with per-axis scores, bases, the
  selection, any standing parks, and the ungoverned report.

## 7. Sources

- `plugins/hexaemeron/skills/kronos/SKILL.md`, the description, steps 2, 3, 4
  and 6, the stop text and the parked lane.
- `plugins/hexaemeron/skills/kronos/scripts/kronos.py`, `PASS_FIELDS`, `MODES`,
  `record` and `show`.
- `plugins/hexaemeron/tests/test_kronos_scoreboard.py`, the field-drift guard.
- `plugins/hexaemeron/skills/kronos/EVOLUTION.md`, `kronos-v0.4.0`, `mature`.
- `plugins/hexaemeron/skills/VERSIONING.md`, the generation-axis rule.
- The wishlist entry `kronos-3`, artifact `wishlist-grab-bag.md`.

## 8. Signals, and the questions behind them

The rank-only record is read weeks later by someone deciding what to spend time
on. Two questions:

- *Was this ranking acted on, or just looked at?* Answered by the `rank_only`
  mark on the pass. Emitted whenever a pass is recorded.
- *What was in scope but had no ledger at the time?* Answered by the
  `ungoverned` list on the pass, which is the step 2 report given somewhere to
  live. Emitted with the pass and printed by `show`.

Refusals keep going to stderr with a code, as they do today.
[ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal must
carry.

## 9. Boundaries, per capability

- **The rank_only flag.** Worth taking: a non-boolean, and the contradiction
  with `run`. Control: type-check it, and refuse the pass when it is true beside
  a run rather than silently dropping one of the two.
- **The ungoverned list.** Worth taking: an unbounded list, a non-string
  element, an empty name. Control: cap the length, require every element to be
  a non-empty string, and never treat an element as a path.
- **Reading a pass written before these fields existed.** Worth taking: a
  `KeyError` on every older line. Control: read both with a default, and hold it
  with a case over a `v0.4.0`-shaped line.

[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list
and the controls.

## 10. The budget, or its absence

None. A rank-only pass is one file read per governed ledger, and the whole point
is that it costs a maintainer minutes rather than a week of Fiat. No performance
budget is claimed and nothing is changed for speed, so
[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) has nothing to measure.

## 11. The fail-closed posture

Every refusal exits non-zero and appends nothing. What stops the run: a
non-boolean `rank_only`, a `rank_only` pass carrying a run, an `ungoverned` list
over its cap or holding a non-string, and every refusal `record` already makes.

Guard-test convention: a fix for a failure found here adds a case to
`plugins/hexaemeron/tests/test_kronos_scoreboard.py` that fails on the unfixed
tree, following
[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md).

## 12. Decisions and their homes

Two decisions here are expensive to reverse, and both are decisions about a
governed skill, so both belong in
`plugins/hexaemeron/skills/kronos/EVOLUTION.md` per
[hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md):

- Rank-only is a field beside `mode` rather than a third value of it. Reversing
  it means every recorded pass loses either its scope or its intent.
- A rank-only pass is recorded in the same scoreboard as passes that launched
  deliveries, marked rather than separated. Reversing it splits the drift check
  across two files.

The generation row recording both lands in step 3, with the version bump
`tests/test_version_propagation.py` requires to agree with it.

## Boundaries

**Always.** Both suites before a commit: `python3 -m unittest discover -s tests
-p "test_*.py"` and `python3 plugins/hexaemeron/tests/run_tests.py`. The
imprimatur lint on every shipped document. A new field named in `SKILL.md` in
the same step that adds it to the script. Kronos's frontier revision and digest
retained in any ledger edit.

**Ask first.** Adding a dependency. Changing the four axes, their caps, the
tie-break or the parked lane. Changing what an existing pass field means.
Writing anywhere git can see. Touching CI.

**Never.** Run git from Kronos. Invoke Fiat from a rank-only pass. Record a
rank-only pass carrying a run. Drop the ungoverned report. Change the held
`Next Fiat job` or reopen the mature frontier. Delete a failing test to make a
suite pass. Claim a lint or a suite ran when it did not.
