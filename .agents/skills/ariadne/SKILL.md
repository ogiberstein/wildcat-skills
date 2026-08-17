---
name: ariadne
description: Route release-evidence work to Ariadne. Use it to bind an artefact digest to build, test, review and deployment evidence; use an external Sigstore or cosign verifier for signatures.
---

# Ariadne portable entrypoint

<!-- marketplace-context:start -->
## Where this sits

Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release.

**Use another tool when.** Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence.

**Current frontier.** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

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
