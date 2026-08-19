---
name: hypomnema
description: >-
  Decide what gets written down and where it lives: the decision record behind
  a choice that would be expensive to reverse, the comment that explains why
  rather than what, the runbook an alert points at, and the README somebody
  starts from. Use when a decision is made, an interface changes, an alert
  needs somewhere to point, or the same explanation has been given twice. Do
  not use it to lint or rewrite prose, which belong to imprimatur and vulgate,
  and do not use it to decide what a study must contain, which belongs to
  protasis.
metadata:
  version: "1.1.0"
---

# Hypomnema

From *hypomnema*, the note written so the reason survives the person who had
it. Code records what was built. This records why, and what was turned down.

## Where this sits

Hypomnema owns what gets recorded and where it goes.

**Use another tool when.** `imprimatur` lints the words and `vulgate` sets
their register, both after this skill has decided there is something to write.
`protasis` says what a study must contain before code exists; this covers what
survives after it. `ephoros` chooses the signals, and this says where the
runbook behind an alert lives.

Serves the `prose` phase. Fiat's prose pass owns the mask order, the PR text
and the receipt, and none of that moves here.

Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md).

## Match what is already there

Look before writing. An existing convention beats every default below, and a
second scheme alongside the first helps nobody.

Check for decision records already in the tree, the numbering and naming they
use, the headings they carry, and any tooling that generates them. Where the
evidence conflicts, say so rather than quietly picking one.

Two conventions already run in this marketplace and its applications. Each
governed skill records its own decisions in an `EVOLUTION.md` ledger, so a
decision about one skill belongs there and not in a second document. The
application generates its changelog from conventional commits through
release-please, so the commit message is the changelog entry, and hand-editing
the generated file loses at the next release.

## Write the record when reversing gets expensive

A decision earns a record when undoing it later would cost real work: a
framework or a dependency that spreads, a data model, a trust boundary, an
interface others build against, a storage format that outlives its writer.

Where no convention exists, put them in `docs/decisions/` numbered in sequence,
and keep this shape.

```markdown
# ADR-001: <the decision, stated as a decision>
## Status
Accepted, 2026-08-18. Superseded by ADR-00N once it stops being true.
## Context
What forced a choice, and what was already true.
## Decision
What was chosen, in one sentence.
## Alternatives
Each one considered, what it offered, and why it lost.
## Consequences
What this makes easy, what it makes hard, and what it commits us to.
```

The alternatives section is the part that pays. A record saying only what was
chosen tells a reader nothing they cannot get from the code; the value is in
the options that lost and the reason they lost.

Records are not deleted when they stop being true. Write a new one, mark the
old superseded, and leave the history where somebody can follow it.

## Comment the reason, never the mechanism

A comment restating the line above it goes stale and was never worth reading.
A comment carrying the reason stays true for as long as the reason does.

```python
# Nothing: the next line says this
counter += 1

# Something: the window resets at the boundary rather than on a timer,
# so a burst at the edge cannot buy a second allowance
if now - window_start > WINDOW:
    counter, window_start = 0, now
```

Write down a trap where somebody will hit it: an ordering that matters, a call
that must happen before another, an argument that looks optional and is not.
Point at the decision record when one exists.

Leave no commented-out code, since history already has it, and no note
promising work you could do now.

## Where each thing lives

- **A decision that shapes the code.** A record under `docs/decisions/`.
- **A decision about a governed skill.** That skill's `EVOLUTION.md`, which is
  the ledger the versioning contract already checks.
- **What an alert means and what to check first.** `docs/runbooks/`, one file
  per alert, named for the alert so the link in the alert can find it. Three
  lines is a runbook: what fired, the first thing to look at, who to wake.
- **How to start the project.** The README: what it is, how to run it, the
  commands, and a pointer onward.
- **What shipped.** The commit message, in the convention the repository
  enforces, where the release tool can reach it.
- **What an agent needs.** The instructions file the runtime reads, kept
  current, because a stale one is followed exactly as confidently as a fresh
  one.

## Interfaces carry their own documentation

Something others call says what it takes, what it returns, and what it raises,
next to the signature rather than in a separate document that drifts. One
example beats a paragraph. Where an interface crosses a process boundary, the
schema is the documentation and prose describes only what the schema cannot.

## The mechanical subset

One rule here is settled by a parser: whether the things a record points at
exist. Run it over the documents a step touched, and require exit 0.

```bash
python3 "$PLUGIN_ROOT/skills/hypomnema/scripts/hypomnema.py" docs plugins
```

It reports a relative link that resolves to nothing, a superseding pointer
naming a record that is absent, and an alert naming a runbook that is not
there. A record pointing at something absent is worse than no record, because
it reads as though the reason exists and was checked.

The bundled third-party skills are skipped, since they document files they
generate in the target repository rather than files that live here. Pass
`--include-vendored` to check them anyway.

Deliberate exceptions state a reason: `<!-- hypomnema: allow <why> -->`, on the
line or the one above it. Deciding what deserves a record stays judgement; this
only checks that what you wrote down leads somewhere.

## Rationalisations

- "The code documents itself." It shows what. It cannot show what was
  rejected, or the constraint that made the choice.
- "Docs come once the interface settles." Interfaces settle sooner when
  written down, because the writing is the first test of the design.
- "Nobody reads documentation." Agents read it every session, and so does
  whoever is on call at three in the morning.
- "A decision record is overhead." Ten minutes now against the same argument
  had again in six months, with nobody able to recall the reason.
- "Comments go stale." Comments about mechanism go stale, which is why this
  skill only asks for the ones about reason.

## Red flags

- A choice that would be expensive to reverse, with no written reason.
- A second decision-record scheme beside an existing one.
- A hand-edited changelog in a repository that generates it.
- A skill decision written somewhere other than its ledger.
- An alert whose runbook link goes nowhere.
- A README that does not say how to run the project.
- Commented-out code kept instead of deleted.
- A note promising work that could be done now.
- An agent instructions file describing a layout that has since moved.

## Before the prose phase is receipted

Report the count, then name every item that failed.

- [ ] Every expensive-to-reverse decision in this step has a record.
- [ ] Each record names the alternatives and why they lost.
- [ ] Superseded records are marked, not deleted.
- [ ] Records follow the convention already in the tree.
- [ ] A skill decision went to its ledger rather than to a second document.
- [ ] New alerts have a runbook file their link resolves to.
- [ ] Changed interfaces document arguments, returns and failures.
- [ ] Non-obvious traps are commented where somebody meets them.
- [ ] No commented-out code and no deferred note remain.
- [ ] The agent instructions file still matches the tree.

## Hand back

Lead with what was recorded and where it went. Name each decision this step
made and the file that now holds its reason.

Separate the decided from the still open. A choice made with its alternatives
written down is settled. One made because nobody objected is open, whatever the
diff suggests, and saying which is which is the whole point of the record.

End with one action: the decision still needing a record, the convention
conflict somebody has to resolve, or the runbook an alert is waiting on.
