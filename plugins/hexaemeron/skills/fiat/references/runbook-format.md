# Runbook format

Turn the study into an ordered list of steps that ends at a working
prototype. Write it to `.hexaemeron/runbook.md`, emit
`.hexaemeron/steps.json`, and receipt both.

## What makes a step a step

- **Discrete.** One PR, one issue, one clear boundary. If two topics are so
  entangled that separate issues would confuse a reader, keep one issue and
  hang sub-issues off it rather than splitting the step.
- **Self-contained.** Completable in a single session by someone holding
  only the study, the runbook, and the repo at the step's entry state.
- **Green at both ends.** Entry state builds and tests pass; exit state
  builds and tests pass. No step hands the next one a broken tree.
- **Sized for the audit loop.** The security phase dominates the clock, so
  a step's surface should be small enough to audit in a handful of rounds.

## Step schema

Every step in the runbook carries:

```markdown
## Step N: <title>

**Goal.** One sentence.
**Entry.** The exact ref or state this step starts from.
**Exit.** Deliverables, plus the command or test that proves them.
**Files.** Paths created or changed.
**Tests.** What gets written or extended, and the expected count if known.
```

## Fixed points

- **Step 1 scaffolds.** Repo layout, toolchain pins, CI stub, licence, and
  committed copies of the study and runbook (both go through the prose pass
  first, like any other shipped document).
- **The last step demonstrates.** It ends with the prototype's demo path
  from the study's problem statement actually running.
- Ordering is dependency order. A step may assume every earlier step's exit
  state and nothing else.

## steps.json

A JSON list, one entry per step, in order. Strings or `{"title": ...}`
objects both parse:

```json
["Scaffold repo and docs", "Core market contract", "Withdrawal queue", "Demo path and primer"]
```

## Epic issue

When `config issue.epic` is true (default), file a tracking issue with
`gh` whose `TODO` checklist is this step list, one box per step, before
receipting, and pass it as `--epic-issue <url>` on the runbook receipt.
Tick a box only when the matching step's PR is pushed and its own issue
reconciled.

## Receipt

```text
hexctl done runbook --artifact .hexaemeron/runbook.md \
  --steps-file .hexaemeron/steps.json --epic-issue <url>
```

Run the `hexaemeron:imprimatur` lint on the runbook before receipting, same
as the study.
