# Repository-wide Brevitas delivery

## Delivery contract

Start from clean `main` at `a7d001009e7e2a7e63343e206ef10ecabc2cab42`. Steps 1 and 2 merged into `main`; steps 3 through 13 merge sequentially into `chore/brevity-compress`. Each pull request appends a manual audit round to `audit/AUDIT.md`, runs the root contract and affected suites, passes Imprimatur then Vulgate then Brevitas, and preserves the batch entry source with Brevitas `--source`.

The entry corpus has 159 tracked Markdown files. The committed study and runbook made the planned corpus 161; concurrent PR #103 added 12 first-party Hexaemeron files, making the final corpus 173. Exclude Markdown under the vendored Hexaemeron `fizz`, `x-ray`, and `solidity-auditor` roots and every `LICENSE*` or `NOTICE*` path. Preserve embedded legal passages byte-for-byte. Check ignored snapshots after every step. Keep the three digest-bound Brevitas originals and Lazarus manifest-bound README unchanged and record their evidence refusals.

Use `step-<n>-<slug>` branches and scoped commits with the required Shoggoth trailers. Pull request text carries the audit pointer, proof command, `origin:ai`, and `<!-- wildcat-origin: shoggoth -->`. Read it back, wait for required checks, merge into the configured base, delete the branch, and receipt exact head and merge SHAs. Stop on a rejected push, failed external gate, required independent approval, or controller verification failure.

## Steps

## Step 1: Shared study, runbook, audit log, and evolution parser

**Goal.** Establish protected snapshots and compact the shared documentation contracts.
**Entry.** Current fetched `origin/main`, initially `a7d001009e7e2a7e63343e206ef10ecabc2cab42`.
**Exit.** `docs/brevitas-repository-pass/study.md` and `runbook.md` are committed; `audit/AUDIT.md` uses compact rounds; both evolution parsers accept the compact list history without changing ledger evidence.
**Files.** The two new docs, `audit/AUDIT.md`, root and Hexaemeron evolution tests, and only the parser code required by those tests.
**Tests.** Root contract tests, Hexaemeron evolution tests, changed-skill validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 2: Brevitas

**Goal.** Compress Brevitas canonical and portable Markdown while retaining its evidence contract.
**Entry.** Current fetched `origin/main` after step 1.
**Exit.** Brevitas and `.agents/skills/brevitas/` Markdown pass all three prose stages; the three `original.md` fixtures remain byte-identical with logged refusals.
**Files.** `plugins/brevitas/`, its portable entry, and `audit/AUDIT.md`.
**Tests.** Root contract, Brevitas suite and evals, Agent Skills validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 3: Sapheneia

**Goal.** Compress Sapheneia canonical and portable Markdown without changing its interaction contract.
**Entry.** Current `chore/brevity-compress` after step 2.
**Exit.** Sapheneia and its portable entry pass all three prose stages with requirements and frontier text intact.
**Files.** `plugins/sapheneia/`, `.agents/skills/sapheneia/`, and `audit/AUDIT.md`.
**Tests.** Root contract, Sapheneia suite, Agent Skills validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 4: Hermes

**Goal.** Compress Hermes canonical and portable Markdown without weakening its fail-closed gas proof.
**Entry.** Current `chore/brevity-compress` after step 3.
**Exit.** Hermes and its portable entry pass all three prose stages with commands, arithmetic requirements and frontier text intact.
**Files.** `plugins/hermes/`, `.agents/skills/hermes-gas-optimiser/`, and `audit/AUDIT.md`.
**Tests.** Root contract, Hermes suite, Agent Skills validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 5: Lemma

**Goal.** Compress Lemma plugin, baseline documentation and portable entry without changing chunk schemas or fixtures.
**Entry.** Current `chore/brevity-compress` after step 4.
**Exit.** All in-scope Lemma Markdown passes the prose stages; baseline and schema claims remain complete.
**Files.** `plugins/lemma/`, `.agents/skills/lemma-chunk/`, and `audit/AUDIT.md`.
**Tests.** Root contract, both Lemma suites, Agent Skills validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 6: Ariadne

**Goal.** Compress Ariadne plugin and portable entry while tightening its shared-versioning link exception.
**Entry.** Current `chore/brevity-compress` after step 5.
**Exit.** Ariadne Markdown passes all prose stages; its link test permits only the canonical shared `VERSIONING.md` target outside the plugin root.
**Files.** `plugins/ariadne/`, `.agents/skills/ariadne/`, the narrow link test, and `audit/AUDIT.md`.
**Tests.** Root contract, Ariadne suite, Agent Skills validation, link checks, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 7: Lazarus

**Goal.** Compress Lazarus plugin and portable entry without invalidating preserved evidence.
**Entry.** Current `chore/brevity-compress` after step 6.
**Exit.** Lazarus Markdown passes all prose stages except the logged manifest-bound README refusal, which remains byte-identical.
**Files.** `plugins/lazarus/`, `.agents/skills/lazarus/`, and `audit/AUDIT.md`; not the manifest-bound README.
**Tests.** Root contract and a fresh environment installed from `plugins/lazarus/requirements.lock`, Lazarus suite, Agent Skills validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 8: Alexandria

**Goal.** Compress Alexandria plugin and portable entry without changing its evidence and invocation contracts.
**Entry.** Current `chore/brevity-compress` after step 7.
**Exit.** Alexandria Markdown passes all prose stages with commands, limits and frontier text intact.
**Files.** `plugins/alexandria/`, `.agents/skills/alexandria/`, and `audit/AUDIT.md`.
**Tests.** Root contract, Alexandria suite, Agent Skills validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 9: Probitas

**Goal.** Compress Probitas sources and generated dossier while advancing only its generation axis.
**Entry.** Current `chore/brevity-compress` after step 8.
**Exit.** The renderer reproduces the dossier byte-for-byte; generation changes from `0.1.0` to `0.2.0`; frontier and Next Fiat job remain unchanged.
**Files.** `plugins/probitas/`, `.agents/skills/probitas/`, renderer sources, regenerated dossier, and `audit/AUDIT.md`.
**Tests.** Root contract, Probitas suite and renderer equality, Agent Skills validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 10: Pandects

**Goal.** Compress Pandects sources and generated catalogue while advancing only its generation axis.
**Entry.** Current `chore/brevity-compress` after step 9.
**Exit.** The renderer reproduces the catalogue byte-for-byte; generation changes from `1.1.0` to `1.2.0`; frontier and Next Fiat job remain unchanged.
**Files.** `plugins/pandects/`, `.agents/skills/pandects/`, renderer sources, regenerated catalogue, and `audit/AUDIT.md`.
**Tests.** Root contract, Pandects Python suite, renderer equality, `forge build`, `forge test`, Agent Skills validation, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 11: Tabularium

**Goal.** Compress Tabularium plugin and portable entry while tightening its shared-versioning link exception.
**Entry.** Current `chore/brevity-compress` after step 10.
**Exit.** Tabularium Markdown passes all prose stages; its link test permits only the canonical shared `VERSIONING.md` target outside the plugin root.
**Files.** `plugins/tabularium/`, `.agents/skills/tabularium/`, the narrow link test, and `audit/AUDIT.md`.
**Tests.** Root contract, Tabularium suite, Agent Skills validation, link checks, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 12: First-party Hexaemeron

**Goal.** Compress first-party Hexaemeron Markdown without changing vendored Pashov or legal bytes.
**Entry.** Current `chore/brevity-compress` after step 11.
**Exit.** Every in-scope Hexaemeron file passes the prose stages; vendored and legal snapshots remain identical.
**Files.** First-party `plugins/hexaemeron/` Markdown, its portable entries, and `audit/AUDIT.md`; no excluded path.
**Tests.** Root contract, Hexaemeron controller and Imprimatur suites, affected skill suites, Agent Skills validation, link checks, source preservation, protected SHA checks, and `git diff --check` pass.

## Step 13: Root and global Markdown

**Goal.** Compress root and shared Markdown and prove the complete 173-file corpus.
**Entry.** Current `chore/brevity-compress` after step 12, reconciled with PR #103 at `a66a6c830e810f5c00eaf378822428106feb5281`.
**Exit.** Root `README.md` is at most 300 lines; all mutable in-scope Markdown is clean; exclusions, legal passages and four refusals are identical; all tests pass; branches are deleted; Fiat verifies `done`.
**Files.** Root and global Markdown, including `README.md`, `AGENTS.md`, remaining `docs/`, `audit/AUDIT.md`, and the 12 new first-party Hexaemeron files.
**Tests.** Every root `AGENTS.md` command, all plugin suites, Pandects Forge tests, all link checks, every changed canonical skill validator, `git diff --check`, full SHA proof, Imprimatur, and Brevitas `--source` over 173 files pass.

## Acceptance

Done means steps 1 and 2 are merged into `main`, steps 3 through 13 are merged into `chore/brevity-compress`, exact head and merge SHAs are receipted, task branches are deleted, and no protected byte or evidence token moved. Root `README.md` is no longer than 300 lines. Probitas is generation `0.2.0`; Pandects is generation `1.2.0`; neither frontier changed. `hexctl status` and `hexctl verify` report `done`.
