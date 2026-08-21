# ADR-007: Displace the Hermes evidence-bundle frontier for a rule corpus

## Status

Accepted, 2026-08-21. Records the boundary the `hermes-v0.1.1` epoch row cuts;
superseded by a later numbered record once it stops being true.

## Context

Hermes held one frontier target: publish a complete, reproducible evidence
bundle against a real Wildcat release. That target was open and unmet. A
maintainer then supplied a new external requirement, a 1,188-line gas
optimisation reference for Solidity 0.8.25 pinned at SHA-256
`297c926dc0a2e011e31da5245273c136273b8faa390f3691910c22c870068449`, and asked
for it to become Hermes's core rather than an addition beside it.

Two rules stood in the way. The shared versioning contract says only a
completed frontier job may replace a held target, and every plugin landing
README publishes the same sentence to readers: change a skill's next job only
when that exact job completed. Neither rule has an exception for a target that
somebody would simply rather not do yet, and that is the point of both.

The contract does describe one route. An epoch entry records a compatibility or
provenance boundary that makes a skill's earlier lineage an unsafe guide, and
the Fiat controller states plainly that an epoch may replace a held next job
where an evolution or generation may not. The controller also refuses a ledger
that gains any number of rows other than one, so the two-row construction the
study first proposed was never available.

## Decision

The `live-evidence-bundle` target is displaced rather than completed, and the
displacement is recorded as one epoch row, `hermes-v0.1.1`, whose change text
carries the word `reopen` and names the target it reopens. The evolution
counter does not move, because the contract reserves it for completing a held
job and this run completes a different one.

Two things make the epoch honest rather than a label of convenience. A
replacement is absorbed: the corpus becomes the source of truth for what counts
as an optimisation, in place of twelve rows of catalogue prose. And the
execution contract is deliberately broken: `verify` now requires `--rule`, so
every existing Hermes invocation stops working until it names a rule.

## Alternatives

- A generation row, retaining the held target byte for byte. This is what the
  study assumed before the controller was read, and it is what the contract
  permits for a change that does not advance the frontier. It lost because a
  generation may not touch the held job, so the corpus would have shipped while
  the ledger still advertised the evidence bundle as the next thing anyone
  should build. The frontier text would have described the skill as it was two
  changes ago.
- An evolution row, treating the corpus as the completed frontier job. It lost
  because the corpus was never the held target, and recording it as a completed
  frontier advance would make the ledger say a job completed that nobody had
  set. That is exactly the rolling target the frontier discipline exists to
  prevent, and it would leave no trace that the bundle was skipped.
- Building the evidence bundle first and the corpus after. Defensible, and
  rejected by the maintainer when the alternative was put to them. Recording
  the refusal is what this document is for.
- Leaving `--rule` optional, so the corpus advises without binding. It lost on
  the same ground the study's own design section states: a refusal every
  operator can satisfy by omitting a flag is not a refusal, and the corpus
  would have become a second document rather than a core.

## Consequences

Hermes's earlier lineage is an unsafe guide, which is what the epoch counter
says: a reader working from a pre-`0.1.1` invocation, or from the catalogue
alone, is working from a contract that no longer holds. The evidence bundle
target stays reopened and available, and the successor the corpus run's own
evidence supports is recorded in the ledger row instead: twelve classes name 62
of the 120 rules, so 58 documented rules cannot be selected as candidates at
all.

The next maintainer who wants to move a held target now has a worked example of
the only route that exists, and a record of what it costs: an epoch row, a
compatibility boundary they have to be able to name, and a decision record
saying who asked and what was refused.
