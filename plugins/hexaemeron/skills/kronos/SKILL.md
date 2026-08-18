---
name: kronos
description: >-
  Rank the held Next Fiat jobs across explicitly in-scope, non-mature skills,
  select the most worthwhile job out of 100, set one durable goal or loop,
  run that job through Fiat, then repeat until no eligible frontier remains.
  Use only when the user explicitly asks for Kronos or for a repeated ranked
  Fiat frontier loop. Do not use it for one ordinary Fiat delivery.
metadata:
  version: "0.1.0"
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
   - leverage for other in-scope skills: 15.
   Show the score and one-sentence basis for every candidate. Do not invent
   work to fill the list.
4. Select the highest score. Break a tie by impact, then readiness, then the
   order in which the ledgers were found.
5. When the runtime provides a durable goal facility, create one goal whose
   objective is to repeat steps 1-8 until no eligible frontier remains. When
   it does not, keep the same loop in the current run. Never create one goal
   per skill.
6. Read the selected skill's canonical instructions, its ledger, and Fiat's
   `SKILL.md`. Invoke Fiat with the held Next Fiat job byte for byte.
7. Let Fiat finish its complete terminal path: implement, validate, stage,
   commit, push each step's stacked pull request, then the integrate phase --
   the stack merged into the run branch in order, the run branch merged into
   the base, branch cleanup where permitted, and issue closure. A stack of
   pull requests merely opened is not a completed iteration; the controller
   reaching `done` is.
8. Require the completed frontier run to update that skill's ledger under
   `VERSIONING.md`: evolution advances once and the held job is replaced, or
   the frontier becomes mature. Then rescan the entire scope from disk --
   every plugin and every governed skill, not only those ranked in the
   previous pass -- rerank from scratch, and repeat. A skill whose frontier
   was replaced re-enters the ranking carrying its new held job, and a skill
   whose ledger has appeared since the last pass enters for the first time.

Stop successfully when no eligible ledger remains. If Fiat halts on a genuine
external blocker, preserve the durable goal and report that blocker; do not
skip to a lower-scoring job to make the loop look busy.

## Hard rules

- Never edit, implement, audit, or rewrite a target itself. Fiat owns the work.
- Never score a mature, terminal, vendored, or out-of-scope skill.
- Never alter a held Next Fiat job before its exact frontier job completes.
- Never continue merely because the loop can continue. No eligible frontier
  means the goal is complete.
