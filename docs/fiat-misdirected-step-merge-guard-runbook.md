# Runbook: misdirected Fiat step-merge guard

## Run shape

### Source receipts

```text
study sha256: fe5f3c4b2a5f71f70f71dae61c1c25c6dff65b998393ddb3527bfed21e891863
starting ref: 08512d4ada7b1d7418e1af213be0d4b8c1494b6d
run branch: fiat/555-refuse-misdirected-step-merges
task issue: https://github.com/wildcat-finance/skills/issues/555
entry Fiat: fiat-v5.21.1
expected result Fiat: fiat-v5.22.1 generation
```

This is one capability and one step. The directional ancestry predicate, live
pull-request check, command behavior, tests, Promise boundary, decision
addendum, and generation row describe one evidence gate. Splitting them would
leave either an undocumented controller or prose that claims a guard the
controller does not yet carry. The step starts from a green tree, publishes
the receipted proposition, implements the guard, and ends by running its full
demo and audit surface.

## Step 1: Detect and refuse misdirected step merges

**Goal.** Publish the accepted issue-#555 specification and add one shared
integrate-phase guard that refuses a merge directive or receipt when exact
unmerged-step commits have travelled downward into a lower step branch, the
current pull request no longer targets the run branch, or the required live
evidence cannot be read, while preserving healthy stacked reachability and
local status inspection.

**Entry.** The exact run branch
`fiat/555-refuse-misdirected-step-merges` at starting ref
`08512d4ada7b1d7418e1af213be0d4b8c1494b6d`. The receipted study is
`.hexaemeron/study.md` at SHA-256
`fe5f3c4b2a5f71f70f71dae61c1c25c6dff65b998393ddb3527bfed21e891863`.
Fiat is `fiat-v5.21.1`; its open frontier revision is
`state-shape-validation`, its frontier digest is
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`,
and issue #363 remains its held next job. `next` and `status` perform no live
stack-landing check. `done_merge_step` calls `refuse_rewritten_stack`, which
finds moved later tips but not PR #542's unchanged step-2 tip carried by the
step-1 branch. Before changing product code, add the issue-#555 focused tests
and preserve their red result on this unfixed tree: the #542-shaped `next` case
must still return `merge-step`, and `status` must still omit a stack verdict.
No tracked file from this run exists at entry.

**Exit.** The following all hold on the same signed, audit-ready tree:

1. `docs/fiat-misdirected-step-merge-guard-study.md` is byte-identical to the
   receipted `.hexaemeron/study.md`, and
   `docs/fiat-misdirected-step-merge-guard-runbook.md` is byte-identical to the
   receipted `.hexaemeron/runbook.md`. Protasis accepts both, Imprimatur reports
   no defect, Brevitas exits 0, every relative link resolves, and the
   deterministic Horos boundary describes the tracked tree.
2. One shared stack-landing function derives its plan from validated
   controller state and immutable push-receipt fields before making a remote
   call. For every unmerged step `j`, it checks every SHA in that step's exact
   `verified_commits` list against lower-numbered step branches `1..j-1`.
   Earlier commits reachable from later branches remain valid, and the run
   branch is never treated as a forbidden carrier.
3. The live snapshot uses only the run's configured repository, known exact
   step refs, and the current step's recorded PR URL. It reads the remote refs,
   obtains the named exact objects without updating a local or remote branch,
   reads the current PR's URL, state, head name and OID, base name, and merge
   OID, then reads the refs again. Changed snapshots, missing objects, malformed
   output, timeouts, authentication failures, missing branches, and PR/ref head
   disagreement return `unavailable`, not `clear` or a fabricated finding.
4. The predicate has exactly four closed results: `not-applicable`, `clear`,
   `blocked`, and `unavailable`. It is `not-applicable` outside `integrate` and
   makes no new network call there. A concrete downward ancestor or wrong
   current PR topology is `blocked`. Failure to answer either evidence plane is
   `unavailable`.
5. Only the first unmerged step's live PR base must equal the run branch. The
   current PR may be `OPEN` before the click or `MERGED` correctly into the run
   branch before its receipt. A future step may already have been retargeted to
   the run branch during the required retarget-first window without being
   judged as the current step. Closed-unmerged, wrong-head, or wrong-base
   topology cannot clear the guard.
6. `next` never emits `merge-step` for `blocked` or `unavailable` and returns a
   structured reason and recovery. Human and JSON `status` expose the ordinary
   deterministic local state before the live verdict. An offline operator can
   still inspect phase, receipt, branch, and merged-prefix state, but the output
   cannot call the stack clear. `done merge-step` reruns the same guard before
   any state or ledger write. All three paths leave state and ledger bytes
   unchanged on clear observation, block, unavailability, and exceptions.
7. Stable diagnostics identify evidence class, result, reason code, current or
   owner step, recorded PR URL, offending commit, carrier branch and exact tip
   when known, and one recovery class. They cap list and message sizes and
   expose no raw response, address, environment value, token, or credential.
8. The focused `StackLandingGuardTests` cover all fourteen study specimens:
   exact #542 downward reachability; an open current PR on the wrong base; a
   partial non-head commit carry; healthy upward reachability; the
   retarget-first window; a correct run-branch merge awaiting receipt; a
   rewritten later branch; missing and malformed ref evidence; GitHub timeout,
   authentication, malformed JSON, and wrong URL; a first/second ref race;
   historical PR `baseRefOid` versus the live named branch; a legacy receipt
   without `verified_commits`; and every non-integrate phase making no new
   remote call. The cases also assert `OPEN` and correctly `MERGED` current-PR
   windows, PR/ref head coherence, exact downward direction, no per-commit
   network loop, and unchanged state and ledger bytes.
9. The red-before-fix run is preserved against the unfixed signed parent. The
   same focused command is green after the cause is fixed. Any Warden repair
   has a fresh Elenchus report from the exact runner in Tests, observes its
   guard red without the repair and green with it, and records one of
   `guarded`, `unguarded`, `passed`, or `inconclusive` without substituting the
   report schema for its CLI format.
10. `push-discipline.md` names the early check, the clean retarget-and-retry
    route, the unavailable-evidence retry, and the halt boundary once commits
    are reachable downward. A dated issue-#555 addendum to ADR-021 records the
    two evidence planes, directional rule, current-PR-only base rule, coherent
    snapshot, and remaining post-check race. Neither surface claims that the
    controller locks GitHub or repairs a damaged graph.
11. The applicable Fiat Promise and coverage state only that a clear result
    binds the named exact refs, recorded commits, and current PR metadata at one
    coherent snapshot. They do not claim atomic prevention, semantic commit
    equivalence, arbitrary-branch coverage, or GitHub availability. The
    existing `fiat-final-integration` and `fiat-receipted-delivery` claims stay
    no broader than their evidence.
12. Fiat's frontmatter, ledger header, and one new history row agree on
    `fiat-v5.22.1`, axis `generation`, frontier revision
    `state-shape-validation`, and frontier digest
    `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`.
    The frontier status, current-frontier text, next-job text, evolution, and
    epoch remain byte-identical to 5.21.1, and this run never uses `--frontier`.
    If `main` consumes 5.22.1 before composition, select the next unused Fiat
    generation only after every held field and compatibility premise is
    rechecked; record that change through issue #554's runbook-amendment path or
    halt rather than silently editing this receipted exit.
13. The non-Solidity security receipt records a waiver because the declared
    surface is Python, Markdown, and JSON and touches no Solidity contract,
    Foundry project, or Hardhat project. The waiver replaces only the Pashov
    pair. Every Warden round still performs the complete risk-register look,
    runs Phylax, Ephoros, and Hypomnema with exit 0, applies Sapheneia's bounded
    audit-record operation, protects every finding and qualification item by
    item, and appends its record to `audit/AUDIT.md`.
14. The focused tests, complete root and Hexaemeron suites, Promise Machine
    sync/check/coverage, evolution guard, JSON parse, Python compile, Protasis,
    Phylax, Ephoros, Hypomnema, Imprimatur, Brevitas, Horos, relative-link,
    byte-identity, and diff checks below exit 0. The Warden loop ends only after
    a recorded zero-finding round. A remaining finding at round eight returns
    Fiat's `audit-verdict` and stops the step instead of claiming closure.

**Files.** The implementation and every later phase of this step are limited
to these tracked paths:

- `docs/fiat-misdirected-step-merge-guard-study.md`, created as the exact
  receipted study copy;
- `docs/fiat-misdirected-step-merge-guard-runbook.md`, created as the exact
  receipted runbook copy;
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
- `plugins/hexaemeron/skills/fiat/SKILL.md`;
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`;
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md`;
- `docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`,
  append-only for the dated issue-#555 addendum;
- `plugins/hexaemeron/tests/test_hexctl.py`;
- `plugins/hexaemeron/tests/test_fiat_skill.py` only for contract, prose, or
  command-surface guards this change makes necessary;
- `tests/promise_machine_coverage.json` for the changed controller and Promise
  bindings;
- `tests/test_promise_machine_contract.py` only if the changed Promise needs a
  focused structural guard not present in the generic coverage checks;
- `tests/test_evolution_contract.py` only if the existing generation guard
  does not cover this exact retained-frontier case;
- `.horos/boundary.json` only if the deterministic scan changes it; and
- `audit/AUDIT.md` for every append-only Warden round record. This path is
  mandatory even when the first round has zero findings.

No dependency, CI file, state version, branch name, receipt schema, plugin
manifest, other skill, other decision record, Solidity file, released digest,
or existing audit byte may change. Issue #555 does not unmerge #542, rebuild
#429 or its controller ledger, implement issue #557's recovery, resolve issue
#556's dynamic target, validate arbitrary runbook commands for issue #508,
force-update a ref, import GitHub's key, or search for substitute pull requests.

**Tests.** Write `StackLandingGuardTests` before the product implementation.
On the unfixed signed parent, run the focused command and preserve the failure
showing that the exact #542 fixture still receives `merge-step` from `next` and
no live verdict from `status`:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl.StackLandingGuardTests -v
```

After implementing the shared predicate, run the same command and require all
fourteen specimens and their race/window subcases to pass. Then run the complete
focused and repository gates in this order:

```bash
cmp -s .hexaemeron/study.md docs/fiat-misdirected-step-merge-guard-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-misdirected-step-merge-guard-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-misdirected-step-merge-guard-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-misdirected-step-merge-guard-runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_hexctl.StackLandingGuardTests -v
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill -v
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py sync --check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m json.tool tests/promise_machine_coverage.json >/dev/null
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/EVOLUTION.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-misdirected-step-merge-guard-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-misdirected-step-merge-guard-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/push-discipline.md docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md docs/fiat-misdirected-step-merge-guard-study.md docs/fiat-misdirected-step-merge-guard-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m py_compile plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/tests/test_hexctl.py plugins/hexaemeron/tests/test_fiat_skill.py
git diff --check
```

Resolve every relative link in the two tracked spec copies from its own
directory. If either conditional contract-test file or `.horos/boundary.json`
does not change, leave it untouched and report that the existing guard or
boundary was sufficient.

The source-bound Elenchus runner contract for every Warden repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected emitted schema: elenchus.unittest.v1
report file: .elenchus/fiat-555-misdirected-step-merge-guard-step-1.json
```

The report path must be fresh for the fixes commit. Warden must observe the
relevant guard red without the fix and green with it before recording
`guarded`. A passing command with no causal guard is `passed`; a fix with no
guard is `unguarded`; a missing, stale, empty, malformed, wrong-schema, or
infrastructure-failed report is `inconclusive`. A round without a fixes commit
omits both fix and verdict fields.

The security-suite receipt is a non-Solidity waiver: no Solidity, contract,
Foundry, or Hardhat surface is in Files. For each audit round, Warden reviews
all thirteen risk-register ids and the fourteen specimens against the entire
step diff, runs the three tree lints above, and prepares a record with coverage,
what was not checked, findings, and `Leads not pursued`. Before appending,
freeze the protected evidence inventory, apply Sapheneia's bounded audit-record
operation, and compare every identifier, number, link, severity,
qualification, unknown, negative result, verdict, status, and lead. Append only
when the inventory is unchanged, then record the exact
`sapheneia:sapheneia` filter declaration and all three zero lint exits. If a
round finds anything, fix the cause on the Warden branch, run the Elenchus
contract above, fold the verified fixes into the step branch, and repeat the
whole round. A zero-finding round closes the loop. Round eight with a finding
stops at `audit-verdict` for the user.

During prose, Hypomnema checks the ADR addendum and every pointer before the
masks. Apply Imprimatur, then Vulgate, then Imprimatur again to each shipped
document and the step and run PR drafts. The issue-closing draft preserves the
exact issue URL, later integration PR URL field, identifiers, status, and every
unresolved item through the separate sequence
`Sapheneia -> Imprimatur -> Vulgate -> Imprimatur`; compare the protected
inventory after both semantic passes. Nothing in the prose receipt claims that
the eventual comment was posted or read back.

**Disciplines.** phylax: exact state fields, Git refs, fetched objects, GitHub
JSON, argv, paths, timeouts, output caps, and diagnostics are untrusted
off-chain boundaries and use the study's fixed-input, no-shell, two-snapshot,
no-secret controls. ephoros: `stack_guard` gives human and JSON `status`,
`next`, and the receipt path the exact result, evidence class, OIDs, reason,
and recovery needed to explain a refusal without adding a metric or alert.
metron: none, because the change makes no latency claim and tests only the
bounded remote-call shape. elenchus: the #542 reproduction and all fourteen
specimens are red before the cause is fixed, green afterwards, and every audit
repair uses the exact runner above. hypomnema: the tracked study, runbook,
ADR-021 addendum, Fiat contract, push discipline, Promise, generation ledger,
and audit append are the durable homes chosen in the study. sapheneia: every
audit round and the eventual task-issue closing draft retain their protected
evidence inventories through the bounded record operation and required prose
sequence.

### Amendment -- 2026-08-24

**What changed.** Complete replacement Exit: The following all hold on the
same signed, audit-ready tree:

1. `docs/fiat-misdirected-step-merge-guard-study.md` is byte-identical to the
   receipted `.hexaemeron/study.md`, and
   `docs/fiat-misdirected-step-merge-guard-runbook.md` is byte-identical to the
   receipted `.hexaemeron/runbook.md`. Protasis accepts both, Imprimatur reports
   no defect on either, every relative link resolves, and the deterministic
   Horos boundary describes the tracked tree. Brevitas exits 0 on the runbook.
   On the byte-identical study it exits 1 with exactly nine B023 findings at
   lines 351, 353, 355, 357, 359, 361, 363, 365, and 367. Those glossary
   definition findings remain visible and qualified; this exit makes no
   Brevitas-clean claim for the study.
2. One shared stack-landing function derives its plan from validated
   controller state and immutable push-receipt fields before making a remote
   call. For every unmerged step `j`, it checks every SHA in that step's exact
   `verified_commits` list against lower-numbered step branches `1..j-1`.
   Earlier commits reachable from later branches remain valid, and the run
   branch is never treated as a forbidden carrier.
3. The live snapshot uses only the run's configured repository, known exact
   step refs, and the current step's recorded PR URL. It reads the remote refs,
   obtains the named exact objects without updating a local or remote branch,
   reads the current PR's URL, state, head name and OID, base name, and merge
   OID, then reads the refs again. Changed snapshots, missing objects, malformed
   output, timeouts, authentication failures, missing branches, and PR/ref head
   disagreement return `unavailable`, not `clear` or a fabricated finding.
4. The predicate has exactly four closed results: `not-applicable`, `clear`,
   `blocked`, and `unavailable`. It is `not-applicable` outside `integrate` and
   makes no new network call there. A concrete downward ancestor or wrong
   current PR topology is `blocked`. Failure to answer either evidence plane is
   `unavailable`.
5. Only the first unmerged step's live PR base must equal the run branch. The
   current PR may be `OPEN` before the click or `MERGED` correctly into the run
   branch before its receipt. A future step may already have been retargeted to
   the run branch during the required retarget-first window without being
   judged as the current step. Closed-unmerged, wrong-head, or wrong-base
   topology cannot clear the guard.
6. `next` never emits `merge-step` for `blocked` or `unavailable` and returns a
   structured reason and recovery. Human and JSON `status` expose the ordinary
   deterministic local state before the live verdict. An offline operator can
   still inspect phase, receipt, branch, and merged-prefix state, but the output
   cannot call the stack clear. `done merge-step` reruns the same guard before
   any state or ledger write. All three paths leave state and ledger bytes
   unchanged on clear observation, block, unavailability, and exceptions.
7. Stable diagnostics identify evidence class, result, reason code, current or
   owner step, recorded PR URL, offending commit, carrier branch and exact tip
   when known, and one recovery class. They cap list and message sizes and
   expose no raw response, address, environment value, token, or credential.
8. The focused `StackLandingGuardTests` cover all fourteen study specimens:
   exact #542 downward reachability; an open current PR on the wrong base; a
   partial non-head commit carry; healthy upward reachability; the
   retarget-first window; a correct run-branch merge awaiting receipt; a
   rewritten later branch; missing and malformed ref evidence; GitHub timeout,
   authentication, malformed JSON, and wrong URL; a first/second ref race;
   historical PR `baseRefOid` versus the live named branch; a legacy receipt
   without `verified_commits`; and every non-integrate phase making no new
   remote call. The cases also assert `OPEN` and correctly `MERGED` current-PR
   windows, PR/ref head coherence, exact downward direction, no per-commit
   network loop, and unchanged state and ledger bytes.
9. The red-before-fix run is preserved against the unfixed signed parent. The
   same focused command is green after the cause is fixed. Any Warden repair
   has a fresh Elenchus report from the exact runner in Tests, observes its
   guard red without the repair and green with it, and records one of
   `guarded`, `unguarded`, `passed`, or `inconclusive` without substituting the
   report schema for its CLI format.
10. `push-discipline.md` names the early check, the clean retarget-and-retry
    route, the unavailable-evidence retry, and the halt boundary once commits
    are reachable downward. A dated issue-#555 addendum to ADR-021 records the
    two evidence planes, directional rule, current-PR-only base rule, coherent
    snapshot, and remaining post-check race. Neither surface claims that the
    controller locks GitHub or repairs a damaged graph.
11. The applicable Fiat Promise and coverage state only that a clear result
    binds the named exact refs, recorded commits, and current PR metadata at one
    coherent snapshot. They do not claim atomic prevention, semantic commit
    equivalence, arbitrary-branch coverage, or GitHub availability. The
    existing `fiat-final-integration` and `fiat-receipted-delivery` claims stay
    no broader than their evidence.
12. Fiat's frontmatter, ledger header, and one new history row agree on
    `fiat-v5.22.1`, axis `generation`, frontier revision
    `state-shape-validation`, and frontier digest
    `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`.
    The frontier status, current-frontier text, next-job text, evolution, and
    epoch remain byte-identical to 5.21.1, and this run never uses `--frontier`.
    If `main` consumes 5.22.1 before composition, select the next unused Fiat
    generation only after every held field and compatibility premise is
    rechecked; record that change through issue #554's runbook-amendment path or
    halt rather than silently editing this receipted exit.
13. The non-Solidity security receipt records a waiver because the declared
    surface is Python, Markdown, and JSON and touches no Solidity contract,
    Foundry project, or Hardhat project. The waiver replaces only the Pashov
    pair. Every Warden round still performs the complete risk-register look,
    runs Phylax, Ephoros, and Hypomnema with exit 0, applies Sapheneia's bounded
    audit-record operation, protects every finding and qualification item by
    item, and appends its record to `audit/AUDIT.md`.
14. Every command in the replacement Tests field returns its stated result.
    The focused and complete suites, Promise Machine checks, evolution guard,
    JSON parse, Python compile, Protasis, Phylax, Ephoros, Hypomnema,
    Imprimatur, Horos, relative-link, byte-identity, and diff checks exit 0.
    Brevitas runs once per path: the runbook, Fiat SKILL, Fiat EVOLUTION, push
    discipline, and ADR each exit 0; the study returns only the exact nine B023
    findings and exit 1 stated in item 1. The executable proof includes
    `python3 -m unittest plugins.hexaemeron.tests.test_hexctl.StackLandingGuardTests -v`,
    `python3 -m unittest discover -s tests`,
    `python3 plugins/hexaemeron/tests/run_tests.py`, and `git diff --check`.
    The Warden loop ends only after a recorded zero-finding round. A remaining
    finding at round eight returns Fiat's `audit-verdict` and stops the step
    instead of claiming closure.

Complete replacement Tests: Write `StackLandingGuardTests` before the product
implementation. On the unfixed signed parent, run the focused command and
preserve the failure showing that the exact #542 fixture still receives
`merge-step` from `next` and no live verdict from `status`:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl.StackLandingGuardTests -v
```

After implementing the shared predicate, run the same command and require all
fourteen specimens and their race/window subcases to pass. Then run the complete
focused and repository gates in this order:

```bash
cmp -s .hexaemeron/study.md docs/fiat-misdirected-step-merge-guard-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-misdirected-step-merge-guard-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-misdirected-step-merge-guard-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-misdirected-step-merge-guard-runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_hexctl.StackLandingGuardTests -v
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill -v
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py sync --check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m json.tool tests/promise_machine_coverage.json >/dev/null
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/EVOLUTION.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-misdirected-step-merge-guard-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-misdirected-step-merge-guard-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/EVOLUTION.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-misdirected-step-merge-guard-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-misdirected-step-merge-guard-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m py_compile plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/tests/test_hexctl.py plugins/hexaemeron/tests/test_fiat_skill.py
git diff --check
```

The first five Brevitas invocations above other than the study command exit 0:
Fiat SKILL, Fiat EVOLUTION, push discipline, ADR-021, and the tracked runbook.
The study invocation exits 1 with exactly nine B023 findings at lines 351, 353,
355, 357, 359, 361, 363, 365, and 367 and no other finding. Preserve that
result as qualified evidence; do not report the study as Brevitas-clean.

Resolve every relative link in the two tracked spec copies from its own
directory. If either conditional contract-test file or `.horos/boundary.json`
does not change, leave it untouched and report that the existing guard or
boundary was sufficient.

The source-bound Elenchus runner contract for every Warden repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected emitted schema: elenchus.unittest.v1
report file: .elenchus/fiat-555-misdirected-step-merge-guard-step-1.json
```

The report path must be fresh for the fixes commit. Warden must observe the
relevant guard red without the fix and green with it before recording
`guarded`. A passing command with no causal guard is `passed`; a fix with no
guard is `unguarded`; a missing, stale, empty, malformed, wrong-schema, or
infrastructure-failed report is `inconclusive`. A round without a fixes commit
omits both fix and verdict fields.

The security-suite receipt is a non-Solidity waiver: no Solidity, contract,
Foundry, or Hardhat surface is in Files. For each audit round, Warden reviews
all thirteen risk-register ids and the fourteen specimens against the entire
step diff, runs the three tree lints above, and prepares a record with coverage,
what was not checked, findings, and `Leads not pursued`. Before appending,
freeze the protected evidence inventory, apply Sapheneia's bounded audit-record
operation, and compare every identifier, number, link, severity,
qualification, unknown, negative result, verdict, status, and lead. Append only
when the inventory is unchanged, then record the exact
`sapheneia:sapheneia` filter declaration and all three zero lint exits. If a
round finds anything, fix the cause on the Warden branch, run the Elenchus
contract above, fold the verified fixes into the step branch, and repeat the
whole round. A zero-finding round closes the loop. Round eight with a finding
stops at `audit-verdict` for the user.

During prose, Hypomnema checks the ADR addendum and every pointer before the
masks. Apply Imprimatur, then Vulgate, then Imprimatur again to each shipped
document and the step and run PR drafts. The issue-closing draft preserves the
exact issue URL, later integration PR URL field, identifiers, status, and every
unresolved item through the separate sequence
`Sapheneia -> Imprimatur -> Vulgate -> Imprimatur`; compare the protected
inventory after both semantic passes. Nothing in the prose receipt claims that
the eventual comment was posted or read back.

**Why.** The receipted multi-path Brevitas command cannot run because this
version of the checker accepts one path per invocation. The byte-identical
study is earlier receipted evidence and its nine glossary-definition findings
cannot be erased to make a later structural lint green. Evidence precedence
therefore keeps the study bytes and records the exact qualified non-zero result,
while the corrected command shape obtains a real per-file verdict everywhere
else. Repeating a false zero-exit claim would weaken both the receipt and the
lint.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds.
