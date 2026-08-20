# Hypomnema evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `hypomnema-v1.2.0`
- Frontier status: `open`
- Frontier revision: `adr-shape-check`
- Current frontier: Six records exist and the lint resolves their pointers, but it reads no structure: the first four stated their status in three different shapes within a day of being written, and two still carry no alternatives section, which only a reader notices.
- Next Fiat job: Ship a lint rule verifying that each record under docs/decisions/ carries the template's dated status and its five sections, with the existing pragma for deliberate exceptions. Accepted when it catches each omission in fixture records, passes over the tree's records once the two without an alternatives section are filled by their authorship trail, and both suites pass.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `hypomnema-v0.1.0` | baseline | `recorded-reasons-and-their-homes` | `5bcbb5f56863de94e5d141ddb78afc84fcc78aea2e64971dff8e3fd1dc5ceb11` | [skill evolution contract](../VERSIONING.md) | Hypomnema starts here, holding what gets recorded and where it goes. |
| `hypomnema-v1.1.0` | evolution | `adr-shape-check` | `5c69c143dc7adb1380e27931e5440e9772b184b96fc5964f3fb5a722d3ac59f9` | [first-records study](../../../../docs/hypomnema-first-records-study.md), [skills#308](https://github.com/wildcat-finance/skills/pull/308), [skills#309](https://github.com/wildcat-finance/skills/pull/309) | Closes the recorded-reasons-and-their-homes frontier. The marketplace's first deliberate decision records exist under the convention this skill states: ADR-005 records the vendoring boundary around the Pashov suite and ADR-006 the reason skill ledgers are not SemVer, and the lint resolves every pointer in them. The run found the convention's home already alive -- the Promise Machine run had left ADR-001 to ADR-004 under docs/decisions/ in three different status shapes -- so it continued the numbering, normalised all six records to one dated Status shape without moving other content, and named the directory as a running convention in the contract. The successor frontier is the structure the lint cannot yet read: shape drift arrived within a day of the first records, and two records still carry no alternatives section. |
| `hypomnema-v1.2.0` | generation | `adr-shape-check` | `5c69c143dc7adb1380e27931e5440e9772b184b96fc5964f3fb5a722d3ac59f9` | [design bridge study](../../../../docs/hypomnema-design-bridge-study.md), [skills#312](https://github.com/wildcat-finance/skills/pull/312) | A shipped study's chosen design now has to reach a standing record before the step that ships it is receipted. The study names the design and the alternatives that lost, which is the material the record template calls the part that pays, and nothing carried it out of the run artefact once the delivery shipped. The bridge is point-or-write: an ADR under docs/decisions/ for a cross-cutting choice, the skill's EVOLUTION.md row for a governed skill's choice, and never both, because two homes for one decision is the drift the conventions paragraph refuses. The pre-receipt checklist asks for it. The held job's target and acceptance are untouched. |
