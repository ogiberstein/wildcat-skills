# Observable run record carryover inoculation 3 runbook

## Scope

One implementation step reconstructs the complete v1 surface, repairs the
three current red mechanisms, and proves the cumulative inoculation before
Fiat opens a new audit round.

## Audit boundary

The inoculation suite preserves prior repairs and exposes regressions. It does
not replace the independent Warden round required for closure.

## Step 1: Reconstruct, repair, inoculate, and demonstrate the observable run record

**Goal.** Semantically reconstruct the signed attempt-5 validator on the
current base, preserve all 40 fixed prior mechanisms, repair and guard the
three red round-2 mechanisms, reduce the reporter same-inode lead, bind all
three packets, and demonstrate the complete eight-family surface before the
first new audit round.

**Entry.** The exact run branch
`fiat/434-observable-run-record-carryover-inoculation` at starting commit
`367e9662384bb29ea94576d270ab86744f3326a2`, with the study and this runbook
receipted. Before importing bytes:

- verify issue attachment `434-CARRYOVER.md` and its local archive at SHA-256
  `11bbf719ce1b2f59b0344d4ad92d69e467c503d758b35a1689a98c7231156784`;
- verify issue attachment `434-CARRYOVER-2.md` and its local archive at
  SHA-256
  `54469718c5949953dae414da664a65f940aca249868e00382f97139cda03fef0`;
- verify issue attachment `434-CARRYOVER-3.md` and its local archive at
  SHA-256
  `5f454dc466109ebaf138959986dcbdfb267d1c1e1291b0db000e18c4f567dcbe`;
- verify 36 unique ids with round counts `6,1,5,5,6,6,4,3`;
- verify archived controller evidence and signed local ref
  `archive/434-observable-run-record-attempt-3` at
  `9158edb4b3d2c49298d8b2ba8092c7540caeb57a`;
- verify the second archived controller evidence and signed local ref
  `archive/434-observable-run-record-attempt-4` at
  `dd5b9269252acc0da860cae0d4a6ec2a012f3cda`, with the current starting
  commit as its sole parent and exactly 37 changed paths;
- verify the third archived controller evidence, signed implementation
  `546b773f6ebd98a16b42c4f1c3a94f54465a5db0`, and signed fixed ref
  `archive/434-observable-run-record-attempt-5` at
  `50a9129c8481e7519d8c640c152f58401035f323`, including its four round-1
  repairs, exact parent, signatures, trailers, and 37-path inventory;
- verify merge base `454bf3c9930c94985e5eb6179f3b01be2bf741c2`
  and the old path inventory; and
- observe the missing observation command, schema, published records,
  carryover map, inoculation module, and Elenchus reporter red on the entry
  parent.

**Exit.** The current tree meets all of these conditions:

- The complete host-neutral `promise-machine-run-observation/v1` schema,
  standard-library validator, operator document, valid and invalid fixtures,
  root Promise declaration and identical generated copies are present.
- Promise coverage, the published study and runbook, and ADR-015 are current.
- ADR-014 and every current-main Fiat, Protasis, Elenchus, marketplace, audit,
  and Wave Atlas change remain intact.
- The historical issue-434 audit record remains halted prior evidence, not a
  clean current-round result.
- `tests/fixtures/run-observation/434-carryover-v1.json` carries the packet
  chain with all three packet digests, all three preserved refs, source runs,
  the original 36 unique finding ids, four round-1 repairs, and three current
  repairs. Every original id maps to a current test, remediation family, and
  one of eight inoculation families; no test is unmapped.
- `tests/test_run_observation_inoculation.py` generates schema/runtime,
  wrong-kind, lifecycle/reference, file-replacement, path-representation,
  normalised-field-name, report-parity/no-echo, and context-binding cases. It
  prints counts and asserts zero crashes and zero unexpected clean mutations.
- The repository reporter runs both focused modules, executes at least one
  test, and writes one fresh `elenchus.unittest.v1` report only to the supplied
  confined `{report}` path.
- Repository paths contain Unicode scalar values in NFC, exclude controls and
  bidi formatting, and retain existing portable segment restrictions in
  schema, runtime, docs, and tests.
- Success is bound to a final bounded reread and digest comparison of the
  caller-named input. An equal-length same-inode rewrite in the last window
  refuses without an unbounded stability loop.
- Hidden-work suffix, prefix, compact, camel, token, and acronym families
  refuse while safe bounded metadata names remain valid.
- The reporter same-inode lead is reduced with a non-recursive original
  `fsync` handle and recorded as guarded if confirmed or bounded inconclusive
  if not reproducible.

The final demonstration is:

```bash
# The direct source-owned report is an absolute output in this worktree.
REPORT_PATH="$(pwd -P)/.elenchus/run-observation.json"
python3 -m unittest tests.test_run_observation tests.test_run_observation_inoculation -v
python3 tests/emit_run_observation_report.py "$REPORT_PATH"
# Elenchus replaces `{report}` with a canonical absolute descendant of its
# detached parent worktree. Its declaration must therefore remain relative.
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py \
  --ref HEAD \
  --test-command "python3 tests/emit_run_observation_report.py {report}" \
  --report-format unittest-json-v1 \
  --report-file .elenchus/run-observation.json
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/success.jsonl
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/refusal.jsonl
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/retry.jsonl
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/handoff.jsonl
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py sync
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins scripts tests schemas
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins scripts tests schemas
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs schemas scripts
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  PROMISE_MACHINE.md \
  docs/decisions/ADR-015-define-the-promise-machine-run-observation-record.md \
  docs/promise-machine/run-observation-study.md \
  docs/promise-machine/run-observation-runbook.md \
  docs/promise-machine/run-observation-v1.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/ADR-015-define-the-promise-machine-run-observation-record.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-v1.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The focused tests assert the five required invalid fixtures exit 1 with their
established `RO008`, `RO009`, `RO011`, `RO012`, and `RO013` codes. The obsolete
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --check` command is
retained only as a negative specimen and exits 2. Passing this exit establishes
that the carried mechanisms and generated inoculation are green on the current
tree. It does not establish audit closure, capture completeness, external
truth, cause, model quality, delivery correctness, deployment readiness,
security, or repository-mutation authority. Only a later independent
zero-finding Warden round closes the audit.

**Files.** Create
`schemas/promise-machine-run-observation-v1.schema.json`,
`scripts/run_observation.py`,
`docs/promise-machine/run-observation-v1.md`,
`docs/promise-machine/run-observation-study.md`,
`docs/promise-machine/run-observation-runbook.md`,
`docs/decisions/ADR-015-define-the-promise-machine-run-observation-record.md`,
`tests/test_run_observation.py`,
`tests/test_run_observation_inoculation.py`,
`tests/emit_run_observation_report.py`,
`tests/fixtures/run-observation/434-carryover-v1.json`, and the valid and
invalid JSONL fixtures below `tests/fixtures/run-observation/`. Modify
`PROMISE_MACHINE.md`, its generated plugin copies through
`scripts/promise_machine.py sync`, `tests/promise_machine_coverage.json`,
`tests/test_promise_machine_contract.py`, and append the preserved halted
issue-434 entries plus this run's later entries to `audit/AUDIT.md`. Refresh
`.horos/boundary.json` only through the current Horos write command if its
exact deterministic scan changes. Modify no Fiat controller/state semantics,
frontier, version, manifest, CI, recorder, redactor, persistence, database,
dashboard, diagnosis, or issue-filing surface.

**Tests.** First retain red entry evidence for every absent public surface and
the three-packet digest/id/map checks. Before semantic import, compare the old
merge-base-to-fixed-tree path list with the declared file boundary and compare
current `main` with the old merge base so concurrent files cannot disappear.
Apply prior changes by path and meaning, not by merge, rebase, or cherry-pick.
For each imported finding, run its minimal guard against the corresponding
unfixed parent or a bounded reverted specimen and record the red result before
accepting it green.

Add direct tests for the 36-id bijection, packet digest, remediation and family
keys, all three packet URLs and digests, all three preserved refs, the four
round-1 guards, the three new repairs, and every generated family. Preserve
red current-head evidence for `analysisText`, `scratchpadContent`,
`deliberationNotes`, `internalMonologueBuffer`, invalid-surrogate and bidi
paths, distinct composed/decomposed forms, and the equal-length same-inode
last-window rewrite. Reduce the reporter lead without recursive instrumentation.

Every delegated mutation and direct source-owned report target must be
canonical and absolute. Resolve `REPORT_PATH` from the current worktree with
`pwd -P`; do not reuse a prior run's worktree path. The Elenchus
`--report-file` value is distinct: it declares a relative descendant of the
detached parent worktree that Elenchus creates for its comparison. Elenchus
replaces `{report}` with a canonical absolute descendant before it invokes the
source-owned reporter, so that emitter still receives only a canonical
absolute in-worktree target. Do not pass the current worktree's absolute
`REPORT_PATH` to `--report-file`.
Before the first write and after each write batch, prove the protected origin
checkout still has exactly its five pre-existing paths, including untracked
`shoggoth-github-under-1mb.jpg`, whose contents must not be read. A relative,
escaping, symlinked, origin-targeting, or undeclared path refuses before write.
Any unrelated concurrent origin drift also stops and is preserved for a new
source-backed restart; no current controller resnapshot capability is assumed.

The exact audit-fix test command is
`python3 tests/emit_run_observation_report.py {report}`; its report format is
`unittest-json-v1`; and its report-file declaration is the relative detached
worktree descendant `.elenchus/run-observation.json`. Run Elenchus with those
exact three inputs against the signed implementation commit and record its
actual verdict. Elenchus replaces `{report}` with an absolute path inside that
detached worktree; the direct source-owned invocation alone receives the
current worktree's absolute `REPORT_PATH`. The emitter, focused suites, all
four valid CLIs, five required invalid exits, root suite, Promise checks, three
discipline lints, prose gates, current Horos check, obsolete Horos negative
specimen, file-scope comparison, and diff check must all report their actual
counts or exits. Remove transient report output before commit unless a
repository contract explicitly tracks it.

Before this runbook is receipted, preflight the parser and argument arity of
every fenced command. Current unittest, Promise, Phylax, Ephoros, Hypomnema,
Imprimatur, Brevitas, Horos, and Elenchus help must exit 0. Extract the signed
attempt-4 observation validator and reporter to a temporary confined directory
and prove their parsers accept `check PATH` and one `REPORT` respectively. Run
the old two-path Brevitas specimen and retain its expected exit 2; run each of
the four exact single-file forms above against an existing bounded specimen and
require exit 0. Parser evidence does not stand in for post-reconstruction test
evidence.

**Disciplines.** phylax: the step imports prior Git/archive evidence and accepts
untrusted JSONL and caller paths, so every digest, path, size, type, relation,
and output boundary must fail closed. ephoros: the command may run unattended,
so its stable findings and inoculation summary must answer which contract,
run, event, carryover id, family, and optional usage fact was observed.
metron: no performance change or budget is claimed; security ceilings are not
speed evidence. elenchus: every transplant or audit failure must be reproduced,
guarded, and reported through the exact source-bound command, format, and file
above. hypomnema: ADR-015 owns the standing decision, the schema owns fields,
operator prose owns use and non-claims, the carryover map owns provenance, and
tests own examples and inoculation evidence.

If round 8, another configured last round, or material source-bound drift still
prevents continuation, attach `434-CARRYOVER-4.md`, preserve all three earlier
packet links and the cumulative
finding/remediation chain, archive the controller and signed fixed tree, halt,
and restart. Later attempts use `-5`, `-6`, and later numbers until
an independent zero-finding Warden round or an explicit user halt.
