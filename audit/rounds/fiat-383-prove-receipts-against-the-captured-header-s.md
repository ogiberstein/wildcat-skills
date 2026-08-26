## Step 1, round 1 -- 2026-08-26T04:05:53Z

Audit schema: fiat-audit-round/v2

Covered: receipt-set-completeness=reviewed; receipt-rlp-encoding=reviewed; typed-receipt-prefix=reviewed; header-root-binding=reviewed; transaction-index-binding=reviewed; log-query-completeness=reviewed; metadata-overclaim=reviewed; evidence-count-upgrade=not-applicable; legacy-format-compatibility=reviewed; provider-response-bounds=reviewed; atomic-capture=reviewed; release-binding=not-applicable; ariadne-schema-parity=not-applicable; marketplace-prose-drift=reviewed

Not checked: Solidity-only Pashov X-Ray, Solidity Auditor, and Fizz under the recorded non-Solidity waiver; Step 2 receipt-trie reconstruction, Step 3 network capture, Step 4 release and Ariadne propagation, Step 5 live fixture and publication; canonical-chain and provider-independence claims

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `plugins/lazarus/schemas/receipt-witness-v1.json:70`; `plugins/lazarus/scripts/lazarus_lib/schemas.py:330` | The witness calls RPC-returned transaction hashes header identities, but `receiptsRoot` commits no transaction hash and the format carries no evidence against the header's `transactionsRoot`. A reduced probe accepted both the original witness and a coherent rewrite with `consensus_projection_equal=True`, `receipts_root_equal=True`, and `target_hash_changed=True` at projection SHA-256 `9fa074210f311ce216f30d332a9fa87307298c2961f57de0b70024a279243273`; a later target-receipt proof would therefore promote recorded RPC metadata. | open pending a Protasis study and runbook amendment before Step 2; this round added no transaction-trie scope and did not narrow the receipted claim |
| S1-R1-02 | medium | `plugins/lazarus/scripts/lazarus_lib/schemas.py:99` | JSON Schema refusals copied hostile keys and values through `ValidationError.message`; one 200,023-byte `receipt_type` produced a 200,116-byte diagnostic containing `PRIVATE_PROVIDER_VALUE_`. | fixed and guarded in this round; refusals now retain a bounded path and rule while omitting rejected payload bytes |

Leads not pursued: no further defect was confirmed across the 19-file Step 1 diff; empty-block receipt witnesses remain outside the fixed 224-transaction Goldfinch acceptance case; transaction-trie proof shape and evidence-class narrowing remain unchosen because S1-R1-01 requires the receipted Protasis amendment; release-v2, Ariadne state-fixture/v2, live capture, mutable marketplace reconciliation, package versions, and evolution rows remain in their later source-bound steps; the security-suite waiver is exactly `issue #383 changes off-chain Python and JSON evidence handling and produces no Solidity; the bundled Pashov Solidity suite does not apply`; schema validation, 79 focused tests, 1,064 combined Lazarus and Ariadne tests, 432 Lazarus tests, 396 root tests, both Protasis checks, Promise Machine, Imprimatur, ADR Brevitas, `git diff --check`, and whole-tree Phylax, Ephoros, and Hypomnema were selected for final rerun before handoff

## Step 1, round 2 -- 2026-08-26T04:48:47Z

Audit schema: fiat-audit-round/v2

Covered: receipt-set-completeness=reviewed; receipt-rlp-encoding=reviewed; typed-receipt-prefix=reviewed; header-root-binding=reviewed; transaction-index-binding=reviewed; log-query-completeness=reviewed; metadata-overclaim=reviewed; evidence-count-upgrade=not-applicable; legacy-format-compatibility=reviewed; provider-response-bounds=reviewed; atomic-capture=reviewed; release-binding=not-applicable; ariadne-schema-parity=not-applicable; marketplace-prose-drift=reviewed

Not checked: Solidity-only Pashov X-Ray, Solidity Auditor, and Fizz under the recorded non-Solidity waiver; Step 2 receipt-trie reconstruction, Step 3 network capture, Step 4 release and Ariadne propagation, Step 5 live fixture and publication; canonical-chain and provider-independence claims

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | `plugins/lazarus/scripts/lazarus_lib/schemas.py:119` | Value-free JSON Schema refusals remained bypassable with a short identifier-shaped unknown key. A reduced probe using `PRIVATE_PROVIDER_VALUE_SECRET` returned `invalid receipt-witness at <root>: unexpected field: PRIVATE_PROVIDER_VALUE_SECRET`, so attacker-chosen bytes could cross the diagnostic boundary despite its size limit. | fixed and regression-tested in this round; diagnostics now use a pinned-schema path capped at 1,024 characters and never render an unknown instance key; short and 200,023-byte hostile cases pass |

Leads not pursued: S1-R1-01 is closed: receipt-witness-v1 now contains only the verified header identity and `receiptsRoot`, contiguous trie indices, canonical receipt payload fields, ordered `(address, topics, data)` logs, the target index, and the exact filter; plan-v3 keeps the target transaction hash only in a required `recorded-rpc` lookup request; coherent target-hash rewriting does not change witness bytes, and no transaction-trie scope was added. S1-R1-02's size bound remains, while its short-key residual is S1-R2-01. The exact combined Elenchus parent run recorded 1,066 executed tests, 14 assertion failures, 7 errors, and 0 skipped, so its verdict is inconclusive: overlaying the amended consensus-only test support on the pre-amendment schema produced expected schema-shape errors alongside the focused short-key assertion failure. The repaired tree is green on 81 focused tests, 1,066 combined Lazarus and Ariadne tests, 434 Lazarus tests, and 396 root tests. No other defect was confirmed across the cumulative 21-file Step 1 tree; later-step implementation and the exact recorded non-Solidity waiver remain as listed in round 1.

## Step 1, round 3 -- 2026-08-26T05:11:02Z

Audit schema: fiat-audit-round/v2

Covered: receipt-set-completeness=reviewed; receipt-rlp-encoding=reviewed; typed-receipt-prefix=reviewed; header-root-binding=reviewed; transaction-index-binding=reviewed; log-query-completeness=reviewed; metadata-overclaim=reviewed; evidence-count-upgrade=not-applicable; legacy-format-compatibility=reviewed; provider-response-bounds=reviewed; atomic-capture=reviewed; release-binding=not-applicable; ariadne-schema-parity=not-applicable; marketplace-prose-drift=reviewed

Not checked: Solidity-only Pashov X-Ray, Solidity Auditor, and Fizz under the recorded non-Solidity waiver; Step 2 receipt-trie reconstruction, Step 3 network capture, Step 4 release and Ariadne propagation, Step 5 live fixture and publication; canonical-chain and provider-independence claims

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | `plugins/lazarus/scripts/lazarus_lib/schemas.py:101`; `plugins/lazarus/tests/test_schemas.py:404` | The bounded `FormatError` kept the raw `jsonschema.ValidationError` as its explicit cause. A reduced traceback probe over a 200,023-byte unknown key emitted 409,618 bytes containing `PRIVATE_PROVIDER_VALUE_`; a 29-byte key leaked too. A library caller that logs the traceback could therefore disclose hostile input and amplify output despite the safe outer message. | fixed and guarded in this round; the validator now suppresses the raw cause after deriving its pinned-schema refusal, and tracebacks for short and 200,023-byte hostile keys and values omit the marker and remain at most 4,096 bytes |

Leads not pursued: S1-R1-01 remains closed under the amended consensus-only boundary; S1-R1-02 and S1-R2-01 remain closed, and S1-R3-01 closes the residual traceback surface without changing the proof format or adding transaction-trie scope. The exact combined Elenchus parent run recorded 1,066 executed tests, 1 assertion failure, 0 errors, and 0 skipped; the fixed tree is green on 81 focused tests, 1,066 combined Lazarus and Ariadne tests, and 396 root tests. No additional defect was confirmed across the cumulative Step 1 tree. Empty-block receipt witnesses remain outside the fixed 224-transaction Goldfinch acceptance case; release-v2, Ariadne state-fixture/v2, network capture, the live fixture, mutable marketplace reconciliation, package versions, and evolution rows remain in their later source-bound steps. The security-suite waiver remains exactly `issue #383 changes off-chain Python and JSON evidence handling and produces no Solidity; the bundled Pashov Solidity suite does not apply`; schema validation, the Lazarus suite, both Protasis checks, Promise Machine, Imprimatur, ADR Brevitas, `git diff --check`, and whole-tree Phylax, Ephoros, and Hypomnema were selected for final rerun before handoff

## Step 1, round 4 -- 2026-08-26T05:27:08Z

Audit schema: fiat-audit-round/v2

Covered: receipt-set-completeness=reviewed; receipt-rlp-encoding=reviewed; typed-receipt-prefix=reviewed; header-root-binding=reviewed; transaction-index-binding=reviewed; log-query-completeness=reviewed; metadata-overclaim=reviewed; evidence-count-upgrade=not-applicable; legacy-format-compatibility=reviewed; provider-response-bounds=reviewed; atomic-capture=reviewed; release-binding=not-applicable; ariadne-schema-parity=not-applicable; marketplace-prose-drift=reviewed

Not checked: Solidity-only Pashov X-Ray, Solidity Auditor, and Fizz under the recorded non-Solidity waiver; Step 2 receipt-trie reconstruction, Step 3 network capture, Step 4 release and Ariadne propagation, Step 5 live fixture and publication; canonical-chain and provider-independence claims

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | medium | `plugins/lazarus/scripts/lazarus_lib/schemas.py:98`; `plugins/lazarus/tests/test_schemas.py:404` | Round 3 used `raise ... from None`, which hid the hostile `jsonschema.ValidationError` from formatted output but retained it as `FormatError.__context__`. A reduced probe over a 200,023-byte unknown key produced a 200,101-byte context representation containing `PRIVATE_PROVIDER_VALUE_`; a 29-byte key leaked too. A caller inspecting exception context could therefore disclose and amplify rejected input. | fixed and guarded in this round; the bounded refusal is now raised after the handler ends, and short and 200,023-byte hostile keys and values leave messages, args, reprs, causes, contexts, and formatted tracebacks marker-free and at most 4,096 bytes, with both cause and context absent |

Leads not pursued: S1-R1-01 remains closed under the amended consensus-only boundary, and S1-R1-02, S1-R2-01, and S1-R3-01 remain closed; S1-R4-01 removes the retained implicit context without changing the proof format or adding transaction-trie scope. The exact combined Elenchus parent run recorded 1,066 executed tests, 1 assertion failure, 0 errors, and 0 skipped; the fixed tree is green on 128 focused tests, 1,066 combined Lazarus and Ariadne tests, and 396 root tests. No further in-scope defect was confirmed across the cumulative Step 1 tree. Fork-aware receipt encoding, trie reconstruction, release-v2, Ariadne state-fixture/v2, network capture, the live fixture, mutable marketplace reconciliation, package versions, and evolution rows remain in their later source-bound steps. The security-suite waiver remains exactly `issue #383 changes off-chain Python and JSON evidence handling and produces no Solidity; the bundled Pashov Solidity suite does not apply`; schema validation, the Lazarus suite, both Protasis checks, Promise Machine, Imprimatur, ADR Brevitas, `git diff --check`, and whole-tree Phylax, Ephoros, and Hypomnema were selected for final rerun before handoff
