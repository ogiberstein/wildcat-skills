# Runbook: carry task issue numbers in Fiat branch names

This generation run starts at `6412c85d7cfd352e21fcc3dc0d8cef39a0649976`
on `fiat/carry-the-task-issue-number-in-run-and-step-bran`. The installed
`fiat-v4.8.1` controller created and pushed that branch before it knew issue
438. The branch stays unchanged. Fresh fixtures use the checked-in controller
to prove the new behavior.

Every step starts from the exact ref emitted by `hexctl next`. Every step ends
with its focused, repository, prose, and boundary gates green. Every
Fiat-created commit uses `git commit -S`, passes `git verify-commit`, and has
exactly one of each required trailer:

```text
Co-authored-by: Shoggoth <shoggoth@wildcat.finance>
Wildcat-Origin: shoggoth
```

After each push or GitHub merge, GitHub must report `verified: true` with
`reason: valid` for every new commit.

## Step 1: Track the accepted issue-branch specification

**Goal.** Commit exact tracked copies of the accepted issue 438 study and this
runbook. Regenerate Horos for the larger tracked tree.

**Entry.** Exact base `6412c85d7cfd352e21fcc3dc0d8cef39a0649976`;
the study receipt is accepted; the runbook receipt is accepted; no product
source has changed.

**Exit.** `docs/fiat-task-issue-branch-names-study.md` and
`docs/fiat-task-issue-branch-names-runbook.md` match their `.hexaemeron`
sources byte for byte. A fresh Horos scan first differs only because the two
Markdown files are new. The regenerated boundary file matches a second fresh
scan. Protasis, Imprimatur, Brevitas, the two complete suites, Promise Machine,
the boundary test, tree lints, and diff checks pass. The signed commit passes
the local signature and trailer checks.

```bash
cmp .hexaemeron/study.md docs/fiat-task-issue-branch-names-study.md
cmp .hexaemeron/runbook.md docs/fiat-task-issue-branch-names-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-task-issue-branch-names-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-task-issue-branch-names-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-task-issue-branch-names-study.md docs/fiat-task-issue-branch-names-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-task-issue-branch-names-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 -m unittest tests.test_boundary_currency
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <commit-sha>
```

**Files.** `docs/fiat-task-issue-branch-names-study.md`;
`docs/fiat-task-issue-branch-names-runbook.md`; `.horos/boundary.json`;
`audit/AUDIT.md` only when the audit records its round.

**Tests.** Add no product test. Compare each tracked document with its accepted
source. Prove that one Horos regeneration is sufficient. Run the specification,
root, Hexaemeron, Promise Machine, boundary, tree, diff, signature, and trailer
gates.

**Disciplines.** protasis: the tracked files preserve the accepted contract.
phylax: Horos owns the repository read boundary. ephoros: the document and scan
comparisons are the bounded signals. metron: none, no performance claim.
elenchus: the stale Horos document is the red specimen. hypomnema: the study and
runbook record this run; the evolution row in step 3 records the durable choice.

## Step 2: Bind task issues to run and step branch names

**Goal.** Add issue-aware initialization to `hexctl` and guard the behavior with
red-before-fix tests.

**Entry.** Step 1's signed head; tracked specifications match their accepted
sources; existing controller and Fiat tests pass; state version is 1.

**Exit.** `init --task-issue <url>` accepts a URL path ending in one positive
issue number. It writes the unchanged URL receipt and the derived run branch in
the same initial state transition. The automatic branch uses
`slug("<issue>-<topic>", 48)`, so a long topic cannot remove the leading number.
An explicit override remains exact but must start with `fiat/<issue>-`. Invalid
issue values and invalid overrides fail before state creation. A late first
`record task_issue` fails without changing state or ledger. A repeated matching
receipt remains idempotent, and a different receipt fails. No-issue names and
stored legacy branches remain byte-identical. Step directives inherit the
issue-bearing run branch without a second parser. Promise Machine evidence is
updated for the controller digest. Focused and complete gates pass.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <commit-sha>
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
`plugins/hexaemeron/tests/test_hexctl.py`;
`tests/promise_machine_coverage.json`; `audit/AUDIT.md` for audit rounds.

**Tests.** First run the issue-aware tests against the exact entry controller
and preserve the failure output. Cover a normal issue URL, a long topic, an
empty normalized topic, issue zero, a malformed path, accepted and rejected
overrides, no state on refusal, no-issue name identity, step propagation, late
record refusal, matching repeat, different repeat, and legacy stored-name
identity. Remove the new branch construction once to prove that its guard goes
red. Then run the focused, complete, Promise Machine, tree, diff, signature,
and trailer gates.

**Disciplines.** protasis: implement only the accepted initialization and
compatibility rules. phylax: CLI text is untrusted; parse one bounded path,
validate before writes, and do not fetch it. ephoros: exit status, one bounded
error, init output, state JSON, and step directives answer the operator
questions. metron: none, one bounded string parse has no speed claim. elenchus:
the entry controller and removal test prove the guard. hypomnema: code owns the
stable refusal; tests own its observable contract.

## Step 3: Publish Fiat v5.10.1 and demonstrate issue-aware branches

**Goal.** Publish the generation, reconcile mutable prose and version surfaces,
and run the checked-in controller through the issue 438 lifecycle.

**Entry.** Step 2's signed and audited head; issue-aware controller tests and all
prior lifecycle tests pass; Fiat still reads `fiat-v5.9.1`; the held issue 363
frontier is unchanged.

**Exit.** One `generation` row advances Fiat to `fiat-v5.10.1`. The row cites
issue 438 and keeps the `state-shape-validation` revision, complete issue 363
frontier text, and digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`
byte-identical. Hexaemeron package version `1.5.4`, both marketplaces, both
manifests, runtime prose, Fiat instructions, and tests agree. The instructions
record a known issue during `init` before branch creation. Branch and push
references state the leading-number and override rules. Historical evidence is
unchanged. A fresh temporary demo produces an issue-bearing run and step branch,
preserves an issue-free name, and refuses a malformed issue, a numberless
override, and a late first receipt without state drift. All focused, complete,
version, evolution, marketplace, Promise Machine, Horos, prose, tree, diff,
signature, and trailer gates pass.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_evolution tests.test_evolution_contract tests.test_marketplace_prose tests.test_version_propagation
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <all-changed-prose>
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <each-applicable-prose-file>
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <commit-sha>
gh api repos/radup1337/skills/commits/<pushed-sha> --jq '.commit.verification | select(.verified == true and .reason == "valid")'
```

**Files.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md`;
`plugins/hexaemeron/skills/fiat/SKILL.md`;
`plugins/hexaemeron/skills/fiat/agents/openai.yaml` only if stale;
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`;
`plugins/hexaemeron/README.md`; both Hexaemeron manifests; both marketplaces;
`plugins/hexaemeron/tests/test_fiat_skill.py`; `tests/test_evolution_contract.py`;
`tests/test_version_propagation.py`; `tests/test_marketplace_prose.py` only if
its public promise changes; `tests/promise_machine_coverage.json` if the final
controller digest changes; `.horos/boundary.json`; `audit/AUDIT.md`.

**Tests.** Run a fresh temporary issue 438 demo and compare exact branch names,
receipt value, step prefix, exit status, and unchanged bytes after refusals.
Independently verify version arithmetic, one new generation row, and byte-exact
frontier preservation. Run the focused, complete, version, evolution,
marketplace, Promise Machine, Horos, applicable prose, tree, diff, signature,
trailer, and GitHub verification gates.

**Disciplines.** protasis: publish only the accepted generation and preserve the
held frontier. phylax: publication adds no network path to the controller.
ephoros: the demo proves the CLI signals; no log, metric, trace, or alert is
warranted. metron: none, no performance claim. elenchus: replay the original
defect and all compatibility specimens on the publication tree. hypomnema: the
evolution row records the durable decision; mutable instructions are reconciled,
and historical records stay untouched.
