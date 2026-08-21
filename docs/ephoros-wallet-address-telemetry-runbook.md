# Runbook: Ephoros catches telemetry keyed by wallet address across Python and TypeScript

Derived from `.hexaemeron/study.md`, whose chosen design is option A: one rule,
E005, inside `ephoros.py`, with the TypeScript surface read through the shared
masked lexer. Four steps, dependency order, one pull request each. Every step
ends with both suites green: `python3 plugins/hexaemeron/tests/run_tests.py`
and `python3 -m unittest discover -s tests`, run from `/home/user/skills`.

One allocation is corrected against the base rather than inherited: the
study's item 12 named ADR-008 as the next free decision-record number, and
`docs/decisions/` on the starting ref already holds ADR-008 and ADR-009. The
decision and its home stand; its number is ADR-010.

## Step 1: Scaffold: commit the study and runbook

**Goal.** Land the reviewed spec documents in the repository the way every
prior run in this tree has.
**Entry.** Branch from `fiat/ephoros-catches-telemetry-keyed-by-wallet-addres`
at `main`, `6412c85d7cfd352e21fcc3dc0d8cef39a0649976`.
**Exit.** `docs/ephoros-wallet-address-telemetry-study.md` and
`docs/ephoros-wallet-address-telemetry-runbook.md` committed;
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <each>`
exits 0; `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py
--study docs/ephoros-wallet-address-telemetry-study.md` and
`python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py
docs/ephoros-wallet-address-telemetry-runbook.md` exit 0; both suites pass.
**Files.** `docs/ephoros-wallet-address-telemetry-study.md`,
`docs/ephoros-wallet-address-telemetry-runbook.md`.
**Tests.** None written; both suites run as the regression gate.
**Disciplines.** phylax: none, committing documents opens no boundary.
ephoros: none, a document does not run unattended. metron: none, no
performance claim. elenchus: none, no failure in hand. hypomnema: the spec
documents are the shipped record of this phase; the two decision records the
study names land in step 4, where their content exists.

## Step 2: E005 in Python and block-YAML, with the E002 subset guard

**Goal.** Report an address used as a metric label, a dashboard key or a log
index in Python source and in supported block-YAML label mappings.
**Entry.** Step 1's exit state, branched from its step branch.
**Exit.** `python3 -m unittest plugins.hexaemeron.tests.test_ephoros_checker`
passes with the new cases, each positive recogniser case having been observed
red before its recogniser landed;
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
scripts` exits 0; both suites pass.
**Files.** `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`,
`plugins/hexaemeron/tests/test_ephoros_checker.py`,
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/` (new Python and
YAML specimens).
**Tests.** Positive: an address-named label in the `labels=[...]` constructor
style, the `.labels(wallet_address=...)` instance style, a 40-hex literal
label, an address-shaped dashboard key, an address-shaped log-index key or
`index=` argument, and an address-named key under a supported block-YAML
`labels:` mapping. Negative: an address in an event's fields, an address in a
message argument, and `print`. Guards: the label `wallet_address` yields E005
and not E002 while a `hash`-named label keeps E002; `# ephoros: allow <why>`
suppresses on the line and the line above; a bare pragma suppresses nothing.
Expected count: at least twelve new cases over the 46 existing.
**Disciplines.** phylax: none, the checker reads the same trees it already
reads. ephoros: none, the deliverable is a terminal lint (study item 8).
metron: none, no performance claim. elenchus: every recogniser case follows
the guard-test convention, red before the fix and kept green. hypomnema: the
E005/E002 subset decision is incurred here and recorded in step 4, in the
ledger row and the SKILL.md mechanical subset, the homes item 12 names.

## Step 3: The TypeScript surface through the shared lexer

**Goal.** E005 reads `.ts`/`.tsx` through
`plugins/hexaemeron/lib/typescript_lexer.py` with phylax's audited input
boundary, and the pinned application clone runs clean.
**Entry.** Step 2's exit state, branched from its step branch.
**Exit.** `python3 -m unittest plugins.hexaemeron.tests.test_ephoros_checker`
passes with the TypeScript cases, positives observed red first;
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py
/home/user/wildcat-finance/wildcat-app-v2` exits 0 with zero suppression
pragmas added to that read-only clone;
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
scripts` exits 0; both suites pass.
**Files.** `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`,
`plugins/hexaemeron/tests/test_ephoros_checker.py`,
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/` (new TypeScript
specimens).
**Tests.** Positive: the three acceptance shapes in TypeScript -- an address
key on a metric label set, on a dashboard structure, and on a log-index
position of a logger or log-store call. Negative: a react-query `queryKey`
array carrying an address, a storage key built from an address, a logger
message interpolating an address, and `console.*`. Boundary: a file over 1 MiB
reports E000, a lexer failure reports E000, no inspected source is executed or
imported, the walk skips `node_modules` the way the Python walk skips
`__pycache__`, and `// ephoros: allow <why>` suppresses while a bare pragma
does not. Expected count: at least ten new cases.
**Disciplines.** phylax: this step opens the untrusted-TypeScript read
boundary; the control is the one phylax already audited -- the 1 MiB cap before
lexing, E000 fail-closed, no execution -- feeding the `ts-lexer-input`
register line. ephoros: none, the deliverable stays a terminal lint. metron:
none, the per-file work is bounded by the cap and phylax runs the same shape
over the same tree with no recorded budget (study item 10). elenchus: the
guard-test convention holds for every fixture. hypomnema: the ephoros/phylax
line over shared TypeScript files is exercised here and recorded in step 4's
ADR-010.

## Step 4: Say so everywhere, then demonstrate

**Goal.** Document E005, record the two decisions, advance the ledger, honour
the frontier run's prose reconciliation, and run the demo path.
**Entry.** Step 3's exit state, branched from its step branch.
**Exit.** The ephoros `SKILL.md` mechanical subset documents E005 and both
pragma forms, with frontmatter version matching the ledger;
`plugins/hexaemeron/skills/ephoros/EVOLUTION.md` carries exactly one new
`ephoros-v0.3.0` row valid under the versioning contract, either recording one
evidenced successor job or closing mature, decided on the evidence then in
hand; `docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md`
records the ephoros/phylax line and both SKILL.md boundary sentences point at
it; the cold read of mutable first-party marketplace prose is done and every
touched file is listed in the step's pull request body;
`python3 -m unittest tests.test_evolution_contract` passes;
`python3 scripts/promise_machine.py check` passes; the demo-path block from
study item 1 runs green in order; both suites pass.
**Files.** `plugins/hexaemeron/skills/ephoros/SKILL.md`,
`plugins/hexaemeron/skills/ephoros/EVOLUTION.md`,
`docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md`,
`plugins/hexaemeron/skills/phylax/SKILL.md` (one boundary sentence pointing at
the ADR), plus whatever files the cold read shows stale.
**Tests.** `tests.test_evolution_contract` over the new row; both suites; no
new test files expected.
**Disciplines.** phylax: none, prose and records only. ephoros: none, prose
and records only. metron: none, no performance claim. elenchus: none unless
the demo path surfaces a failure, which then follows its triage order.
hypomnema: this is the step where the ADR and the ledger row land; it owns
their shape and homes.
