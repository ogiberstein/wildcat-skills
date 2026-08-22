# hexaemeron

<!-- marketplace-context:start -->
## In one line

Hexaemeron runs an explicit, receipted delivery loop, and every skill it uses answers on its own: fuzzing, audit-readiness and security review, prose lint and voice, and the specification, debugging, hardening, telemetry, measurement and record-keeping skills the loop holds each phase to.

**Current frontier.** The bundled Solidity audit suite has not yet been exercised in a published end-to-end Fiat delivery.

**Next Fiat job.** Use /hexaemeron:fiat to run and publish the first Solidity delivery that exercises the bundled x-ray, solidity-auditor and fizz loop end to end, recording every round and closing state. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Let there be light.

One command that takes a topic from nothing to a working prototype:
study, runbook, then for each runbook step the simplest implementation that
satisfies it, a security loop that runs until clean or
reasoned out, a prose pass in the house voice, and a reviewable pull request.
The steps stack; the stack lands on the base in one merge. Every phase
leaves a receipt in a hash-chained ledger, so the run survives context
resets, crashes, and week-long pauses -- resume is the same command.

Named for the six days of ordered creation from a void to finished work,
then rest. The entry skill is `fiat`, so the invocation is
`/hexaemeron:fiat` and a fresh run's first words are the line above.

## How it works

Let there be light. A deterministic controller (`hexctl`) decides what comes next and refuses to advance without a receipt; state and a hash-chained ledger survive context resets, so resume is the same command.

1. Study the topic and write a linted study file.
2. Derive a runbook of discrete, self-contained steps.
3. Implement the least complicated construction that satisfies each runbook step.
4. Run the vendored Pashov suite (`x-ray`, `solidity-auditor`, `fizz`) in rounds until a round comes back clean or the remaining leads are judged not worth another pass, fixes on a stacked branch.
5. Rewrite every shipped document and the PR text through the bundled `imprimatur` lint and `vulgate` voice mask.
6. Push the step branch, open its pull request against the step below it, and move to the next step.
7. Once every step is pushed, merge the stack into the run branch in order, receipt one signed base sync if concurrent work created an integration conflict, then merge the run branch into the base once.

A run works on one integration branch cut from the base. An issue-free run uses
`fiat/<run slug>`. When a known task issue is supplied during initialization,
the branch uses `fiat/<issue>-<run slug>` and every step branch keeps that
prefix. Each step's pull request targets the step below it, step 1 targets the
run branch, and nothing merges until the whole stack is ready. The base sees
exactly one merge per run.

## What it ships

- the executable [`hexctl.py`](./skills/fiat/scripts/hexctl.py) controller with a tamper-evident ledger (`verify` proves both chain and state);
- the [`imprimatur`](./skills/imprimatur) three-tier prose lint and the [`vulgate`](./skills/vulgate) voice mask, invokable on their own;
- [`kronos`](./skills/kronos), which ranks eligible held frontier jobs and loops complete Fiat runs until none remain;
- six more skills holding each phase to a standard, six of them with an executable check: [`protasis`](./skills/protasis) on what a study and runbook must answer, [`elenchus`](./skills/elenchus) on the root cause of a failure that already happened, [`phylax`](./skills/phylax) on the off-chain surface, [`ephoros`](./skills/ephoros) on what a step emits once it runs unattended, [`metron`](./skills/metron) on every measurement except gas, and [`hypomnema`](./skills/hypomnema) on what gets recorded and where;
- the Pashov Audit Group suite vendored verbatim (MIT; `LICENSE` and `NOTICE.md` in each skill directory);
- Codex metadata for explicit or automatic invocation; and
- the controller, contract, practice-check and lint test suite, plus a fuzz-audit log ([`audit/AUDIT.md`](./audit/AUDIT.md)) covering the controller's own surfaces.

## Day to day

**Developers.** A half-formed idea and a week to find out whether it holds. Hexaemeron turns it into a study, a runbook of discrete steps, and one pull request per step. Each directive carries a source-bound agent packet; each Fiat-created commit is verified locally, and pushed ranges and merge SHAs must carry GitHub's valid verification before their receipts advance.

**Security and audit.** You want the Pashov suite over a contract and nothing else. `x-ray`, `solidity-auditor` and `fizz` are vendored whole and run on their own, without taking on the loop around them.

**Marketing.** A launch post reads like a machine wrote it. `imprimatur` says what is wrong with it across three tiers and `vulgate` rewrites it in house voice. Neither needs the controller, and neither needs installing separately.

**Business development.** An integration document has to be accurate about what the protocol does and readable by someone who is not an engineer. The study phase produces the first and the prose masks produce the second.

## The shape of a run

| Day | Phase | What happens |
| --- | --- | --- |
| 1 | `study` | Study the topic; write `.hexaemeron/study.md` to `protasis`'s contract, linted |
| 2 | `runbook` | Divide the work into steps that meet `protasis`'s schema: discrete, self-contained, provable exits |
| 3-4 | `implement` | Build the step, least mental load that satisfies the runbook |
| 5 | `audit` | The vendored Pashov suite in rounds until clean or reasoned out; non-Solidity rounds run the `phylax`, `ephoros` and `hypomnema` lints; fixes on a stacked branch |
| 6 | `prose` | `hypomnema` decides what gets recorded, then the `imprimatur` lint and the `vulgate` mask, on every document and the PR text |
| rest | `push` | Stage and commit the final diff, push the step branch, and open its stacked pull request |
| -- | `integrate` | Merge the stack into the run branch in step order, then the run branch into the base once, and close the task issue |

Days 3 through the rest repeat per step. The sixth day makes the prose in
a human image, which is roughly the joke the name is carrying.

## Usage

```text
/hexaemeron:fiat "borrowing-base covenant hook for V2.5"   # start
/hexaemeron:fiat --base release/v2.5 "..."                  # start from a ref
/hexaemeron:fiat --task-issue https://example.test/issues/438 "..." # bind a known issue
/hexaemeron:fiat                                            # resume
/hexaemeron:fiat status                                     # report
/hexaemeron:kronos                                          # rank and run frontier jobs until none remain
```

Kronos is the small loop around Fiat. It scores every eligible held frontier
out of 100, sends the best one through a complete Fiat run, then ranks again.
The name carries the old Kronos/Chronos knot: sickle for the ripest job, clock
for keeping the sequence moving.

> Highest first, then Fiat runs.
>
> Kronos cuts till work is done.

The run stops on its own only for a decision that belongs to a human: the
audit loop hit its round cap with findings still open, a push was
refused, or a Solidity repo is missing its security-suite receipt.
Everything else proceeds.

## The controller

`skills/fiat/scripts/hexctl.py` sequences the run. The model does the work;
the controller decides what comes next and refuses to advance without a
receipt. State sits in `.hexaemeron/` (self-gitignored) beside an
append-only ledger where every entry hashes over the one before it. Before any
state-backed command reads further, the controller checks the required
version-1 container spine in deterministic order and refuses a missing or
wrong-kind container with a value-free path-and-kind diagnosis.

```text
hexctl init --topic <topic> [--task-issue <url>]  # start; bind a known issue before branch creation
hexctl next                 # the single next action, as JSON
hexctl status [--json]      # where the run is
hexctl done <phase> ...     # receipt a phase; validation lives here
hexctl audit-round ...      # record one security round
hexctl record <key> <val>   # named receipts (resolved suite, run context)
hexctl halt / resume        # put a stop itself on the ledger
hexctl reset                # archive a completed run and clear active state
hexctl verify               # check state shape, then prove chain and state integrity
```

`init --task-issue <url>` stores the exact issue URL in the initial transition
and puts its positive issue number first in the automatic run branch. The
complete issue-bearing slug keeps the existing 48-character limit. An exact
override must start with `fiat/<issue>-`. A late first issue receipt is refused
rather than renaming a stored branch; issue-free and legacy names stay
unchanged.

Mutating commands hold a kernel lock for their whole run. A second writer is
refused with the first process's details and a worktree command; `next`,
`status`, and `verify` still answer. The operating system releases the lock if
the holder crashes, so a stale metadata file never needs manual cleanup.

The receipts are opinionated where the process is: the audit phase will not
open without a resolved (or explicitly waived) security suite; it will not
close with findings open unless a reasoned no-further-leads verdict is
recorded; a prose receipt missing either configured skill is rejected; and a
push receipt requires the final head and a pull request aimed at the step below
it in the stack, and refuses a merge commit outright. Merges are the integrate
phase's business: the controller hands them out one step at a time, in order,
and the run is not done until the run branch has landed on the base and any
recorded task issue is closed. Fiat creates no GitHub issue unless the user or
target repository requires one.

## Skill versions and the stopping rule

The first-party Fiat, Imprimatur, Vulgate, and Kronos skills keep an
`EVOLUTION.md` ledger beside `SKILL.md`. Labels use
`{skill}-v{evolution}.{generation}.{epoch}`: evolution counts completed
frontier advances, generation counts meaningful behavioural changes, and
epoch marks a rare compatibility or provenance boundary. These are governed
by `skills/VERSIONING.md`; they are not SemVer and do not change invocation
names.

A held Next Fiat job changes only after that exact frontier job completes.
Once a capable review finds that another pass has no concrete chance of
material improvement, the ledger becomes `mature`, its next job becomes
`None -- mature`, and Fiat refuses further frontier runs. A different rewrite
or another model's curiosity is not grounds to keep seasoning it.

## Configuration

Per-run, via `hexctl config set <path> <value>`:

| Path | Default | Meaning |
| --- | --- | --- |
| `skills.prose_lint` | `hexaemeron:imprimatur` | Bundled lint the prose receipt demands |
| `skills.voice` | `hexaemeron:vulgate` | Bundled voice mask the prose receipt demands |
| `skills.security` | the vendored Pashov ids | Intent only; the ids the `security_suite` receipt records at preflight |
| `audit.max_rounds` | `8` | Rounds before the controller forces a verdict |
| `audit.stacked_suffix` | `--audit` | Fix branch: `<step-branch>--audit` |
| `audit.fold` | `false` | Merge the stacked branch into the step branch on close |
| `audit.log_path` | `audit/AUDIT.md` | Where rounds append |
| `git.base` | `main` | Starting ref, and the only branch a run merges into |
| `git.run_branch_prefix` | `fiat/` | Run branch is this plus the topic slug, or `<issue>-<topic slug>` when `init --task-issue` binds a known issue; an exact override must keep that issue prefix |

The Pashov suite -- `x-ray`, `solidity-auditor`, and `fizz` -- is based on
https://github.com/pashov/skills tag `v28062026` under the MIT licence. Each
`NOTICE.md` records the local distribution changes. The copies keep their
upstream instructional register; Wildcat's house prose lint does not rewrite
third-party source solely for style. Credit: Pashov Audit Group,
https://www.pashov.com/. Preflight records the bundled ids in the
`security_suite` receipt; the controller gates on the receipt, not the config,
so a stale config cannot fake a suite. Prose-free or Solidity-free runs record
a waiver instead.

## The skills each phase is held to

Six skills carry the standards each phase is held to, and each runs on its own
outside the loop. `protasis` says what a study and a runbook must answer.
`elenchus` works an observed failure down to its cause and guards it.
`phylax` holds the off-chain surface: input, subprocesses, fetched hosts,
secrets, dependencies and model output. `ephoros` chooses what a step emits
once it runs unattended. `metron` refuses a performance change without a
recorded before and after. `hypomnema` decides which decisions earn a written
reason and where each record lives. Each carries its own `EVOLUTION.md`, so
Kronos ranks their frontiers alongside the rest.

## The prose masks

Everything the loop needs ships in the plugin; it stands alone. The two
prose masks are vendored, not referenced: `imprimatur` (a three-tier lint
over the tells that mark prose as machine-written) and `vulgate` (a voice
mask that renders text into a plain human register) live under `skills/`
and can be invoked on their own, outside the loop, whenever a draft needs
the treatment. Edit the lexicon in place when a term needs adding.
Upstream attribution for the absorbed lint material sits in
`skills/imprimatur/NOTICE.md`. Fiat never bypasses a gate, but once the gates
pass it merges its own PR and closes its own task issue rather than leaving
routine publication work behind.

## Agents

Four subagents for context isolation on long runs: `surveyor` (the study),
`mason` (a step's implementation), `warden` (one audit round), `scribe`
(the prose pass). The old caveat about skills not
resolving inside subagents is gone on both fronts: the prose masks and the
security suite are files inside the plugin, reachable from any context by
path, so the warden and scribe always have their tools.

## Tests

```text
python3 tests/run_tests.py
```

The tests cover the controller and Fiat contract: phase ordering, ordered
state-container validation, completed run archival and reset, audit gating and
round caps, fixes evidence, prose skill enforcement, halt/resume, ledger
tamper detection, concurrent writer exclusion, crash recovery, and the
Wildcat marketplace boundary.
