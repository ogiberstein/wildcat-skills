# Issue 594: bind a step merge to the pull request the directive names

Rounds for the run on branch
`fiat/594-bind-a-step-merge-to-the-pull-request-the-di`, off `main` at
`a79e663a136c446a6653ddbb14648782fef99173`. The controller derived this path at
`init` with no operator action, which is issue 576's change on its first live
run. Headings carry step and round alone, because the file names the run.

## Step 1, round 1 -- 2026-08-24

Non-Solidity round over the two Markdown documents step 1 commits, at
`1e1b157d6a2ffce108359a9a47a07545a6e6c310`. Zero findings.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over `README.md AGENTS.md .agents plugins docs`. Protasis accepts the
shipped study in `--study` mode and the shipped runbook in runbook mode.
Imprimatur scores both 100.0 with no defects and Brevitas is clean on both. Horos
reports that the boundary matches the tree. The root suite reports 349 tests OK
with no skips and the Hexaemeron suite 1,045/1,045. The commit's local signature
is good and it carries exactly one co-author trailer and one origin trailer.

Both shipped copies are byte-identical to the receipted ones, which the issue 576
run could not manage: its study cited the five discipline skills as
`../<name>/SKILL.md`, which resolves from a skill directory and nowhere else, and
Hypomnema H001 caught all five once the file reached
`plugins/hexaemeron/docs/`. This study was written with `../../skills/<name>/`
from the start, so the exit holds in bytes rather than in content.

Two register concerns are reachable at this step and both were checked.
`false-refusal`: the step changes no code, so no guard exists yet to fire on a
healthy run. `network-dependence`: likewise, `next` and `status` are unchanged and
still make no remote read in the integrate phase. The other four,
`premature-merge-undetected`, `retarget-drift`, `ancestry-unanswered` and
`printed-command`, sit in the step 2 and step 3 diffs and are not yet reachable.

One thing worth recording about this run's own evidence. The controller driving
it is `fiat-v5.22.1`, the generation issue 576 published hours earlier, so this
is the first run whose audit log path was derived rather than set by hand and the
first whose `audit-round` directive names that path. Both worked with no operator
action. That is not a claim about this run's subject; it is the previous run's
change being exercised.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-24

Non-Solidity round over the run-branch movement guard, at
`c72ed15a85e6843c59abfcbb2330677f234c670f`. Zero findings.

The three bundled lints exit 0. `scripts/promise_machine.py check` and
`coverage --check` are clean after the recorded `hexctl.py` digest moved to
`315cf29ff9d7`-prefixed bytes; no promise or field map changed, because the diff
adds no result field. Horos reports that the boundary matches the tree. The root
suite reports 349 tests OK with no skips and the Hexaemeron suite 1,057/1,057
with the twelve new cases in `test_stack_topology.py`. Seven of those assertions
fail against the step 1 tip. The commit's local signature is good and it carries
exactly one co-author trailer and one origin trailer.

Three things went wrong while building this and all three were fixed before the
commit. They are recorded because each one is a way the guard could have shipped
wrong, not because any of them survived.

The first draft refused every healthy merge. A receipt runs *after* its own merge
has landed, so at `done merge-step` the run branch legitimately already holds the
commit being receipted, and comparing it against the previous receipt makes every
correct run fail. The fix accepts the landing commit as well as the last
receipted one, and `test_a_healthy_stack_merges_unchanged` is the case that would
have caught it.

The second draft guarded `sync-run` and `integrate` as well as `merge-step`, and
broke `test_pinned_starting_commit_syncs_and_integrates_into_the_named_base`.
`_integrate_directive` returns `integrate` whether or not a sync has been
receipted, so after the stack lands the run branch may legitimately carry a merge
the controller has not recorded: that is what `done sync-run` exists to receipt.
The guard now stops when the stack does, which is also the honest scope, because
merge-step is where both issues' damage happens.

The third was in the test helper rather than the controller.
`self.fake_refs[self.state()["run_branch"]] = sha` binds the dictionary before
`state()` runs, and `state()` replaces it, so the write landed in a copy nothing
read afterwards and six cases passed against a guard that had not been given
anything to find. Named in the helper's docstring so the next reader does not
repeat it.

Four register concerns are reachable at this step and each was checked.
`premature-merge-undetected`: the movement check compares the remote tip against
this run's own receipts, and `test_it_refuses_at_next_rather_than_at_the_merge_after`
asserts it arrives at the directive rather than at the receipt after it.
`false-refusal`: `test_a_healthy_stack_merges_unchanged` merges three steps with
the guard live, `test_nothing_fires_before_the_first_merge` covers the state
where the controller has recorded no expectation, and the full suite passing at
1,057 is the wider evidence. `ancestry-unanswered`: not reachable as written,
because the final design compares recorded SHAs and asks git no ancestry question
at all, which is why it needs no local objects and works against an unfetched
remote. `network-dependence`: one `ls-remote` per merge-step directive, in a
phase that already makes several GitHub calls per receipt, and `status` reports
an unreadable remote as unknown rather than refusing. `retarget-drift` and
`printed-command` sit in step 3's diff.

One deliberate limit. The `ancestry-unanswered` concern was written against a
design that asked `git merge-base --is-ancestor` whether a waiting step's head
was reachable from the run branch. That design needs both objects present
locally, which an unfetched clone does not guarantee, and would have turned a
stale checkout into a refusal about a person. Comparing recorded SHAs answers the
same question with no objects and no fetch. The concern stays in the register
because the study is receipted; this is the record of why it is not reachable.

Leads not pursued: none.
