# Study: Resolve ADR references made from source comments

Assuming, unless corrected:

1. The walk gains source suffixes with one comment marker family each: `#` for Python and shell, `//` with `/* */` blocks for Solidity, JavaScript and TypeScript.
2. A marker counts only at the start of a line's stripped text or preceded by whitespace, so a marker inside a string literal, a URL's `//`, or a quoted heading's `#` earns no scan.
3. The new code is H006; H000 to H005 stay byte-compatible interfaces.
4. Python 3.11 and stdlib unittest, matching every other check in this plugin.
5. The run starts from `main` at `0d5cf1ae68fa3d1ba3a364dcd84eee28adb3beea`.

## 1. Problem statement

The SKILL tells why-comments to point at the decision record when one exists, and `hypomnema.py` reads no file that is not markdown: an ADR cited from a Python or Solidity comment can dangle forever, which is exactly the record-pointing-at-something-absent failure the lint exists to catch. This run extends the walk, which is the held frontier job (`source-comment-adr-references`, [skills#317](https://github.com/wildcat-finance/skills/issues/317)): scan comment lines in source files for ADR references and check them against the `adr_index` the markdown pass already builds. Done means the lint catches a dangling reference from a fixture source file, resolves one that exists, leaves non-comment mentions alone, the ledger advances `hypomnema-v2.2.0` to `hypomnema-v3.2.0` with one evidenced successor job or a mature close, and both suites pass: `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

- `hypomnema.py` owns the walk, the `adr_index` built from record file names, the fixtures skip relative to the walked root, and codes H000 to H005; the source scan joins that walk and reuses the index unchanged.
- The last two merged pull requests that changed the target: [skills#344](https://github.com/wildcat-finance/skills/pull/344), whose carried-forward items are restated here (this run consumes the held successor it recorded; the design-bridge mechanical check stays open and the successor judgement weighs it; the environment-bound tests are restated in item 3; plugin cache staleness stays host-owned; the origin marker rides as inline code on this session's pull requests); and [skills#314](https://github.com/wildcat-finance/skills/pull/314), whose bridge rule is untouched by a wider walk.
- The audit records of the in-scope skills were read before design options were drawn. The "Hypomnema ADR shape check" rounds are fresh this session: step 3 logged the in-step pragma-parsing fault and its guard, and the walk's fixtures skip was settled there, which is what keeps this run's deliberately dangling source fixtures out of tree-wide runs. No accepted lead bears on the scan.
- Every `ADR-` mention in the tree's source files today sits inside a Python string literal in `test_hypomnema_checker.py`, not in a comment. The marker rule in the assumptions is what keeps them unscanned, and the new tests build their specimen strings by concatenation so the test file never carries a whitespace-preceded marker beside a reference.

## 3. Constraints and non-goals

- Starting ref: `main` at `0d5cf1ae68fa3d1ba3a364dcd84eee28adb3beea`. The two `test_elenchus_checker` cases needing a `forge` binary and node v26 stay failing in this container, identically on base.
- Codes H000 to H005 keep their numbers and firing conditions; the markdown pass, the vendored skip and the fixtures skip do not move.
- The evolution row must increment the evolution counter, retain generation and epoch, and either record one evidenced successor or close mature.
- Non-goal: a full tokenizer per language; the marker rule is a stated boundary, and a reference the rule cannot see is a miss the tests document rather than a fault to engineer around.
- Non-goal: scanning markdown prose for bare ADR mentions; the markdown pass keeps its link, supersession and shape rules as they are.
- Non-goal: the design-bridge mechanical check from skills#314, which stays with a later frontier judgement.

## 4. Design options

1. **A source pass inside `check()`, dispatched by suffix, with one marker family per suffix.** Comment text is the stripped text after a line-start or whitespace-preceded marker, plus `/* */` block interiors for the `//` family; references found there are checked against the existing index, H006 when absent. Chosen: one command still lints a tree, the index is built once the way it already is, and the marker rule keeps string literals and URLs unscanned. It trades away references the rule cannot see, such as a marker glued to a quote character, which stays a documented boundary.
2. **Tokenize each language properly.** Rejected: a parser dependency per language for a lint that runs everywhere, against a fault the marker rule already covers in this tree.
3. **A separate source-scanning script.** Rejected: a second invocation to forget, and the audit round cites one hypomnema command.

## 5. Risk register seed

```risk-register
string-false-positive | the marker rule against string literals, quoted headings and URLs | fixtures prove a reference inside a string, after a quote-glued marker, and behind a URL's double slash earn no finding
tree-self-trip | the new tests against the walk that reads the test file itself | the tree-wide walk exits 0 with the new tests in place, their specimens built so no literal carries a whitespace-preceded marker beside a reference
index-reuse | the source pass against the adr_index the markdown pass builds | the same index answers both passes and a record renamed away is caught from source and markdown alike
interface-drift | codes H000 to H005 against the new code | the existing tests pass unchanged and H006 joins the docstring and the SKILL.md subset
ledger-arithmetic | the evolution row against the versioning contract | the round relies on the evolution suite passing over the new row
```

The audit loop should look hardest at tree-self-trip: the lint now reads its own test suite, and a specimen written carelessly makes the suite fail the tree it ships in.

## 6. Glossary seeds

- Source comment: the stripped text after a line-start or whitespace-preceded marker, or a `/* */` block interior in the `//` family.
- Marker rule: the whitespace condition in assumption 2 that keeps strings and URLs unscanned.
- H006: a source comment citing a record the index does not hold.

## 7. Sources

- `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `scripts/hypomnema.py`, `EVOLUTION.md`
- `plugins/hexaemeron/skills/VERSIONING.md`
- `plugins/hexaemeron/tests/test_hypomnema_checker.py` and its fixtures
- `audit/AUDIT.md`, "Hypomnema ADR shape check" rounds
- [skills#317](https://github.com/wildcat-finance/skills/issues/317), [skills#344](https://github.com/wildcat-finance/skills/pull/344), [skills#314](https://github.com/wildcat-finance/skills/pull/314)

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is a lint invoked from a terminal; nothing runs unattended. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content when one exists.

## 9. Boundaries, per capability

The lint now reads source files as well as markdown, still as given by the caller's argument list, still with no subprocess and no socket; an unreadable source file is reported the way an unreadable record is. [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary rules; its lint runs each round.

## 10. The budget, or its absence

None, and here is why: the walk gains the repository's source files at one pass per line, no caller states a latency requirement, and the suites time the run in practice. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one exists.

## 11. The fail-closed posture

A suite, lint or Promise Machine gate failure stops the step and is worked under [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md); H006 ships with the tests that would catch its regression, and the standing guards are the evolution suite over the row and the shipped-prose gate over the contract text.

## 12. Decisions and their homes

Two decisions are expensive to reverse: the marker rule becomes the boundary every later reference check inherits, and the frontier either takes a successor or closes. Both are recorded in the hypomnema ledger row this run cuts ([hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md): a decision about a governed skill lives in its `EVOLUTION.md`), with this study committed under `docs/` carrying the rejected alternatives. The successor candidate the evidence supports is the runbook shape: the SKILL states the three-line runbook convention and H003 checks only that a named runbook file exists, never that it carries what fired, the first thing to look at and who to wake -- the same existence-without-shape gap this ledger has now closed twice.
