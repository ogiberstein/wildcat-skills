# Example attestations

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

## The records

Two `ariadne capture` statements over `../tests/fixtures/forge-project` are
committed as produced.

Build records, digests, and deltas came from the compiler. Test and fuzz
dispositions were supplied by hand; nobody fuzzed the nine-line escrow. A test
binds both examples to the committed fixture.

- `escrow-v1.1.0.json`: tests and fuzz passed; its audit covers the released
  commit and it records a deployment.
- `escrow-v1.1.0-with-gaps.json`: fuzzing timed out and its audit covers an
  earlier revision.

Both verify. The second records four outstanding properties and an audit two
commits behind the release.

```bash
python3 ../scripts/ariadne.py verify escrow-v1.1.0-with-gaps.json
```

It exits 0 after seven gate lines and three checks; the audit line reads `1
covering a revision other than the released commit`.

## The tampered copies

`tampered/` holds a copy of each with one thing changed, and the suite asserts
that `verify` exits 1 on each and names the gate.

- `escrow-v1.1.0-claim-repointed.json`: a claim points outside the statement;
  gate 1 fails.
- `escrow-v1.1.0-with-gaps-reason-removed.json`: timed-out work lacks a reason;
  gate 3 fails.

## What tampering the gates do not catch

A producer editing their own unsigned statement can delete a gap and record a
pass instead. Nothing in the gates can tell that apart from a run that really
passed, because both parse, both pass every gate, and neither contradicts
anything else in the document.

What catches it is an externally verified signature. A statement is signed
over its bytes, so an edit after signing fails verification, and an edit before
signing puts the producer's name on the claim. Gate 7 keeps that boundary
visible: Ariadne labels an unsigned statement unsigned and never supplies an
author from a signature it did not check.

The gates refuse misleading shapes. They cannot establish that a producer told
the truth before signing.
