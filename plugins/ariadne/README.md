# Ariadne

<!-- marketplace-context:start -->
## In one line

Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release.

**Try something else when.** Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence.

**Current frontier.** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.

**Next Fiat job.** Use /hexaemeron:fiat to implement the dataset predicate with its schema, gates, conformance fixtures and capture path while keeping signing and signature verification external. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Release evidence another person can check. Ariadne binds a digest subject to
its compiler, tests, fuzzing, audit scope, and deployment record.

The statement is [in-toto's](https://github.com/in-toto/attestation); the
envelope is [DSSE's](https://github.com/secure-systems-lab/dsse). Ariadne adds
digest-bound claims, visible skipped or failed work, non-verdict results,
identified comparison baselines, and deterministic replay classes.

The core is artefact-neutral. Contract releases are first; datasets, chain-state
fixtures, and grounded-agent releases belong in separate predicates.

## What is in it

- The core holds digest matching, in-toto Statement v1, DSSE
  pre-authentication encoding, the predicate registry, and input bounds.

- Five gates run for every predicate. Two belong to known predicates; unknown
  types report those gates unchecked.

- The Solidity predicate records source, build, bytecode, ABI, selector and
  storage deltas, audit revisions, deployments, and chain-confirmation state.
  [`schemas/`](./schemas) is tested against the validator.

- Capture turns Foundry output into a statement that verifies unedited. It
  accepts stated test results, confirms nothing on-chain, and scrubs the build
  command.

- Replay runs requested `exact` commands without a shell and only when asked; it compares their
  artefact digest. It lists `nondeterministic` commands without running them.

- `tests/fixtures/conformance/` holds passing and gate-breaching statements.
  [`examples/`](./examples) has clean and gap-bearing attestations plus tampered
  copies. Both originals verify; the copies do not.

## The path, end to end

From this directory, `plugins/ariadne`. Capture a release from a build, verify
it, and see a tampered copy refused:

```bash
python3 scripts/ariadne.py capture solidity-release \
  --project tests/fixtures/forge-project/v2 \
  --previous tests/fixtures/forge-project/v1 --previous-name v1.0.0 \
  --repository https://github.com/wildcat-finance/example-escrow \
  --commit 9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a \
  --tests passed --out release.json

python3 scripts/ariadne.py verify release.json
python3 scripts/ariadne.py verify examples/tampered/escrow-v1.1.0-claim-repointed.json

python3 scripts/ariadne.py replay release.json
python3 scripts/ariadne.py replay release.json \
  --allow-execution --project tests/fixtures/forge-project/v2
```

Capture and verify print seven gate lines, three checks, and exit 0. The
tampered example exits 1; gate 1 names the claim outside the subject bytes.

The preview runs nothing. The second rebuilds inside the fixture and compares
the artefact digest; use a copy if the fixture must remain untouched.

## The subcommands

```bash
python3 scripts/ariadne.py predicates
python3 scripts/ariadne.py inspect <statement-or-envelope.json>
python3 scripts/ariadne.py verify <statement-or-envelope.json>
python3 scripts/ariadne.py capture solidity-release --project <dir> \
  --repository <url> --commit <40-hex> --out release.json
python3 scripts/ariadne.py replay <statement.json>
```

`inspect` reports what a bare statement or DSSE envelope covers. `verify` prints
each gate. Exit codes: 0 success, 1 breached gate, 2 bad input.

[`docs/`](./docs) has the design and its rejected alternatives, the predicate
field by field, the conformance set, and the capture flags.

## Where it stops

The registry holds one predicate. Dataset, chain-state fixture, and
grounded-agent types run only core gates and report the rest unchecked.

Nothing confirms a deployment against a chain, signs, or runs as a GitHub
Action. Those jobs need a node, key custody, or an owning workflow.

## Keys

Ariadne holds no keys. `cosign attest` signs; `cosign verify-attestation`
checks. Ariadne reads and writes envelopes, reports signature presence, and
says it did not check them. Unsigned is a supported, labelled state.

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

No test touches a network and none needs a Solidity toolchain.

## Licence

Apache-2.0. See [LICENSE](./LICENSE).
