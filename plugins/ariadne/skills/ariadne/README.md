---
name: ariadne
description: >
  Read and write the signed statements that keep a release joined to the
  evidence behind it: an in-toto statement over a DSSE envelope, with a
  predicate registry and gates that keep absence visible. Use when someone
  hands over an attestation and asks what it actually covers, when a release
  needs evidence a stranger can check rather than a badge, or when a new kind
  of artefact needs a predicate of its own. Never use it to claim a signature
  was verified; that is cosign's job.
metadata:
  version: "0.1.0"
---

# Ariadne

A release publishes a claim. The evidence behind it sits somewhere else, joined
by a URL and a promise: the compiler that produced the bytecode, the test run,
the fuzz campaign, the audit and its scope, the deployment. Ariadne writes the
join down as a statement whose subject is a digest, so a reader can check the
binding without trusting whoever assembled it.

`$SKILL_DIR` is the directory holding this file. The tool lives at
`$SKILL_DIR/../../scripts/ariadne.py`; resolve it from where you loaded this
skill.

## Day to day

**Engineering.** A release goes out and someone asks, six months later, which
commit the deployed bytecode came from and whether the audit covered it. The
statement answers from its own contents rather than from a changelog nobody
updated.

**Security.** An attestation arrives with a release. `inspect` says what it
covers and whether its signatures were checked, and says plainly that this tool
did not check them. What it never does is print an author it has not verified.

**Research and data.** A dataset or a chain-state fixture needs the same thread
as a contract release: the sources read, the block boundary, what was covered
and what was not. The core is artefact-neutral so those predicates cost a module
rather than a fork.

## The commands

```bash
python3 scripts/ariadne.py predicates

python3 scripts/ariadne.py capture solidity-release \
  --project <dir> --previous <dir> --previous-name v1.0.0 \
  --repository <url> --commit <40-hex> --out release.json

python3 scripts/ariadne.py inspect <statement-or-envelope.json>

python3 scripts/ariadne.py verify <statement-or-envelope.json>

python3 scripts/ariadne.py replay <statement.json> [--allow-execution --project <dir>]
```

`predicates` lists the predicate types this build understands. One is
registered, `https://ariadne.wildcat.finance/solidity-release/v1`, and a
statement of any other type still parses and still gets its core gates.

`capture` reads a Foundry project's build output into a release statement that
`verify` accepts unedited. It does not decide whether your tests passed: a
result arrives as a stated disposition, and leaving it out records `skipped`
with a reason saying nothing was supplied.
[`docs/capturing-a-release.md`](../../docs/capturing-a-release.md) has the
flags.

`inspect` reads either a bare in-toto statement or a DSSE envelope wrapping
one, and reports the predicate type, whether that type is registered here, the
subjects with their digests, and what is known about the signatures.

`verify` runs the gates and prints a line for each. When the predicate type is
one this build does not know, it says gates 2 and 5 went unchecked rather than
reporting a clean run. A document that arrived from elsewhere is bounded first:
a size cap, a depth cap counted before parsing, and a refusal of duplicate keys,
all adjustable with `--max-bytes` and `--max-depth`.

`replay` re-runs the commands a statement marks `exact`. Without
`--allow-execution` it prints the plan and runs nothing, which is the default
because the commands inside a statement are somebody else's data rather than
instructions. It never uses a shell, refuses a command whose arguments were
redacted at capture, and refuses a program name carrying a path separator.

Exit codes: 0 success, 1 a gate was breached, 2 usage or validation error.

## The block every predicate carries

Two lists, which the core gates read and a predicate fills in:

- `claims`. What was checked. Each names the subject digest it covers and its
  disposition, one of `passed`, `failed`, `skipped`, `timed_out` or `redacted`.
  Anything other than `passed` carries a reason, because the reason is the
  record.
- `commands`. What was run. Each carries its `argv` and a determinism class of
  `exact` or `nondeterministic`. An `exact` command carries the digest of its
  output, since otherwise a replay would have nothing to compare against.

## What the core refuses

These are properties of the code rather than reminders:

- A subject with no digest, a digest that is not lowercase hex, a truncated
  digest, an empty digest set, or a set carrying only unsupported algorithms.
- A statement whose `_type` is not `https://in-toto.io/Statement/v1`, or whose
  `predicateType` is not a URI.
- A base64 payload mixing the standard and URL-safe alphabets, because it is
  the output of neither encoder and guessing is how a payload gets decoded two
  ways.
- Following a symlink while digesting a source tree. It raises rather than
  either following the link out of the tree or quietly skipping a file that was
  there.

Subjects match by digest and never by name. A verifier that matched by name
would accept a claim pointing at a label instead of at bytes.

## The gates

Seven. Five belong to the core and every predicate inherits them; two are shape
a predicate fills in.

| Gate | Owner | What it holds |
| --- | --- | --- |
| 1 Every claim names its subject | core | A result tied to a repository or a branch is rejected; it names the digest it covers |
| 2 The environment is recoverable | predicate | A bare tool version is not a build description |
| 3 Absence stays visible | core | Skipped, failed, timed-out and redacted work stays in the signed statement |
| 4 Results are not upgraded into conclusions | core | A passing property records the property and the run, not that the artefact is safe |
| 5 Deltas name both sides | predicate | A comparison fails when either baseline cannot be identified exactly |
| 6 Replay distinguishes deterministic work | core | Bytecode can require an exact match; a fuzz campaign's coverage cannot |
| 7 Signing is optional, verification is not | core | An unsigned statement is labelled unsigned and receives no implied author |

The five core gates run for any predicate, including a type this build has
never heard of. Gates 2 and 5 come from the predicate: the Solidity release
predicate implements both, and for a type this build does not know, `verify`
says they went unchecked rather than passing over them in silence.

`tests/fixtures/conformance/` holds a statement that passes and, for each core
gate, one that breaches it. [`docs/conformance.md`](../../docs/conformance.md)
describes the set for anyone writing another producer or verifier.

## What this never does

- Hold a signing key, or produce a signature. `cosign attest` signs the
  envelope and `cosign verify-attestation` checks it.
- Report that a signature was verified. This tool checks none, and says so
  every time it is asked about one.
- Mint a new envelope. The statement is in-toto's and the envelope is DSSE's,
  deliberately, so a verifier written by someone else can read what this
  writes.
- Re-serialise a payload before checking it. A signature covers bytes, and a
  verifier that re-encodes first is checking a document its signer never saw.
- Record a result nobody supplied. Capture writes `skipped` with a reason
  rather than guessing at a run it did not see, and every deployment it writes
  says nothing confirmed it against a chain.

## The Solidity release predicate

The first shape on the core. Its subject is compiled bytecode, and it carries
the source and commit, the compiler and its settings, the creation and runtime
digests of every release subject, the ABI, selector and storage deltas against
the previous release, the audits with the revision each covered, and the
deployments with whether anything confirmed them against a chain. Nothing here
reaches a network, so that last field always says nothing did.

[`docs/solidity-release.md`](../../docs/solidity-release.md) describes it field
by field, and `schemas/solidity-release-v1.json` ships for producers that are not
this tool.

## Examples

[`examples/`](../../examples) holds two attestations over the fixture project:
a clean release, and one carrying a fuzz campaign that timed out and an audit
covering an earlier revision. Both verify. The second is the more useful one to
read: a format whose only examples are clean releases teaches producers to make
their releases look clean.

`examples/tampered/` holds a copy of each with one thing changed, and each
fails a named gate.

## Where it stops

Named so the edge is visible rather than implied.

The registry holds one predicate. The dataset, chain-state fixture and
grounded-agent predicates are specified and not implemented here, so a statement
of one of those types verifies its core gates and is told which gates went
unchecked.

Nothing confirms a deployment against a chain, nothing signs, and nothing runs
as a GitHub Action. Each of those is a deliberate boundary rather than an
omission: the first needs a node, the second needs key custody this tool
declines, and the third needs a workflow that owns neither.
