# Alexandria schemas

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** The specified production Compound v3 harvester is not implemented.
<!-- marketplace-context:end -->

Step 2 defines three raw-release contracts:

- `capture-plan-v1.schema.json` declares local source files, source references,
  capture scope, finality and evidence boundaries;
- `coverage-v1.schema.json` declares counted source collections, explicit gaps
  and complete, partial, failed or unsupported status; and
- `archive-manifest-v1.schema.json` binds copied objects and captures to one
  release identity.

The standard-library verifier enforces the cross-field rules that JSON Schema
cannot express: canonical bytes, safe paths, exact digests, sorted entries,
component access and redistribution classes, capture-source references,
scope, finality and block-identifier semantics, JSON-pointer counts, gap
semantics and correction self-reference.

Step 3 adds `credit-event-v1.schema.json` and
`position-observation-v1.schema.json` for the narrow Tabularium view. The
`tabularium-view-v1.schema.json` manifest section binds both JSONL files,
registered mapping revisions, coverage reconciliation and row counts to the
verified raw release. Runtime checks also require row subjects, actions,
properties and mapping rules to agree with their declared chain and venue.

Step 4 adds `address-index-v1.sql`, the disposable SQLite layout, and
`address-query-v1.schema.json`, the stable query envelope. Index rows retain
derived release, raw release, component, capture and credit-row identities.
Runtime checks also cover the database application ID, schema version, logical
digest, exact release-backed contents, cumulative-row overlap and
coverage-to-empty rules.

`demo-plan-v1.schema.json` covers the repository-source pins and fixed query
used by the offline example. `demo-summary-v1.schema.json` covers its release
identities, logical index digest and artifact receipts. These are demonstration
contracts; production captures still enter through the ordinary capture-plan
schema.
