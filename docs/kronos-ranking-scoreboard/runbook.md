# Runbook: record each Kronos ranking pass in a durable scoreboard

Derived from [study.md](study.md). Three steps, dependency ordered. Step 1
scaffolds and commits the spec, step 2 builds the writer, step 3 wires it into
the skill and runs the demo path.

The run branch is `fiat/record-each-kronos-ranking-pass-in-a-durable-sco`, cut
from `main` at `fec7ee5`. Both suites are green at that ref: 34/34 at the root
and 381/381 under the plugin.

## Step 1: Commit the spec

**Goal.** Put the study and this runbook in the repository, where the next two
steps and any later reader can reach them.

**Entry.** The run branch at `fec7ee5`, tree clean, both suites green.

**Exit.** `docs/kronos-ranking-scoreboard/study.md` and
`docs/kronos-ranking-scoreboard/runbook.md` exist, with every relative link
rewritten for their new depth. Proved by
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins`
exiting 0, and by both suites still passing:
`python3 -m unittest discover -s tests -p "test_*.py"` and
`python3 plugins/hexaemeron/tests/run_tests.py`.

**Files.** `docs/kronos-ranking-scoreboard/study.md`,
`docs/kronos-ranking-scoreboard/runbook.md`.

**Tests.** None added. The two existing suites and the hypomnema link check are
the gate; the root suite already lints every shipped document through
`tests/test_shipped_prose_lints.py`.

**Disciplines.** phylax: none, this step adds no boundary and runs no code.
ephoros: none, documents emit nothing. metron: none, no performance claim.
elenchus: none, no failure in hand. hypomnema: this step is the record, and the
link check is what proves the pointers resolve from the new depth.

## Step 2: Build the scoreboard writer

**Goal.** A stdlib script that appends one validated pass to a JSON Lines
scoreboard and renders the file, with the held-job identity hash computed from
each candidate's ledger rather than taken from the caller.

**Entry.** Step 1's exit state: the spec committed, both suites green.

**Exit.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py` supports
`record --scoreboard <path>` reading a pass on stdin and `show --scoreboard
<path>`, exits 0 clean, 1 on a refusal, 2 on bad invocation, and appends
nothing on any refusal. Proved by
`python3 plugins/hexaemeron/tests/run_tests.py` passing with the new cases
included, and by `python3 -m unittest discover -s tests -p "test_*.py"`.

**Files.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py`,
`plugins/hexaemeron/tests/test_kronos_scoreboard.py`,
`plugins/hexaemeron/tests/fixtures/kronos/` for ledger fixtures.

**Tests.** New cases in `test_kronos_scoreboard.py`: a clean append; an axis
over its cap; a total over 100; a selection that is not the highest score and
states no tie-break; a candidate whose ledger path resolves outside the
checkout root; a ledger that is a directory; a truncated final line in an
existing scoreboard; a candidate count over the cap; stdin that is not JSON;
an unknown field; the identity hash matching the ledger's own recorded digest;
`show` marking a moved axis under an unchanged identity hash; `show` on an
absent file. Expect the plugin suite above 381 by roughly fifteen cases.

**Disciplines.** phylax: this step opens three boundaries the study names,
stdin, a caller-supplied ledger path, and an append to an existing file, and
each needs its control. ephoros: the scoreboard is the loop's own telemetry, so
what a refusal prints and where it prints it is part of the step. metron: none,
no performance claim and no speed-motivated change. elenchus: none, no failure
in hand; the guard convention applies to failures this step surfaces.
hypomnema: the interface documentation sits with the script, and the two
expensive decisions are recorded in step 3.

## Step 3: Wire the scoreboard into Kronos and demonstrate

**Goal.** Make the writer part of the loop: `SKILL.md` step 3 records the pass
and step 8 reads it back, the version moves to `0.3.0`, the ledger carries one
generation row, and the demo path runs.

**Entry.** Step 2's exit state: the writer shipped and both suites green.

**Exit.** `SKILL.md` names the scoreboard in steps 3 and 8 and carries
`version: "0.3.0"`; `EVOLUTION.md` carries one new generation row retaining
frontier revision `terminal-goal-loop` and digest
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` byte for
byte, with status still `mature` and next job still `None -- mature`. Proved by
`python3 -m unittest discover -s tests -p "test_*.py"` passing, which is where
`test_evolution_contract.py` and `test_version_propagation.py` live, by
`python3 plugins/hexaemeron/tests/run_tests.py`, and by the demo path: record
two passes over this checkout's real ledgers into a scratch scoreboard, the
second moving one axis score for a candidate whose held-job identity hash is
unchanged, then `show` marking that axis as drifted.

**Files.** `plugins/hexaemeron/skills/kronos/SKILL.md`,
`plugins/hexaemeron/skills/kronos/EVOLUTION.md`.

**Tests.** No new test file. The root suite's evolution-contract and
version-propagation cases are what prove the ledger row and the version bump
agree; both already exist and both must pass over the edited ledger.

**Disciplines.** phylax: none, this step adds no boundary; it edits two
documents. ephoros: none beyond what step 2 emits. metron: none, no performance
claim. elenchus: none, no failure in hand. hypomnema: the two decisions the
study named as expensive to reverse, the gitignored scoreboard and the reused
canonical hash, are recorded here in the ledger row, which is where a decision
about a governed skill lives.
