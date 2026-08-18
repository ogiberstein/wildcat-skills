---
name: lazarus
description: Route finite historical Ethereum fixture work to Lazarus. Use it for proof-checked fixed-block state and exact-request replay without fallback; use Alexandria for lending archives.
---
- `/lazarus:lazarus`, `$lazarus`, and a plain request for a proof-checked
  historical Ethereum fixture all select `lazarus`.

Lazarus portable entrypoint

Read [the runtime contract](../../../plugins/lazarus/AGENTS.md), select its sole
skill, and follow that canonical `SKILL.md` in full.

<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures finite fixed-block Ethereum state and RPC evidence, verifies the proof-backed part, and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation, and Ariadne to bind a released fixture to its evidence. **Current frontier:** Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented.
<!-- marketplace-context:end -->

The canonical skill covers capture, offline verification, and exact-request
loopback replay. A recorded RPC response is not proof-backed state. The
canonical skill and runtime contract prevail over this entrypoint.
