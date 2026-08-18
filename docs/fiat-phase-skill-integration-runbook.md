# Runbook: fold the six phase skills into Fiat's loop as contract

Four steps. Each is one pull request, green at both ends, and the audit round
for every step runs the three tree lints, because the security-suite waiver
names them as this run's mechanical check.

## Step 1: Protasis takes the content contract

**Goal.** Fiat names no study or runbook content rule of its own.
**Entry.** `main` at the run's base, both suites green.
**Exit.** `references/study.md` and `references/runbook-format.md` are gone;
Fiat's directive table points the two phases at protasis and its phase notes
carry the artefact paths, `steps.json` shape and receipt commands; protasis's
supersession paragraph says it is the authority rather than that it will be;
protasis's ledger records the completed evolution. Proof:
`python3 -m unittest discover -s tests` and
`python3 plugins/hexaemeron/tests/run_tests.py` pass, and the record lint
finds no dangling pointer.
**Files.** `plugins/hexaemeron/skills/fiat/SKILL.md`, two deleted references,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`docs/fiat-phase-skill-integration-study.md`,
`docs/fiat-phase-skill-integration-runbook.md`,
`plugins/hexaemeron/tests/test_fiat_skill.py` where its pins move with the
format.
**Tests.** Existing suites; any pin in `test_fiat_skill.py` that names the
deleted files or the old phase-note prose moves with the change.

## Step 2: the loop names the phase skills as contract

**Goal.** Each phase's reference states which skills it runs under and what
that requires, rather than suggesting consultation.
**Entry.** Step 1 merged.
**Exit.** `references/audit-loop.md`'s non-Solidity round requires the three
tree lints with exit 0 and logs their result per round;
`references/prose-pass.md` opens with hypomnema's decision and pointer lint
before the masks; Fiat's implement phase note binds metron's baseline rule to
performance-motivated changes and elenchus to failures worked mid-step. Proof:
both suites, three lints clean.
**Files.** `references/audit-loop.md`, `references/prose-pass.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`.
**Tests.** Existing suites; `test_fiat_skill.py` pins move if touched.

## Step 3: every surface agrees

**Goal.** The plugin contract, both READMEs, the portable entrypoints, the
codex manifest and the marketplace manifests describe the same loop.
**Entry.** Step 2 merged.
**Exit.** The plugin `AGENTS.md` fiat row and README loop table name the phase
skills where the phases run them; the root README's Hexaemeron paragraph and
status row match; the seven `.agents/skills/` entrypoints carry no stale
supersession language; the plugin version is `1.2.0` in all three manifests so
installations re-fetch. Proof: both suites, marketplace prose tests, three
lints.
**Files.** `plugins/hexaemeron/AGENTS.md`, `plugins/hexaemeron/README.md`,
root `README.md`, `.agents/skills/hexaemeron/SKILL.md` and the six phase-skill
entrypoints, `plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`.
**Tests.** Existing suites; marketplace prose tests hold the surfaces equal.

## Step 4: cold read, then close the ledger

**Goal.** Every document this run touched reads clean to a stranger, and the
ledgers record the completed evolution exactly once.
**Entry.** Step 3 merged.
**Exit.** Imprimatur scores every touched document 100 with zero defects and
the brevitas linter exits 0 on each; wording that only a participant in this
run could parse is rewritten; Fiat's ledger takes its evolution to
`fiat-v3.3.1` with one evidenced next job or a mature close. Proof, which is
also the run's demo path: both suites, all three tree lints, imprimatur and
brevitas over the touched set, and `hexctl verify` proving the ledger chain.
**Files.** Documents flagged by the cold read,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md` frontmatter.
**Tests.** Existing suites.
