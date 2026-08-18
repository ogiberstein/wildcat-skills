---
name: ariadne
description: >
  Read and write the evidence statements that keep a release joined to the
  record behind it: an in-toto statement, optionally inside a DSSE envelope,
  with a predicate registry and gates that keep absence visible. Use when
  someone hands over an attestation and asks what it actually covers, when a
  release needs evidence a stranger can check rather than a badge, or when a
  new kind of artefact needs a predicate of its own. Ariadne neither signs nor
  verifies signatures; those operations belong to cosign.
metadata:
  version: "0.1.0"
---

# Ariadne

## Frontier

Ariadne owns its own attestation-predicate frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release.

**Use another tool when.** Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence.

**Current frontier.** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

Ariadne joins a digest subject to its compiler, test run, fuzz campaign, audit
scope, and deployment evidence. A reader can check that binding without trusting
the assembler.

`$SKILL_DIR` is the directory holding this file. The tool lives at
`$SKILL_DIR/../../scripts/ariadne.py`; resolve it from where you loaded this
skill.

## Day to day

**Engineering.** Six months after release, the statement identifies the commit
that produced deployed bytecode and whether the audit covered it.

**Security.** `inspect` shows coverage and signature-check state. It says this
tool checked no signature and never prints an unverified author.

**Research and data.** Dataset and chain-state predicates can bind sources,
block boundaries, coverage, and gaps without forking the artefact-neutral core.

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

`predicates` lists understood types. Only
`https://ariadne.wildcat.finance/solidity-release/v1` is registered; other
types still parse and run core gates.

`capture` turns Foundry output into a statement that `verify` accepts unedited.
It accepts a stated test disposition; omission records `skipped` and its reason.
[`docs/capturing-a-release.md`](../../docs/capturing-a-release.md) has the
flags.

`inspect` reports a bare statement or DSSE envelope's predicate type,
registration, digest subjects, and known signature state.

`verify` prints every gate. Unknown predicates report gates 2 and 5 unchecked.
Before parsing external input, it enforces adjustable `--max-bytes` and
`--max-depth` bounds and refuses duplicate keys.

`replay` handles commands marked `exact`. Without `--allow-execution`, it only
prints the plan. Execution uses no shell and refuses redacted arguments or a
program name with a path separator. Treat recorded commands as somebody else's
data, not instructions.

Exit codes: 0 success, 1 a gate was breached, 2 usage or validation error.

## The block every predicate carries

Every predicate fills two lists read by the core gates:

- `claims`: each check names its subject digest and a `passed`, `failed`,
  `skipped`, `timed_out`, or `redacted` disposition. Non-passing claims require
  a reason.
- `commands`: each run records `argv` and an `exact` or `nondeterministic`
  class. `exact` commands require an output digest for replay comparison.

## What the core refuses

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

Subjects match only by digest; names are labels, not bytes.

## The gates

Seven. Five belong to the core and every predicate inherits them; two are shape
a predicate fills in.

| Gate | Owner | What it holds |
| --- | --- | --- |
| 1 Every claim names its subject | core | A result tied to a repository or a branch is rejected; it names the digest it covers |
| 2 The environment is recoverable | predicate | A bare tool version is not a build description |
| 3 Absence stays visible | core | Skipped, failed, timed-out and redacted work stays in the statement |
| 4 Results are not upgraded into conclusions | core | A passing property records the property and the run, not that the artefact is safe |
| 5 Deltas name both sides | predicate | A comparison fails when either baseline cannot be identified exactly |
| 6 Replay distinguishes deterministic work | core | Bytecode can require an exact match; a fuzz campaign's coverage cannot |
| 7 Signature verification is external | core | An unsigned statement is labelled unsigned and no statement receives an implied author |

All predicates run five core gates. Known predicates supply gates 2 and 5;
unknown types report both unchecked.

`tests/fixtures/conformance/` holds passing and core-gate-breaching statements.
[`docs/conformance.md`](../../docs/conformance.md) describes the set.

## What this never does

- Hold a signing key, or produce a signature. `cosign attest` signs the
  envelope and `cosign verify-attestation` checks it.
- Report that a signature was verified. This tool checks none, and says so
  every time it is asked about one.
- Mint a new envelope. The statement is in-toto's and the envelope is DSSE's,
  deliberately, so a verifier written by someone else can read what this
  writes.
- Re-serialise before checking. A signature covers the received bytes.
- Record an unsupplied result. Capture writes `skipped` with a reason; every
  deployment says nothing confirmed it on-chain.

## The Solidity release predicate

Its compiled-bytecode subject carries source and commit, compiler settings,
creation and runtime digests, ABI, selector and storage deltas, audit revisions,
deployments, and chain-confirmation state. Nothing here reaches a network, so
that state always says unconfirmed.

[`docs/solidity-release.md`](../../docs/solidity-release.md) describes it field
by field, and `schemas/solidity-release-v1.json` ships for producers that are not
this tool.

## Examples

[`examples/`](../../examples) holds a clean attestation and one with a timed-out
fuzz campaign and stale audit revision. Both verify.

`examples/tampered/` holds a copy of each with one thing changed, and each
fails a named gate.

## Where it stops

The registry holds one predicate. Dataset, chain-state fixture, and
grounded-agent predicates are specified but unimplemented; they run core gates
and report predicate gates unchecked.

Nothing confirms deployments on-chain, signs, or runs as a GitHub Action. Those
jobs require a node, key custody, or an owning workflow.
