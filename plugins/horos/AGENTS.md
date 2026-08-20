# Horos runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Horos.** Horos classifies a repository's evidenced token sinks and emits the reading boundary agents consult before ordinary work. Use Lemma to chunk source for retrieval, Brevitas to constrain engineering prose and Metron to measure runtime cost. No reading boundary applies during security review. **Current frontier:** The reopened scope is complete: the three home repositories carry graded boundaries, candidates, censuses and adoption stanzas, with the product pull requests awaiting their own review gates; no evidenced improvement remains.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Horos contains one Agent Skill. Read `skills/horos/SKILL.md` in full before
scanning, checking or mapping a repository.

## Capabilities and paths

- Resolve `$PLUGIN_ROOT` to this `plugins/horos/` directory.
- Run `skills/horos/scripts/horos.py` from that fixed plugin path.
- Treat the repository named by the user as the target. Do not substitute this
  distribution checkout unless the user named it.
- `scan --write` writes `.horos/boundary.json` and optional census/candidate
  records inside the target. `check` and `map` are read-only.
- Names such as `$horos`, `/horos:horos` and `horos:horos` are invocation
  aliases, not shell commands.

## Network and side effects

Horos reaches no network, imports none of the source it inspects and executes no
target file. Writes are atomic and confined to the target's `.horos/`
directory. A non-zero command exit means the requested scan, check or map did
not succeed.

## What this skill must refuse

- No reading boundary during a security review, audit or incident.
- No hard exclusion without the evidence carried by the boundary entry.
- No claim that omitted paths are safe or cheap; classification is fail-open.
- No whole-repository claim from a scoped check.
- No generated, vendored or binary source executed in order to classify it.
- No stale boundary treated as current after `check` reports drift.

If a scan, check, map or test did not run, say so plainly and do not describe
its result as successful.
