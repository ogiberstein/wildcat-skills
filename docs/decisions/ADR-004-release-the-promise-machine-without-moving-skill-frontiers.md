# ADR-004: Release the Promise Machine without moving skill frontiers

## Status

Accepted, 2026-08-20. Contract: `promise-machine/v1`.

## Context

The Promise Machine adds one generated law copy and runtime binding to every
plugin. Installed hosts cache plugins by package version, while each canonical
skill carries a separate behavioural version and a held frontier. Treating the
suite release as a skill advance would say that frontier work happened when it
did not. Leaving package versions unchanged would let a host retain the package
from before the governing contract existed.

Level-2 and level-3 promises also produce different durable records. Replacing
those domain formats with one generic envelope would discard useful semantics
and create a second authority beside their existing schemas and writers.

## Decision

Publish every plugin at the patch package version recorded in the Promise
Machine study. The Claude manifest, Codex manifest and Claude marketplace entry
for a plugin carry the same package version. Canonical skill versions,
evolution histories, frontier revisions, frontier digests and `Next Fiat job`
values do not move for this suite-wide release.

Keep domain result formats authoritative. The checked coverage inventory joins
every level-2 and level-3 promise to its existing result schema, writer or
contract and names where promise id, subject, scope, evidence references and
classes, unknowns, transition and exception are carried. The root checker
refuses a missing, incomplete, stale or repository-escaping runtime binding.

## Consequences

Hosts receive the Promise Machine only after observing a new plugin package
identity. A package update no longer implies a skill frontier advance. Reviewers
can inspect consequential results through the domain format they already use
and the checked join that limits what the result authorises.

Future behavioural changes still update the affected canonical skill's
evolution ledger on the axis required by `VERSIONING.md`. Future package-only
changes update the three package surfaces without rewriting skill history.
Rollback restores the prior package manifests, marketplace entries, runtime
inventory, public prose and checker gate together; a partial rollback is not a
valid release state.
