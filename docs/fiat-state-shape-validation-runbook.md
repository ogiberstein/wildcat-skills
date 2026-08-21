# Runbook: validate Fiat state at the load boundary

This frontier run starts at `6980aef4c33ece8614b21e4ef8ff32dd19c3e7fc` on run branch `fiat/fiat-next-validate-the-shape-of-the-state-load-s`. Every step starts from the exact ref emitted by `hexctl next` and ends with its focused, repository, prose and boundary gates green. Every Fiat-created local commit uses `git commit -S`, passes `git verify-commit`, and carries exactly one `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and exactly one `Wildcat-Origin: shoggoth` trailer. Every pushed commit and GitHub-created merge must report `verified: true` with `reason: valid` before its receipt.

## Step 1: Track the accepted state-validation specification

**Goal.** Commit byte-identical tracked copies of the accepted issue 321 study and this runbook, then regenerate Horos for the enlarged tracked tree.

**Entry.** Exact base `6980aef4c33ece8614b21e4ef8ff32dd19c3e7fc`; study receipt accepted; root and Hexaemeron suites green; no product source changed.

**Exit.** `docs/fiat-state-shape-validation-study.md` and `docs/fiat-state-shape-validation-runbook.md` match their receipted `.hexaemeron` sources byte for byte. A fresh Horos document first differs from the exact-parent document only because two tracked Markdown files were added, then the regenerated tracked document matches a second fresh scan. Both Protasis modes, Imprimatur, per-file Brevitas where applicable, root, Hexaemeron, Promise Machine, boundary and tree gates are green. The signed step commit and any audit or fold commit pass local signature and exact-trailer checks. Prove it with:

```bash
cmp .hexaemeron/study.md docs/fiat-state-shape-validation-study.md
cmp .hexaemeron/runbook.md docs/fiat-state-shape-validation-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-state-shape-validation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-state-shape-validation-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-state-shape-validation-study.md docs/fiat-state-shape-validation-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-state-shape-validation-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 -m unittest tests.test_boundary_currency
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

**Files.** `docs/fiat-state-shape-validation-study.md`; `docs/fiat-state-shape-validation-runbook.md`; `.horos/boundary.json`; `audit/AUDIT.md` only when the Warden records its round.

**Tests.** Add no product test. Capture exact-parent versus fresh whole-document Horos inequality before regeneration and fresh versus regenerated identity afterwards. Run both specification checks, Imprimatur, runbook Brevitas, root, Hexaemeron, Promise Machine, boundary, tree and diff gates. Verify every local commit and both trailers; after push, require GitHub valid verification for every SHA in the exact step range.

**Disciplines.** protasis: the tracked copies preserve the accepted build contract. phylax: Horos owns the repository reading boundary and deterministic tracked census. ephoros: no unattended behaviour is added; the two whole-document comparisons are the evidence. metron: none, no performance claim. elenchus: the stale Horos census is the deliberate red specimen and regeneration fixes its cause. hypomnema: the study and runbook are run inputs; step 3's evolution row is the durable decision home.

## Step 2: Validate the state container spine in load_state

**Goal.** Make `load_state` reject every missing or wrong-kind required state container with one value-free path diagnosis shared by all commands and `verify`.

**Entry.** Step 1's signed head; tracked specifications match their receipts; controller and Fiat skill suites green; state version remains 1.

**Exit.** One ordered validator checks the root object, required `config` sections, `receipts`, `steps`, every step object, step `receipts`, step `audit`, `audit.rounds`, and every round object before returning state. Missing and wrong-kind specimens exit 1 with `state key '<path>' must be an object|array`, never echo the value, never traceback, and never change state or ledger bytes. `status`, `next`, `verify`, and one mutation emit the same line for the same fixture. Existing valid, legacy, lifecycle, receipt-semantic, signature and topology tests remain green. Red-before-fix tests first reproduce the traceback or divergent acceptance, then pass only through the central load boundary. Prove it with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
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

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; `plugins/hexaemeron/tests/test_hexctl.py`; `plugins/hexaemeron/tests/test_fiat_skill.py` only if its public contract assertions need the new gate; `tests/promise_machine_coverage.json` if the runtime digest changes; `audit/AUDIT.md` for Warden rounds.

**Tests.** Add a table-driven container matrix for missing and wrong-kind root, config, required config sections, receipts, steps, step members, step receipts, audit, rounds and round members. Assert deterministic first-fault order, exact value-free stderr, exit 1, unchanged state and ledger, command and verify parity, legacy state acceptance, and valid round/lifecycle behaviour. Prove each guard red before the validator exists. Run focused, root, complete Hexaemeron, Promise Machine and tree gates, then apply local and GitHub verification to every owned commit.

**Disciplines.** protasis: implement only the accepted container spine and stable diagnosis. phylax: local state bytes are untrusted input; parse, validate kind, avoid value echo, and refuse without mutation. ephoros: the path and expected kind answer the operator's first two questions; no new log or metric is warranted. metron: none, one already-loaded spine walk carries no speed claim. elenchus: every shape starts as a failing specimen and must fail again if its central check is removed. hypomnema: code owns the stable message and tests own its observable contract; do not add a schema document or ADR.

## Step 3: Advance the frontier and reconcile every mutable prose surface

**Goal.** Publish the completed frontier as `fiat-v5.9.1`, record issue 363 as the successor, reconcile suite-wide mutable first-party marketplace prose, and synchronize Hexaemeron publication and Promise Machine evidence.

**Entry.** Step 2's signed and audited head; the full state-shape matrix and prior lifecycle tests green; Fiat still reads `fiat-v4.9.1`, frontier revision `receipted-lint-rounds`, and the issue 321 held job.

**Exit.** Exactly one evolution-axis row advances Fiat to `fiat-v5.9.1`, changes the frontier revision to `state-shape-validation`, carries a digest independently recomputed from the new frontier fields, and holds issue 363's task-identity job as the open successor. The controller runtime, Fiat skill, runtime description, Hexaemeron package manifests and both marketplaces agree on the released versions. A cold read inventories all mutable first-party marketplace prose across the root, 14 plugins, canonical first-party skills, agents, references, manifests and marketplaces; every stale state-validation, version or successor statement is edited, while generated, vendored, content-addressed, fixture, completed-study and historical-audit boundaries remain untouched. The study's temporary-repository demo runs across every malformed fixture and command. Evolution, version, marketplace, Promise Machine, Horos, root, Hexaemeron, prose and tree gates are green. Prove it with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_evolution tests.test_evolution_contract tests.test_marketplace_prose tests.test_version_propagation
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <all-changed-prose>
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <each-applicable-changed-prose-file>
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <each-local-commit-sha>
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
gh api repos/<owner>/<repo>/commits/<each-pushed-or-github-merge-sha> --jq '.commit.verification | select(.verified == true and .reason == "valid")'
```

**Files.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md`; `plugins/hexaemeron/skills/fiat/SKILL.md`; `plugins/hexaemeron/skills/fiat/agents/openai.yaml`; Fiat references proved stale by the cold read; `plugins/hexaemeron/README.md`; Hexaemeron manifests; both marketplaces; `tests/test_evolution_contract.py`; `tests/test_version_propagation.py`; `tests/test_marketplace_prose.py`; `tests/promise_machine_coverage.json`; `.horos/boundary.json`; every other mutable first-party prose surface proved stale; `audit/AUDIT.md` for Warden rounds.

**Tests.** Run the malformed-state demo from a fresh temporary run and compare exact stderr and source bytes across `status`, `next`, `verify`, and a mutation. Independently recompute frontier version arithmetic and digest, verify one new row and the issue 363 successor, then run focused controller, evolution, version, marketplace, root, Hexaemeron, Promise Machine, Horos, applicable prose and tree suites. Record the cold-read inventory and exclusions. Apply signed local and GitHub valid-verification gates to every commit and merge.

**Disciplines.** protasis: close the held acceptance exactly and name the next frontier without importing it. phylax: publication adds no new boundary; diagnostics stay value-free and state remains untouched on refusal. ephoros: the CLI refusal is the signal and the demo proves it across commands. metron: none, no performance claim. elenchus: replay the full red matrix and lifecycle on the publication tree. hypomnema: the evolution row is the durable decision; mutable marketplace prose is reconciled exhaustively with exclusions stated, and historical evidence is not rewritten.
