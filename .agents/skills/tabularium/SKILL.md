---
name: tabularium
description: Route reproducible, venue-qualified credit-event releases to Tabularium. Use preserved source records and explicit mapping provenance; use Alexandria for raw harvesting or Probitas for a dossier.
---

# Tabularium portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning.

**Use another tool when.** Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay.

**Current frontier.** Euler v1/v2 preservation now ships; Compound v3 remains specification-only, with no verified Alexandria raw witness from the Phase 0 trace and ordered-storage method proof.
<!-- marketplace-context:end -->

Read [the Tabularium runtime contract](../../../plugins/tabularium/AGENTS.md).
Use its selection table to choose the skill, then read that canonical
`SKILL.md` in full and follow it.

Invocation prefixes are aliases:

- `/tabularium:tabularium`, `$tabularium`, and a plain request to build or
  verify a preserved credit-event release all select `tabularium`.

This release builds deterministic canonical JSONL and a coverage manifest from
preserved Goldfinch, Euler v1 and Euler V2 source records. `verify` checks the
release fully offline and rebuilds the expected event bytes from the preserved
source. Euler V2 protocol generation and Euler V3 source API are recorded as
separate fields.

The canonical skill and runtime contract are authoritative if this entrypoint
disagrees with them.
