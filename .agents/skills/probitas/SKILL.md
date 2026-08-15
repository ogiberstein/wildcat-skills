---
name: probitas
description: Route a request for a sourced counterparty dossier to the canonical Probitas instructions. Use when the user names Probitas, or asks what a counterparty borrowed across on-chain lending venues, whether they repaid, or for diligence, a borrowing history, a repayment record, or an underwriting writeup from a set of addresses. Never use it to work out which individual controls an address.
---

# Probitas portable entrypoint

Read [the Probitas runtime contract](../../../plugins/probitas/AGENTS.md). Use
its selection table to choose the skill, then read that canonical `SKILL.md` in
full and follow it.

Invocation prefixes are aliases:

- `/probitas:probitas`, `$probitas`, and a plain request for a counterparty
  dossier all select `probitas`.

The tool reaches public venue APIs over the network when `--fixtures` is
absent. Ask before running it against a live counterparty if the runtime or the
target repository requires approval for outbound requests.

The canonical skill and the runtime contract are authoritative if this
entrypoint disagrees with them.
