# ADR-028: Use cumulative portable checkpoints rooted at an immutable Fiat base

## Status

Proposed, 2026-08-24. Recorded for
[skills#558](https://github.com/wildcat-finance/skills/issues/558) and
[skills#559](https://github.com/wildcat-finance/skills/issues/559). Planned
implementation is split between
[skills#560](https://github.com/wildcat-finance/skills/issues/560) and
[skills#561](https://github.com/wildcat-finance/skills/issues/561).

PR #569 published this record as ADR-023. That collision check ran against an
earlier `main`, and by the time the PR merged, ADR-023 held the accepted Kronos
working-state decision. This record moved to ADR-028. The decision is
unchanged.

## Context

Fiat keeps controller state and its receipt ledger under ignored
`.hexaemeron/` state in the run's dedicated worktree. Git branches transfer
committed repository history, but they do not establish the exact portable
controller state, receipt prefix, bounded run observation, prior checkpoint
acceptances, or next permitted action.

Long runs also face a moving integration branch. Fiat `5.19.1` keeps the
exact starting commit in `state.base` while `config.git.base` names the branch
used for later integration. PRs #549 and #550 preserve product evidence across
that movement, and PR #562 retains bounded superseded sync receipts when a
failed composition is replaced by fresh signed and revalidated evidence. A
checkpoint must carry the same distinctions: the run start is immutable
evidence; a later `main` commit is context for integration, not a new origin
for earlier work; and an inactive failed sync remains part of the receipt
history rather than disappearing behind its replacement.

PRs #478 and #479 contain useful earlier work on cumulative archives. Their
late ADR bytes were not part of the recorded audit round and did not land on
`main`. That proposal also allowed arbitrary staged, unstaged, and untracked
state. The contribution promise in Wave Delta needs a smaller first boundary:
one completed green Fiat transition that another machine can verify and
continue.

## Decision

A version-1 portable Fiat checkpoint is a cumulative archive created only at a
green transition: implementation, audit, prose, commit signature, push, and
remote verification have passed, and the dedicated worktree is clean apart
from allowlisted controller-owned portable state. Active and superseded
integration-sync receipts are part of that portable state when the run has
reached integration.

One run records a `run_anchor` containing repository, issue, run id, execution
class, controller version, study/runbook/policy digests, and the full starting
commit. The starting commit is immutable for the run. A later observed or
integrated `main` SHA is recorded separately and has no effect on checkpoint
identity or lineage.

Each archive contains a complete Git bundle able to materialise both the
starting commit and declared working commit, path-independent controller state,
a verified receipt prefix, one schema-valid bounded run observation, prior
checkpoint acceptance statements, and a digest/size/media-type inventory. It
does not carry credentials, live delegation handles, locks, sockets, caches,
build output, raw host/model transcripts, or the current checkpoint's own
acceptance statement.

The format uses two identities:

- `snapshot_id` is SHA-256 over the canonical typed semantic snapshot payload.
  The profile fixes UTF-8/Unicode handling, key and array order, optional-field
  form, integers, and domain separation; it refuses floats and ambiguous
  encodings.
- `archive_sha256` is SHA-256 over the exact deterministic ZIP bytes.

The archive may carry `snapshot_id` outside the payload it hashes. The service
acceptance statement is a signed sidecar over the already computed snapshot and
archive identities, so no digest includes a signature that depends on that
same digest. The next cumulative checkpoint carries the prior statement.

A root run-anchor record has stage zero. Every checkpoint names accepted
parents and derives stage as one plus the maximum parent stage. Clocks and
upload order never establish progress.

Restore writes only into an empty, newly created dedicated worktree. It verifies
the archive profile, every member digest, Git objects and signatures, starting
and working commits, receipt prefix, observation binding, prior acceptance
chain, and next controller action before offering an explicit resume.

## Alternatives

- **Incremental patch chain.** Smaller uploads and better deduplication.
  Rejected for version 1 because every restore depends on all earlier untrusted
  objects, one missing or revoked object strands descendants, and a later
  checkpoint is not independently useful.
- **Git branches and pull requests only.** Already deployed and good for
  authorship. Rejected as the full answer because the ignored controller and
  receipt state plus the next action remain local.
- **Capture an arbitrary dirty worktree.** Preserves more unfinished effort.
  Rejected for version 1 because it widens secret and filesystem exposure,
  makes the audit/prose/signature boundary unclear, and can restore a state that
  is not safe for another contributor to trust. A later protocol may add an
  explicitly non-advancing draft package under a separate decision.
- **Rebase each checkpoint onto current `main`.** Makes the archive look
  current. Rejected because it rewrites the run anchor and confuses integration
  work with evidence already earned at the original product head.
- **One digest for semantic and transport identity.** Simpler to explain.
  Rejected because deterministic transport changes and semantic changes have
  different compatibility and security consequences.

## Consequences

Cumulative archives repeat Git and controller bytes. Storage and upload are
larger than an incremental chain, and version 1 cannot rescue arbitrary
unfinished editor state. In return, one accepted archive is a complete,
bounded handover unit whose meaning does not depend on earlier uploads or the
contributor's machine.

Starting-base drift becomes mechanically distinguishable from later integration
drift. A service or Atlas response cannot turn a newer `main` SHA into a new
origin for the run.

The current acceptance statement remains outside the archive and must be kept
with it. The next checkpoint carries the prior statement, so a later restore can
verify the publication chain without a self-reference.

This record chooses the portable state and identity boundary. It does not
choose service ownership, infrastructure, enforcement class, or fork policy;
ADR-029 through ADR-032 cover those decisions. It remains Proposed until review
accepts it and the component issues prove the named refusal cases.
