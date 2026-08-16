---
name: alexandria
description: Route requests to preserve lending-protocol captures by digest and expose a narrow, source-bound credit view to the canonical Alexandria instructions. Use when the user names Alexandria or asks for an address-queryable archive for Tabularium or Probitas. Raw ingest and verification, Goldfinch and Clearpool derivation, disposable indexing, address queries and an offline demonstration are available.
---

# Alexandria portable entrypoint

Read [the Alexandria runtime contract](../../../plugins/alexandria/AGENTS.md).
Use its selection table to choose the skill, then read the canonical
`SKILL.md` in full and follow it.

Invocation prefixes are aliases:

- `/alexandria:alexandria`, `$alexandria`, and a plain request to work with
  the lending-data archive all select `alexandria`.

The current release can ingest and verify raw releases, derive registered
Goldfinch and Clearpool credit views, rebuild a disposable address index and
query it for Probitas. The canonical skill and runtime contract are
authoritative if this entrypoint disagrees with them.
