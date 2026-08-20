# Runbook: add a rank-only reporting mode to Kronos

Derived from [study.md](study.md). Three steps, dependency ordered. Step 1
scaffolds and commits the spec, step 2 adds the two record fields, step 3 wires
the invocation into the skill and runs the demo path.

The run branch is `fiat/add-a-rank-only-reporting-mode-to-kronos`, cut from
`main` at `0998786`. Both suites are green at that ref: 34/34 at the root and
437/437 under the plugin.

## Step 1: Commit the spec

**Goal.** Put the study and this runbook in the repository, where the next two
steps and any later reader can reach them.

**Entry.** The run branch at `0998786`, tree clean, both suites green.

**Exit.** `docs/kronos-rank-only/study.md` and `docs/kronos-rank-only/runbook.md`
exist, with every relative link rewritten for their new depth. Proved by
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins`
exiting 0, and by both suites still passing:
`python3 -m unittest discover -s tests -p "test_*.py"` and
`python3 plugins/hexaemeron/tests/run_tests.py`.

**Files.** `docs/kronos-rank-only/study.md`, `docs/kronos-rank-only/runbook.md`.

**Tests.** None added. The two existing suites and the hypomnema link check are
the gate.

**Disciplines.** phylax: none, this step adds no boundary and runs no code.
ephoros: none, documents emit nothing. metron: none, no performance claim.
elenchus: none, no failure in hand. hypomnema: this step is the record, and the
link check is what proves the pointers resolve from the new depth.

## Step 2: Record what a rank-only pass is

**Goal.** Two fields on the pass, `rank_only` and `ungoverned`, validated on the
way in and marked on the way out, with `SKILL.md` naming both.

**Entry.** Step 1's exit state: the spec committed, both suites green.

**Exit.** `record` accepts `rank_only` and `ungoverned`, refuses a `rank_only`
pass carrying a `run`, refuses a non-boolean `rank_only`, refuses an
`ungoverned` list over its cap or holding a non-string, and writes both into the
line; `show` marks a rank-only pass and prints its ungoverned list; a scoreboard
line written before either field existed still reads. `SKILL.md`'s Scoreboard
section names both fields, which the field-drift guard from `kronos-v0.3.0`
requires in this same step. Proved by
`python3 plugins/hexaemeron/tests/run_tests.py` passing with the new cases, and
by `python3 -m unittest discover -s tests -p "test_*.py"`.

**Files.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py`,
`plugins/hexaemeron/tests/test_kronos_scoreboard.py`,
`plugins/hexaemeron/skills/kronos/SKILL.md` for the two field names only.

**Tests.** New cases in `test_kronos_scoreboard.py`: a rank-only pass recorded
with no run; a rank-only pass carrying a run refused; a non-boolean `rank_only`
refused; a pass with neither field recorded exactly as it is today; an
`ungoverned` list stored and rendered; a list over the cap refused; a
non-string element refused; an empty name refused; `show` marking a rank-only
pass; `show` printing the ungoverned list; a `v0.4.0`-shaped line carrying
neither field still reading. Expect the plugin suite above 437 by roughly eleven
cases.

**Disciplines.** phylax: this step takes two more caller-supplied fields on the
stdin document, one of which contradicts an existing field, so both need their
controls. ephoros: the mark and the list are what a later reader consults, so
what `show` prints is part of the step. metron: none, no performance claim.
elenchus: none, no failure in hand; the guard convention applies to any this
step surfaces. hypomnema: the interface documentation sits with the script, and
the two expensive decisions are recorded in step 3.

## Step 3: Wire rank-only into Kronos and demonstrate

**Goal.** Make rank-only a way to invoke Kronos: the loop states where it stops,
the description admits it, the version moves to `0.5.0`, and the ledger carries
one generation row.

**Entry.** Step 2's exit state: the fields shipped and both suites green.

**Exit.** `SKILL.md` states the rank-only invocation and what it hands back, its
description names rank-only as a reason to invoke Kronos, and it carries
`version: "0.5.0"`; `EVOLUTION.md` carries one new generation row retaining
frontier revision `terminal-goal-loop` and digest
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` byte for
byte, with status still `mature` and next job still `None -- mature`. Proved by
`python3 -m unittest discover -s tests -p "test_*.py"` passing, which is where
`test_evolution_contract.py`, `test_version_propagation.py` and
`test_portable_skills.py` live, by `python3 plugins/hexaemeron/tests/run_tests.py`,
and by the demo path: record a rank-only pass over this checkout's real ledgers
naming an ungoverned skill, then `show` marking the pass rank-only and listing
that skill.

**Files.** `plugins/hexaemeron/skills/kronos/SKILL.md`,
`plugins/hexaemeron/skills/kronos/EVOLUTION.md`.

**Tests.** No new test file. The root suite's evolution-contract,
version-propagation and portable-skills cases prove the ledger row, the version
bump and the description agree, and the field-drift guard proves the skill text
still names every field the script accepts.

**Disciplines.** phylax: none, this step adds no boundary; it edits two
documents. ephoros: none beyond what step 2 emits. metron: none, no performance
claim. elenchus: none, no failure in hand. hypomnema: the two decisions the
study named as expensive to reverse are recorded here in the ledger row, which
is where a decision about a governed skill lives.
