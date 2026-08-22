# Study: receipted study amendments

Assuming, unless corrected:

1. Issue 446 is ordinary Fiat delivery. It does not advance Fiat's held issue 363 frontier, change Fiat's evolution ledger, or require a package version bump.
2. The exact start is `52b3b45c3d72cb2f163b1dfe88c920035d1385d5` on `main`; the isolated run branch is `fiat/446-receipted-study-amendments`.
3. The accepted subject is the study already receipted by `done study`, after the runbook exists and while a step is open. Draft edits before the study receipt remain ordinary edits.
4. The amended candidate contains the receipted study bytes unchanged followed by one final dated Protasis amendment block. No deletion, rewrite, insertion, or reordering of earlier bytes is an amendment.
5. The amendment block uses Protasis's four fields: `What changed`, `Why`, `Steps touched`, and `Still holding`. Every current or pending step is unbuilt and receives an explicit entry-and-exit verdict in `Still holding`.
6. A valid amendment may continue only when the current step's entry and exit still hold. A broken current-step verdict is recorded but blocks the dependent transition, leaving inspection and an explicit halt or later re-specification available.
7. Python 3 and the standard library remain the implementation boundary. The controller may invoke the bundled Protasis checker by an argv-only subprocess; it adds no dependency or network access.
8. The existing 1 MiB bounded-source limit, scoped-path checks, state lock, atomic state write, hash-chained ledger, and state version 1 remain in force.
9. The ledger records digests and bounded verdict metadata, never the full study, signature material, credentials, or uncontrolled subprocess output.
10. The two reported reproductions are maintainer-recorded issue evidence. Their application trees and timing were not independently inspected in this run.

## 1. Problem statement

Fiat pins the study digest at `done study` and recomputes it before every later delegated packet. Protasis requires a mid-run correction to append a dated amendment to that same study. The first required edit therefore looks identical to tampering, and `hexctl next` refuses it. The controller offers no sanctioned transition that preserves the original belief, validates the correction, and re-pins the amended bytes.

Issue 446 records two separate runs where step 1's baseline disproved the pre-build specification. The first corrected a stray-literal count and an HTML-entity false positive. The second found that lint could not start and three tests were already failing, invalidating stated runbook exits. Re-initialisation recovered execution but erased the original belief from the active ledger.

The working prototype adds a receipted study-amendment command. Given a candidate that appends one valid Protasis amendment, it proves the old receipted bytes are the unchanged prefix, validates the complete study and amendment fields, binds every unbuilt step to a verdict, records both digests, and re-pins the study. A holding amendment lets `next` continue. A broken current-step verdict remains recorded but blocks the dependent transition.

Acceptance is checked by:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_protasis_checker
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
```

The named demonstration creates a temporary run, receipts a study and runbook, appends a four-field amendment, receipts it, observes both digests in the ledger, and obtains the next source-bound packet from the amended study. Negative demonstrations cover prefix mutation, missing fields, missing step verdicts, a broken current step, invalid Protasis structure, oversized input, and post-amendment drift.

## 2. Prior art

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` already supplies most of the required safety boundary. `done_study` reads bounded bytes and stores their SHA-256. `receipted_source` refuses later drift before `delegation_packet` selects a study risk register or runbook step. Mutating commands share the state lock and `commit` appends a hash-chained ledger transition. What is absent is a transition that can replace the expected digest without weakening the drift refusal.

The last two merged pull requests touching the target controller and tests were read before choosing a design:

- [PR 445](https://github.com/wildcat-finance/skills/pull/445), "Bind task issues to Fiat run and step branches", added issue-bound initialization and more fail-closed state and branch evidence. Its carried-forward section leaves issue 363 open and reports no amendment work.
- [PR 444](https://github.com/wildcat-finance/skills/pull/444), "Widen the ledger row gate to the compact shape", aligned controller ledger parsing with the suite and anchored append-only frontier history. It reinforces the rule that a controller mutation needs an explicit, replayable ledger transition.

[PR 307](https://github.com/wildcat-finance/skills/pull/307), "The mid-run spec amendment contract", is the semantic origin. It chose an appended block over an in-place edit or separate amendments file so the document itself preserves the earlier belief. It requires four fields and a verdict for every unbuilt step. It carried the first live use forward; issue 446 is that live use exposing Fiat's missing transition.

The applicable Fiat audit records were read in `audit/AUDIT.md`, including the delegation-packet, state-shape, and task-issue rounds. They show the established pattern: validate bounded external values before state traversal or mutation, bind the exact subject and digest, preserve append-only evidence, and keep receipts narrower than the underlying judgement. The task-issue rounds closed their only parser finding and carried no open lead into this design. The Protasis amendment audit recorded two clean rounds and left live controller use open rather than claiming it existed.

Issue 446 and its maintainer comment are the current failure record. No previous Fiat integration body carries a study-amendment implementation forward. Issue 363 remains the separately held delegated-task identity job and is a non-goal here.

## 3. Constraints and non-goals

The implementation begins at the recorded start SHA and changes only the Fiat controller, focused tests, Fiat instructions or reference prose needed to expose the command, Promise Machine runtime bindings required by a changed canonical skill, and the tracked study/runbook copies required by this delivery. It does not change state version 1 or reinterpret an existing receipt without an explicit amendment history.

The command operates only after both study and runbook receipts exist and while the run is in `steps`. The study receipt remains the canonical path. A candidate outside the target root, unreadable input, symlink escape, wrong phase, absent receipt, digest mismatch unrelated to a final appended block, or oversized source fails before state or ledger mutation.

The original receipted bytes must be the exact prefix of the candidate. The final amendment is the only suffix. Its dated heading and four fields are parsed deterministically, the complete candidate passes the bundled `protasis.py --study` checker, and every step whose status is not `done` is named once with an entry-and-exit verdict. Ambiguous, duplicate, or missing verdicts fail.

An accepted holding amendment updates `receipts.study.sha256` and appends amendment history containing the prior digest, new digest, amendment digest, date, touched step numbers, and normalized step verdicts. The ledger transition carries the same bounded facts. The full prose stays in the study artefact, where the original bytes remain readable as its prefix.

If the current step is marked broken, the controller first records the valid append-only amendment and then blocks later work in durable controller state. It must not emit another Mason, Warden, or Scribe packet from a step whose entry or exit no longer holds. Recovery remains inspection, an explicit safe halt, or a separately specified runbook-repair transition; inventing that second transition is outside issue 446.

Non-goals are arbitrary study rewrites, amending a runbook, editing completed-step history, reopening the study phase, automatically repairing an invalid step, accepting free-form verdicts that cannot be bound to step numbers, changing the Protasis amendment contract, closing issue 363, changing package or skill versions, adding a dependency, touching CI, or weakening ordinary digest-drift refusal.

**Always.** Keep the old bytes as the exact prefix; validate the full study and one final amendment; bind every unbuilt step verdict; use bounded scoped reads and argv-only checker execution; make state and ledger updates under the existing lock; run focused and complete suites before each Fiat commit; run Imprimatur on shipped prose; sign every Fiat-created commit and verify its signature and provenance trailers.

**Ask first.** Change state version or public receipt shape incompatibly; add a dependency; accept edits before the old digest boundary; add a runbook-repair transition; touch CI; edit the held frontier; bypass a failed checker; merge without required gates.

**Never.** Treat arbitrary drift as an amendment; erase the earlier study bytes; infer a holding verdict from silence; emit work for a broken current step; put full study prose, raw checker output, credentials, or signature material in the ledger; claim a checker, test, signature, audit, push, or merge that did not occur.

## 4. Design options

### Option A: restore, edit, and re-run `done study`

This reuses an existing verb but requires reopening the study phase or bypassing its phase gate. It overwrites the one study receipt and leaves no explicit old-to-new transition. The ledger would show a second completion rather than an amendment, obscuring the reason and the step verdicts.

### Option B: accept any new study digest through `record`

A generic receipt replacement is small but cannot distinguish a valid append from arbitrary mutation. It would make the existing tamper refusal user-overridable and would not validate Protasis or bind step effects.

### Option C: a dedicated append-only `amend study` transition (chosen)

Add a narrow command that reads the amended candidate, finds the final amendment boundary, hashes the unchanged prefix against the current receipt, validates the candidate and four-field block, checks every unbuilt step verdict, and commits the new digest plus bounded amendment history. The study itself retains the original bytes and correction. A holding amendment continues; a broken current step records the new evidence but blocks the dependent packet.

This is the cheapest construction that preserves both contracts. Its trade is deliberate narrowness: it does not repair a runbook or allow earlier prose cleanup. A correction that changes a step still needs a separately specified recovery after the amendment is safely recorded.

### Option D: store amendments in a separate file

This keeps the receipted study immutable but contradicts Protasis's decision that the document itself show the earlier belief and its correction. Every consumer would also need to discover and order a second artefact before reading the specification.

## 5. Risk register seed

```risk-register
prefix-forgery | the boundary between receipted bytes and the amendment suffix | the exact candidate prefix hashes to the current study receipt and any earlier-byte mutation refuses before state change
amendment-selection | the final dated amendment block selected from Markdown | fenced decoys earlier headings duplicate final blocks and trailing prose cannot confuse the selected suffix
field-ambiguity | the four required amendment fields | each field occurs exactly once in the final block with non-empty bounded content
step-verdict-coverage | Still holding text mapped to current and pending steps | every unbuilt step number appears exactly once with an entry-and-exit verdict and completed steps cannot be rewritten
broken-step-transition | a valid amendment that invalidates the current step | the amendment is recorded but controller state blocks all dependent packets until explicit recovery
checker-binding | the amended bytes supplied to Protasis | argv-only invocation uses the bundled checker exact candidate and exit status with bounded diagnostic handling
path-scope | candidate and canonical study paths | real paths remain inside the target and bounded reads reject symlink escape directories and oversized sources
partial-write | study artefact state file and ledger during amendment | validation finishes first and controller mutation uses the existing lock and recoverable atomic-write order
receipt-history | mutable current digest beside prior study evidence | amendment history and ledger carry old new and amendment digests without erasing earlier transitions
post-amend-drift | study bytes after a successful amendment | next and verify recompute the new digest and refuse any further unreceipted edit
legacy-state | runs whose study receipt has no amendments member | ordinary reads and next behavior remain unchanged until the new command is used
evidence-overclaim | checker success and normalized verdicts | receipts claim structure order and recorded operator verdicts not truth of the correction or correctness of the remaining plan
```

## 6. Glossary seeds

| Term | Meaning | Boundary |
| --- | --- | --- |
| Receipted study | The study path and SHA-256 accepted by `done study`. | Its current digest is immutable except through the amendment transition. |
| Amendment candidate | The complete original study plus one proposed final amendment block. | It is not trusted until prefix, shape, checker, and step verdict gates pass. |
| Amendment boundary | The byte offset where the final dated amendment heading begins. | Everything before it must hash to the current receipt. |
| Unbuilt step | The current open step and every pending step whose status is not `done`. | Each needs one entry-and-exit verdict. |
| Holding verdict | A step-specific statement that both entry and exit remain valid. | Silence and ambiguous prose are not holding. |
| Broken current step | A current-step verdict saying its entry or exit no longer holds. | The amendment remains evidence, but no dependent packet is authorised. |
| Amendment history | Bounded digest and verdict metadata stored with the current study receipt and on the ledger. | It does not copy the study prose or prove the correction true. |

## 7. Sources

- [Issue 446](https://github.com/wildcat-finance/skills/issues/446) and its maintainer comment, two recorded reproductions, conflict analysis, and proposed acceptance shape.
- Exact start: Git commit `52b3b45c3d72cb2f163b1dfe88c920035d1385d5`.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, especially bounded source reads, `done_study`, `receipted_source`, delegation packets, state commit, halt, verify, and CLI parsing.
- `plugins/hexaemeron/tests/test_hexctl.py`, especially study receipt binding, mutation refusal, packet reconstruction, source decoys, state-shape, locking, and bounded-input cases.
- `plugins/hexaemeron/skills/protasis/SKILL.md`, especially “The spec stays alive”, and `plugins/hexaemeron/skills/protasis/scripts/protasis.py`.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `PROMISE_MACHINE.md`, and `plugins/hexaemeron/AGENTS.md`.
- [PR 445](https://github.com/wildcat-finance/skills/pull/445), [PR 444](https://github.com/wildcat-finance/skills/pull/444), and amendment-origin [PR 307](https://github.com/wildcat-finance/skills/pull/307).
- `audit/AUDIT.md`, Fiat delegation-packet, state-shape, task-issue, and Protasis amendment-contract rounds.

## 8. Signals, and the questions behind them

This remains an interactive controller, not an unattended service. No metric, trace, alert, or background log is added. The command's bounded stdout and stderr, `status --json`, `next`, and the ledger answer the operator questions.

1. “Which study belief changed?” The amendment receipt and ledger expose old, new, and amendment digests plus the amendment date.
2. “Was this an append or arbitrary drift?” A prefix mismatch produces a bounded refusal before controller mutation.
3. “Which steps were reconsidered?” The normalized verdict map names every current and pending step.
4. “May the current step continue?” `next` either emits its source-bound packet against the new study digest or reports the durable broken-step block.

The amendment step emits these signals. Existing `verify` and `next` recheck the amended subject. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) remains the signal authority; this study cites rather than restates its contract.

## 9. Boundaries, per capability

The candidate path and bytes are untrusted filesystem input. Their value is one proposed append-only study. Scoped real-path checks, the existing byte ceiling, exact prefix hashing, deterministic final-block selection, and bounded UTF-8 decoding close that boundary.

The amendment prose is untrusted structured input. Its value is a reasoned correction and step verdicts. Exact field cardinality, explicit step-number coverage, ambiguity refusal, and the bundled Protasis check close that boundary. The controller records that the operator supplied the verdict; it does not assert the prose is true.

The Protasis checker is an internal subprocess boundary. Its value is the mechanical study-shape verdict. The controller invokes the fixed sibling path with `sys.executable`, an argv list, no shell, a timeout, bounded captured output, and the exact candidate bytes presented through a controlled temporary file when necessary.

The study artefact, state, and ledger form the durable-write boundary. Validation completes before mutation. The existing state lock prevents a second controller writer. Atomic replacement and the hash-chained state commit keep the new artefact digest and receipt transition recoverable; a killed run must leave either the old receipted state or the new recorded state, never an unlabelled mixed claim.

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) remains the boundary and control authority; this study does not duplicate its rules.

## 10. The budget, or its absence

No speed improvement is claimed, so there is no Metron before-and-after budget. The command performs bounded linear reads and one bundled checker invocation over a study already capped at 1 MiB. Existing controller timeouts and byte ceilings are functional safety limits, not performance claims.

The focused regression command is the repeatable check:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl
```

If implementation introduces an optimization, cache, parallel path, or a new latency claim, amend this study before the change. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md) remains the measurement authority.

## 11. The fail-closed posture

The known red parent is the reproduction already present in `test_receipts_bind_bytes_and_mutation_refuses_packets`: after a receipted study changes, `next` returns the study-digest refusal. New Elenchus guards preserve that refusal for arbitrary edits while demonstrating the one sanctioned append path.

Before implementation, focused tests must show the unfixed controller has no `amend` verb and that a Protasis-shaped append still leaves `next` refusing. The fixed tree then accepts only the valid append, records both digests, and emits the amended packet. Removing prefix comparison, any required field, a step-verdict coverage check, checker binding, or the current-step block must make a named regression red again.

Malformed candidate paths, prefix edits, duplicate or missing fields, fenced-heading decoys, invalid dates, missing or duplicate step verdicts, completed-step rewrites, checker failure, oversize, wrong phase, concurrent mutation, and post-amend drift stop at the nearest boundary. No error path rewrites the ledger to manufacture a pass. A valid amendment that marks the current step broken is recorded, then the controller blocks dependent work and names explicit recovery.

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) remains the triage and guard authority. The audit record must distinguish the original failure, each red guard, the fix, and the clean rerun.

## 12. Decisions and their homes

The append-only command, prefix proof, four-field validation, unbuilt-step verdict gate, bounded receipt history, and broken-current-step block are governed Fiat behavior. Their stable contract belongs in `plugins/hexaemeron/skills/fiat/SKILL.md` and the narrow CLI implementation in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`.

Red-to-green behavior belongs in `plugins/hexaemeron/tests/test_hexctl.py`; structural prose assertions belong in `plugins/hexaemeron/tests/test_fiat_skill.py`; existing Protasis checker behavior remains in its own tests unless implementation exposes a concrete missing checker rule. Promise Machine digest bindings move only as required by changed canonical bytes.

The accepted study and runbook receive tracked copies in the existing Fiat documentation area during step 1. Audit dispositions append to `audit/AUDIT.md`. The implementation decision does not earn a standalone ADR because one governed skill's instructions and tests are its established home. It does not earn an evolution row or version change because issue 446 is not the held frontier job.

If implementation needs a runbook-amendment transition, a new state version, a dependency, or a change to Protasis's contract, amend this study before code. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) remains the record-placement authority.
