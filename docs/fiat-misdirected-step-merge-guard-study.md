# Study: refuse misdirected Fiat step merges before the next click

Assuming, unless corrected:

1. The target is `wildcat-finance/skills` at starting commit
   `08512d4ada7b1d7418e1af213be0d4b8c1494b6d`, with Fiat
   `fiat-v5.21.1` and its held `state-shape-validation` frontier unchanged.
2. Issue #555 is an exogenous `wish`, not Fiat's held frontier job. A shipped
   controller change therefore increments Fiat's generation to
   `fiat-v5.22.1`, retains the existing frontier revision and digest byte for
   byte, and does not use `--frontier`.
3. A normal stack remains the review topology: step 2 contains step 1, step 3
   contains steps 1 and 2, and so on. That upward reachability is expected and
   must not be refused.
4. The dangerous direction is downward. Commits owned by an unmerged step
   must not become reachable from a lower-numbered step branch. The run branch
   is excluded from that rule because it is the intended merge destination.
5. `next` and `status` may consult the target's configured `origin` and the
   GitHub pull requests already recorded by push receipts. They gain no
   authority to edit a ref, retarget or merge a pull request, or write a
   controller receipt.
6. GitHub and the Git transport may be unavailable. Failure to read them is an
   unavailable verdict, never proof that the stack is sound or damaged.
7. The runbook-amendment transition shipped by issue #554 is present. It can
   correct source-bound instructions for an unbuilt step; it cannot alter Git
   ancestry, a pull request's remote state, or a push receipt.

## 1. Problem statement

Fiat must show the operator that a step stack is no longer safe before it
offers the next `merge-step` instruction. A working prototype adds one shared
stack-landing guard to `next`, `status`, and the existing `done merge-step`
receipt path during `integrate`.

The guard answers two separate questions:

1. Has any exact commit owned by a not-yet-receipted step become reachable
   from a lower-numbered step branch?
2. Does the pull request for the step currently next in controller order still
   target the run branch?

The first question is directional. Earlier-step commits being ancestors of a
later step branch is the expected stack. Later-step commits being ancestors of
an earlier step branch means the later step was merged downward, as PR #542
was. The second question is limited to the current step. A future pull request
still targets the step immediately below it until the retarget-first operation,
so requiring every future pull request to target the run branch would reject a
healthy stack.

The demo path is a hermetic three-step repository plus bounded GitHub-response
fixtures. Before the product change, the #542-shaped specimen reaches a
`merge-step` directive from `next` and has no warning in `status`. After the
change:

- `next` emits no `merge-step` directive when either question is false or the
  required live evidence is unavailable;
- `status` still exposes the deterministic local controller state, then names
  the live stack verdict as clear, blocked, or unavailable;
- `done merge-step` reuses the same guard before writing state or ledger; and
- a normal stacked graph, the retarget-first window, and a correctly merged
  current step all remain accepted.

The focused proof command is:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl -v
```

The full root and Hexaemeron suites, Promise Machine checks, version contract,
prose checks, and repository diff check also have to remain green.

## 2. Prior art and observed topology

Current Fiat already owns most of the parts, but joins them too late.

- `done_push` records the pull request URL, its declared base, the pushed head,
  and the exact locally and GitHub-verified commit list. Those immutable commit
  SHAs are the controller's deterministic statement of which commits a step
  owns.
- `_integrate_directive` names the first unmerged step and says it merges into
  the run branch. It reads only controller state.
- `remote_branch_tip` reads one exact remote ref. `commit_is_ancestor` treats
  Git's statuses 0 and 1 as answers and every other status as unavailable.
- `inspect_pull_request` reads the recorded pull request from GitHub and checks
  its head, base, state, author, and merge SHA against caller-supplied
  expectations.
- `refuse_rewritten_stack` runs only inside `done_merge_step`. It compares the
  tips of later waiting branches with their push receipts. It catches GitHub's
  native-stack rebase because that moves those tips, but it does not catch a
  later step merged into an earlier branch when the later branch itself stays
  put.
- `cmd_next` currently computes a state-only directive. `cmd_status` validates
  receipted source and prints state, but neither inspects live branch topology
  or pull request metadata.

Issue #555 records the missing join. Issue #429 and PR #542 supply the fixed
historical specimen. A live read at `2026-08-24T18:03:26Z` observed:

- run branch
  `fiat/429-audit-record-schema-timestamp-synopsis` at
  `c04718fc700b09bf2d6c089f3ac5a8bf05a5738c`;
- step 1 branch at
  `d86fcf922cbc1ca2c6b43b3b738211ddd2c1010e`;
- step 2 branch at the original signed head
  `4b78dfa8b35efe4da794a200096682eb7495c3b3`; and
- step 3 branch at
  `f11fe174161f46bf79080422169ad943214e1b4f`, descended from the step 2 head.

The graph says exactly what happened. Correct PR #509 produced run-branch
merge `c04718f` with parents `ced4e6f` and step 1 head `6069703`. PR #542
then produced step-1-branch merge `d86fcf9` with parents step 1 head `6069703`
and step 2 head `4b78dfa`. The step 2 head is therefore an ancestor of the
step 1 branch, while the step 2 branch tip still equals its original head.
From `6069703`, the intact step 2 head carries 31 commits; the misdirected step
1 branch carries those 31 plus the GitHub-signed merge, 32 commits. A tip-only
rewrite check sees no movement on step 2 and misses the damage.

GitHub's live PR record provides the other half. PR #542 is `MERGED`; its
`baseRefName` is the step 1 branch, its `headRefName` is the step 2 branch, its
head OID is `4b78dfa`, and its merge OID is `d86fcf9`. Its `baseRefOid` remains
`6069703`, even though the named base branch now points at `d86fcf9`. That
distinction matters: pull request metadata records the merge's named target and
historical OIDs, while the Git ref service records where the branch is now.
Neither plane can stand in for the other.

ADR-021 already decides that a rewritten native stack lands from a branch
holding the original commits, not by accepting GitHub's replacement
signatures. `push-discipline.md` already states the retarget-first order. The
audit record's earlier post-push incident also established that stale push
evidence is repaired from exact PR topology, exact remote heads, and freshly
verified local ranges rather than by rewriting an old receipt. This work moves
a narrower topology question earlier; it does not replace those controls.

The two most recent merged changes relevant to this controller are PR #585,
which shipped issue #554's append-only runbook-amendment receipts, and PR #579,
which bound optional run-observation prefixes without making observation a
phase gate. The former supplies a source-repair route. The latter is a useful
boundary precedent: an unavailable companion observation cannot strengthen a
delivery claim, just as unavailable GitHub state cannot clear this guard.

## 3. Constraints, scope, and non-goals

The starting ref is
`08512d4ada7b1d7418e1af213be0d4b8c1494b6d`. The implementation stays in
Python's standard library and the existing bounded `git` and `gh` helpers. It
adds no dependency, CI job, state version, public receipt field, branch naming
rule, or GitHub webhook.

The product scope is:

- derive an immutable inspection plan from the current state and push receipts;
- take a coherent, bounded snapshot of the known step refs and the current
  recorded pull request;
- test every exact commit owned by each unmerged step against lower-numbered
  step branch tips only;
- require the current step's live pull request base to equal the run branch;
- expose one structured verdict to `next` and both forms of `status`;
- reuse the verdict at `done merge-step` before any state or ledger write;
- state the two evidence classes and recovery in Fiat's contract,
  `push-discipline.md`, and an addendum to ADR-021; and
- publish a Fiat generation row, expected to be `fiat-v5.22.1`, without
  changing the held frontier revision, digest, status, current frontier, next
  job, evolution, or epoch.

The current step's pull request may be `OPEN` before the click or `MERGED`
after a correct click and before its receipt. Both states can be valid when its
live base is the run branch and its head agrees with the coherent ref snapshot.
A closed-unmerged pull request, a missing required branch, a head disagreement,
or a malformed response cannot clear the guard.

The guard does not:

- prevent a person from using GitHub after a clear `next` response;
- make a GitHub read and a later merge atomic;
- detect a cherry-pick whose new SHA reproduces equivalent content;
- enumerate arbitrary repository branches outside the run's recorded stack;
- decide that a semantically equivalent replacement commit belongs to a step;
- unmerge PR #542, rebuild #429's lost controller state, or repair issue #557;
- resolve a stale target version dynamically, which remains issue #556;
- validate arbitrary runbook commands, which remains issue #508;
- rewrite a push receipt, import GitHub's signing key, force-update a branch,
  or bypass a required review; or
- turn `status` into an authorising receipt.

Issue #554's amendment mechanism is relevant only at the source boundary. If
the guard finds an open current pull request on the wrong base and the active
runbook carries stale instructions, a valid append-only runbook amendment may
replace the unbuilt step's complete field and carry the corrected recovery to
Mason or Warden. The amendment cannot change the PR base itself, alter the
commit graph, clear this guard, or make an already misdirected merge safe. A
clean retarget still needs a fresh live check. A damaged graph stops the normal
merge-step path.

**Always.** Preserve the state and ledger bytes on every observation; use only
exact recorded PR URLs, branch names, commits, and bounded outputs; distinguish
clear, blocked, and unavailable; retain upward stack reachability; run both
suites before a commit; run Imprimatur on shipped prose; verify every signed
Fiat-created commit before publication.

**Ask first.** Add a dependency, state field, receipt transition, network
credential, CI change, GitHub permission, new branch protection, force update,
or any recovery that mutates a damaged remote stack.

**Never.** Treat a failed remote read as a clean stack, inspect an unrecorded PR
chosen from search results, echo a credential or unbounded response, infer a
commit owner from mutable branch ranges, accept upward reachability as a
finding, edit controller history, or claim the guard prevented an external
click.

## 4. Design options and choice

### Option A: inspect only live pull request metadata

This catches an open current PR before it is merged into the wrong branch, and
PR #542 still names the wrong base after merge. It cannot catch a manual branch
merge, a ref update outside the recorded PR, or a partial carry of original
step commits. A merged PR's OIDs are also historical snapshots rather than the
current named branch tips.

### Option B: inspect only remote Git refs and commit ancestry

This catches the durable graph fact even when the merge happened outside the
recorded PR. It cannot see that an open PR is pointed at the wrong target before
the click, and a missing or deleted branch loses the named remote surface even
when the PR record remains readable.

### Option C: keep the check only in `done merge-step`

This keeps `next` and `status` offline, but repeats the defect: the controller
learns about a bad target only after GitHub has accepted the merge. The original
commits may survive, but the receipted landing route is already broken.

### Option D: combine the immutable receipt slice, remote refs, and current PR metadata

Chosen. The controller first derives, without network access, each unmerged
step's exact owned-commit list and the lower branches against which those SHAs
must not be reachable. It then reads all known step refs as exact OIDs, obtains
the referenced objects without updating a tracked file or branch, reads the
current PR by its recorded URL, and checks ref tips again. A changed first and
second ref snapshot is unavailable rather than clear. The PR head OID must
agree with the corresponding remote tip.

For each unmerged step `j`, the ancestry loop checks its receipted own commits
against steps `1..j-1`. It does not check against later branches. It does not
check the run branch for wrongful reachability. Separately, only the first
unmerged step's live PR base must equal the run branch. This leaves the required
retarget-first window valid: while step 1 is current, step 2 may be retargeted
to the run branch before step 1 merges, without the guard trying to validate
step 2's future base.

The result has four values: `not-applicable`, `clear`, `blocked`, and
`unavailable`. Outside `integrate`, it is `not-applicable` and no network call
runs. In `integrate`, `next` emits no merge directive for `blocked` or
`unavailable`. `status` renders its ordinary local state first and then the
verdict, including in JSON form. This keeps safe local inspection possible
when GitHub is offline: the operator can still see the exact phase, receipts,
and merge prefix, but the output says the live stack is unverified and cannot
clear a merge. `done merge-step` repeats the guard and exits before mutation
unless it is clear.

No snapshot makes the next GitHub click atomic. Reading refs, PR metadata, and
refs again narrows the race and detects changes during inspection. A mutation
one instant later remains possible. That is why the receipt path repeats the
guard and why the prose still says retarget first. The controller reports what
it observed; it does not claim a lock it does not hold.

Recovery follows the observed state:

- If the current PR is open on the wrong base and no downward reachability is
  present, retarget it to the run branch, then rerun `next` or `status`.
- If original step commits are already reachable from a lower branch, preserve
  every ref and halt the ordinary merge-step route. ADR-021's original-commit
  landing may be planned from an intact final step head, but this guard neither
  performs nor receipts that recovery.
- If a branch, object, GitHub response, authentication path, or coherent
  snapshot is unavailable, restore that evidence source and retry. Do not
  retarget, merge, or reconstruct a range from the failure.
- If an old runbook's complete instruction is now false while the topology is
  still repairable, issue #554's append-only runbook amendment can correct that
  source. The remote action and fresh guard still stand on their own.

## 5. Risk register, red specimens, and success criteria

```risk-register
directional-ancestry | exact step commits against the recorded stack graph | only lower-numbered step branches are forbidden carriers and healthy upward reachability stays accepted
partial-commit-carry | the receipted own-commit list for an unmerged step | every recorded SHA is checked so carrying one commit cannot hide behind an unchanged head
mutable-ref-snapshot | remote step refs while GitHub may update them | two bounded ref reads bracket object and PR inspection and a mismatch returns unavailable
pr-base-state | the current recorded pull request on GitHub | live head base state and URL must match the controller plan and failures never become absence
offline-evidence | Git and GitHub transports used by next and status | next withholds merge while status preserves labelled local inspection without claiming live safety
legacy-receipt-gap | older push receipts without an immutable verified commit list | the guard names unavailable evidence and never rebuilds ownership from a mutable base ref
missing-step-ref | a step branch deleted before final integration | the missing named ref blocks landing and the diagnostic retains the step and branch identity
retarget-window | the interval between retargeting the next PR and receipting the current merge | only the current PR base is gated so the required retarget-first order remains valid
post-check-race | the interval after a clear snapshot and before an external click | done merge-step repeats the guard and no output claims atomic prevention
recovery-overreach | a stack already carrying a misdirected merge | the guard stops and points to preserved original commits without rewriting receipts refs or signatures
diagnostic-bounds | remote command output and operator-visible findings | bounded helpers expose exact OIDs and stable reasons without raw credentials or unbounded bodies
frontier-drift | Fiat version and held job surfaces | one generation row retains every held frontier field and the run omits frontier authority
amendment-overclaim | issue 554 runbook amendments beside a remote topology failure | an amendment may replace source instructions but cannot clear Git or GitHub evidence
```

The implementation guards must include these red specimens:

1. **Exact #542 direction.** Step 2 head `4b78dfa` is an ancestor of step 1
   tip `d86fcf9`, while step 2's own tip has not moved. Before the fix, `next`
   returns `merge-step`; after it, `next` blocks and names the owned commit,
   carrier step, branch, and tip.
2. **Open wrong base.** The current step's PR is `OPEN` against the prior step
   branch. The graph is still repairable. The guard blocks with the retarget and
   retry recovery before any merge exists.
3. **Partial carry.** A non-head commit from step 3's verified list is merged
   into step 1 while the step 3 head remains absent there. Checking only the
   head stays red; checking the whole list turns it green.
4. **Healthy upward stack.** Every step 1 commit is reachable from steps 2 and
   3. No later-step commit is reachable downward. The guard is clear.
5. **Retarget-first window.** Step 1 remains current while step 2 has already
   been retargeted to the run branch. The guard ignores step 2's future PR base
   and remains clear.
6. **Correct merge awaiting receipt.** The current PR is `MERGED` into the run
   branch and its commits are reachable from the run branch, not a lower step
   branch. The guard permits the receipt path.
7. **Rewritten later branch.** A waiting branch tip differs from its push
   receipt. The new shared guard retains the existing native-stack refusal and
   its original-commit recovery.
8. **Missing branch and malformed remote output.** Each is unavailable, not a
   clean or a topology finding.
9. **GitHub timeout, authentication failure, malformed JSON, and wrong URL.**
   `next` supplies no merge directive; `status` still exposes local state with
   an unavailable live verdict; no state or ledger bytes change.
10. **Snapshot race.** The first and second ref reads differ. The check refuses
    to combine evidence from the two views and asks for a retry.
11. **Historical PR OID.** A merged PR's `baseRefOid` names the old parent while
    the branch ref names the merge. The guard uses the PR for target identity
    and the ref for current ancestry, rather than treating one as both.
12. **Legacy receipt.** A waiting step lacks `verified_commits`. The guard
    reports that immutable ownership evidence is unavailable and does not call
    `rev-list` against the now-mutable named PR base.
13. **Non-integrate commands.** Study, runbook, build, audit, prose, and push
    phases make no new remote topology call.
14. **Version arithmetic.** Fiat moves from 5.21.1 to 5.22.1 on generation
    only, with the frontier revision, digest, status, current target, next job,
    evolution, and epoch unchanged.

Success means the focused test is red on the signed parent for the #542-shaped
guard and green on the implementation, all fourteen specimens pass, both
complete suites pass, Promise Machine coverage stays current, the exact
changed prose passes Imprimatur, and `git diff --check` exits 0. The demo must
also compare state and ledger bytes before and after every `next` and `status`
case, including blocked and unavailable cases.

## 6. Glossary seeds

- **Owned commit:** one exact SHA in a step push receipt's immutable
  `verified_commits` list, not a commit inferred later from a branch name.
- **Lower branch:** a step branch whose number is smaller than the owner
  step's number.
- **Upward reachability:** an earlier step commit carried by a later step
  branch; the expected stacked-review graph.
- **Downward reachability:** a later step's owned commit carried by a lower
  step branch; the misdirected-merge signal.
- **Current step:** the first step absent from the integrate receipt's ordered
  `merged` prefix.
- **Coherent snapshot:** exact remote ref OIDs that are unchanged across the
  bounded PR and object reads, with the current PR head agreeing with its ref.
- **Deterministic evidence:** controller state, ledger receipts, exact owned
  SHAs, and ancestry computed over exact local objects.
- **GitHub evidence:** mutable PR metadata returned for the recorded URL at one
  bounded live read.
- **Unavailable:** the controller could not answer the evidence question; it
  is neither clear nor blocked by a proven topology fault.

## 7. Sources

- [Issue #555](https://github.com/wildcat-finance/skills/issues/555), including
  its filing-time topology account and warning that moving branch names are
  perishable.
- [Issue #429](https://github.com/wildcat-finance/skills/issues/429), including
  the stalled-run comment naming original head `4b78dfa`, the lost state, and
  the separation among issues #554, #555, #556, and #557.
- [PR #542](https://github.com/wildcat-finance/skills/pull/542), whose live
  metadata and merge `d86fcf9` preserve the misdirected target.
- [PR #509](https://github.com/wildcat-finance/skills/pull/509), the correct
  step 1 merge into the run branch used to distinguish the two directions.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, especially
  `cmd_next`, `cmd_status`, `_integrate_directive`,
  `refuse_rewritten_stack`, `remote_branch_tip`, `commit_is_ancestor`, and
  `inspect_pull_request` at the starting ref.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md` and
  `docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`.
- `docs/fiat-runbook-amendments-study.md` and
  `docs/fiat-runbook-amendments-runbook.md`, shipped by
  [PR #585](https://github.com/wildcat-finance/skills/pull/585).
- `audit/AUDIT.md`, section “Fiat delegation packets, post-push merge
  incident”, for the exact-head and non-rewritten-receipt precedent.
- `plugins/hexaemeron/skills/VERSIONING.md` and
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md` at the starting ref.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) applies to the CLI
result, not to a service metric or alert. The guard runs only when an operator
asks for `next`, `status`, or a merge receipt.

The operator questions are:

1. Which exact step and commit made the stack unsafe, and which lower branch
   carries it?
2. Did the current PR point at the run branch when checked, and what head,
   state, and base did GitHub return?
3. Was the verdict blocked by a proven graph fact or unavailable because a
   transport, ref, object, or response could not be read?
4. What may the operator safely do next: retarget and retry, restore evidence
   and retry, or halt with the original commits preserved?

One structured `stack_guard` result answers them with verdict, checked command
surface, step number, recorded PR URL, exact commit and ref OIDs when present,
evidence class, stable reason code, and recovery class. Human `status` prints
the same facts after its ordinary local state. JSON status carries the same
closed keys. Raw command output, commit bodies, addresses, tokens, and GitHub
response bodies are not signals. No persistent metric or alert is added because
there is no unattended process.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) governs the off-chain
surfaces opened by this check.

- **Controller state and receipts.** Worth taking: exact run branch, ordered
  merged prefix, step branch names, PR URLs, head SHAs, and immutable verified
  commit lists. Control: existing state-shape validation, bounded counts, and
  no reconstruction from chat or mutable refs.
- **Git transport.** Worth taking: exact OIDs for the known `refs/heads/...`
  names and the corresponding commit objects. Control: fixed argv, configured
  `origin`, explicit refs only, no shell, bounded output and time, no branch
  update, two ref reads, and fail-closed status handling.
- **GitHub API.** Worth taking: the recorded current PR's URL, state, head name
  and OID, base name, and merge OID. Control: existing repository-identity and
  URL checks, fixed fields, authenticated local client, bounded output and
  time, strict JSON kinds, and no search-selected PR.
- **Local Git graph.** Worth taking: ancestry status 0 or 1 for exact SHA pairs.
  Control: require all objects by exact OID, preserve the existing rule that
  every other process status means unavailable, and never compare against an
  inferred mutable range.
- **Diagnostics.** Worth taking: stable reason, step, branch, and abbreviated
  or full non-secret OIDs needed for recovery. Control: cap list length and
  message bytes, quote no remote body, and echo no environment or credential.

No secret is newly read or stored. The GitHub client uses its existing
authentication path. The guard does not broaden repository authority: it reads
only the repository and PRs already named by the run.

## 10. The budget, or its absence

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) records no performance
change for this work. The graph is bounded by Fiat's existing maximum step and
commit counts, and the feature makes no latency promise.

The implementation must still avoid one remote process per commit. One bounded
ref listing, one bounded object acquisition for the exact ref set, one current
PR read, one second ref listing, and local ancestry calls are the intended
shape. Tests assert the number of remote calls from a three-step and
maximum-shaped fixture so an accidental nested network loop is visible. No
wall-clock threshold is a success criterion, so there is no before-and-after
measurement to claim.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) governs the red
specimen and repair guard.

The causal failure is the #542 graph: step 2's immutable head remains unchanged
but becomes reachable from step 1 through a GitHub merge. The existing
tip-movement check stays green, which proves the missing predicate. The first
implementation guard must fail on the signed parent because `next` still emits
`merge-step` and `status` lacks a stack verdict. The same fixture turns green
only when both commands use the shared directional predicate.

`next` fails closed by withholding a merge directive for either `blocked` or
`unavailable`. `status` remains readable but cannot print `clear` without a
coherent live snapshot. `done merge-step` writes no state or ledger unless the
fresh result is clear. An exception, timeout, missing object, malformed
response, missing immutable list, deleted ref, or ref race is unavailable.
Only observed downward reachability or wrong current PR topology is blocked as
a proved fault. The distinction is part of the guard and its tests.

The source-bound audit repair runner will be specified in the runbook with one
`{report}` argument, `unittest-json-v1` as its CLI report format,
`elenchus.unittest.v1` as the emitted schema, and a fresh issue-specific report
path. A missing, stale, empty, malformed, or infrastructure-failed report is
`inconclusive`, not evidence that a repair is guarded.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) applies because
the evidence split, directional predicate, and offline behavior will be costly
to rediscover after another merge incident.

- Add a dated issue-#555 addendum to
  `docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`.
  It will record why the early guard uses both exact remote refs and current PR
  metadata, why only downward reachability is forbidden, why only the current
  PR must target the run branch, and why no snapshot prevents the next click.
- State the operator rule and recovery in
  `plugins/hexaemeron/skills/fiat/references/push-discipline.md`. This is the
  command-facing home, not the proof of what the controller observed.
- Put the executable predicate, evidence classification, and structured result
  in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, with red specimens in
  `plugins/hexaemeron/tests/test_hexctl.py`.
- Update the applicable Fiat Promise boundary and coverage only to the claim
  the code can make: a clear result establishes the named topology at one
  coherent snapshot. It does not establish atomic prevention or semantic
  equivalence of commits.
- Record the behavioral release as one Fiat generation row in
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md` and matching SKILL frontmatter,
  expected `fiat-v5.22.1`. Retain the held frontier fields and omit
  `--frontier`.

No new ADR is needed. ADR-021 already owns the landing decision and contains
the earlier, later-detection boundary this issue changes. An addendum keeps the
decision history joined instead of splitting one rule across two records.

If implementation finds that Git cannot obtain the exact remote objects
without updating a branch or that GitHub does not return the named fields for a
recorded PR, the chosen design is blocked. The one clearing action is to amend
this study with the observed command and response boundary before selecting a
different evidence source.
