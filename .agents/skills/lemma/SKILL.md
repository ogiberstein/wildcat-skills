---
name: lemma
description: Route Solidity or Markdown chunking requests to the canonical Lemma instructions. Use when the user names Lemma, asks to turn solc standard JSON input or Markdown documents into source-linked JSONL, or needs citation-aware retrieval chunks. Lemma does not embed, index, retrieve, or answer from chunks.
---

# Lemma portable entrypoint

Read [the Lemma runtime contract](../../../plugins/lemma/AGENTS.md), then read
[the canonical `chunk` skill](../../../plugins/lemma/skills/chunk/SKILL.md) in
full and follow it. Resolve every relative path from the canonical skill's
directory. The canonical file is authoritative if this entrypoint and it ever
disagree.

`/lemma:chunk` is the plugin-qualified invocation. `$lemma` remains the
host-neutral entrypoint for agents that discover this portable skill.
