Euler preservation delivery runbook

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

Step 1 shipped source-bound Euler v1 and Euler V2 releases as one Fiat review
boundary:

- Goal: add deterministic Euler releases without changing any earlier
  Goldfinch byte; keep Euler V2 protocol generation separate from the Euler V3
  source API.
- Entry: clean `main` at `27e930f`, issue #57, 92 passing Tabularium tests and
  four test-fixed Goldfinch digests.
- Exit: `euler-v1-v0` and `euler-v2-v0` build twice in fresh directories to
  committed bytes, verify without network access or writes, and reject source
  and derived-artifact tampering. The Goldfinch digest gate and full repository
  matrix stay green; marketplace prose rotates the next job to Compound III
  Phase 0.

Files. Add Euler adapters, versioned release validation, schema v2,
self-contained examples, dictionaries, rebuild scripts and focused tests under
`plugins/tabularium/`. Update the canonical skill, portable entry, agent
contract, host manifests, root catalogue, guides and landing page. Preserve
vendored prose, historical audit findings outside their current-context line,
legal attribution and the digest-bound Lazarus fixture README.

Tests. Cover exact v1 Borrow, Repay and Liquidation mappings; every V2
credit-event family; source/native retention; owner/sub-account checks;
selector uniqueness; deterministic order; unknown-event refusal; fixed release
digests; two fresh rebuilds; no-network verification; and source, capture,
canonical, coverage, version and count tampering. Run the complete repository
Python matrix, Pandects Foundry checks and `git diff --check`.
