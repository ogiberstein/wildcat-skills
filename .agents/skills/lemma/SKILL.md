---
name: lemma
description: Route Solidity or Markdown chunking to Lemma. Use it for validated, source-linked JSONL; do not use it to embed, index, retrieve or answer from those chunks.
---

# Lemma portable entrypoint

<!-- marketplace-context:start -->
## Scope

Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text.

**Use another tool when.** It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent.

**Current frontier.** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

## Authority

Read [the runtime contract](../../../plugins/lemma/AGENTS.md), then read and follow
[the canonical `chunk` skill](../../../plugins/lemma/skills/chunk/SKILL.md) in full.
Resolve relative paths from its directory. It wins if the two files disagree.

## Invocation

Use `/lemma:chunk` through the plugin or `$lemma` through host-neutral discovery.
