# ADR-011: Load one Shoggoth identity contract at each operating entry

## Status

Superseded, 2026-08-23. [ADR-014](ADR-014-attribute-governed-agent-work-to-shoggoth.md)
retains its single-contract placement and replaces its communication-only
boundary.

## Context

People joining the project need a durable way to address the agents and skills
as individuals and as one collective. Conversation memory carried the terms,
but it was local to one installation and could identify the Creator more
personally than the shared contract should. A global Codex `AGENTS.md` would
still belong to one machine. It would not travel with a clone, an installed
plugin, or the Shoggoth Interceptor.

The skills repository and the Interceptor are separate operating entries. The
first is where the collective originates and evolves. The second applies the
same collective to external repositories while retaining its own authority and
evidence limits. Target repositories remain outside both instruction trees.

## Decision

`SHOGGOTH.md` in the skills repository is the canonical identity contract.
The root `AGENTS.md` requires agents in this repository to read it, and the
root README points people to it. The Interceptor carries a byte-identical,
source-bound copy with the same contract identity; both its `AGENTS.md` and
`CLAUDE.md` require that copy before work begins. Identity terms change address
and communication only. They never activate a skill or widen authority.

## Alternatives

- **Keep the definition in conversation memory.** This follows one person
  between tasks without changing either repository. It lost because another
  contributor, machine, or clean installation would not receive it, and local
  retention should not be the public source for a shared identity.
- **Put the definition only in a global `AGENTS.md`.** Codex can load that file
  for every repository on one machine. It lost because the file does not travel
  with a clone, does not configure other hosts, and would mix Wildcat identity
  into unrelated work that never invoked the collective.
- **Repeat the definition in every `SKILL.md`.** Every selected member would
  carry the wording directly. It lost because selection happens after startup,
  vendored skills must remain unchanged, and many copies would turn one
  definition into a recurring drift problem.
- **Install instructions into each target repository.** The Interceptor could
  place an `AGENTS.md` beside the code it works on. It lost because target
  instructions belong to the target's maintainers, and an external harness
  must not rewrite them to explain itself.

## Consequences

Contributors can learn the shared names from the repository before speaking to
an agent. Codex receives the definition from `AGENTS.md`; the Interceptor's
existing host receives it from `CLAUDE.md`. The Interceptor copy names the
canonical source and contract identity, and its tests pin the accepted bytes,
so an edit is deliberate and reviewable.

The two repositories still require a coordinated change when the identity
contract evolves. The contract identifier changes with its meaning, the
Interceptor copy is replaced from the canonical bytes, and both repositories'
checks must pass. No target repository is modified, and no identity wording
can supersede a permission or evidence gate.
