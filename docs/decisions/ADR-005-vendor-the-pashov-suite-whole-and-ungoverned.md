# ADR-005: Vendor the Pashov suite whole and ungoverned

## Status

Accepted, 2026-08-20. Records a boundary in force since the suite was
vendored; superseded by a later numbered record once it stops being true.

## Context

Hexaemeron bundles five skills that originate outside Wildcat Labs: `x-ray`,
`solidity-auditor`, `fizz` and fizz's two nested skills, together the Pashov
suite. The delivery loop depends on them for its security rounds, so they have
to ship inside the plugin. They are also another author's working method, and
every other first-party skill here is governed by an `EVOLUTION.md` ledger
under the versioning contract. The question the repository answered in
practice, and never wrote down, is how upstream instructions live inside a
governed marketplace.

## Decision

The suite is vendored whole: upstream-owned, byte-for-byte unmodified, and
ungoverned. No vendored skill keeps a ledger or a Wildcat version; the
versioning contract exempts them by name and Hexaemeron's plugin frontier
covers them as a bundle. What the Wildcat suite accepts from a vendored
operation is stated outside the vendored bytes, in digest-bound overlay
declarations; ADR-003 records that binding.

## Alternatives

- Fork and adapt the suite. Editing the instructions would let the loop's
  conventions reach inside them, but the files would stop being comparable to
  upstream, so an upstream improvement or correction could never be reviewed
  in or attributed. It lost because an unattributable fork costs more than
  the adaptation buys.
- Govern each vendored skill with its own ledger. Ledgers would make the
  suite look like the rest of the marketplace, but the frontier discipline
  would then hold Wildcat accountable for evolving another author's method,
  and a `Next Fiat job` on someone else's instructions is a promise nobody
  here can keep. It lost because a ledger states ownership the suite does not
  have.
- Pin the suite as an external dependency and fetch it at install time. The
  plugin would stay small, but installation would gain a network dependency
  and an unpinned trust boundary, and offline installs would break. It lost
  because the loop's security rounds cannot depend on a fetch.

## Consequences

Upstream updates arrive as deliberate re-vendoring: new bytes, reviewed, with
the overlay digests recomputed or the update refused. The suite's behaviour
is always attributable to its author, and Wildcat's claims about it live in
first-party files the checker can hold to account. The cost is that the
loop's own conventions stop at the vendored boundary: the prose masks, the
ledgers and the promise declarations never reach inside those directories,
and `hypomnema.py` skips them unless asked not to.
