# Push discipline

The stacked branches, their pull requests, the one merge into the base, and a
closed task issue are the delivery trail. Fiat does not create an issue unless
the user or a higher-priority target-repository rule requires one. If one
exists, record it as `task_issue` and close it with the integration merge.

## Branches and commits

A run owns one integration branch off the base, named at `init` and held in
state. Cut it before step 1 and push it:

```text
git checkout -b <run branch> <base>
git push -u origin <run branch>
```

- Take the step branch and the ref to cut it from out of the `implement`
  directive (`branch`, `branch_from`); the controller refuses a receipt for
  any other name. Step branches are siblings of the run branch, never nested
  under it -- git cannot hold `fiat/x` and `fiat/x/step-1` at the same time.
- A step branch is descriptive by construction: run slug, step number, step
  title. A branch called `step1` says nothing to whoever finds it later.
- Keep commits scoped to the current runbook step.
- Preserve the target repository's required commit format and checks.
- End every Fiat-created commit message, after a blank line, with both exact
  provenance trailers:

  ```text
  Co-authored-by: Shoggoth <shoggoth@wildcat.finance>
  Wildcat-Origin: shoggoth
  ```

## The stacked pull request

Push the step branch, then open its pull request using the title and body
prepared in the prose phase, targeting the `pr_base` the directive names:

```text
gh pr create --base <pr_base> --head <branch> ...
```

For step 1 that base is the run branch; for every later step it is the step
below it. Pass it explicitly, every time. Never let a pull request fall back to
the repository default branch, and never point one at the recorded base: a step
that targets `main` puts unreviewed, unintegrated work one click from the
default branch, and a run of those is the pile of merges this workflow exists
to avoid. The body states what changed, why, where the audit record lives, how
to run the proof, and which step it stacks on. Do not invent an issue
reference. Include one only when the user independently supplied a relevant
issue.

Before opening the pull request, make sure the target repository has the
`origin:ai` label, and create it when it does not:

```text
gh label list --repo <owner/repo> --search origin:ai
gh label create origin:ai --repo <owner/repo> \
  --color ededed --description "Opened by an agent, not a person"
```

Creating it is additive and reversible, and a first Fiat run against a fresh
repository will always be the one that needs it. Append
`<!-- wildcat-origin: shoggoth -->` to the prepared body, then apply `origin:ai`
in the same `gh pr create` command. Read the pull request back from GitHub and
confirm that both markers persisted before receipting the push phase.

Read it back, rather than trusting that `gh pr create` applied it. A label
silently missing is the common failure here, not a label that does not exist:
the marker is what tells a reader the pull request is agent-authored, and one
that reads as human is worse than one that is merely unlabelled.

**A failed query is not an answer.** `gh label list | grep -q origin:ai` reports
the same thing when the label is absent and when the call was rate-limited,
unauthenticated or offline, so a command shaped that way will invent a missing
label and then create one that already exists. Check the exit status separately
from the match, and on a failed call say the check could not be completed rather
than reporting what it did not find. This holds for every gh query in the loop,
not only the label.

If the label genuinely cannot be created, because the account lacks the
permission or the repository forbids it, say so out loud and record the reason
rather than opening the pull request unlabelled and silent.

Extra labels are additive. Do not remove or rename either provenance marker.
Do not amend a pre-existing human commit or relabel a pre-existing human pull
request merely because Fiat later resumes work around it.

Verify the pull request URL after creation. Wait for required checks and
convert the PR from draft if necessary, then stop: a step's pull request stays
open until the whole stack is ready. Receipt it and move to the next step.

```text
hexctl done push --pr-url <url> --head-commit <sha> --pr-base <ref>
```

The receipt refuses a `--merge-commit` here. Merges belong to `integrate`.

## Bringing the stack down

`next` returns `merge-step` once per step, in step order, starting at the
bottom. For each one:

1. Retarget the next step's pull request onto the run branch first, before this
   one merges or its branch goes:

   ```text
   gh pr edit <next pr> --base <run branch>
   ```

   Do this even though the stack currently points at this step's branch. Once
   the step below has landed in the run branch, the run branch already contains
   it, so the next pull request's diff against the run branch is exactly that
   step and nothing more.
2. Merge that step's pull request into the run branch with the repository's
   permitted merge method, without bypassing a gate. Do not pass
   `--delete-branch`, and do not delete the branch here. Branch cleanup is the
   integrate phase's last act, once the whole stack has landed.
3. Verify the merge commit, then receipt it before touching the next one:

   ```text
   hexctl done merge-step --step <n> --merge-commit <sha>
   ```

The controller refuses these out of order, so a resumed run always knows how
far down the stack it got.

**Why the order is retarget, then merge, and never delete.** Deleting a merged
step's branch does not retarget the pull request stacked on it. GitHub closes
that pull request instead, and a closed pull request whose base ref no longer
exists can be neither reopened nor retargeted: `reopenPullRequest` and
`updatePullRequest` both refuse it. The stack is then stuck in a state its own
recovery instructions cannot reach, and the way out is to push the deleted
branch back at its old head, reopen, retarget, and merge. Retargeting first
costs one command per step and cannot produce that state at all.

## The integration pull request

With every step merged, the run branch holds the whole delivery. Open one pull
request from the run branch into the recorded base, using the prose phase's
run-level title and body, and apply the same provenance markers:

```text
gh pr create --base <recorded base> --head <run branch> ...
```

**Carry the unfinished forward.** The run-level body lives at
`.hexaemeron/run-pr.md`, written in the prose phase, and the integration pull
request is opened from it. Before the receipt will take it, that file has to
name everything this run found and did not finish: an audit lead left
unpursued, a finding accepted rather than fixed, a boundary the run would not
cross, a claim it could not verify, a fix that belongs to another skill's held
job. Put them under a heading a reader can find, `## Carried forward`, one line
each, with where the evidence lives. This is the last thing the run writes into
the repository, and the next study over the same target reads it as prior art
under `protasis` item 2, so an item missing here is an item the next run
rediscovers from nothing. A run that finished everything says that under the
same heading rather than dropping it: an absent section cannot be told apart
from an unasked question.

`done integrate` refuses without it, and names which of the three faults it
found: the file unreadable, the heading absent, or the heading standing empty.
Reading stops at the next heading, so a later section cannot stand in for this
one. What passes is recorded on the receipt as the line count and the digest of
the body, so the ledger holds what the run published rather than a promise that
it did.

Wait for required checks, merge without bypassing them, and verify the merge
commit. Then delete the run branch and every step branch where policy permits:
this is the one place branch cleanup happens, and by now nothing is stacked on
any of them, so deleting cannot close a pull request that still has work to do.
If a `task_issue` receipt exists, close that exact issue now with a short
comment linking the merged pull request. This is the only merge into the base in
the whole run.

```text
hexctl done integrate --pr-url <url> --merge-commit <sha> \
  [--closed-issue-url <url>]
```

Never force-push over another person's work and never bypass a required review
or failing gate. A plan or implementation is not complete while its own branch,
PR, or issue is awaiting routine agent action.

If GitHub rejects a push or merge, a required independent approval cannot be
self-supplied, or an external gate fails, record `hexctl halt --reason ...`
with the exact blocker. Do not call the run complete.
