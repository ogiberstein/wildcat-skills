# Study: Lint the shape of the decision records

Assuming, unless corrected:

1. The lint extends `hypomnema.py` with two new codes, H004 and H005; H000 to H003 stay byte-compatible interfaces.
2. A decision record is a markdown file named `ADR-<number>...` inside a directory named `decisions`, which matches the six records the convention holds today.
3. The dated status shape is the one `hypomnema-v1.1.0` normalised the records to: a status word, a comma, an ISO date, as the first line under `## Status`.
4. Python 3.11 and stdlib unittest, matching every other check in this plugin.
5. The run starts from `main` at `8d5079b43276d6e4f26df58e9e32411ae2898c43`.

## 1. Problem statement

Six decision records exist under `docs/decisions/` and the lint resolves their pointers, but it reads no structure: the first four stated their status in three different shapes within a day of being written, and ADR-002 and ADR-004 still carry no alternatives section, which only a reader notices. This run ships the shape rule, which is the held frontier job (`adr-shape-check`, [skills#316](https://github.com/wildcat-finance/skills/issues/316)): each record carries the template's dated status and its five sections, with the existing pragma for deliberate exceptions. Done means the lint catches each omission in fixture records, passes over the tree's records once the two without an alternatives section are filled from their authorship trail, the ledger advances `hypomnema-v1.2.0` to `hypomnema-v2.2.0` with one evidenced successor job, and both suites pass: `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` owns the walk, the fence-aware line scan, the allow pragma and codes H000 to H003; the shape rule belongs in that walk. The SKILL's "Write the record when reversing gets expensive" section states the template: Status, Context, Decision, Alternatives, Consequences, with a dated status line.
- The last two merged pull requests that changed the target: [skills#314](https://github.com/wildcat-finance/skills/pull/314), which carried forward that a mechanical check of its design bridge needs this job's record parser first (still open here; the successor judgement weighs it) and the ADR-002 and ADR-004 backfill (done this run); and [skills#311](https://github.com/wildcat-finance/skills/pull/311), which normalised the six records to one dated status shape, named the drift as this frontier's evidence, and parked the backfill inside this job's acceptance so the restructuring happens under a check that holds it.
- The audit records of the in-scope skills were read before design options were drawn. "Hypomnema first records" step 2 round 1 holds the accepted lead this run consumes: the two records' rejected options live as prose in sections another run authored, and restructuring risked rewording that reasoning without a check. Step 3 round 1 holds the trap this run will meet again: a SKILL.md edit moved a Promise Machine binding surface and the coverage gate refused it (PM071); the remedy is the checker's own inventory update after the field map is reviewed as unchanged.
- The rejected options themselves are on the page in the Promise Machine study, `docs/promise-machine/study.md`: Option D and the 20-entrypoint status quo for ADR-002, and the release non-goals ("advancing a held frontier merely because Fiat delivers this repository change", "standardising every output into one receipt schema") for ADR-004. The backfill lifts from there rather than inventing.

## 3. Constraints and non-goals

- Starting ref: `main` at `8d5079b43276d6e4f26df58e9e32411ae2898c43`. The two `test_elenchus_checker` cases needing a `forge` binary and node v26 stay failing in this container, identically on base.
- Codes H000 to H003 keep their numbers and firing conditions; the six records keep their content -- the backfill adds two alternatives sections lifted from the authorship trail and moves nothing else.
- The evolution row must increment the evolution counter, retain generation and epoch, replace the held job with one evidenced successor, and carry the digest recomputed over the new frontier line.
- Non-goal: enforcing section order or heading depth beyond presence; the frontier names the dated status and the five sections.
- Non-goal: a mechanical check of the design bridge (that a shipped study's choice reached a record), which skills#314 left to a later frontier judgement and this run leaves there.
- Non-goal: reading files that are not markdown; the walk's reach is its own held question for the successor judgement.

## 4. Design options

1. **A record-shape pass inside `check()`, gated on the record's path.** A file named `ADR-<number>...` under a `decisions` directory earns H004 for each of the five sections it misses and H005 for a status whose first line is not the dated shape. Chosen: the rule joins the walk that already owns fences and pragmas, one command still lints a tree, and the pragma covers a deliberate exception the way it covers a pointer. It trades away catching records filed outside a decisions directory, which the conventions paragraph already refuses.
2. **A separate records lint.** Rejected: a second invocation to forget, and the audit loop's non-Solidity round cites one hypomnema command.
3. **A repository test instead of a lint rule.** Rejected: a test here protects only this tree, while the lint travels with the plugin to every repository the convention reaches.

## 5. Risk register seed

```risk-register
backfill-fidelity | the two filled alternatives sections against the promise-machine study | the round diffs each new section against the cited options and non-goals and confirms no option or reason was invented
shape-source | the H005 dated-status rule against the six normalised records | the round confirms the rule accepts exactly the shape v1.1.0 normalised to and every record passes
false-positive | the record matcher against markdown that merely mentions records | fixtures prove a non-record file and a section heading quoted inside a fence earn no shape verdict
interface-drift | codes H000 to H003 against the two new codes | the existing tests pass unchanged and the new codes join the docstring and the SKILL.md subset
ledger-arithmetic | the evolution row against the versioning contract | the round relies on the evolution suite passing over the new row
```

The audit loop should look hardest at backfill-fidelity: the sections being filled record another run's reasoning, and a reworded rejection is exactly the corruption the first-records round refused to risk without a check.

## 6. Glossary seeds

- Decision record: a markdown file named `ADR-<number>...` under a `decisions` directory, in the template the SKILL states.
- Dated status: the first line under `## Status`, a status word, a comma and an ISO date, as v1.1.0 normalised.
- Shape codes: H004 (a record missing one of the five sections), H005 (a status that is not dated).

## 7. Sources

- `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `scripts/hypomnema.py`, `EVOLUTION.md`
- `plugins/hexaemeron/skills/VERSIONING.md`
- `plugins/hexaemeron/tests/test_hypomnema_checker.py`
- `docs/decisions/ADR-001` through `ADR-006`, `docs/promise-machine/study.md`
- `audit/AUDIT.md`, "Hypomnema first records" and "Hypomnema design bridge" rounds
- [skills#316](https://github.com/wildcat-finance/skills/issues/316), [skills#314](https://github.com/wildcat-finance/skills/pull/314), [skills#311](https://github.com/wildcat-finance/skills/pull/311)

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is a lint invoked from a terminal; nothing runs unattended. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content when one exists.

## 9. Boundaries, per capability

The lint's reach stays the caller's argument list and the tree it walks; the shape pass opens no subprocess, socket or new input path beyond the markdown read that already exists. [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary rules; its lint runs each round.

## 10. The budget, or its absence

None, and here is why: the shape pass reads section headings during the walk the lint already makes, and no caller states a latency requirement. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

A suite, lint or Promise Machine gate failure stops the step and is worked under [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md); each new code ships with the test that would catch its regression, and the standing guards are the evolution suite over the row and the shipped-prose gate over the contract text.

## 12. Decisions and their homes

Two decisions are expensive to reverse: the code numbering H004 and H005 becomes a cited interface, and the successor frontier replaces the held job. Both are recorded in the hypomnema ledger row this run cuts ([hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md): a decision about a governed skill lives in its `EVOLUTION.md`), with this study committed under `docs/` carrying the rejected alternatives. The successor candidate the evidence supports is the walk's reach: the SKILL tells why-comments to point at the decision record, `hypomnema.py` returns nothing for any file that is not markdown, and [skills#317](https://github.com/wildcat-finance/skills/issues/317) verified the gap standing -- an ADR cited from a Python or Solidity comment can dangle forever, which is the record-pointing-at-something-absent failure the lint exists to catch.
