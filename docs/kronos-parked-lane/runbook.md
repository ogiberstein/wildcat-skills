# Runbook: park a blocked Kronos job instead of stalling the loop

Derived from [study.md](study.md). Three steps, dependency ordered. Step 1
scaffolds and commits the spec, step 2 builds the lane, step 3 wires it into the
skill and runs the demo path.

The run branch is `fiat/park-a-blocked-kronos-job-instead-of-stalling-th`, cut
from `main` at `36f1e2e`. Both suites are green at that ref: 34/34 at the root
and 414/414 under the plugin.

## Step 1: Commit the spec

**Goal.** Put the study and this runbook in the repository, where the next two
steps and any later reader can reach them.

**Entry.** The run branch at `36f1e2e`, tree clean, both suites green.

**Exit.** `docs/kronos-parked-lane/study.md` and
`docs/kronos-parked-lane/runbook.md` exist, with every relative link rewritten
for their new depth. Proved by
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins`
exiting 0, and by both suites still passing:
`python3 -m unittest discover -s tests -p "test_*.py"` and
`python3 plugins/hexaemeron/tests/run_tests.py`.

**Files.** `docs/kronos-parked-lane/study.md`,
`docs/kronos-parked-lane/runbook.md`.

**Tests.** None added. The two existing suites and the hypomnema link check are
the gate.

**Disciplines.** phylax: none, this step adds no boundary and runs no code.
ephoros: none, documents emit nothing. metron: none, no performance claim.
elenchus: none, no failure in hand. hypomnema: this step is the record, and the
link check is what proves the pointers resolve from the new depth.

## Step 2: Build the parked lane

**Goal.** Three subcommands that record a park, release it, and report the
standing set, plus the change to `record` that lets a pass skip a parked
candidate without dropping it from the ranking.

**Entry.** Step 1's exit state: the spec committed, both suites green.

**Exit.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py` supports
`park --scoreboard-dir <dir> --skill <name> --ledger <path> --reason <text>`,
`unpark --scoreboard-dir <dir> --skill <name> --reason <text>` and
`parked --scoreboard-dir <dir>`; `parked` exits 2 while any park stands and 0
when none does, keeping 1 for a refusal; and `record` accepts `parked` on a
candidate, applies the tie-break to unparked candidates only, and refuses a pass
whose flags disagree with the standing parks. Proved by
`python3 plugins/hexaemeron/tests/run_tests.py` passing with the new cases
included, and by `python3 -m unittest discover -s tests -p "test_*.py"`.

**Files.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py`,
`plugins/hexaemeron/tests/test_kronos_scoreboard.py`.

**Tests.** New cases in `test_kronos_scoreboard.py`: a park appended with the
reason byte for byte; a reason carrying a newline that leaves the file one line
per record; an empty reason refused; an oversized reason refused; a park whose
ledger cannot be read refused; an unpark with no standing park refused; a second
park for an already parked skill refused; park, unpark, park again replaying to
one standing park; `parked` exiting 2 with a park standing and 0 without; a
stale park reported as stale when the ledger's identity hash has moved; a
deleted ledger reported as unknown rather than resolved; a pass selecting the
highest unparked candidate accepted; a pass selecting a parked candidate
refused; a pass whose candidates are all parked refused; a pass claiming a park
that was never recorded refused; a truncated tail in the parked file refused.
Expect the plugin suite above 414 by roughly sixteen cases.

**Disciplines.** phylax: this step takes a caller-supplied reason string stored
verbatim and opens a second append target in the same directory, so both need
their controls. ephoros: `parked` is what a loop and a later reader consult, so
its exit codes and output are part of the step. metron: none, no performance
claim. elenchus: none, no failure in hand; the guard convention applies to any
this step surfaces. hypomnema: the interface documentation sits with the script,
and the three expensive decisions are recorded in step 3.

## Step 3: Wire the parked lane into Kronos and demonstrate

**Goal.** Make the lane part of the loop: the stop text gains the third option
it lacked, selection skips parked candidates, completion is blocked while a park
stands, the version moves to `0.4.0`, and the ledger carries one generation row.

**Entry.** Step 2's exit state: the lane shipped and both suites green.

**Exit.** `SKILL.md` states the parked lane in the loop and the stop text and
carries `version: "0.4.0"`; `EVOLUTION.md` carries one new generation row
retaining frontier revision `terminal-goal-loop` and digest
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` byte for
byte, with status still `mature` and next job still `None -- mature`. Proved by
`python3 -m unittest discover -s tests -p "test_*.py"` passing, which is where
`test_evolution_contract.py` and `test_version_propagation.py` live, by
`python3 plugins/hexaemeron/tests/run_tests.py`, and by the demo path: park a
skill against this checkout's real ledger, record a pass that selects the
next-ranked candidate, see `parked` exit 2, unpark, and see it exit 0.

**Files.** `plugins/hexaemeron/skills/kronos/SKILL.md`,
`plugins/hexaemeron/skills/kronos/EVOLUTION.md`.

**Tests.** No new test file. The root suite's evolution-contract and
version-propagation cases prove the ledger row and the version bump agree, and
the field-drift guard added in `kronos-v0.3.0` proves the skill text names every
field the script accepts.

**Disciplines.** phylax: none, this step adds no boundary; it edits two
documents. ephoros: none beyond what step 2 emits. metron: none, no performance
claim. elenchus: none, no failure in hand. hypomnema: the three decisions the
study named as expensive to reverse are recorded here in the ledger row, which
is where a decision about a governed skill lives.
