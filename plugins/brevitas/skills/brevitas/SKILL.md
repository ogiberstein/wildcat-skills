---
name: brevitas
description: Enforce evidence-preserving structural output budgets on engineering prose. Apply automatically to chat answers and written drafts containing audit findings, security or diff review, gas analysis, invariant discussion, protocol analysis, or specification commentary, and on explicit $brevitas invocation. Govern volume, structure, and connective prose only. Do not apply to code comments, commit messages, or completeness-oriented specification documents.
metadata:
  version: "0.1.0"
---

# Brevitas

## Frontier

Brevitas owns the engineering-prose structure frontier, not Hexaemeron's
delivery or Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run another
frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Brevitas enforces mechanical volume and structure budgets on engineering review prose while preserving evidence.

**Use another tool when.** Use Imprimatur for banned vocabulary, Vulgate for register, and Sapheneia for AuDHD interaction shape. Brevitas does not own any of those jobs.

**Current frontier.** The linter has not been forward-tested across a held cross-model corpus of engineering reviews, and preservation of counterexamples and reproduction steps remains agent-checked.
<!-- marketplace-context:end -->

Apply this as the final structural pass after any lexicon or register skill such as
imprimatur or vulgate. Do not alter word choice, voice, or AuDHD presentation.

## Precedence

Preserve evidence before satisfying any budget. Never delete or weaken:

- addresses or transaction hashes;
- `file:line` references or numeric claims;
- concrete counterexamples or reproduction steps; or
- an explicit statement that a fact, property, or conclusion could not be established.

If evidence does not fit, let the budget yield and cut prose further. Never trade
evidence for brevity. If the irreducible evidence still exceeds a finding budget,
retain it and use the evidence-exception mechanism below.

## Compose

1. Answer immediately. Do not restate the request or introduce the answer.
2. Apply these physical-line budgets:
   - Direct answer: at most 6 nonblank lines before the first list or code fence.
   - Finding: at most 5 prose lines: claim, location, mechanism, impact, fix.
   - Code: at most one fence per point and 15 content lines per fence.
3. Give each finding this checkable shape:

   ```text
   [High] Claim.
   Location: `src/Contract.sol:42`
   Mechanism: Concrete causal path.
   Impact: Concrete consequence.
   Fix: Smallest correction.
   ```

   Use only the severity word; do not add a severity-justification paragraph.
4. Put findings adjacent. Add no transition, preamble, or summary between them.
5. Use a table only with at least 3 data rows and 3 real-data columns.
6. Use headings only when the draft has at least 3 sections. A document title does
   not count as a section.
7. Use at most one qualifier per claim.

For an irreducible finding, place this immediately before it:

```html
<!-- brevitas: evidence-exception reason="counterexample requires ordered steps" -->
```

Use the exception only when compression would remove protected evidence. Keep any
extra lines as evidence, counterexample, reproduction, or establishment-limit
statements; do not use the exception to retain connective prose.

## Delete

Delete request restatements, list preambles, post-list summaries, process narration,
bold-label-colon items, trailing offers, unrequested next-step menus, stacked hedges,
and confidence theatre such as "importantly", "notably", or "it's worth noting".
Do not reprint visible code. Quote only the lines that carry the defect.

## Lint

Run the checker before sending substantive chat prose or saving a report. Pipe chat
drafts through stdin; pass a file for written work:

```bash
python3 scripts/brevitas.py - < draft.md
python3 scripts/brevitas.py report.md
python3 scripts/brevitas.py report.md --source uncompressed.md
make -C /path/to/brevitas lint FILE=/path/to/report.md
```

Use `--mode answer` for direct answers and `--mode report` for reports. `auto`
infers a report from findings or at least 3 sections. When compressing existing
material, always pass `--source`; the checker then fails if an address, transaction
hash, `file:line` reference, or numeric token disappears. Fix every diagnostic and
rerun until exit status 0.

Host-required status commentary is outside the draft lint boundary. Do not suppress
status messages required by the execution environment.

## Evals

Run `make test`. The corpus in `evals/cases/` contains preserved audit, x-ray,
and security-review excerpts with source paths, ranges, and pinned fixture
digests. `scripts/run_evals.py` verifies fixture integrity, target structure,
evidence-token survival, actual compression for positive cases, and exact
retention for the evidence-exception case.

## Exclusions

Do not apply this skill to code comments, commit messages, or specification documents
where completeness is the point. Do not perform lexicon, tone, register, or
accessibility transformations.
