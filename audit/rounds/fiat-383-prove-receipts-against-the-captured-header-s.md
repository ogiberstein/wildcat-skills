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
