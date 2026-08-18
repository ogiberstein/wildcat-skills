# The Solidity release predicate

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

Type URI: `https://ariadne.wildcat.finance/solidity-release/v1`.
Schema: [`schemas/solidity-release-v1.json`](../schemas/solidity-release-v1.json).

Compiled bytecode is the release subject. Every creation and runtime digest is
in `subject`, so a reader holding the bytes can find its statement.

The predicate adds checkable release facts to core `claims` and `commands`.

## The fields

**`source`** -- `repository`, `commit`, `tree_digest`. A commit identifies the
revision; the tree digest identifies bytes.

**`build`** -- `compiler`, `compiler_version`, `optimizer.enabled`,
`optimizer.runs`, `evm_version`, optional `via_ir`, `dependency_lock_digest`,
and argv `command`. Gate 2 requires the full environment.

**`release_subjects`** -- per-contract `name`, `source_path`, `creation_digest`,
`runtime_digest`, and optional `abi_digest`. Every digest must be a subject.

**`deltas`** -- previous-release comparison. Both sides and every `abi`,
`method_identifiers`, and `storage` entry carry `name` and `digest`. A first
release carries `"baseline": null` and `reason`.

**`audits`** -- `report_digest`, `covered_revision`, `scope`. Without
`covered_revision`, the report does not establish coverage of what shipped.

**`deployments`** -- `chain_id`, `address`, `creation_tx`, optional proxy
`implementation`, and `confirmed_against_chain`. This offline build records
`false` rather than implying confirmation.

## The two gates it owns

**Gate 2, the environment is recoverable.** Requires full build and source
records and names missing fields.

**Gate 5, deltas name both sides.** Refuses unidentified sides and delta content
beside a null baseline.

With five core gates, a release prints seven gate lines and three checks for
field shape, audits, and deployments.

## What the deltas measure

An ABI removal breaks compile-time callers. A method identifier change under an
unchanged signature breaks runtime calls. Storage movement breaks upgrades.

Storage comparison follows variables, catching moved or retyped values.

## The schema and the validator

The schema guides other producers. The validator also enforces semantic absence,
baseline, and determinism rules: a schema can type `counterexamples` as an array
but cannot reject an empty array beside an absent campaign.

Tests compare schema requirements with module field tables; drift fails.

## Worked examples

`tests/fixtures/conformance/pass-solidity-release.json` is a complete release
with a skipped fuzz campaign, an audit and an unconfirmed deployment.
`pass-solidity-first-release.json` is the same shape with a null baseline. The
`fail-gate2-*` and `fail-gate5-*` fixtures beside them each breach one gate.

```bash
python3 scripts/ariadne.py verify tests/fixtures/conformance/pass-solidity-release.json
```
