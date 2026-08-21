# Study: Hold alert runbooks to the three-line shape

Assuming, unless corrected:

1. A runbook is in scope for the new rule only when it is a Markdown file below a directory named `runbooks`.
2. The three required answers are represented by the headings `## What fired`, `## First check`, and `## Who to wake`; prose under each heading must be non-empty.
3. The existing `<!-- hypomnema: allow <why> -->` pragma may suppress a deliberate exception from the file's first line or the missing heading's line.
4. The new code is H007; H000 to H006 keep their numbers and firing conditions.
5. Python 3.11 and stdlib unittest remain the implementation boundary.
6. The run starts from `main` at `87e213c19e64687406d7ba7601e093929bb3d813`.

## 1. Problem statement

Hypomnema says that an alert runbook must answer what fired, the first thing to look at and who to wake. H003 proves only that an alert's named file exists. A file below `docs/runbooks/` can therefore be empty and pass. This run implements issue 318 and the live held job `runbook-shape-check`: the lint must report H007 for each missing or empty answer, accept a complete runbook, honour a reasoned exception, preserve H000 to H006 and advance the Hypomnema ledger exactly once. Working means the fixture command fails with the named faults, the tree-wide lint is clean, and both repository suites pass.

## 2. Prior art

- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` already recognises decision-record paths, walks Markdown outside fences, applies the reasoned pragma and emits stable codes H000 to H006. The runbook shape belongs in this bounded walk.
- H003 matches an alert's `runbook:` annotation and checks that the target exists. Issue 319 owns requiring that annotation on alert-rule surfaces; this run does not duplicate that responsibility.
- The last two merged pull requests that changed Hypomnema were [skills#343](https://github.com/wildcat-finance/skills/pull/343), which added H004/H005 and guarded the heading-pragma trap, and [skills#346](https://github.com/wildcat-finance/skills/pull/346), which added H006 and recorded this runbook-shape gap as the successor. Their pull-request bodies and the corresponding `audit/AUDIT.md` rounds were read. Neither carries an open defect for this rule; the earlier design-bridge mechanical check remains a candidate successor rather than part of this run.
- Existing runbook prose appears in studies, controller docs and examples, but there is no first-party `docs/runbooks/` directory on the starting ref. Fixtures therefore establish positive and negative specimens without forcing unrelated documents into the alert-runbook convention.
- The versioning contract requires a frontier run to cold-read and reconcile all mutable first-party marketplace prose. The implementation step reviews the root and plugin marketplace descriptions, first-party runtime contracts, READMEs and canonical skill prose; only surfaces whose Hypomnema lint description becomes stale are changed.

## 3. Constraints and non-goals

- Starting ref: `main` at `87e213c19e64687406d7ba7601e093929bb3d813`.
- H000 to H006 are stable interfaces. H003 remains existence-only and issue 319 remains Ephoros-owned.
- The evolution row increments evolution, retains generation and epoch, recomputes the frontier digest and records one evidenced successor or a mature close.
- No Solidity changes, dependency additions, subprocesses, sockets or generated-file edits.
- Non-goal: prescribe operational content beyond the three answers.
- Non-goal: parse alert-rule YAML or require annotations; issue 319 owns that endpoint.
- Non-goal: infer headings from arbitrary prose. A fixed shape keeps the check reviewable and gives Ephoros one format to hand off to.
- Always: run the target unit tests, root suite, Hexaemeron suite, Promise Machine check and all repository prose/tree lints before the frontier row is receipted.
- Ask first: any dependency, CI, public interface or trust-boundary change.
- Never: edit vendored skills, weaken an existing code, skip a failing specimen or claim an unrun command.

## 4. Design options

1. **Three fixed headings with non-empty bodies, checked inside the existing Markdown pass.** Chosen. It is the lowest-comprehension construction, produces one finding per absent answer and gives the Ephoros handoff an explicit shape. It trades away accepting semantically equivalent free-form prose.
2. **Keyword searches anywhere in the document.** Rejected because examples and incidental mentions would satisfy the rule while the operator-facing answers remained absent.
3. **A frontmatter schema.** Rejected because it introduces a second document convention and parser for three short answers.
4. **A separate runbook linter.** Rejected because the audit loop already relies on one Hypomnema invocation and H003 owns the adjoining pointer check.

## 5. Risk register seed

```risk-register
path-scope | the matcher deciding which Markdown files are alert runbooks | only files below a runbooks directory earn H007 and an unrelated runbook mention stays unclassified
heading-content | the three headings and their bodies outside fenced examples | each missing or empty answer is caught while a complete fixture passes
pragma-scope | deliberate exceptions against a missing answer | only a reasoned pragma on the file first line or relevant heading suppresses the finding
handoff-ownership | H007 beside H003 and issue 319 | H003 remains existence-only and no alert-rule annotation logic enters Hypomnema
interface-drift | H000 to H006 beside H007 | every existing test passes unchanged and the docs name the new code without renumbering the old ones
ledger-arithmetic | the new evolution row and successor judgement | the evolution and Promise Machine checks pass over exactly one new row and the recomputed binding digest
prose-reconciliation | mutable first-party marketplace prose against the changed contract | every mutable prose surface is reviewed and only descriptions made stale by H007 are changed
```

The audit loop should look hardest at heading-content and pragma-scope: a shape check that accepts an empty section or suppresses from an unrelated line recreates the existence-only fault under another name.

## 6. Glossary seeds

- Alert runbook: a Markdown file below a directory named `runbooks`.
- Three-line shape: the `What fired`, `First check` and `Who to wake` answers, each present and non-empty.
- H007: a required runbook answer is absent or empty.

## 7. Sources

- `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `scripts/hypomnema.py`, `EVOLUTION.md`
- `plugins/hexaemeron/skills/VERSIONING.md`
- `plugins/hexaemeron/tests/test_hypomnema_checker.py` and `plugins/hexaemeron/tests/fixtures/hypomnema/`
- `audit/AUDIT.md`, the Hypomnema ADR-shape and source-comment rounds
- [skills#318](https://github.com/wildcat-finance/skills/issues/318), [skills#343](https://github.com/wildcat-finance/skills/pull/343), [skills#346](https://github.com/wildcat-finance/skills/pull/346)

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is a lint invoked from a terminal and nothing runs unattended. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns the alert-rule endpoint built in issue 319.

## 9. Boundaries, per capability

The lint continues to read only caller-named files and trees. It adds a path classification and bounded Markdown section scan, with no subprocess, socket, credential or write path. Unreadable input already fails as H000. [Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns those controls and its lint runs each audit round.

## 10. The budget, or its absence

None, and here is why: the check reuses the existing single file read and no caller states a latency target. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns a measurement contract when a performance claim exists.

## 11. The fail-closed posture

A fixture, suite, lint, Promise Machine or evolution failure stops the step and is worked under [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md). H007 ships with one guard per missing answer, empty-answer guards, a clean specimen and suppression boundaries.

## 12. Decisions and their homes

The fixed heading shape, H007 interface and successor judgement are decisions about a governed skill. They live in the new Hypomnema `EVOLUTION.md` row, while this committed study preserves the rejected alternatives. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) keeps that decision in the skill ledger rather than a second ADR. The evidenced successor candidate is the still-manual design bridge recorded by skills#314: mechanically prove that a shipped study's chosen design points to its standing record without copying the decision into two homes.
