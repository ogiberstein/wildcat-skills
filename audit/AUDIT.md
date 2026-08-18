# Rolling Fiat frontiers audit

## Step 1, round 1 -- 2026-08-17

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| None | - | - | The committed non-Solidity diff has no open finding. | clean |

The review checked the nine landing-page commands, frontier agreement across
marketplace copies, the scope of skill-level README deletions, stale live
links, the protected Lazarus fixture digest, and the Alexandria receipt
regenerated after Probitas added two venues. The repository Python matrix and
Pandects Foundry checks pass.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 1 -- 2026-08-17

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `plugins/alexandria/scripts/alexandria_lib/compound_registry.py` | Offline validation checked the registry's shape and pin labels but did not bind all 28 generated entries to the reviewed registry bytes; Git replace objects could also affect source reads. | fixed in this round |
| S1-R1-02 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | Rebound malformed RPC results could raise uncontrolled type errors, an error response could also carry a result, and a nested trace-filter frame was not tied to the selected transaction. | fixed in this round |
| S1-R1-03 | high | `plugins/tabularium/scripts/tabularium_lib/compound_witness.py` | A relevant slot-0 or `userBasic` write at an unexpected depth was silently skipped when a later write restored the expected poststate, leaving an unexplained write out of the witness. | fixed in this round |
| S1-R1-04 | medium | `plugins/tabularium/scripts/tabularium_lib/compound_witness.py` | Witness verification used unbounded path reads and did not verify that the imported Alexandria module came from the sibling plugin. | fixed in this round |

The review covered the study risk register, the full implementation diff,
registry and corpus pins, capture bounds and secret handling, JSON-RPC
request/result binding, proxy and implementation storage attribution, call to
opcode alignment, Ethereum Keccak, signed `int104` decoding, offline no-write
behaviour and immutable release bytes. Focused suites now pass 253 Alexandria
tests and 134 Tabularium tests. Both socket-denied rebuilds match the committed
release and witness.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 2 -- 2026-08-17

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | Round 1's top-level type checks did not cover malformed struct-log elements, nested prestate maps or non-hexadecimal proxy runtime code, so some rebound evidence could still fail outside the controlled refusal path. | fixed in this round |

The hardening review also checked the registry generator against the pinned
Comet Git objects with replacement refs disabled. Its bytes match the
committed registry. The focused hostile tests and both socket-denied rebuilds
pass after the nested evidence checks.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 3 -- 2026-08-17

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | The capture bounded each response but not aggregate bytes, so a permitted 48-request run could exhaust disk well before a component crossed its individual ceiling. | fixed in this round |
| S1-R3-02 | medium | `plugins/tabularium/scripts/tabularium_lib/compound_witness.py` | The principal fact pointed at the entire opcode list and only the poststate slot; it did not bind the prestate map that establishes an absent slot as zero or each exact principal-writing struct log. | fixed in this round |

The aggregate capture cap is 128 MiB and fails before installation. The
principal fact now selects the prestate storage map, exact poststate slot and
each contributing struct log. The witness manifest also binds the fact byte
count. Focused tests and both offline rebuilds pass with the regenerated
unpublished witness bytes.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 4 -- 2026-08-17

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| None | - | - | The fixed non-Solidity tree has no open finding. | clean |

The clean review repeated the registry, capture, JSON-RPC, trace alignment,
storage attribution, source-selector, safe-read, schema and immutable-byte
checks against the accumulated audit branch. All 255 Alexandria tests and 134
Tabularium tests pass. Both socket-denied rebuilds match, and the twelve
published Goldfinch and Euler truth digests are unchanged.

Leads not pursued: none.

## Fiat installed-path proof, step 1, round 1 -- 2026-08-17

The Solidity suite was waived because this step changes only Markdown
evidence and governed skill metadata. The review covered every changed line
against the runbook risk register.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | `plugins/hexaemeron/docs/fiat-installed-path-and-maturity-proof/proof.md` | The proof reported 14 non-blocking Imprimatur signals, but the reproducible per-file total is 15. | Fixed on the stacked audit branch before round 2. |

Leads not pursued: publisher authentication, cache signing, native Windows
support, and general release attestation are outside this frontier and are
not claimed by the proof.

## Fiat installed-path proof, step 1, round 2 -- 2026-08-17

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| None | - | - | The corrected non-Solidity tree has no open finding. | clean |

The clean review repeated the controller-path, target-root, receipt-order,
source-hash, frontier-version, digest, maturity, test-result, and prose-count
checks against the stacked branch.

Leads not pursued: publisher authentication, cache signing, native Windows
support, and general release attestation remain outside this frontier and are
not claimed by the proof.

## Imprimatur labelled prose, step 1, round 1 -- 2026-08-18

The Solidity suite was waived because this step changes a Python evaluator,
frozen evaluation data, tests, prose and governed skill metadata. The review
covered provenance and the 1 August 2025 cutoff, default-branch reachability,
blind-id separation, independent annotator ids, UTF-8 offsets, source-group
split isolation, duplicate checks, one-to-one span pairing, metric
denominators, candidate freezing, the spent holdout and the open-frontier
decision.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/evaluate_labelled_corpus.py` | The evaluator parsed the published schemas but did not apply them to fixture rows, and it did not verify the annotation-seal or candidate-freeze digests before scoring. A changed row or schema could therefore be evaluated under the same published evidence claims. | Fixed in this round: the standard-library evaluator now enforces the schema subset, checks both digest manifests, and rejects identical annotator ids; mutation regressions cover row and schema changes. |

The focused evaluator has 15 passing checks after the fix. The 55 Imprimatur
tests, 61 Hexaemeron tests and 14 repository tests also pass. Replaying
`final.json` still produces the same metrics and gate decisions.

Leads not pursued: model authorship beyond the declared provenance rule,
population-prevalence claims and tuning against the spent v1 holdout are
outside this frontier and are explicitly disclaimed by the fixture.

## Imprimatur labelled prose, step 1, round 2 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| None | - | - | The fixed non-Solidity tree has no open finding. | clean |

The clean review repeated the fixture-row schema checks, annotation and
candidate digest checks, distinct-annotator check, UTF-8 span validation,
split isolation, metric replay and frontier digest verification against the
stacked audit branch. The focused evaluator has 15 passing checks and the
published calibration and final reports replay without a byte difference.

Leads not pursued: model authorship beyond the declared provenance rule,
population-prevalence claims and tuning against the spent v1 holdout remain
outside this frontier.

## Withdrawal batch fee law, step 1, round 1 -- 2026-08-18

The Pashov pair did not run and no campaign ran, because this step commits two
markdown documents and touches no Solidity. Saying so is the point: the
`security_suite` receipt names `x-ray`, `solidity-auditor` and `fizz`, none of
them read this diff, and a zero count here would assert they had. The review
instead read the committed spec against the risk register it declares, against
the nine shipped laws, and against the two models it proposes to correct.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/study.md` | The study asserted that all nine laws hold in the violating state, but only the five single-state laws had been executed. The four pair laws were reasoned about from what a fee does not touch. In a corpus whose whole argument is that a passing campaign proves nothing without a specimen, an argued verdict presented beside measured ones is the same defect one level up. | Fixed in this round: all four pair laws executed against the pair on both models, and the study now reports what was run. `accrual/path-independent/v1` returns held and the study says that verdict carries no weight, because the law compares two runs rather than one system's before and after. |
| S1-R1-02 | low | `plugins/pandects/docs/withdrawal-batch-fee-law/study.md` | The study named a fee leak in `integrations/wildcat/WildcatMarketModel.sol` with figures, and never fixed the boundary to the deployed market contracts. The plugin's own applicability document warns that nothing in the model should be mistaken for them; a reader meeting the figures first could take the study as a claim about the protocol. | Fixed in this round: the study states that the finding is about the reduced model and the corpus's silence, and that it establishes nothing either way about the deployed contracts. |

A third lead was checked and is not a finding. The study's chosen statement is
false of `Sound` as shipped, and the study says so and builds on it. That is the
method in `docs/writing-a-law.md` working rather than a defect in the spec.

Leads not pursued: whether the two model corrections should ship as their own
step ahead of the law, which the runbook argues against on the grounds that
`pandects.py check` and the corpus diagonal leave no green intermediate state;
and the seven property families deferred from the original delivery, which are
outside this frontier.

## Withdrawal batch fee law, step 1, round 2 -- 2026-08-18

Again no Solidity in the diff and no campaign, for the same reason, stated again
rather than counted as a clean suite run. This round read the round-1 fixes back,
then checked the runbook's own numbers against the test files it points step 2 at.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | The runbook sized step 2's test work as the diagonal growing "from 9x9 to 10x10 over the single-state half". No such table exists. `test/Corpus.t.sol` runs its diagonal over the single-state laws alone, where `COUNT` is 5, and `test/Pairs.t.sol` runs over 3, with path independence handled separately. Nine and ten are corpus totals. Whoever implemented step 2 from the runbook would have gone looking for a table with the wrong shape. | Fixed in this round: the runbook names both dimensions and says that ten is a total rather than a dimension. |

The round-1 fixes were re-read and hold. The four pair-law verdicts in the study
match what was executed, the path-independence caveat is stated where the verdict
appears, and the boundary sentence about the deployed contracts sits in the
problem statement where a reader meets the figures.

One check found nothing and is worth recording because it removes work from step
2. `test_the_sound_reference_holds_every_law` charges its fee before it reserves,
so the queue is empty when the cap applies and the tightened cap cannot change
that test. The runbook now says so.

Leads not pursued: the two carried from round 1, unchanged.

## Withdrawal batch fee law, step 1, round 3 -- 2026-08-18

No Solidity and no campaign again. This round read the runbook's file lists
against what the repository actually generates and against what it treats as a
record, which is the class of error the previous two rounds had not looked at.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 2 listed `docs/catalogue.md` as a file to write and step 4 listed it again as prose to reconcile. It is neither: `python3 scripts/pandects.py render` generates it and `tests/test_documents.py` checks it against the renderer. A hand-edit either fails that check, or passes it by reproducing what the renderer would have produced and thereby hides a real drift. An earlier round of the original delivery, S5-R2-01, fixed the renderer for exactly this reason. | Fixed in this round: step 2 regenerates it and says why, and step 4 drops it from the prose surfaces and names the command. |
| S1-R3-02 | low | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 4's reconciliation list left this run's own study and runbook out without saying so, and both of them claim Pandects ships nine laws. The omission reads as an oversight rather than a decision, so an implementer would either rewrite a spec into disagreement with the run it specifies, or leave a claim stale with nothing recording which was meant. | Fixed in this round: step 4 states that the two spec documents are records on the same footing as the audit log's historical rounds and are not reconciled, and why rewriting them would be worse. |

The round-2 fix was re-read against the sources. `COUNT` is 5 in
`test/Corpus.t.sol` and 3 in `test/Pairs.t.sol`, which is what the runbook now
says.

Leads not pursued: the two carried from round 1, unchanged.

## Withdrawal batch fee law, step 1, round 4 -- 2026-08-18

No Solidity and no campaign. This round read step 3's evidence requirement
against the tooling that exists to satisfy it, and re-checked which documents in
the plugin are generated, which the previous round had only established for one of
them.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 3 asked for "a search record for each run" and for "a run record beside the existing campaign evidence", without naming a mechanism. One exists and does not cover the case: `python3 scripts/pandects.py run` writes a search record and knows only the `foundry` engine. An implementer would either read the requirement as satisfied by that command for all three engines, which would silently drop the two fuzzers the step exists to run, or invent a record format for them. | Fixed in this round: step 3 names the command for the Foundry record, says it has no Echidna or Medusa support, and requires the two fuzzers to be recorded as audit prose the way the original delivery recorded them. It also says not to extend the runner here. |

`docs/applicability.md` was checked and is not generated. `pandects render` writes
`docs/catalogue.md` and nothing else, so step 4's remaining prose surfaces are
hand-written and correctly listed.

Leads not pursued: extending the search-record runner past `foundry`, now stated
in the runbook as out of scope for this step and a candidate frontier of its own;
and the two carried from round 1.

## Withdrawal batch fee law, step 1, round 5 -- 2026-08-18

No Solidity and no campaign, for the fifth time and for the same reason. This
round re-read the four earlier fixes against their sources and then resolved every
file path the two documents name, which is the check that catches a spec rotting
against a repository that moved under it.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| None | - | - | The fixed non-Solidity tree has no open finding. | clean |

Thirty-nine distinct paths are named across the study and the runbook. Every one
resolves, except the two the run exists to create,
`src/laws/PooledClaimsCoverOpenBatches.sol` and `specimens/FeeFromQueued.sol`, and
a glob in the sources list. The earlier fixes hold: the pair-law verdicts match
what was executed, the deployed-contract boundary sits where the figures are, both
diagonal dimensions match `COUNT` in their test files, `docs/catalogue.md` is
regenerated rather than written, the two spec documents are declared records, and
step 3 names the runner and its single engine.

Leads not pursued: extending the search-record runner past `foundry`; whether the
two model corrections should ship ahead of the law, which the runbook argues
against on the grounds that no green intermediate state exists; and the seven
property families deferred from the original delivery. Each is recorded in the
round that raised it.

## Withdrawal batch fee law, step 2, round 1 -- 2026-08-18

Reviewed: the whole of the step's diff. The new law, both model corrections, the
specimen, the counterexample, the catalogue entry, the renderer, the test that
counted for it, and the Wildcat notes.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `search-record.json` | The record shipped at the plugin root stated nine laws and a corpus digest taken over nine, and the corpus now holds ten. Nothing compared it with the catalogue, in CI or in the suite, so it had gone stale silently and would have gone stale again on the eleventh law. A stale search record is worse than an absent one: it carries a count and a digest with the authority of something a script produced, and nothing about reading it says when. | Fixed in this round: regenerated, and three tests now hold the shipped record against the catalogue's law count, its recomputed digest and its version. Each was made to fail against a perturbed record before being kept. |
| S2-R1-02 | medium | `test/SoundInvariant.t.sol` | The harness asserted the five old single-state laws over the reference under fuzzing and did not assert the sixth. So the one law whose correctness rests on two caps that were just rewritten was the one law no search checked against the reference; the diagonal tested it at a single hand-derived state. A cap is exactly the thing a single state cannot vouch for. | Fixed in this round: `invariant_pooled_claims_cover_open_batches` added. It passes at 64 runs and 4096 calls with no reverts. |
| S2-R1-03 | medium | `adapters/medusa/README.md` | The document offered the command line as an alternative to the config file and then claimed, two paragraphs later, that the settings match `adapters/echidna/echidna.yaml`. Both cannot be true. Naming a target on the command line means not passing `--config`, so the run happens under Medusa's defaults, with assertion testing on where the file turns it off. Anyone following the documented command and recording the shipped configuration would be recording a different search from the one they ran. Passing both is worse: the file's empty `targetContracts` beats `--target-contracts`, and Medusa exits with no tests found before searching anything, which is the silent non-run this same file warns about at the bottom. | Fixed in this round: the file route is now the documented one, the command-line route is named as a run under Medusa's defaults, and the both-flags case is written down with the exact message it exits on. |

**What ran.** 75 Solidity tests across ten suites under forge 1.7.1 and solc
0.8.28, up from 74 by the invariant added here. 109 catalogue, checker,
search-record and document tests on Python 3.14, up from 106 by the three gates
added here. The repository's 20. `pandects check` over ten laws, every part
present. Slither 0.11.6 over 50 contracts. Echidna 2.3.3 against `SoundCampaign`
and `WildcatMarketCampaign` with the shipped configuration and seed 20260816.
Medusa 1.5.1 against `SoundCampaign` at twenty thousand, run through a copy of
the shipped config with `targetContracts` filled in, for the reason S2-R1-03
gives.

**The engines on the corrected models.** `SoundCampaign` failed nothing under
either engine: eight properties passing over 20,116 calls under Echidna, eight
passing under Medusa. `WildcatMarketCampaign` failed
`recorded_claim_never_shrinks` and nothing else, which is the documented
expectation for a design whose batches accumulate while open, and it is unchanged
by the fee correction. So neither correction cost the corpus a property, and
neither introduced one.

**What the engines did not test.** The new law. `src/campaigns/Specimens.sol`
carries one property per law and the new one is not among them, which is step 3's
whole content. Foundry's invariant runner reaches it after S2-R1-02 and the two
fuzzers do not reach it yet. Saying so is the point: eight properties passing is
evidence about eight laws.

**Slither.** Twenty-three results across three classes, all of them the same
benign set the original delivery documented: cached array length in four queue
traversals, costly operations inside a loop that returns after one iteration, and
one unused constant inherited by a specimen. Nothing names the new law or the new
specimen.

**The independence argument, and its limit.** `FeeFromQueued` can only lower
`claims` further than the reference would, so the laws it could break are the
ones bounded below by `claims`. The old cap stopped exactly at `reserved`, which
is why `reserves-backed-by-claims` survives it, and the remaining eight read
quantities a fee does not move. That is an argument rather than a search, the
diagonal checks one state, and step 3 is where an engine gets to disagree.

Leads not pursued:

- **`pandects run` knows one engine.** The shipped record carries the Foundry
  campaign and nothing else, so the Echidna and Medusa evidence in this run lives
  in this log as prose. That is the arrangement step 3 was told to keep and it is
  a candidate frontier of its own, recorded in the runbook.
- **The two carried from step 1**, unchanged.

## Withdrawal batch fee law, step 2, round 2 -- 2026-08-18

Reviewed: the tree with round 1 applied, and what round 1's own commit did to it.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | `.gitignore` | Round 1's commit tracked three engine artefacts: `crytic-export/combined_solc.json`, `.medusa-artifact-hash` and `slither_results.json`. The ignore rules for all three existed and did not match, because they were written as `plugins/*/` and an engine writes beside wherever it was invoked from. The Medusa run went through a config under `adapters/medusa/`, so the artefacts landed two levels below the plugin root and walked straight past a one-level pattern. This is the lead the original delivery carried from its own step 5 round 2 about `slither_results.json` being tracked, arriving again by the same mechanism. | Fixed in this round: the three files are untracked, the patterns are depth-independent, and a fresh Medusa run confirmed all three are ignored where they are actually written rather than where the old patterns expected them. |
| S2-R2-02 | low | `.gitignore` | `plugins/*/search-record.json` sat in the fuzzing-output section while the file it names is tracked, shipped as evidence, and as of round 1 held to the catalogue by three tests. The two statements cannot both be right. Left alone, a fresh clone that regenerated the record would show no diff, and deleting it would draw no complaint from git. | Fixed in this round: the entry is removed and the reason it is not output is written where the entry used to be. |

**What ran.** The full suite again on the fixed tree: 75 Solidity tests under
forge 1.7.1, 109 Python tests, the repository's 20, `pandects check` over ten
laws. Medusa 1.5.1 twice more, once to reproduce the artefact paths and once to
confirm they are ignored. No engine re-run was needed for the findings themselves,
because neither touches a contract.

**What round 1's fixes look like on re-reading.** The three search-record gates
were re-checked against a perturbed record and each still fails for its own
reason. `invariant_pooled_claims_cover_open_batches` still passes at 64 runs and
4096 calls. The Medusa README's file route was exercised in this round, which is
how the artefact paths in S2-R2-01 were found: following one's own corrected
instructions is what surfaced the defect the instructions caused.

Leads not pursued: the two carried from step 1, and `pandects run` knowing one
engine, carried from round 1.

## Withdrawal batch fee law, step 2, round 3 -- 2026-08-18

Reviewed: the new law against the corpus's own edge-case tests rather than
against its specimen. The first two rounds looked at evidence and at tooling.
This one asked which of the assertions the other nine laws face were never
extended to the tenth.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | medium | `test/Corpus.t.sol` | `test_a_queue_law_over_a_target_with_no_queue_reverts` walked a hardcoded `Law[2]` of the two queue laws that existed when it was written. The new law is a third and was not in it, so nothing asserted that it reverts rather than returning a verdict against a target with no queue. The test's own comment names the failure it exists to prevent: a law returning true there reports that a system with no queue keeps its queue in order. | Fixed in this round: the array is a `Law[3]` and the new law is asserted with the other two. |
| S2-R3-02 | medium | `test/Corpus.t.sol` | The new law sums unchecked and reports the overflow as a violation, and no test could reach that branch. `test_a_sum_that_overflows_is_reported_as_a_violation` uses `Extreme`, which implements no queue, so a queue law reverts on the read long before its own addition is asked to hold the answer. The branch that exists precisely so the law does not fall silent where the numbers are worst was itself unexercised, which is the corpus's own argument about untested properties turned on one of its laws. | Fixed in this round: `ExtremeQueue` reports two claims each owed everything there is, and `test_a_queue_law_reports_its_own_overflow` asserts the law returns rather than reverts, returns violated, and gives the overflow as its reason. |

**What ran.** 76 Solidity tests under forge 1.7.1, up from 75 by the assertion
added here. 109 Python tests, the repository's 20, `pandects check` over ten laws.
No engine re-run: both findings are test coverage over an unchanged law, and
neither alters a contract the engines drive.

**Why the second one is worth a fixture.** The overflow branch is not decoration.
In 0.8 the addition reverts, a revert under `fail_on_revert = false` carries no
verdict, and the law would go quiet exactly where a system's numbers had gone
furthest wrong. The corpus argues that about every other summing law and tests it
for two of them. Asserting the detail string as well as the verdict is what makes
the test evidence that this branch ran rather than evidence that some branch
returned false.

Leads not pursued: `Extreme` and `ExtremeQueue` are two fixtures where the
difference is one interface, and a single parameterised fixture would serve both.
Left alone deliberately: the split is what makes the two tests say different
things, and merging them would put a flag in a fixture whose whole job is to be
obvious. The three carried from earlier rounds and from step 1 stand.

## Withdrawal batch fee law, step 2, round 4 -- 2026-08-18

Reviewed: what an integrator gets rather than what the corpus proves about
itself. Earlier rounds read the evidence, the tooling and the edge cases. This one
followed the law outwards, into the files somebody else's protocol actually
inherits.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R4-01 | high | `adapters/CorpusBase.sol` | The adapter an integrator inherits names its laws one by one in Solidity and had nine of the ten. So the corpus documented ten laws, `pandects check` counted ten, and anybody pointing `CorpusObserver` at their own market ran nine, with no signal anywhere: the adapter compiles, `queueHolds` returns a verdict, `explainOneState` returns five reasons, and every test passes. The one law missing was the one this whole run exists to add. Called high because it is exactly what the corpus is built to refuse, a law that is never asked reported as a corpus that holds, reaching the surface an outsider inherits rather than a specimen written to be broken. | Fixed in this round: the adapter carries it, `queueHolds` judges it, `explainOneState` returns six reasons and says why its width is the catalogue's count, and `test/Adapters.t.sol` reads six. |
| S2-R4-02 | medium | `tests/test_documents.py` | Nothing tied the adapter to the catalogue, which is why S2-R4-01 could happen quietly and would happen again on the eleventh law. The plugin already has this check twice over, for the rendered catalogue and for the integration notes, and the one surface where the omission reaches a third party had none. | Fixed in this round: `ShippedAdapterTests` holds every catalogued law to the adapter, with path independence excluded as an exact pinned set rather than a skip list, so a second exclusion has to be argued for in the file. Made to fail by removing the law from the adapter before being kept. |

**What ran.** 76 Solidity tests under forge 1.7.1, 111 Python tests, up from 109
by the two checks added here, the repository's 20, and `pandects check` over ten
laws. The adapter change is a contract change, so Slither 0.11.6 ran again over 50
contracts with no new result, and Echidna 2.3.3 ran again against `SoundCampaign`:
eight properties passing, seed 20260816. The campaign harness does not reach the
new law, which is step 3, so that number is still evidence about eight laws.

**Why this one is the important finding of the step.** The corpus's argument is
that a passing campaign proves nothing without a specimen, because a law that
cannot fail is invisible in a green result. A law absent from the shipped adapter
is worse than one that cannot fail: it is one nobody asks, on the surface furthest
from anybody who would notice. `specimens/FeeFromQueued.sol`,
`test_pooled_claims_cover_open_batches_counterexample`, the catalogue entry and
`invariant_pooled_claims_cover_open_batches` were all correct while
`CorpusObserver`, the contract an integrator points at their own market, ran nine
laws.

**Carried into step 3 with a mechanism rather than a hope.**
`src/campaigns/Specimens.sol` has the same shape and the same hazard and is still
unchecked. The check cannot land here: until the harness carries the law it would
fail, and a check added after the change it was meant to force is a check written
to pass. The runbook's step 3 now requires `ShippedAdapterTests` to be extended to
the campaign harness in the same commit that adds the property.

Leads not pursued: the merged-fixture question from round 3, `pandects run`
knowing one engine, and the two carried from step 1.

## Withdrawal batch fee law, step 2, round 5 -- 2026-08-18

Reviewed: round 4's own fix, on the suspicion that gating one file and calling the
class closed was too quick. It was.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R5-01 | high | `adapters/foundry/CorpusInvariants.sol` | The same defect as S2-R4-01, one file along and untouched by its fix. `CorpusBase` carries the law objects; this file decides which of them a Foundry run asserts, and it declared eight invariants for nine laws. After round 4 the adapter carried the tenth law and no Foundry invariant asked it, so an integrator extending `CorpusOneStateTest` still ran nine. Carrying a law and never asserting it is the same silence as not carrying it. | Fixed in this round: `invariant_pooled_claims_cover_open_batches` added, standing down with the other queue laws when `hasWithdrawalQueue` is false, and the two comments that counted the queue laws as two now say three. |
| S2-R5-02 | medium | `tests/test_documents.py` | Round 4's check read one path and asserted the law's component name appeared in it. That is why it did not see S2-R5-01: the component name did appear, in the file that binds it, and the check had no opinion about the file that asserts it. A check aimed at one of two surfaces is not a check on the class. | Fixed in this round: the check takes a list of shipped adapters. It maps the variable names `CorpusBase` binds components to, classifies each law's shape by reading whether its component extends `Law` or `PairLaw` rather than from a hand-kept list, and asserts every one-state law's variable is asserted in the Foundry adapter. Made to fail by deleting the invariant while leaving the law bound, which is the exact shape S2-R5-01 had. |

**What ran.** 76 Solidity tests under forge 1.7.1 and 111 Python tests, up from
109 in round 4 by one net: round 4's second check was replaced rather than added
to, because the version it shipped counted braces and carried a dead local. The
repository's 20 and `pandects check` over ten laws.

**On round 4's second check.** It passed, it was green, and it could not have
caught what round 5 found. It also contained a statement with no effect and a
subtest that asserted a string appeared somewhere in a file. Recorded plainly
because the step's own findings are about tests that cannot fail, and writing one
in the round that argues against them is worth writing down rather than quietly
replacing.

**The class, now that it has been walked properly.** Six shipped surfaces name
laws: the catalogue, the rendered document, the integration notes, `CorpusBase`,
`CorpusInvariants` and the campaign harness. Five are now held to the catalogue by
a test. The sixth is the campaign harness, still step 3's, still scheduled in the
runbook with the reason it cannot be gated earlier.

Leads not pursued: the merged-fixture question from round 3, `pandects run`
knowing one engine, and the two carried from step 1.

## Withdrawal batch fee law, step 2, round 6 -- 2026-08-18

Reviewed: the rest of the class rounds 4 and 5 opened. Two rounds had each found
the same defect in one more file, so this round enumerated every shipped file that
names laws before looking at any of them.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R6-01 | high | `adapters/echidna/CorpusEchidna.sol`, `adapters/medusa/CorpusMedusa.sol` | The third and fourth occurrence, in the two adapters an integrator extends to run the corpus under a fuzzer. Each declared five one-state properties and the tenth law was not among them, so anyone pointing Echidna or Medusa at their own system through the shipped adapter searched nine laws. The runbook had scheduled both files into step 3. Rounds 4 and 5 are the argument against that: a law missing from a surface an outsider inherits is a defect in the step that adds the law, and scheduling is how it survived twice. | Fixed in this round: both adapters carry the property, standing down with the other queue laws when `hasWithdrawalQueue` is false. |
| S2-R6-02 | medium | `tests/test_documents.py` | Round 5's check took a list of two paths, which was the right shape aimed at the wrong set. It knew about `CorpusBase` and the Foundry adapter and had no opinion about the two engine adapters, so it could not have caught S2-R6-01 either. Three rounds running, the check was narrower than the class. | Fixed in this round: the binding file and the asking files are separated, and the asking set is all three adapters that decide which bound law a run asks. Each was made to fail on its own by deleting one property at a time, which caught a fourth thing: the probe used for the Foundry file in the first attempt matched nothing, so a clean result there was the probe failing rather than the check passing. The exact-string version failed as it should. |

**What ran.** 76 Solidity tests under forge 1.7.1, 111 Python tests, the
repository's 20, `pandects check` over ten laws, Slither 0.11.6 over 50 contracts
at 23 results with nothing new, and Echidna 2.3.3 against four campaigns with the
shipped configuration and seed 20260816.

**The evidence this round bought.** Every campaign that extends the shipped
adapters picked the new law up as a consequence of S2-R6-01's fix, so the engines
reached it in step 2 rather than step 3:

| campaign | the new law | its own expected failure | calls |
| --- | --- | --- | --- |
| `SoundCampaign` | not carried | none | 20,140 |
| `ObservedQueueJumpedEchidna` | passing | `queue_order_preserved` | 20,205 |
| `DrivenClaimHaircutEchidna` | passing | `recorded_claim_never_shrinks` | 20,176 |
| `WildcatMarketCampaign` | passing | `recorded_claim_never_shrinks` | 20,123 |

The last row is the one worth reading twice. Echidna searched 20,123 calls against
the corrected Wildcat model and did not reach a state where pooled claims sit below
what the open batches are owed. Before the correction, five calls written by hand
got there and took four fifths of a departing lender's money on the way. Each
campaign still fails exactly the property it was built to fail and no other, so the
new law did not arrive broad.

`SoundCampaign` extends `Campaign` in `src/campaigns/Specimens.sol` rather than the
shipped adapter, which is why it is the one campaign the new law does not reach.
That harness is step 3's remaining content and the last surface without a check.

Leads not pursued: the merged-fixture question from round 3, `pandects run`
knowing one engine, and the two carried from step 1.

## Withdrawal batch fee law, step 2, round 7 -- 2026-08-18

Reviewed: every file in the plugin that names laws, enumerated mechanically
before any of them was opened, because three rounds running had found the same
defect one file further along and inspection had picked the files in the wrong
order each time. Ten Solidity files import two or more laws and three documents
name three or more. One of the ten had not been looked at.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R7-01 | medium | `test/Wildcat.t.sol` | Step 2 added a row to the integration's applicability table saying the model holds the new law once corrected, with figures, and added no assertion behind it. `test_the_model_holds_every_one_state_law_it_claims` asserted five laws and the document claimed six. That document's own idiom is the opposite: it says of two other claims that they are watched happening rather than described, and the check requiring every catalogued law to appear in it exists because a claim nobody tests is the thing this plugin refuses. The claim was mine and it shipped bare. | Fixed in this round: the law joins the law-by-law assertion, and `test_a_delinquent_market_can_take_no_fee_from_a_queued_batch` drives the market into the state the notes describe and asserts the figures they quote -- 200 held, a batch owed 1000 unpaid, and a fee of nothing where the earmark cap permitted 800. Reverting the model's cap to `reserved()` makes it fail with "a fee was taken out of a queued batch". |

**What ran.** 77 Solidity tests under forge 1.7.1, up from 76 by the assertion
added here, 111 Python tests, the repository's 20, and `pandects check` over ten
laws. No engine or Slither re-run: the only contract touched is a test.

**The enumeration, and what it settles.** Every shipped surface that names laws is
now either held to the catalogue by a test or scheduled with the reason it cannot
be. `adapters/CorpusBase.sol` binds them and is gated; the Foundry, Echidna and
Medusa adapters decide which are asked and are gated; `docs/catalogue.md` is
generated and drift-checked; `integrations/wildcat/APPLICABILITY.md` is gated for
mention and, after this round, asserted for the claim it makes; `test/Corpus.t.sol`
walks a diagonal of six; `test/SoundInvariant.t.sol` searches all six.
`src/campaigns/Specimens.sol` is the one surface left and it is step 3's, with its
check required in the same commit as its property. `docs/withdrawal-batch-fee-law/study.md`
names six law ids and is a record rather than a surface, which step 4 states.

Leads not pursued:

- **A gate on the applicability table itself.** Every law the table says holds
  could be required to appear in an assertion in `test/Wildcat.t.sol`. It would
  have caught S2-R7-01 the way the adapter gates caught rounds 4 to 6. It needs a
  parser for a prose table with three laws that legitimately do not hold and one
  that holds under a condition, and a fragile parser guarding a document is a
  worse trade than the check is worth. Recorded rather than built, and it is a
  candidate frontier.
- The merged-fixture question from round 3, `pandects run` knowing one engine, and
  the two carried from step 1.

## Withdrawal batch fee law, step 2, round 8 -- 2026-08-18

Reviewed: the comments this step's own rounds wrote, on the principle that a round
which has spent six findings on untested claims should read its own. One of them
promised a guarantee that did not exist.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R8-01 | medium | `adapters/CorpusBase.sol` | Round 4 widened `explainOneState` to six and wrote above it that the width is the count of one-state laws in the catalogue and that `test/Adapters.t.sol` holds it to that count. The second half was false. That test reads `string[6]` because the adapter returns `string[6]`; the two are one number written twice and a test taking it from the file it checks would be wrong the same way. So an eleventh one-state law would leave the width at six and nothing would say so, which is the argument the renderer's own drift test makes, and the comment claiming otherwise was written in the round that found the same defect elsewhere. | Fixed in this round: `test_the_explanation_is_as_wide_as_the_one_state_laws` reads the signature out of the source, counts the one-state laws in the catalogue by the shape their components declare, asserts the two agree, and asserts each of those laws is the subject of one of the assignments. Narrowing the width and hollowing the last entry each make it fail for their own reason. The comment now names the test that exists. |

**What ran.** 77 Solidity tests under forge 1.7.1, 112 Python tests, up from 111
by the check added here, the repository's 20, `pandects check` over ten laws, and
Slither 0.11.6 over 50 contracts at 23 results, unchanged. No engine re-run: this
round touched one comment and one test.

**Accepted, and why.** This is the eighth round, which is the configured ceiling,
so the tree has a fix in it that no later round has audited. That is the honest
shape of the close rather than a clean sweep: round 8 found one defect, fixed it,
and proved the fix fails when it should, and no ninth round exists to read the
proof back. The four leads below are accepted for the reasons given, none of them
because the rounds ran out.

- **A gate on the applicability table**, from round 7. It would catch the class
  S2-R7-01 belongs to, and it needs a parser for a prose table carrying three laws
  that do not hold and one that holds conditionally. A fragile parser guarding a
  document is a worse trade than the check is worth. A candidate frontier.
- **`pandects run` knows one engine**, from round 1. The shipped record carries the
  Foundry campaign, and the Echidna and Medusa results are written into the
  rounds above as prose rather than emitted as records.
  That is the arrangement the runbook fixes for step 3, and widening the runner is
  its own piece of work.
- **`Extreme` and `ExtremeQueue` differ by one interface**, from round 3. Merging
  them would put a flag inside a fixture whose job is to be obvious.
- Two more come from step 1 and stand unchanged. Whether the model corrections
  should have shipped as their own step, which the runbook argues against because
  no green intermediate state exists between them and the law. And the seven
  property families the original delivery deferred.

**The one surface still without a check.** `src/campaigns/Specimens.sol`, and it is
step 3's first line of work with the check required in the same commit as the
property. Recorded here as well as in the runbook, because it is the only thing
this step knowingly leaves for the next one.

## Withdrawal batch fee law, step 3, round 1 -- 2026-08-18

Reviewed: the whole of the step's diff, and first of all the check it added, since
step 2 spent six findings on checks narrower than the class they were written for.
It was narrower than the class it was written for.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | `tests/test_documents.py` | The campaign-harness check skipped every pair law. It classified each law by shape and returned early on anything that was not one-state, so the three pair properties the harness declares through `judgePair` were held to nothing, and a fourth pair law would arrive in the catalogue and not in the harness with a green suite either way. The check was written in the commit that closed this class for the one-state family and left the other half open. | Fixed in this round: pair-law bindings are read alongside the one-state ones and the property pattern accepts `judge` or `judgePair`, so both families are held under both prefixes. Deleting `echidna_recorded_claim_never_shrinks` now names that law. |
| S3-R1-02 | medium | `tests/test_documents.py` | Nothing tied a catalogued specimen to a campaign. Every one has a campaign today, and `FeeFromQueuedCampaign` exists because this step added it by hand, so the eleventh specimen would have rested on somebody remembering. A specimen with a property to fail and no harness to fail it under is caught by the deterministic suite and by no search, and a campaign report says nothing about which specimens were in it. | Fixed in this round: every catalogued specimen must have a `<Specimen>Campaign` in the harness. Renaming `FeeFromQueuedCampaign` now names the law whose specimen went undriven. |

**What ran.** 77 Solidity tests under forge 1.7.1, 114 Python tests, up from 113 by
the specimen check, the repository's 20, and `pandects check` over ten laws. No
engine re-run for the findings themselves: both are tests over an unchanged harness,
and the engine evidence this step exists for was taken in the implement phase and is
recorded below.

**The engines, on the harness this step built.** Both reach the specimen and neither
reaches anything else.

| engine | `pooled_claims_cover_open_batches` | the other eight | detail |
| --- | --- | --- | --- |
| Echidna 2.3.3, seed 20260816 | falsified, shrunk to four calls | passing | `deposit`, `borrow(1)`, `reserve`, `accrueFee(1)` |
| Medusa 1.5.1, twenty thousand | failed | passing | "pooled claims are below what the open batches are owed" |

**A defect in the check, caught by the check.** The first version of the pair-law
pattern read `judgePair?`, which is `judgePai` followed by an optional `r` rather
than `judge` followed by an optional `Pair`. It matched the pair laws and missed
every one-state law, so twelve subtests failed at once and named the laws they could
not find. Worth recording because the failure was loud: a pattern that matches
nothing leaves `asked` empty and every law unfound, rather than passing quietly,
which is the behaviour a check guarding against silence should have.

Leads not pursued: the four accepted at the close of step 2 stand, and none of them
is touched by this step.
