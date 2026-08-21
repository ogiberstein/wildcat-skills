# Study: machine-built Fiat delegation packets

Assuming, unless corrected:

1. Issue 320 is an ordinary Fiat generation from `fiat-v4.8.1`; it must leave the `receipted-lint-rounds` frontier revision, frontier digest, current frontier and held `load_state` job byte-identical.
2. The exact starting SHA is `793b112c8f7824e54b8e6c97b06034d0d5270b85`, on run branch `fiat/fiat-1-emit-a-delegation-packet-for-every-direct` from `main`.
3. The four bundled agent contracts are authoritative for role inputs: surveyor, mason, warden and scribe. Other directives remain with the orchestrator.
4. The user's permanent signing rule applies to this run and every later Fiat run: every Fiat-created local commit is made with `git commit -S`, passes local `git verify-commit`, and carries each required Shoggoth trailer exactly once.
5. Before a pushed Fiat commit may merge, GitHub's commit response must say `verification.verified: true` and `verification.reason: "valid"`. GitHub-created step and integration merge commits use that GitHub check and are not required to carry local trailers.
6. `git`, `gh` and an authenticated GitHub repository are available at delivery time. Missing signing material, authentication or verification evidence halts the affected receipt; it is not waived silently.
7. `hexctl next` may invoke `git` and `gh`. It passes arguments without a shell. Each call has fixed time and byte caps. Empty output never earns success.
8. A packet may expose paths inside the named target and installed Hexaemeron plugin only. It must not read outside either boundary.

## 1. Problem statement

`hexctl next` names work but leaves an orchestrator to assemble the delegation brief from Fiat's skill, the active controller state, the study or runbook, and one of four agent contracts. Fiat's delegation prose names only surveyor and mason even though warden and scribe ship beside them. A fresh context can recover the phase from state, but it cannot recover the exact spawn input without repeating that assembly by hand.

The working prototype makes every directive structurally total. Existing directive fields stay in place, and every JSON object adds:

```json
{
  "state_sha256": "<sha256 of canonical state.json>",
  "agent": "surveyor | mason | warden | scribe | null",
  "brief": {}
}
```

Delegated phases carry a non-empty role-specific `brief`; inline, terminal and refusal directives carry `agent: null` and an empty object. A caller can therefore branch on data rather than phase lore. Re-running `next` in a fresh process against unchanged state and artefacts must return the same object byte for byte.

The same generation makes the user's signing rule executable. Commit-bearing receipts refuse until the exact Fiat-owned commit range passes the local signature and trailer checks, and pushed or GitHub-created commits refuse until GitHub reports `verified: true` with reason `valid`.

The demo path is a fresh temporary run driven through study, runbook, implement, audit, prose, push, merge-step and integrate. At each phase, `next` must emit the expected agent and exact brief or the explicit null packet. A second process must reproduce each directive. Mutation, unsigned-commit, duplicate-trailer, missing-remote-verification and invalid-reason specimens must fail with named messages. The focused command is:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
```

The complete proof also runs:

```bash
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
```

## 2. Prior art

Current `hexctl.py` already emits deterministic phase JSON, builds branch plans, records study and runbook artefact paths, carries the security-suite receipt, stores audit configuration and hashes state into its ledger. It does not add an agent, a brief, an artefact digest or a commit-verification gate. The current agent contracts state these inputs:

- surveyor: topic, target directory, base ref and study output path;
- mason: the runbook step, branch and `branch_from` ref;
- warden: step branch, stacked audit branch, suite ids, plugin root, audit log, round and risk-register seed;
- scribe: changed-file list, PR base, PR draft path and plugin root.

Protasis `v3.4.0` fixed the risk-register line as `id | boundary | check`, and `v4.5.0` now checks that shape. Its ledger records why a second receipt-time interpretation was rejected: two scanners drift. Fiat should carry the source-bound block and its study digest, not invent another risk grammar.

The last two merged Fiat-specific pull requests were read:

- PR 276, “Carry a run's unfinished work forward to the next study”, shipped `fiat-v4.8.1`. Its carried-forward installed-controller warning is answered here by designing against the checkout controller at that exact version; an installed copy still needs the existing currency procedure before a later run can rely on this generation. Its Horos CI and landing-README items do not belong to issue 320 and remain outside this run.
- PR 239, “Fiat: a frontier run proves its ledger update”, shipped `fiat-v4.7.1` and carried no `## Carried forward` section. Its explicit sequencing rule applies: issue 320 is generation work and cannot displace the held `load_state` job. Its unrelated Kronos scoring note stays outside this run.

PR 293 was also read because it is the most recent merged pull request touching Fiat. It added the Promise Machine declaration without changing Fiat behaviour. Its carried-forward host-picker captures and other skills' frontiers do not enter this issue.

The Fiat audit history was read. The receipted-lint run found several malformed-state tracebacks, deliberately left full `load_state` validation as the held frontier, and noted that `verify` does not validate arbitrary round shapes. This study neither solves nor obscures that job. A separate audit entry found a Fiat-created commit with only one provenance trailer; amending it fixed the run. That is direct evidence that prose alone does not hold the signing rule. The carried-forward lack of a Hexaemeron CI workflow has since been overtaken by repository checks but does not change the local and GitHub verification gates specified here.

Outside prior art is limited to the interfaces already used by the repository: `git commit -S`, `git verify-commit`, `git rev-list`, and the GitHub REST commit object's `commit.verification` fields through `gh api`.

## 3. Constraints and non-goals

The build starts at `793b112c8f7824e54b8e6c97b06034d0d5270b85`. It uses Python 3 and the standard library, the existing Git and GitHub CLI, JSON controller output, and the current hash-chained state model. No dependency is added.

The packet is additive: existing top-level directive fields and receipt commands keep their meaning. `state_sha256`, `agent` and `brief` appear on every directive, including `halted`, `done`, `resolve-security-suite`, `close-audit`, `audit-verdict`, `push`, `merge-step` and `integrate`. Only study, implement, audit-round and prose name an agent.

The exact briefs are:

| Agent | Brief fields | Source |
| --- | --- | --- |
| `surveyor` | `topic`, `target_dir`, `base_ref`, `output_path` | state, resolved target and `.hexaemeron/study.md` |
| `mason` | `runbook_step`, `branch`, `branch_from` | source-bound runbook step and branch plan |
| `warden` | `step_branch`, `stacked_branch`, `security_suite`, `plugin_root`, `audit_log_path`, `round`, `risk_register` | branch plan, config, receipts and source-bound study block |
| `scribe` | `files`, `pr_base`, `pr_draft_path`, `plugin_root` | exact step diff, branch plan and `.hexaemeron/steps/<n>/pr.md` |

`runbook_step` is the exact Markdown step block plus its artefact path, SHA-256, step number and title. `risk_register` is the exact fenced block plus its artefact path and SHA-256; the existing Protasis check remains the shape authority. `files` is the sorted, unique set of changed paths in the exact `pr_base..<step branch>` range, bounded by count and output bytes. The scribe applies its own prose scope to that list.

Study and runbook receipts record the artefact SHA-256. A later packet refuses if the current bytes differ. Existing pre-generation states without those digests keep their old non-delegated behaviour only until their current run ends; they do not receive a packet that claims source binding it cannot establish.

Expected release surfaces are `fiat-v4.9.1` and the next synchronized Hexaemeron package generation from `1.5.1`. The Fiat generation row retains the prior frontier revision and digest byte for byte. Protasis stays `v4.5.0`; this run consumes its settled format and does not change its promise.

Non-goals are automatic agent spawning, changing a model choice, validating agent output, redesigning the controller state, solving `load_state`, changing Protasis's schema, signing GitHub's own merge commits locally, attesting pre-existing human commits, supporting a non-GitHub forge, or treating GitHub verification as proof of commit authorship beyond GitHub's stated result.

**Always.** Run focused and complete suites before every Fiat-created commit; use `git commit -S`; run `git verify-commit` locally; count each exact Shoggoth trailer once; run Imprimatur on shipped prose; check every pushed Fiat commit and every GitHub-created merge SHA through the GitHub commit endpoint before merge or receipt.

**Ask first.** Adding a dependency; changing the state version or public directive keys beyond the additive packet; changing GitHub merge strategy; touching CI; weakening an exact verification result; widening path, subprocess or network access beyond the named target, plugin and GitHub repository.

**Never.** Move or rewrite the held `load_state` frontier in this generation; accept a missing or malformed brief; infer verification from a zero-length response; use a shell for Git or GitHub commands; mark a `verified: false` or non-`valid` reason as acceptable; add trailers to pre-existing human commits; bypass a merge gate; claim a signature, test or remote check ran when it did not.

## 4. Design options

### Option A: prose templates only

Add all four agents to Fiat's delegation section and spell out their briefs. This is the smallest diff, but a resumed context still assembles fields by hand and nothing rejects an omitted or stale value. It fails the issue's machine-built requirement and the permanent signing rule.

### Option B: controller packets with source-bound artefacts and receipt gates (chosen)

Make `next` add the total envelope and build each role brief from state, receipts, resolved paths, bounded Git output and digest-checked study/runbook bytes. Keep Protasis authoritative by carrying its exact block instead of reinterpreting its fields. Add local and GitHub commit checks to the receipts that consume commit SHAs and to the full pushed step range.

This is the cheapest construction that removes hand assembly and fails closed. Its named trade is a narrow loss of controller hermeticity: commit verification introduces bounded Git and GitHub subprocesses. The Phylax controls in sections 5 and 9 close that boundary.

### Option C: separate packet manifest generated beside state

Write `.hexaemeron/delegations/<phase>.json` and have `next` point at it. This gives inspectable files but creates another mutable truth surface, needs garbage collection and can disagree with state after every receipt. It adds more state than the four consumers need.

### Option D: external wrapper around unchanged `hexctl`

A wrapper could combine `next`, state, Git and the agent documents. It preserves controller hermeticity, but becomes a second controller whose version and failure rules are not in the ledger. The user asked for the rule inside Fiat going forward, so this option is rejected.

## 5. Risk register seed

```risk-register
packet-state-drift | state.json and a freshly rebuilt delegation packet | state_sha256 binds the directive and two fresh next processes emit identical JSON
artefact-drift | receipted study and runbook bytes used by mason and warden | next refuses a changed digest instead of emitting stale or reinterpreted content
protasis-grammar-drift | Fiat's extraction of the source-bound step and risk block | parity fixtures cover fenced headings, item boundaries, byte caps and the v3.4 three-field block without creating a second shape verdict
file-range-confusion | git range used to build the scribe list and commit verification set | the range is exactly pr_base..head, sorted and bounded, and excludes pre-existing base commits
subprocess-control | argv and output of git and gh invoked by hexctl | no shell is used, cwd is the target, time and byte caps apply, and non-zero or malformed output is a named refusal
local-signature-gap | every Fiat-created commit in the step range | git verify-commit succeeds and both exact Shoggoth trailers occur once on every commit
remote-verification-gap | every pushed Fiat commit before merge | GitHub returns verified true and reason valid for each exact SHA; absent, false, unknown or malformed results stop the receipt
merge-origin-confusion | GitHub-created step and base merge commits | phase identifies them as GitHub commits and requires the same remote verification without adding local trailers
legacy-state-overclaim | a pre-generation run with no artefact digest or packet fields | it retains compatible legacy directives or stops with a migration message, never emits a source-bound claim
path-escape | target, plugin, artefact and PR-draft paths in a brief | canonical paths stay inside the named target or plugin root and symlink escapes are refused
```

The audit loop must cite each id as reviewed or not applicable. Signing and remote-verification faults are release blockers, not accepted leads.

## 6. Glossary seeds

| Term | Meaning | Nearest boundary |
| --- | --- | --- |
| Delegation packet | The additive `state_sha256`, `agent` and `brief` fields on one `next` directive. | It does not receipt agent work. |
| Inline directive | A directive with `agent: null` and `brief: {}` that remains with the orchestrator. | Null is an explicit owner decision. |
| Source-bound block | Exact study or runbook bytes named with their path, digest and selector. | Its digest does not judge the content. |
| Fiat-created commit | A commit created locally as part of the run-owned step range. | It excludes base history and GitHub-created merges. |
| Pushed commit set | Every SHA in the exact step `pr_base..<head_commit>` range after the branch is on GitHub. | No commit outside the range is relabelled. |
| Valid GitHub verification | `commit.verification.verified` is true and `commit.verification.reason` is exactly `valid` for the named SHA. | It states GitHub's result, not general authorship. |
| Post-compaction reconstruction | A fresh `hexctl next` call derives the same current packet from durable state and source-bound artefacts. | It does not use chat history. |

## 7. Sources

- Issue 320: `https://github.com/wildcat-finance/skills/issues/320`.
- Exact start: Git commit `793b112c8f7824e54b8e6c97b06034d0d5270b85`.
- Fiat controller and contract: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `SKILL.md`, `EVOLUTION.md`, `references/push-discipline.md`.
- Agent contracts: `plugins/hexaemeron/agents/surveyor.md`, `mason.md`, `warden.md`, `scribe.md`.
- Controller and prose tests: `plugins/hexaemeron/tests/test_hexctl.py`, `test_fiat_skill.py`.
- Protasis contract and settled register: `plugins/hexaemeron/skills/protasis/SKILL.md`, `EVOLUTION.md`, `scripts/protasis.py`.
- Last merged Fiat-specific changes: PR 276 and PR 239; most recent target-touching PR: PR 293.
- Fiat audit record: `audit/AUDIT.md`, especially “Receipted lint rounds” and the provenance-trailer finding recorded on 18 August 2026.
- Version law: `plugins/hexaemeron/skills/VERSIONING.md`.
- Promise boundary: root `PROMISE_MACHINE.md`, contract `promise-machine/v1`.
- Git verification: `git-verify-commit(1)` and `git-rev-list(1)` from the installed Git documentation.
- GitHub commit response: REST `GET /repos/{owner}/{repo}/commits/{ref}`, field `commit.verification`.

## 8. Signals, and the questions behind them

This is a command-line controller, not an unattended service. Ephoros therefore does not require production telemetry. The controller's existing JSON and refusal messages are the operational signals.

The questions and answers are:

1. “Which agent owns this action?” Every `next` response answers with `agent`, including explicit null.
2. “Was this brief built from the current state?” `state_sha256` answers, and a fresh process reproduces it.
3. “Which source bytes supplied the step or risk seed?” Mason and warden briefs carry artefact paths and SHA-256 values.
4. “Why can this commit not merge?” Signature, trailer, commit-range and GitHub verification refusals name the SHA and failed predicate without printing signature material or credentials.

The packet step emits the first three; the commit-gate step emits the fourth through bounded command results. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) remains the authority for signal content.

## 9. Boundaries, per capability

Packet assembly reads controller state, the receipted study and runbook, the Git step range and installed plugin paths. The value at those boundaries is a context-independent brief. Controls are canonical in-scope paths, regular-file checks, byte and entry caps, stored artefact digests, stable sort order and a state fingerprint.

Git inspection executes a local binary against the target repository. The value is the exact owned commit set and cryptographic signature result. Controls are fixed argv, no shell, target cwd, explicit SHA/ref validation, timeout and output caps, non-zero refusal, and tests with adversarial fake binaries.

GitHub inspection crosses the network through authenticated `gh`. The value is GitHub's verification result for already-pushed SHAs. Controls are a repository resolved from the target, one endpoint per exact SHA, JSON type checks, fixed `verified` and `reason` predicates, timeout and response caps, and refusal on auth, rate, transport or parse failure. No token or raw signature is written to state or the ledger.

Agent output stays outside the controller. A packet authorises the named role to start from declared inputs; it does not validate the role's conclusions or receipt its work. [Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the detailed subprocess, filesystem and remote-host controls.

## 10. The budget, or its absence

No speed improvement is claimed, so Metron has no comparative performance budget. There are hard resource ceilings instead: study and runbook reads retain the existing 2 MiB class of cap; Git file and commit lists are capped at 500 entries and 2 MiB; each Git or GitHub subprocess gets a 30-second timeout and 2 MiB combined output cap. The exact limits may be lowered during implementation but not raised without an amendment.

The budget check is a focused test that feeds one item past each cap and expects a named refusal:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl
```

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) remains the authority if implementation makes a speed claim.

## 11. The fail-closed posture

Packet production stops on malformed required state, a missing role field, an unreadable or digest-mismatched artefact, a step or register selector that earns no unique match, a path escape, an unbounded Git result or any subprocess failure. Inline directives remain explicit; an unknown phase never receives a guessed agent.

Commit-bearing receipts stop on an empty range where a commit is owed, a malformed SHA, failed `git verify-commit`, missing or duplicate exact trailer, pushed SHA absent from GitHub, `verified` not true, `reason` not `valid`, or a GitHub-created merge SHA that lacks the valid remote result. A network failure is unknown evidence and blocks merge; it is not converted to false or success.

Each fault gets an Elenchus guard: reproduce the exact failure, assert the named message and transition refusal, fix the cause, then prove the specimen fails again when the fix is removed. Existing positive lifecycle tests must remain green. [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns that failure workflow.

## 12. Decisions and their homes

The packet schema, explicit-null rule, source-binding choice, legacy-state treatment, exact commit-range definition, local-versus-GitHub verification split and bounded subprocess exception are expensive to reverse. Record them in the Fiat `EVOLUTION.md` generation row, with the operating procedure in `SKILL.md` and `references/push-discipline.md`. Keep the four role-specific fields in their agent files and pin their agreement in `test_fiat_skill.py`; do not create five independent copies of the table.

The controller implementation and refusal codes live in `hexctl.py`; behavioural evidence lives in `test_hexctl.py`. Publication versions stay synchronized through both plugin manifests and marketplace records. The held frontier text remains untouched and is protected by the existing generation test.

No design choice remains unresolved. The only delivery-time unknown is environmental: whether the configured signing key and GitHub verification service are available. The specified response is a recorded halt, not a different design. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) decides whether the implementation needs an additional ADR after the cold read; this study expects the evolution row and push-discipline record to be sufficient because no public data format outside Fiat's directive JSON is introduced.
