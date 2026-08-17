---
name: lemma
description: Route Solidity or Markdown chunking to Lemma. Use it for validated, source-linked JSONL; do not use it to embed, index, retrieve or answer from those chunks.
---

# Lemma portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text.

**Use another tool when.** It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent.

**Current frontier.** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

Read [the Lemma runtime contract](../../../plugins/lemma/AGENTS.md), then read
[the canonical `chunk` skill](../../../plugins/lemma/skills/chunk/SKILL.md) in
full and follow it. Resolve every relative path from the canonical skill's
directory. The canonical file is authoritative if this entrypoint and it ever
disagree.

`/lemma:chunk` is the plugin-qualified invocation. `$lemma` remains the
host-neutral entrypoint for agents that discover this portable skill.
