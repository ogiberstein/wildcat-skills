# Conformance fixtures

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

`tests/fixtures/conformance/` checks producers and verifiers against the core
gates. Later predicates inherit the set.

Core fixtures use the deliberately unregistered
`https://ariadne.wildcat.finance/conformance-example/v1`. A verifier runs core
gates and reports gates 2 and 5 unchecked.

The registered `solidity` and `gate2`/`gate5` fixtures also exercise predicate
gates.

## The naming convention

- `pass-<what>.json` verifies clean. Every gate holds.
- `fail-gate<n>-<what>.json` breaches gate `n` and no other gate.

Tests require a breaching fixture per core gate and exactly the named failure.

## What is here

- `pass-minimal.json`: one subject and empty claims and commands blocks. Empty
  is recorded; absent is not.
- `pass-absence-recorded.json`: passed, skipped, and timed-out claims with both
  determinism classes.
- `pass-in-an-unsigned-envelope.json`: the same shape in an unsigned DSSE
  envelope.
- `fail-gate1-claim-names-a-branch.json`: claim names `refs/heads/main`.
- `fail-gate1-digest-not-in-subject.json`: claim names an uncovered digest.
- `fail-gate3-no-claims-block.json`: claims block absent.
- `fail-gate3-no-disposition.json`: claim disposition absent.
- `fail-gate3-skipped-without-reason.json`: skipped work has no reason.
- `fail-gate4-conclusion-key.json`: verdict under `summary.verdict`.
- `fail-gate6-no-determinism.json`: command lacks a determinism class.
- `fail-gate6-exact-without-output-digest.json`: exact command lacks output.
- `fail-gate7-self-asserted-verification.json`: payload claims verification.
- `pass-solidity-release.json`: skipped fuzzing, revision-bound audit, and
  unconfirmed deployment.
- `pass-solidity-first-release.json`: null baseline with a reason.
- `fail-gate2-compiler-version-only.json`: compiler version alone.
- `fail-gate2-source-without-commit.json`: tree digest without commit.
- `fail-gate5-baseline-without-digest.json`: named but unidentified baseline.
- `fail-gate5-content-against-null-baseline.json`: changes against no baseline.

## Running them

```bash
python3 scripts/ariadne.py verify tests/fixtures/conformance/pass-absence-recorded.json
python3 scripts/ariadne.py verify tests/fixtures/conformance/fail-gate3-skipped-without-reason.json
```

The first exits 0. The second exits 1 and names the gate. Run the full set with
`python3 -m unittest discover -s tests -t .`.

## What the gates do not catch

Gates 4 and 7 check keys, not prose. A predicate cannot carry `verdict` or
`verified` as a field another tool would read as structured data, and that is
the whole of it. A `reason` string reading "looks fine to me" passes, because
any wordlist over free text would fail honest sentences far more often than
dishonest ones.

Gate 1 checks that a claim names a digest the statement covers. In a statement
with several subjects it cannot tell that a claim about one names another.

The gates cannot establish producer honesty. They refuse misleading shapes.

## Using them elsewhere

The fixtures are plain in-toto statements and DSSE envelopes. Nothing in them
depends on this implementation, so another verifier can read the same files and
should reach the same verdicts. If yours disagrees with one, the disagreement is
worth reporting either way: a fixture can be wrong.
