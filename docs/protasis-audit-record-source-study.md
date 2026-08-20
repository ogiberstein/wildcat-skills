# Study: Protasis names the audit record as a study source

Assuming, unless corrected:

1. The change is to prose contracts only: `plugins/hexaemeron/skills/protasis/SKILL.md` and its ledger. No script changes.
2. The twelve study items stay twelve. The held `study-schema-check` job's acceptance surface must not move, so the audit-record source widens item 2's content rather than adding a thirteenth item.
3. Python 3.11 with stdlib unittest, matching every suite in this repository.
4. The run starts from `main` at `b26181b438528a97c99d20600aaeb937f68d0b09`.

## 1. Problem statement

A Fiat study that has not read the audit records of the skills it covers reconstructs reasoning that is already written down, and where it cannot find the real reason for a decision it supplies a plausible one. That plausible reason then governs the build: a rejected option gets rejected for the wrong cause, an accepted risk gets quietly reopened, and the round that already judged the question reads afterwards as though it never happened. Wave 1 of the wishlist surfaced a live case: the execution order predicted that parked-lane records would live in the Kronos scoreboard, and the round that decided otherwise, with its reason, sits in `audit/AUDIT.md` where no later study is told to look.

This run makes the audit records of every in-scope skill a named source in protasis item 2 (prior art), read before design options (item 4) are drawn. Done means: `plugins/hexaemeron/skills/protasis/SKILL.md` names the audit record in item 2, the pre-receipt checklist asks whether it was read, the protasis ledger carries one generation row (`protasis-v2.2.0` to `protasis-v2.3.0`) holding the frontier revision and digest byte for byte, and the frontmatter version matches the ledger. Proved by `python3 -m unittest discover -s tests`, `python3 plugins/hexaemeron/tests/run_tests.py`, and a read of item 2 showing the named source.

## 2. Prior art

- `plugins/hexaemeron/skills/protasis/SKILL.md` item 2 already reaches the last two merged pull requests that changed the target (added in `protasis-v2.2.0`). The audit record is the same shape of failure one layer deeper: the PR body holds what a run would not finish, the audit file holds why a round decided what it decided.
- `audit/AUDIT.md` is the accumulated audit record for this repository: per-step, per-round tables with findings, fixes, and a `Leads not pursued` line. Fiat's audit loop names it through `config audit.log_path`, defaulting to `audit/AUDIT.md` (`plugins/hexaemeron/skills/fiat/references/audit-loop.md`).
- The last two merged pull requests that changed the target: [skills#293](https://github.com/wildcat-finance/skills/pull/293) (Promise Machine; carried forward: Codex picker capture and Claude Code re-authentication, neither touching protasis; protasis's study checker named as still open, which is the held frontier job this run must not move) and [skills#276](https://github.com/wildcat-finance/skills/pull/276) (`protasis-v2.2.0`; carried forward: installed plugin caches lag until refreshed, horos CI and README items owned elsewhere). Each item is either out of this run's scope by name or restated here as a constraint.
- The wishlist grab-bag entry protasis-4 specifies the change and its verification caution: cite sources, never restate discipline cores in a protasis-owned manifest, because content rules live in exactly one skill and a restated manifest goes stale continuously.

## 3. Constraints and non-goals

- Starting ref: `main` at `b26181b438528a97c99d20600aaeb937f68d0b09`.
- The held `Next Fiat job` (`study-schema-check`) must keep its target and acceptance condition: a generation row retains the frontier revision and digest byte for byte, enforced by `test_history_axes_enforce_independent_counters_and_frontier_hold` and by `hexctl done integrate`.
- Non-goal: the study schema check itself. That is the held frontier job, delivered by the next run.
- Non-goal: changing `audit/AUDIT.md`'s format or location, which belong to Fiat's audit loop.
- Non-goal: a manifest of audit sources owned by protasis.

## 4. Design options

1. **Widen item 2's prose to name the audit record as a source, plus one checklist line.** Costs a paragraph; keeps twelve items; the schema check that ships next run covers item 2 unchanged in shape. Chosen: it is the option cheapest to comprehend that meets the problem statement. It trades away machine enforcement, which the next run's check partially supplies, and accepts that a study can still claim to have read without reading.
2. **Add a thirteenth study item for audit prior art.** Rejected: moves the twelve-item acceptance surface of the held `study-schema-check` job, which a generation change must not do.
3. **A protasis-owned manifest listing each skill's audit records.** Rejected on the recorded verification caution: content rules live in exactly one skill, and with all six phase-skill ledgers actively evolving a restated manifest goes stale continuously.

## 5. Risk register seed

The audit loop should look hardest at prose drift: a wording of item 2 that contradicts the audit loop's own definition of the audit file (path, per-round shape), a checklist line that asks for something item 2 does not say, and a ledger row that breaks the generation arithmetic or digest hold. Untrusted input, subprocesses, secrets and partial writes do not arise; the diff is markdown and one ledger row.

## 6. Glossary seeds

- Audit record: the per-step, per-round findings file Fiat's audit loop appends to, at `config audit.log_path`, default `audit/AUDIT.md`.
- In-scope skill: a skill the study's topic covers or changes, including siblings it cites.
- Generation row: a ledger entry incrementing the second version number while holding the frontier revision and digest.

## 7. Sources

- `plugins/hexaemeron/skills/protasis/SKILL.md` and `EVOLUTION.md`
- `plugins/hexaemeron/skills/VERSIONING.md`
- `plugins/hexaemeron/skills/fiat/references/audit-loop.md`
- `audit/AUDIT.md`
- [skills#293](https://github.com/wildcat-finance/skills/pull/293), [skills#276](https://github.com/wildcat-finance/skills/pull/276)
- Wishlist grab-bag, batch 1 and the protasis entry (artifact `12e0da9f`, read 2026-08-20)

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is contract prose read by agents at study time and a ledger row. Nothing here runs unattended, so there is no three-in-the-morning question. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content when one exists.

## 9. Boundaries, per capability

None new, and here is why: the change opens no input path, spawns nothing, and touches no secret. The one boundary in play is the existing versioning contract around the ledger, and [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) has no off-chain surface to harden in a markdown diff. The controls that hold are the evolution tests and `hexctl`'s integrate gate.

## 10. The budget, or its absence

None, and here is why: no execution path changes, so there is nothing to measure. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

A suite failure or lint failure stops the step; the fix follows [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md): reproduce, reduce, fix the mechanism, and guard it. The guard convention here is the existing evolution tests, which already refuse a malformed row; no new guard tests are expected for a prose change unless a round surfaces a failure.

## 12. Decisions and their homes

One decision is expensive to reverse: widening item 2 rather than adding a thirteenth item, because the next run ships a schema check against exactly twelve items. Its record is the protasis ledger row this run writes (`EVOLUTION.md` is the ledger for a decision about a governed skill, per [hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md)), with this study committed under `docs/` as the reasoning behind it.
