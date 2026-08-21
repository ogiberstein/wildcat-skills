# Runbook: machine-built Fiat delegation packets

This run starts at `793b112c8f7824e54b8e6c97b06034d0d5270b85`. Each step branches from the exact ref emitted by `hexctl next`, ends with the focused and repository gates green, and carries no work from a later step. Every local commit in all three steps is made with `git commit -S`, passes local `git verify-commit`, and carries each exact Shoggoth trailer once. After push, every run-owned commit must have GitHub verification `verified: true` and `reason: valid` before merge. GitHub-created step and integration merge SHAs owe the GitHub check, not local trailers.

## Step 1: Track the accepted study and runbook

**Goal.** Commit the accepted issue 320 specification and this three-step runbook, then restore Horos currency against the enlarged tracked tree.

**Entry.** Exact base `793b112c8f7824e54b8e6c97b06034d0d5270b85`; controller study receipt accepted; run branch `fiat/fiat-1-emit-a-delegation-packet-for-every-direct`; root and Hexaemeron suites green before the branch is cut.

**Exit.** `docs/fiat-delegation-packets-study.md` and `docs/fiat-delegation-packets-runbook.md` match their receipted `.hexaemeron` sources byte for byte. The pre-regeneration Horos currency check is captured red because the tracked tree gained the two documents, then the regenerated boundary is current. Protasis, Imprimatur and per-file Brevitas accept both documents; root, Hexaemeron, Promise Machine and tree lints are green. Every step commit is signed and locally verified with each trailer exactly once. Prove it with:

```bash
cmp .hexaemeron/study.md docs/fiat-delegation-packets-study.md
cmp .hexaemeron/runbook.md docs/fiat-delegation-packets-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-delegation-packets-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-delegation-packets-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-delegation-packets-study.md docs/fiat-delegation-packets-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-delegation-packets-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-delegation-packets-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <each-local-commit-sha>
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
```

**Files.** `docs/fiat-delegation-packets-study.md`; `docs/fiat-delegation-packets-runbook.md`; `.horos/boundary.json`; `audit/AUDIT.md` when the audit round is recorded.

**Tests.** Add no product test. Record the Horos check failing before regeneration and passing afterwards. Run the root and Hexaemeron suites, both Protasis modes, Imprimatur, Brevitas once per document, Promise Machine, all three tree lints and `git diff --check`. After every local commit, run the three signature and trailer commands above. After push, query each exact PR-range SHA through GitHub and refuse merge unless verification is true with reason valid.

**Disciplines.** protasis: the tracked copies remain the build contract. phylax: Horos path and file-count handling touches the repository boundary. ephoros: no unattended runtime is introduced; the red and green Horos results are the evidence. metron: none, no performance claim. elenchus: the stale boundary is the deliberate red specimen and regeneration is the cause-level fix. hypomnema: the study and runbook are the durable decision record.

## Step 2: Emit total packets for all four agents

**Goal.** Make every `hexctl next` directive carry `state_sha256`, `agent` and `brief`, with exact surveyor, mason, warden and scribe inputs assembled from durable state and source-bound artefacts.

**Entry.** Step 1's signed head; tracked study and runbook match their receipts; existing lifecycle, branch-stack and controller verification tests are green; no Fiat source or agent contract has changed since the exact base.

**Exit.** Study, implement, audit-round and prose directives name surveyor, mason, warden and scribe respectively with only their contracted fields. All other directives carry `agent: null` and `brief: {}`. Study and runbook receipts bind artefact SHA-256 values; mason and warden packets carry the exact source blocks and refuse byte drift or ambiguous selectors. The scribe list is the sorted, bounded exact step diff. Two fresh `next` processes emit byte-identical JSON from unchanged evidence. Legacy states cannot gain a source-binding claim they lack. Red-before-fix tests first show all four missing packets and acceptance of mutated artefacts, then pass only after the controller fix. Prove it with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-delegation-packets-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-delegation-packets-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/agents/surveyor.md plugins/hexaemeron/agents/mason.md plugins/hexaemeron/agents/warden.md plugins/hexaemeron/agents/scribe.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/agents/surveyor.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/agents/mason.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/agents/warden.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/agents/scribe.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <each-local-commit-sha>
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; `plugins/hexaemeron/tests/test_hexctl.py`; `plugins/hexaemeron/tests/test_fiat_skill.py`; `plugins/hexaemeron/agents/surveyor.md`; `plugins/hexaemeron/agents/mason.md`; `plugins/hexaemeron/agents/warden.md`; `plugins/hexaemeron/agents/scribe.md`; `audit/AUDIT.md` when rounds are recorded.

**Tests.** Extend CLI lifecycle cases across every directive with an exact-key matrix for the four role briefs and the null packet. Add stable `state_sha256`, second-process reconstruction, study/runbook digest, mutated-byte, duplicate-selector, path-escape, byte-cap, 500-entry cap, deterministic sort, fenced-heading parity, legacy-state and missing-evidence guards. Capture the pre-fix failures before implementation. Run focused, root, Hexaemeron, Promise Machine, Protasis, per-file prose and tree gates. Apply the signature/trailer checks to every local content, audit, repair and fold commit; after push, require the valid GitHub result for every exact step-range SHA.

**Disciplines.** protasis: the packet carries source-bound runbook and risk-register material without changing their schema. phylax: packet assembly reads files, resolves paths and runs bounded Git inspection; caps, canonical containment and no-shell argv are required. ephoros: `agent`, `state_sha256`, source digests and named refusals answer the resume questions. metron: none, only hard resource caps and no speed claim. elenchus: each missing, stale, ambiguous, escaped or oversized input starts as a failing guard and closes at its cause. hypomnema: the four agent contracts are the only role-field homes and tests pin agreement with the controller.

## Step 3: Gate every Fiat commit and publish the generation

**Goal.** Enforce the permanent local and GitHub signature rule at commit-bearing receipts, then publish the ordinary `fiat-v4.9.1` and synchronized Hexaemeron package generation without moving Fiat's held frontier.

**Entry.** Step 2's signed head; four-agent packet suite green; exact packet schema and artefact digests stable; current Fiat ledger still reads `fiat-v4.8.1` with frontier revision `receipted-lint-rounds` and the held `load_state` text and digest unchanged.

**Exit.** The controller enumerates the exact run-owned commit range, runs local `git verify-commit`, counts both exact trailers once on every local commit, and refuses missing, duplicate, malformed or unsigned evidence. After push it checks every exact SHA with GitHub and accepts only `verified: true` plus `reason: valid`. `merge-step` and `integrate` apply the GitHub predicate to their GitHub-created merge SHA without demanding local trailers. Subprocesses use fixed argv, target cwd, time and byte caps, and named refusals. Fake `git` and `gh` guards cover exit failure, timeout, overflow, invalid JSON, false verification, invalid reason, missing SHA, range confusion and credential-safe errors; each is red before the fix. Fiat becomes `fiat-v4.9.1` as a generation while the frontier line and digest stay byte-identical. Hexaemeron package versions, both manifests and both marketplace records agree on the next package generation. Promise Machine bindings, runtime metadata, README/AGENTS prose, agent contracts and push discipline describe the shipped rule. Horos is current. Prove it with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_evolution tests.test_evolution_contract tests.test_marketplace_prose
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/push-discipline.md plugins/hexaemeron/README.md plugins/hexaemeron/AGENTS.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/EVOLUTION.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/README.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/AGENTS.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <each-local-commit-sha>
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
gh api repos/<owner>/<repo>/commits/<each-pushed-or-github-merge-sha> --jq '.commit.verification | select(.verified == true and .reason == "valid")'
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; `plugins/hexaemeron/skills/fiat/SKILL.md`; `plugins/hexaemeron/skills/fiat/EVOLUTION.md`; `plugins/hexaemeron/skills/fiat/references/push-discipline.md`; `plugins/hexaemeron/skills/fiat/agents/openai.yaml`; `plugins/hexaemeron/tests/test_hexctl.py`; `plugins/hexaemeron/tests/test_fiat_skill.py`; `plugins/hexaemeron/tests/test_evolution.py`; `tests/test_evolution_contract.py`; `tests/test_marketplace_prose.py`; `tests/promise_machine_coverage.json` if the runtime binding changes; `plugins/hexaemeron/README.md`; `plugins/hexaemeron/AGENTS.md`; `plugins/hexaemeron/.claude-plugin/plugin.json`; `plugins/hexaemeron/.codex-plugin/plugin.json`; `.claude-plugin/marketplace.json`; `.agents/plugins/marketplace.json`; `.horos/boundary.json`; `audit/AUDIT.md` when rounds are recorded. Cold-read root `README.md`, `AGENTS.md` and the four agent contracts, editing them only when they are proved stale.

**Tests.** Add unit and CLI tests for exact local ranges, signed success, unsigned failure, duplicate and missing trailers, intermediate commits, fake-binary non-zero exits, timeout, output caps and malformed output. Add fake GitHub cases for verified valid, verified false, every non-valid reason, missing commit and authentication/rate failure, plus separate GitHub-created merge coverage. Test that no token or raw signature reaches state, ledger or errors. Re-run packet guards, evolution/version checks, marketplace synchronization, Promise Machine, root and Hexaemeron suites, all prose and tree lints, Horos currency and `git diff --check`. Before every local commit, run the relevant suites; after it, run local verification and trailer counts. After each push and before each merge, check every exact GitHub SHA; halt on any unknown result.

**Disciplines.** protasis: all gates implement the accepted exact predicates and release boundary. phylax: local subprocess and GitHub response handling are new trust boundaries, so fixed argv, repository binding, caps, timeouts and secret-safe failures are mandatory. ephoros: refusal output names the SHA and failed predicate without exposing credentials. metron: none, subprocess caps are safety bounds and no performance gain is claimed. elenchus: every signature, range, transport and parse fault gets a red specimen before the fix and a regression that fails when removed. hypomnema: `EVOLUTION.md` records the generation, push discipline owns the permanent operating rule, mutable publication prose is cold-read, and the held frontier stays byte-identical.
