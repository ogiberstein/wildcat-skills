---
name: pandects
description: Route a request about executable credit invariants to the canonical Pandects instructions. Use when the user names Pandects, asks which laws a lending or credit system should hold, or wants reviewed properties for a fuzzing campaign. Never use it to report a campaign under an engine that did not run.
---

# Pandects portable entrypoint

Read [the Pandects runtime contract](../../../plugins/pandects/AGENTS.md). Use
its selection table to choose the skill, then read that canonical `SKILL.md` in
full and follow it.

Invocation prefixes are aliases:

- `/pandects:pandects`, `$pandects`, and a plain request for credit invariants
  all select `pandects`.

The corpus reaches no network and has no Solidity dependency to fetch. Running
it against a target compiles and executes that target's code locally, so obey
the target repository's own instructions first.

The canonical skill and the runtime contract are authoritative if this
entrypoint disagrees with them.
