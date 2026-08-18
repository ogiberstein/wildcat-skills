---
name: alexandria
description: Route lending-data preservation, reviewed credit-view and verified address-query work to Alexandria. Use it for digest-bound releases with explicit coverage; use Tabularium for semantic event releases or Probitas for a dossier.
---

- `/alexandria:alexandria`, `$alexandria`, and a plain request to work with
  the lending-data archive all select `alexandria`.

Alexandria portable entrypoint

Read [the runtime contract](../../../plugins/alexandria/AGENTS.md), select its
sole skill, and follow the canonical `SKILL.md` in full.

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.
<!-- marketplace-context:end -->

The release ingests and verifies raw releases, derives registered Goldfinch
and Clearpool credit views, rebuilds a disposable address index, queries it for
Probitas, and builds and checks the bounded Compound v3 Phase 0 method release.
The canonical skill and runtime contract prevail over this entrypoint.
