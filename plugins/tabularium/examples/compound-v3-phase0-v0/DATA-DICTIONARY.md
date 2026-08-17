# Compound v3 Phase 0 data dictionary

`facts.jsonl` contains three non-canonical fact kinds. Every row binds the
transaction, block, proxy implementation and implementation-code digest.

| Kind | Meaning |
| --- | --- |
| `call` | A successful ordered Bulker-to-Comet call with its call path, selector, input, output and raw call-trace selector. |
| `storage-write` | A relevant proxy-storage `SSTORE`, in opcode order, bound to the enclosing Comet call path and the raw struct-log selector. |
| `principal-transition` | The packed `userBasic` word before and after the transaction, its Ethereum mapping slot, signed `int104` values and active base borrow index. |

`witness.json` binds the Alexandria release ID, pinned Comet commit, raw
component digests, fact digest and Alexandria method receipt. The receipt
records archive-state, nested-call, ordered-storage and provider-reported
finality gate outcomes. `rpc_modules` is recorded as unsupported by the
gateway.

The storage key is Ethereum Keccak-256 over the padded account and mapping slot
5. SHA3-256 is not interchangeable. The signed principal uses the low 104 bits
of `userBasic`; the base borrow index is read from the packed totals word.

The checked-in witness contains one account moving from principal `0` to
`-6349137978`. The repository also carries a synthetic hostile conformance
fixture for the log-silent borrower-to-borrower debt-transfer shape described
by Compound's pinned scenario tests. That fixture is not mined evidence.
