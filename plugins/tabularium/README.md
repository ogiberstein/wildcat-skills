# Tabularium

<!-- marketplace-context:start -->
## In one line

Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning.

**Try something else when.** Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay.

**Current frontier.** Compound v3 schema and adapter work is specified; Euler v1/v2 preservation is tracked in wildcat-finance/skills#57.
<!-- marketplace-context:end -->

A public record of on-chain credit events that keeps the venue's source record
beside every common row.

Goldfinch wound down with its front end gone and its hosted indexer still
serving the borrower record. Tabularium preserves that record now, while it is
cheap to reach, and turns the 34 borrow and 477 repay entities into 511 rows
another researcher can rebuild without the endpoint.

The common event families do not flatten the venue. A row says
`goldfinch.borrow` or `goldfinch.repay`, keeps the complete native entity, and
names the mapping rule and adapter version that produced it. In particular, a
repayment row records the payment Goldfinch reported. It does not say that the
borrower's whole debt was settled.

Three rules hold the release together:

1. Raw evidence and interpretation stay separate. The source bytes are never
   rewritten to make the canonical output tidier.
2. Coverage is a file, not an assurance. Mapped and unsupported entity counts,
   interpretation versions and known gaps sit in `coverage.json`.
3. Verification rebuilds. Matching a declared digest is not enough; `verify`
   maps the preserved source again and requires the bytes, order and source
   selectors to agree.

## Run it

From this directory, `plugins/tabularium`:

```bash
python3 scripts/tabularium.py build \
  --source <release-dir>/source.json \
  --capture-manifest <release-dir>/capture.json \
  --out <release-dir>/events.jsonl \
  --manifest <release-dir>/coverage.json \
  --release <release-id>

python3 scripts/tabularium.py verify <release-dir>/coverage.json
```

`build` refuses a capture whose source digest, byte count, indexed block,
indexed block timestamp, deployment or entity counts disagree with the raw
snapshot. It writes canonical JSONL and a coverage manifest only inside the
release directory.

`verify` reaches no network and writes nothing. It refuses absolute paths,
parent traversal, symlinks, aliased files, unsupported versions, malformed
JSON, count drift, duplicate selectors, reordered rows and canonical bytes
that do not match a fresh source rebuild.

## The checked-in release

[`examples/goldfinch-v0`](examples/goldfinch-v0/README.md) contains the
unchanged source and capture manifest, the 511-row ledger, its coverage
manifest, a data dictionary and a rebuild demonstration.

From the repository root:

```bash
python3 plugins/tabularium/examples/goldfinch-v0/rebuild.py
```

The demonstration copies the preserved inputs to a new temporary directory,
builds there, makes all four release files read-only, verifies them offline and
compares the canonical and coverage bytes with the committed release. It never
rewrites the example.

The source also contains `_meta`, `callableLoans`, `creditLines` and
`tranchedPools`. Their counts remain visible in the coverage manifest, but this
adapter does not turn them into canonical events.

## What it never proves

The capture boundary is the block reported by a hosted indexer. Neither that
boundary nor each event has an independently verified Ethereum block number
and hash here.

The release is unsigned. Offline verification proves that the four local files
agree with one another and with the implemented mapping. It does not establish
publisher identity or authenticity.

No address-to-person inference and no counterparty score enter the ledger.
Those are different claims, with different evidence, and do not belong inside
an event record.

## Adding a venue or correcting a release

[`docs/adding-an-adapter.md`](docs/adding-an-adapter.md) sets out the source
validation, mapping, provenance, coverage and fixture work a new venue needs.
[`docs/release-policy.md`](docs/release-policy.md) makes published
interpretations immutable: a corrected mapping gets a new version and a new
release directory rather than replacing old bytes.

[`docs/compound-v3-preservation.md`](docs/compound-v3-preservation.md) specifies
the Compound III mapping and preservation requirements. Alexandria's linked
harvest specification owns raw collection; this document explains why logs
alone miss or misclassify debt transitions and what execution evidence the
Tabularium mapping needs.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium
```

Python 3.9 or later, standard library only. The tests make no network request.

## Reading further

- [`examples/goldfinch-v0/DATA-DICTIONARY.md`](examples/goldfinch-v0/DATA-DICTIONARY.md)
  -- every canonical field and the limits of its meaning.
- [`docs/adding-an-adapter.md`](docs/adding-an-adapter.md) -- how a second venue
  earns a release.
- [`docs/release-policy.md`](docs/release-policy.md) -- how a later
  interpretation supersedes an earlier one without rewriting it.
- [`docs/compound-v3-preservation.md`](docs/compound-v3-preservation.md) -- the
  Compound III mapping and preservation requirements.
- [`audit/AUDIT.md`](audit/AUDIT.md) -- every audit round and the fixes it
  required.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
