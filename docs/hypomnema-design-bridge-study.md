# Study: Each study's chosen design becomes a standing record

Assuming, unless corrected:

1. The change is contract prose in `plugins/hexaemeron/skills/hypomnema/SKILL.md` plus one generation ledger row; no script changes and no change to the held job's text.
2. Pointing at a record satisfies the rule: a governed skill's design decision already belongs in its `EVOLUTION.md` row, so the bridge demands a durable home, not a duplicate ADR.
3. The run starts from `main` at `f004754dd804dd45f785fa75a440b69b29326ac6`.

## 1. Problem statement

The frontier job just closed backfilled records for choices already made; this is the forward-looking step beyond it. Protasis forces every study to name a chosen design with its trade, which is exactly the context-alternatives-consequences material the record template calls the part that pays, yet nothing carries it out of `docs/*-study.md` into a durable record once the delivery ships. A study is a run artefact: the next reader finds the code and the ledgers, not the option that lost. This run defines the prose-phase rule: before the step that ships a study is receipted, the study's chosen design with its rejected alternatives becomes a standing record, or points at one -- an ADR under `docs/decisions/` for a cross-cutting choice, the skill's `EVOLUTION.md` row for a governed skill's choice. Done means the contract states the rule and its checklist line, the ledger takes one generation row (`hypomnema-v1.1.0` to `hypomnema-v1.2.0`) holding revision and digest byte for byte, and both suites pass: `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

- `plugins/hexaemeron/skills/hypomnema/SKILL.md` already owns the prose-phase record decisions ("Write the record when reversing gets expensive") and the pre-receipt checklist this rule slots into. Protasis item 4 (design options, the pick and its trade) and item 12 (decisions and their homes) supply the material; the bridge closes the gap between naming a home and the record existing there.
- The audit records of the in-scope skills were read before design options were drawn. This wave's own runs demonstrate the pointing arm live: every study's item 12 named the ledger row that would record the choice, and each row exists. None produced a cross-cutting ADR, which is the arm the rule makes explicit.
- The last two merged pull requests that changed the target: [skills#311](https://github.com/wildcat-finance/skills/pull/311), which carried forward the ADR-002 and ADR-004 alternatives backfill (owned by the held `adr-shape-check` job, untouched here), this exact bridge as the batch's next delivery (this run), the two environment-bound tests (restated in item 3), and host plugin caches (stays host-owned); and [skills#293](https://github.com/wildcat-finance/skills/pull/293), whose carried items are host-capture work outside this scope.
- The wishlist grab-bag entry hypomnema-1 names the rule and its boundary: "the queued frontier job backfills ADRs for choices already made; this is the forward-looking step beyond it."

## 3. Constraints and non-goals

- Starting ref: `main` at `f004754dd804dd45f785fa75a440b69b29326ac6`. The two `test_elenchus_checker` cases needing `forge` and node v26 stay failing in this container, identically on base.
- The generation row must retain frontier revision `adr-shape-check` and its digest byte for byte, and the held job's wording must not move.
- Non-goal: a mechanical check that the bridge happened; the held job owns the record shape check, and a bridge check would need it first.
- Non-goal: changing Fiat's prose-pass reference, which already sends the phase here for what gets recorded; the rule lands in the skill Fiat defers to.
- Non-goal: retroactive records for studies shipped before this rule; the frontier job that just closed handled the backfill's first two and holds the rest.

## 4. Design options

1. **State the bridge in "Write the record when reversing gets expensive" and add one pre-receipt checklist line.** Chosen: the section already defines when a decision earns a record, so the bridge is one paragraph naming the study as a source and the two homes, and the checklist makes the phase refuse without it. It trades away a dedicated section a reader could cite by heading, which the checklist line mitigates.
2. **A new top-level section for study bridging.** Rejected: it would restate when a record is earned, and a second statement of the same rule is the drift this skill warns about.
3. **Put the rule in protasis item 12.** Rejected: protasis decides what must be settled before code exists; carrying a decision into a durable record after it is made is this skill's charter, and the boundary between the two is stated in both contracts.

## 5. Risk register seed

```risk-register
double-record | the rule against the skill-decision convention | the round confirms the rule lets a governed skill's choice point at its ledger row rather than demanding a duplicate ADR
scope-creep | the rule's trigger against protasis's items 4 and 12 | the round confirms the rule fires on shipped studies in the prose phase and does not redefine what a study must contain
ledger-arithmetic | the generation row against the versioning contract | the round relies on the evolution suite passing over the new row
```

The audit loop should look hardest at double-record: a rule that forces an ADR for every study would put each governed skill's decision in two homes, which is the exact failure the conventions paragraph refuses.

## 6. Glossary seeds

- Bridge: the prose-phase act of turning a shipped study's chosen design and rejected alternatives into a standing record, or pointing at the record that holds them.
- Standing record: an ADR under `docs/decisions/` or a governed skill's `EVOLUTION.md` row; a run artefact is not one.

## 7. Sources

- `plugins/hexaemeron/skills/hypomnema/SKILL.md` and `EVOLUTION.md`
- `plugins/hexaemeron/skills/protasis/SKILL.md`, items 4 and 12
- `plugins/hexaemeron/skills/fiat/references/prose-pass.md`
- [skills#311](https://github.com/wildcat-finance/skills/pull/311), [skills#293](https://github.com/wildcat-finance/skills/pull/293)
- Wishlist grab-bag, hypomnema entry 1 (artifact `12e0da9f`, read 2026-08-20)

## 8. Signals, and the questions behind them

None, and here is why: the rule is read at prose-pass time; nothing runs unattended. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content when one exists.

## 9. Boundaries, per capability

None new, and here is why: a markdown diff opens no input path, subprocess or secret; [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) still lints every round.

## 10. The budget, or its absence

None, and here is why: no execution path changes. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

A lint or suite failure stops the step and is worked under [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md); the standing guards are the shipped-prose gate, the pointer lint, the Promise Machine coverage gate over the contract's bytes, and the evolution suite over the row.

## 12. Decisions and their homes

The point-or-write shape of the bridge is expensive to reverse: once prose passes receipt against it, demanding an ADR per study would re-home every governed skill's decisions. The record is the hypomnema ledger row this run cuts, pointing at this study, committed under `docs/`, for the rejected alternatives -- which is itself the bridge's pointing arm, applied one run early.
