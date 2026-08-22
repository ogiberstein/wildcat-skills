# Study: a clear contributor path into the Shoggoth

Assuming, unless corrected:

1. The public audience is an intelligent contributor who can use GitHub but does not need to understand the controller internals.
2. The explainer describes what works now and labels the volunteer selector as a proposal; it must not present an unimplemented command as live.
3. The highest numbered open `**Wave:**` block in issue metadata is the current wave. On 2026-08-22 that is Wave 12, with six open, unassigned issues.
4. A named issue URL overrides every inferred selection. Without one, ordinary volunteer help should prefer the current wave rather than a skill frontier.
5. Frontier work remains opt-in and subject to the owning skill's maturity gate. Maintenance may instead refresh Horos, census issues, or produce a new ranking proposal without claiming a frontier advance.
6. The PDF follows the Promise Machine field-guide V2 design and uses the Wildcat Shoggoth as a humanoid figure with a faceted geometric head. It must not depict a literal cat.
7. The run starts from `98d0cded34bc559ba7ed2466988c40f0c3e28937`, the merge of external-contributor PR #445.

## 1. Problem statement

Build a short contributor guide for someone outside the core team and a discussion issue for the missing volunteer-intent signal. The guide explains how a person can choose useful work, announce it, let Fiat turn it into a receipted delivery, and contribute maintenance without pretending every contribution advances a skill frontier.

A working prototype has four parts:

- a repository Markdown guide grounded in an external contributor's 2026-08-22 delivery;
- a wide-page PDF and infographic in the established field-guide style, using repository mascot references;
- a filed framework observation that proposes an explicit volunteer selector and public claim boundary; and
- evidence that the prose lints, repository tests, PDF text checks and rendered-page inspection pass.

The demo path is: read the guide, follow its present-day named-issue route, inspect the proposed three-lane selector, open the PDF, and follow the linked discussion issue.

## 2. Prior art

An external contributor supplied the live example. Their prompt was `/fiat how do i help evolve you`. The resulting work landed in [PR #445](https://github.com/wildcat-finance/skills/pull/445), which closed [issue #438](https://github.com/wildcat-finance/skills/issues/438). The run produced three fork pull requests, added issue-aware Fiat branch names, fixed a malformed task-issue URL parser finding, published Fiat 5.10.1 and Hexaemeron 1.5.4, and merged upstream as `98d0cded34bc559ba7ed2466988c40f0c3e28937`. This is evidence that an external contributor can complete a real, audited Fiat delivery.

The last two merged pull requests changing the controller were read before options were drawn:

- [PR #445](https://github.com/wildcat-finance/skills/pull/445) made a known task issue visible in every automatic run and step branch. It carried Fiat's held job, issue #363, forward unchanged. Its previously unfinished maintainer merge and issue closure are now complete.
- [PR #444](https://github.com/wildcat-finance/skills/pull/444) repaired the evolution-ledger gate after it disagreed with the repository's accepted compact ledger shape. It carried no volunteer-selection design.

The relevant audit record was read. PR #445's step 2 round 1 found that the task-issue parser accepted relative, hostless and non-HTTP inputs. Commit `63861895b98585cf597ae1fb3a2ec749ae3c9ef7` added raw-control, scheme, hostname and canonical positive-number checks; round 2 closed the finding. The guide may therefore say that the issue URL is bound and validated. It may not say that branch visibility prevents duplicate work on its own.

The Shoggoth Interceptor protocol already fetches open issues, excludes assigned work, ranks candidates, resolves the implementation repository and sends one issue through Fiat. It detects issue trails in branches and pull requests. It has no explicit volunteer lane and its issue reader is deliberately read-only. Those constraints matter: a volunteer signal cannot silently assign, label or comment without separate authority.

The issue corpus carries `**Wave:**` metadata. On the study snapshot, Waves 3 through 12 remain open; Wave 12 is the latest and contains issues #418 through #423, all six open and unassigned. Ten other open issues have no wave metadata, including later observations and Fiat wishes. Kronos already supports recorded rank-only passes over held frontier jobs, but that is a different candidate universe from the Wave backlog.

## 3. Constraints and non-goals

- Starting ref: `98d0cded34bc559ba7ed2466988c40f0c3e28937` on `main`.
- Toolchain: repository Python tests and bundled prose lints; ReportLab/Pillow/PyPDF and Poppler for the derived PDF; built-in image generation with repository reference art.
- The guide must distinguish present behaviour from proposed behaviour.
- The mascot is a humanoid with a geometric mask-like head. No fur, paws, whiskers, tail, domestic-cat anatomy or cyber-cat substitute.
- The issue is a discussion artefact, not an implementation of the selector.
- No skill frontier, evolution ledger, package version, controller receipt shape or Shoggoth write policy changes in this run.
- No automatic issue assignment, label, comment or closure is added.
- No claim that the highest wave is objectively the most important work; it is the default backlog slice selected by stated metadata.
- No performance claim or new runtime dependency.

Always: run the root tests before each implementation receipt, lint every shipped prose file, validate the PDF text and page count, and inspect rendered pages. Ask first: adding a dependency, changing issue metadata, implementing write access, or changing a public command. Never: edit protected Shoggoth guardrails, present a proposed selector as live, invent the contributor's results, mutate unrelated issue metadata, or claim a check ran when it did not.

## 4. Design options

### Option A: keep natural-language inference

Interpret words such as “evolve”, “help” and “next” to choose a job. This is frictionless, but the external contribution also demonstrates the defect: small wording changes can steer the candidate universe, and the same friendly prompt may repeatedly consume a frontier or old Fiat-adjacent job.

### Option B: an explicit volunteer intent packet

Propose one visible volunteer signal with three lanes: `wave`, `frontier` and `maintenance`. A named issue wins. With no issue and no lane, `wave` is the default and selects from the highest open Wave metadata. `frontier` invokes the owning ledgers and maturity gates. `maintenance` names a bounded task such as refreshing Horos or producing a census/ranking proposal. This is cheapest to explain and preserves current specialist boundaries.

Trade: it adds a small grammar and requires a decision about where volunteer intent becomes publicly visible before a pull request exists.

### Option C: GitHub assignment or label only

Treat assignment or a new label as the entire signal. It is public and easy to inspect, but outside contributors may not have permission, and the Shoggoth issue path currently has no write authority. It also says who claimed work without saying whether they volunteered for a Wave, frontier or maintenance lane.

### Option D: run a full census and Kronos-style ranking every time

Recompute all issues and held jobs before every volunteer run. This adapts to drift, but is slow, mixes two candidate universes, and turns “I can help” into a planning exercise. A census is valuable maintenance when requested or when the snapshot is stale, not a mandatory prelude to every contribution.

### Chosen design

Use Option B in the discussion issue and explainer, while describing the present safe route as a named issue URL. Keep assignment, issue comments, branches and pull requests as possible public claim channels to be settled in discussion. This trades automatic magic for one explicit choice and refuses to infer frontier intent from the word “evolve”.

## 5. Risk register seed

```risk-register
selection-overclaim | the guide's proposed command examples | proposed syntax is visibly marked as not implemented
mascot-identity | the generated artwork and PDF composition | every figure is checked against the humanoid geometric-head references and carries no literal-cat anatomy
contributor-attribution | the external contribution summary | dates links commits findings and outcomes match GitHub and the merged audit record
wave-drift | the issue snapshot behind the default lane | the PDF dates the Wave 12 snapshot and does not claim it remains current forever
duplicate-work | the gap between local volunteer intent and public visibility | the proposal names assignment branch PR and comment boundaries without claiming any is already automatic
issue-authority | filing the discussion issue | the issue requests design discussion and performs no assignment label or metadata mutation beyond the authorised observation label
binary-review | the generated PDF and infographic | source prose remains reviewable and the final binary is rendered text-extracted and page-count checked
scope-widening | the temptation to implement the selector during documentation work | no controller interceptor ledger or version files change
```

## 6. Glossary seeds

- **Fiat:** the receipted delivery controller that turns a scoped job into study, runbook, implementation, audit, prose and publication steps.
- **Shoggoth:** the issue-selection and delivery operator that chooses work, invokes Fiat and leaves evidence.
- **Wave:** a backlog grouping written in issue-body metadata, such as `Wave 12 - voice`.
- **Frontier:** a skill's own held next improvement, governed by its evolution ledger and maturity gate.
- **Maintenance:** bounded upkeep or planning that need not advance a frontier, such as a Horos refresh or issue census.
- **Volunteer intent:** an explicit statement that a person is offering to run Fiat and which candidate lane they mean.
- **Claim signal:** the visible evidence that a specific issue is already being worked, such as assignment, an issue-number branch or an open pull request.

## 7. Sources

- `AGENTS.md`, especially the four issue queues and repository checks.
- `PROMISE_MACHINE.md`.
- `plugins/hexaemeron/skills/fiat/SKILL.md` and `EVOLUTION.md` at the starting ref.
- `plugins/hexaemeron/skills/kronos/SKILL.md` and `docs/kronos-rank-only/study.md`.
- `audit/AUDIT.md`, “Fiat task-issue branch names” rounds.
- [wildcat-finance/skills issue #438](https://github.com/wildcat-finance/skills/issues/438).
- [wildcat-finance/skills PR #445](https://github.com/wildcat-finance/skills/pull/445).
- [wildcat-finance/skills PR #444](https://github.com/wildcat-finance/skills/pull/444).
- GitHub issue snapshot taken 2026-08-22 for Wave metadata and assignment state.
- Shoggoth Interceptor `CLAUDE.md`, `README.md`, `bin/shoggoth.py` and `bin/console.py`.
- Wildcat mascot references: `mascot-imagegen-kit/skill-characters/shoggoth.png`, `skill-characters/hexaemeron.png`, `skill-characters/kronos.png`, and the brand guideline corpus.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal design. This run adds no unattended process, so it emits no runtime telemetry. The human-facing artefacts must still answer: “Which lane did the volunteer mean?”, “Which exact issue, snapshot or maintenance scope was selected?”, “Is anybody already working it?”, and “Did this delivery finish or only produce a discussion proposal?” The guide and issue answer those questions through explicit lane, issue URL, dated snapshot, claim-channel and status fields.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary controls.

- GitHub reads: take issue, pull request and assignment metadata; control with authenticated read-only queries and exact URLs.
- Issue creation: take only the authorised discussion body; control by previewing the exact title/body, applying the existing `observation` and `origin:ai` labels, and reading the created issue back.
- Image generation: take only approved repository references; control by visual identity review and the no-literal-cat constraint.
- PDF creation: take local prose and approved artwork; control with stable output path, text extraction, page-count assertion and rendered-page inspection.
- Repository mutation: take only the contributor guide, study/runbook copies and final reviewable assets; control with the Fiat branch stack, tests and signed commits.

## 10. The budget, or its absence

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns performance evidence. There is no performance change and no runtime budget. The practical size boundary is editorial: no more than six wide pages, with a one-page quick-start path. Page count is checked with `pdfinfo`; this is a presentation constraint, not a speed claim.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns failure work. Stop the dependent transition if the external contribution cannot be verified, proposed syntax reads as live, the mascot becomes a literal cat, an issue write differs from the preview, a prose lint fails, repository tests fail, or the PDF render shows clipping or overlap. A fix gets a guard where mechanical: text assertions for current/proposed labels, PDF term and page-count checks, and visual reinspection after any layout or image change.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns record placement. The current guide lives under `docs/` and keeps the dated external-contributor case study. The volunteer selector is expensive to reverse only after it becomes a public command, so this run files a framework observation rather than an ADR or implementation. The issue is the durable home for lane grammar, default selection, claim-channel and census-trigger discussion. The study records why natural-language inference and mandatory full census were rejected for this prototype.
