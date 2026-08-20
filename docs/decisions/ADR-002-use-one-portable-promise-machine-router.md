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

## Consequences

Host-neutral discovery gains one extra selection hop. In return, there is one
portable identity to keep current, while plugin and canonical contracts remain
authoritative. Existing slash, dollar-prefixed and plugin-qualified invocation
aliases remain aliases; they do not require shadow skill files.

Rollback restores the removed entrypoints from Git, removes the suite router
and reverts the root discovery prose and tests in the same change. A partial
rollback is invalid because it would recreate competing identities.
