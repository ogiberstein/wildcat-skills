---
name: lazarus
description: Route finite historical Ethereum fixture work to Lazarus. Use it for proof-checked fixed-block state and exact-request replay without fallback; use Alexandria for lending archives.
---

# Lazarus portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests.

**Use another tool when.** Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence.

**Current frontier.** Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented.
<!-- marketplace-context:end -->

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
