Goldfinch v0 data dictionary

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

`events.jsonl` contains one canonical event v1 JSON object per line. All
amounts use decimal strings in the asset's base units, so reading the file does
not require binary floating-point arithmetic.

Canonical fields

- `schema_version`: canonical event schema revision; this release uses `1`.
- `id`: deterministic Tabularium row identifier from its source selector.
- `event_family`: broad family, `borrowing` or `repayment`.
- `action`: `goldfinch.borrow` or `goldfinch.repay`.
- `venue`: `goldfinch`.
- `chain`: `ethereum-mainnet`.
- `transaction`: source transaction hash, log index and decimal-string timestamp.
- `parties`: addresses and their venue-specific roles.
- `instrument`: credit instrument type and source identifier.
- `asset`: symbol and decimal precision used for `amount`.
- `amount`: non-negative `base_units` decimal string reported by the source.
- `provenance`: source kind, contract, entity, identifier, selector, adapter and
  mapping-rule versions.
- `native_record`: complete source entity retained beside its interpretation.

The `source_selector` points to exactly one `borrows` or `repays` entity in
`source.json`. `source_contract` names the validated Goldfinch market address.
The mapping rules are `goldfinch.borrow.v1` and `goldfinch.repay.v1`, produced
by Goldfinch adapter `1.0.0`.

Coverage and meaning

The release includes all 34 `borrows` and 477 `repays` in the preserved
snapshot. It does not map `_meta`, `callableLoans`, `creditLines` or
`tranchedPools` as canonical events. Their counts remain in `coverage.json`.

`borrowing` and `repayment` are common event families, but their actions retain
Goldfinch's meaning. In particular, `goldfinch.repay` means the source recorded
a repayment amount. It is not a general statement that every obligation was
paid, the facility closed, or the debt fully settled.

The hosted indexer's reported block is the capture boundary. Neither that
boundary nor a per-event block number and hash is independently proved against
Ethereum. The release is unsigned, so a successful offline verification checks
the four files for internal consistency; it does not establish publisher
identity or authenticity.
