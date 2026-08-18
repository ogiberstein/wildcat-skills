---
name: hypomnema
description: Route decisions about what to record to Hypomnema: which choices earn a written reason, where each kind of record lives, and whether the pointers in them resolve.
---

# Hypomnema portable entrypoint

Hypomnema decides which decisions earn a written reason and which file holds it, matching whatever convention a repository already runs rather than adding a second one.

## Alone, or as part of the suite

On its own it answers where a decision, a runbook or a gotcha belongs, and its lint reports records pointing at things that do not exist, which reads as though a reason was checked when it was not.

Inside Hexaemeron it runs before the prose phase and decides whether there is anything to write, leaving the mask order and the receipt to Fiat. It is one of six practice skills that share a shape and hand work
to each other, so reaching for the neighbour a rule names usually beats
stretching this one.

Read [the canonical Hypomnema skill](../../../plugins/hexaemeron/skills/hypomnema/SKILL.md)
in full and follow it. [The Hexaemeron runtime contract](../../../plugins/hexaemeron/AGENTS.md)
carries the selection table naming its siblings, and both are authoritative if
this entrypoint disagrees with them.
