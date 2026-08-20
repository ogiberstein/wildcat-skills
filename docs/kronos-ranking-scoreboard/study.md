# Study: record each Kronos ranking pass in a durable scoreboard

Assuming, unless corrected:

1. Python 3.11 or later and stdlib `unittest`, matching every other checker in
   this plugin. The machine running this has 3.14.6.
2. The scoreboard is a per-checkout working record, not a published artefact.
   Nobody outside the machine that ran the loop needs to read it.
3. Kronos keeps its hard rule that Fiat owns all repository work. A scoreboard
   writer that commits, branches or pushes would break that rule.
4. This is generation-axis work. Kronos stays mature, the held frontier target
   and its digest are retained byte for byte, and the run passes no
   `--frontier` flag.
5. The run starts from `fec7ee5` on `main`, with both suites green at 34/34
   and 381/381.

## 1. Problem statement

Kronos scores every eligible held Next Fiat job out of 100 across four axes,
prints the scores and a one-sentence basis in chat, runs the winner through
Fiat, and then at step 8 rescans from disk and reranks from scratch. Nothing
carries from one pass to the next. Two consequences follow.

The first is that axis weighting drifts invisibly. The same held job can score
62 in one pass and 78 three passes later with nothing changed about it, because
the judgement is made fresh each time against a chat transcript that has since
been compacted. Nobody can see the drift, because there is nothing to compare.

The second is that the reasoning evaporates. A maintainer who wants to know why
a frontier was picked in March has the merged pull requests and nothing about
the field those jobs were picked out of.

What is built: a scoreboard writer that appends one validated record per
ranking pass to a durable file, and a reader that renders the file, including
how each skill's per-axis scores moved between passes.

A working prototype means all of this holds:

- `python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py record
  --scoreboard <path>` reads a pass on stdin, validates it, and appends exactly
  one JSON line.
- The appended line carries each candidate's held-job identity hash, computed
  from that skill's `EVOLUTION.md` on disk rather than supplied by the caller.
- `python3 ... kronos.py show --scoreboard <path>` prints the passes, and marks
  every axis score that moved for a skill whose held-job identity hash did not.
- `python3 plugins/hexaemeron/tests/run_tests.py` passes, carrying new cases
  for the writer.
- The demo path: record two passes over this checkout's real ledgers, the
  second changing one axis score for an unchanged held job, and `show` marks
  it.

## 2. Prior art

**In this skill.** `plugins/hexaemeron/skills/kronos/SKILL.md` step 3 defines
the four axes and their caps: material impact 40, evidenced urgency 25,
readiness of inputs 20, work unblocked elsewhere 15. The tie-break in step 4
runs impact, then readiness, then discovery order, and step 8 is the rescan.
Kronos has no `scripts/` directory today. It is prose and one
`agents/openai.yaml`.

**The identity hash already exists.** `plugins/hexaemeron/skills/VERSIONING.md`
defines a canonical line per ledger:

```text
{status}|{frontier revision}|{current frontier}|{next Fiat job}
```

with its final newline, hashed with SHA-256, and stores that digest in every
history row. `tests/test_evolution_contract.py:111` recomputes it and asserts
it matches the latest row. That is the held-job identity hash this study needs.
It is specified, it is tested, and a scoreboard line carrying it can be checked
against the ledger's own recorded digest. Defining a second hash would leave
two ways of naming one thing.

**The checker pattern.** Six sibling skills ship a stdlib-only script with
numbered diagnostic codes, exit 0 clean, 1 findings, 2 bad invocation, a stated
trust boundary, and bounded reads:
`plugins/hexaemeron/skills/protasis/scripts/protasis.py` is the closest in
shape. Each has a matching `plugins/hexaemeron/tests/test_*_checker.py`.

**The gitignored state directory.** Fiat keeps run state in `.hexaemeron/`,
which ships its own `.gitignore` holding `*`, so git never sees it.
`fiat/SKILL.md` states the pattern and `hexctl reset` archives within it.

**Outside.** JSON Lines (jsonlines.org) is the append-only record format used
here already, in `.hexaemeron/ledger.jsonl`.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `fec7ee5` on `main`.
- Python 3.11 or later, stdlib only. No new dependency.
- Kronos must not write to the git index or run git. Its hard rule gives Fiat
  every repository operation.
- Fiat refuses to start against a dirty tree. Anything Kronos writes before
  invoking Fiat has to be invisible to `git status --short`, or the next
  iteration of the loop cannot start.
- `tests/test_version_propagation.py` requires `SKILL.md` frontmatter version
  and the ledger's current version to agree, so the bump and the ledger row
  land in the same step.
- The held frontier revision `terminal-goal-loop` and its digest
  `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` are
  retained byte for byte. Kronos stays mature.

**Non-goals.**

- No scoring. The writer records the judgement; it does not make or second-
  guess it. An axis score is a number the ranking agent supplies.
- No published scoreboard. Not committed, not exported, not signed.
- No cross-checkout merge of scoreboards.
- No change to the four axes, their caps, or the tie-break.
- No enforcement that a pass was actually run. A loop that skips the writer
  produces a shorter file, and only a reader notices.

## 4. Design options

**A. Prose contract only.** State the scoreboard file, its path and its fields
in `SKILL.md`, with no machinery. Cheapest to build. Trades away every
guarantee: the identity hash gets eyeballed or omitted, the axis caps go
unchecked, and the file drifts into whatever each pass felt like writing. The
wishlist entry this study answers exists because prose rules in this estate go
unenforced.

**B. A gitignored `.kronos/` directory and a stdlib writer.** A new
`scripts/kronos.py` with `record` and `show`, appending validated JSON lines to
`.kronos/scoreboard.jsonl` beside a `.gitignore` holding `*`, mirroring
`.hexaemeron/`. The writer computes each identity hash from the ledger on disk
and refuses a pass whose axes exceed their caps or whose selection contradicts
the tie-break. Trades away visibility to anyone who did not run the loop: the
record lives on one machine and not in the repository's history.

**C. Committed records under `docs/kronos/`.** Same writer, output committed so
the history is shared. Trades away the loop itself: an uncommitted scoreboard
file makes the tree dirty, and Fiat stops on a dirty tree before it starts, so
the next iteration cannot run. Committing it instead would put Kronos in the
business of branching and committing, which its first hard rule forbids.

**D. Fold the scoreboard into `hexctl`.** Reuse Fiat's hash-chained ledger and
lock. Trades away the boundary between the two skills: `hexctl` state is
per-run and archived at `reset`, while a scoreboard exists to span runs, and
Kronos is not Fiat.

**Chosen: B.** It is the cheapest construction that keeps the loop able to
start. C is the one a reader wants until the dirty-tree interaction is traced,
and that interaction is not a detail: it stops the second iteration of every
loop. B's cost is stated plainly in the non-goals rather than hidden, and a
maintainer who wants a shared record can copy the file by hand, which is a
decision for a later frontier and not this one.

## 5. Risk register seed

This is Python reading files named on a command line and on stdin. The audit
loop should look hardest at:

- **Untrusted input.** The pass document arrives on stdin. Malformed JSON, a
  candidate list of a hundred thousand entries, a `skill` field carrying path
  separators, and a ledger path pointing outside the checkout are all things a
  caller can hand over.
- **Path handling.** Each candidate names an `EVOLUTION.md` the writer opens to
  compute the identity hash. A path that is a symlink, a device, a directory or
  a two-gigabyte file is the caller's choice, not the writer's.
- **Partial writes.** An append interrupted halfway leaves a truncated final
  line, and the next `record` has to decide what that means rather than
  appending after it.
- **Filesystem behaviour.** Creating `.kronos/` and its `.gitignore` has to be
  safe to repeat, and must not follow a symlink into somewhere else.
- **No secrets, no subprocess, no socket.** The writer starts no process and
  opens no network connection. An audit round should confirm that rather than
  assume it.

## 6. Glossary seeds

- **Pass.** One execution of Kronos steps 1 through 4: discover, filter, score
  every eligible candidate, select one.
- **Candidate.** One eligible governed skill and the held Next Fiat job scored
  in that pass.
- **Held-job identity hash.** The SHA-256 of the canonical frontier line
  defined by `VERSIONING.md`, computed from the candidate's ledger at the time
  of the pass.
- **Scoreboard.** The append-only JSON Lines file, one line per pass.
- **Drift.** An axis score that changed for a candidate whose held-job identity
  hash did not.

## 7. Sources

- `plugins/hexaemeron/skills/kronos/SKILL.md`, steps 3, 4 and 8, and the hard
  rules.
- `plugins/hexaemeron/skills/kronos/EVOLUTION.md`, current version
  `kronos-v0.2.0`, status `mature`.
- `plugins/hexaemeron/skills/VERSIONING.md`, the canonical frontier line and
  the generation-axis rule.
- `tests/test_evolution_contract.py:111`, the digest recomputation.
- `plugins/hexaemeron/skills/protasis/scripts/protasis.py`, the checker shape.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, the dirty-tree stop and the
  `.hexaemeron/` gitignore pattern.
- `plugins/hexaemeron/skills/hypomnema/SKILL.md`, where each record lives.
- The wishlist entry `kronos-1`, artifact `wishlist-grab-bag.md`.

## 8. Signals, and the questions behind them

Kronos runs unattended across a long loop, so the scoreboard is itself the
telemetry. Two questions someone asks afterwards:

- *Why did this frontier get picked over that one?* Answered by the per-axis
  scores and the basis on the pass line. Emitted by the `record` step of every
  pass.
- *Did the ranking change its mind about a job nobody touched?* Answered by the
  drift marking in `show`, which compares axis scores across passes sharing an
  identity hash. Emitted on demand rather than continuously.

`record` writes to stdout only what it appended, and reports refusals on stderr
with a code, so a loop that pipes it can tell an append from a rejection.
[ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal
must carry.

## 9. Boundaries, per capability

- **Reading a pass document from stdin.** Worth taking: a caller can send
  anything. Control: parse with a byte cap, require the top-level shape, cap
  the candidate count, and reject unknown fields rather than storing them.
- **Opening a candidate's ledger by caller-supplied path.** Worth taking: a
  path outside the checkout, a symlink, or a huge file. Control: resolve the
  path, require a regular file, require it to sit under the scoreboard's
  checkout root, and cap the read.
- **Appending to the scoreboard file.** Worth taking: a truncated final line
  from an interrupted run. Control: validate every existing line before
  appending, refuse on a malformed tail rather than writing past it, and write
  with a single append that ends in a newline.
- **Creating `.kronos/` and its `.gitignore`.** Worth taking: an existing
  symlink at that path. Control: refuse anything that is not a real directory,
  and write the `.gitignore` only when absent.

[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list
and the controls.

## 10. The budget, or its absence

None. The writer appends one line per Kronos pass, and a Kronos pass is bounded
by a Fiat delivery that takes hours. No performance claim is made and no change
here is motivated by speed, so
[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) has nothing to measure.

## 11. The fail-closed posture

Every refusal exits non-zero and appends nothing. A pass is recorded whole or
not at all. What stops the run: unreadable stdin, a pass failing validation, a
ledger path that resolves outside the checkout, a malformed existing scoreboard
line, or `.kronos/` occupied by something that is not a directory.

Guard-test convention: a fix for a failure found here adds a case to
`plugins/hexaemeron/tests/test_kronos_scoreboard.py` that fails on the unfixed
tree, following
[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md), which owns the
triage order and the guard rule.

## 12. Decisions and their homes

Two decisions here are expensive to reverse, and both are decisions about a
governed skill, so both belong in `plugins/hexaemeron/skills/kronos/EVOLUTION.md`
per [hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md):

- The scoreboard is gitignored rather than committed. Reversing it means
  reopening the dirty-tree interaction with Fiat.
- The held-job identity hash is the `VERSIONING.md` canonical line rather than
  a hash of Kronos's own choosing. Reversing it invalidates every line already
  written.

The generation row recording both lands in step 3, alongside the version bump
that `tests/test_version_propagation.py` requires to agree with it.

## Boundaries

**Always.** Both suites before a commit: `python3 -m unittest discover -s tests
-p "test_*.py"` and `python3 plugins/hexaemeron/tests/run_tests.py`. The
imprimatur lint on every shipped document. Kronos's held frontier revision and
digest retained byte for byte in any ledger edit.

**Ask first.** Adding a dependency. Changing the four axes or their caps.
Changing the canonical frontier line. Writing anywhere git can see. Touching
CI.

**Never.** Run git from Kronos. Commit the scoreboard. Edit a vendored skill.
Change the held `Next Fiat job` or reopen the mature frontier. Delete a failing
test to make a suite pass. Claim a lint or a suite ran when it did not.
