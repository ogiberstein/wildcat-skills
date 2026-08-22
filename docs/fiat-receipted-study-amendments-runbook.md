# Runbook: receipted study amendments

This runbook implements the accepted study at exact start
`52b3b45c3d72cb2f163b1dfe88c920035d1385d5`. It is ordinary Fiat delivery for
issue 446. It does not alter Fiat's evolution ledger, held issue 363 frontier,
or package versions.

## Delivery boundary

- Step 1 publishes the accepted records.
- Step 2 implements, guards, documents, and demonstrates the transition.

## Step 1: Publish the accepted amendment specification

**Goal.** Commit byte-identical tracked copies of the accepted study and
runbook so the implementation and audit have a reviewable specification.

**Entry.** Run branch `fiat/446-receipted-study-amendments` at
`52b3b45c3d72cb2f163b1dfe88c920035d1385d5`, with `.hexaemeron/study.md` and
`.hexaemeron/runbook.md` receipted and mechanically clean.

- Evidence is limited to the named files and commands below.

**Exit.** The two tracked documents match their receipted sources byte for
byte, the Horos boundary describes the new tracked tree, Protasis accepts both
artefacts, Imprimatur and Brevitas accept the shipped prose, the root suite and
Hexaemeron suite pass, and `git diff --check` exits 0.

```bash
cmp .hexaemeron/study.md docs/fiat-receipted-study-amendments-study.md
cmp .hexaemeron/runbook.md docs/fiat-receipted-study-amendments-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-receipted-study-amendments-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-receipted-study-amendments-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-receipted-study-amendments-study.md docs/fiat-receipted-study-amendments-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-receipted-study-amendments-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-receipted-study-amendments-runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
git diff --check
```

**Files.** Create
`docs/fiat-receipted-study-amendments-study.md` and
`docs/fiat-receipted-study-amendments-runbook.md`; refresh
`.horos/boundary.json` only if the deterministic scan changes it.

**Tests.** Run the exact comparison, both Protasis modes, Imprimatur, Brevitas,
the root suite, the complete Hexaemeron suite, the Horos currency check carried
by the root suite, and the diff check. No test count is assumed before the run.

**Disciplines.** phylax: the step adds only bounded Markdown records and the
generated reading boundary, with no executable input. ephoros: none, the step
runs nothing unattended. metron: none, no performance claim. elenchus: exact
byte comparisons guard the accepted artefacts. hypomnema: the tracked study and
runbook are the durable homes for the design and build order.

## Step 2: Add and demonstrate the receipted amendment transition

**Goal.** Add the narrow `amend study` transition, its fail-closed guards and
user contract, then demonstrate a holding amendment and a broken-current-step
block against a temporary run.

**Entry.** Step 1's stacked branch, with the accepted records committed and all
entry checks green.

- Evidence is limited to the named controller, contract, tests, and checks.

**Exit.** The unfixed parent first reproduces the absent-command/digest refusal;
the fixed controller accepts only one append-only Protasis amendment, records
the prior, new, and amendment digests plus complete unbuilt-step verdicts,
re-pins the study, continues only on a holding current step, and durably blocks
a broken current step. Arbitrary mutation, prefix drift, invalid fields,
ambiguous or missing step verdicts, wrong phase, unsafe path, oversize, checker
failure, concurrent mutation, legacy state, and post-amend drift have named
guards. The CLI and Fiat instructions expose the recovery boundary. The
focused controller and prose tests, both complete suites, Promise Machine
checks, all three non-Solidity discipline lints, Imprimatur, Brevitas, the
temporary demonstration, and `git diff --check` exit 0.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_protasis_checker
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
```

The demonstration uses a temporary Git repository and the checked-in
controller. It receipts a complete study and two-step runbook, appends a dated
four-field amendment whose two verdicts hold, runs the new command, observes
both study digests in state and ledger, and obtains the amended Mason packet.
A second temporary run records a valid amendment whose current-step verdict is
broken and observes the controller's durable blocked directive. No fixture
state is presented as a production run.

**Files.** Modify
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`, and
`plugins/hexaemeron/tests/test_fiat_skill.py`. Update
`tests/promise_machine_coverage.json` only for exact changed runtime or skill
digests. Modify no evolution ledger, manifest, marketplace, package version,
vendored skill, or CI file.

**Tests.** Add red-parent guards for the missing amendment command and the
existing digest refusal before implementation. Extend controller tests for the
positive transition, digest history, packet reconstruction, broken-current-step
block, all study risk-register failure classes, unchanged legacy behavior, and
the demonstration path. Extend skill prose tests for the command, boundary,
receipt, and recovery wording. Run the focused and complete commands above;
record actual counts only after they finish.

**Disciplines.** phylax: candidate paths, Markdown bytes, subprocess arguments,
bounded diagnostics, temporary files, atomic writes, and killed-run recovery
are implementation boundaries. ephoros: stdout, stderr, state, ledger, and
`next` must answer which digests and step verdicts control continuation.
metron: none, no speed change is claimed and existing byte/time ceilings are
safety bounds. elenchus: the known digest refusal is reproduced red first and
every accepted or rejected transition receives a regression guard.
hypomnema: stable behavior belongs in Fiat's canonical skill, the code in the
controller, the guards in tests, and round dispositions in the audit log; no
evolution row or ADR is warranted.
