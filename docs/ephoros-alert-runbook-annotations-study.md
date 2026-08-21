# Study: Require alert rules to carry a resolving runbook annotation

Assuming, unless corrected:

1. An alert rule is in scope when a `.yaml` or `.yml` file contains a Prometheus-style list entry whose mapping starts with `alert:`.
2. The required handoff is an `annotations` mapping on that alert entry containing `runbook: <relative-path>.md`; a `runbook` key elsewhere does not satisfy the alert.
3. The supported prototype is block-style YAML. Flow mappings, anchors that supply the annotation indirectly, templated files and other configuration languages remain outside the parser's claim.
4. Ephoros classifies alert entries and owns only annotation presence. Hypomnema does not classify alerts: its generic H003 pointer pass recognises a `runbook:` field in supported YAML and owns whether the relative target exists, while H007 continues to own the three answers in Markdown below a `runbooks` directory.
5. Python 3.11 and the standard library remain the implementation boundary; no YAML dependency is added.
6. E004 is the new Ephoros finding code. E000 to E003 and Hypomnema H000 to H007 retain their numbers and existing firing conditions.
7. This is ordinary generation work under issue 319, not Ephoros's held frontier. Ephoros advances from `ephoros-v0.1.0` to `ephoros-v0.2.0`; Hypomnema advances from `hypomnema-v4.2.0` to `hypomnema-v4.3.0` for its wider H003 input surface. Both generation rows retain their current frontier revision, digest, status and `Next Fiat job` byte for byte.
8. The run starts from `main` at `0bfad60bb482245dd08d9747139d26824392a2c7`.

I will proceed on these assumptions unless corrected.

## 1. Problem statement

Ephoros says every alert needs a runbook, but its checker reads only Python and enforces none of that handoff. A Prometheus-style alert rule can therefore omit the annotation entirely and pass every mechanical gate. Build a bounded alert-rule pass for Wildcat contributors that reports E004 for each in-scope alert entry without its own local `runbook` annotation. Keep the three obligations separate: Ephoros requires the annotation, Hypomnema H003 resolves its relative target, and Hypomnema H007 checks the target's `What fired`, `First check` and `Who to wake` answers.

A working prototype is established by these checkable criteria:

- The focused Ephoros tests report one E004 for each unannotated alert entry, including one missing entry beside an annotated neighbour, and report no E004 for a correctly annotated entry.
- Negative fixtures prove that comments, block-scalar examples, a top-level `runbook` key and a `runbook` key belonging to another alert do not satisfy an alert entry.
- The focused Hypomnema tests report H003 for a supported YAML `runbook` annotation whose relative target is absent, accept the same annotation once its target exists, and preserve H003's existing Markdown cases.
- H007, unchanged, rejects an existing target below a `runbooks` directory when any of its three answers is absent or empty; a complete end-to-end alert, pointer and runbook specimen is clean under both checkers.
- Existing E000 to E003 and H000 to H007 tests pass unchanged, the full first-party tree is clean, and the root and Hexaemeron suites pass.
- The two generation rows pass the evolution contract while retaining both held frontier jobs unchanged.

The demo path is:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_ephoros_checker plugins.hexaemeron.tests.test_hypomnema_checker
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

## 2. Prior art

- `plugins/hexaemeron/skills/ephoros/SKILL.md`, `scripts/ephoros.py` and `tests/test_ephoros_checker.py` define E001 to E003 over Python. The current tree has no alert-rule fixture and the shipped checker returns no verdict for YAML.
- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` defines H003 as existence-only pointer resolution and H007 as the three-answer Markdown shape. The recently shipped `docs/hypomnema-runbook-shape-check-study.md` names issue 319 as the owner of annotation presence and explicitly leaves alert-rule YAML out of Hypomnema's alert classification.
- The last two merged pull requests that changed Ephoros were [skills#293](https://github.com/wildcat-finance/skills/pull/293) and its stacked step [skills#288](https://github.com/wildcat-finance/skills/pull/288). PR 293's `Carried forward` section names host captures and other skills' frontiers, none of which applies here. PR 288 has no `Carried forward` section; its then-open behavioural-conformance work was completed by the integrated Promise Machine run. Neither PR carried an alert-rule implementation or an Ephoros-specific unresolved defect.
- The earlier introduction PR, [skills#103](https://github.com/wildcat-finance/skills/pull/103), records why Ephoros ignores `print`, restricts duration means and resolves logger names. Its known CI gap remains outside this issue: local runs must execute the Hexaemeron suite, and changing CI requires approval.
- `audit/AUDIT.md` records two relevant boundaries. Promise Machine step 6 found that a judgement-held Ephoros review had borrowed evidence from its narrower parser and replaced that overclaim with labelled review cases. The Hypomnema runbook-shape round records that H003 stays existence-only, H007 owns the target shape and annotation presence stays with issue 319. This build preserves both decisions.
- `plugins/hexaemeron/audit/AUDIT.md` contains no Ephoros-specific finding; it predates the practice-skill checker. No accepted audit lead requires reopening in this generation.

## 3. Constraints and non-goals

- Starting ref: `main` at `0bfad60bb482245dd08d9747139d26824392a2c7`.
- The Promise Machine boundary remains narrow: a clean E004 pass establishes annotation presence on the supported YAML subset, not correct alerting, correct YAML in every dialect, a resolving target or operationally useful runbook content.
- Ephoros alone decides that a YAML entry is an alert and whether it carries the annotation. Hypomnema's YAML work is a generic H003 pointer scan and must not emit an alert-presence finding. H007 remains unchanged.
- The annotation is a relative local Markdown path so H003 can establish existence and H007 can inspect a repository record. Remote runbook URLs are deferred.
- E000 to E003 and H000 to H007 are stable interfaces. Existing suppressions retain their scope; any E004 suppression must use the existing reasoned `# ephoros: allow <why>` form on the alert line or the line above it.
- No third-party YAML parser, network call, subprocess, Solidity, vendored file, generated artefact, CI workflow or broader configuration-language support.
- The Ephoros held target remains wallet-address linkage across Python and TypeScript. The Hypomnema held target remains the design-bridge check. This ordinary run does not claim either frontier advance.
- **Always.** Run the focused checker tests, root suite, Hexaemeron suite, Promise Machine check, evolution check and repository prose/tree lints before commit; lint every shipped document with Imprimatur; record a baseline before any performance-motivated change.
- **Ask first.** Add a dependency, touch CI, change a public checker interface beyond the named codes and suffixes, widen the trust boundary, add another config dialect or rewrite a released digest.
- **Never.** Edit vendored directories, weaken H003 or H007, let one alert borrow another's annotation, delete a failing test, commit credentials or claim an unrun command.

## 4. Design options

1. **One bounded, indentation-aware YAML alert pass in Ephoros plus a generic YAML H003 pointer pass in Hypomnema.** Chosen. It is the least code that preserves ownership: Ephoros identifies `alert` entries and requires their nested annotation; Hypomnema sees only a `runbook` pointer and applies its existing resolution rule. It trades away full YAML semantics and non-YAML alert formats.
2. **Add PyYAML and parse complete YAML objects in both checkers.** This handles anchors and flow mappings, but adds an execution dependency and duplicate traversal for a narrow prototype.
3. **Make Ephoros check both presence and target resolution.** This is locally simpler, but duplicates H003 and would let the two skills disagree about the same missing target.
4. **Make Hypomnema classify alert rules and enforce the annotation.** This keeps pointer work together, but crosses the explicit ownership boundary and turns a record checker into an alert-rule checker.

Option 1 is chosen because it is cheapest to comprehend while meeting the issue. Its deliberate trade is a documented block-YAML subset rather than the false claim of general YAML parsing.

## 5. Risk register seed

```risk-register
alert-classification | the YAML lines Ephoros classifies as alert entries | only block-style list entries with an alert key are in scope and neighbouring config is left alone
annotation-ownership | the split between E004 and H003 | Ephoros checks presence only and Hypomnema resolves the named target without classifying alerts
record-isolation | multiple alert entries in one YAML file | each alert must carry its own nested annotation and cannot borrow one from a neighbour or top-level mapping
yaml-lexing | comments quoted text and block scalars near alert-shaped content | non-key examples do not create alerts or satisfy annotations and unsupported forms remain visible as out of scope
pointer-base | a relative runbook path read from YAML | H003 resolves from the alert-rule file directory and reports the original pointer line when absent
stable-codes | E000 to E003 and H000 to H007 beside E004 | every existing test passes unchanged and the new code does not renumber or widen an old finding
frontier-preservation | the two ordinary generation rows | current frontier revisions digests statuses and held jobs remain byte-identical while generation increments once
tree-self-trip | the new YAML walk over first-party files | fixtures are skipped on directory walks and the complete marketplace scan exits clean
```

The audit loop should look hardest at record-isolation and annotation-ownership. A parser that lets one annotation satisfy two alerts misses the issue; a parser that resolves the target in Ephoros duplicates Hypomnema.

## 6. Glossary seeds

- Alert entry: a supported block-style YAML list mapping introduced by an `alert` key.
- Runbook annotation: a `runbook` key nested under that alert entry's `annotations` mapping, containing a relative Markdown path.
- E004: an in-scope alert entry has no qualifying runbook annotation.
- H003: the named local runbook target does not exist relative to the file containing the pointer.
- H007: an alert runbook below a `runbooks` directory lacks one of its three required, non-empty answers.
- Ownership handoff: E004 establishes presence, H003 establishes existence and H007 establishes recognised shape, with no one code claiming all three.

## 7. Sources

- [skills#319](https://github.com/wildcat-finance/skills/issues/319)
- `PROMISE_MACHINE.md`, `.agents/skills/promise-machine/SKILL.md`, `plugins/hexaemeron/AGENTS.md`
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/protasis/SKILL.md`
- `plugins/hexaemeron/skills/ephoros/SKILL.md`, `EVOLUTION.md`, `scripts/ephoros.py`, and `plugins/hexaemeron/tests/test_ephoros_checker.py`
- `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `EVOLUTION.md`, `scripts/hypomnema.py`, and `plugins/hexaemeron/tests/test_hypomnema_checker.py`
- `plugins/hexaemeron/skills/VERSIONING.md`
- `docs/hypomnema-runbook-shape-check-study.md`, `docs/hypomnema-runbook-shape-check-runbook.md`
- `audit/AUDIT.md`, Promise Machine steps 5 and 6 and Hypomnema runbook-shape steps 1 and 2; `plugins/hexaemeron/audit/AUDIT.md`
- [skills#293](https://github.com/wildcat-finance/skills/pull/293), [skills#288](https://github.com/wildcat-finance/skills/pull/288), [skills#103](https://github.com/wildcat-finance/skills/pull/103)

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is a lint invoked from a terminal and does not run unattended. Its result is command output rather than durable telemetry. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) remains the authority for any future unattended checker service; this run adds no such service.

## 9. Boundaries, per capability

The new capability reads caller-named first-party YAML as untrusted text, classifies only a bounded alert shape and returns findings without executing input or writing files. Size, decoding, path and fixture-walk behaviour must fail visibly or stay inside the existing checker boundary; no shell, URL, credential, dependency or model-output boundary is introduced. [Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary review and its tree lint remains an audit gate.

## 10. The budget, or its absence

None, and here is why: no performance claim or caller-supplied latency ceiling exists, and the supported pass is bounded by each file's bytes and lines. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md) applies if implementation is proposed for speed; that would first require a recorded baseline and exact repeatable command.

## 11. The fail-closed posture

An unreadable or malformed supported input, focused-test failure, old-code regression, tree-lint finding, Promise Machine mismatch, evolution failure or suite failure stops the step. Any observed failure is preserved and worked under [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md): reproduce it, localise the mechanism and add a guard that fails without the fix before resuming. E004 ships with missing, neighbour-isolation and false-positive guards; the H003 YAML extension ships with dangling, restored-target and Markdown-regression guards.

## 12. Decisions and their homes

The alert classifier, E004 boundary and rejected full-YAML alternatives are Ephoros decisions and belong in the `ephoros-v0.2.0` generation row. The generic YAML input extension for H003 and its refusal to classify alerts belong in the `hypomnema-v4.3.0` generation row. This committed study supplies the source material, while the two ledgers are the standing records; no cross-cutting ADR is added and neither decision is copied into two homes. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns that placement. Both rows cite issue 319 and the delivered evidence while retaining their held frontiers unchanged.
