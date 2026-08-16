---
name: tabularium
description: Route requests for a reproducible ledger of sourced on-chain credit events to the canonical Tabularium instructions. Use when the user names Tabularium, asks to preserve a credit-event record, or wants to build or verify a source-bound Goldfinch borrow and repayment release offline. Never use it to claim publisher authenticity or an independently proved chain boundary.
---

# Tabularium portable entrypoint

Read [the Tabularium runtime contract](../../../plugins/tabularium/AGENTS.md).
Use its selection table to choose the skill, then read that canonical
`SKILL.md` in full and follow it.

Invocation prefixes are aliases:

- `/tabularium:tabularium`, `$tabularium`, and a plain request to build or
  verify a preserved credit-event release all select `tabularium`.

This release builds deterministic canonical JSONL and a coverage manifest from
preserved Goldfinch borrow and repay entities. `verify` checks the release
fully offline and rebuilds the expected event bytes from the preserved source.

The canonical skill and runtime contract are authoritative if this entrypoint
disagrees with them.
