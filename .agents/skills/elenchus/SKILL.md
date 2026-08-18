---
name: elenchus
description: Route root-cause work on a failure that already happened to Elenchus: reproduce, localise, reduce, fix the mechanism, guard it with a test that fails without the fix.
---

# Elenchus portable entrypoint

Elenchus works a failure you already have down to its cause and leaves a guard behind: a red test, a broken build, a returned counterexample.

## Alone, or as part of the suite

On its own it is a triage order and a check. The check applies a commit's own test files to its parent and reports whether the guard is real, which needs nothing but git and your test command.

Inside Hexaemeron it works whatever an audit round surfaces, and its guard check is what stops a fix landing on the promise of a test rather than the fact of one. It is one of six practice skills that share a shape and hand work
to each other, so reaching for the neighbour a rule names usually beats
stretching this one.

Read [the canonical Elenchus skill](../../../plugins/hexaemeron/skills/elenchus/SKILL.md)
in full and follow it. [The Hexaemeron runtime contract](../../../plugins/hexaemeron/AGENTS.md)
carries the selection table naming its siblings, and both are authoritative if
this entrypoint disagrees with them.
