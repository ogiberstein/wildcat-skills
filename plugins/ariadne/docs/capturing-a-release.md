# Capturing a release from a Foundry build

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

```bash
python3 scripts/ariadne.py capture solidity-release \
  --project path/to/project \
  --previous path/to/previous-release --previous-name v1.0.0 \
  --repository https://github.com/you/yours \
  --commit <40-hex git object id> \
  --out release.json

python3 scripts/ariadne.py verify release.json
```

The output passes `verify` unedited. Hand-editing would detach its numbers from
the build.

## What the project needs

Set `build_info = true` in `foundry.toml` and
`extra_output = ["storageLayout"]` for storage deltas. Capture reads:

- `out/build-info/*.json` for compiler version, optimiser settings, EVM target,
  and sources. If absent, capture names the required setting.
- `out/<file>.sol/<Name>.json` for the ABI, both bytecodes, the method
  identifiers and the storage layout.

Nothing is recompiled; the statement records compiler output.

Gate 2 requires a dependency lock digest. Capture uses `foundry.lock`,
`soldeer.lock`, `package-lock.json` or `yarn.lock` if one is there, and the
source directory otherwise. `build.dependency_lock_source` names the choice.

## What capture will not do

**It does not decide whether your tests passed.** A test result arrives as a
stated disposition:

```bash
--tests "passed" --fuzz "timed_out:budget of 30 minutes reached with 4 properties outstanding"
```

Omission records `skipped` with a reason. Capture never invents `passed`.

**It does not confirm a deployment.** `--deployment
chain_id=1,address=0x...,creation_tx=0x...` records
`confirmed_against_chain: false` because no node was queried. An address without
that note would read as confirmed.

**It scrubs the build command, and only that.** URLs lose content after the
scheme, key-shaped tokens are replaced, and values after `--rpc-url`,
`--private-key`, `--etherscan-api-key`, and related flags are redacted. The
redaction count stays with the command. Repository URLs lose `user:token@` but
remain navigable.

Reasons and scopes are recorded verbatim; do not put credentials in them.

**It does not read outside the project.** Resolved `--project`, `--previous`,
and `out` paths may not escape their project, including through symlinks.

## The delta

With `--previous`, capture writes contract-by-contract ABI, selector, and
storage deltas naming both sides. Without it, `"baseline": null` and a reason
pass gate 5 for a declared first release.

`--previous-name` labels the baseline; otherwise capture uses its directory.

## An audit

```bash
--audit report=audits/acme-2026.pdf,revision=<40-hex>,scope="src/Escrow.sol and its libraries"
```

Without the revision, a linked report does not establish coverage of what
shipped.

## Worked example

The fixture project in `tests/fixtures/forge-project` is two versions of one
contract, with build output committed. `v2` adds `sweep(address)` and inserts a
storage variable ahead of `balance`.

```bash
python3 scripts/ariadne.py capture solidity-release \
  --project tests/fixtures/forge-project/v2 \
  --previous tests/fixtures/forge-project/v1 --previous-name v1.0.0 \
  --repository https://github.com/wildcat-finance/example-escrow \
  --commit 9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a \
  --out release.json
```

The delta shows `sweep(address)` added to the ABI and to the selectors,
`deadline` added to storage, and `balance` moved from slot 1 to slot 2.
