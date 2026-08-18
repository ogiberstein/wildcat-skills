---
name: metron
description: Route performance work to Metron: baseline first, change one thing, re-measure the same way, then keep it or revert it. Everything except Solidity gas, which is Hermes.
---

# Metron portable entrypoint

Metron holds every measurement except gas: the page, the route, the query, the harvest and the release build.

## Alone, or as part of the suite

On its own it is four refusals and a decision table. No baseline means no change, no re-measurement means no keep, neutral is a revert, and a red suite means no win however good the number looks.

Inside Hexaemeron it applies to any change made in the name of speed, and it is the discipline Hermes already imposes on gas, extended to everything gas is not. It is one of six skills bundled with Hexaemeron that share a shape
and hand work to each other, so reaching for the neighbour a rule names usually beats
stretching this one.

Read [the canonical Metron skill](../../../plugins/hexaemeron/skills/metron/SKILL.md)
in full and follow it. [The Hexaemeron runtime contract](../../../plugins/hexaemeron/AGENTS.md)
carries the selection table naming its siblings, and both are authoritative if
this entrypoint disagrees with them.
