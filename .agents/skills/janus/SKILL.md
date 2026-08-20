---
name: janus
description: Route hook-conformance work to Janus. Use it to state and enforce what a contract hook may observe and change around a host action, checked by a manifest and a stateful Foundry harness; use Fizz to generate a protocol-specific fuzz harness instead.
---

# Janus portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Janus tests a contract hook at the threshold it controls: what it may observe and change before a host action, what it may change after, and what it must never touch.

**Use another tool when.** Use Hexaemeron Fizz to generate a protocol-specific fuzz harness, Pandects for the economic laws a hook-driven transition must preserve, and Ariadne to carry a manifest revision and its conformance result with a release.

**Current frontier.** Janus ships the Wildcat v2.5 host adapter and its seven gates against modeled hooks, and no second host adapter yet shows the manifest format holds for another callback model.
<!-- marketplace-context:end -->

Read [the Janus runtime contract](../../../plugins/janus/AGENTS.md). Use its
selection table to choose the skill, then read that canonical `SKILL.md` in
full and follow it.

Invocation prefixes are aliases:

- `/janus:janus`, `$janus`, and a plain request to check a hook's permitted
  effects around a host action all select `janus`.

The suite reaches no network and has no Solidity dependency to fetch. Running a
host adapter's suite compiles and executes that host's modeled code locally, so
obey the target repository's own instructions first.

The canonical skill and the runtime contract are authoritative if this
entrypoint disagrees with them.
