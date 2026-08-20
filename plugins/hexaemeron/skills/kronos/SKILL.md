---
name: kronos
description: >-
  Rank the held Next Fiat jobs across explicitly in-scope, non-mature skills,
  select the most worthwhile job out of 100, set one durable goal or loop,
  run that job through Fiat, then repeat until no eligible frontier remains.
  Use only when the user explicitly asks for Kronos or for a repeated ranked
  Fiat frontier loop. Do not use it for one ordinary Fiat delivery.
metadata:
  version: "0.4.0"
---

# Kronos

Read [EVOLUTION.md](EVOLUTION.md). Kronos is terminal by design; that maturity
blocks attempts to improve Kronos itself, not the frontier loop it controls.

Named for the old knot between Kronos and Chronos: a sickle for taking the
ripest frontier first, and a clock that keeps Fiat moving until the field is
bare.

> Highest first, then Fiat runs.
>
> Kronos cuts till work is done.

## Phase-only mode

When the user explicitly asks for phase-only Kronos, run this same Kronos loop
with a fixed candidate universe of exactly six skills:

1. Protasis
2. Phylax
3. Ephoros
4. Metron
5. Elenchus
6. Hypomnema

Resolve those six directories beside this skill in the active Hexaemeron
plugin. Read all six ledgers and fail closed if any ledger is missing,
malformed, carries a status other than `open` or `mature`, or contradicts its
status with its Next Fiat job. Do not discover, report, score, select or start
a frontier from any other skill. Steps 3-7 below are unchanged. In step 8,
rescan all six phase ledgers from disk and no others, rerank from scratch and
repeat. A replacement held job may re-enter the ranking.

Unless the user supplies an iteration cap, stop only when none of the six
phase ledgers remains eligible and no park stands against one of them. If the
user requests a bounded batch, stop after that many completed Fiat iterations or
sooner if the phase market is exhausted, and report any park still standing
rather than letting the cap bury it. The scope limits which skill owns a
selected frontier; Fiat may still change any file genuinely required by that
exact held job.

## Loop

1. Resolve the scope from the user's named directories or repositories. If no
   narrower scope was named, use the current marketplace checkout, rooted at
   the checkout itself rather than at any one plugin. Scope spans every plugin
   in that checkout, not only the plugin Kronos was invoked from.
2. Walk the whole scope and find every `EVOLUTION.md` beneath it, descending
   into each plugin's own skills directory. A governed skill is named by its
   own directory and not by its plugin, so one plugin may hold several and a
   skill may be named differently from the plugin around it. Exclude:
   - Kronos itself;
   - vendored or third-party skills;
   - a ledger whose `Frontier status` is `mature`;
   - a ledger whose `Next Fiat job` is `None -- mature` or absent.
   Report any in-scope skill carrying no ledger as ungoverned instead of
   dropping it silently. An ungoverned skill is never scored, but a skill that
   has quietly lost its ledger must not vanish from the report.
3. Score each remaining held job out of 100:
   - material user or protocol impact: 40;
   - evidenced urgency or defect severity: 25;
   - readiness of inputs and acceptance conditions: 20;
   - work it unblocks or shapes in other in-scope skills: 15.
   Show the score and one-sentence basis for every candidate. Do not invent
   work to fill the list.
4. Select the highest score among candidates with no standing park. Break a tie
   by impact, then readiness, then the order in which the ledgers were found. A
   parked candidate is still scored and still reported; it is only barred from
   selection, because the loop already knows why it stalled.
5. When the runtime provides a durable goal facility, create one goal whose
   objective is to repeat steps 1-8 until no eligible frontier remains. When
   it does not, keep the same loop in the current run. Never create one goal
   per skill.
6. Read the selected skill's canonical instructions, its ledger, and Fiat's
   `SKILL.md`. Invoke Fiat with the held Next Fiat job byte for byte. Once
   Fiat's `init` has named the run, record the pass to the scoreboard below
   with `run` naming it. Record it here rather than at selection, because the
   link to the run this pass launched is half the record and does not exist
   until Fiat is invoked. The cost is that a pass which never reaches `init`
   leaves no line.
7. Let Fiat finish its complete terminal path: implement, validate, stage,
   commit, push each step's stacked pull request, then the integrate phase --
   the stack merged into the run branch in order, the run branch merged into
   the base, branch cleanup where permitted, and issue closure. A stack of
   pull requests merely opened is not a completed iteration; the controller
   reaching `done` is.
8. Require the completed frontier run to update that skill's ledger under
   `VERSIONING.md`: evolution advances once and the held job is replaced, or
   the frontier becomes mature. Require it mechanically rather than by reading:
   start the run with `hexctl init --frontier <that skill's EVOLUTION.md>`, and
   `done integrate` refuses until the ledger carries exactly one new valid row.
   A loop that ranks by held job cannot afford to take an unchanged ledger for
   a closed one, because the next pass would rank the same job again. Then
   rescan the entire scope from disk -- every plugin and every governed skill,
   not only those ranked in the previous pass -- rerank from scratch, and
   repeat. A skill whose frontier was replaced re-enters the ranking carrying
   its new held job, and a skill whose ledger has appeared since the last pass
   enters for the first time. Read the scoreboard back before reranking. Where
   it reports drift, an earlier pass scored the same held job differently, and
   the new score either has a reason or is the one to correct. Run `parked`
   before concluding that no eligible frontier remains: a standing park is a job
   the loop set down rather than finished.

Stop successfully when no eligible ledger remains and no park stands. If Fiat
halts on a genuine external blocker, park the job: record the blocker verbatim
against it, then continue with the next-ranked candidate. Never skip to a
lower-scoring job without parking the one above it. A skip nobody recorded is
how the loop comes to look busy while the thing that mattered goes missing.

A park is a claim the loop records, not one it judges. It never expires, and
nothing releases it but a person. While one stands the loop is not complete,
however empty the rest of the market looks.

## Scoreboard

Step 8 reranks from scratch. Without a record, the same held job can score 62 in
one pass and 78 three passes later with nothing about it changed, and nobody can
see that happen. Each pass goes to `.kronos/scoreboard.jsonl` at the scope
root, one JSON line, beside a `.gitignore` the writer creates. The file stays
out of git deliberately: Fiat refuses to start against a dirty tree, so a
scoreboard git can see would stop the loop's next iteration before it began.

The writer is `scripts/kronos.py` beside this skill:

```text
python3 "<this skill dir>/scripts/kronos.py" record \
  --scoreboard <scope root>/.kronos/scoreboard.jsonl --root <scope root>
python3 "<this skill dir>/scripts/kronos.py" show \
  --scoreboard <scope root>/.kronos/scoreboard.jsonl
```

`record` reads the pass on stdin as one JSON object: `scope`, `mode` of `full`
or `phase-only`, `selected`, an optional `run` naming the Fiat run this pass
launched, an optional `rank_only` saying the pass stopped after selection, an
optional `ungoverned` listing the in-scope skills found carrying no ledger, and
`candidates`. A `rank_only` pass naming a `run` is refused: it launched none.
Each candidate carries `skill`, `ledger`, the four
axis scores under the names `impact`, `urgency`, `readiness` and `unblocks`, a
one-sentence `basis`, an optional `total` for the arithmetic the ranking did in
chat, which is refused when it disagrees with the axes, and an optional `parked`
naming whether that candidate has a standing park.

It computes each candidate's held-job hash from that ledger on disk rather than
taking one from the caller, so a recorded line can be checked against the digest
the ledger already stores. It refuses an axis outside its cap, a stated total
that disagrees with its axes, a selection the tie-break does not pick, a ledger
it cannot use, and a scoreboard file it cannot parse. A refusal appends nothing
and exits non-zero. `show` prints the passes and marks every axis score that
moved for a candidate whose held job did not.

The scoreboard records a judgement; it does not make one. Every score and basis
is still the ranking's own work, and a loop that skips the writer leaves a
shorter file and no other trace.

## Parked lane

A blocked job goes in `.kronos/parked.jsonl` beside the scoreboard, through the
same script:

```text
python3 "<this skill dir>/scripts/kronos.py" park \
  --scoreboard-dir <scope root>/.kronos --skill <name> \
  --ledger <that skill's EVOLUTION.md> --reason "<the halt, as Fiat gave it>"
python3 "<this skill dir>/scripts/kronos.py" unpark \
  --scoreboard-dir <scope root>/.kronos --skill <name> --reason "<why>"
python3 "<this skill dir>/scripts/kronos.py" parked \
  --scoreboard-dir <scope root>/.kronos
```

`park` stores the reason byte for byte beside the skill's held-job hash at that
moment. Pass Fiat's halt reason through unaltered; a summary of it is not the
thing a maintainer needs later to judge whether the blocker still stands.
`unpark` releases a park and carries its own reason. Neither rewrites a record;
both append, so the history of what was blocked and why survives the release.

`parked` prints what stands and exits 3 while any does, 0 when none does, and 1
on a refusal. The 3 is not an error. It is what stops step 8 declaring the loop
complete, so run it before saying no eligible frontier remains.

A park whose skill now shows a different held job is reported as stale: the job
it named has moved on, and whether the park still applies is a person's call. A
ledger that cannot be read is reported as unknown and the park stands, because
an unreadable file is not evidence a blocker cleared.

Parks and the scoreboard stay separate files on purpose. The scoreboard is
history, where each line is what was true at that pass; the parked lane is
current state that changes. Reading one as the other is how a line stops meaning
what it says.

## Hard rules

- Never edit, implement, audit, or rewrite a target itself. Fiat owns the work.
- Never score a mature, terminal, vendored, or out-of-scope skill.
- In phase-only mode, never discover or score a ledger outside the fixed
  six-skill phase allowlist.
- Never alter a held Next Fiat job before its exact frontier job completes.
- Never continue merely because the loop can continue. No eligible frontier
  means the goal is complete.
- Never select a parked candidate, and never drop one from the ranking.
- Never summarise, shorten or reword a halt reason on the way into a park.
- Never release a park on the loop's own judgement, and never call the loop
  complete while one stands.
