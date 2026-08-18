---
name: ephoros
description: Route decisions about telemetry to Ephoros: which events, metrics, traces and alerts a step must emit to stay diagnosable once it runs unattended.
---

# Ephoros portable entrypoint

Ephoros decides what a step emits once nobody is watching it: events with stable names, metrics with bounded labels, one correlation identifier, and alerts on what somebody feels.

## Alone, or as part of the suite

On its own it is a set of on-call questions and a lint over three rules. Use it when shipping anything unattended, or when an incident could not be explained from what was recorded.

Inside Hexaemeron it sits in the implement phase, and it inherits Phylax's rule about what must never appear in output rather than restating it. It is one of six skills bundled with Hexaemeron that share a shape
and hand work to each other, so reaching for the neighbour a rule names usually beats
stretching this one.

Read [the canonical Ephoros skill](../../../plugins/hexaemeron/skills/ephoros/SKILL.md)
in full and follow it. [The Hexaemeron runtime contract](../../../plugins/hexaemeron/AGENTS.md)
carries the selection table naming its siblings, and both are authoritative if
this entrypoint disagrees with them.
