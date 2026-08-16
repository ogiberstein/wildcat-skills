---
name: lazarus
description: Route historical Ethereum fixture work to the canonical Lazarus instructions. Use when the user names Lazarus or asks to capture, verify or replay the finite state and exact RPC evidence an old application test needs without relying on its original archive endpoint. Never use it to turn ordinary RPC responses into state-proof claims.
---

# Lazarus portable entrypoint

Read [the Lazarus runtime contract](../../../plugins/lazarus/AGENTS.md). Use its
selection table to choose the skill, then read that canonical `SKILL.md` in
full and follow it.

Invocation prefixes are aliases:

- `/lazarus:lazarus`, `$lazarus`, and a plain request for a proof-checked
  historical Ethereum fixture all select `lazarus`.

The canonical skill implements capture, offline verification and exact-request
loopback replay. Keep its evidence classes separate: a recorded RPC response is
not a proof-backed state claim.

The canonical skill and runtime contract are authoritative if this entrypoint
disagrees with them.
