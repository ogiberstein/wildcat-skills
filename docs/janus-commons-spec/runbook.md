# Runbook: Create the janus skill in the Wildcat Commons

Derived from the study beside this file. Two steps, in dependency order. The
repository already carries its layout, toolchain pins, CI and licence, so step
1 scaffolds the only thing this run adds to the record: the committed study
and runbook, beside the delivered spec itself. Step 2 wires the Commons
section to the spec and runs the demo path from the study's problem statement.

## Step 1: Land the delivered janus spec and the run records

**Goal.** The delivered spec sits in the tree byte-identical, with this run's
study and runbook committed beside the repository's other run records.

**Entry.** The run branch `claude/janus-wildcat-skill-bejdy0` at
`496f7a102bf012195c48ed1615f8eff7fd832f7b`, a clean tree.

**Exit.** `sha256sum docs/commons/janus.md` prints
`8234ee09201927aeb8df34c9068c5c68e9201539057ccffce3d2600dd724c3ed`;
`docs/janus-commons-spec/study.md` and `docs/janus-commons-spec/runbook.md`
exist; `python3 -m unittest discover -s tests` passes.

**Files.** `docs/commons/janus.md` (created, delivered bytes),
`docs/janus-commons-spec/study.md` (created),
`docs/janus-commons-spec/runbook.md` (created).

**Tests.** None written: the change adds records under `docs/**`, which the
root suite deliberately leaves out of the prose sweep. The full root suite
runs anyway to prove the additions disturb nothing; expected count is the
suite's current size, all green.

**Disciplines.** phylax: none, the step adds Markdown and opens no input,
subprocess, network or credential path. ephoros: none, nothing here runs
unattended. metron: none, no performance claim. elenchus: none, no failure in
hand; any that surfaces is worked to cause before the step continues.
hypomnema: the placement decision is expensive to reverse and its record is
the committed study's Design options section, which this step lands.

## Step 2: Point the Commons at the spec and demonstrate

**Goal.** A reader of the Commons section's `janus` bullet can reach the full
specification, and the study's demo path passes end to end.

**Entry.** Step 1's exit state, on a branch cut from step 1's branch.

**Exit.** All three demo-path commands from the study pass:
`python3 -m unittest discover -s tests` is green,
`sha256sum docs/commons/janus.md` prints the pinned digest, and
`grep -n "docs/commons/janus.md" README.md` finds the pointer in the Commons
section. The imprimatur lint scores `README.md` clean, which the suite also
enforces.

**Files.** `README.md` (the `janus` bullet in "What remains" gains a pointer
sentence; nothing else moves).

**Tests.** None written: `tests/test_shipped_prose_lints.py` already holds
`README.md` to a clean lint score, so the edit is guarded by the existing
suite. The full root suite runs as the exit proof.

**Disciplines.** phylax: none, one prose sentence in an existing document.
ephoros: none, nothing runs unattended. metron: none, no performance claim.
elenchus: none, no failure in hand. hypomnema: none further, the decision
record landed with step 1; this step only makes it reachable.
