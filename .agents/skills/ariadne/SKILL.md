---
name: ariadne
description: Route a request about release evidence statements to the canonical Ariadne instructions. Use when the user names Ariadne, hands over an attestation and asks what it covers, or wants a release bound to the build, test, review and deployment evidence behind it. Ariadne neither signs nor verifies signatures.
---

# Ariadne portable entrypoint

Read [the Ariadne runtime contract](../../../plugins/ariadne/AGENTS.md). Use its
selection table to choose the skill, then read that canonical `SKILL.md` in full
and follow it.

Invocation prefixes are aliases:

- `/ariadne:ariadne`, `$ariadne`, and a plain request to read or write an
  attestation all select `ariadne`.

The tool holds no signing key and reaches no network of its own. Signing and
signature verification belong to `cosign`, and this tool never reports a
signature as checked. Its `replay` subcommand runs commands a statement
recorded, and only when the user asks for it.

The canonical skill and the runtime contract are authoritative if this
entrypoint disagrees with them.
