# Protasis evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `protasis-v1.1.0`
- Frontier status: `open`
- Frontier revision: `runbook-schema-check`
- Current frontier: Protasis is the sole content authority for Fiat's study and runbook phases, and every rule it states about a runbook step is read by a person rather than executed.
- Next Fiat job: Ship a checker that reads a runbook and fails when a step is missing goal, entry, exit, files or tests, or when an exit names no command. Accepted when it catches each omission in a fixture runbook, passes over this run's own runbook, and both suites pass.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
<!-- hypomnema: allow the linked reference existed when this row was written; the fold this ledger records deleted it -->
| `protasis-v0.1.0` | baseline | `study-and-runbook-content-contract` | `abc3d55f5e57beac3e9e36275c4a0d0964ff0f0a44343f6a1329bd85c9ea5716` | [fiat study reference](../fiat/references/study.md) | Protasis starts here, holding the content contract for the study and runbook phases. |
| `protasis-v1.1.0` | evolution | `runbook-schema-check` | `36e9f312a003b5e61528f80bb3679f084ed9f0750e3b2e41c0d53ea4020f6816` | [fiat phase-skill integration study](../../../../docs/fiat-phase-skill-integration-study.md) | Completes the held fold: Fiat's study and runbook references are deleted, its directive table points both phases here, and this skill carries the content contract alone. |
