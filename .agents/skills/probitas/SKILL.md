---
name: probitas
description: Route sourced counterparty lending dossiers to Probitas. Use declared addresses and keep coverage gaps visible; do not infer identity or issue a Wildcat verdict.
---

- `/probitas:probitas`, `$probitas`, and a plain request for a counterparty
  dossier all select `probitas`.

Probitas portable entrypoint

Read [the runtime contract](../../../plugins/probitas/AGENTS.md), select its
sole skill, and follow that canonical `SKILL.md` in full.

<!-- marketplace-context:start -->
> **Marketplace context: Probitas.** Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict. Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty. **Current frontier:** Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.
<!-- marketplace-context:end -->

The tool reaches public venue APIs over the network when `--fixtures` is
absent. Ask before running it against a live counterparty if the runtime or the
target repository requires approval for outbound requests.

The canonical skill and runtime contract prevail over this entrypoint.
