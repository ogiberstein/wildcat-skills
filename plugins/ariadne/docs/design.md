# Design

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

Why Ariadne has this shape and which alternatives were rejected.

## The problem

Release links do not establish audit revision, bytecode provenance, or fuzz
settings. Assembly strips evidence identity and leaves recipients to reconstruct
claims.

Ariadne records the join under a digest subject.

## Prior art, and where this starts

The envelope and statement are borrowed, not forked.

- **in-toto Statement v1.** `_type` is the literal
  `https://in-toto.io/Statement/v1`, `subject` is an array of
  ResourceDescriptors each of which must carry `digest`, `predicateType` is a
  type URI, `predicate` is the object. Subjects match by digest alone; `name`
  only distinguishes entries.
- **in-toto ResourceDescriptor v1.** `name`, `uri`, `digest`, `content`,
  `downloadLocation`, `mediaType`, `annotations`, with at least one of `uri`,
  `digest` or `content` required.
- **DSSE v1.0.0.** Envelope fields `payload` (base64 of the serialised body),
  `payloadType`, and `signatures[].sig` with optional `keyid`. The signature
  covers `PAE(type, body) = "DSSEv1" SP LEN(type) SP type SP LEN(body) SP body`,
  where `LEN` is decimal ASCII with no leading zeros.
- **Sigstore.** `cosign attest` and `cosign verify-attestation` produce and
  check exactly this envelope. Signing is a solved problem and gets delegated.
- **SLSA provenance v1** covers build execution, not Solidity interfaces,
  storage, fuzz corpora, audit scope, or deployment identity.
- **Sourcify and solc's CBOR metadata** bind deployed bytecode to source. That
  is a check ariadne records the result of, not one it reimplements.

The nearest in-toto predicates, `test-result`, `release`, and `link`, carry no
bytecode digest or storage-layout delta.

## The shape

**The core is artefact-neutral.** Any compiled artefact, dataset, fixture, or
corpus is a digest subject. Absence stays visible, results remain results, claims
name exact subjects, and replay distinguishes exact from nondeterministic work.

**A predicate shapes one artefact kind.** Dataset and contract statements share
a verifier and envelope without sharing a schema.

- `digests.py`: digest sets, file and tree digests, agreement.
- `statement.py`: Statement v1 and subjects.
- `envelope.py`: DSSE, PAE, and both base64 alphabets.
- `safejson.py`: size, depth, and duplicate-key bounds.
- `core_predicate.py`: shared `claims` and `commands`.
- `gates.py`: five core gates.
- `verify.py`: gates, signature state, and unchecked work.
- `registry.py`: type URI to predicate module.
- `predicates/solidity_release.py`: Solidity release predicate.
- `capture/foundry.py`: Foundry capture.
- `deltas.py`: ABI, method identifier, and storage comparisons.
- `replay.py`: deterministic command replay.

## The gates

Five belong to the core and every predicate inherits them. Two are shape a
predicate fills in.

| Gate | Owner | What it holds |
| --- | --- | --- |
| 1 Every claim names its subject | core | A result tied to a repository or a branch is rejected; it names the digest it covers |
| 2 The environment is recoverable | predicate | A bare tool version is not a build description |
| 3 Absence stays visible | core | Skipped, failed, timed-out and redacted work stays in the statement |
| 4 Results are not upgraded into conclusions | core | A passing property records the property and the run, not that the artefact is safe |
| 5 Deltas name both sides | predicate | A comparison fails when either baseline cannot be identified exactly |
| 6 Replay distinguishes deterministic work | core | Bytecode can require an exact match; a fuzz campaign's coverage cannot |
| 7 Signature verification is external | core | An unsigned statement is labelled unsigned and no statement receives an implied author |

## Choices, and what they cost

**One Solidity tool with embedded gates** would be shorter but would fork at the
second predicate instead of serving four artefacts.

**Generic JSON Schema validation** cannot express absence, delta baselines, or
determinism. It can type `counterexamples` as an array but cannot reject an empty
array beside an absent campaign. The standard library has no JSON Schema validator.

A handwritten validator ships beside the interoperability schema. Tests compare
required fields and revision patterns to prevent drift.

**Signing in process** adds a dependency and key custody. Gate 7 instead treats
unsigned statements as supported.

## Constraints

Standard library only on Python 3.9 through 3.13. Tests use committed Foundry
output, touch no network, and require no `forge`.

## Where the risk is

What an audit should look hardest at, and what the log in
[`../audit/AUDIT.md`](../audit/AUDIT.md) works through.

1. **Canonicalisation.** DSSE signs bytes. A verifier that re-serialises the
   payload before checking it verifies something the signer never signed, or
   displays one thing and checks another.
2. **Base64 variance.** DSSE permits both alphabets. A lenient decoder paired
   with a strict re-encoder is a mismatch surface.
3. **Digest confusion.** Subjects match by digest alone. Mixed-case hex,
   truncated values, a weak algorithm accepted alongside a strong one, or an
   empty digest set are all ways to make a subject match something it should
   not.
4. **Gate bypass by omission.** Every absence gate breaks the same way, through
   a field left optional. A missing disposition must fail rather than default to
   passing.
5. **Replay as code execution.** A recorded command inside a statement is
   attacker-controlled data.
6. **Capture reading outside the project.** Paths, symlinks and traversal.
7. **Secrets in statements.** Build commands carry RPC URLs, API keys and
   tokens.
8. **Untrusted JSON.** Size, nesting depth, duplicate keys and integer size in a
   document handed to `verify` by a stranger.
9. **Missing-baseline degradation.** A delta whose baseline cannot be resolved
   must fail gate 5 rather than report no changes.
10. **Unsigned reported as verified.** Without `cosign`, the verifier reports
    structure and gates and says the signature was not checked. It must never
    print a word that reads as an authenticated author.

## Terms

- **Statement.** The in-toto v1 object: subject, predicate type, predicate.
- **Subject.** The digested artefact a statement is about. Matching is by
  digest.
- **Predicate.** The typed body of a statement, shaped for one kind of artefact.
- **Predicate type.** The versioned URI naming that shape, under
  `https://ariadne.wildcat.finance/`.
- **Envelope.** The DSSE wrapper carrying the payload and its signatures.
- **PAE.** Pre-authentication encoding, the byte string a DSSE signature
  actually covers.
- **Digest set.** Algorithm to hex value map, as in `{"sha256": "..."}`.
- **Gate.** A check the verifier runs over a statement; a breach fails the
  statement.
- **Disposition.** What happened to a declared check: passed, failed, skipped,
  timed out, redacted.
- **Determinism class.** Whether a recorded command's output must match byte for
  byte on replay, or cannot.
- **Delta baseline.** The named previous release a comparison is made against,
  identified by digest.
- **Release subject.** One compiled contract in a release, with its creation and
  runtime bytecode digests.
- **Conformance fixture.** A statement committed as a test case, valid or
  breaching a named gate, for other producers and verifiers to run against.
