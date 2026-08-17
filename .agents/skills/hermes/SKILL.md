---
name: hermes
description: Route one-class Solidity gas optimisation to Hermes. Use it for measured, fail-closed Foundry work; use Pandects or the audit skills for broader behavioural and security review.
---

# Hermes portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Hermes measures one Solidity gas optimisation class at a time and rejects the candidate when its Foundry evidence does not clear every gate.

**Use another tool when.** Use Pandects for credit-specific laws, or Hexaemeron's audit skills for a broader security review.

**Current frontier.** There is no published follow-on; the shipped catalogue and fail-closed loop are the current boundary.
<!-- marketplace-context:end -->

Read [the Hermes runtime contract](../../../plugins/hermes/AGENTS.md), then read
[the canonical Hermes skill](../../../plugins/hermes/skills/hermes/SKILL.md) in
full and follow it. Resolve every relative path from the canonical skill's
directory. The canonical file is authoritative if this entrypoint and it ever
disagree.
