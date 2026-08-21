---
name: fiat
description: >
  Run the one-shot delivery loop: study, runbook, then per-step
  implement/audit/prose/push until a working prototype exists.
  Use only when a Wildcat contributor explicitly asks to start, run, resume,
  or report a Hexaemeron or Fiat delivery, including /hexaemeron:fiat forms.
  Do not infer activation from a similar task.
metadata:
  version: "5.9.1"
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
Every state-backed command first validates the required version-1 container
spine in deterministic order. A missing or wrong-kind container stops with one
value-free path-and-kind diagnosis before a reader or writer can traverse it.

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
   treat the validated state file as canonical.
4. Otherwise: say exactly `Let there be light.` and nothing else before it,
   run the read-only preflight checks below, then bring the base up to date
   before anything is cut from it, then `hexctl init --topic "<topic>" --base
   <ref>`, record the post-init receipts, and enter the loop.
   `--base` defaults to `main`; honour any branch, repo, or commit the user
   named as the starting point. `init` also names the run branch, printed and
   held in state: one integration branch for the whole run, cut from the base.
   Create it before the first step (`git checkout -b <run branch> <base>`) and
   push it. Pass `--run-branch <name>` only when the user wants a different
   name than the topic slug.

**Sync the base first.** A run inherits every mistake in the ref it was cut
from, and a local checkout that has been sitting is the normal case rather than
the exception:

```text
git fetch origin
git status --short                     # must be clean
git checkout <base> && git merge --ff-only origin/<base>
git rev-parse HEAD                     # record this; it is the run's real start
```

Fast-forward only. If the base will not fast-forward, the local branch has
commits the remote does not, and that is a question for the user rather than
something to merge or rebase past on the way to starting work. If the tree is
dirty, stop: uncommitted work belongs to whoever left it there, and it would
otherwise ride into the first step's commit under this run's provenance. Cut the
run branch from the synced base, and state the starting SHA in the study's
constraints so the spec and the branch agree about where the run began. Skipping
this is how a study cites a starting ref that is a hundred commits behind the
work it is about to build on.

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
   versions or frontier text. The contract also states what every frontier run
   owes before it is recorded as done, whichever plugin the skill sits in; read
   it there rather than expecting the held job to spell it out.

**Make step 4 mechanical.** Name the ledger at `init` and the controller holds
the run to it:

```text
hexctl init --topic "<topic>" --base <ref> \
  --frontier plugins/<plugin>/skills/<skill>/EVOLUTION.md
```

`init` records that file's digest and row count, and `done integrate` refuses
until it carries exactly one new row valid under the versioning contract: the
axis arithmetic, the digest recomputed over the frontier line the row describes,
the header and the row naming the same version, a generation holding the prior
revision and digest, and a mature status carrying no next job. Each refusal names
which of those failed.

Pass it whenever the run is meant to advance a frontier. Leave it off for
ordinary delivery, where there is no ledger row to owe. If the job turns out not
to close after all, `hexctl halt --reason ...` puts that on the ledger; the gate
refuses a silent finish, not a recorded stop.

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
3. If `init` warns that this controller is older than a Fiat checked into the
   target repository, act on it before the run gets going: update the plugin,
   refresh through the host's own boundary, and re-resolve the paths, per
   [plugin-currency.md](references/plugin-currency.md). Where the update cannot
   happen, record the `controller_version` receipt that reference specifies and
   say so out loud. Do not run the loop under a controller you have noticed is
   behind and said nothing more about: the rules it does not enforce leave no
   trace, because a flag it rejects is indistinguishable from a rule nobody
   wrote.
4. The prose masks ship inside this plugin: the `imprimatur` lint (a script
   at `$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py`) and the
   `vulgate` voice mask (rules at `$PLUGIN_ROOT/skills/vulgate/SKILL.md`).
   Nothing to resolve.
5. The security suite is vendored in this plugin: the Pashov `x-ray`,
   `solidity-auditor`, and `fizz` skills sit under `$PLUGIN_ROOT/skills/`.
   After init, record the bundled ids:
   `hexctl record security_suite
   '["hexaemeron:x-ray","hexaemeron:solidity-auditor","hexaemeron:fizz"]'`.
   If the run will produce no Solidity and no suite applies, record a waiver
   instead: `hexctl record security_suite '"waived: <reason>"'` -- and say so
   out loud. Never claim a tool ran when it did not.
6. If the user supplied a task issue or a higher-priority target-repository
   rule required one, record its URL after init with `hexctl record task_issue
   '"<url>"'`. Do not invent an issue otherwise.
7. Nothing else.

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
| `audit-round` | One security round: run the suite, log, fix on the stacked branch | [audit-loop.md](references/audit-loop.md) | `audit-round --findings <n> [--log <path>] [--fixes-commit <sha>]`, plus `--phylax-exit`, `--ephoros-exit` and `--hypomnema-exit` on a non-Solidity round |
| `close-audit` | Last round was clean; close the phase | [audit-loop.md](references/audit-loop.md) | `done audit [--fixes-ref <ref>]` |
| `resolve-security-suite` | Suite receipt missing; resolve or waive | preflight step 4 | `record security_suite ...` |
| `prose` | Rewrite every prose artefact and draft the PR text | [prose-pass.md](references/prose-pass.md) | `done prose --files <n> --skills <csv>` |
| `push` | Stage and commit final changes, push the step branch, open its stacked PR against `pr_base`, and leave it open | [push-discipline.md](references/push-discipline.md) | `done push --pr-url <url> --head-commit <sha> --pr-base <ref>` |
| `merge-step` | Merge the named step's PR into the run branch, bottom of the stack first | [push-discipline.md](references/push-discipline.md) | `done merge-step --step <n> --merge-commit <sha>` |
| `sync-run` | When the base advanced and the integration PR conflicts, receipt one signed two-parent merge of the exact remote base tip into the completed run stack | [push-discipline.md](references/push-discipline.md) | `done sync-run --commit <sha> --base-commit <sha>` |
| `integrate` | Open and merge one PR from the run branch into the base, name what the run leaves unfinished in `.hexaemeron/run-pr.md`, then clean up and close any recorded task issue | [push-discipline.md](references/push-discipline.md) | `done integrate --pr-url <url> --merge-commit <sha> [--closed-issue-url <url>]` |
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

**Push.** Stage and commit every intended final change with a valid local
signature and the two exact provenance trailers, push the step branch,
and open its pull request against the `pr_base` the directive names, using the
prepared prose. Wait for its gates but leave it open: a step's work lands in the
integrate phase, not here. Do not add an issue reference unless one was
independently supplied or required by higher-priority repository policy. Receipt
the head SHA, PR URL, and PR base.

**Integrate.** Once every step is pushed, the stack comes down in order.
Retarget the next step's pull request onto the run branch, then merge this
step's, and delete no branch here; receipt each merge before starting the next.
Deleting a merged step's branch closes the pull request stacked on it, and a
closed pull request whose base ref is gone can be neither reopened nor
retargeted, so the order is not a preference. With the stack landed, open one
pull request from the run branch into the recorded base. If concurrent work
advanced the base and that pull request conflicts, merge the exact remote base
tip into the run branch once with a signed two-parent commit whose first parent
is the final recorded step merge, push it, require GitHub valid verification,
and receipt it with `done sync-run`; never rebase or rewrite the signed stack.
Then name everything the run
left unfinished in its body under `## Carried forward`, wait for its gates,
merge it without bypassing them, require GitHub to report `verified: true` and
`reason: valid` for every pushed commit and merge SHA, delete the run branch and the step branches
where policy allows, and close any recorded task issue. That merge is the only
one into the base for the whole run. A routine publish or closure action is not
a handoff to a human.

## Delegation and context

Every `next` envelope carries `state_sha256`, an explicit `agent`, and a
source-bound `brief`. Delegate the exact packet to `surveyor`, `mason`,
`warden`, or `scribe` when the runtime supports isolated agents. An inline
directive carries explicit null packet fields. Refuse an artefact whose digest
has drifted; do not reconstruct its study block, runbook step, risk register,
or sorted prose diff from chat. If delegation is unavailable, execute the same
packet in the main session. After compaction, rerun `next`: the receipted
artefacts and state digest deterministically reconstruct the packet.

## Stop conditions

Stop and ask the user when: `next` says `audit-verdict`; a push is rejected;
the security suite cannot be resolved for a Solidity repo; or `verify` fails.
Use `hexctl halt --reason ...` so the stop itself is on the ledger.

## Hard rules

- Never advance past a phase whose receipt command failed.
- Never reconstruct progress from chat; `status` and `next` are the truth.
- Never claim a lint, audit round, or test run happened when it did not.
- Never receipt a Fiat-created commit without a valid local signature and one
  exact copy of each provenance trailer. Never receipt a pushed commit or
  GitHub merge SHA unless GitHub reports `verified: true` and `reason: valid`.
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

## Promise Machine contract

### fiat-receipted-delivery

- Promise: A successful `hexctl verify` establishes that the controller state has the required version-1 container shape, the state and append-only ledger agree, and every recorded phase transition occurred in the required order with the required receipt shape.
- Evidence: The ordered state-container check, exact study and runbook receipts, step branches and locally verified commit ranges, GitHub-verified pushed commits and merge SHAs, audit rounds, prose and push receipts, hash-chained ledger, controller version and zero-exit verification result.
- Evidence classes: checked, recorded
- Boundary: Controller verification proves the required container shape, receipt order, integrity, and the recorded local and GitHub signature checks; it does not validate heterogeneous leaf values, prove a test summary, audit judgement, implementation claim, signer authority beyond those checks, or user authority merely written into a receipt.
- Authorises: Advancing only to the single next controller directive and reporting the recorded workflow state without strengthening any underlying receipt.
- Consequence: 2
- Refuses: Skipping a phase, reconstructing progress from chat, accepting a malformed or missing receipt, or describing an unrun check as complete.
- Recovery: Inspect `hexctl status`, repair the current phase's real evidence without editing ledger history, submit the required receipt and rerun `hexctl verify`.
- Exceptions: none

### fiat-final-integration

- Promise: A successful integration receipt establishes that every stacked step was merged in controller order, the run branch passed its required gates and exactly one recorded merge landed the run on the named base under the user's delivery authority.
- Evidence: The user's explicit Fiat request, green step and integration checks, stacked PR URLs, exact GitHub-verified pushed ranges, GitHub-verified merge-step and integration SHAs, final controller state and verified ledger.
- Evidence classes: checked, recorded
- Boundary: Integration establishes the recorded repository transition; it does not prove the software defect-free, make audit judgements independent or authorise a deployment, financial action or another repository.
- Authorises: Publication of the complete run to the named base and a final report limited to the merged artefacts and recorded evidence.
- Consequence: 3
- Refuses: Direct step merges to the base, bypassed gates, a second base merge, deletion that closes a stacked PR prematurely or integration without explicit delivery authority.
- Recovery: Leave the stack open, restore the required branch or check, retarget and merge in controller order, or halt with the exact blocker before any base mutation.
- Exceptions: none
