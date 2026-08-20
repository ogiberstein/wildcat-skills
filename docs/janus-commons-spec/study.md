# Study: Create the janus skill in the Wildcat Commons

**Run branch:** `claude/janus-wildcat-skill-bejdy0`, cut from `main` at
`496f7a102bf012195c48ed1615f8eff7fd832f7b`. That SHA is the run's real start.

Assuming, unless corrected:

1. "Create the janus skill" means publishing the delivered janus specification
   into this repository's structure, not building the conformance harness. The
   spec's own status line reads "unbuilt spec", its marketplace-context block
   says Janus "remains an unbuilt hook-conformance specification", and its
   "What ships with it" list is a future inventory. Building the harness would
   contradict the document being landed.
2. The delivered spec text is preserved byte for byte. Its SHA-256 is
   `8234ee09201927aeb8df34c9068c5c68e9201539057ccffce3d2600dd724c3ed`, and the
   landed file must carry the same digest.
3. Janus gets no install surface: no `marketplace.json` entry, no
   `plugins/janus/` directory, no portable entry under `.agents/skills/`. The
   marketplace lists tools that do a job today; an unbuilt spec does not.
4. Python 3.11 and stdlib `unittest`, matching the repository's root suite.
5. The run branch is the session-designated `claude/janus-wildcat-skill-bejdy0`
   rather than a topic slug, matching the precedent of the horos delivery
   merged as PR #242 from `claude/horos-boundary-skill-scope-d1ho0d`.
6. This runtime has no `gh` CLI; pull requests and merges run through the
   authenticated GitHub MCP tools instead.

## 1. Problem statement

The root README's Wildcat Commons section names `janus` as one of two tools
that remain unbuilt, in one sentence and with nothing behind the name. Wildcat
Labs has now written the full specification: what Janus tests, why it belongs
to Wildcat, its seven gates, what will ship, its prior art and its open
questions. The work is to land that document in the repository where a
reader of the Commons section will find it, without pretending the tool
exists.

A working prototype here is the delivered spec present in the tree at its
delivered digest, reachable from the Commons section, with the full root test
suite green. The demo path:

```text
python3 -m unittest discover -s tests
sha256sum docs/commons/janus.md          # 8234ee09...24c3ed
grep -n "docs/commons/janus.md" README.md
```

## 2. Prior art

- `README.md` lines 476 to 488: the Commons section's "What remains" list,
  holding the one-line `janus` and `berean` entries this spec expands.
- The graduated Commons tools: `ariadne`, `tabularium`, `pandects`, `lazarus`,
  `alexandria`, each of which entered the tree as a built plugin. None entered
  as a spec, so there is no unbuilt-spec precedent to copy.
- `tests/test_shipped_prose_lints.py`: its scope docstring names `docs/**` as
  "records of what was written at the time", including "a delivered spec".
  That is the test suite's own word for what this run lands.
- `tests/test_marketplace_prose.py`: `marketplace.json` must name exactly the
  twelve shipped plugins; every plugin landing README carries a frontier
  sentence, a Next Fiat job line and a marketplace-context block. These
  contracts are what a `plugins/janus/` placement would have to satisfy.
- `tests/test_version_propagation.py` and `tests/test_evolution_contract.py`:
  every `SKILL.md` under `plugins/*/skills/` is governed by the versioning
  contract and an `EVOLUTION.md` ledger.
- The horos delivery, PR #242, merged from a `claude/` branch: the structural
  precedent for this run's branch shape.
- [ERC-7579](https://eips.ethereum.org/EIPS/eip-7579), named by the spec as a
  second hook architecture to study and explicitly not to share claims with.

## 3. Constraints and non-goals

Constraints: starting ref `496f7a1` on `main`; Python 3.11; no new
dependencies; the spec lands byte-identical to delivery; every edited shipped
document scores clean under the imprimatur lint; the run ships no Solidity.

Non-goals, deferred past this delivery: the hook-manifest schema, host-adapter
interface, state-delta recorder, Foundry harness, hostile reference hooks,
Wildcat host adapter, SARIF reports; any `berean` document; any change to the
marketplace manifests or install instructions.

## 4. Design options

1. **Full plugin at `plugins/janus/`.** Maximal visibility: janus would appear
   beside the shipped tools. Trades away honesty and economy. The marketplace
   test pins `marketplace.json` to exactly the shipped plugins, the landing
   README contracts demand a frontier sentence and a rolling Fiat job, and the
   versioning contract demands a ledger. All of that surface for a tool whose
   own spec says it is unbuilt, in a marketplace whose role table scores
   plugins "for doing the job". Rejected.
2. **Delivered spec under `docs/commons/`, linked from the Commons section.**
   The spec lands as a record at `docs/commons/janus.md`, and the `janus`
   bullet in "What remains" gains a pointer to it. Trades away install-surface
   visibility: a reader finds janus only through the README or the tree. This
   matches the prose-lint scope's own description of `docs/**` and adds one
   directory that `berean` can join later. Chosen: it is the cheapest
   construction to comprehend that still meets the problem statement.
3. **Root-level `commons/` directory.** A new top-level namespace for one
   file. The prose sweep would lint it as shipped prose, so any later lexicon
   change could force rewrites of a delivered record, and the README's
   repository-layout section would need a new entry. Rejected.
4. **Spec text inlined into the README.** The Commons section would grow by a
   hundred lines of another document's content, all of it under the README's
   lint. Rejected.

## 5. Risk register seed

What the audit loop should look hardest at:

- The README edit. `test_marketplace_prose.py` asserts exact sentences and
  section ordering in the README; the new pointer sentence must not disturb
  them, and must itself score clean under imprimatur.
- Byte preservation. The prose pass rewrites prose artefacts; the spec is a
  delivered record and must leave the pass with its digest unchanged.
- Sweep boundaries. The spec carries a marketplace-context block without a
  frontier line. Today no test scans `docs/**` for those blocks; confirm that
  remains true of the suite as landed, not assumed from memory.
- Placement misread. If a full plugin was wanted after all, the reversal is
  one file move plus one README sentence; the recorded assumption makes the
  reading loud rather than silent.

## 6. Glossary seeds

- Wildcat Commons: the README section holding tools Wildcat publishes for
  anyone to inspect, run and improve.
- Hook: a module a host protocol calls before and after an action.
- Host action: the protocol operation a hook runs around, such as a deposit
  or withdrawal.
- Hook manifest: the declaration of what a hook may observe and change.
- Host adapter: the piece that exposes one protocol's actions and state to
  the harness, and limits every claim to that protocol.
- Delivered spec: a document landed as a record of what was written, kept
  byte-identical rather than re-edited under later rules.
- Landing README: a plugin's `README.md` carrying the marketplace contracts;
  janus deliberately does not get one.

## 7. Sources

- Delivered spec: session upload `df2f2f4d-janus.md`, SHA-256
  `8234ee09201927aeb8df34c9068c5c68e9201539057ccffce3d2600dd724c3ed`.
- `README.md` (Commons section, repository layout, Publish section).
- `tests/test_marketplace_prose.py`, `tests/test_shipped_prose_lints.py`,
  `tests/test_portable_skills.py`, `tests/test_version_propagation.py`,
  `tests/test_evolution_contract.py`.
- `git log --first-parent main`, PR #242 merge commit `496f7a1`.
- https://eips.ethereum.org/EIPS/eip-7579

## 8. Signals, and the questions behind them

None. Nothing in this delivery runs unattended: it lands two documents and one
README sentence, checked by the root test suite at commit time. There is no
process to ask about at three in the morning. [ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md)
owns signal content where a run has any; this one has none to carry.

## 9. Boundaries, per capability

None opened. The change adds Markdown and edits README prose: no input
parsing, no subprocess, no network call, no credential, no execution path.
[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list
where a step opens one; the audit round still runs its lint so the claim of
"none" is checked rather than trusted.

## 10. The budget, or its absence

None. No performance claim is made and nothing here is measured for speed.
[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where one
exists.

## 11. The fail-closed posture

A red result from `python3 -m unittest discover -s tests` stops the step: no
commit and no push while any root suite fails. A digest mismatch on
`docs/commons/janus.md` is treated the same way. Any failure surfaced
mid-step is worked under [elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md)
before the step continues, and its guard lands in the root suite where the
regression would recur.

## 12. Decisions and their homes

One decision is expensive to reverse once published: where janus lives, and
that it is a record rather than a plugin. Its record is this study's Design
options section, committed under `docs/` in step 1. No `docs/decisions/`
record is created: that scheme is not in the main tree today, and
[hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) warns against a
second scheme beside an existing one; introducing a repository-wide
decision-record convention as a side effect of a janus delivery would itself
be a decision taken silently. The evidence conflict, per hypomnema, said
plainly: unmerged branches show a `docs/decisions/` scheme was tried and then
rolled back, so this run cites the study and leaves that convention alone.

## Boundaries the study must state

- **Always.** The root test suite before every commit. The imprimatur lint on
  every shipped document this run touches. The spec digest checked after any
  pass that could rewrite it.
- **Ask first.** Adding janus to `marketplace.json` or any install surface.
  Creating a `docs/decisions/` scheme. Touching CI. Editing any exact sentence
  `test_marketplace_prose.py` asserts.
- **Never.** Reword the delivered spec. Edit a vendored directory. Delete or
  weaken a failing test. Claim a command ran when it did not.
