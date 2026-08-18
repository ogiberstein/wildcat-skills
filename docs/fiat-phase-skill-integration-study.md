# Study: fold the six phase skills into Fiat's loop as contract

## Problem statement

Fiat runs a receipted delivery loop whose phases are held to standards that
now live in six sibling skills, added in
[skills#103](https://github.com/wildcat-finance/skills/pull/103): protasis,
elenchus, phylax, ephoros, metron and hypomnema. Fiat names them only as
notes in its phase table, and it still carries two reference files,
`references/study.md` and `references/runbook-format.md`, whose content
protasis supersedes. Two documents state the same contract and only one of
them is governed.

Working prototype means: Fiat's `SKILL.md` and references name the phase
skills as the contract each phase runs under; the two superseded references
are gone; the surfaces that describe the loop agree with each other; and every
touched document is cold-read clean. The check that proves it: both suites
pass, the three tree lints exit clean, and imprimatur scores every touched
document at 100 with zero defects.

## Prior art

- `plugins/hexaemeron/skills/fiat/SKILL.md` (`fiat-v2.3.1`, frontier reopened
  by epoch in [skills#115](https://github.com/wildcat-finance/skills/pull/115)):
  the loop, the directive table, phase notes that name the six as consultation.
- `plugins/hexaemeron/skills/fiat/references/`: `study.md` and
  `runbook-format.md` carry content rules protasis now owns, plus the receipt
  commands and artefact paths that stay Fiat's. `audit-loop.md` has a
  non-Solidity round that asks for a diff review with no mechanical part.
  `prose-pass.md` orders the masks and holds the receipt. `push-discipline.md`
  and `wildcat-marketplace.md` are untouched by this topic.
- `plugins/hexaemeron/skills/protasis/SKILL.md` (`protasis-v0.1.0`): the
  content contract, with a paragraph saying it is written to be folded in and
  a ledger whose held job is exactly this fold, with the acceptance condition
  "Fiat names no study or runbook content rule of its own and both suites
  pass".
- The other five phase skills, each with a `Serves the ... phase` line and,
  for phylax, ephoros and hypomnema, an executable lint under `scripts/`.
- Tests: `plugins/hexaemeron/tests/test_fiat_skill.py` pins
  `wildcat-marketplace.md` and prose strings in Fiat's `SKILL.md`;
  `test_evolution.py` governs the ledgers and pins the plugin frontier
  sentence; the root `tests/` govern marketplace prose agreement across
  surfaces. `test_hexctl.py` writes its own fixtures and does not read the
  references.
- Surfaces describing the loop: the plugin `AGENTS.md` selection table and
  README, the root `README.md` and `AGENTS.md`, seven `.agents/skills/`
  entrypoints, the codex manifest's long description, and the marketplace
  manifests carrying plugin version `1.1.0`.

## Constraints and non-goals

- Base is `main` at `c8c09e1`. One pull request per step, both suites green at
  every commit, and marketplace prose tests hold surfaces byte-identical where
  they already do.
- `hexctl.py` does not change. The controller's receipts, artefact paths and
  phase order are proven by 124 tests and none of this topic needs them to
  move. The fold moves prose authority, not control flow.
- Fiat must keep standing alone. The bundled masks stay the prose receipt's
  requirement; brevitas is a marketplace sibling, so the loop may name it as
  an option when installed but must not require it.
- The plugin's marketplace-context frontier sentence stays: the bundled
  Solidity audit suite has still not been exercised end to end, and this run
  ships no Solidity.
- The rolling next-job line in the plugin landing README changes only when its
  exact job completes, which this run does not.
- Non-goals past the prototype: teaching hexctl to verify lint receipts
  itself, folding elenchus or metron scripts into the controller, and any
  change to the vendored Pashov suite.

## Design options

1. **Delete the two references and put the receipt mechanics in `SKILL.md`.**
   Protasis becomes the named content authority in the directive table; the
   artefact paths, `steps.json` shape and receipt commands, which are
   controller contract rather than content, move into Fiat's phase notes.
   Two files die, one grows slightly, and no stub survives to drift.
2. **Replace both references with redirect stubs.** Cheapest diff, but the
   stubs are two more surfaces saying "look elsewhere", and a reader following
   the directive table pays an extra hop forever.
3. **Merge protasis bodily into Fiat.** Undoes skills#103, orphans protasis's
   ledger, and makes the content contract invisible to a reader who wants it
   without the controller.

Option 1. It is the construction protasis's own acceptance condition
describes, and the cheapest to comprehend afterwards: one authority per
question, no hop, no stub.

## Risk register seed

- A deleted reference still linked from anywhere: the record lint catches a
  dangling pointer, so run it per round over the changed tree.
- Prose-string pins in `test_fiat_skill.py` breaking on the rewrite: read the
  test before editing, move pins with the format as done for the README table.
- The ledgers: protasis and fiat both take an evolution increment at
  completion, each exactly once, with digests recomputed; a wrong axis or a
  reused digest fails both suites.
- Scope creep into hexctl: the waiver above is the boundary, and any urge to
  make the controller enforce lint receipts goes to the ledger as a next job
  instead.
- Marketplace prose agreement: the context paragraph is held byte-identical
  across three surfaces by test, so any wording change lands on all three in
  the same commit.

## Glossary seeds

A phase skill is one of the six that state what a phase must contain or emit;
each answers alone, and the loop holds its phase to it. The content authority
for an artefact is the skill whose `SKILL.md` says what it must answer: Fiat
keeps artefact paths and receipts, protasis keeps content. The round lints are
phylax, ephoros and hypomnema's scripts, run against the changed tree as the
mechanical part of a non-Solidity audit round.

## Sources

- This repository at `c8c09e1`: the six skill directories, fiat's references,
  both test suites, and the surfaces listed under prior art.
- [skills#103](https://github.com/wildcat-finance/skills/pull/103),
  [skills#113](https://github.com/wildcat-finance/skills/pull/113) and
  [skills#115](https://github.com/wildcat-finance/skills/pull/115) for the
  dependency change, the brevitas rule change and the reopening evidence.
- `plugins/hexaemeron/skills/VERSIONING.md` for the ledger mechanics the
  completion step must follow.
