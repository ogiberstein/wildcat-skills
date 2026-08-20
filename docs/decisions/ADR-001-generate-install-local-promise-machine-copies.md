# ADR-001: Generate install-local Promise Machine copies

## Status

Accepted, 2026-08-20. Superseded by a later numbered record once standalone
plugins can resolve a shared repository law without carrying their own bytes.

## Context

`PROMISE_MACHINE.md` is one authored suite law. Claude Code and Codex install a
plugin directory as an isolated package, so a standalone plugin cannot rely on
the repository root remaining beside it. Authoring a separate law in every
plugin would create 14 independent sources whose meaning and version could
drift.

## Decision

Author the law once at the repository root and generate one byte-identical
`plugins/<plugin>/PROMISE_MACHINE.md` copy at each fixed installation
destination. `scripts/promise_machine.py` refuses symlinks and paths outside
the repository, writes atomically, and checks every copy against the root.

Plugin runtime contracts link to their local copy. Repository-wide runtime
instructions link to the root. The same `promise-machine/v1` bytes therefore
govern both surfaces.

## Alternatives

- **Author a law per plugin.** This would make each plugin self-contained, but
  it would also make every copy an independent policy surface. It was rejected
  because structural similarity cannot prevent semantic drift.
- **Require standalone plugins to fetch the root law.** This would preserve one
  source, but it would add a network dependency and make offline installation
  incomplete. It was rejected because runtime policy must ship with the plugin.
- **Put the complete law in every `AGENTS.md`.** This would avoid another file,
  but any policy change would rewrite 14 runtime contracts and obscure their
  plugin-specific boundaries. It was rejected because generated policy and
  authored routing serve different purposes.

## Consequences

The root law is the only file contributors edit. A plugin-local edit fails the
copy check and is repaired by synchronisation. Standalone packages grow by one
small Markdown file. Changes to the root law deliberately change every plugin
package and therefore participate in the release/version checks introduced by
the Promise Machine runbook.
