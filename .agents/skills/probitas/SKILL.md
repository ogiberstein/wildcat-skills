---
name: probitas
description: Route sourced counterparty lending dossiers to Probitas. Use declared addresses and keep coverage gaps visible; do not infer identity or issue a Wildcat verdict.
---

# Probitas portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict.

**Use another tool when.** Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty.

**Current frontier.** Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.
<!-- marketplace-context:end -->

Read [the Probitas runtime contract](../../../plugins/probitas/AGENTS.md). Use
its selection table to choose the skill, then read that canonical `SKILL.md` in
full and follow it.

Invocation prefixes are aliases:

- `/probitas:probitas`, `$probitas`, and a plain request for a counterparty
  dossier all select `probitas`.

The tool reaches public venue APIs over the network when `--fixtures` is
absent. Ask before running it against a live counterparty if the runtime or the
target repository requires approval for outbound requests.

The canonical skill and the runtime contract are authoritative if this
entrypoint disagrees with them.
