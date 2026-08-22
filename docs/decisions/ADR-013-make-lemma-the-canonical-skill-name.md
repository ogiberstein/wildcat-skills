# ADR-013: Make Lemma the canonical skill name

## Status

Accepted, 2026-08-22.

## Context

The Lemma plugin originally exposed its only canonical skill as `chunk`. That
made the qualified invocation `lemma:chunk`, while every other single-skill
plugin used the same name for the plugin, skill directory, frontmatter, and
ordinary invocation. The difference was an authoring mistake rather than a
meaningful boundary.

The mistaken name had spread into host prompts, routing, tests, coverage rows,
the evolution ledger, and repository prose. Keeping it for compatibility would
make every new user learn an exception and would leave automated discovery at
odds with the plugin's public name.

## Decision

Rename the canonical skill directory from `skills/chunk` to `skills/lemma`, set
the frontmatter name to `lemma`, and make the ordinary and qualified invocation
forms `$lemma` and `/lemma:lemma`.

The promise ids and the chunking commands remain unchanged because they name
operations and evidence, not the skill's discovery identity. The held frontier
also remains unchanged. The ledger records an epoch change because the old
invocation and path are deliberately incompatible, while the plugin package
receives its own patch-version increment for host distribution.

## Alternatives

- **Keep `chunk` as the canonical name.** This avoids a breaking invocation but
  preserves an accidental exception in every host and document.
- **Add `lemma` as an alias.** This would create two discovery identities for
  one implementation and make the Promise Machine's one-canonical-skill rule
  harder to explain and enforce.
- **Rename promise ids and executables too.** This was rejected because
  chunking is still the operation. Renaming those surfaces would add breakage
  without correcting another identity error.

## Consequences

Plugin, directory, frontmatter, router, host prompt, test, and documentation
names now agree. Existing requests that explicitly invoke `$chunk` or
`/lemma:chunk` must change to `$lemma` or `/lemma:lemma`.

The output schema, command-line tools, promise boundaries, and current frontier
do not change. A source reference to a chunk or chunker remains ordinary domain
language and is not renamed.
