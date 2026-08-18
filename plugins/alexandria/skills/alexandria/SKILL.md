---
name: alexandria
description: >
  Preserve heterogeneous lending-protocol captures by digest and expose a
  narrow, source-bound credit view for Tabularium and Probitas. Use when the
  user names Alexandria or asks to archive lending data for reproducible,
  address-scoped credit research. Raw release and registered Goldfinch and
  Clearpool derivation, disposable indexing, address queries and a checked-in
  offline demonstration and bounded Compound v3 Phase 0 method proof are
  available.
metadata:
  version: "0.2.0"
---

# Alexandria

## Frontier

Alexandria owns its own preservation and credit-view frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend.

**Use another tool when.** Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay.

**Current frontier.** Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.
<!-- marketplace-context:end -->

Alexandria is the archive and catalogue behind durable lending-protocol
research. Raw captures remain unchanged. Small manifests describe what was
captured, what was missed and which digest names each object. Tabularium owns
the interpretation of the narrow credit view, and Probitas consumes that view
without treating Alexandria as a lending venue.

`$SKILL_DIR` is the directory holding this file. The command lives at
`$SKILL_DIR/../../scripts/alexandria.py`; resolve it from where you loaded this
skill.

## Day to day

**Research.** A protocol endpoint or hosted indexer may disappear. Preserve
the exact response, its capture scope and its gaps before the only cheap copy
is gone.

**Credit.** A counterparty record needs events, position observations and an
account of the venues and intervals checked. An empty result without coverage
is not a clean history.

**Data engineering.** Raw GraphQL responses, chain logs and replay fixtures
do not need one payload schema. Bind their bytes in one manifest, then build a
small, versioned credit view that points back to them.

## Raw releases

Prepare a capture plan using the contracts under
`$SKILL_DIR/../../schemas/`. Every component path is relative to the plan's
directory. Every component has a `public`, `restricted` or `private` access
class and a `permitted`, `restricted`, `prohibited` or `unknown` redistribution
class. Give every capture a venue, an `eip155` chain, a non-secret source
reference, an evidence and finality class, a full-dataset or subject-scoped
boundary and counted coverage or a stated gap. Then ingest it:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" ingest \
  --plan capture-plan.json --output release
```

Ingest reads only the plan and its confined local source files. It copies raw
bytes unchanged into digest-derived paths, writes through a temporary sibling
directory and installs the release atomically. It refuses absolute paths,
traversal, symlinks and replacement of a different release. Record the
`sha256:...` release ID printed on success.

Verify before using or moving a release:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" verify release
```

Verification is offline and read-only. It checks canonical manifest bytes,
release identity, object paths, byte counts, digests, component access and
redistribution classes, capture source, scope, evidence and finality classes,
collection counts, declared gaps, correction links and exact release-tree
membership. It does not establish publisher identity, source completeness or
chain finality.

Derive the narrow Tabularium view into a new release:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" derive raw-release \
  --output derived-release
python3 "$SKILL_DIR/../../scripts/alexandria.py" verify derived-release
```

Derivation first verifies the input and never changes it. Registered
Goldfinch and Clearpool mappings emit deterministic credit events and, where
the source supplies position state, observations. Every row names the raw
release, component digest, source and context selectors, mapping rule, adapter
version and evidence class. Verification resolves those selectors, reruns the
mappings and reconciles row, family, subject and coverage counts. Capture
renames do not change row IDs, and repayment legs remain neutral source
amounts unless the native record supplies a principal and interest split.
Derivation stops above 100,000 rows or 64 MiB for either JSONL file.

Rebuild the disposable address index and query it:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" index derived-release \
  --output alexandria.sqlite
python3 "$SKILL_DIR/../../scripts/alexandria.py" query \
  --index alexandria.sqlite --address 0x...
```

Indexing verifies every derived release, refuses to write inside one and
retains the derived release, raw release, component, capture and row
identities. Querying opens SQLite read-only, checks its exact schema and
logical digest, then matches every indexed partition to its release. Equivalent
rows shared by cumulative releases appear once. Conflicting content under one
row ID is refused.

A zero-row result is empty only when complete capture scope covers every
requested address, venue, chain and time boundary and the mapping has no
unsupported source records.

Probitas can consume that evidence only when the operator passes its explicit
`--alexandria-index` option. The translation retains the original venue and
evidence class, combines per-chain coverage conservatively and keeps registry
venues absent from the archive visible as gaps. It does not infer people,
defaults, full repayment or a current balance.

To exercise the whole path without a network, run the fixed demonstration from
the repository root:

```bash
output="$(mktemp -d)/credit-history-v0"
python3 plugins/alexandria/examples/credit-history-v0/demo.py build --output "$output"
python3 plugins/alexandria/examples/credit-history-v0/demo.py verify "$output"
```

The plan pins existing Goldfinch and Clearpool files by digest. The result is a
reproducibility fixture, not a production corpus. Its Goldfinch source remains
provider-reported and its Clearpool source remains subject-scoped with unknown
finality.

## Compound v3 Phase 0

The [Compound method-proof example](../../examples/compound-v3-phase0-v0/README.md)
pins all 28 production Comet deployments at one upstream commit and preserves
two Ethereum USDC transactions. Its checker binds old-state access, nested
calls, the proxy implementation and code, transaction-start storage, ordered
storage writes and a provider-reported finalized boundary.

Generate the fixed registry from a local pinned checkout, or build and check a
captured source tree offline:

```bash
python3 "$SKILL_DIR/../../scripts/compound_v3_phase0.py" registry \
  --comet-repository <comet-checkout> --output registry.json
python3 "$SKILL_DIR/../../scripts/compound_v3_phase0.py" build \
  --input <captured-input> --output <release>
python3 "$SKILL_DIR/../../scripts/compound_v3_phase0.py" check <release>
```

The separate `capture` subcommand is networked. It requires
`ALEXANDRIA_COMPOUND_RPC_URL`, omits the endpoint and headers from the release,
and collects only the fixed corpus. Do not describe the result as an interval
history, chain proof or independent finality check.

The [Compound v3 harvest specification](../../docs/compound-v3-harvest.md)
describes the resumable, reconciled production collector that remains to be
built. Tabularium owns the separate canonical mapping.

Read the [study](../../docs/study.md) for the selected construction and the
[runbook](../../docs/runbook.md) for the implementation boundaries.

## Settled boundary

1. Raw objects retain their exact bytes and native shapes.
2. Release manifests bind components to capture scope and coverage.
3. Tabularium mappings own the meaning of derived credit events and position
   observations.
4. SQLite is a disposable address index, not release evidence.
5. Probitas retains the original venue on every archive-backed record and
   keeps unharvested venue coverage visible.
6. Lazarus fixtures may support selected observations but are not a universal
   archive payload.

A digest can establish that bytes match a manifest. It does not establish who
published them, that an indexer captured a complete chain history, or that a
reported block is canonical. Those claims require separate evidence.
