# Ephoros evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

## Held frontier

- Current version: `ephoros-v0.2.0`
- Frontier status: `open`
- Frontier revision: `emitted-signal-contract`
- Current frontier: Three Python rules are executable and run clean over this marketplace, while the TypeScript surface, the alert rules and the address-linkage rule remain read by a person.
- Next Fiat job: Extend the lint to catch telemetry keyed by wallet address, the one rule this skill owns that phylax does not, across both Python and the TypeScript surface. Accepted when an address used as a metric label, a dashboard key and a log index are each caught in a fixture, the lint runs clean over this marketplace and wildcat-app-v2, and both suites pass.

## History

- `ephoros-v0.1.0` | baseline | `emitted-signal-contract` | `84e954fec8e47067179c8005120b0d5b689f5c89d0216ecfe4d56c0978f885ab` | [phylax secrets rule](../phylax/SKILL.md) | Ephoros starts here, holding the telemetry a step leaves behind once it runs unattended.
- `ephoros-v0.2.0` | generation | `emitted-signal-contract` | `84e954fec8e47067179c8005120b0d5b689f5c89d0216ecfe4d56c0978f885ab` | [alert annotation study](../../../../docs/ephoros-alert-runbook-annotations-study.md), [skills#319](https://github.com/wildcat-finance/skills/issues/319) | E004 now reports each supported block-YAML alert list entry without its own nested `annotations.runbook` Markdown path. Comments, block scalars, top-level pointers and neighbouring entries do not create or satisfy the annotation, and the existing reasoned pragma remains the only exception. Ephoros stops at presence: Hypomnema owns resolution and target shape. The held frontier revision, digest, status and next job are unchanged.

## Ledger boundary

A generation row records a wider implementation without moving the held
frontier revision or digest.
