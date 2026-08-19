# Conformance fixtures

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
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

The `solidity` and `dataset` fixtures use the two types this build registers, so
they exercise each predicate's own gates as well as the core ones. Gates 2 and 5
mean different things for a dataset release than for a contract release, so each
type carries its own breaching fixtures for them.

## The naming convention

The suite reads the names, so they have to be right:

- `pass-<what>.json` verifies clean. Every gate holds.
- `fail-gate<n>-<what>.json` breaches gate `n` and no other gate.
- `fail-check-<check>-<what>.json` breaches a check that carries no gate number,
  and no other check.

Gates 2 and 5 are numbered. The other checks a predicate adds carry no number,
so they need the third form: coverage and inputs on a dataset release, audits and
deployments on a contract release, and the field-shape check on either. Without
it those checks shipped with no fixture at all.

Four completeness tests hold the set together. Each core gate has a breaching
fixture. Each registered predicate has a passing fixture, and a breaching fixture
of its own type for every numbered gate it owns. Every unnumbered check any
registered predicate exposes has one too. A fifth test asserts that each
breaching fixture fails exactly the gate or check its name claims, which catches
a fixture that breaks two things at once and would pass for the wrong reason.

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
| `fail-check-audits-solidity-without-covered-revision.json` | An audit report attached to a release without naming the revision it covered |
| `fail-check-deployments-solidity-without-confirmation.json` | A deployment address printed without saying whether anything confirmed it against a chain |
| `pass-dataset-release.json` | A complete dataset release: two released files with record counts, one input digested and one recorded absent with its reason, a coverage interval with a gap, and a comparison against the previous release |
| `pass-dataset-first-release.json` | The same shape with a null baseline, its reason, and an empty gap list that asserts the producer looked |
| `fail-gate2-dataset-producer-without-parameters.json` | A producer named with a version but no digest over the parameters it was given |
| `fail-gate5-dataset-baseline-without-digest.json` | A dataset comparison against a release named but not identified |
| `fail-check-coverage-dataset-no-gaps-block.json` | A coverage interval with no gaps block, which reads as complete without saying so |
| `fail-check-inputs-dataset-locator-only.json` | An input with a locator and neither a digest nor a reason for not having one |
| `fail-check-predicate-fields-dataset-unknown-field.json` | A dataset predicate carrying a field the type does not define |

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
