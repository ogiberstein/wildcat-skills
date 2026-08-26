# Wave Atlas: the ten issues to handle now

This ranking is a snapshot taken on 26 August 2026. It compares all 101 open
issues in the thirteen Wave Atlas milestones with `wildcat-finance/skills`
`main` at `ab611eb96a6a9bddecb57bff2416641296e0a21e` and
`wildcat-finance/shoggoth-wave-atlas` `main` at
`6de500c7b5dcbe0aa842dcd0d57e9cdcb619a3ce`. It ranks work that is already in
flight first, then defects that overstate evidence, then the shortest path to
the current Fiat frontier. It does not authorise a second run over an issue
that already has one.

## 1. #608: finish the Fiat sync-receipt key repair

`done integrate` reads `base_commit`, while `done sync-run` records
`base_head`. The mismatch defeats the concurrent-frontier ledger subtraction
and has already left a merged run without its final receipt. PR #612 contains
the accepted study and runbook; finish that existing run rather than opening a
replacement.

## 2. #621: finish the disposable-repository signing isolation

Throwaway Git fixtures still inherit contributor signing and can stop before
their assertions run. PRs #626 and #627 carry the first implementation and its
clean audit. Land the existing stack, verify the hostile inherited-signing
case, and keep real repository signing untouched.

## 3. #503: integrate the Imprimatur source-comment reader

PRs #628 and #629 delivered the implementation to the run branch, but
integration PR #630 is conflicted with current `main`. Resolve that integration
without weakening the comment-language cases, rerun the exact prose gate, and
close the issue after the merged tree proves the behaviour.

## 4. #617: make Shoggoth attribution survive the runtime host

Current host defaults can reintroduce a Claude author, co-author, or generated
footer after a candidate was checked. Fiat then refuses the result under
ADR-016. Require post-publication read-back, diagnose the host default that
caused each refusal, and keep every existing identity gate intact.

## 5. #556: finish version relations for long Fiat runs

PRs #603 and #604 contain the first two clean steps of the existing run.
Complete that stack so a runbook can state a relation that is resolved against
the integration base instead of freezing a minor version that can become stale
during the run.

## 6. #622: finish the affected-scope check selector after #621

The current repository contract says to run checks for every affected area but
does not compute that set. Keep the existing #622 run; do not start a parallel
one. Its selector must fail closed on unowned paths, include declared
consumers, rediscover tests for each invocation, and never cache a pass verdict.

## 7. #504: make Pandects report which laws were exercised

Pandects currently writes the catalogue size as `laws_searched`, even when the
campaign cannot exercise every law. Add per-law exercise evidence before or in
the same delivery as #381, so Echidna and Medusa support does not copy the
overclaim into two more engines.

## 8. #497: close Protasis's current amendment-check frontier

Protasis is now `v4.8.0`, but its ledger still names
`amendment-block-check` as the open frontier. Put the study amendment shape in
the canonical Protasis scanner, retain controller-only receipt checks in Fiat,
and record the one evolution row the frontier completion requires.

## 9. #453: inject known guards before production edits

Its prerequisites #327, #429, and #369 have landed. The remaining gap is now
actionable: when a run starts with known failures, executable guards must be
bound to the unfixed parent before Mason changes production code. This is the
last declared blocker before Fiat's current held frontier.

## 10. #363: bind delegated task identity to the current run

Fiat `v5.26.1` still names this exact problem as its next job. After #453,
make Surveyor, Mason, Warden, and Scribe expose deterministic identities bound
to the current issue or topic, step, and role; stale reused collaboration
handles must be refused or replaced across resume and compaction.

## Immediately after the ten

- Narrow #505 to the Atlas residual. Live reads, cache fallback, snapshot age,
  and dropped-issue reporting now exist; source revision and deployment
  currency still need one current contract.
- Rename and close #551 as superseded once #553 carries its protected incident
  evidence and the recovery path is delivered.
- Keep #377, #383, and #395 at the head of their domain queues. Their current
  ledgers still name the same Horos, Lazarus, and Alexandria frontiers.
- Keep Homologia (#458), Basanos (#498), and Synkrisis (#449) as distinct
  proposed capabilities. No current sibling owns their exact promises.
