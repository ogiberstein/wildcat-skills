# Runbook: Ariadne dataset predicate

Five steps. Each is one pull request stacked on the one below it. Both suites
run at every boundary:

```text
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne
```

The second is red at entry to step 1, for a reason step 1 fixes. Every later
step enters green and exits green.

## Step 1: Scaffold the run and repair the plugin link contract

**Goal.** Commit the study and the runbook, describe the shape the next steps
build, and make the ariadne suite green so later steps have a sound entry state.

**Entry.** The run branch `fiat/ariadne-dataset-predicate-with-schema-gates-conf`
off `main`. `plugins/ariadne/tests/test_docs.py` fails: `EVOLUTION.md` links to
`../../../hexaemeron/skills/VERSIONING.md`, outside the published plugin.

**Exit.** Both suites green, 24 repository tests and 310 ariadne tests with no
failures. `plugins/ariadne/docs/dataset.md` states the type URI, the field
table, and which gate owns which field.

**Files.**

- `plugins/ariadne/docs/dataset-predicate-study.md` (new, the study)
- `plugins/ariadne/docs/dataset-predicate-runbook.md` (new, this file)
- `plugins/ariadne/docs/dataset.md` (new, the shape)
- `plugins/ariadne/skills/ariadne/EVOLUTION.md` (link to the versioning
  contract by published URL rather than by a path that leaves the plugin)

**Tests.** No new tests. `test_docs.py` moves from one failure to zero, which
is the step's proof.

## Step 2: The predicate module and its published schema

**Goal.** Register `https://ariadne.wildcat.finance/dataset/v1` with its field
tables, its gates 2 and 5, its coverage and inputs checks, and a published
schema held to the module by the drift test.

**Entry.** Step 1's exit state.

**Exit.** `ariadne predicates` lists two types. A dataset statement verifies
with no gate reported unchecked. Both suites green, with the ariadne count up by
the new tests.

**Files.**

- `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` (new)
- `plugins/ariadne/scripts/ariadne_lib/predicates/__init__.py` (register it)
- `plugins/ariadne/scripts/ariadne_lib/core_predicate.py` (receive `missing`
  and `check_side`, moved verbatim)
- `plugins/ariadne/scripts/ariadne_lib/predicates/solidity_release.py` (import
  the two moved helpers from their new home; no other change)
- `plugins/ariadne/schemas/dataset-v1.json` (new)
- `plugins/ariadne/tests/test_dataset.py` (new)
- `plugins/ariadne/tests/test_schema_drift.py` (cover both predicates)
- `plugins/ariadne/tests/test_registry.py` (two registered types)

**Tests.** `test_dataset.py` covers each gate's pass and fail paths: gate 2 with
a missing producer field, a missing input digest and an unlisted subject digest;
gate 5 with a null baseline carrying differences, and with a changed entry
naming one side; coverage with an out-of-bounds gap, an overlapping pair, a
reversed interval and an absent `gaps` key; inputs with neither digest nor
disposition. The drift test runs its field-table comparisons over both
predicates. Expect roughly 30 new tests.

## Step 3: Conformance fixtures for the new type

**Goal.** Give another implementation a fixture set for the dataset predicate,
and hold the completeness test to every registered predicate's gates rather
than only the core ones.

**Entry.** Step 2's exit state.

**Exit.** Every new fixture breaches its named gate alone and no other. The
completeness test fails if a dataset gate ships without a fixture. Both suites
green.

**Files.**

- `plugins/ariadne/tests/fixtures/conformance/pass-dataset-*.json` (new)
- `plugins/ariadne/tests/fixtures/conformance/fail-gate2-dataset-*.json` (new)
- `plugins/ariadne/tests/fixtures/conformance/fail-gate5-dataset-*.json` (new)
- `plugins/ariadne/tests/test_conformance.py` (per-predicate completeness)
- `plugins/ariadne/docs/conformance.md` (name the new fixtures)

**Tests.** The existing three conformance tests extend to the new fixtures. One
new test asserts that each registered predicate's gate numbers each have a
breaching fixture.

## Step 4: The capture path and its command

**Goal.** Read a dataset release already on disk into a statement, taking every
disposition from the caller, and expose it as `capture-dataset`.

**Entry.** Step 3's exit state.

**Exit.** `capture-dataset` over the committed fixture release writes a
statement that `verify` passes with no unchecked gate. A release path containing
a `..` segment or a symlink out of the tree is refused. Both suites green.

**Files.**

- `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` (new)
- `plugins/ariadne/scripts/ariadne_lib/capture/__init__.py` (export it)
- `plugins/ariadne/scripts/ariadne.py` (the `capture-dataset` subcommand)
- `plugins/ariadne/tests/fixtures/dataset-release/v1/` and `v2/` (new)
- `plugins/ariadne/tests/test_capture_dataset.py` (new)
- `plugins/ariadne/docs/capturing-a-dataset.md` (new)

**Tests.** Digesting by streaming rather than whole-file reads; record counts
read from the files; a refused path outside the release tree; a refused gap that
falls outside the coverage bounds; `--out` writing atomically; the produced
statement verifying clean. Expect roughly 20 new tests.

## Step 5: Demonstrate, then reconcile the ledger and the marketplace prose

**Goal.** Run the study's demo path end to end, then bring every mutable
first-party prose surface and the ledger into agreement with what shipped.

**Entry.** Step 4's exit state.

**Exit.** The two-command demo path from the study exits 0 with seven gate lines
and none unchecked. `EVOLUTION.md` carries one new history row on the evolution
axis with a recomputed frontier digest. Every `marketplace-context` block and
every plugin landing README agrees. Both suites green.

**Files.**

- `plugins/ariadne/skills/ariadne/EVOLUTION.md` (new row, new held job or
  `mature`)
- `plugins/ariadne/skills/ariadne/SKILL.md` (frontmatter version, the frontier
  line, `Where it stops`, and the new predicate's section)
- `plugins/ariadne/README.md`, `plugins/ariadne/AGENTS.md`,
  `plugins/ariadne/docs/*.md`, `plugins/ariadne/examples/README.md`,
  `plugins/ariadne/audit/AUDIT.md`,
  `plugins/ariadne/tests/fixtures/forge-project/README.md`
  (the shared context block)
- `plugins/ariadne/.claude-plugin/plugin.json`,
  `plugins/ariadne/.codex-plugin/plugin.json`
- `.claude-plugin/marketplace.json`, `.agents/skills/ariadne/SKILL.md`,
  root `README.md`

**Tests.** No new tests. `tests/test_evolution_contract.py` and
`tests/test_marketplace_prose.py` are the proof, plus the demo path.
