# Study: Ship the protasis study schema check

Assuming, unless corrected:

1. The check extends `plugins/hexaemeron/skills/protasis/scripts/protasis.py` behind a `--study` flag rather than a second script, and the runbook mode's invocation and codes P000 to P004 stay untouched.
2. Study items are level-two headings of the form `## N. Title`, numbered 1 to 12, as every committed study under `docs/` writes them.
3. Python 3.11 and stdlib unittest, matching the existing checker and suite.
4. The run starts from `main` at `68ddc3c09496706886542665c21f7689add1e03c`.

## 1. Problem statement

The runbook step schema is executable and the study contract beside it is not: twelve mandated items, every one of them read by a person. A study missing an item, or answering items 8 through 12 with silence, passes today because nothing but a reviewer's attention refuses it, and silence cannot be told apart from not having looked. This run ships the held frontier job: a check over a study that fails when one of the twelve items is absent, and when an answer to items 8 through 12 is neither content nor a stated none carrying its reason. Done means the check catches each omission in fixture studies, passes over this run's own study, and both suites pass: `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

- `protasis.py` holds the runbook mode: fence-aware scanning, a byte cap, a step cap whose dropped count is reported, findings as stable codes, and an allow pragma. The study mode reuses that machinery rather than growing a sibling implementation.
- The audit records of the in-scope skill were read before design options were drawn. `audit/AUDIT.md` under the discipline-cores run (S3-R1-01 to S3-R4-01) shows the same fault four times: the check returning a verdict it had not earned rather than crashing -- a cap that discarded what it dropped, a last step that absorbed dropped fields, and two fence-tracking holes. Every one shapes this design: one shared scanner, spans that end at the next heading, and no silent truncation. The run-1 rounds ("Protasis audit-record source") add the two environment-bound suite failures this container cannot clear.
- The last two merged pull requests that changed the target: [skills#297](https://github.com/wildcat-finance/skills/pull/297), which carried forward the two environment-bound hexaemeron tests (restated in item 3), this held job (this run), and installed-plugin cache staleness (stays open, owned by hosts); and [skills#293](https://github.com/wildcat-finance/skills/pull/293), which named protasis's study checker as remaining open on its own frontier -- this run is that item.
- `plugins/hexaemeron/tests/test_protasis_checker.py` and `tests/fixtures/protasis/` hold the test conventions the new cases extend.

## 3. Constraints and non-goals

- Starting ref: `main` at `68ddc3c09496706886542665c21f7689add1e03c`. The container cannot run the two `test_elenchus_checker` cases needing `forge` and node v26; both fail identically on the base and are outside this run's diff.
- Codes P000 to P004 are a cited interface and do not move. Study findings get their own S-prefixed codes.
- Non-goal: judging answer quality. A wrong answer with words in it passes; presence is the parser's job and judgement is the reviewer's, exactly as the runbook mode states.
- Non-goal: checking emptiness of items 1 through 7. The held job's acceptance names items 8 through 12 for the answer check because "none, and here is why" is only a complete answer there; the first seven are read whole by the reviewer.
- Non-goal: binding the check into Fiat's directive table or receipts, which is Fiat's contract and Fiat's ledger.

## 4. Design options

1. **A `--study` flag on `protasis.py` with S-prefixed codes.** One file, one shared scanner, one test module; the fence and cap lessons apply to both modes by construction. Chosen: cheapest to comprehend and it cannot drift from the runbook mode's hygiene. Trades away a separate module's independence: a fault in the shared scanner now touches both modes, which the shared tests also cover.
2. **A second script `study.py` beside the checker.** Rejected: duplicates the scanner whose duplication caused three of the four recorded faults last time.
3. **Auto-detecting document kind from content.** Rejected: a runbook quoting a study heading, or the reverse, makes the kind a guess, and a wrong guess returns verdicts the check has not earned.

## 5. Risk register seed

The audit loop should look hardest at unearned verdicts, the fault every recorded protasis finding shares: an item heading quoted inside a fence being counted as an item, a duplicate item number letting one answered copy hide an empty one, a bare "None." passing because the none-rule matched too loosely, and an S001 miss when a heading deviates in whitespace or case. Partial reads are bounded by the existing byte cap; no subprocess, network or secret is involved.

## 6. Glossary seeds

- Study item: a level-two heading `## N. Title`, N from 1 to 12, and the lines under it up to the next level-two heading.
- Bare none: an answer that asserts none and stops, carrying no reason.
- S-code: a stable study finding code, S000 upward, an interface other tools may cite once shipped.

## 7. Sources

- `plugins/hexaemeron/skills/protasis/scripts/protasis.py` and `SKILL.md`
- `plugins/hexaemeron/skills/protasis/EVOLUTION.md` (held job text)
- `audit/AUDIT.md`, discipline-cores and audit-record-source sections
- `plugins/hexaemeron/tests/test_protasis_checker.py`
- [skills#297](https://github.com/wildcat-finance/skills/pull/297), [skills#293](https://github.com/wildcat-finance/skills/pull/293)

## 8. Signals, and the questions behind them

None, and here is why: the check is a lint invoked from a terminal, and the runbook mode's precedent holds -- it has no on-call question, per [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md), whose contract owns signal content when one exists.

## 9. Boundaries, per capability

The check's trust boundary is its argument list, unchanged from the runbook mode: paths are read as given, anything that is not a regular file is refused, reads are byte-capped, and no subprocess or socket is opened. [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary rules; its lint runs in every audit round.

## 10. The budget, or its absence

None, and here is why: the check reads one document per path with a 2 MiB cap, the same bound the runbook mode has run under without a performance complaint. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

An unreadable path is S000, never a silent skip; a document with no item is S003, never clean; anything dropped by a cap is reported, never discarded. A failure surfaced mid-step follows [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md): reproduce, reduce, fix the mechanism, and guard it with a test in `test_protasis_checker.py`.

## 12. Decisions and their homes

Two decisions are expensive to reverse. The S-code numbering becomes a cited interface the moment it ships, and the choice to extend `protasis.py` rather than grow a sibling script shapes every later checker change. Both are recorded in the protasis ledger's evolution row for this run ([hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md): a decision about a governed skill lives in its `EVOLUTION.md`), with this study committed under `docs/` carrying the reasoning. The row also holds the next frontier judgement this run must make at close.
