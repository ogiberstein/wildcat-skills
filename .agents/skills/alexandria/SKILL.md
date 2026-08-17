---
name: alexandria
description: Route lending-data preservation, reviewed credit-view and verified address-query work to Alexandria. Use it for digest-bound releases with explicit coverage; use Tabularium for semantic event releases or Probitas for a dossier.
---

# Alexandria portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend.

**Use another tool when.** Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay.

**Current frontier.** Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.
<!-- marketplace-context:end -->

Read [the Alexandria runtime contract](../../../plugins/alexandria/AGENTS.md).
Use its selection table to choose the skill, then read the canonical
`SKILL.md` in full and follow it.

Invocation prefixes are aliases:

- `/alexandria:alexandria`, `$alexandria`, and a plain request to work with
  the lending-data archive all select `alexandria`.

The current release can ingest and verify raw releases, derive registered
Goldfinch and Clearpool credit views, rebuild a disposable address index and
query it for Probitas. It also builds and checks the bounded Compound v3 Phase
0 method release. The canonical skill and runtime contract are authoritative
if this entrypoint disagrees with them.
