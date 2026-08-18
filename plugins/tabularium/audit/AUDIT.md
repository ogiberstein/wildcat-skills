# Tabularium audit log

<!-- marketplace-context:start -->
> **Record status.** This is a historical audit record; findings and dispositions below are preserved as evidence. Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

The Solidity security suite is waived for this run because Tabularium is a
Python data and agent-skill prototype with no Solidity contracts. Each step
still receives a review against the study's risk register and the exact branch
diff.

## Step 1, round 1 -- 2026-08-16

Scope: `main...45213e3f95e3f69a0f5dab02a656e4fa64ead45a`. Reviewed the
plugin and marketplace metadata, runtime contract, portable entrypoint,
canonical skill, CLI placeholder, design records and tests. The command has no
network or write path; every non-help invocation exits non-zero without
producing or verifying a release. JSON manifests parse, Python sources compile,
`git diff --check` reports no errors, the 10 root tests pass and the 6
Tabularium tests pass.

No findings.

Leads not pursued: none.

## Euler releases, step 1, round 1 -- 2026-08-17

Scope: `27e930f...83b3b58`. Reviewed source-to-event mapping, capture and
coverage binding, numeric bounds, selector uniqueness, offline rebuilds,
tamper refusals and the separation between the Euler V2 protocol generation
and Euler V3 source API. Rebuilt both Euler releases and re-ran 14 root and 117
Tabularium tests.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E1-R1-01 | medium | `scripts/tabularium_lib/adapters/euler_v2.py` | An oversized decimal block field could escape the controlled validation path through Python's integer-string conversion limit. | fixed in `83b3b58f1419c04e2450da2df3cfd1ecdb8530dc` |
| E1-R1-02 | medium | `scripts/tabularium_lib/adapters/euler_v2.py` | Distinct source IDs could name the same transaction and log index, allowing duplicate canonical event identities. | fixed in `83b3b58f1419c04e2450da2df3cfd1ecdb8530dc` |
| E1-R1-03 | medium | `scripts/tabularium_lib/release_v2.py` | A rebound capture could claim a timestamp different from the preserved Euler V3 response metadata. | fixed in `83b3b58f1419c04e2450da2df3cfd1ecdb8530dc` |

The fixes bound decimal block fields before conversion, reject repeated
transaction/log identities, and require the capture timestamp to equal the
preserved response timestamp. The two Euler release rebuilds remain
byte-identical to the checked-in artifacts.

Leads not pursued: none.

## Euler releases, step 1, round 2 -- 2026-08-17

Scope: `27e930f...ea8bcea`, including the round 1 fixes. Re-read both
capture contracts against the preserved response bytes, repeated the offline
rebuilds and tamper cases, compiled the Python sources, and ran 14 root and 118
Tabularium tests.

FINDING
[Medium] E1-R2-01: The exact-request descriptor omitted request ID `1`.
Location: `examples/euler-v1-v0/capture.json`, `scripts/tabularium_lib/release_v2.py`
Mechanism: The preserved JSON-RPC response carried the ID but the capture did not.
Impact: The purported exact request was incomplete.
Fix: fixed in `ea8bcead3a2e2dcad6f652485ed0aac41c2c98fe`.
END

The fix binds request ID `1`, rotates only the new Euler v1 capture and
coverage digests, and adds a rebound-tamper test. The source and canonical
event bytes did not change. No earlier Tabularium release byte changed.

Leads not pursued: none.

## Euler releases, step 1, round 3 -- 2026-08-17

Scope: `27e930f...2feeb85`, including both earlier audit rounds. Re-read
multi-row consistency and empty-result behaviour, then repeated the release
rebuilds, source tampering, Python compilation, 14 root tests and 121
Tabularium tests.

FINDING
[Medium] E1-R3-01: Empty responses accepted reversed coverage.
Location: `scripts/tabularium_lib/adapters/euler_v2.py`
Mechanism: A reversed indexed block interval could still claim complete coverage.
Impact: An invalid empty boundary could verify.
Fix: fixed in `2feeb85de056bef62a55d975a8fe98022daa5a8a`.
END

FINDING
[Medium] E1-R3-02: Shared block or transaction identities could conflict.
Location: `scripts/tabularium_lib/adapters/euler_v1.py`, `scripts/tabularium_lib/adapters/euler_v2.py`
Mechanism: Rows could disagree on hash, block number, transaction index or timestamp.
Impact: One identity could produce contradictory canonical metadata.
Fix: fixed in `2feeb85de056bef62a55d975a8fe98022daa5a8a`.
END

The fixes reject reversed coverage and reconcile shared block and transaction
metadata before ordering or serialising events. Both release rebuilds remain
byte-identical, and all prior Goldfinch artifacts remain unchanged.

Leads not pursued: none.

## Euler releases, step 1, round 4 -- 2026-08-17

Scope: `27e930f...e1e3fb7`, including all prior fixes. Compared the V2
amount mapping with the checked-in API response and Probitas' independently
validated event shapes, then ran 14 root and 123 Tabularium tests and rebuilt
both releases.

FINDING
[Medium] E1-R4-01: Arbitrary amount-leg names inherited canonical meaning.
Location: `scripts/tabularium_lib/adapters/euler_v2.py`
Mechanism: A liquidation could pass with one borrow-shaped `assets` leg.
Impact: An API shape change could acquire an old mapping.
Fix: fixed in `e1e3fb71fb779aa2dc5d4295c69c66943a2f570c`.
END

The fix requires exactly one `assets` leg for non-liquidation events and both
`assets` and addressed `collateral` legs for liquidations. Regression tests
cover an unknown leg and an incomplete liquidation.

Leads not pursued: none.

## Euler releases, step 1, round 5 -- 2026-08-17

Scope: `27e930f...2d7dc28`, including all four finding rounds. Re-read the
adapter, release and verifier paths against the study risk register and the
preserved source shapes. Exercised malformed numbers, duplicate and
contradictory identities, incomplete amount legs, request and timestamp
rebinding, unknown event types, path and artifact tampering, offline read-only
verification and deterministic order.

The 14 root and 123 Tabularium tests passed. Each Euler release rebuilt twice
to its committed bytes. The four Goldfinch artifacts retained their fixed
digests.

No findings.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-16

Scope:
`issue-74-scaffold-tabularium...ca4d8e85f916dce351b6c5364d4c60dd987750f0`.
Reviewed canonical serialisation, numeric bounds, Goldfinch source validation,
mapping semantics, output ordering, source preservation, the event and
coverage schemas, CLI failure behaviour and all tests. Reproduced the 511-row
build twice at SHA-256
`751754a2f913691cf95f3e9f859b156f9ccd7963b1d72d4fc3379348924469b1`.

FINDING
[Medium] S2-R1-01: A post-check symlink could replace preserved source.
Location: `scripts/tabularium_lib/core.py`, `scripts/tabularium_lib/builder.py`
Mechanism: The builder checked aliasing, then `Path.write_bytes` followed a symlink introduced before the write.
Impact: Output could overwrite source despite the alias gate.
Fix: fixed in `f6131579cba199cea111f1e65de6d6e28c64b244` with atomic replacement.
END

The fix writes to a same-directory temporary file, flushes and fsyncs it, then
uses atomic replacement. A regression test inserts a source-pointing symlink
after the alias check and proves the source stays unchanged while the symlink
itself is replaced.

Leads not pursued: none.

## Step 2, round 2 -- 2026-08-16

Scope: `issue-74-scaffold-tabularium...0ccc4db8c8c1f4f4e06cd6ca79fb0eaa9858f16f`,
including the round 1 fix. Re-read the mapper and serialisation paths against
the event schema and study risk register. Exercised the same-path, symlink,
hardlink and post-check symlink cases; compiled the Python sources; parsed the
schemas; rebuilt the full snapshot twice; and re-ran 10 root and 42 Tabularium
tests. Both outputs have SHA-256
`751754a2f913691cf95f3e9f859b156f9ccd7963b1d72d4fc3379348924469b1`.
The raw capture remains
`644b706804b6e28d69b1028b87937e0e36c882f703419d0e2bf568b056892bc9`.

No findings.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-16

Scope:
`issue-77-event-model-goldfinch--audit...508f0426d5b21e1e44c0e8ad81a2be37477c239e`.
Reviewed release construction, manifest binding, path confinement, source and
capture preservation, canonical reconstruction, unsupported-version refusal,
tamper cases, offline operation and read-only verification. Rebuilt the real
511-row release in separate directories and obtained identical canonical and
coverage bytes. The canonical SHA-256 remains
`751754a2f913691cf95f3e9f859b156f9ccd7963b1d72d4fc3379348924469b1`.

FINDING
[Low] S3-R1-01: Malformed JSON could escape the controlled error path.
Location: `scripts/tabularium_lib/core.py`
Mechanism: An extremely long integer or recursive encoder failure raised `ValueError` or `RecursionError`, not `TabulariumError`.
Impact: Malformed input exposed an uncontrolled CLI traceback.
Fix: fixed in `dbcaf19c443493606a1eef807fc7982cd9607cb7`.
END

The fix keeps parser and encoder failures on the controlled error path and
uses an iterative numeric-validation walk for deeply nested values. Regression
tests cover an overlong integer, deep nesting and an encoder recursion error.

Leads not pursued: none.

## Step 3, round 2 -- 2026-08-16

Scope:
`issue-77-event-model-goldfinch--audit...02267b631a8063c5c1bba922f9c48d6157ffef19`,
including the round 1 fix. Re-ran both test suites, compiled the Python sources,
parsed the schemas, compared separate real builds, verified a read-only release
offline and exercised source and canonical tampering. The 511-row canonical and
coverage SHA-256 values remained
`751754a2f913691cf95f3e9f859b156f9ccd7963b1d72d4fc3379348924469b1` and
`58184a75d8eca6ae8d9b44653c36ce8c482549c5d3cecd1a2a991b0936561f6d`.

FINDING
[Low] S3-R2-01: NUL-bearing artefact paths escaped verification failure.
Location: `scripts/tabularium_lib/paths.py`
Mechanism: `Path.resolve` raised an uncontrolled `ValueError`.
Impact: A malformed manifest path produced a traceback.
Fix: fixed in `307fa255a354b220aa5ab725de5a9c0e392f1e32`.
END

FINDING
[Low] S3-R2-02: A FIFO coverage manifest could block verification.
Location: `scripts/tabularium_lib/verifier.py`
Mechanism: Verification opened the entry manifest before checking it was regular.
Impact: The read could block indefinitely.
Fix: fixed in `307fa255a354b220aa5ab725de5a9c0e392f1e32`.
END

The fix rejects NUL-bearing artefact paths and refuses non-regular entry
manifests before opening them. Regression tests cover both cases.

Leads not pursued: none.

## Step 3, round 3 -- 2026-08-16

Scope:
`issue-77-event-model-goldfinch--audit...9393ff7e4a351958cad980b2eda20669d2d69fe0`,
including both earlier rounds of fixes. Re-read the release and verifier paths,
ran 10 root and 77 Tabularium tests, compiled the Python sources and exercised
NUL paths, FIFOs, directories, symlinks, hardlink aliases, malformed JSON,
duplicate keys, non-finite numbers and rebound tampering. Verification stayed
offline and left a read-only release unchanged. Separate real builds remained
byte-identical, with canonical SHA-256
`751754a2f913691cf95f3e9f859b156f9ccd7963b1d72d4fc3379348924469b1` and
coverage SHA-256
`58184a75d8eca6ae8d9b44653c36ce8c482549c5d3cecd1a2a991b0936561f6d`.

No findings.

Leads not pursued: none.

## Step 4, round 1 -- 2026-08-16

Scope:
`issue-82-coverage-offline-verifier--audit...dbbc02c867f7227cfb5728ba577e36bd6dc5a537`.
Reviewed the checked-in release bytes, coverage, counts, source preservation,
offline and read-only verification, temporary rebuild demonstration, public
status changes, data dictionary, adapter guide, supersession policy and tests.
Reproduced all four release hashes and 511 unique rows, then exercised rebound
capture and canonical tampering, path escapes, symlinks and demo mismatches.

FINDING
[Medium] S4-R1-01: Capture validation left two source fields unbound.
Location: `scripts/tabularium_lib/release.py`
Mechanism: It reconciled block number, not indexed timestamp or deployment identifier.
Impact: A rebound coverage digest could verify a contradictory capture.
Fix: fixed in `87cb45b2cc32728eaf4aafcdc23c26df1f7a4c9f`.
END

The fix binds both capture fields to `source._meta` and adds regression tests
for timestamp and deployment drift. The root, Ariadne, Probitas and Tabularium
suites passed 10, 310, 422 and 90 tests after the fix, and the real temporary
rebuild still matched the committed release.

Leads not pursued: none.

## Step 4, round 2 -- 2026-08-16

Scope:
`issue-82-coverage-offline-verifier--audit...ed38efcbf6fb6b6b33c9d6dd2f46ee07d10d47a3`,
including the round 1 fix. Repeated the complete release and documentation
review and exercised missing, wrong-type and conflicting timestamp and
deployment values on both sides of the capture binding. Invalid builds failed
without a traceback or output. Rehashed tampering, traversal, symlinks and a
demo mismatch were refused. The source and capture stayed byte-identical to
staging, the 511-row release verified read-only and offline, and its hashes
remained unchanged.

The root, Ariadne, Probitas and Tabularium suites passed 10, 310, 422 and 90
tests. Probitas emitted one pre-existing unclosed-file `ResourceWarning` in
`test_abi.py`; it did not fail the suite and is outside this step's diff.

No findings.

Leads not pursued: none.
