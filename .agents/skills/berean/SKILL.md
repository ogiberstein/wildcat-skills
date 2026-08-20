---
name: berean
description: Route evidence-backed protocol-agent release work to Berean. Use it to pin corpora, prove byte-exact citations and block-bound reads, and grade recorded answers; use Lemma for chunking and Lazarus for chain preservation.
---

# Berean portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it.

**Use another tool when.** Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence.

**Current frontier.** The reference release answers against a frozen demonstration corpus and preserved Goldfinch mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
<!-- marketplace-context:end -->

Read [the Berean runtime contract](../../../plugins/berean/AGENTS.md). Use
its selection table to choose the skill, then read that canonical `SKILL.md`
in full and follow it.

Invocation prefixes are aliases:

- `/berean:berean`, `$berean`, and a plain request to verify or release an
  evidence-backed protocol agent all select `berean`.

The canonical skill pins document corpora by digest, proves citations as
exact bytes, holds chain values to a named chain and block through preserved
read records, grades recorded answers against ordinary and adversarial
evaluation cases, and keeps promotion and rollback as records. It runs no
model and reaches no network.

The canonical skill and runtime contract are authoritative if this
entrypoint disagrees with them.
