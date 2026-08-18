---
name: pandects
description: Route executable credit-law work to Pandects. Use it for the reviewed law corpus, broken specimens and reduced counterexamples; use Fizz to generate a protocol-specific harness.
---

- `/pandects:pandects`, `$pandects`, and a plain request for credit invariants
  all select `pandects`.

Pandects portable entrypoint

Read [the runtime contract](../../../plugins/pandects/AGENTS.md), select its
sole skill, and follow that canonical `SKILL.md` in full.

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

The corpus reaches no network and has no Solidity dependency to fetch. Running
it against a target compiles and executes that target's code locally, so obey
the target repository's own instructions first.

The canonical skill and the runtime contract are authoritative if this
entrypoint disagrees with them.
