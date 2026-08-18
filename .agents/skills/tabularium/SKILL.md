---
name: tabularium
description: Route reproducible, venue-qualified credit-event releases to Tabularium. Use preserved source records and explicit mapping provenance; use Alexandria for raw harvesting or Probitas for a dossier.
---

- `/tabularium:tabularium`, `$tabularium`, and a plain request to build or
  verify a preserved credit-event release all select `tabularium`.

Tabularium portable entrypoint

Read [the runtime contract](../../../plugins/tabularium/AGENTS.md), select its
sole skill, and follow that canonical `SKILL.md` in full.

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

This release builds deterministic canonical JSONL and a coverage manifest from
preserved Goldfinch, Euler v1 and Euler V2 source records. `verify` checks the
release fully offline and rebuilds the expected event bytes from the preserved
source. Euler V2 protocol generation and Euler V3 source API are recorded as
separate fields.

It also rebuilds a non-canonical Compound v3 Phase 0 witness from a verified
Alexandria release. Those ordered calls, storage writes and signed-principal
transition prove one recorded method, not a canonical event release or market
history.

The canonical skill and runtime contract are authoritative if this entrypoint
disagrees with them.
