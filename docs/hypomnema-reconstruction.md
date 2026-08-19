# Hypomnema retrospective faux-loop

## Status

This document reconstructs the two Hypomnema evolution entries merged through
PRs #182 to #190 on 2026-08-19. It is a retrospective, not an ADR, a Fiat
controller receipt, or proof that those runs completed cleanly.

The rollback returns Hypomnema to `hypomnema-v0.1.0`. The original frontier
and `Next Fiat job` remain open. The removed text remains available in Git and
the merged PRs.

## Study

The merged range added seven files under `docs/decisions/`, changed
Hypomnema's ledger twice, and changed its frontmatter once. Four later PRs
treated descriptions of existing skills as accepted organisation-wide
decisions. The final PR marked the frontier mature.

That history cannot support the versions it claimed:

- PRs #182, #183, and #185 carried the same ADR-001 and ADR-002 payload
  through three merges. PR #184 then repaired the ledger digest and next job.
- PR #186 added a point-in-time skill inventory as ADR-003. Its stated count
  was already stale against the repository it entered.
- ADR-004 through ADR-007 did not contain the Alternatives section required by
  Hypomnema's own record shape.
- The name `Aegis` did not occur in the pre-evolution tree. ADR-004 through
  ADR-007 used it as though it were an established review-and-release chain.
- ADR-007 declared a fixed Ephoros event schema that does not exist in the
  Ephoros skill or checker.
- PR #190 changed the ledger to `hypomnema-v1.1.1` but left the version in
  `SKILL.md` at `1.1.0`.
- The `v1.1.1` entry used the epoch counter to reopen and close the frontier
  without evidence of a compatibility or provenance boundary. The versioning
  contract forbids using epoch as a patch counter.

### Removed material

| Source | Material | Retrospective disposition |
| --- | --- | --- |
| PRs [#182](https://github.com/wildcat-finance/skills/pull/182), [#183](https://github.com/wildcat-finance/skills/pull/183), [#184](https://github.com/wildcat-finance/skills/pull/184), and [#185](https://github.com/wildcat-finance/skills/pull/185) | ADR-001, ADR-002, and `hypomnema-v1.1.0` | Keep as source material only. The two records follow the expected shape and describe real repository rules, but the repeated merge chain and repaired ledger do not establish a clean evolution. |
| PR [#186](https://github.com/wildcat-finance/skills/pull/186) | ADR-003 skill map | Reject as an ADR. It is a mutable inventory, duplicates routing files, and was stale when merged. |
| PR [#187](https://github.com/wildcat-finance/skills/pull/187) | ADR-004 safety cluster | Reject as an ADR. It omits alternatives and restates four skill contracts as one new decision. |
| PR [#188](https://github.com/wildcat-finance/skills/pull/188) | ADR-005 Imprimatur gate | Reject as an ADR. It omits alternatives and promotes an undefined chain name over the Imprimatur skill and ledger. |
| PR [#189](https://github.com/wildcat-finance/skills/pull/189) | ADR-006 Vulgate gate and ADR-007 Ephoros gate | Reject as ADRs. Both omit alternatives; ADR-006 restates Vulgate, while ADR-007 adds behaviour Ephoros does not carry. |
| PR [#190](https://github.com/wildcat-finance/skills/pull/190) | `hypomnema-v1.1.1` and mature frontier | Reject the transition. The ledger and frontmatter disagree, the epoch has no qualifying boundary, and the maturity claim depends on the rejected records. |

The uncommitted follow-on changed the Hypomnema frontmatter to `1.1.1`,
rewrote the epoch row, and added `docs/imprimatur-adr-005/study.md` and
`runbook.md`. It is preserved in the named pre-rollback stash and is not part
of this reconstruction.

## Runbook

1. Stop every OpenCode process whose working directory is this checkout.
2. Preserve the uncommitted follow-on in a named Git stash.
3. Restore ADR-001 through ADR-007, `SKILL.md`, and `EVOLUTION.md` to the
   pre-evolution tree at `c0f6ff2`.
4. Classify each removed record against Hypomnema's required shape and the
   repository state it claimed to describe.
5. Keep this retrospective as the map to the removed work. Do not restore the
   seven files as accepted decisions.
6. Run the Hypomnema checker, Imprimatur, and the repository test suites.

## Implementation

The rollback branch restores these authoritative values:

- Current version: `hypomnema-v0.1.0`.
- Frontier status: `open`.
- Frontier revision: `recorded-reasons-and-their-homes`.
- `SKILL.md` version: `0.1.0`.
- Accepted decision records under `docs/decisions/`: none.

The seven removed ADRs remain recoverable from merge commits `7fc5336`,
`4ccfcc7`, `ff9f6a8`, `9d31f3f`, and `0dc1e47`. The two rejected ledger states
remain recoverable from `7fc5336` and `0fa3c12`.

## Audit and prose

This section records only checks run against the rollback and this
retrospective. It does not stand in for Fiat's audit or prose receipts.

- Repository unit tests: 24 passed.
- Hexaemeron tests: 134 passed.
- Imprimatur tests: 55 passed.
- Hypomnema pointer check: clean.
- Imprimatur lint over this document: score 100, no findings.

## Result

The two evolution entries are removed. Their useful historical content is
indexed here without treating it as accepted policy. Hypomnema is back at the
last version whose ledger and frontmatter agree.

If ADR-001 and ADR-002 are still wanted, the open `Next Fiat job` can produce
fresh records in one controller run. That run should create one integration
PR, advance the evolution counter once after its tests pass, and choose the
next frontier from evidence gathered during the run. ADR-003 through ADR-007
should not be carried into it.
