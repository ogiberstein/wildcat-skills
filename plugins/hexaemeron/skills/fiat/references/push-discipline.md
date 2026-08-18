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
`origin:ai` label. Append `<!-- wildcat-origin: shoggoth -->` to the prepared
body, then apply `origin:ai` in the same `gh pr create` command. Read the pull
request back from GitHub and confirm that both markers persisted before
receipting the push phase.

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

1. Merge that step's pull request into the run branch with the repository's
   permitted merge method, without bypassing a gate.
2. Verify the merge commit, then delete the merged step branch where policy
   permits. GitHub retargets the next step's pull request onto the run branch
   when its base branch goes; confirm that it did, and retarget it by hand
   (`gh pr edit <pr> --base <run branch>`) if it did not.
3. Receipt it before touching the next one:

   ```text
   hexctl done merge-step --step <n> --merge-commit <sha>
   ```

The controller refuses these out of order, so a resumed run always knows how
far down the stack it got.

## The integration pull request

With every step merged, the run branch holds the whole delivery. Open one pull
request from the run branch into the recorded base, using the prose phase's
run-level title and body, and apply the same provenance markers:

```text
gh pr create --base <recorded base> --head <run branch> ...
```

Wait for required checks, merge without bypassing them, verify the merge
commit, and delete the run branch where policy permits. If a `task_issue`
receipt exists, close that exact issue now with a short comment linking the
merged pull request. This is the only merge into the base in the whole run.

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
