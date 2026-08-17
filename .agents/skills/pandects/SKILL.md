---
name: pandects
description: Route executable credit-law work to Pandects. Use it for the reviewed law corpus, broken specimens and reduced counterexamples; use Fizz to generate a protocol-specific harness.
---

# Pandects portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample.

**Use another tool when.** Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release.

**Current frontier.** No law prevents fees from reducing pooled lender claims below amounts owed on open withdrawal batches.
<!-- marketplace-context:end -->

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
