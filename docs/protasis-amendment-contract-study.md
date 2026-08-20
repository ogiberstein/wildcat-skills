# Study: The mid-run spec amendment contract

Assuming, unless corrected:

1. The change is contract prose in the "The spec stays alive" section of `plugins/hexaemeron/skills/protasis/SKILL.md` plus one generation ledger row; no script changes and no change to the held job's text.
2. An amendment is a block appended to the study rather than an edit that overwrites history, so a reader can still see what the run believed before the change.
3. The run starts from `main` at `54431ba4e7547968a099d1031415ffe292f6833d`.

## 1. Problem statement

"The spec stays alive" says change the study first when a decision changes, and stops there. Nothing states what an amendment must contain, so an in-flight change can silently invalidate downstream steps: step 4's entry assumes a layout step 2 just abandoned, and nobody re-confirmed it. This run specifies a dated delta block -- what changed, why, which runbook steps it touches, and re-confirmation that each unbuilt step's entry and exit still hold -- with a refusal to proceed past a step whose entry the amendment broke, and with the decision that forced the change recorded where hypomnema's rules put it. Done means the section states the block and the refusal, the ledger takes one generation row (`protasis-v3.4.0` to `protasis-v3.5.0`) holding revision and digest byte for byte, and both suites pass: `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

- `plugins/hexaemeron/skills/protasis/SKILL.md`, "The spec stays alive": two sentences, no amendment shape, no refusal. The step schema's Entry and Exit fields are exactly what an unexamined amendment breaks.
- [hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns where the forcing decision is recorded; this contract cites it rather than restating where records live.
- The audit records of the in-scope skills were read before design options were drawn. The protasis rounds in `audit/AUDIT.md` record one live amendment-shaped event: the study-schema-check run rewrote its held-job wording mid-step when the shipped-prose gate refused it, recomputed the digest, and logged the fix inside the round -- a change that touched no other step's entry, which is exactly the confirmation an amendment block makes explicit instead of lucky.
- The last two merged pull requests that changed the target: [skills#304](https://github.com/wildcat-finance/skills/pull/304), whose carried-forward items stay open where they are (the held block check, Fiat-side per-concern logging, the two environment-bound tests restated in item 3, host plugin caches); and [skills#301](https://github.com/wildcat-finance/skills/pull/301), whose filler-none S002 boundary stays accepted and whose Fiat `--study` binding stays Fiat-ledger work.
- The wishlist grab-bag entry protasis-3 names the block's required content and the refusal; this study follows it.

## 3. Constraints and non-goals

- Starting ref: `main` at `54431ba4e7547968a099d1031415ffe292f6833d`. The two `test_elenchus_checker` cases needing `forge` and node v26 stay failing in this container, identically on base.
- The generation row must retain frontier revision `risk-register-block-check` and its digest byte for byte, and the held job's wording must not move.
- Non-goal: a mechanical check over amendment blocks; the study contract's checkable surface is the held frontier's territory, and this block is rare enough that a check would be built on no corpus.
- Non-goal: changing Fiat's controller or receipts; the refusal is a contract rule the run obeys, not a new gate in `hexctl`.
- Non-goal: restating hypomnema's placement rules; the section cites them.

## 4. Design options

1. **A dated `### Amendment -- <date>` block appended to the study, four fixed fields, plus a stated refusal.** What changed, why, steps touched, and still-holding re-confirmation per unbuilt step; the run does not proceed past a step whose entry the amendment broke until the runbook is re-derived or the step re-specified. Chosen: append-only keeps the pre-change belief readable, four fields are the minimum that make the invalidation visible, and the refusal reuses the contract's existing blocked-phase language. It trades away brevity in a heavily amended study, which is itself a signal the topic needed decomposing.
2. **Edit the study in place and rely on git history.** Rejected: the diff lives outside the document, so a reader holding only the study cannot see what changed, and the runbook's steps reference a study whose page silently moved under them.
3. **A separate amendments file beside the study.** Rejected: two documents drift, and the study is the one artefact the contract already commits and re-reads.

## 5. Risk register seed

```risk-register
refusal-drift | the new refusal against the contract's existing refuse-report shape | the round reads both and confirms the refusal names what is missing, where it was looked for, and the action that clears it
field-mismatch | the four block fields against the wish and this study | the round confirms the section asks for exactly what item 1 states
ledger-arithmetic | the generation row against the versioning contract | the round relies on the evolution suite passing over the new row
```

The audit loop should look hardest at refusal-drift: the contract already has a three-part refusal report shape, and a second shape beside it would be the two-conventions failure hypomnema warns about.

## 6. Glossary seeds

- Amendment block: a dated `### Amendment -- <date>` section appended to a committed study, carrying what changed, why, the steps touched, and the still-holding confirmation.
- Unbuilt step: a runbook step whose implement phase has not been receipted when the amendment lands.
- Forcing decision: the decision whose change made the amendment necessary, recorded under hypomnema's rules.

## 7. Sources

- `plugins/hexaemeron/skills/protasis/SKILL.md` and `EVOLUTION.md`
- `plugins/hexaemeron/skills/hypomnema/SKILL.md`
- `audit/AUDIT.md`, "Protasis study schema check" step 3 round 1
- [skills#304](https://github.com/wildcat-finance/skills/pull/304), [skills#301](https://github.com/wildcat-finance/skills/pull/301)
- Wishlist grab-bag, protasis entry 3 (artifact `12e0da9f`, read 2026-08-20)

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is contract prose read at amendment time; nothing runs unattended. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content when one exists.

## 9. Boundaries, per capability

None new, and here is why: a markdown diff opens no input path, subprocess or secret; [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) has nothing to harden here and its lint still runs each round.

## 10. The budget, or its absence

None, and here is why: no execution path changes. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

A suite or lint failure stops the step and is worked under [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md); the standing guards are the evolution suite over the row and the shipped-prose gate over the contract text.

## 12. Decisions and their homes

The append-only choice is expensive to reverse: once studies carry amendment blocks, an in-place-edit convention beside them is the second scheme hypomnema refuses. The record is the protasis ledger row this run cuts, with this study committed under `docs/` carrying the rejected alternatives.
