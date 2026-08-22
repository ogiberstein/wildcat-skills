# Study: task issue numbers in Fiat branch names

Assuming, unless corrected:

1. Issue 438 is ordinary Fiat generation work from `fiat-v5.9.1`. It must leave the `state-shape-validation` frontier revision, its digest, its current-frontier text, and the complete issue 363 `Next Fiat job` text byte-identical.
2. The exact start is `6412c85d7cfd352e21fcc3dc0d8cef39a0649976` on `main`. The active run branch is `fiat/carry-the-task-issue-number-in-run-and-step-bran`.
3. A new issue-backed run supplies the task issue during `init`. The controller does not infer an issue from the topic or recover one after branch creation.
4. The automatic shape is `fiat/<issue>-<current topic slug>`. The complete issue-bearing slug keeps the existing 48-character limit, with the issue at its leading edge.
5. `--run-branch` remains an exact override. With a task issue, it must start with `fiat/<issue>-`; for example, `fiat/438-prep`.
6. A run without a task issue keeps its current branch name byte for byte. A stored run branch is never recomputed or renamed.
7. The task issue receipt remains the exact URL string used by the integration closure check. State version 1 and every receipt shape remain unchanged.
8. Python 3 and the standard library remain the implementation boundary. The feature adds no dependency, network call, subprocess, secret, or CI change.
9. The active managed controller is `fiat-v4.8.1`, while the checkout is `fiat-v5.9.1`. The recorded `controller_version` receipt makes that enforcement gap explicit.
10. `origin` is the `radup1337/skills` fork with administrator access. `upstream` is `wildcat-finance/skills` with read access. An upstream merge and issue closure remain maintainer actions.

## 1. Problem statement

Fiat records a task issue but derives the run branch only from the topic. A Git reader therefore cannot connect an unmerged run branch to its issue. Issue 438 gives two live issue 322 step branches that exhibit the failure. Both contain truncated topic text and neither contains `322`.

The working prototype makes issue identity visible at the first Git boundary. A new run started with issue 438 produces a run branch beginning `fiat/438-`. Every derived step branch preserves that prefix. A run without an issue produces the same names as `6412c85d7cfd352e21fcc3dc0d8cef39a0649976`. Existing state continues to return its stored branch unchanged.

The checkable acceptance conditions are:

1. `init --task-issue https://github.com/wildcat-finance/skills/issues/438` stores that exact receipt and emits a branch slug of at most 48 characters beginning `fiat/438-`.
2. A long topic cannot remove or truncate the leading `438-` token.
3. Step 1 and later step directives begin with the exact issue-bearing run branch.
4. `init` without `--task-issue` returns the current run branch for the same topic.
5. An explicit override starting with `fiat/438-` passes. An override that omits or changes that prefix fails before state creation.
6. A malformed task issue URL fails before state creation. A first task issue added after issue-free initialization is refused instead of renaming the stored branch.
7. A legacy state fixture with a stored issue-free branch loads, verifies, and emits that branch unchanged.
8. The Fiat generation advances to `fiat-v5.10.1` while the issue 363 frontier fields and digest remain exact.

The focused proof is:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
```

The two complete repository suites required by issue 438 are:

```bash
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

## 2. Prior art

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` already contains the necessary sources but reads them at different times. `cmd_init` derives and stores `run_branch` from the topic. `step_branch_name` prefixes every step with that stored run branch. `expected_task_issue` later reads a string or mapping from `receipts.task_issue`, but preflight records it only after initialization. The issue number is therefore available for closure and absent from naming.

The last two merged Fiat integration pull requests were read before selecting a design:

- [PR 431, “Validate Fiat state before controller traversal”](https://github.com/wildcat-finance/skills/pull/431), landed the current `fiat-v5.9.1` checkout. It preserved stored branch-name checks, state version 1, and the topology gates. Its `## Carried forward` section names issue 363 as the remaining delegated-task identity job and no other unfinished Fiat work.
- [PR 365, “Give every Fiat delegation and commit a verifiable identity”](https://github.com/wildcat-finance/skills/pull/365), landed the branch-tip, remote-tip, pull-request, repository, and merge-identity gates built in [PR 364](https://github.com/wildcat-finance/skills/pull/364). It carried issues 321 and 363 forward and reported no open audit finding.

[PR 120, “Stack the steps, merge once”](https://github.com/wildcat-finance/skills/pull/120), was read as the naming origin. It introduced the current run and step branch construction, the explicit override, stored-name compatibility, stacked pull request bases, and one final base merge. Its exact name-derivation lines remain unchanged at this start.

[PR 234](https://github.com/wildcat-finance/skills/pull/234) was also read because it changed the lifecycle of the same branches. It established that removing a base branch closes the pull request stacked on it, moved deletion after stack integration, and added the stale-controller warning. Those results rule out an automatic rename after a branch or pull request exists.

The in-scope Fiat audit record was read at `audit/AUDIT.md`, especially “Fiat delegation packets, step 3”. Findings I320-S3-R1-01 through I320-S3-R3-01 showed that plausible names and SHAs were insufficient until the controller bound the declared branch, its tip, its pull request, and its repository. All were fixed, and round 4 reported zero findings and no further leads. Issue 438 extends identity earlier, at branch construction. It must not loosen those later topology checks.

The current evolution ledger and “Fiat state-shape validation, step 3, round 1” were also read. They make issue 363 the held successor for delegated task identity. Branch identity is separate generation work. This run must not import, rewrite, narrow, or claim completion of issue 363.

Issue 438 cites the Shoggoth convention `shoggoth/issue-<owner>-<repo>-<n>/<slug>` as external prior art. Its useful property is direct issue visibility before a pull request exists. Its owner and repository fields, interceptor behavior, and exact branch grammar remain out of scope.

## 3. Constraints and non-goals

The build starts from `6412c85d7cfd352e21fcc3dc0d8cef39a0649976`. The new input is an optional `--task-issue <url>` argument on `init`. A valid value has a URL path ending in `/issues/<positive-decimal-number>`. The controller stores the original URL as `receipts.task_issue` and uses only the decimal component for naming.

For automatic names, the existing 48-character branch-slug limit remains unchanged. The controller passes `<issue>-<topic>` through the existing slug function, so right-side truncation cannot remove the issue. Empty topic slugs still use `run`. Step naming requires no second issue parser because it already prefixes the stored run branch.

An override remains authoritative over descriptive text but not issue identity. When an issue exists, the complete branch must start with `fiat/<issue>-`. This keeps `fiat/438-prep` valid and refuses `release/438-prep`, `fiat/prep`, or `fiat/1438-prep`. Without an issue, the current override behavior is unchanged.

The supported time to attach a new task issue is initialization. A later first `record task_issue` on a stacked run is refused because the controller cannot prove that its stored branch is unpushed. Re-recording the same issue already present in legacy or resumed state may remain idempotent. A different issue is refused. Existing state is read, not migrated.

This run is itself an existing-run case. Its old controller initialized and pushed `fiat/carry-the-task-issue-number-in-run-and-step-bran` before issue 438 was recorded. That branch stays unchanged. The prototype is proved with fresh fixtures against the checked-in controller, not by renaming the branch that builds it.

The active controller receipt records `fiat-v4.8.1` against checkout `fiat-v5.9.1`. Version 4.8.1 does not enforce the later branch-topology, signature, packet, or state-shape guarantees. Controller receipts in this run establish phase order only. Tests and audit must invoke the checked-in controller directly for current behavior, and reports must keep that distinction explicit.

Remote work uses the `radup1337/skills` fork. The issue 438 contribution can open an upstream pull request from that fork, but this run cannot merge upstream or close the upstream issue. It must not submit a terminal integration receipt until the upstream merge and closure are true. The older controller's weaker repository checks do not create authority to claim either event.

Non-goals are word-boundary slug truncation, renaming existing branches, changing step-title length, changing the default `fiat/` prefix, changing receipt payloads, changing state version, changing the Shoggoth interceptor, changing issue 363 task identities, supporting issue references that are not issue URLs, or adding a GitHub lookup during initialization.

**Always.** Supply a known task issue to `init`; keep its original URL in the receipt; keep the issue token ahead of topic truncation; run both complete suites before each Fiat commit; run Imprimatur on shipped prose; sign every Fiat-created commit; verify its signature and exact provenance trailers.

**Ask first.** Add a dependency; change state version or a receipt shape; permit an issue-backed override outside `fiat/<issue>-`; permit a late rename; touch CI; weaken branch-topology checks; merge an upstream pull request; or close an upstream issue.

**Never.** Infer the issue from topic prose; truncate the issue token; rename a stored or pushed branch; accept an override with a different issue; rewrite issue 363's frontier text; treat the old controller as current evidence; claim an upstream merge, issue closure, test, lint, signature, or audit that did not occur.

## 4. Design options

### Option A: add the issue number to the topic

The caller could initialize with topic `438 Carry the task issue number...`. This needs no controller change, but the topic is not the task receipt and no guard detects a missing, stale, or unrelated number. It leaves branch identity as orchestration convention rather than controller behavior.

### Option B: accept and store the task issue during `init` (chosen)

Add optional `--task-issue`, extract one positive decimal issue number, store the unchanged URL receipt in the initial state commit, and build the automatic branch as `<prefix><slug(issue-topic, 48)>`. Require an explicit override to start with the same `fiat/<issue>-` prefix. Keep the no-issue path and every stored legacy branch unchanged.

This is the cheapest construction that has both inputs before the branch is committed to state. Its trade is a stricter timing rule: a new issue cannot be attached after issue-free initialization. That refusal is safer than a branch rename whose pull request state the controller cannot prove.

### Option C: rewrite `run_branch` when `record task_issue` runs

This preserves the current preflight command order, but it creates a rename window. The run branch may already exist locally, remotely, or as a pull request base. Proving that no observer depends on it would add local and remote Git checks, race conditions, and recovery behavior to a naming change.

### Option D: keep the stored branch and publish a second issue alias

An issue-named alias would help branch scanners but create two refs for one run. Receipts, pull request bases, cleanup, and integration would need to decide which ref is authoritative. This repeats the identity ambiguity instead of removing it.

## 5. Risk register seed

```risk-register
issue-url-parse | the optional task issue value accepted by init | only a URL path ending in issues slash one positive decimal number supplies identity and malformed input leaves no state
issue-receipt-drift | task issue URL and issue number used by branch construction | one parse supplies both the unchanged receipt and the decimal branch token with mismatch tests
truncation-loss | issue prefix inside the existing 48-character branch slug | long-topic tests prove right-side truncation preserves the issue token at the start of the automatic branch tail
override-escape | explicit run branch supplied with a task issue | prefix checks accept only fiat slash the exact issue number and hyphen and refuse another namespace omission collision or number
late-rename | first task issue recorded after issue-free initialization | the controller refuses rather than changing a stored run branch whose Git publication state is unknown
legacy-branch-mutation | version-1 state created before this generation | loading status next and verify preserve the stored run branch byte for byte
no-issue-regression | ordinary repository delivery without a task issue | golden cases retain the current automatic and override names exactly
step-propagation | run branch copied into each derived step branch | multi-step fixtures require every branch and pull request base to retain the issue-bearing run prefix
topology-regression | issue-bearing names at implement push and merge receipts | existing branch-tip remote-tip pull-request and repository guards remain green without special cases
frontier-drift | fiat generation publication surfaces | the generation row retains the exact issue 363 frontier revision text target acceptance and digest
controller-version-gap | v4.8.1 run receipts beside v5.9.1 checkout behavior | current-controller tests and audit evidence are reported separately from old-controller phase receipts
fork-completion-overclaim | fork branches and an upstream issue outside the user's merge authority | no integration receipt claims upstream merge or issue closure until both are observed
```

The audit loop must cite every id as reviewed or not applicable. `late-rename`, `legacy-branch-mutation`, `topology-regression`, and `fork-completion-overclaim` are release boundaries rather than acceptable open leads.

## 6. Glossary seeds

| Term | Meaning | Boundary |
| --- | --- | --- |
| Task issue | The exact issue URL stored in `receipts.task_issue`. | The branch uses only its final positive decimal issue number. |
| Issue token | The standalone decimal number at the start of the run branch's final component. | It is not inferred from the topic. |
| Branch slug | The normalized run identity, limited to 48 characters. | It is the topic alone without an issue and the leading issue plus topic with one. |
| Issue-backed run | A run initialized with `--task-issue`. | A later receipt does not retroactively make a branch issue-backed. |
| Stored branch | The exact `state.run_branch` value written by `init`. | Resume reads it and never derives it again. |
| Existing run | Any state written before this generation or before a new task issue could be supplied at initialization. | Its refs and pull requests are not renamed. |
| Fork delivery | Branches pushed under `radup1337/skills` for a contribution to `wildcat-finance/skills`. | Fork authority does not include upstream merge or issue closure. |

## 7. Sources

- [Issue 438](https://github.com/wildcat-finance/skills/issues/438), observed branches, requested decisions, acceptance, and generation boundary.
- [Issue 363](https://github.com/wildcat-finance/skills/issues/363), the separate held delegated-task identity job.
- Exact start: Git commit `6412c85d7cfd352e21fcc3dc0d8cef39a0649976`.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, especially `slug`, `run_branch_of`, `step_branch_name`, `branch_plan`, `expected_task_issue`, `cmd_init`, and `cmd_record`.
- `plugins/hexaemeron/tests/test_hexctl.py`, especially current run-name, explicit-override, stack, task-issue closure, legacy-state, and topology cases.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `references/push-discipline.md`, and `EVOLUTION.md`.
- `plugins/hexaemeron/skills/VERSIONING.md`, generation and frontier-preservation rules.
- Naming origin [PR 120](https://github.com/wildcat-finance/skills/pull/120), lifecycle repair [PR 234](https://github.com/wildcat-finance/skills/pull/234), topology step [PR 364](https://github.com/wildcat-finance/skills/pull/364), and the last two integrations, [PR 365](https://github.com/wildcat-finance/skills/pull/365) and [PR 431](https://github.com/wildcat-finance/skills/pull/431).
- `audit/AUDIT.md`, “Fiat delegation packets, step 3” and “Fiat state-shape validation, step 3, round 1”.
- `.hexaemeron/state.json` and `.hexaemeron/ledger.jsonl`, current `controller_version`, task issue, base, and stored run-branch evidence.
- GitHub repository evidence: `radup1337/skills` is a fork with viewer permission `ADMIN`; `wildcat-finance/skills` has viewer permission `READ`.

## 8. Signals, and the questions behind them

This is an interactive command-line controller, not an unattended service. It adds no log, metric, trace, or alert. Exit status, bounded stderr, init stdout, state JSON, and `next` JSON are sufficient signals for these questions:

1. “Which issue does this new branch serve?” The issue token is visible in init output, `state.run_branch`, and every step directive.
2. “Why was this custom branch refused?” The init error names the required issue token without creating state.
3. “Did ordinary issue-free delivery change?” Golden branch-name cases compare exact output.
4. “Why does this self-hosting run still lack `438`?” Its stored branch and `controller_version` receipt identify it as an existing run under the older controller.

The initialization step emits the first two signals. The focused regression set answers the last two. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md), especially “Write the questions before the code” and “Verify the telemetry”, remains the signal authority.

## 9. Boundaries, per capability

The task issue crosses the CLI boundary as untrusted text. Its value is one stable decimal identifier plus the unchanged closure URL. The control accepts one URL path form, requires a positive decimal terminal component, and fails before creating `.hexaemeron` state.

The explicit branch override is another untrusted CLI value. Its value is user-selected namespace and wording. Existing `check_branch_name` remains authoritative for Git syntax, while the new final-component check binds it to the parsed task issue.

State and the append-only ledger form the persistence boundary. Initialization writes the task issue receipt and issue-bearing run branch in one initial state. Later commands read the stored branch. They do not reparse the URL to produce a different name.

The fork and upstream repositories form a delivery boundary, not a new controller code boundary. The feature performs no remote lookup. The run may publish to the authorized fork and open an upstream contribution, but it cannot convert read permission into merge or closure authority.

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md), especially “Name the boundaries before choosing controls”, “Everything from outside is hostile”, and “Subprocesses and paths”, remains the boundary and control authority.

## 10. The budget, or its absence

No performance improvement is claimed, so there is no before-and-after Metron budget. Initialization performs one bounded string parse and branch-name construction. It adds no I/O beyond the existing state creation.

The functional ceiling is enforced through the focused controller suite, including a long topic and malformed issue values:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl
```

If implementation adds a Git, GitHub, filesystem, or timing claim, the study must be amended before that change. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md), especially “Budgets” and “Measure how you will re-measure”, remains the measurement authority.

## 11. The fail-closed posture

Initialization stops before state creation when the task issue is malformed, the extracted number is absent or zero, the automatic branch is unusable, the override omits the exact issue token, or the branch equals the base. A late first task-issue record stops without changing state or ledger. Resume never repairs or renames a stored branch.

The observed failure becomes an Elenchus guard. Against the unfixed start, a fresh issue-backed fixture first shows that task issue receipt and branch identity cannot be established together. The fixed tree must make that case green, preserve the no-issue and legacy cases, and make the guard red again when issue-prefix construction or override validation is removed. The focused and complete suites then verify the surrounding controller behavior.

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md), especially “Triage, in order” and “Guard”, remains the failure and regression authority. A test that was never observed failing on the unfixed start is not reported as a guard.

## 12. Decisions and their homes

The issue-at-init timing, leading token, override rule, no-issue compatibility, and no-rename rule are governed Fiat behavior. Their durable decision record belongs in the `fiat-v5.10.1` generation row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, with issue 438 as evidence and the current frontier fields unchanged.

The CLI and branch construction live in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`. Red-to-green behavior lives in `plugins/hexaemeron/tests/test_hexctl.py`. User procedure and examples live in `plugins/hexaemeron/skills/fiat/SKILL.md` and its branch or push reference only where the cold read finds stale prose. The accepted study and runbook receive tracked copies in the repository's existing Fiat documentation location. Audit dispositions append to `audit/AUDIT.md`.

No standalone ADR is required because this is a decision about one governed skill and its evolution ledger is the established home. If implementation needs a state-version change, a receipt-shape change, a late branch mutation, or any edit to issue 363's held target, amend this study before code. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md), especially “Match what is already there” and “Where each thing lives”, remains the record-placement authority.
