# Push discipline

The pushed branch and pull request are the delivery trail. Fiat does not
create or require a GitHub issue.

## Branches and commits

- Branch as `step-<n>-<slug>` where repository conventions allow.
- Keep commits scoped to the current runbook step.
- Preserve the target repository's required commit format and checks.

## Pull request

Push the branch, then open a pull request using the title and body prepared in
the prose phase. The body states what changed, why, where the audit record
lives, and how to run the proof. Do not invent an issue reference. Include one
only when the user independently supplied a relevant issue.

Verify the pull request URL after creation. Never merge it and never
force-push over another person's work.

## Receipt

```text
hexctl done push --pr-url <url>
```
