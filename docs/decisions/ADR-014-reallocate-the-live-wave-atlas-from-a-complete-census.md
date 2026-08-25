# ADR-014: Reallocate the live Wave Atlas from a complete census

## Status

Accepted, 2026-08-23.

## Context

The Wave Atlas is the contributor-facing view of the Wildcat Skills issue
queue. Its active allocation had been built from a complete 79-issue census,
then changed incrementally as issues closed and new issues were filed. The
result still assigned every open issue, but the milestone descriptions no
longer described every member and the deployed Atlas served an older compiled
snapshot.

The reallocation had to compare every live open issue with every other one.
Shipped gates that returned false-clean or overstated their evidence had to
outrank new capability work. Active delivery blockers and work already in
progress also had to remain visible. Numeric priority alone was insufficient:
hard dependencies and coherent implementation bundles constrain which work can
usefully precede other work.

Four framework-introspection issues, #434 through #437, were explicitly moved
to a separate Handover milestone. Closed issues had to retain their historical
assignments, while the superseded alpha and beta milestones were closed after
the active queue moved. Issue bodies, titles, labels, assignees, comments, and
project membership were outside the authorised mutation.

## Decision

Rebuild the active Wave Atlas from the complete live open-issue universe, using
GitHub milestones as the only Wave assignment.

Apply these rules:

1. Query all live open issues, all milestones, open pull requests, active
   branches, the repository head, and each governed skill frontier before
   scoring.
2. Score relative priority on impact out of 40, urgency out of 25, readiness
   out of 20, and unblocking value out of 15. Apply hard dependencies,
   in-progress work, and coherent implementation bundles outside that score.
3. Clear the milestone field from every open issue before assigning the new
   queue. Assign each open issue exactly once to Wave 0 through Wave 11, except
   #434 through #437, which belong to Handover by explicit governance
   decision.
4. Create fresh active milestones instead of retitling the prior beta
   milestones. Close the superseded alpha and beta milestones after successful
   reassignment, leaving their completed issues attached.
5. Preserve a rollback snapshot before mutation. Use sequential REST updates
   with bounded retries, then verify the live issue universe, exact
   issue-to-milestone mapping, milestone counts, omissions, and duplicates.
6. Rebuild the deployed Atlas snapshot from the verified post-mutation GitHub
   state. Label it as a verified snapshot rather than a live index, preserve
   recorded dependency edges, test the public job pool, and verify the
   production route after deployment.

Milestone descriptions hold the score and concise ordering reason for every
current member. They are the durable ranking record for this allocation.

## Alternatives

- **Patch only the issues added since the previous census.** This would be
  faster, but it would retain priority assumptions made before the current
  controller fixes, live branches, false-clean findings, and contributor
  handover work existed.
- **Retitle and reuse the beta milestones.** This would reduce milestone
  count, but completed issues attached to those milestones would be silently
  reclassified under the new allocation.
- **Order only by the numeric score.** This gives a simple ranking, but it can
  place consumers before their prerequisites and split changes that should be
  made and reviewed together.
- **Write Wave metadata into issue bodies.** This creates a second source of
  truth and changes issue content. GitHub milestone fields already provide the
  canonical assignment and counts.
- **Use one parallel bulk mutation.** This is faster when the API is healthy,
  but previous and current runs both observed transport failures. Sequential,
  state-checked writes make a partial result recoverable.
- **Continue calling the deployed Atlas live.** The site packages issue data
  into a build artefact. A no-store response header does not make that source
  live, so the label would overstate the evidence.

## Consequences

The active queue has one complete point-in-time allocation with no open issue
missing or duplicated. Current Waves and Handover are separate from closed
historical alpha and beta allocations, so completed work keeps its original
context without presenting those milestones as active queues.

The earliest Waves favour delivery continuity and truthful existing gates over
net-new capability. Later Waves follow dependency chains through fixtures,
ingestion, release representation, statements, accessible interaction, and
maintenance. Handover is an explicit exception to the numeric sequence.

The allocation is not self-updating. A new or closed issue can make the
snapshot and its relative scores stale. A future refresh must repeat the full
census and post-mutation verification; editing only the compiled Atlas file is
not sufficient evidence that GitHub and the site agree.

The public job endpoint remains a draw from dependency-clear issues, not a
claim that every offered issue has equal importance or that Wave order is a
hard dependency.
