# Study: A structured risk-register block the warden can enumerate

Assuming, unless corrected:

1. The change is contract prose in `plugins/hexaemeron/skills/protasis/SKILL.md` item 5 plus one generation ledger row; no script changes and no change to the held job's text.
2. The block is line-based rather than YAML or JSON, so a future check needs no parser dependency and a person can write it without one.
3. The run starts from `main` at `75fc3d3707bbccf107aa43ad3aa008b77f7850a0`.

## 1. Problem statement

Study item 5 is freeform prose, yet warden's brief hands it "the risk register seed from the study" and Fiat's non-Solidity round must review the diff for the register's concerns the lints cannot see. Freeform prose cannot be enumerated, so the look is a judgement call nobody can verify afterwards: a round can honestly say it reviewed the register while a concern in the third sentence went unread. This run defines a fenced minimal block for item 5 -- concern id, boundary, what the audit loop checks -- so each round can log per-concern reviewed or not-applicable. Done means item 5 states the block's form, this run's own committed study carries one, the ledger takes one generation row (`protasis-v3.3.0` to `protasis-v3.4.0`) holding revision and digest byte for byte, and both suites pass: `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

- `plugins/hexaemeron/agents/warden.md` receives "the risk register seed from the study" verbatim, and `plugins/hexaemeron/skills/fiat/references/audit-loop.md` requires each non-Solidity round to review the diff "for the risk register's concerns the lints cannot see" and log the result. Both consume the seed; neither can enumerate it today.
- The audit records of the in-scope skills were read before design options were drawn. This run's own rounds under "Protasis study schema check" in `audit/AUDIT.md` log register review as prose ("the round worked the risk register's four unearned-verdict concerns"), which is exactly the unverifiable look the block replaces. No accepted lead in the protasis or fiat records bears on the block's form.
- The last two merged pull requests that changed the target: [skills#301](https://github.com/wildcat-finance/skills/pull/301), whose carried-forward items are restated here (the filler-none S002 boundary stays accepted and out of scope; binding `--study` into Fiat's phase notes stays Fiat-ledger work; the two environment-bound tests are restated in item 3; plugin cache staleness stays host-owned) and whose successor frontier this run's block feeds; and [skills#297](https://github.com/wildcat-finance/skills/pull/297), which carried the same environment and cache items forward.
- The held job (`risk-register-block-check`) says a later frontier run ships the check over the shape this run defines. Its text, target and acceptance do not move here; the versioning contract and the evolution suite enforce the hold.

## 3. Constraints and non-goals

- Starting ref: `main` at `75fc3d3707bbccf107aa43ad3aa008b77f7850a0`. The two `test_elenchus_checker` cases needing `forge` and node v26 stay failing in this container, identically on base.
- The generation row must retain frontier revision `risk-register-block-check` and its digest byte for byte, and must not touch the held job's wording.
- Non-goal: the mechanical check over the block, which is the held frontier job.
- Non-goal: changing warden's brief or Fiat's audit-loop reference, which live on Fiat's side; the block rides through the existing "risk register seed from the study" handoff unchanged.
- Non-goal: a taxonomy of concern categories; the block carries what its author names.

## 4. Design options

1. **A fenced block with the info string `risk-register`, one concern per line, three pipe-separated fields.** Kebab-case id, the boundary it sits at, what the audit loop checks. Chosen: a person writes it in one line per concern, a round cites concerns by id, and a future check splits on pipes with no parser dependency. It trades away nesting and multi-line detail, which the surrounding item 5 prose still carries.
2. **A YAML block.** Rejected: invites a parser dependency the held job would then inherit, and multi-line YAML answers are harder to cite by id in a round log.
3. **A markdown table.** Rejected: table syntax is what the imprimatur and evolution tooling already parse for other meanings, and a table invites formatting churn (alignment, escapes) that a pipe-line block avoids inside a fence.

## 5. Risk register seed

```risk-register
shape-drift | item 5's stated form against the held job's wording | the round reads both and confirms the job's target and acceptance did not move
example-mismatch | the example block in item 5 against the stated form | the round checks the example parses as three pipe-separated fields per line
ledger-arithmetic | the generation row against the versioning contract | the round relies on the evolution suite passing over the new row
```

The audit loop should look hardest at the first: the held job's acceptance names "that shape", so a block form stated ambiguously here makes the next frontier run guess.

## 6. Glossary seeds

- Risk-register block: the fenced block in study item 5, info string `risk-register`, one concern per line as `id | boundary | what the audit loop checks`.
- Concern id: the kebab-case first field, stable within a study, cited by audit rounds.
- Warden: the audit-round agent brief at `plugins/hexaemeron/agents/warden.md`.

## 7. Sources

- `plugins/hexaemeron/skills/protasis/SKILL.md` and `EVOLUTION.md`
- `plugins/hexaemeron/agents/warden.md`, `plugins/hexaemeron/skills/fiat/references/audit-loop.md`
- `audit/AUDIT.md`, "Protasis study schema check" rounds
- [skills#301](https://github.com/wildcat-finance/skills/pull/301), [skills#297](https://github.com/wildcat-finance/skills/pull/297)
- Wishlist grab-bag, protasis entry 2 (artifact `12e0da9f`, read 2026-08-20)

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is contract prose read at study time; nothing runs unattended. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content when one exists.

## 9. Boundaries, per capability

None new, and here is why: a markdown diff opens no input path, subprocess or secret. [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) has nothing to harden here; its lint still runs each round.

## 10. The budget, or its absence

None, and here is why: no execution path changes. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

A suite or lint failure stops the step and is worked under [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md); the standing guards are the evolution suite over the row and the shipped-prose gate over the contract text.

## 12. Decisions and their homes

The block's field order and separator are expensive to reverse once the held frontier job ships a check that parses them. The decision is recorded in the protasis ledger row this run cuts ([hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md): a decision about a governed skill lives in its `EVOLUTION.md`), with this study committed under `docs/` carrying the rejected alternatives.
