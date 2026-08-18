# Metron evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `metron-v0.1.0`
- Frontier status: `open`
- Frontier revision: `measured-before-and-after`
- Current frontier: Metron demands a baseline, a re-measurement and a revert when neither moved, and every one of those steps depends on a person choosing to take them.
- Next Fiat job: Ship a budget file and a check that reads it, records a run, compares against the stored baseline, and fails when a named budget regresses beyond its stated variance. Accepted when it fails on a deliberate regression in a fixture, passes on a neutral change, and both suites pass.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `metron-v0.1.0` | baseline | `measured-before-and-after` | `65eec7ac2fae18768bf4c6d041e5ca110675327159afb6e4f69fc23fdae364cc` | [hermes measured gas loop](../../../hermes/skills/hermes/SKILL.md) | Metron starts here, applying the measured-evidence discipline everywhere gas is not the unit. |
