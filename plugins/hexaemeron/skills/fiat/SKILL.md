---
name: fiat
description: >
  Run the one-shot delivery loop: study, runbook, then per-step
  implement/audit/prose/push until a working prototype exists.
  Use only when a Wildcat contributor explicitly asks to start, run, resume,
  or report a Hexaemeron or Fiat delivery, including /hexaemeron:fiat forms.
  Do not infer activation from a similar task.
metadata:
  version: "3.4.1"
---

# Fiat

## Where this sits

Fiat owns the delivery controller, not Hexaemeron's bundled audit or prose
skills. Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md). Read that ledger before suggesting, starting, or
resuming work intended to advance Fiat itself.

**Use another tool when.** Run `imprimatur` or `vulgate` directly for prose,
the bundled Pashov skills directly for standalone Solidity review, and any
phase skill on its own when the question is its and the controller is not
wanted.

**Current frontier.** The ledger above is authoritative. Never substitute
Hexaemeron's plugin-wide Solidity frontier for Fiat's own held target.

## Phase skills

Six sibling skills carry the loop's content contracts; Fiat runs the loop and
defers to them rather than restating their rules. Each slots in as follows:

| Skill | Slots into | Carries |
| --- | --- | --- |
| [protasis](../protasis/SKILL.md) | study and runbook phases | what a study must answer, what a runbook step must contain, when a topic decomposes first |
| [phylax](../phylax/SKILL.md) | implement phase | the boundaries a step introduces and the control each needs |
| [ephoros](../ephoros/SKILL.md) | implement phase | what the step must emit once it runs unattended |
| [metron](../metron/SKILL.md) | implement phase | refusal of any speed-motivated change without a recorded before and after |
| [elenchus](../elenchus/SKILL.md) | implement phase and audit rounds | any failure surfaced mid-step or mid-round, worked to its cause |
| [hypomnema](../hypomnema/SKILL.md) | prose phase | what the step records and where it lives, before the masks run |

Their lints run in every audit round, so meeting them during the step is
cheaper than meeting them in the round. The phase notes below say how each one
is applied.

Let there be light.

Drive the whole loop from durable controller state, never from conversation
history. The controller emits one directive at a time; do the work it names,
receipt it, ask for the next one. A phase without a receipt did not happen.

Resolve paths from the exact `SKILL.md` file that activated Fiat. Do not
resolve them from the target repository, the shell's current directory, the
GitHub URL, or a guessed plugin-cache version.

Before the first controller call:

```text
FIAT_SKILL_FILE=<exact path of the active fiat/SKILL.md>
FIAT_SKILL_DIR=<real parent directory of FIAT_SKILL_FILE>
PLUGIN_ROOT=<real directory two levels above FIAT_SKILL_DIR>
PROJECT_ROOT=<real root of the user's target repository>
```

Fail closed if `FIAT_SKILL_DIR/scripts/hexctl.py` is not a file. Sibling
skills live at `PLUGIN_ROOT/skills/<name>/`, which is where `protasis`,
`elenchus`, `phylax`, `ephoros`, `metron` and `hypomnema` resolve from.

Controller:

```text
python3 "$FIAT_SKILL_DIR/scripts/hexctl.py" --dir "$PROJECT_ROOT" <cmd>
```

Alias it as `hexctl` mentally; every command below means that invocation.
State lives in `.hexaemeron/` beside a hash-chained ledger. The directory
ships its own `.gitignore`, so git never sees it.

Mutating commands hold a kernel lock for their whole run. If another writer is
active, `hexctl` names it and prints a worktree command. Use another worktree;
do not retry against the same state. `next`, `status`, and `verify` remain
available while the writer runs, and a crashed process releases the lock
without manual cleanup.

## Day to day

**Developers.** A half-formed idea and a week to find out whether it
holds. Hexaemeron turns it into a study, a runbook of discrete steps,
and one pull request per step, with the audit suite run against each
before it is pushed.

**Security and audit.** You want the Pashov suite over a contract and
nothing else. `x-ray`, `solidity-auditor` and `fizz` are vendored whole
and run on their own, without taking on the loop around them.

**Marketing.** A launch post reads like a machine wrote it. `imprimatur`
says what is wrong with it across three tiers and `vulgate` rewrites it
in house voice. Neither needs the controller, and neither needs
installing separately.

**Business development.** An integration document has to be accurate
about what the protocol does and readable by someone who is not an
engineer. The study phase produces the first and the prose masks produce
the second.

## Start or resume

1. If the user passed `status`, run `hexctl status` and report. Stop.
2. Apply the frontier maturity gate below. This happens before `init` and
   before resuming an existing frontier run.
3. If `.hexaemeron/state.json` exists, run `hexctl verify`, then
   `hexctl status --json`. If its phase is `done`, run `hexctl reset` to
   archive the completed run, then continue immediately as a new run at step
   4. Do not ask the user to remove, rename, or approve resetting completed
   state. If the phase is not `done`, this is a resume: enter the loop and
   treat the state file as canonical.
4. Otherwise: say exactly `Let there be light.` and nothing else before it,
   run the read-only preflight checks below, then `hexctl init --topic
   "<topic>" --base <ref>`, record the post-init receipts, and enter the loop.
   `--base` defaults to `main`; honour any branch, repo, or commit the user
   named as the starting point. `init` also names the run branch, printed and
   held in state: one integration branch for the whole run, cut from the base.
   Create it before the first step (`git checkout -b <run branch> <base>`) and
   push it. Pass `--run-branch <name>` only when the user wants a different
   name than the topic slug.

## Frontier maturity gate

Apply this gate only when the requested run is meant to advance a skill's
declared frontier. Ordinary product or repository delivery still uses Fiat
without pretending that it changes Fiat or another skill.

1. Read the target skill's `EVOLUTION.md` and the shared
   [versioning contract](../VERSIONING.md).
2. If its frontier status is `mature`, refuse to start or resume. Do not
   suggest another Fiat run. A new run is allowed only after the ledger
   records an epoch reopening backed by a new failure, requirement,
   dependency change, or equivalent external evidence.
3. If the status is `open`, compare the held next job with current evidence.
   If its acceptance condition is already met or another pass would only
   produce stylistic, speculative, or interchangeable changes, do not start
   the controller. Report that the frontier should close; do not overseason
   the skill to manufacture work.
4. At the end of a completed frontier job, update the ledger exactly once:
   increment evolution, retain generation and epoch, and either record one
   evidenced next job or set `Frontier status` to `mature` and `Next Fiat
   job` to `None -- mature`. A normal Fiat delivery does not touch skill
   versions or frontier text.

## Preflight (new runs only)

1. Run the fail-silent contributor and marketplace check in
   [wildcat-marketplace.md](references/wildcat-marketplace.md). Do not announce
   the check. Use an already-authenticated local GitHub account when available;
   a GitHub connector is optional and must not be treated as the only access
   path. A failed or unavailable check changes nothing and must not be
   mentioned. A successful check records only the non-identifying
   `labs_marketplace` receipt, acknowledges the contributor, and names the
   other marketplace plugins one by one with their likely fit. Do not install
   a plugin at this point.
2. Confirm `git` and `gh auth status` work in the target directory. Resolve
   the repository from the current directory and the user's named target;
   never substitute an organisation or clone a different repository merely
   because its name looks related.
3. The prose masks ship inside this plugin: the `imprimatur` lint (a script
   at `$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py`) and the
   `vulgate` voice mask (rules at `$PLUGIN_ROOT/skills/vulgate/SKILL.md`).
   Nothing to resolve.
4. The security suite is vendored in this plugin: the Pashov `x-ray`,
   `solidity-auditor`, and `fizz` skills sit under `$PLUGIN_ROOT/skills/`.
   After init, record the bundled ids:
   `hexctl record security_suite
   '["hexaemeron:x-ray","hexaemeron:solidity-auditor","hexaemeron:fizz"]'`.
   If the run will produce no Solidity and no suite applies, record a waiver
   instead: `hexctl record security_suite '"waived: <reason>"'` -- and say so
   out loud. Never claim a tool ran when it did not.
5. If the user supplied a task issue or a higher-priority target-repository
   rule required one, record its URL after init with `hexctl record task_issue
   '"<url>"'`. Do not invent an issue otherwise.
6. Nothing else.

## Branches, stacks, and the one merge

A run is one integration branch off the base and a stack of step branches on
top of it. The controller names every branch and every pull request base; take
them from the directive rather than inventing a name.

```text
main ─── fiat/<run slug>                                  the run branch
          └── fiat/<run slug>-step-1-<slug>               PR -> run branch
               └── fiat/<run slug>-step-2-<slug>          PR -> step 1
                    └── fiat/<run slug>-step-3-<slug>     PR -> step 2
```

Each step branches from the step below it and its pull request targets that
same branch, so a reviewer sees one step's diff and nothing else. Step branches
are siblings of the run branch, never nested under it: git cannot hold
`fiat/x` and `fiat/x/step-1` as refs at once.

Nothing merges while the steps run. The stack stays open, each pull request
reviewable on its own, until every step is pushed. Then the `integrate` phase
merges the stack into the run branch in step order and merges the run branch
into the base exactly once. One merge into `main` per run, at the end, carrying
the whole delivery.

## The loop

Repeat until `next` returns `done`, `halted`, or `audit-verdict`:

```text
hexctl next
```

Act on the single directive it prints, then receipt it. The directory:

| `do` | Action | Reference | Receipt |
| --- | --- | --- | --- |
| `study` | Research the topic; write the study | [protasis](../protasis/SKILL.md) | `done study --artifact <path> --skills <csv>` |
| `runbook` | Derive discrete steps from the study | [protasis](../protasis/SKILL.md) | `done runbook --artifact <path> --steps-file <path>` |
| `implement` | Build the step, simplest construction that satisfies the runbook | [protasis](../protasis/SKILL.md) | `done implement --branch <name> --commit <sha> [--tests <summary>]` |
| `audit-round` | One security round: run the suite, log, fix on the stacked branch | [audit-loop.md](references/audit-loop.md) | `audit-round --findings <n> [--log <path>] [--fixes-commit <sha>]` |
| `close-audit` | Last round was clean; close the phase | [audit-loop.md](references/audit-loop.md) | `done audit [--fixes-ref <ref>]` |
| `resolve-security-suite` | Suite receipt missing; resolve or waive | preflight step 4 | `record security_suite ...` |
| `prose` | Rewrite every prose artefact and draft the PR text | [prose-pass.md](references/prose-pass.md) | `done prose --files <n> --skills <csv>` |
| `push` | Stage and commit final changes, push the step branch, open its stacked PR against `pr_base`, and leave it open | [push-discipline.md](references/push-discipline.md) | `done push --pr-url <url> --head-commit <sha> --pr-base <ref>` |
| `merge-step` | Merge the named step's PR into the run branch, bottom of the stack first | [push-discipline.md](references/push-discipline.md) | `done merge-step --step <n> --merge-commit <sha>` |
| `integrate` | Open and merge one PR from the run branch into the base, then clean up and close any recorded task issue | [push-discipline.md](references/push-discipline.md) | `done integrate --pr-url <url> --merge-commit <sha> [--closed-issue-url <url>]` |
| `audit-verdict` | Max rounds hit with findings open | ask the user | `done audit --no-further-leads --reason ...` or `halt --reason ...` |
| `halted` | Report the reason; wait for the user | -- | `resume --note ...` when cleared |
| `done` | Final report | below | -- |

Read the named reference before working a phase for the first time in a run.
The receipt command is the boundary: if it exits non-zero, the phase is not
done -- fix what it complained about rather than arguing with it.

After a successful `done study` receipt, the study is the completed spec. If
the `labs_marketplace` receipt exists, perform the post-spec reassessment in
[wildcat-marketplace.md](references/wildcat-marketplace.md) before asking the
controller for the runbook directive. This is the first point at which a
missing marketplace plugin may be installed. Refresh skills only after all
selected installs finish; resume in a new chat when the host requires one.

## Phase notes

**Study and runbook.** `protasis` is the content authority: what a study must
answer, what a runbook step must contain, and when one topic needs decomposing
first. Fiat keeps the mechanics. The study goes to `.hexaemeron/study.md` and
the runbook to `.hexaemeron/runbook.md` beside `.hexaemeron/steps.json`, a JSON
list with one entry per step in order, as strings or `{"title": ...}` objects.
Run the `imprimatur` lint on each artefact before receipting it, and pass the
skills that ran to the receipt. Repo copies are committed later, in step 1 of
the runbook, after the prose pass.

**Implementation.** Pick the construction that takes the least effort to
comprehend, then stop. The step runs under the phase skills: `phylax` names
the boundaries the step introduces and the control each needs, `ephoros` names
what it must emit once it runs unattended, `metron` refuses any change made in
the name of speed without a recorded before and after, and a failure worked
mid-step follows `elenchus` rather than a guess. Their lints run in every
audit round, so meeting them here is cheaper than meeting them there. The runbook step is the yardstick: reread it before
declaring the step complete, and do not add anything it does not ask for.
The `implement` directive carries `branch` and `branch_from`: cut that exact
branch from that exact ref. Step 1 branches from the run branch, every later
step from the step below it, so each step builds on the reviewed tree of the
one before without waiting for a merge.

**Audit.** `elenchus` works any failure a round surfaces down to its cause.
The longest phase by design. One round is the full suite: `x-ray`
first, then `solidity-auditor`; when the step ships Solidity under Foundry or
Hardhat, `fizz` builds or refreshes the invariant fuzz suite and its campaign
results count as part of the round. Read each skill's SKILL.md from
`$PLUGIN_ROOT/skills/<name>/` and follow it. Every finding is logged
to the audit file, fixes committed to the stacked branch. Record the round even when it finds nothing.
Zero findings closes the loop; a genuine judgement that the remaining leads
are not worth another round closes it with `--no-further-leads --reason`.
Never report a round that did not run.

**Prose.** `hypomnema` decides what this step needs recorded and where it
goes, before the masks run. Every prose artefact in scope plus the PR title and
body, through
the `imprimatur` lint first and the `vulgate` mask second, content held
constant. Both are bundled: run the lint script by path, read the mask's
SKILL.md by path and apply it. The receipt refuses a skills list missing
either configured id.

**Push.** Stage and commit every intended final change, push the step branch,
and open its pull request against the `pr_base` the directive names, using the
prepared prose. Wait for its gates but leave it open: a step's work lands in the
integrate phase, not here. Do not add an issue reference unless one was
independently supplied or required by higher-priority repository policy. Receipt
the head SHA, PR URL, and PR base.

**Integrate.** Once every step is pushed, the stack comes down in order. Merge
step 1's pull request into the run branch, delete its branch, and let the next
step's pull request retarget onto the run branch; receipt each merge before
starting the next. With the stack landed, open one pull request from the run
branch into the recorded base, wait for its gates, merge it without bypassing
them, delete the run branch where policy allows, and close any recorded task
issue. That merge is the only one into the base for the whole run. A routine
publish or closure action is not a handoff to a human.

## Delegation and context

For long runs, hand research and implementation bulk to the bundled agents
(`surveyor`, `mason`) through the runtime's subagent mechanism, passing the
controller path, the state directory, and the current directive verbatim. If
the runtime has no subagent mechanism, perform the work in the main session
and keep the controller receipt as the boundary. Keep the audit and prose
phases in the main session when a delegated context cannot load the bundled
skills. After each `done push`, compact if the runtime supports it: the
receipts carry everything a fresh context needs.

## Stop conditions

Stop and ask the user when: `next` says `audit-verdict`; a push is rejected;
the security suite cannot be resolved for a Solidity repo; or `verify` fails.
Use `hexctl halt --reason ...` so the stop itself is on the ledger.

## Hard rules

- Never advance past a phase whose receipt command failed.
- Never reconstruct progress from chat; `status` and `next` are the truth.
- Never claim a lint, audit round, or test run happened when it did not.
- Never force-push over someone else's work or bypass a merge gate.
- Never target the base or the repository default branch with a step pull
  request, and never merge one during the steps; the stack lands in
  `integrate`.
- Never merge into the base more than once in a run, and never open a step
  branch straight off the base once a run branch exists.
- Never invent a branch name the controller did not give, and never name a
  branch after its number alone.
- Never call a plan or implementation complete while its own final changes,
  PR, task branch, or recorded issue still need routine stage, push, merge,
  deletion, or closure work.
- Never create a GitHub issue merely to satisfy this workflow.
- Never disclose a failed, unavailable, or inconclusive contributor check.
- Never install a wider-marketplace plugin before the study receipt exists.
- Never run or recommend a frontier Fiat job for a skill whose ledger is
  mature, or when a capable review finds no concrete material improvement.
- Never change a held `Next Fiat job` during a generation update; only clarify
  its context without changing its target or acceptance condition. An epoch
  may replace it only with the reopening evidence required by the ledger.

## Final report

When `next` returns `done`, run `hexctl status` and `hexctl verify`, then
hand over: topic, the run branch and the base it landed on, the step list with
each stacked PR URL and the order the stack merged in, the integration PR and
its merge SHA, audit rounds per step with the closing state of each, and where
the study and runbook live.
