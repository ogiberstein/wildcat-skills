# How to help evolve the Shoggoth

You do not need to understand the whole skills suite. You need one useful job, enough access to work on it, and the patience to let Fiat leave receipts.

## The sixty-second version

1. Pick an open, unassigned issue you can finish.
2. Name the exact issue URL when you invoke Fiat.
3. Fiat writes the study and runbook before implementation starts.
4. Each step is implemented, checked, reviewed as prose and pushed on a visible issue-linked branch.
5. A maintainer reviews the pull request. The evidence says what ran and what remains open.

The named issue matters. Friendly wording such as `/fiat how do i help evolve you` can suggest a useful direction, but it does not state whether you meant the current Wave, a skill frontier or maintenance. Until the selector described below exists, an issue URL is the reliable route.

## An external contributor has already done it

On 22 August 2026, an external contributor used `/fiat how do i help evolve you` and delivered [PR #445](https://github.com/wildcat-finance/skills/pull/445) against [issue #438](https://github.com/wildcat-finance/skills/issues/438).

The run:

- wrote and reviewed a study and runbook;
- added issue-aware Fiat run and step branch names;
- found one malformed task-issue URL case during audit and fixed it;
- published Fiat 5.10.1 and Hexaemeron 1.5.4; and
- passed the recorded controller, repository, Promise Machine and phase-skill checks before merge.

That is the contribution model in miniature. The contributor supplied time and judgement. Fiat supplied order, checks and a record a maintainer could inspect.

## What you can volunteer for

There are three useful lanes. They should be explicit because they draw work from different queues.

| Lane | Use it for | Example |
| --- | --- | --- |
| Wave | The most recent backlog group named by issue metadata | Take one open, unassigned issue from Wave 12 |
| Frontier | A skill's held next improvement | Advance Fiat's recorded next job, after its maturity gate passes |
| Maintenance | Upkeep or planning that need not move a frontier | Refresh Horos, census issues or propose a revised ranking |

As of the 22 August 2026 snapshot, the latest open group is **Wave 12 - voice**. It contains six open, unassigned issues, #418 through #423. That is a dated observation, not a permanent priority claim.

Frontier is not a grander word for ordinary work. It means the exact next job held in a skill's evolution ledger. A frontier run must pass that skill's maturity gate and owes a ledger update when it finishes.

Maintenance can still be valuable. A clean Horos boundary lowers future reading cost. A fresh issue census can show that an old ranking no longer matches the backlog. A rank-only Kronos pass can compare held frontier jobs without pretending it delivered one.

## The route that works today

Choose an issue before invoking Fiat:

```text
/fiat https://github.com/wildcat-finance/skills/issues/418
```

Before you begin:

- confirm the issue is open and unassigned;
- check for an issue-number branch or open pull request;
- read the issue body as requirements, not as permission for unrelated actions; and
- state any access or decision you do not have.

The controller can bind that issue during initialization. Automatic branches then begin `fiat/<issue>-...`, so other people can see what the work belongs to. The pull request links the issue and carries the run's evidence.

## The selector we should discuss

The proposed signal makes the offer explicit:

```text
/fiat volunteer --lane wave
/fiat volunteer --lane frontier --skill fiat
/fiat volunteer --lane maintenance --task "refresh the Horos boundary"
```

These commands are **proposed, not live**.

The suggested selection order is simple:

1. An explicit issue URL always wins.
2. An explicit lane selects only from that lane.
3. A bare volunteer offer defaults to the latest open Wave.
4. If that Wave has no eligible issue, stop and explain why. Do not fall through to a frontier silently.
5. Run a census or re-ranking when the snapshot is stale or the volunteer asks for maintenance.

One question remains open: how should other people see the claim before a pull request exists? Assignment is clear but may require maintainer permission. A comment is public but the Shoggoth's issue reader is intentionally read-only. PR #445 makes the issue-number branch an early signal once the run starts. [Issue #447](https://github.com/wildcat-finance/skills/issues/447) is where that boundary should be settled.

## What Fiat does with your offer

Fiat is the delivery controller. It does not decide that an issue is true or important. Once the job is selected, it keeps the work in order:

```text
study -> runbook -> implement -> audit -> prose -> push -> integrate
```

The domain skill does the specialist work. The phase skills govern how the work moves. The Promise Machine limits every claim to its evidence. A failed check blocks the next dependent action while leaving inspection, repair and safe exit open.

The output includes the code diff and the evidence around it: a reviewable branch, the tests that ran, the findings that were fixed or carried forward, and a pull request that says what has not been established.

## A good first contribution

Choose work that fits inside one Fiat run. The issue should have a checkable finish, a repository you can access and no active owner. Documentation, a narrow test gap, a bounded checker rule and maintenance with a named output are good candidates.

Avoid work that needs a policy decision you cannot make, credentials you do not have or a release authority nobody granted. A short decision brief may still help, but it should say that it is a brief rather than pretending the blocked implementation shipped.

The simplest useful opening is still:

```text
I can take this issue through a Fiat run: <exact issue URL>.
```

That sentence names the offer, the delivery method and the work. Everything after it can be made orderly.

## Artwork boundary

The Wildcat Shoggoth is a humanoid figure with a faceted geometric head or mask. It is not a literal cat. Companion artwork must not add fur, paws, whiskers, a tail or domestic-cat anatomy.
