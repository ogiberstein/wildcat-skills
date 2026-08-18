# Sapheneia

<!-- marketplace-context:start -->
## In one line

Sapheneia shapes the agent's own interaction with an AuDHD reader: the action, meaning, working state and evidence stay visible from turn to turn.

**Try something else when.** Use Imprimatur to inspect prose for banned machine-writing patterns, and use Vulgate or another voice mask to change register. Sapheneia governs interaction shape; it does not diagnose the reader or choose a house voice.

**Current frontier.** Cross-model behaviour has not yet been held against a published AuDHD task corpus.

**Next Fiat job.** Use /hexaemeron:fiat to build and publish a held cross-model corpus covering debugging, explanation, destructive-action and long-running task turns, then reconcile the ten rules against its results. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Sapheneia is the interaction contract for agents working with AuDHD engineers.
It keeps the next action, task boundary, done condition, current state, evidence
and unknowns on screen.

The skill applies to the agent itself. Once active, it shapes commentary,
questions, progress reports, errors and final replies until the reader turns it
off. It does not diagnose anyone, and a reader's stated preference wins.

The ten ranked rules and the complete activation contract live in
[`skills/sapheneia/SKILL.md`](skills/sapheneia/SKILL.md).

#### Day to day

**Developers.** A coding task spans several turns and the current step keeps
falling out of view. Sapheneia keeps one step active, states what changed and
what was verified, and ends with one next action.

**Security and audit.** A finding mixes observed behaviour, inference and an
untested assumption. Sapheneia labels each one and keeps the risk-bearing
qualification attached to the decision it changes.
## How it works

The contract sits upstream of whatever the agent is producing. It applies to
commentary, progress updates, questions, errors and final replies for the rest
of the session once selected. It does not diagnose the reader, and it yields
as soon as the reader states a different preference.

The ten rules are ranked. The first line carries the action or finished result;
asks are literal and labelled; multi-step work has one active step; facts,
assumptions and unknowns stay separate; and unfinished work ends with one next
action. Imprimatur remains the prose lint, and a voice mask remains responsible
for register.

## What it ships

- one canonical [`SKILL.md`](./skills/sapheneia/SKILL.md) shared by Codex, Claude Code and portable agents;
- an agent-facing runtime contract that makes the agent itself the subject;
- contract tests that hold the ranked rule count, persistence language, host descriptions and portable links together.

