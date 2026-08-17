# Alexandria

<!-- marketplace-context:start -->
## In one line

Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend.

**Try something else when.** Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay.

**Current frontier.** The specified production Compound v3 harvester is not implemented.

**Next Fiat job.** Use /hexaemeron:fiat to build the specified production Compound v3 harvester with pinned deployment discovery, explicit coverage and finality evidence, and a reproducible offline release. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose, then replace every completed or stale Next Fiat job with the next evidenced repair or frontier step.
<!-- marketplace-context:end -->

An offline tool for digest-bound lending-data releases.

Alexandria keeps heterogeneous lending-protocol captures unchanged. It binds
each capture to explicit scope and coverage, derives a narrow Tabularium credit
view and supplies that view to Probitas through a disposable index. Alexandria
is an archive and data source, not a lending venue or underwriting system.

## Complete prototype

Alexandria can ingest raw releases, derive verified credit views, rebuild an
address index and query it:

```bash
python3 scripts/alexandria.py --help
python3 scripts/alexandria.py ingest --plan capture-plan.json --output release
python3 scripts/alexandria.py verify release
python3 scripts/alexandria.py derive release --output derived-release
python3 scripts/alexandria.py verify derived-release
python3 scripts/alexandria.py index derived-release --output alexandria.sqlite
python3 scripts/alexandria.py query --index alexandria.sqlite --address 0x...
```

Ingest copies the declared raw bytes into SHA-256-derived paths and writes one
canonical manifest. Verification checks the release identity, every byte count
and digest, confined paths, component access and redistribution classes,
capture source, scope, finality, evidence class, counted coverage, declared
gaps, correction links and exact release-tree membership without using the
network or changing the release. Repeating an ingest from fixed inputs
produces the same objects, manifest and release ID.

Goldfinch and Clearpool releases can now produce deterministic Tabularium
credit events and position observations. Verification rebuilds both views from
the raw objects and reconciles provenance, mapping revisions and coverage.
Row IDs survive capture renames and raw-release corrections. Native repayment
amounts stay labelled as source amounts because neither input splits them into
principal and interest.

The SQLite index is disposable. Each build starts from verified derived
releases and refuses to write inside them. Each query checks the exact SQLite
schema and logical digest, then matches every indexed partition to its
referenced release. Equivalent rows shared by cumulative releases appear once;
conflicting rows under one ID are refused. Queries return stable event,
observation and per-venue coverage JSON. Probitas opts into the archive with
`--alexandria-index`; its normal fixture and live adapter route is unchanged.

The checked-in [`credit-history-v0`](examples/credit-history-v0/README.md)
demonstration runs that complete path from the existing Goldfinch and Clearpool
source files through Probitas's five gates without network access:

```bash
output="$(mktemp -d)/credit-history-v0"
python3 examples/credit-history-v0/demo.py build --output "$output"
python3 examples/credit-history-v0/demo.py verify "$output"
```

Its expected receipts bind 522 derived events, 31 observations, an 11-event
Clearpool address query and 11 Probitas records. Goldfinch remains partial for
that query because the mapping declares 25 unsupported native records.

## Architecture

The design separates:

1. unchanged raw objects named by SHA-256;
2. immutable release manifests with exact scope and coverage;
3. Tabularium-owned credit events and position observations; and
4. a disposable SQLite address index for Probitas queries.

A digest match will prove only that local bytes agree with the manifest. It
will not prove who published them, that a hosted source was complete or that
its reported block was canonical.

## Design record

- [`docs/study.md`](docs/study.md) records the research, selected construction
  and risk register.
- [`docs/runbook.md`](docs/runbook.md) divides the prototype into five chained
  delivery steps.
- [`docs/raw-releases.md`](docs/raw-releases.md) defines the ingest, identity,
  coverage and offline verification rules.
- [`docs/credit-view.md`](docs/credit-view.md) defines the registered mappings,
  row contracts and derived-release verification.
- [`docs/address-index.md`](docs/address-index.md) defines index rebuilding,
  queries, false-empty refusal and the Probitas bridge.
- [`docs/compound-v3-harvest.md`](docs/compound-v3-harvest.md) pins Compound's
  official registry and specifies production capture, revision, checkpoint,
  reconciliation and acceptance rules. It is a plan, not a harvester.
- [`docs/data-dictionary.md`](docs/data-dictionary.md) names the fields that
  cross raw releases, derived views, queries and Probitas.
- [`schemas/README.md`](schemas/README.md) states when each machine-readable
  contract enters the build.
- [`examples/README.md`](examples/README.md) states the offline demonstration
  boundary.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria
```

The implementation uses Python's standard library and reaches no network.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
