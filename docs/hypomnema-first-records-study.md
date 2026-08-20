# Study: The first decision records and their convention

Assuming, unless corrected:

1. The four records the Promise Machine run left under `docs/decisions/` stand as the convention's home and numbering; this run continues from ADR-005 rather than starting a second scheme.
2. Normalising those four records' headings to the template preserves every fact in them; only section shape moves.
3. The run starts from `main` at `f12f23f7f098b2f24609976bb93f64d3055850ab`.

## 1. Problem statement

Hypomnema's held frontier job: establish the first decision records for choices this marketplace already made and never wrote down, starting with the vendoring boundary around the Pashov suite and the reason skill ledgers are not SemVer. Both decisions govern daily work -- the vendored suite is edited by nobody and governed by no ledger, and every ledger label reads like SemVer while meaning something else -- yet the reason for each lives in scattered contract prose or in nobody's head. Done means the two records exist under the convention the skill states, `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins` exits 0 resolving every pointer in them, the ledger takes one evolution row (`hypomnema-v0.1.0` to `hypomnema-v1.1.0`), and both suites pass: `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

- `docs/decisions/` already holds ADR-001 to ADR-004, written by the Promise Machine run after this job was held. The directory and numbering are the convention; this run continues them. The four records state their status in three different shapes (a `## Status` section, a bare status line, a bullet list), which is the drift hypomnema's own "match what is already there" rule exists to stop, one day in.
- ADR-003 records the digest binding of vendored promises. It assumes the vendoring boundary rather than recording it: why the suite is vendored whole, byte-exact and ungoverned is stated across `plugins/hexaemeron/skills/VERSIONING.md`, `AGENTS.md` and the Hexaemeron runtime contract, and decided nowhere. ADR-005 records the boundary and points at ADR-003 for the binding.
- `plugins/hexaemeron/skills/VERSIONING.md` states that ledger labels "are not SemVer" and defines the three counters, but the document is a contract, not a record: it says what holds, not what was rejected or why. ADR-006 records the decision behind it.
- The audit records of the in-scope skills were read before design options were drawn. The hypomnema ledger has one baseline row and no audit rounds of its own; the protasis rounds from this wave record no accepted lead touching record placement.
- The last two merged pull requests that changed the target: [skills#293](https://github.com/wildcat-finance/skills/pull/293), which created `docs/decisions/` and whose carried-forward items are host-capture work outside this run's scope; and [skills#276](https://github.com/wildcat-finance/skills/pull/276), which touched hypomnema's sibling ledgers and carried the plugin-cache staleness item that stays open and host-owned.

## 3. Constraints and non-goals

- Starting ref: `main` at `f12f23f7f098b2f24609976bb93f64d3055850ab`. The two `test_elenchus_checker` cases needing `forge` and node v26 stay failing in this container, identically on base.
- The evolution row replaces the frontier fields and recomputes the digest; the versioning contract's axis arithmetic is enforced by the evolution suite and the integrate gate.
- Non-goal: the forward-looking bridge from each study's chosen design into an ADR, which is the separate wish this batch delivers next.
- Non-goal: a mechanical shape check over records; that is this run's frontier judgement to hold, not to build.
- Non-goal: backfilling every unrecorded decision in the marketplace; the held job names two and the numbering leaves room for the rest.

## 4. Design options

1. **Two new records under the existing directory, plus normalising the four existing records to the template's headings.** Chosen: it meets the held job under the convention as it stands, and the normalisation makes the convention it claims -- one shape, stated once -- true on the day the ledger says it is established. It trades away byte-stability of four day-old records, whose content survives unchanged.
2. **Two new records, existing four left as they are.** Rejected: the skill's own red flag is a second scheme beside the first; leaving three status shapes standing establishes all three.
3. **Fold the two decisions into `VERSIONING.md` and the runtime contract as prose.** Rejected: a contract states what holds; the value of a record is the alternatives that lost, which contract prose has no home for.

## 5. Risk register seed

```risk-register
content-drift | the four normalised records against their committed content | the round diffs each normalisation and confirms no fact, date or alternative moved
pointer-rot | every relative link in the six records | the round requires the hypomnema lint at exit 0 over docs and plugins
ledger-arithmetic | the evolution row against the versioning contract | the round relies on the evolution suite passing over the new row
```

The audit loop should look hardest at content-drift: a normalisation that quietly reworded a rejected alternative would corrupt the only home that reasoning has.

## 6. Glossary seeds

- Record: an ADR under `docs/decisions/`, numbered in sequence, carrying status, context, decision, alternatives and consequences.
- Vendoring boundary: the rule that the Pashov suite ships byte-exact, upstream-owned and ungoverned by skill ledgers.
- Template: the record shape hypomnema's contract states, with the alternatives section carrying the reasons the losers lost.

## 7. Sources

- `plugins/hexaemeron/skills/hypomnema/SKILL.md` and `EVOLUTION.md`
- `docs/decisions/ADR-001` to `ADR-004`
- `plugins/hexaemeron/skills/VERSIONING.md`, `AGENTS.md`, `plugins/hexaemeron/AGENTS.md`, `plugins/hexaemeron/PROMISES.md`
- [skills#293](https://github.com/wildcat-finance/skills/pull/293), [skills#276](https://github.com/wildcat-finance/skills/pull/276)
- Wishlist grab-bag, hypomnema section (artifact `12e0da9f`, read 2026-08-20)

## 8. Signals, and the questions behind them

None, and here is why: records are read at decision time and lint time; nothing here runs unattended. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content when one exists.

## 9. Boundaries, per capability

None new, and here is why: the diff is markdown and one ledger row, opening no input path, subprocess or secret; [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) still lints every round.

## 10. The budget, or its absence

None, and here is why: no execution path changes. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

A lint or suite failure stops the step and is worked under [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md); the standing guards are the hypomnema pointer lint over the records and the evolution suite over the row.

## 12. Decisions and their homes

Two decisions land in the records themselves: ADR-005 (the vendoring boundary) and ADR-006 (ledgers are not SemVer). The decision to normalise the four existing records rather than stand three shapes is about this governed skill's convention, so its record is the evolution row this run cuts, pointing at this committed study for the rejected alternatives. The frontier judgement at close is also the row's to hold.
