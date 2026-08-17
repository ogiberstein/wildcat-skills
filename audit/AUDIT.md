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
