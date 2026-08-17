# Conformance fixtures

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** Dataset, state-fixture and grounded-agent predicates are specified but not implemented.
<!-- marketplace-context:end -->

`tests/fixtures/conformance/` holds statements for checking an implementation
against, whether it produces them or verifies them. They exercise the core
gates, so a predicate written later inherits the whole set rather than starting
its own.

The core fixtures use the predicate type
`https://ariadne.wildcat.finance/conformance-example/v1`, which is registered
nowhere on purpose. A verifier meeting it should check the core gates, report
that gates 2 and 5 belong to a predicate it does not know, and not describe the
run as clean.

The `solidity` and `gate2`/`gate5` fixtures use the Solidity release type, which
this build does register, so they exercise the predicate's own gates as well as
the core ones.

## The naming convention

The suite reads the names, so they have to be right:

- `pass-<what>.json` verifies clean. Every gate holds.
- `fail-gate<n>-<what>.json` breaches gate `n` and no other gate.

A test asserts that each core gate has at least one breaching fixture, so a gate
added later cannot ship without one. Another asserts each breaching fixture
fails exactly the gate its name claims, which catches a fixture that breaks two
things at once and would pass for the wrong reason.

## What is here

| Fixture | What it shows |
| --- | --- |
| `pass-minimal.json` | The smallest statement that holds: one subject, an empty claims block and an empty commands block. Empty is a record; absent is not |
| `pass-absence-recorded.json` | A passed claim, a skipped one with its reason, a timed-out one with its reason, and both determinism classes |
| `pass-in-an-unsigned-envelope.json` | The same shape inside a DSSE envelope with no signatures, verified and reported unsigned |
| `fail-gate1-claim-names-a-branch.json` | A claim naming `refs/heads/main` instead of a digest |
| `fail-gate1-digest-not-in-subject.json` | A claim naming a digest the statement does not cover |
| `fail-gate3-no-claims-block.json` | A predicate with no claims block at all |
| `fail-gate3-no-disposition.json` | A claim that does not say what happened to it |
| `fail-gate3-skipped-without-reason.json` | Work marked skipped with no reason given |
| `fail-gate4-conclusion-key.json` | A verdict smuggled in as `summary.verdict` |
| `fail-gate6-no-determinism.json` | A recorded command with no determinism class |
| `fail-gate6-exact-without-output-digest.json` | An exact command with nothing for a replay to compare against |
| `fail-gate7-self-asserted-verification.json` | A payload asserting inside the signed bytes that it was verified |
| `pass-solidity-release.json` | A complete Solidity release: a skipped fuzz campaign, an audit naming its revision, an unconfirmed deployment |
| `pass-solidity-first-release.json` | The same shape with a null baseline and a reason |
| `fail-gate2-compiler-version-only.json` | A build described by a compiler version and nothing else |
| `fail-gate2-source-without-commit.json` | A source record with a tree digest and no commit |
| `fail-gate5-baseline-without-digest.json` | A comparison against a release named but not identified |
| `fail-gate5-content-against-null-baseline.json` | Added functions listed against a baseline the statement says does not exist |

## Running them

```bash
python3 scripts/ariadne.py verify tests/fixtures/conformance/pass-absence-recorded.json
python3 scripts/ariadne.py verify tests/fixtures/conformance/fail-gate3-skipped-without-reason.json
```

Exit 0 for the first, 1 for the second, with the failing line naming the gate.
The whole set runs under:

```bash
python3 -m unittest discover -s tests -t .
```

## What the gates do not catch

Worth stating, so nobody reads a clean run as more than it is.

Gates 4 and 7 check keys, not prose. A predicate cannot carry `verdict` or
`verified` as a field another tool would read as structured data, and that is
the whole of it. A `reason` string reading "looks fine to me" passes, because
any wordlist over free text would fail honest sentences far more often than
dishonest ones.

Gate 1 checks that a claim names a digest the statement covers. In a statement
with several subjects it cannot tell that a claim about one names another.

None of these gates can tell whether a producer meant well, and none is asked
to. They refuse the shapes that let a careless statement read as a careful one.

## Using them elsewhere

The fixtures are plain in-toto statements and DSSE envelopes. Nothing in them
depends on this implementation, so another verifier can read the same files and
should reach the same verdicts. If yours disagrees with one, the disagreement is
worth reporting either way: a fixture can be wrong.
