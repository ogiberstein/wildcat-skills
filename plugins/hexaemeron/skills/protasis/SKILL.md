---
name: protasis
description: >-
  Hold a Fiat study and runbook to a content contract before any code is
  written: stated assumptions, testable success criteria, a chosen design with
  its trade named, the five discipline questions answered before any build, and
  steps that are discrete, green at both ends, sized for the audit loop and
  explicit about the gates they incur. Use when a topic is about to enter the
  study or runbook phase, when a requirement arrives vague or bundles several
  capabilities, or when deciding whether a runbook is ready to build from. Do
  not use it to run the controller or write a receipt, which belong to fiat,
  and do not use it to record a decision after the fact, which belongs to
  hypomnema.
metadata:
  version: "2.1.0"
---

# Protasis

From *protasis*, the proposition laid down before the argument runs. Nothing is
built from a topic; things are built from a proposition about a topic.

## Where this sits

Protasis owns the content contract for the `study` and `runbook` phases: what
those two documents must answer before implementation is allowed to start. It
owns no state, writes no receipt and gates nothing itself.

**Use another tool when.** Fiat owns the controller, the artefact paths, the
receipts and the phase gate. `hypomnema` records a decision once it has been
made; protasis decides what has to be settled first. `elenchus` works a failure
you already have. `metron` supplies the measurement a performance criterion
needs.

Serves the `study` and `runbook` phases.

Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md).

Fiat's study and runbook phases run under this contract. Fiat keeps the
artefact paths and receipt commands; this skill says what the artefacts must
contain. Nothing else carries these rules.

## Refuse these four

1. No study, no runbook. A runbook derived from conversation instead of a
   written study is not a runbook.
2. No runbook, no implementation. A step that does not exist in the runbook
   does not get built, however small it looks.
3. No criterion, no success. A study whose success condition cannot be checked
   by a command or a named demo path is unfinished.
4. No stated assumption, no spec. Assumptions go on the page before the
   content they support.

Report a refusal in three parts: what is missing, where you looked, and the one
action that clears it. Say plainly that the phase is blocked rather than
in progress. None of the four is a suggestion to proceed carefully.

If the gap is an ambiguity rather than an absence, ask one literal question
instead of picking a reading.

## Assumptions go first

List what you are assuming before writing any spec content, and say plainly
that you will proceed on them unless corrected.

```
Assuming, unless corrected:
1. Foundry, not Hardhat; the repo has foundry.toml and no hardhat.config.
2. Solidity 0.8.x with checked arithmetic; unchecked blocks are opt-in per site.
3. Python 3.11 and stdlib unittest, matching every other plugin here.
4. An archive RPC is available for the capture step; without one, step 3 changes.
```

An unstated assumption is the failure this phase exists to catch. On the page,
a wrong one costs a sentence. Buried in step 4, it costs the step.

## Vague requirement, testable criterion

Restate the request as conditions a command can check, then confirm the
restatement before building on it.

```
Requirement: "make the harvester faster"

Restated:
- A full Ethereum USDC interval harvest finishes inside 20 minutes on a warm cache.
- The digest of the produced release is byte-identical to the current one.
- Peak resident memory stays under 2 GB.
Measured by metron, before and after. Are these the right targets?
```

"Faster", "cleaner", "more robust" and "production-ready" are not criteria.
Neither is a criterion that can only be checked by asking someone whether they
are happy.

## What a study must answer

1. **Problem statement.** What is being built, for whom, and what a working
   prototype means here. Name the demo path or the check that proves it.
2. **Prior art.** What exists already, in this repo, in the organisation's
   other repos, and outside. Name files, packages and standards by identifier.
3. **Constraints and non-goals.** The starting ref, toolchain and version pins,
   what the user ruled out, what is deferred past the prototype.
4. **Design options.** Two to four candidate constructions, each with the trade
   it makes. Pick one, say why. The pick is the option cheapest to comprehend
   that still meets the problem statement.
5. **Risk register seed.** What the audit loop should look hardest at. In
   Solidity: trust boundaries, external calls, arithmetic, upgrade paths, key
   custody. In Python: untrusted input, subprocess and filesystem handling,
   secret material, partial writes, and what happens when a long run is killed
   halfway.
6. **Glossary seeds.** Terms the runbook and implementation will reuse, one
   line each.
7. **Sources.** Enough of a pointer to find each one again.

The five that follow are the disciplines the build will be held to. Answering
them here costs a sentence each; leaving them to the audit loop costs a step.

8. **Signals, and the questions behind them.** Two to four questions someone
   will ask at three in the morning once this runs unattended, and which steps
   emit the signals that answer them.
   [ephoros](../ephoros/SKILL.md) owns what a signal must carry.
9. **Boundaries, per capability.** Each boundary this opens, what is worth
   taking at it, and the control that closes it. This feeds item 5 rather than
   replacing it. [phylax](../phylax/SKILL.md) owns the boundary list and the
   controls.
10. **The budget, or its absence.** Any performance budget this must hold, with
    the exact command that measures it.
    [metron](../metron/SKILL.md) owns what a budget carries and how it is
    checked.
11. **The fail-closed posture.** What stops the run, and the guard-test
    convention a fix will follow.
    [elenchus](../elenchus/SKILL.md) owns the triage order and the guard rule.
12. **Decisions and their homes.** The decisions expected to be expensive to
    reverse, and the file each record will live in.
    [hypomnema](../hypomnema/SKILL.md) owns which decisions earn a record and
    where each one lives.

For items 8 through 12, "none, and here is why" is a complete answer. A lint
invoked from a terminal has no on-call question; a step that reads two files
has no budget. What is not a complete answer is silence, because silence cannot
be told apart from not having looked.

Cite those five contracts, never restate them. Each owns its own rules and each
evolves on its own ledger, so a copy here is stale the moment it is written.

A section reading "TBD" is a section to fill or cut. Where the request is
ambiguous, record the reading you chose and the reason for it. Never resolve an
ambiguity silently.

## What a runbook step must contain

A step is discrete: one pull request, one boundary. It is self-contained, so
someone holding only the study, the runbook and the repo at that step's entry
state can finish it. Both ends are green; no step hands the next a broken tree.
And it stays small enough to audit, because that phase dominates the clock.

```markdown
## Step N: <title>

**Goal.** One sentence.
**Entry.** The exact ref or state this step starts from.
**Exit.** Deliverables, plus the command or test that proves them.
**Files.** Paths created or changed.
**Tests.** What gets written or extended, and the expected count if known.
**Disciplines.** Which of the five apply to this step and why, or none with
the reason.
```

The Disciplines line carries the study's items 8 through 12 down to the step
that actually incurs them. Name each discipline and the reason in one clause:

```text
**Disciplines.** phylax: this step opens the ingestion path. ephoros: it runs
unattended once deployed. metron: none, no performance claim. elenchus: none,
no failure in hand. hypomnema: the storage format is expensive to reverse.
```

A step that names a discipline without a reason has not answered; a step that
omits one has not been asked. Mason builds against the declared gates and
warden audits against them, so a gate named here is cheaper than the same gate
discovered in round three.

Three fixed points. Step 1 scaffolds: layout, toolchain pins, CI stub, licence,
and committed copies of the study and runbook. The last step demonstrates, by
running the demo path from the problem statement. Ordering is dependency order,
and a step may assume every earlier step's exit state and nothing else.

If a step's exit cannot be proved by a command, it is not an exit. "Reviewed",
"working" and "integrated" prove nothing on their own.

## When one topic is several

Most topics are one capability and go straight to the study. Decompose first
only when a single request bundles capabilities that could ship and be verified
separately, or when one could be cut without rewriting the others.

The decomposition is a table and a build order, not a project plan:

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| capture | Fixed-block RPC capture, digest-keyed | none |
| verify | Proof checks over a capture | capture |
| replay | Local replay boundary, no fallback | capture |
| fixture | Published fixture and its manifest | verify, replay |

Build order: capture, then verify and replay, then fixture.

Module ids are kebab-case, chosen once, never renamed mid-topic. Dependencies
point one way; if two modules each need the other, they are one module. An
interface belongs in the spec of the module that provides it. Each module then
gets its own study, and its modules become runbook steps in that order.

## Boundaries the study must state

Three tiers, each with concrete entries:

- **Always.** Both test suites before a commit. The imprimatur lint on every
  shipped document. A recorded measurement before any performance change.
- **Ask first.** Adding a dependency. Changing a storage layout or a public
  ABI. Touching CI. Widening a trust boundary. Rewriting a released digest.
- **Never.** Commit key material or an RPC credential. Edit a vendored
  directory. Delete a failing test to make a suite pass. Claim a command ran
  when it did not.

## The spec stays alive

When a decision changes, change the study first and the code second. When scope
moves, say so on the page. Both documents are committed and reviewed like any
other shipped artefact, and both go through the prose pass first.

## Rationalisations

- "This is simple, it needs no spec." Simple topics need short specs, not none.
  Two lines and a checkable criterion is a spec.
- "I will write the study afterwards." Then it is documentation. The value here
  is forcing clarity before the code exists.
- "A spec slows us down." Fifteen minutes of study against hours of rework in
  the audit loop, which is the phase that already dominates the clock.
- "Requirements will change anyway." Which is why the study is edited rather
  than abandoned.
- "The user knows what they want." Every clear request carries implicit
  assumptions. This phase exists to surface them.
- "It is one feature, splitting it is overhead." If its criteria cluster into
  separately verifiable groups, every later step has to reason over the whole
  contract. A four-row table is cheaper.
- "I will decompose while planning." Planning slices steps inside a study.
  Module boundaries have to be settled before the study is written, not after.

## Red flags

- Code before any written requirement.
- Asking whether to start building before "done" has been defined.
- A step in flight that appears in no runbook.
- A design decision made and not written down.
- One study whose criteria span capabilities that could ship separately.
- Build order settled implicitly during implementation.

## Before the runbook is receipted

Report the count, then name every failure. A set reported as passed without the
count is not a report.

- [ ] The study answers all twelve items.
- [ ] Items 8 through 12 each carry an answer or a stated none with its reason.
- [ ] No discipline core is restated where a citation belongs.
- [ ] Assumptions are on the page and were confirmed or corrected.
- [ ] Every success criterion names a command, a test or a demo path.
- [ ] The chosen design says what it traded away.
- [ ] Always, ask-first and never each carry concrete entries.
- [ ] Each step carries goal, entry, exit, files, tests and disciplines.
- [ ] Every discipline a step names carries the reason it applies.
- [ ] No exit rests on anything but a command.
- [ ] Step 1 scaffolds and the last step demonstrates.
- [ ] Steps are in dependency order.
- [ ] If the topic was decomposed, every step traces to a module id.

## Hand back

Lead with the state: ready to build, or blocked on a named gap. Then give the
count of checks passed out of the total, and name each one that failed.

Keep three things apart. What the study establishes, what it assumes, and what
could not be settled. An assumption that changes the build order or the chosen
design gets said out loud, not buried in a section.

End with one action, and make it something the reader can do in a couple of
minutes: confirm an assumption, answer one question, or approve the runbook.
Name the open question rather than closing it with a guess. Corrected here, an
assumption costs a sentence. Found in the audit loop, it costs a step.
