# ADR-008: Adopt the source document's rule namespace and declare scope per rule

## Status

Accepted, 2026-08-21. Records the shape of the Hermes gas-rule corpus;
superseded by a later numbered record once it stops being true.

## Context

The corpus transcribes one pinned document: 120 rules, 28 rejected universal
rules and 40 citations. Three shape decisions had to be settled before any of
it was written down, and each becomes something other people cite.

The document identifies its rules as `CMP-01` through `YUL-14` and its
rejections as `MYTH-01` through `MYTH-28`. It also pins itself to exactly one
configuration in its header, Solidity 0.8.25 on Cancun, because that is what
its author measured against.

That single pin cannot survive contact with a real target. Foundry in this
checkout reports `solc: null` for a project that pins no compiler, and its
default `evm_version` is `osaka`, two forks past Cancun. A scope check by string
equality against the document's header would refuse every correct candidate on
a 0.8.28 project and pass an unpinned one.

## Decision

The corpus adopts the document's identifiers verbatim as its public namespace.
`STO-09` in a pull request, a commit message or a `result.json` means the rule
the document numbers `STO-09` and nothing else.

Scope is declared per rule as a compiler range, a fork floor and a pipeline set,
each with a written reason, and separately from `verified_on`, which records the
one configuration the document actually evidences. Comparison is ordering, not
equality: a floor of Berlin is satisfied by Paris and by Osaka. A compiler the
harness cannot read, or a fork name the corpus does not order, refuses rather
than being assumed to match.

Corpus refusals keep exit code 20 and carry a `refusal` string naming the
condition, rather than minting a seventh exit code.

Records are lists of objects carrying an `id`, not objects keyed by id.

## Alternatives

- Renumbering the rules into a Hermes-local scheme. It would have let the
  corpus grow rules the document does not have, without the numbering implying
  a source. It lost because every citation would then need a translation table
  back to the document that justifies it, and a rule id whose authority cannot
  be looked up is worth less than one that can.
- Copying the document's header pins as each rule's scope. Simplest, and it
  lost on measurement rather than taste: it refuses correct candidates on any
  project not pinned to 0.8.25 and Cancun exactly, which is most of them.
- Treating scope as advisory and letting the operator judge. It lost because
  the whole reason for a machine-readable corpus is that the judgement stops
  being a matter of who read the header.
- A seventh exit code for corpus refusals. It reads more precisely at a glance,
  and it lost because the published contract says an exit code names the
  rejected gate, there is no seventh gate, and a code that named one would
  describe the harness wrongly to anybody switching on it. The `refusal` field
  carries the precision instead.
- Keying records by id, which gives uniqueness for free. It lost because
  `json.load` silently drops a duplicate key, so the corpus would answer a
  duplicated rule id by quietly holding one of them. A list makes the duplicate
  a refusal.

## Consequences

The rule ids are an interface. Renaming one later breaks every pull request,
commit message and evidence directory that cited it, so a rule the corpus holds
keeps its id even when the document is revised.

The declared scopes and the class mapping are the two authored fields in an
otherwise transcribed corpus. No schema check can catch a wrong value in either,
which is why each scope bound carries its reason on the page and why both are
read rule by rule in the audit round. The transcribed fields need no such care:
a test compares each against the pinned document.

Any tool reading a Hermes rejection has two things to switch on, the exit code
for the gate and the `refusal` string for the cause, and neither moves when the
other gains a value.
