# ADR-002: Use one portable Promise Machine router

## Status

Accepted, 2026-08-20.

## Context

The repository exposed 20 host-neutral entrypoints beside 28 canonical skills.
Those entrypoints repeated selection and frontier prose, so discovery could
present a portable copy and an installed plugin as separate behavioural
identities. A host-neutral agent still needs one stable place to begin.

## Decision

`.agents/skills/` contains one `promise-machine` router. It reads the root
runtime contract, selects one of the 14 plugin runtime contracts and lets that
contract identify one canonical `SKILL.md`. The router has no behavioural
version and owns no domain promise. Package versions remain in plugin manifests;
skill versions remain in canonical frontmatter and evolution ledgers.

The Claude and Codex marketplaces continue to expose all 14 installable
plugins. Horos is added to the Codex marketplace so both host sets are explicit
and equal.

## Alternatives

- **Keep the 20 host-neutral entrypoints.** Each repeated selection and
  frontier prose beside its canonical skill, so discovery could present a
  portable copy and an installed plugin as separate behavioural identities,
  and every copy was one more surface to keep current. It lost to a single
  identity with one selection hop.
- **Retain every entrypoint, generate it from its canonical definition and
  declare which source wins.** This preserved direct discovery, but it
  depended on source precedence that neither Codex nor the Agent Skills
  specification documents, and it left two visible entries in the
  demonstrated Codex surface.
- **Remove the host-neutral surface entirely.** This closed the duplicate
  identities at the smallest cost, but a host-neutral agent still needs one
  stable place to begin, and deleting the surface would have left none.

## Consequences

Host-neutral discovery gains one extra selection hop. In return, there is one
portable identity to keep current, while plugin and canonical contracts remain
authoritative. Existing slash, dollar-prefixed and plugin-qualified invocation
aliases remain aliases; they do not require shadow skill files.

Rollback restores the removed entrypoints from Git, removes the suite router
and reverts the root discovery prose and tests in the same change. A partial
rollback is invalid because it would recreate competing identities.
