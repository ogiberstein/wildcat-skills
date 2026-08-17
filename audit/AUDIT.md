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
