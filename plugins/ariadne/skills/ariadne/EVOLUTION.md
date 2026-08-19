# Ariadne evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `ariadne-v1.1.0`
- Frontier status: `open`
- Frontier revision: `state-fixture-predicate`
- Current frontier: The state-fixture and grounded-agent predicates remain unimplemented; the dataset predicate now ships with its schema, gates, conformance fixtures and capture path.
- Next Fiat job: Implement the state-fixture predicate with its schema, gates, conformance fixtures and capture path, and close the gate 5 hole the dataset run recorded against the Solidity release predicate, which a new predicate would inherit. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `ariadne-v0.1.0` | baseline | `dataset-predicate` | `0c0310a503de564b892e7206d6b8e88ec3acd4ad99a62d02f3f83cd16991bc20` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `ariadne-v1.1.0` | evolution | `state-fixture-predicate` | `ec925d3f57001ac32eb6d40ffdd7d43f130e360283ef40eb8fbbda724f262c2f` | [skills#200](https://github.com/wildcat-finance/skills/pull/200) | Closes the dataset-predicate frontier. The type is registered with its own gates 2 and 5, a coverage check that refuses an interval with no gaps block, an inputs check that refuses a locator on its own, a published schema held to the module by a drift test, nine conformance fixtures, and a capture path that refuses a release it cannot read whole. Eight audit rounds fixed 23 findings; three are recorded open and out of scope. |
