# Rolling Fiat frontiers audit

## Step 1, round 1 -- 2026-08-17

The committed non-Solidity diff has no open finding. Status: clean.

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
| S1-R1-02 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | Rebound malformed RPC results exposed uncontrolled type errors; an error response could also carry a result, and a nested trace-filter frame was not tied to the selected transaction. | fixed in this round |
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

- S1-R2-01 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | Round 1's top-level type checks did not cover malformed struct-log elements, nested prestate maps or non-hexadecimal proxy runtime code, so some rebound evidence could still fail outside the controlled refusal path. | fixed in this round

The hardening review also checked the registry generator against the pinned
Comet Git objects with replacement refs disabled. Its bytes match the
committed registry. The focused hostile tests and both socket-denied rebuilds
pass after the nested evidence checks.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 3 -- 2026-08-17

- S1-R3-01 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | The capture bounded each response but not aggregate bytes, so a permitted 48-request run could exhaust disk well before a component crossed its individual ceiling. | fixed in this round
- S1-R3-02 | medium | `plugins/tabularium/scripts/tabularium_lib/compound_witness.py` | The principal fact pointed at the entire opcode list and only the poststate slot; it did not bind the prestate map that establishes an absent slot as zero or each exact principal-writing struct log. | fixed in this round

The aggregate capture cap is 128 MiB and fails before installation. The
principal fact now selects the prestate storage map, exact poststate slot and
each contributing struct log. The witness manifest also binds the fact byte
count. Focused tests and both offline rebuilds pass with the regenerated
unpublished witness bytes.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 4 -- 2026-08-17

The fixed non-Solidity tree has no open finding. Status: clean.

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

- S1-R1-01 | low | `plugins/hexaemeron/docs/fiat-installed-path-and-maturity-proof/proof.md` | The proof reported 14 non-blocking Imprimatur signals, but the reproducible per-file total is 15. | Fixed on the stacked audit branch before round 2.

Leads not pursued: publisher authentication, cache signing, native Windows
support, and general release attestation are outside this frontier and are
not claimed by the proof.

## Fiat installed-path proof, step 1, round 2 -- 2026-08-17

The corrected non-Solidity tree has no open finding. Status: clean.

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

- S1-R1-01 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/evaluate_labelled_corpus.py` | The evaluator parsed the published schemas but did not apply them to fixture rows, and it did not verify the annotation-seal or candidate-freeze digests before scoring. A changed row or schema could therefore be evaluated under the same published evidence claims. | Fixed in this round: the standard-library evaluator now enforces the schema subset, checks both digest manifests, and rejects identical annotator ids; mutation regressions cover row and schema changes.

The focused evaluator has 15 passing checks after the fix. The 55 Imprimatur
tests, 61 Hexaemeron tests and 14 repository tests also pass. Replaying
`final.json` still produces the same metrics and gate decisions.

Leads not pursued: model authorship beyond the declared provenance rule,
population-prevalence claims and tuning against the spent v1 holdout are
outside this frontier and are explicitly disclaimed by the fixture.

## Imprimatur labelled prose, step 1, round 2 -- 2026-08-18

The fixed non-Solidity tree has no open finding. Status: clean.

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

- S1-R1-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/study.md` | The study asserted that all nine laws hold in the violating state, but only the five single-state laws had been executed. The four pair laws were reasoned about from what a fee does not touch. In a corpus whose whole argument is that a passing campaign proves nothing without a specimen, an argued verdict presented beside measured ones is the same defect one level up. | Fixed in this round: all four pair laws executed against the pair on both models, and the study now reports what was run. `accrual/path-independent/v1` returns held and the study says that verdict carries no weight, because the law compares two runs rather than one system's before and after.
- S1-R1-02 | low | `plugins/pandects/docs/withdrawal-batch-fee-law/study.md` | The study named a fee leak in `integrations/wildcat/WildcatMarketModel.sol` with figures, and never fixed the boundary to the deployed market contracts. The plugin's own applicability document warns that nothing in the model should be mistaken for them; a reader meeting the figures first could take the study as a claim about the protocol. | Fixed in this round: the study states that the finding is about the reduced model and the corpus's silence, and that it establishes nothing either way about the deployed contracts.

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

- S1-R2-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | The runbook sized step 2's test work as the diagonal growing "from 9x9 to 10x10 over the single-state half". No such table exists. `test/Corpus.t.sol` runs its diagonal over the single-state laws alone, where `COUNT` is 5, and `test/Pairs.t.sol` runs over 3, with path independence handled separately. Nine and ten are corpus totals. Whoever implemented step 2 from the runbook would have gone looking for a table with the wrong shape. | Fixed in this round: the runbook names both dimensions and says that ten is a total rather than a dimension.

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

- S1-R3-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 2 listed `docs/catalogue.md` as a file to write and step 4 listed it again as prose to reconcile. It is neither: `python3 scripts/pandects.py render` generates it and `tests/test_documents.py` checks it against the renderer. A hand-edit either fails that check, or passes it by reproducing what the renderer would have produced and thereby hides a real drift. An earlier round of the original delivery, S5-R2-01, fixed the renderer for exactly this reason. | Fixed in this round: step 2 regenerates it and says why, and step 4 drops it from the prose surfaces and names the command.
- S1-R3-02 | low | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 4's reconciliation list left this run's own study and runbook out without saying so, and both of them claim Pandects ships nine laws. The omission reads as an oversight rather than a decision, so an implementer would either rewrite a spec into disagreement with the run it specifies, or leave a claim stale with nothing recording which was meant. | Fixed in this round: step 4 states that the two spec documents are records on the same footing as the audit log's historical rounds and are not reconciled, and why rewriting them would be worse.

The round-2 fix was re-read against the sources. `COUNT` is 5 in
`test/Corpus.t.sol` and 3 in `test/Pairs.t.sol`, which is what the runbook now
says.

Leads not pursued: the two carried from round 1, unchanged.

## Withdrawal batch fee law, step 1, round 4 -- 2026-08-18

No Solidity and no campaign. This round read step 3's evidence requirement
against the tooling that exists to satisfy it, and re-checked which documents in
the plugin are generated, which the previous round had only established for one of
them.

- S1-R4-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 3 asked for "a search record for each run" and for "a run record beside the existing campaign evidence", without naming a mechanism. One exists and does not cover the case: `python3 scripts/pandects.py run` writes a search record and knows only the `foundry` engine. An implementer would either read the requirement as satisfied by that command for all three engines, which would silently drop the two fuzzers the step exists to run, or invent a record format for them. | Fixed in this round: step 3 names the command for the Foundry record, says it has no Echidna or Medusa support, and requires the two fuzzers to be recorded as audit prose the way the original delivery recorded them. It also says not to extend the runner here.

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

The fixed non-Solidity tree has no open finding. Status: clean.

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

- S2-R2-01 | medium | `.gitignore` | Round 1's commit tracked three engine artefacts: `crytic-export/combined_solc.json`, `.medusa-artifact-hash` and `slither_results.json`. The ignore rules for all three existed and did not match, because they were written as `plugins/*/` and an engine writes beside wherever it was invoked from. The Medusa run went through a config under `adapters/medusa/`, so the artefacts landed two levels below the plugin root and walked straight past a one-level pattern. This is the lead the original delivery carried from its own step 5 round 2 about `slither_results.json` being tracked, arriving again by the same mechanism. | Fixed in this round: the three files are untracked, the patterns are depth-independent, and a fresh Medusa run confirmed all three are ignored where they are actually written rather than where the old patterns expected them.
- S2-R2-02 | low | `.gitignore` | `plugins/*/search-record.json` sat in the fuzzing-output section while the file it names is tracked, shipped as evidence, and as of round 1 held to the catalogue by three tests. The two statements cannot both be right. Left alone, a fresh clone that regenerated the record would show no diff, and deleting it would draw no complaint from git. | Fixed in this round: the entry is removed and the reason it is not output is written where the entry used to be.

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

- S2-R3-01 | medium | `test/Corpus.t.sol` | `test_a_queue_law_over_a_target_with_no_queue_reverts` walked a hardcoded `Law[2]` of the two queue laws that existed when it was written. The new law is a third and was not in it, so nothing asserted that it reverts rather than returning a verdict against a target with no queue. The test's own comment names the failure it exists to prevent: a law returning true there reports that a system with no queue keeps its queue in order. | Fixed in this round: the array is a `Law[3]` and the new law is asserted with the other two.
- S2-R3-02 | medium | `test/Corpus.t.sol` | The new law sums unchecked and reports the overflow as a violation, and no test could reach that branch. `test_a_sum_that_overflows_is_reported_as_a_violation` uses `Extreme`, which implements no queue, so a queue law reverts on the read long before its own addition is asked to hold the answer. The branch that exists precisely so the law does not fall silent where the numbers are worst was itself unexercised, which is the corpus's own argument about untested properties turned on one of its laws. | Fixed in this round: `ExtremeQueue` reports two claims each owed everything there is, and `test_a_queue_law_reports_its_own_overflow` asserts the law returns rather than reverts, returns violated, and gives the overflow as its reason.

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

- S2-R4-01 | high | `adapters/CorpusBase.sol` | The adapter an integrator inherits names its laws one by one in Solidity and had nine of the ten. So the corpus documented ten laws, `pandects check` counted ten, and anybody pointing `CorpusObserver` at their own market ran nine, with no signal anywhere: the adapter compiles, `queueHolds` returns a verdict, `explainOneState` returns five reasons, and every test passes. The one law missing was the one this whole run exists to add. Called high because it is exactly what the corpus is built to refuse, a law that is never asked reported as a corpus that holds, reaching the surface an outsider inherits rather than a specimen written to be broken. | Fixed in this round: the adapter carries it, `queueHolds` judges it, `explainOneState` returns six reasons and says why its width is the catalogue's count, and `test/Adapters.t.sol` reads six.
- S2-R4-02 | medium | `tests/test_documents.py` | Nothing tied the adapter to the catalogue, which is why S2-R4-01 could happen quietly and would happen again on the eleventh law. The plugin already has this check twice over, for the rendered catalogue and for the integration notes, and the one surface where the omission reaches a third party had none. | Fixed in this round: `ShippedAdapterTests` holds every catalogued law to the adapter, with path independence excluded as an exact pinned set rather than a skip list, so a second exclusion has to be argued for in the file. Made to fail by removing the law from the adapter before being kept.

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

- S2-R5-01 | high | `adapters/foundry/CorpusInvariants.sol` | The same defect as S2-R4-01, one file along and untouched by its fix. `CorpusBase` carries the law objects; this file decides which of them a Foundry run asserts, and it declared eight invariants for nine laws. After round 4 the adapter carried the tenth law and no Foundry invariant asked it, so an integrator extending `CorpusOneStateTest` still ran nine. Carrying a law and never asserting it is the same silence as not carrying it. | Fixed in this round: `invariant_pooled_claims_cover_open_batches` added, standing down with the other queue laws when `hasWithdrawalQueue` is false, and the two comments that counted the queue laws as two now say three.
- S2-R5-02 | medium | `tests/test_documents.py` | Round 4's check read one path and asserted the law's component name appeared in it. That is why it did not see S2-R5-01: the component name did appear, in the file that binds it, and the check had no opinion about the file that asserts it. A check aimed at one of two surfaces is not a check on the class. | Fixed in this round: the check takes a list of shipped adapters. It maps the variable names `CorpusBase` binds components to, classifies each law's shape by reading whether its component extends `Law` or `PairLaw` rather than from a hand-kept list, and asserts every one-state law's variable is asserted in the Foundry adapter. Made to fail by deleting the invariant while leaving the law bound, which is the exact shape S2-R5-01 had.

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

- S2-R6-01 | high | `adapters/echidna/CorpusEchidna.sol`, `adapters/medusa/CorpusMedusa.sol` | The third and fourth occurrence, in the two adapters an integrator extends to run the corpus under a fuzzer. Each declared five one-state properties and the tenth law was not among them, so anyone pointing Echidna or Medusa at their own system through the shipped adapter searched nine laws. The runbook had scheduled both files into step 3. Rounds 4 and 5 are the argument against that: a law missing from a surface an outsider inherits is a defect in the step that adds the law, and scheduling is how it survived twice. | Fixed in this round: both adapters carry the property, standing down with the other queue laws when `hasWithdrawalQueue` is false.
- S2-R6-02 | medium | `tests/test_documents.py` | Round 5's check took a list of two paths, which was the right shape aimed at the wrong set. It knew about `CorpusBase` and the Foundry adapter and had no opinion about the two engine adapters, so it could not have caught S2-R6-01 either. Three rounds running, the check was narrower than the class. | Fixed in this round: the binding file and the asking files are separated, and the asking set is all three adapters that decide which bound law a run asks. Each was made to fail on its own by deleting one property at a time, which caught a fourth thing: the probe used for the Foundry file in the first attempt matched nothing, so a clean result there was the probe failing rather than the check passing. The exact-string version failed as it should.

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

- S2-R7-01 | medium | `test/Wildcat.t.sol` | Step 2 added a row to the integration's applicability table saying the model holds the new law once corrected, with figures, and added no assertion behind it. `test_the_model_holds_every_one_state_law_it_claims` asserted five laws and the document claimed six. That document's own idiom is the opposite: it says of two other claims that they are watched happening rather than described, and the check requiring every catalogued law to appear in it exists because a claim nobody tests is the thing this plugin refuses. The claim was mine and it shipped bare. | Fixed in this round: the law joins the law-by-law assertion, and `test_a_delinquent_market_can_take_no_fee_from_a_queued_batch` drives the market into the state the notes describe and asserts the figures they quote -- 200 held, a batch owed 1000 unpaid, and a fee of nothing where the earmark cap permitted 800. Reverting the model's cap to `reserved()` makes it fail with "a fee was taken out of a queued batch".

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
  could be required in an assertion in `test/Wildcat.t.sol`.
  It would
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

- S2-R8-01 | medium | `adapters/CorpusBase.sol` | Round 4 widened `explainOneState` to six and wrote above it that the width is the count of one-state laws in the catalogue and that `test/Adapters.t.sol` holds it to that count. The second half was false. That test reads `string[6]` because the adapter returns `string[6]`; the two are one number written twice and a test taking it from the file it checks would be wrong the same way. So an eleventh one-state law would leave the width at six and nothing would say so, which is the argument the renderer's own drift test makes, and the comment claiming otherwise was written in the round that found the same defect elsewhere. | Fixed in this round: `test_the_explanation_is_as_wide_as_the_one_state_laws` reads the signature out of the source, counts the one-state laws in the catalogue by the shape their components declare, asserts the two agree, and asserts each of those laws is the subject of one of the assignments. Narrowing the width and hollowing the last entry each make it fail for their own reason. The comment now names the test that exists.

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

- S3-R1-01 | medium | `tests/test_documents.py` | The campaign-harness check skipped every pair law. It classified each law by shape and returned early on anything that was not one-state, so the three pair properties the harness declares through `judgePair` were held to nothing, and a fourth pair law would arrive in the catalogue and not in the harness with a green suite either way. The check was written in the commit that closed this class for the one-state family and left the other half open. | Fixed in this round: pair-law bindings are read alongside the one-state ones and the property pattern accepts `judge` or `judgePair`, so both families are held under both prefixes. Deleting `echidna_recorded_claim_never_shrinks` now names that law.
- S3-R1-02 | medium | `tests/test_documents.py` | Nothing tied a catalogued specimen to a campaign. Every one has a campaign today, and `FeeFromQueuedCampaign` exists because this step added it by hand, so the eleventh specimen would have rested on somebody remembering. A specimen with a property to fail and no harness to fail it under is caught by the deterministic suite and by no search, and a campaign report says nothing about which specimens were in it. | Fixed in this round: every catalogued specimen must have a `<Specimen>Campaign` in the harness. Renaming `FeeFromQueuedCampaign` now names the law whose specimen went undriven.

**What ran.** 77 Solidity tests under forge 1.7.1, 114 Python tests, up from 113 by
the specimen check, the repository's 20, and `pandects check` over ten laws. No
engine re-run for the findings themselves: both are tests over an unchanged harness,
and the engine evidence this step exists for was taken in the implement phase and is
recorded below.

**The engines, on the harness this step built.** Both reach the specimen and neither
reaches anything else.

- engine: Echidna 2.3.3, seed 20260816; `pooled_claims_cover_open_batches`: falsified, shrunk to four calls; the other eight: passing; detail: `deposit`, `borrow(1)`, `reserve`, `accrueFee(1)`
- engine: Medusa 1.5.1, twenty thousand; `pooled_claims_cover_open_batches`: failed; the other eight: passing; detail: "pooled claims are below what the open batches are owed"

**A defect in the check, caught by the check.** The first version of the pair-law
pattern read `judgePair?`, which is `judgePai` followed by an optional `r` rather
than `judge` followed by an optional `Pair`. It matched the pair laws and missed
every one-state law, so twelve subtests failed at once and named the laws they could
not find. Worth recording because the failure was loud: a pattern that matches
nothing leaves `asked` empty and every law unfound, rather than passing quietly,
which is the behaviour a check guarding against silence should have.

Leads not pursued: the four accepted at the close of step 2 stand, and none of them
is touched by this step.

## Withdrawal batch fee law, step 3, round 2 -- 2026-08-18

Reviewed: the tree with round 1 applied, then the harness's own reporting path,
which no round had opened. The properties were right and the thing that tells you
why one failed was not.

- S3-R2-01 | medium | `src/campaigns/Specimens.sol` | `explain` returned eight reasons for the nine laws the harness now carries, and the missing one was the new law's. That function exists so a reader replaying a falsified sequence gets the law's own words with the numbers in them rather than reconstructing them from a call trace, and for the one law this run added it returned nothing. Both engines had already falsified that property, so the failure was reachable and its reason was not. This is the same defect as `explainOneState` in step 2, which is the third place in the plugin where a law count is written twice. | Fixed in this round: `explain` returns nine, the new law's reason sits with the one-state group, and the three pair-law positions moved by one. `test_the_campaign_explanation_is_as_wide_as_the_laws_it_carries` holds the width and the contents to the catalogue; narrowing it back and hollowing the entry each fail for their own reason.
- S3-R2-02 | low | `src/campaigns/Specimens.sol` | The comment on `FeeFromQueuedCampaign` said reaching the property needs three things and listed a deposit, a borrow and a fee. It needs four. The withdrawal request is the one it left out and the one that matters: with no recorded claim nothing is owed, and with a claim no larger than what is held the earmark covers it and the cap does not leak. Echidna's own shrink is four calls. | Fixed in this round: the comment names four, says which one the earlier draft dropped and why the property cannot be reached without it.

**What the index shift caught on the way.** `test/Explain.t.sol` read positions as
numerals, so inserting a one-state law in the middle of that group moved every
pair-law index by one and the compiler only objected to the width. A test asserting
`details[6]` carried a pair law's reason would have gone on passing against a
different law's reason had the widths happened to agree. The positions are named
constants now, with the reason written where they are declared.

**What ran.** 78 Solidity tests under forge 1.7.1, up from 77 by the reason
assertion for the new law, 115 Python tests, up from 114 by the width check, the
repository's 20, and `pandects check` over ten laws. No engine re-run: `explain` is
not a property and no property changed.

Leads not pursued: the four accepted at the close of step 2. None is touched here.

## Withdrawal batch fee law, step 3, round 3 -- 2026-08-18

Reviewed: the harness header, which is the last thing in this step's files stating a
number nothing checked, and the two claims that number rests on.

- S3-R3-01 | low | `src/campaigns/Specimens.sol` | The header reads "Nine of these eleven are expected to fail one property". Both numbers are written by hand, both move when a specimen is added, and this run has already found four counts written twice with nothing holding them. The figures were right; nothing said they would stay right. | Fixed in this round: a test counts the campaigns the file declares and the ones whose specimen breaks a law the harness asks, spells both out, and requires the header to match. Reverting the header to the pre-step counts names the two it should have read.

**The two exceptions, verified rather than reasoned.** The claim is that nine of
eleven campaigns fail a property, so two do not, and the two are worth an engine run
each because they are the exceptions the count depends on.

- campaign: `SoundCampaign`; result: nine properties passing; calls: 20,140
- campaign: `CompoundsPerStepCampaign`; result: nine properties passing; calls: 20,140

`CompoundsPerStepCampaign` is the interesting one. Its specimen compounds, which
breaks `accrual/path-independent/v1`, and no campaign can search that law because a
campaign drives one system along one route. So it holds everything a campaign can
ask, and the new property is among the nine it holds, which is independence evidence
for the new law from a specimen built to break something else.

**Round 2's own prose.** It shipped "load-bearing" in the audit entry and in the
comment that entry described, which imprimatur bans as a structural metaphor. The
lint ran after that commit rather than before it. Fixed in `364a7ac`, and recorded
here rather than left in a commit message, because the same mistake in a shipped
document is what step 2's rounds spent findings on.

**What ran.** 78 Solidity tests under forge 1.7.1, 116 Python tests, up from 115 by
the count gate, the repository's 20, `pandects check` over ten laws, and Echidna
2.3.3 against `CompoundsPerStepCampaign` with the shipped configuration and seed
20260816.

Leads not pursued: the four accepted at the close of step 2, none touched here.

## Withdrawal batch fee law, step 3, round 4 -- 2026-08-18

Reviewed: the step against its own exit conditions, then the diagonal against the
engines rather than against hand-derived states. Two conditions the runbook set for
this step had not been met.

- S3-R4-01 | medium | `test/Adapters.t.sol` | The step's exit asks for the new entry point to be exercised without an engine, the way `test_the_echidna_entry_points_answer` already does for an older law, and nothing called either of the new prefixed wrappers. They are two separate functions delegating to the same internal judgement, so one can be wired to the wrong law while the other is right, and only a campaign under that one engine would notice: the deterministic suite would pass and the other engine would agree with it. | Fixed in this round: `test_both_prefixes_answer_for_the_new_law` calls both before and after the four-call sequence, and asserts two unrelated laws stay held. Rewiring `property_pooled_claims_cover_open_batches` to a different law fails it by name.
- S3-R4-02 | low | `audit/AUDIT.md` | The step's exit asks that a Medusa record state the seed as unavailable rather than invent one. Round 1 recorded the Medusa run with its engine, version and call limit and said nothing about a seed at all, which is the absence this plugin's own discipline is about: silence reads as a run whose seed nobody wrote down rather than a run that has none to write. | Fixed in this round: recorded below, and the earlier table stands with this note against it.

**Medusa exposes no seed.** Medusa 1.5.1 takes no seed argument and reports none, so
the runs in rounds 1 to 4 carry the engine, its version, the configuration digest,
the call limit of twenty thousand and the corpus digest, and no seed. Echidna's runs
all carry seed 20260816 from `adapters/echidna/echidna.yaml`. A Medusa campaign here
is reproducible to the configuration and not to the sequence.

**The diagonal, under search.** The deterministic diagonal asserts each specimen
breaks its own law at one state. This is the same claim put to an engine, every
campaign in the harness, each at roughly twenty thousand calls with seed 20260816.

| campaign | the law it fails | the new law |
| --- | --- | --- |
| `SoundCampaign` | none | passing |
| `MintedClaimsCampaign` | `value_conserved` | passing |
| `OverReservedCampaign` | `reserves_backed` | passing |
| `OverPromisedCampaign` | `held_partitioned` | passing |
| `DebtForgivenCampaign` | `debt_falls_only_against_payment` | passing |
| `AccruesAtRestCampaign` | `no_accrual_at_rest` | passing |
| `CompoundsPerStepCampaign` | none searchable | passing |
| `ClaimHaircutCampaign` | `recorded_claim_never_shrinks` | passing |
| `QueueJumpedCampaign` | `queue_order_preserved` | passing |
| `PayableBeyondReservesCampaign` | `reserves_cover_payable` | passing |
| `FeeFromQueuedCampaign` | **the new law** | falsified, four calls |

Every campaign fails exactly one property and it is the one its specimen was built to
break. The new law fires on one specimen out of eleven and on none of the other ten
under search, which is the study's second risk answered by an engine rather than by
the argument the step opened with. Three adapter-based campaigns were run earlier in
step 2 and agree: `ObservedQueueJumpedEchidna`, `DrivenClaimHaircutEchidna` and
`WildcatMarketCampaign` each hold the new law and fail only their own.

**What ran.** 79 Solidity tests under forge 1.7.1, up from 78 by the entry-point
assertion, 116 Python tests, the repository's 20, `pandects check` over ten laws, and
Echidna 2.3.3 against eight campaigns in this round.

Leads not pursued: the four accepted at the close of step 2, none touched here.

## Withdrawal batch fee law, step 3, round 5 -- 2026-08-18

Reviewed: what these rounds have said about the suite, rather than the tree. Both
findings are about this log rather than the code, and both are the kind the honesty
rule at the top of Fiat's audit loop exists for.

- S3-R5-01 | medium | `audit/AUDIT.md` | Round 2 changed a function in `src/campaigns/Specimens.sol`, which is a contract, and recorded "No engine re-run: `explain` is not a property and no property changed." That was true of the engines and said nothing about Slither, which had not run against this step's contracts at all. Rounds 3 and 4 carried the same omission forward. A round that changes Solidity and reports the suite without one of its members has reported a suite that did not run. | Fixed in this round: Slither 0.11.6 run against the step's tree. 52 contracts, 23 results across the same three benign classes the original delivery documented, and nothing naming the new campaign or the new law. The rounds above stand with this note against them.
- S3-R5-02 | medium | `audit/AUDIT.md` | The `security_suite` receipt names `hexaemeron:x-ray`, `hexaemeron:solidity-auditor` and `hexaemeron:fizz`, and no round in either step has said what became of the third. Silence about a named member of the suite is the failure this log is supposed to make impossible, and it is worse here than a waiver would have been, because a reader counting three names against the rounds would assume all three ran. | Fixed in this round: stated below, plainly, with what was done instead and why.

**Fizz, and why the generator did not run.** `fizz` generates a stateful Solidity
fuzz suite under `test/fizz/` with its runtime metadata beside it. This plugin
already has that suite: `src/campaigns/Specimens.sol` is a hand-written harness with
one campaign per specimen and one property per law, and building or refreshing it is
the whole content of this step rather than something a round does to it. It sits
under `src/` on purpose, and the file says why: crytic-compile skips `test/` when it
builds a Foundry project, so a harness generated into `test/fizz/` is a harness
neither engine can see.

So the function `fizz` performs was performed, by hand, as the step's deliverable,
and the generator was not run because running it would produce a second harness in
the one directory this plugin documents as unreachable. That is a judgement, not a
waiver, and it is recorded here rather than left as an absence. `x-ray` and
`solidity-auditor` are the reading passes and the rounds above are what they
produced.

**What ran.** 79 Solidity tests under forge 1.7.1, 116 Python tests, the
repository's 20, `pandects check` over ten laws, and Slither 0.11.6 over 52
contracts. No engine re-run in this round: nothing in it touches a contract.

Leads not pursued: the four accepted at the close of step 2, none touched here.

## Withdrawal batch fee law, step 3, round 6 -- 2026-08-18

Reviewed: the fixed tree, and each check the five earlier rounds added, by breaking
the thing it guards and confirming it says so.

The fixed tree has no open finding. Status: clean.

**The checks, re-proved rather than re-read.** Removing a pair-law property fails the
prefix check. Renaming a specimen's campaign fails two checks at once, the
specimen-has-a-campaign one and the header count, which is the right answer and shows
they are independent. Narrowing `explain` back to eight fails the width check.
Changing "Nine of these eleven" to ten fails the header check. All four then pass
again with the file restored.

**What ran.** 79 Solidity tests across ten suites under forge 1.7.1 and solc 0.8.28,
116 catalogue, checker, search-record and document tests on Python 3.14, the
repository's 20, `pandects check` over ten laws, Slither 0.11.6 over 52 contracts at
23 results, and Echidna 2.3.3 over every campaign in the harness at roughly twenty
thousand calls each with seed 20260816.

**One asymmetry, stated rather than left to be noticed.** Echidna drove all eleven
campaigns. Medusa drove two: `SoundCampaign`, which holds everything, and
`FeeFromQueuedCampaign`, which is the specimen this step exists for. The step's exit
asks that both engines drive the new specimen and both do. The other nine campaigns
have Echidna's verdict and not Medusa's, and no claim here rests on Medusa having
searched them.

Leads not pursued: the four accepted at the close of step 2, none of them touched by
this step, and the Medusa coverage asymmetry above, which is a stated limit rather
than a defect.

## Withdrawal batch fee law, step 4, round 1 -- 2026-08-18

Reviewed: every document the step touched, the ledger against the versioning
contract, and the branch the step was built on. This step ships prose and a ledger
entry, so `x-ray`, `solidity-auditor` and `fizz` had no Solidity to read and none of
them ran. Saying so rather than recording a zero, for the reason step 3 round 5 gave.

- S4-R1-01 | medium | `plugins/pandects/audit/AUDIT.md` | The plugin's own audit log records this run's whole subject as a lead not pursued, closing with "No law covers it. It is a real gap and a new law rather than a fix to this one." A law covers it now, and nothing in that log said so. Its historical rounds stay as written, which is right, but that left a reader of the plugin's own record meeting an open gap that had been closed in another file. The same log also carries the `slither_results.json` lead, which this run closed in step 2 round 2. | Fixed in this round: a "Leads closed since" section says what became of both, names the law, the specimen, the reduced counterexample and where the run is recorded, and states which leads remain untouched. No historical round was edited.
- S4-R1-02 | medium | this log | The step was branched from a stale `origin/loop/2026-08-18-kronos`, taken before step 3's pull request merged, so the tree it was verified against did not contain step 3. The demo path caught it: `forge test` reported 77 where step 3 had closed at 79. Merging would not have reverted step 3, because the merge base was below it, but every number in the step's receipt would have described a tree that was never going to ship. | Fixed before the step was committed: the branch was reset to the current tip and the twelve-file change reapplied, which it did cleanly because step 3 and step 4 share no file. Re-verified after replanting: 79 Solidity tests, ten laws, no catalogue drift. Recorded here rather than left in the reflog, because the receipt would have carried the wrong evidence and only a count nobody was checking on purpose revealed it.

**The ledger, against the contract.** `pandects-v0.1.0` becomes `pandects-v1.1.0`:
the evolution counter moves once for a completed frontier job, generation and epoch
are retained, and `SKILL.md` frontmatter matches the ledger. The frontier revision
moves from `withdrawal-batch-fee-law` to `search-record-engine-coverage`, which an
evolution entry is allowed to do and a generation entry is not. The recorded SHA-256
was recomputed from the four ledger fields as written, including the trailing
newline, and matches the digest in the history row.

**The new frontier, and why it is not mature.** The contract asks whether another
pass has a concrete evidenced chance of material improvement. It does, and the
evidence is this run's own log: rounds in steps 2 and 3 recorded Echidna and Medusa
results as prose because `pandects run` emits one engine, `foundry`, and nothing
else. A corpus whose argument is that a campaign result means nothing without its
search record can machine-record one of the three engines it uses. That is a gap
this run demonstrated rather than one chosen from a list.

**What was reconciled.** Twelve documents carried the old frontier sentence and all
twelve carry the new one. Five prose law counts said nine and say ten. Two others say
nine and are right: one counts the laws other than this one, and one is about a
lexicon. `docs/catalogue.md` was regenerated rather than edited and produced no
diff, because it already counted ten from the catalogue.

**What ran.** The repository's 20 tests including the marketplace prose gate, 116
plugin tests, 79 Solidity tests under forge 1.7.1, `pandects laws` printing ten with
their applicability, `pandects check` over ten laws, and `pandects render` with no
drift.

Leads not pursued: the four accepted at the close of step 2, and the Medusa coverage
asymmetry stated in step 3 round 6.

## Withdrawal batch fee law, step 4, round 2 -- 2026-08-18

Reviewed: the tree with round 1 applied, then every count and claim in browsing prose
that the run had touched or should have. One it had not touched.

- S4-R2-01 | medium | `README.md` | The repository README says how many of the corpus's laws carry no tolerance, and it still said eight. Nine of the ten are exact; only `accrual/path-independent/v1` carries a bound. Step 4 had corrected the same claim in the plugin's own README and missed this one, so the two documents disagreed with each other and one of them disagreed with the catalogue. | Fixed in this round: nine, taken from the catalogue's `bounds` field rather than counted by eye.
- S4-R2-02 | medium | `tests/test_marketplace_prose.py` | Nothing held either README's corpus counts to the catalogue. The rendered document derives both of its counts, the adapters are held to theirs by the plugin's suite, and these two were hand-written sentences that a frontier run adding a law simply has to remember. This run corrected five of them and missed the sixth, which is the whole argument. | Fixed in this round: `test_pandects_prose_counts_the_laws_the_catalogue_holds` derives the total, the exact count and the family count from the catalogue and requires both documents to state them. Each of the three anchored claims was made to fail on its own before the test was kept.

**The mirror, checked and clean.** `.agents/skills/pandects/SKILL.md` was compared with
the canonical skill in case the version bump had left them disagreeing. It is a
deliberately different document, a short routing entrypoint with its own description
and no frontmatter version, and no other plugin's mirror carries a version either. The
frontier sentence is the part they share and the prose gate already holds it.

**The ledger, machine-checked rather than read.** `tests/test_evolution_contract.py`
holds every governed ledger to the versioning contract, and it passes on this entry:
the frontmatter version matches the ledger, the recorded SHA-256 matches the digest of
the current status line, and the axis rules allow an evolution entry to move the
frontier revision where a generation entry may not. The reading in round 1 was right
and this is the part of it that did not depend on my reading.

**What ran.** The repository's 21 tests, up from 20 by the count gate, 116 plugin
tests, 79 Solidity tests under forge 1.7.1, and the demo path: ten laws printed, ten
laws with every part present, no catalogue drift. No Solidity in this step, so the
Pashov pair and `fizz` had nothing to read and did not run.

Leads not pursued: the four accepted at the close of step 2, and the Medusa coverage
asymmetry from step 3 round 6.

## Withdrawal batch fee law, step 4, round 3 -- 2026-08-18

Reviewed: whether the frontier this step declares is visible where a reader would meet
it. The ledger names a gap in the search-record runner. Two documents describe that
runner and neither said the gap existed.

- S4-R3-01 | medium | `plugins/pandects/README.md` | "Saying how it was searched" opens with "A campaign result without its settings is an anecdote" and then hands the reader `pandects run`, without saying that the command emits the Foundry campaign and nothing else. A reader who has just run Echidna or Medusa, which this plugin ships adapters and a configuration for, would look for a record the tool cannot produce. The section names `foundry.toml` and so is not false; it is silent exactly where the corpus's own held frontier says the gap is. | Fixed in this round: the section says `run` knows one engine, that an engine which did not run is absent rather than empty, that a campaign under either fuzzer is not recorded by the command, and that widening it is the held frontier.
- S4-R3-02 | medium | `plugins/pandects/adapters/medusa/README.md` | The adapter document says "A Medusa record therefore carries the engine, the configuration, the sequence length and the corpus digest", which describes such records as things this plugin produces. Nothing produces them. It is the document somebody reads to learn how to run Medusa here, so it is the worst place for that to be implied. | Fixed in this round: the record is described as written by hand, with `pandects run` named as emitting Foundry and no other engine, and the widening named as the frontier.

**Why these count as reconciliation rather than new work.** The held job asks for a
cold read of mutable first-party marketplace prose, and the step had read it for law
counts and the frontier sentence. It had not read it against the frontier it was
about to declare. A ledger that names a gap while the two documents describing that
tool imply it is filled is a record disagreeing with itself, which is the same defect
class as a count written twice.

**What ran.** The repository's 21 tests, 116 plugin tests, 79 Solidity tests under
forge 1.7.1, and the demo path: ten laws printed, ten laws with every part present, no
catalogue drift. No Solidity in the diff, so the Pashov pair and `fizz` had nothing to
read and did not run.

Leads not pursued: the four accepted at the close of step 2, and the Medusa coverage
asymmetry from step 3 round 6.

## Withdrawal batch fee law, step 4, round 4 -- 2026-08-18

Reviewed: the fixed tree, the gates the earlier rounds added, and one last read for
anything still describing the closed frontier as open.

The fixed tree has no open finding. Status: clean.

**Nothing still calls the gap open.** No document or contract outside the audit logs
and this run's own spec describes a fee reducing pooled claims below what open batches
are owed as uncovered. `src/laws/ReservesCoverPayableClaims.sol` still says no law
covers a claim paid beyond what it was owed, which remains true and is a different
defect. `docs/applicability.md` names two laws as examples of qualified applicability,
and both readings still hold.

**The frontier agrees everywhere.** The new sentence appears once per surface across
all twelve documents that carry a marketplace-context block, and matches the row in the
repository README's selection table. The other nine plugins' frontiers are untouched.

**The gates, re-proved.** Setting the repository README's exact count back to eight
fails the count gate. Desyncing the ledger label from the frontmatter fails two
evolution-contract checks at once, which is the right answer: the label and the digest
are separate claims.

**What ran.** The repository's 21 tests, 116 plugin tests, 79 Solidity tests across ten
suites under forge 1.7.1 and solc 0.8.28, and the demo path from the study's problem
statement: `pandects laws` printing ten with their applicability, `pandects check` over
ten laws with every part present, and `pandects render` producing no drift. No Solidity
in this step at any round, so `x-ray`, `solidity-auditor` and `fizz` had nothing to read
and none of them ran; the reading passes are these four rounds.

Leads not pursued: the four accepted at the close of step 2, unchanged and none of them
touched by this step, and the Medusa coverage asymmetry stated in step 3 round 6.

## Repository-wide Brevitas pass, step 1, round 1 -- 2026-08-18

- Low: A historical finding changed during the structural audit-log rewrite.
- Location: `audit/AUDIT.md:20` at entry ref `a7d001009e7e2a7e63343e206ef10ecabc2cab42`.
- Mechanism: `could raise uncontrolled type errors` became `permitted uncontrolled type errors`.
- Impact: the rewrite altered the recorded failure mechanism without new audit evidence.
- Fix: used `exposed` for the first mechanism and retained the separate qualified error-response claim.

The manual round also checked both parser implementations, their compact-list fixtures,
the 159-file source inventory, 43 excluded files, 29 protected passages, four digest
refusals, and the committed study and runbook. No other open finding was established.
The Solidity security suite remains waived because the step changes Markdown and Python
test parsers only.

## Repository-wide Brevitas pass, step 1, round 2 -- 2026-08-18

The fixed non-Solidity tree has no open finding. Status: clean.

The round re-read the historical mechanism at `audit/AUDIT.md:20`, both compact-list
parsers, their fixtures, and the full protected-state proof. Root `22/22`, Hexaemeron
`62/62`, Imprimatur, Brevitas `--source`, protected SHA verification, and
`git diff --check` pass. No further lead was established.

## Repository-wide Brevitas pass, step 2, round 1 -- 2026-08-18

The Brevitas prose diff has no open finding. Status: clean.

The review compared five changed files with entry ref `a7d001009e7e2a7e63343e206ef10ecabc2cab42`, checked the compact history parser, and recomputed frontier digest `dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62`. It also verified the three refusal digests: `08e534ff9fd8005778e2224f374bd1e42a4bb129c2504e8aa54549f8621f0494`, `2cdd9bb04532ec278184d2a3290a0b0b72c02be47ca634911428440ddbed6d58`, and `ed8fbcf14186a1c79f9db8f971796d192969ec729edeb2bba0fc78f30ff75e48`.

Root `22/22`, Brevitas `13/13`, evals `3/3`, Agent Skills validation, Imprimatur, Brevitas `--source`, protected SHA verification, and `git diff --check` pass. The security suite remains waived because only Markdown changed.

## Step 1, round 1 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | step commit | Fiat-created commit carried one provenance trailer where push-discipline requires both | fixed by amend on the step branch |

Leads not pursued: none. The round ran the waiver's lint battery -- phylax,
ephoros and hypomnema over the changed tree, all clean -- and reviewed the diff
against the study's risk register: no dangling pointer survives (the record
lint caught one at implement time, fixed before commit), the fiat prose pins
in `test_fiat_skill.py` still hold, both ledgers keep their axes, `hexctl.py`
is untouched, and the marketplace prose tests pass. Root 24/24, hexaemeron
124/124.

## Step 1, round 2 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The amended commit carries both provenance trailers, the lint
battery is clean over the fixed tree, and both suites pass.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The three lints exit clean over the changed tree; the diff
touches two references and one phase note, none of which a test pins; the new
lint commands resolve through `$PLUGIN_ROOT` exactly as the masks already do
in the same file; and both suites pass. Root 24/24, hexaemeron 124/124.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The lint battery is clean over the changed tree; the diff touches
two READMEs' prose, one manifest description and three version fields; the
short description four surfaces must agree on is untouched, and the marketplace
prose tests hold. Root 24/24, hexaemeron 124/124.

Leads not pursued: the root README's one-line Hexaemeron entry says nothing
about the phase skills. It also says nothing false, and the status table's
"Use it for" cell already names them, so no change.

## Step 4, round 1 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The lint battery is clean, the ledger axes hold under both
suites, the evolution row's digest matches the recomputed header, and the
cold read's one defect, a hand-off line predating the phase skills, was fixed
in the step commit. Root 24/24, hexaemeron 124/124.

Leads not pursued: none.

## Step 1, round 1 -- 2026-08-18

Run: Horos, the reading-boundary skill. Step 1 scaffolds and registers the
plugin. Suite waived (no Solidity); the round ran the three bundled lints and
a diff review against the study's risk register.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/horos/README.md | "What it ships" claimed the scanner, boundary and maps in the present tense while this step ships only the scaffold | fixed: section reframed as what the runbook lands, in order |
| S1-R1-02 | low | plugins/horos/docs/runbook.md | the committed runbook copy pointed at the gitignored .hexaemeron path as the spec | fixed: points at the committed study beside it |
| S1-R1-03 | low | README.md | the role matrix omits a Horos column, and a Developers score at or above five demands a worked example the landing README lacked | fixed: column added (Developers 8, Security 2, all other desks 1) and a Day-to-day example added |

Lints: phylax 0, ephoros 0, hypomnema 0 over plugins tests and the changed
documents. Leads not pursued: none.

## Step 1, round 2 -- 2026-08-18

The round re-ran against the tree with round 1's fixes applied. Lints: phylax
0, ephoros 0, hypomnema 0. Root 24/24, horos 4/4. The review of the fix diff
found nothing further.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); the round ran the three bundled lints, all clean,
then reviewed the classifier against the study's risk register.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/horos/skills/horos/scripts/horos.py | classify_file swallowed OSError and returned None, so an unreadable file was reported as readable instead of counted in files_skipped_unreadable, understating what the scan skipped | fixed: the function raises and the walker counts, with a chmod-0 regression test |
| S2-R1-02 | low | plugins/horos/skills/horos/scripts/horos.py | classify_file is public but did not itself refuse symlinks; only the walker guarded them, so a direct caller could make the scanner read outside root | fixed: the function refuses links as well |

Leads not pursued: a stat-then-open race (a file swapped for a symlink between
the check and the read) is accepted for the prototype; exploiting it requires
an attacker writing to the tree during the scan, at which point the tree is
already theirs.

## Step 2, round 2 -- 2026-08-18

Re-ran against the fixed tree. Lints: phylax 0, ephoros 0, hypomnema 0.
Horos 26/26, root 24/24. The fix diff review found nothing further: the one
public caller of classify_file already counts the raised OSError as skipped.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none beyond the accepted race recorded in
round 1.

## Step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Review focused on the
risk register's partial-write and determinism rows.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | plugins/horos/skills/horos/scripts/horos.py | the temporary boundary file used one fixed name, so two concurrent scans of the same tree could unlink each other's half-written temporary and fail one run's atomic replace | fixed: the temporary name carries the writing process id; the existing cleanup tests pin that no temporary survives either path |

Leads not pursued: a giant hand-crafted boundary.json can make check spend
memory parsing it; accepted for the prototype, the file is repository-local
and the parse failure path already exits 2.

## Step 3, round 2 -- 2026-08-18

Re-ran against the fixed tree. Lints: phylax 0, ephoros 0, hypomnema 0.
Horos 39/39, root 24/24. The fix diff is one line plus its comment; the
review found nothing further.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none beyond round 1's accepted parse-memory
lead.

## Step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
45/45, root 24/24. The review checked the map verb against the never rules:
it parses and never imports or executes the target, hostile nesting is capped
by the tokenizer's indentation limit and lands in the caught SyntaxError
path, and undecodable bytes are replaced before parsing.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: map reads the named file whole, unlike the
bounded scanner; that is the verb's purpose (one tool read instead of the
agent reading the file), and the file is user-named rather than
tree-discovered.

## Step 5, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
51/51, root 24/24, and the study's four repeatable success criteria pass as
written from the repository root. The review checked the shipped example
against the risk register: the fixture's committed boundary is reproduced
byte for byte by a fresh scan on every supported interpreter path (the
document is sorted-key JSON of ints and posix strings), the documented
mutation fails by name in both drift directions, relative links in the final
SKILL.md resolve, and the example's vendored and lockfile specimens are
inert data that no suite imports or executes.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Live-evidence run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two committed spec documents. Root 24/24, horos 51/51. The step adds prose
only; the review checked the committed copies match the receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Live-evidence run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
bundle. Horos 55/55, root 24/24. The review checked the risk register's
rows: the bundle names its commit and tool version, the consistency test
reads only the committed boundary and never re-scans or touches the network,
and the quoted totals are asserted rather than trusted. The one derived
number (80.3%) is recomputed by the test from the quoted operands.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Live-evidence run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
six changed surfaces. Root 24/24 (the evolution contract validates the
v1.1.0 row's script-computed digest and the prose contract validates surface
agreement and job uniqueness), horos 55/55. The review confirmed the refusal
is recorded in both the skill text and the ledger with its reason, and that
the in-place study corrections are named in the commit rather than silent.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Rule-classes run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two spec documents. Root 24/24, horos 55/55. Prose-only step; the committed
copies match the receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Rule-classes run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0 over plugins tests,
hypomnema 0 over the changed README. Horos 61/61, root 24/24. The review
checked the register's false-exclusion row: both rules are gated on name
plus content or name plus path, each carries two near-miss tests, and the
example's readable file stays readable. The SVG rule runs before the marker
scan by decision, recorded as a comment at the check itself.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: .svgz and other compressed asset variants
stay readable; they are binary when deflated on disk and out of the held
job's evidence either way.

## Rule-classes run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
new bundle. Horos 65/65, root 24/24. The review held the register's rows:
the first capture's files are untouched (git shows additions only), the
delta test proves the added entries are exactly the two families with
nothing removed, both bundles name the same commit, and the consistency
tests read only committed files.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Rule-classes run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0 over plugins tests,
imprimatur 100 on all four reconciled surfaces. Root 24/24 (the evolution
contract validates the v2.1.0 digest; the prose contract validates surface
agreement and job uniqueness), horos 65/65. The review confirmed the
supersession keeps the refusal's grounds in the record rather than erasing
them, and that both prior ledger rows are byte-identical to before.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Outline-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
67/67, root 24/24. The review checked the move: the Python extractor's
output is pinned by the untouched fixture test, the registry refuses
unregistered suffixes naming its supported list, and the refusal-message
test moved with the message as the runbook records.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Outline-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 79/79, root
24/24. The review walked the risk register's lexer rows: escapes consume
line continuations, character classes protect a slash inside a regex, the
newline guard bounds a wrong regex guess to one line, operator folding
keeps arrow and equality tokens whole, and every unterminated construct
confesses the remainder.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: inside a template expression the scanner
treats a slash literally, so a regex literal containing a brace or backtick
inside `${...}` can mis-span the template. Bounded to that template, and
deferred to the step 4 corpus run, which will show whether real code does
this before any fix is designed.

## Outline-extractor run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 89/89, root
24/24. Two defects were found and fixed during the step's own build, before
the implement receipt, and are recorded here for the trail: a statement
position that never advanced on a stray closing brace hung the first live
run (fixed with an explicit step-over plus a monotonic advance guard), and
method heads truncated at their parameter list because the statement-end
scanner was handed the closing parenthesis itself (fixed with
position-ordered member dispatch). The round's review after those fixes
walked the emitted fixture line by line against the source and found the
slices verbatim and the confession exact.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings in the round itself. Leads not pursued: multiline arrow-
function signatures quote only their first line; the differential in step 4
measures whether that loses names in practice.

## Outline-extractor run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
92/92, root 24/24. The review held the register's rows: the oracle tool is
committed but nothing in the runtime or test path imports or invokes it
(the consistency tests read only the committed results JSON); the bundle
names its commit, oracle version and altitudes; the acceptance numbers
(missed 0, extra 0, crashes 0) are asserted by test rather than quoted; and
the three corpus-found fixes each landed with the corpus rerun after them.
The step 2 lead (a regex with braces inside a template expression) did not
occur in 866 real files: no file crashed or misparsed on it, so it stays a
recorded limitation.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: the corpus is one repository's style
(prettier, semicolon-free); a semicolon-heavy or decorator-heavy corpus
would exercise different paths and can join the evidence when one matters.

## Outline-extractor run, step 5, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24 (the evolution contract validates
the v3.2.0 digest; the prose contract validates surface agreement and job
uniqueness), horos 92/92. The review confirmed the refusal's revision is
recorded as a revision, both prior ledger rows are byte-identical, and the
new held job is the maintainer's own words for the filetype census.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Census run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two spec documents. Root 24/24, horos 92/92. Prose-only step; the committed
copies match the receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Census run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
changed README. Horos 101/101, root 24/24. The review held the register's
rows: one walk produces both artefacts (the tally rides the existing loops
rather than a parallel implementation), the frozen boundary is reproduced
byte for byte by test, rows sum to the totals with the boundary column
bounded by its row, symlinks and skipped directories appear in neither
walk, and the census writer is the boundary's own atomic writer refactored,
not a copy.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: readable files are statted twice when the
census is on (once inside classify_file, once for the tally); measured
against Metron's rule it is noise on real trees and not worth plumbing size
out of the classifier.

## Census run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
104/104, root 24/24. One defect was caught by the bundle's own consistency
test before the implement receipt and is recorded for the trail: the prose
quoted the boundary walk's file count instead of the census's (which
includes files inside aggregated directories), 1,041 against the true
1,113. The review confirmed both documents carry the shipped schema, the
rows sum to the totals, and the Solidity call is recorded as a candidate
pending more censuses, in the maintainer's words.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings in the round itself. Leads not pursued: none.

## Census run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24 (evolution digest and prose
contracts), horos 104/104, demo census byte-identical. The review confirmed
the held job carries the maintainer's own restraint: breadth first, no
extractor from one tree, Solidity recorded as leading candidate rather than
commitment, and the three prior ledger rows byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Go-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
104/104, root 24/24. Prose-only step; one imprimatur defect (a bold-lead
bullet) was fixed before the copies were committed, and the committed
copies match the receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Go-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 116/116, root
24/24. The review walked the study's risk rows: raw strings keep
backslashes as plain bytes and span lines, runes holding quotes are pinned,
iota members emit without types, receivers ride inside function slices, and
the statement walker advances monotonically (the guard the TypeScript
extractor learned the hard way is present from the start).

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: an anonymous struct in a result type
(func f() struct{ x int } {) would mis-slice at the struct's brace; the
step 3 corpus over 1,421 real files will show whether the pattern occurs
before any fix is designed.

## Go-extractor run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
118/118, root 24/24. The review held the register's rows: the venv and
oracle stay outside every runtime and test path (the consistency tests read
only the committed results JSON), the bundle names its commit, oracle and
the compiler-absence trade, the acceptance numbers are asserted by test,
and the step 2 lead (an anonymous struct in a result type) did not occur in
1,421 real files. The three dev-side tooling defects the run surfaced are
named in the bundle; the shipped outliner needed no fix at all.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: the corpus is gofmt-regular by
construction; hand-mangled Go would exercise the confession paths harder,
and can join the evidence when such a tree matters.

## Go-extractor run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24, horos 118/118, demo pinned. The
review confirmed the evolution row's numbers equal the committed bundle's,
the C++ job carries the maturity expectation in the maintainer's words, and
all prior rows are byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Cpp-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
118/118, root 24/24. Prose-only step; one imprimatur defect (a structural
metaphor) was fixed before the copies were committed.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Cpp-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 132/132, root
24/24. Three defects were found and fixed during the step's own build,
before the implement receipt, recorded for the trail: a broken template
reattachment vestige replaced with the decorator pattern; a function body's
close consuming the following statement (refresh, fromQuery and formatApr
vanished from the fixture until the tail scan was cut back to the brace);
and Allman-style bodies orphaned from their heads until a one-line peek
joined them, with the orphan-brace branch defused from eating statements.
The round's review walked the fixture against the source and found the
slices verbatim, the raw-string containment exact and the confession
correct.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings in the round itself. Leads not pursued: preprocessor
conditionals that unbalance braces mis-slice until the next recogniser, as
the study prices; the step 3 corpus reports how often real code does it.

## Cpp-extractor run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity shipped; the corpus is the Solidity compiler's
C++); lints phylax 0, ephoros 0, hypomnema 0. Horos 136/136, root 24/24.
The review held the register's rows: the venv and oracle stay outside every
runtime and test path, the bundle declares its altitudes and exclusions
including the 170 oracle-unparsed files, the acceptance numbers are
asserted by test, and the five corpus-found outliner defects each landed
with the corpus rerun after them. The step 2 lead (preprocessor
conditionals unbalancing braces) produced zero confessed regions across 842
files of heavily conditionalised code.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: the oracle-unparsed fifth of the corpus
is compared for crash-freedom only; a stronger C++ oracle would widen the
compared set and can join the evidence if one becomes available without a
toolchain the ingested tree does not owe us.

## Cpp-extractor run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24 (the evolution contract validates
the mature row's digest; the prose contract validates surface agreement),
horos 136/136, demo pinned. The review confirmed the maturity closure meets
the study's stated condition (the differential closed clean at declared
altitudes), the reopening path is named on every surface, and all prior
ledger rows are byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity shipped); lints phylax 0, ephoros 0, hypomnema 0.
Horos 136/136, root 24/24. Prose-only step; the committed copies match the
receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (the run ships Python that reads Solidity, none of its own);
lints phylax 0, ephoros 0. Horos 149/149, root 24/24. The review walked the
study's risk rows: hex and unicode strings lex through the ordinary quote
scanner with prefixes staying in code harmlessly, attribute chains and
override lists ride in verbatim heads, the walker inherits the monotonic
advance and Allman peeks its three predecessors learned, and constructors
are outlined but excluded from the differential's compared set like C++
destructors.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 3, round 1 -- 2026-08-18

Suite waived (Python reading Solidity, none shipped); lints phylax 0,
ephoros 0, hypomnema 0. Horos 152/152, root 24/24. The review held the
register's rows: the venv and oracle stay outside every runtime and test
path, the bundle declares its altitudes and exclusions, the acceptance
numbers are asserted by test, and the one corpus defect (the multiline
inheritance swallow, exactly the silent-consumption class this loop exists
to catch) landed with a pinned regression and a structural fix rather than
a heuristic patch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 4, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, imprimatur 100 on all four
reconciled surfaces. Root 24/24, horos 152/152, demo pinned. The review
confirmed the evolution row's numbers equal the committed bundle's, the
held job quotes the maintainer's specification by its committed path, and
all prior rows are byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Refinement run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
152/152, root 24/24. Prose-only step; the committed copies match the
receipted artefacts and sit beside the maintainer's verbatim specification.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Refinement run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Root 24/24. One
finding, and it is a process finding against this run's own record: the
implement receipt recorded "horos 157/157" while the plugin suite was in
fact red with two test errors, because a chained shell command swallowed
the suite's exit status. The errors were wrong expectations in the two new
nested-attributes tests (asserting file-level entries where directory
aggregation correctly forecloses them), fixed in 1d33f7f with the semantics
documented in the tests themselves. The true counts: 155 tests before the
fix with 2 errors; 155/155 after. The receipt's count also overstated the
total by two. The correction stands here rather than in a rewritten
receipt, because the ledger is append-only and the round exists to catch
exactly this.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | .hexaemeron ledger | implement receipt asserted a green suite over a red one | corrected in 1d33f7f and recorded here |

Leads not pursued: none.

## Refinement run, step 2, round 2 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 155/155, root
24/24, against the fixed tree. The round re-walked the two corrected tests
against the scanner's actual semantics and the scope table's registration
order, and re-verified the frozen fixture boundary is byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Refinement run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
changed README. Horos 159/159, root 24/24, both verified before the
implement receipt this time. The review walked the specification against
the landed pipeline clause by clause: the hard list is exactly the
specification's five plus corroborated directories, geometry stays
candidate wherever found including the windows, the sample is
deterministic (first eight sorted, 4 KiB each), the byte budget holds (at
most 8 KiB for large unresolved files), candidates never bind and check
never fails on them, and the safety rule the specification preserves
(security reviews ignore the boundary) is untouched in the skill text.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: the specification's closing note names
nested .gitattributes and corroborated exclusions as the largest gains;
both landed, and the recapture evidence for real trees belongs to the
third job.

## Refinement run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0 (the git subprocess carries its
allow comment naming fixed argv, no shell, pinned cwd), ephoros 0. Horos
165/165, root 24/24, verified before the receipt. The review held the
register's rows: ignored files never enter any universe, the widened mode
still excludes them, aggregation counts only universe members, check
reproduces the committed universe, and the fixture's tracked label is safe
because running the suite presupposes a git clone.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Refinement run, step 5, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, imprimatur 100 on all four
reconciled surfaces. Root 24/24, horos 165/165, demo byte-identical, all
verified before the receipt. The review confirmed the discipline's new
grade and universe language matches the shipped behaviour exactly, and all
prior ledger rows are byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Marking run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
165/165, root 24/24, verified before the receipt. Prose-only step.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Marking run, step 2, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, hypomnema 0 over the changed
AGENTS.md. Root 24/24 with the stanza in place, horos 165/165, check from
the root clean, all verified before the receipt. The review read the
committed boundary's 14 hard entries and spot-checked them against the
tree: the fixture's own specimens, the shipped example artefacts and the
evidence JSONs classify exactly as the rules say, and no hand-written
plugin source appears in the hard set. The 35 candidates are advisory and
say so.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.
