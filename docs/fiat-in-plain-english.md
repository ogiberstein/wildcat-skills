# Fiat in plain English

Fiat is the controller. It asks what happens next, gives that work to a named
agent when one applies, checks the result, and records a receipt. An agent
cannot advance the run or approve its own output.

## The whole run

| Phase | Who does the work | What comes back | Who advances the run |
| --- | --- | --- | --- |
| Study | Surveyor | Problem, options, risks, chosen design | Fiat |
| Runbook | Fiat, under Protasis | Small implementation steps and tests | Fiat |
| Implement | Mason | Code, tests, commit and deferred items | Fiat |
| Audit | Warden | Findings, fixes and audit log | Fiat |
| Prose | Scribe | Checked documentation and PR text | Fiat |
| Push | Fiat | Pushed branch and stacked PR | Fiat |
| Integrate | Fiat | Ordered step merges and one merge into the base | Fiat |

```text
You give Fiat a task
        |
Surveyor studies it
        |
Fiat writes the runbook under Protasis
        |
Mason implements one step
        |
Warden audits that step until the round closes
        |
Scribe checks the documentation and PR text
        |
Fiat pushes the step and opens its stacked PR
        |
Repeat for every runbook step
        |
Fiat merges the stack in order, then merges once into the base
```

## The four named agents

### Surveyor

Surveyor handles the study. It receives the topic, target repository, base ref
and output path. It writes a buildable description of the problem, the design
options, the chosen design and the risks that the audit should inspect.

Surveyor cannot record its own receipt or move Fiat to the runbook.

### Mason

Mason implements exactly one runbook step. It receives the complete step, the
branch name and the ref from which that branch must start. It writes the code
and tests, commits the work, then reports the branch, commit SHA, test command,
pass count and any deliberate deferral.

Mason cannot push, open a PR, merge or change Fiat's controller state.

### Warden

Warden runs exactly one audit round on one step. It runs the configured
security suite, writes every finding to the audit log and commits any fixes.
It reports the finding count, fixes commit and log path.

Warden cannot call a round clean if a required audit tool did not run.

### Scribe

Scribe handles the prose phase for one step. It checks every changed prose file
and the PR title and body. It runs Imprimatur, applies Vulgate without changing
the facts, then runs the lint again.

Scribe cannot invent an issue reference or record its own receipt.

## Skills used inside the phases

These are rule sets, not top-level Fiat agents.

| Skill | Phase | Question it answers |
| --- | --- | --- |
| Protasis | Study and runbook | Is the specification complete enough to build? |
| Phylax | Implement | Are external inputs, commands, secrets and dependencies controlled? |
| Ephoros | Implement | What logs, metrics, traces and alerts must the step emit? |
| Metron | Implement | Was a performance change measured before and after? |
| Elenchus | Implement and audit | Was a failure traced to its cause and guarded by a test? |
| Hypomnema | Prose | What decisions and operational knowledge must be recorded? |
| Imprimatur | Prose | Does the text contain configured machine-writing patterns? |
| Vulgate | Prose | Can the wording be made plain without changing its meaning? |

## Agents inside the Solidity audit tools

Warden may run larger internal teams when a step contains applicable Solidity.
They do not control Fiat and they do not run for non-Solidity work.

Solidity Auditor uses twelve specialist roles: Access Control, Asymmetry,
Boundary, Economic Security, Execution Trace, First Principles, Flow Gap,
Invariant, Math and Precision, Numerical Gap, Periphery and Trust Gap.

Fizz can use Conservation Auditor, Round-Trip and Rounding Analyst, State
Transition Mapper, Adversarial Profit Maximizer, Protocol-Type Specialist,
Property Synthesizer, Global Property Implementer, Specific Property
Implementer and Report Writer. A Protocol Analyzer may run when the usual
protocol analysis is unavailable.

## What keeps the agents bounded

Each named agent receives a source-bound brief and must return a named
artefact. Only Fiat can accept that result and submit the controller receipt.
If the receipt fails, the phase remains open.

Fiat also owns branch creation, pushes, PRs, ordered merges and the final
status report. Small tasks may run directly in Fiat's main context instead of
a subagent, but the role, checks and receipt stay the same.

