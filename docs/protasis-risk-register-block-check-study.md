# Study: Check the risk-register block the study contract fixes

Assuming, unless corrected:

1. The check extends `protasis.py --study` with three new codes, S005 to S007; S000 to S004 and P000 to P004 stay byte-compatible interfaces.
2. The one historical study a test holds clean, `docs/protasis-study-schema-check-study.md`, predates the block and takes the existing allow pragma on its item 5 heading rather than a rewritten answer.
3. Python 3.11 and stdlib unittest, matching every other check in this plugin.
4. The run starts from `main` at `3c061c2e15df085cf300220250b421bbd03f664c`.

## 1. Problem statement

`protasis-v3.4.0` fixed a structured shape for study item 5: a fenced block with info string `risk-register`, one concern per line as three pipe-separated fields -- a kebab-case id stable within the study, the boundary the concern sits at, and what the audit loop checks. The audit loop logs each id as reviewed or not applicable, so the shape is what makes the look enumerable. Nothing checks the shape: a study whose item 5 stayed prose, or whose block drops a field, passes `--study` today, and the round built on it is back to the judgement call the block exists to remove. This run ships the check, which is the held frontier job (`risk-register-block-check`, [skills#315](https://github.com/wildcat-finance/skills/issues/315)). Done means `--study` fails a study whose risk-register seed does not carry the shape, catches each missing or malformed field in fixture studies, passes over a study whose block carries every field, the ledger advances `protasis-v3.5.0` to `protasis-v4.5.0` with one evidenced successor job, and both suites pass: `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

- `plugins/hexaemeron/skills/protasis/scripts/protasis.py` already owns the study mode: the twelve-item spans, the shared fence-aware scanner, the byte cap, the allow pragma and codes S000 to S004. The check belongs in that walk; a second scanner beside it is the drift its own docstring warns about.
- The last two merged pull requests that changed the target: [skills#307](https://github.com/wildcat-finance/skills/pull/307), whose carried-forward items are restated here (no study carries an amendment block yet, and that stays open -- it seeds the successor job in item 12's decision; the two environment-bound tests are restated in item 3; plugin cache staleness stays host-owned); and [skills#304](https://github.com/wildcat-finance/skills/pull/304), which named this check as the held job this run now runs, and left Fiat's per-id round-logging phrasing as Fiat-ledger work, which it stays.
- The audit records of the in-scope skills were read before design options were drawn. The "Protasis risk-register block" and "Protasis amendment contract" rounds in `audit/AUDIT.md` are clean and log per concern id, which is the consumption side this check protects. The "Protasis study schema check" rounds carry the fault family every earlier protasis finding shares -- verdicts the scanner had not earned on fenced or duplicated content -- so the new codes reuse the shared scanner rather than growing a fourth copy. No accepted lead bears on the block's form.
- `docs/protasis-risk-register-block-study.md` settled the shape and rejected YAML and a markdown table; this run parses exactly what it fixed and reopens none of it.

## 3. Constraints and non-goals

- Starting ref: `main` at `3c061c2e15df085cf300220250b421bbd03f664c`. The two `test_elenchus_checker` cases needing a `forge` binary and node v26 stay failing in this container, identically on base.
- Codes S000 to S004 and P000 to P004 are cited interfaces: their numbers, firing conditions and the flagless runbook mode do not move.
- The evolution row must increment the evolution counter, retain generation and epoch, replace the held job with one evidenced successor, and carry the digest recomputed over the new frontier line; the evolution suite enforces the arithmetic.
- Non-goal: checking that an audit round actually cites the ids, which is round-log content on Fiat's side.
- Non-goal: judging whether a boundary or check field is any good; presence and shape are the parser's line, quality stays the reviewer's.
- Non-goal: an amendment-block check; this run only records it as the successor frontier if the evidence holds at the end.

## 4. Design options

1. **Extend `--study` with codes S005 to S007.** S005 for an item 5 with no risk-register block or none naming a concern, S006 for a line that does not split into exactly three pipe-separated fields, S007 for a malformed field -- an id that is not kebab-case, an id already used, or an empty boundary or check. Chosen: the check joins the walk that already owns item spans, fences and pragmas, one command still checks a study, and the codes join a numbering other tools already cite. It trades away independent versioning of the register rules, which the ledger's single frontier makes moot.
2. **A separate `--register` mode or script.** Rejected: a second invocation to forget, and the audit loop and Fiat's phase notes cite one study command.
3. **Parse the block in `hexctl` at receipt time.** Rejected: the content contract is protasis's, the controller would need its own copy of the fence scanner, and two scanners drift.

## 5. Risk register seed

```risk-register
false-clean | the block scanner against fenced and duplicated content elsewhere in a study | fixtures prove a block quoted inside another fence, and an item 5 duplicated by S004, earn no register verdict
interface-drift | codes S000 to S004 and P000 to P004 against the three new codes | the existing tests pass unchanged and the new codes join the docstring, the SKILL.md subset and the fixtures
fixture-coverage | the acceptance's each-missing-or-malformed-field claim against the fixture set | each fault class has a fixture line and a test that names its code
history-pragma | the one historical study a test holds clean against the new codes | the pragma on its item 5 states why it predates the shape, and no other historical study gains a silent edit
ledger-arithmetic | the evolution row against the versioning contract | the round relies on the evolution suite passing over the new row
```

The audit loop should look hardest at false-clean: every recorded protasis finding is a verdict the scanner had not earned, and the register scanner walks the same fences that produced them.

## 6. Glossary seeds

- Register line: one concern in the block, `id | boundary | what the audit loop checks`.
- Concern id: the kebab-case first field, stable within a study, cited by audit rounds.
- Register codes: S005 (no block naming a concern), S006 (wrong field count), S007 (malformed field).

## 7. Sources

- `plugins/hexaemeron/skills/protasis/SKILL.md`, `scripts/protasis.py`, `EVOLUTION.md`
- `plugins/hexaemeron/skills/VERSIONING.md`
- `plugins/hexaemeron/tests/test_protasis_checker.py` and its fixtures
- `docs/protasis-risk-register-block-study.md`, `audit/AUDIT.md` protasis rounds
- [skills#315](https://github.com/wildcat-finance/skills/issues/315), [skills#307](https://github.com/wildcat-finance/skills/pull/307), [skills#304](https://github.com/wildcat-finance/skills/pull/304)

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is a lint invoked from a terminal at study time; nothing runs unattended. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content when one exists.

## 9. Boundaries, per capability

The checker's trust boundary stays the argument list: paths are read as given, bounded by the existing regular-file and byte-cap refusals, and the new scanner starts no subprocess and opens no socket. [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary rules; its lint runs each round.

## 10. The budget, or its absence

None, and here is why: the register scan is one more pass over an already-capped document, and no caller states a latency requirement. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

A suite or lint failure stops the step and is worked under [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md); each new code ships with the test that would catch its regression, and the standing guards are the evolution suite over the row and the shipped-prose gate over the contract text.

## 12. Decisions and their homes

Two decisions are expensive to reverse. The code numbering S005 to S007 becomes a cited interface the moment it ships, and the successor frontier replaces the held job; both are recorded in the protasis ledger row this run cuts ([hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md): a decision about a governed skill lives in its `EVOLUTION.md`), with this study committed under `docs/` carrying the rejected alternatives. The successor candidate the evidence supports is the amendment block: `protasis-v3.5.0` fixed its four fields, [skills#307](https://github.com/wildcat-finance/skills/pull/307) carried forward that no study exercises them yet, and nothing enumerates them -- the same shape-then-check split this run closes for item 5.
