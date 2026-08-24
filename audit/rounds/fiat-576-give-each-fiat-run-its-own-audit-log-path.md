# Issue 576: give each Fiat run its own audit log path

Rounds for the run on branch
`fiat/576-give-each-fiat-run-its-own-audit-log-path`, off `main` at
`103fa90c444f35eb09e87b9d2ec29c43a6d34c1f`. The run set
`config audit.log_path` to this file before its first round, so its own
evidence exercises the change it delivers rather than landing in
`audit/AUDIT.md`. Headings carry step and round alone, because the file names
the run.

## Step 1, round 1 -- 2026-08-24

Non-Solidity round over the two Markdown documents step 1 commits, at
`fe7f59ff03d699178a2a2a656a8b7381d7680be0`. Zero findings.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over `README.md AGENTS.md .agents plugins docs`. Protasis accepts the
shipped study in `--study` mode and the shipped runbook in runbook mode.
Imprimatur reports no defect on either, both scoring 100.0. Brevitas exits 0 on
each. Horos reports that the boundary matches the tree. The root suite reports
349 tests OK with no skips and the Hexaemeron suite 986/986, both from inside
this run's worktree. The commit's local signature is good and it carries exactly
one co-author trailer and one origin trailer.

One deviation from the step's stated exit, and it is why this round is clean
rather than red. The exit says both shipped documents are byte-identical to the
run's `.hexaemeron` copies. The shipped study is not. It differs in five link
targets and nothing else:

```text
266c266
< [ephoros](../ephoros/SKILL.md) owns what a signal must carry.
---
> [ephoros](../../skills/ephoros/SKILL.md) owns what a signal must carry.
282c282
< model output reaching a command. [phylax](../phylax/SKILL.md) owns the boundary
---
> model output reaching a command. [phylax](../../skills/phylax/SKILL.md) owns the boundary
289c289
< no step is taken in the name of speed, so [metron](../metron/SKILL.md) has
---
> no step is taken in the name of speed, so [metron](../../skills/metron/SKILL.md) has
304c304
< [elenchus](../elenchus/SKILL.md) owns the triage order and the guard rule.
---
> [elenchus](../../skills/elenchus/SKILL.md) owns the triage order and the guard rule.
322c322
< [hypomnema](../hypomnema/SKILL.md) owns which decisions earn a record and where
---
> [hypomnema](../../skills/hypomnema/SKILL.md) owns which decisions earn a record and where
```

The receipted study cites the five discipline skills as `../<name>/SKILL.md`,
which resolves from a skill directory and from nowhere else. A study ships under
`plugins/hexaemeron/docs/<topic>/`, where all five resolve to nothing. Hypomnema
H001 named every one, and `test_hypomnema_checker.OverTheMarketplace` and
`test_hypomnema_checker.SourceComments` failed the Hexaemeron suite at 984/986
with them. The shipped copy cites `../../skills/<name>/SKILL.md`, which is the
same five documents from where this file lives, and is what the two studies
already committed under `plugins/hexaemeron/docs/` do.

A receipted study cannot be edited and `amend study` only appends, so the choice
was a red tree or a shipped document differing from the receipt in five link
targets. Protasis forbids handing the next step a broken tree. The tree is green
and the difference is recorded here, in full. No claim, criterion, assumption or
design in the document changed.

Two register concerns are reachable at this step and both were checked.
`history-mutation`: `git diff fiat/576-give-each-fiat-run-its-own-audit-log-path
-- audit/AUDIT.md` is empty, because this run's rounds go to this file instead.
`boundary-currency`: `horos check .` reports that the boundary matches the tree,
and `tests/test_boundary_currency.py` passes 7 tests. The other five concerns,
`derived-path-injection`, `override-escape`, `legacy-state-drift`,
`recorded-log-divergence` and `overclaimed-record`, sit in the step 2 and step 3
diffs and are not reachable yet.

One observation for step 5, which owns the boundary.
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` inside a run
worktree rewrites `counts.files_walked` from 1496 to 1532 while all 100 entries
stay identical, because the CLI's walk counts paths that the committed
boundary's `tracked` universe excludes. Step 5's exit pairs that command with
`git diff --exit-code .horos/boundary.json`, which would fail on a count nobody
meant to change. `horos check .` answers the same question without writing, so
step 5 uses it and regenerates only if an entry drifts.

Leads not pursued: none.
