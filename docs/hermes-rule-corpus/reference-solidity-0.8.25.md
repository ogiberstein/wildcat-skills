# Solidity 0.8.25 Gas Optimization Reference

**revision:** citation-preserving markdown edition  
**compiler target:** Solidity `0.8.25`  
**baseline EVM target:** Cancun / Ethereum L1

> citation convention: inline references use standard Markdown footnotes such as `[^REF-01]`. Every footnote contains an ordinary Markdown link, and the final citation table duplicates the complete source list so the references survive download, copy/paste, GitHub rendering, and most static-site generators.

## 1. scope

this reference is intended for an agent that evaluates an existing Solidity codebase and proposes gas optimizations. it targets:

- Solidity `0.8.25`
- `evmVersion = "cancun"`
- both legacy and via-IR compiler pipelines
- Ethereum L1 Cancun gas semantics as the baseline
- separate benchmarking for every L2 or non-Ethereum EVM chain
- production systems where correctness, upgrade safety, auditability, and liveness dominate minor gas reductions

Solidity 0.8.25 defaults to Cancun, can emit `MCOPY` for memory copies, and exposes `TLOAD`/`TSTORE` through inline assembly. canonical standard `for`-loop increments have been automatically unchecked since Solidity 0.8.22.[^REF-01][^REF-02]

## 2. operating principles

### optimization priority

evaluate candidates in this order:

1. remove unnecessary transactions, transfers, callbacks, or persistent state transitions;
2. replace unbounded or asymptotically poor state models;
3. reduce `SSTORE`, then `SLOAD`;
4. reduce external calls and token movements;
5. reduce calldata, memory allocation, copying, and hashing;
6. improve control flow and arithmetic;
7. consider assembly and opcode-level transformations last.

the major production patterns support this order: Aave compresses and lazily updates protocol state; Uniswap v3 uses bitmaps and specialized arithmetic; Uniswap v4 replaces intermediate transfers with transient net-delta accounting; Seaport specializes common execution paths.[^REF-15][^REF-16][^REF-19][^REF-20][^REF-22][^REF-23][^REF-27]

### evidence grades

| grade | meaning |
|---|---|
| A | mechanism is defined by compiler or EVM semantics and appears in mature, audited production code |
| B | mechanism is sound and has production evidence, but applicability is strongly workload-dependent |
| C | specialist or research-backed optimization requiring local artifact evidence and strong equivalence testing |
| X | obsolete advice, folklore, or a contextual technique that must not be emitted as a universal rule |

### automation levels

| level | agent policy |
|---|---|
| safe | agent may patch after mechanically establishing preconditions, then run the full validation gate |
| guarded | agent may prepare a patch, but a human must review the proof and approve the change |
| never | suggestion only; architecture, storage layout, ABI, transient-storage, and assembly consequences remain human-owned |

## 3. proposed rule schema

```yaml
id: STO-09
title: cache repeated storage reads
type: technique
category: state-model-and-storage

compiler_scope:
  - 0.8.25
evm_scope:
  - cancun
pipelines:
  - legacy
  - via-ir

priority: P1
expected_impact: high
correctness_risk: low
evidence_grade: A
status: recommended

summary: >
  Copy a storage value to a stack local when it is read repeatedly
  and cannot change during the relevant region.

mechanism: >
  Even warm SLOADs cost more than stack operations. The first access
  may additionally be cold.

detector_signals:
  - same storage expression read multiple times
  - repeated getters for the same packed word
  - repeated mapping key and member path

recommendation: >
  Load once after the last preceding mutation and keep the cache scope narrow.

preconditions:
  - no internal write invalidates the cached value
  - no callback or external call can make the value stale

proof_obligations:
  - every use observes the same version of the value
  - cache placement dominates all uses

failure_modes:
  - stale state after callback or reentrancy
  - excess stack pressure or code-size regression

validation:
  - optimized IR and assembly diff
  - success and failure gas snapshots
  - mutation and reentrancy tests

automation:
  autofix: safe

references:
  - EIP-2929
  - Aave BorrowLogic
tags:
  - sload
  - cache
```

## 4. compiler and measurement rules

### CMP-01 — pin the complete build configuration

**P0 · A · safe**

pin the exact compiler binary, EVM target, optimizer state, run count, pipeline, metadata settings, libraries, and linked addresses. do not compare gas results produced by different configurations.

### CMP-02 — optimize the production artifact

**P0 · A · safe**

production tests, fuzzing, invariants, audits, gas snapshots, and bytecode review must run against the optimized artifact. testing only an unoptimized debug build does not validate production code generation.

### CMP-03 — treat optimizer runs as a lifecycle parameter

**P1 · A · guarded**

`runs` models expected lifetime executions and trades deployment/code size against runtime cost; it is not the number of optimizer iterations. benchmark a matrix of plausible values against expected deployment count and call frequency.[^REF-03]

### CMP-04 — benchmark legacy and via-IR

**P1 · B · never**

neither pipeline is a universal winner. compile and validate both where the project is free to choose, but retain one canonical audited configuration.

### CMP-05 — inspect optimized IR, assembly, and bytecode

**P1 · A · safe**

a source rewrite is not evidence of an optimization. confirm that generated code changes in the expected way and does not create a larger regression through inlining, stack layout, or code size.

### CMP-06 — profile representative transaction paths

**P0 · A · safe**

define success, revert, cold, warm, first-use, repeat-use, batch, maximum-size, and adversarial scenarios before ranking candidates.

### CMP-07 — measure cold and warm state independently

**P0 · A · safe**

state access and account access differ between first and subsequent uses within a transaction. `SSTORE` cost also depends on original, current, and new values.[^REF-10][^REF-11] one aggregate gas figure for a stateful function is generally lossy.

### CMP-08 — report a cost vector, not one percentage

**P0 · A · safe**

report:

- deployment and initcode
- runtime success paths
- runtime failure paths
- calldata or data-availability cost
- persistent state growth
- number of transactions
- system-wide transfers and approvals
- break-even by usage scenario

### CMP-09 — apply the compiler known-bugs gate

**P0 · A · safe**

a long-lived 0.8.25 pin needs an automated review against Solidity’s known-bugs list whenever source features or compiler settings change.[^REF-08]

### CMP-10 — require semantic equivalence testing

**P0 · A · guarded**

optimization validation must cover outputs, storage, logs, reverts, calls, value movement, and protocol invariants. assembly and decoder rewrites should retain an executable reference implementation wherever possible.

### CMP-11 — maintain scenario-level gas snapshots

**P1 · A · safe**

track named gas scenarios and linked runtime/initcode size in CI. accepted regressions require an explicit explanation.

### CMP-12 — do not customize optimizer step sequences casually

**P2 · C · never**

a custom Yul optimizer sequence creates a bespoke compiler configuration with a large validation and maintenance burden. Solidity’s Yul optimizer is a set of interacting greedy passes rather than a globally optimal superoptimizer.[^REF-03]

## 5. state model and storage

### STO-01 — pack co-accessed bounded fields

**P1 · A · never**

pack fields when they are commonly read or written together and have durable range bounds. generate a bit-allocation specification and storage-layout diff.

### STO-02 — use full-width arithmetic locals

**P1 · A · guarded**

use `uint256` or `int256` for stack and ordinary memory arithmetic unless narrow semantics are required. narrow widths usually help only when they improve storage packing; EVM stack words and ordinary memory elements remain 256 bits.

### STO-03 — do not pack independently hot fields blindly

**P1 · A · never**

updating one packed field requires loading, masking, and rewriting the shared slot. packing fields that are usually updated separately can cost more despite using fewer slots. Solidity explicitly documents this read-modify-write trade-off.[^REF-04]

### STO-04 — use packed configuration words

**P1 · A · never**

for stable protocol configuration, encode bounded fields with named masks and offsets. reserve extension bits and expose typed getters and setters.

Aave v3’s reserve configuration is the canonical production model: many risk, collateral, borrowing, cap, and status values share packed words.[^REF-15]

### STO-05 — load a packed word once

**P1 · A · guarded**

when several fields from one packed slot are required, cache the raw word and decode all values locally rather than invoking multiple getters.

### STO-06 — aggregate packed updates into one write

**P1 · A · guarded**

load the word, apply every bit mutation locally, validate the final representation, and perform one `SSTORE`. do not expose unsafe intermediate state through callbacks.

### STO-07 — use bitmaps for dense boolean state

**P1 · A · guarded**

use `mapping(uint256 => uint256)` words for dense flags, membership, initialization state, or bounded indexed domains.

Uniswap v3 stores 256 tick initialization flags per word and uses bit scans to find the next initialized tick. Aave stores two user-state bits per reserve.[^REF-19][^REF-16]

### STO-08 — use nonce bitmaps for unordered authorization

**P1 · A · never**

for parallel signed authorizations, partition a nonce into word index and bit position. Permit2 uses an unordered nonce bitmap instead of one storage slot per nonce.[^REF-25]

### STO-09 — cache repeated `SLOAD`s

**P1 · A · safe**

load storage once when no mutation or callback can invalidate the value. keep the cache’s lifetime narrow. even a warm `SLOAD` is more expensive than stack reuse, while the first access to a slot may be cold.[^REF-10]

### STO-10 — cache a storage base pointer

**P1 · A · safe**

replace repeated `mapping[key].member` expressions with a local storage reference when several members are accessed.

### STO-11 — cache storage-array length when invariant

**P1 · A · safe**

cache `.length` before a loop only when the loop body and every reachable callback cannot change it. this is useful for storage arrays, not a universal rule for memory or calldata.

### STO-12 — accumulate locally, commit once

**P0 · A · guarded**

load initial accounting state, perform bounded calculations locally, validate the final value, and execute one storage write.

### STO-13 — skip common no-op writes

**P1 · B · guarded**

guard an `SSTORE` when idempotent calls are common and the old value is already loaded. benchmark the actual state distribution; adding an `SLOAD` and branch solely for the guard can lose.

### STO-14 — validate before persistent writes

**P0 · A · guarded**

perform deterministic parameter, authorization, balance, and limit checks before storage mutation when this does not weaken reentrancy safety or required error precedence.

### STO-15 — use constants for true compile-time values

**P1 · A · safe**

constants avoid storage initialization and reads. check code-size effects when a large expression or value is substituted at many call sites.

### STO-16 — use immutables for deployment-time constants

**P1 · A · guarded**

immutables remove `SLOAD` at the cost of embedding values into runtime code. model repeated references, fleet size, proxies, and clone alternatives.

### STO-17 — use fixed-width internal representations

**P1 · A · never**

use `bytes32` or another fixed-width type when protocol data is canonically bounded to one word. define padding and encoding at the boundary.

### STO-18 — use short-string representations conditionally

**P2 · A · never**

for immutable labels bounded to 31 bytes, a `ShortString`-style word representation can avoid dynamic handling. retain a fallback when arbitrary strings are part of the interface.[^REF-31]

### STO-19 — use code-as-data for large immutable blobs

**P1 · B · never**

an SSTORE2-style data contract can replace many storage slots with deployed code and `EXTCODECOPY`. include deployment, cold account access, copy cost, offsets, read frequency, code limits, and chain support in the break-even.[^REF-30]

### STO-20 — use sentinel values to collapse state

**P1 · B · never**

reserve a value such as zero or maximum to represent uninitialized, unlimited, disabled, or another state only when that value can never become valid protocol data.

### STO-21 — skip decrementing unlimited allowances

**P1 · A · guarded**

when maximum value explicitly means unlimited, branch before subtraction and avoid repeated allowance writes. Aave and Permit2 both use this motif.[^REF-17][^REF-26]

### STO-22 — emit non-consensus history instead of storing it

**P0 · A · never**

use events for append-only history that no future on-chain transition needs to read. retain only current state, commitments, roots, counters, or data required for future verification.

### STO-23 — use cumulative indexes and lazy checkpoints

**P0 · A · never**

replace iteration over every account with global cumulative indexes and per-account checkpoint-on-touch settlement. prove monotonicity, conservation, rounding, and long-horizon overflow bounds. Aave’s indexed balances and reserve-state updates are a mature production example.[^REF-18]

### STO-24 — paginate or aggregate unbounded collections

**P0 · A · never**

do not return or process arbitrarily large storage collections. use bounded pages, indexed getters, commitments, pull claims, or event reconstruction.

### STO-25 — delete storage for lifecycle correctness, not refund farming

**P1 · A · never**

refunds are reduced and capped under the post-London gas schedule.[^REF-12] model clearing cost, likely reuse, state growth, and liveness; never add an unbounded cleanup loop for speculative refunds.

### STO-26 — use mapping plus compact indexed registry

**P1 · A · never**

when both keyed lookup and enumeration are required, keep canonical records in a mapping and a dense list of keys or stable IDs. define tombstones and prohibit unsafe ID reuse.

### STO-27 — treat storage layout as an external interface

**P0 · A · never**

field order, field width, packed masks, and raw slots are ABI-like commitments for proxies, delegatecalls, and storage-reference libraries. no gas rewrite may change them without a migration or equivalence proof.[^REF-04]

## 6. transient storage

### TRN-01 — transient reentrancy guards

**P1 · A · never**

on Cancun-compatible chains, a transient guard avoids persistent lock writes. prove nested-call behavior, multicall reuse, proxy/delegatecall ownership, and every intended clear boundary.[^REF-09]

### TRN-02 — transaction-local callback context

**P1 · A · never**

use transient state for values that must survive external calls but must not survive the transaction: unlock status, phase, temporary authorization, or callback context.[^REF-09]

### TRN-03 — transient mapping emulation

**P1 · A · never**

hash a namespace plus fixed-width logical keys into a transient slot. avoid dynamic packed preimages and prove namespace separation.

Uniswap v4 derives transient slots for per-target, per-currency signed deltas.[^REF-22]

### TRN-04 — net-delta or flash accounting

**P0 · A · never**

record signed transaction-local asset deltas and perform only final settlement rather than transferring assets after every internal operation.

this removes gross intermediate transfers but requires a locked execution boundary, strict asset-conservation invariants, adversarial-token handling, and proof that every nonzero obligation is settled before exit. Uniswap v4 is the primary production reference.[^REF-24]

### TRN-05 — unresolved-obligation counter

**P0 · A · never**

increment a transient counter on zero-to-nonzero obligation transitions and decrement on nonzero-to-zero transitions. assert zero at the final boundary instead of enumerating every touched key.[^REF-23]

### TRN-06 — model `CALL` versus `DELEGATECALL` ownership

**P0 · A · never**

delegatecalled code operates on the caller’s transient state; a separately called contract owns separate transient state. slot namespaces and lock domains must match the proxy and module architecture.[^REF-09]

### TRN-07 — chain-capability gate

**P0 · A · safe**

bytecode reaching `TLOAD` or `TSTORE` fails on a chain without EIP-1153. compiler success is not evidence that every deployment chain supports the artifact.[^REF-09]

## 7. calldata, memory, and ABI

### MEM-01 — retain read-only dynamic inputs in calldata

**P1 · A · safe**

declare external read-only dynamic arguments as `calldata` and avoid implicit conversion to memory.

### MEM-02 — preserve calldata through internal helpers

**P1 · A · guarded**

a calldata parameter loses its advantage when the first helper accepts memory. use calldata helpers or carefully selected overloads.

### MEM-03 — use calldata slices

**P1 · A · guarded**

validate offset and length once, then pass a calldata view rather than allocating and copying a subrange.

### MEM-04 — use custom packed calldata only on concentrated hot paths

**P0 · B · never**

a custom byte format can remove ABI padding and redundant fields, but it creates a parser and a new external protocol.

requirements:

- versioned wire-format specification
- canonical widths and byte order
- off-chain reference encoder
- reference Solidity decoder
- malformed and truncated input fuzzing
- signature and commitment compatibility tests
- separate L1 and L2 fee measurements

### MEM-05 — decode only the consumed fields

**P1 · B · never**

a specialized path need not allocate a maximal nested structure when it uses a few fixed fields. keep the generic decoder as a differential oracle.

Seaport’s basic-order path demonstrates this optimization at production scale.[^REF-27]

### MEM-06 — use scratch memory for fixed short-lived operations

**P2 · A · never**

use `0x00–0x3f` for ephemeral hashes or call data only when no pointer escapes and Solidity’s zero-slot and free-memory-pointer invariants remain valid.[^REF-06]

### MEM-07 — allocate exact buffers

**P2 · B · never**

construct only the memory span required for a call, hash, event, revert, or return value. memory expansion is monotonic within the call frame.

### MEM-08 — re-benchmark old memory-copy assembly under `MCOPY`

**P2 · A · guarded**

Solidity 0.8.25 can emit `MCOPY` for ordinary memory byte-array copies. preserve legacy assembly only when it retains a measured shape-specific advantage or different semantics.[^REF-01]

### MEM-09 — avoid distant memory offsets

**P1 · A · guarded**

one access at a high offset expands memory over the entire intervening range. all attacker-controlled offset and length arithmetic requires explicit bounds.

### MEM-10 — handle fixed returndata directly

**P2 · B · never**

when a caller needs only success, no data, or one fixed word, avoid allocating arbitrary bytes and passing them through a generic decoder.

### MEM-11 — bound revert-data bubbling

**P2 · B · never**

unbounded `RETURNDATACOPY` allows a callee to force memory expansion. define whether errors are propagated, truncated, mapped, or replaced.

### MEM-12 — hash fixed static tuples directly

**P2 · B · never**

for a fixed sequence of canonical 32-byte words, scratch-memory `KECCAK256` can replace generic `abi.encode`. differential-test every helper against the canonical encoding.

### MEM-13 — return exact-size fixed data

**P2 · B · never**

assembly may write fixed ABI words and `return(pointer, length)` directly. every byte in the returned span must be initialized.

### MEM-14 — support EIP-2098 compact signatures where compatible

**P2 · A · guarded**

accept 64-byte compact signatures alongside standard 65-byte signatures when wallet and library compatibility is established.

### MEM-15 — use Merkle commitments for large static sets

**P0 · A · never**

replace large on-chain membership maps with a root plus proofs where set mutability and proof availability permit. define canonical leaf encoding, domain separation, ordering, and replay protection.

### MEM-16 — never copy an unbounded storage array wholesale

**P0 · A · never**

narrow storage element types still consume ordinary 32-byte memory words after copying. expose indexed or bounded retrieval instead.[^REF-06]

## 8. control flow and arithmetic

### CTL-01 — order independent checks by cost and failure probability

**P1 · A · guarded**

cheap, frequently failing conditions should generally precede hashes, signatures, storage mutations, and external calls. preserve required error precedence and information policy.

### CTL-02 — finish validation and effects before external interactions

**P0 · A · never**

use checks-effects-interactions or a deliberately locked callback state machine. do not move writes after a call merely to reduce reverted-write gas.

### CTL-03 — hoist loop invariants

**P1 · A · safe**

move invariant hashes, storage reads, lengths, address derivations, and conversions outside loops when neither the loop body nor callbacks can mutate their dependencies.

### CTL-04 — use canonical `for` loops

**P2 · A · safe**

prefer:

```solidity
uint256 length = items.length;
for (uint256 i; i < length; ++i) {
    _consume(items[i]);
}
```

on 0.8.25, manually wrapping the increment in `unchecked` is generally redundant for recognized canonical loops.[^REF-02]

### CTL-05 — use `unchecked` only under a local proof

**P1 · A · guarded**

prove every intermediate value, not merely the final result. keep unchecked regions small and colocate the bound or invariant.

### CTL-06 — validate a range once and reuse the proof

**P1 · A · guarded**

a dominating boundary check can justify downstream unchecked arithmetic, narrow casts, or unsafe array access. ensure no independently callable helper bypasses it.

### CTL-07 — remove generic SafeMath wrappers

**P1 · A · safe**

Solidity 0.8.25 already provides checked arithmetic. preserve only wrappers that add domain-specific errors, saturating behavior, or other semantics.

### CTL-08 — batch operations

**P0 · A · never**

amortize authorization, hashing, state warming, setup, and settlement across bounded batches. specify atomic versus partial failure and enforce maximum size.

### CTL-09 — prohibit unbounded mutable-state loops

**P0 · A · never**

replace them with pull claims, pagination, incremental cursors, cumulative indexes, heaps, bitmaps, or other bounded structures.

### CTL-10 — use reviewed full-precision `mulDiv`

**P0 · A · never**

when `x * y` can overflow despite the quotient fitting, use a 512-bit intermediate implementation with explicit rounding. Uniswap v3 `FullMath` and OpenZeppelin `Math.mulDiv` are mature references.[^REF-20][^REF-36]

### CTL-11 — normalize fixed-point scale and delay division

**P1 · B · never**

reduce repeated scale conversions and divisions, but use full-precision intermediates and prove rounding, monotonicity, and conservation.

### CTL-12 — cache type hashes and domain components

**P1 · A · guarded**

type hashes can be constants. deployment-invariant domain components can be immutable or cached, provided chain ID, proxy address, and replay behavior remain correct.

### CTL-13 — use bit scans for bitmap navigation

**P1 · A · never**

use reviewed MSB/LSB routines and bit identities instead of scanning all 256 positions. specify zero-input and signed-index behavior. Uniswap v3’s tick bitmap is the canonical example.[^REF-19]

### CTL-14 — specialize the dominant path

**P0 · A · never**

a narrow fixed-shape path can remove generic decoding, loops, feature branches, and unused checks. differential-test it against the generic path for every input in its eligible subset. Seaport’s basic-order fulfiller is a mature example.[^REF-27]

### CTL-15 — benchmark branchless rewrites

**P2 · C · never**

the EVM lacks a branch predictor, but arithmetic selection can still use more operations and bytecode than a branch. signed extrema are a common failure mode.

### CTL-16 — omit redundant zero initialization

**P2 · A · safe**

remove assignments that are semantically identical to Solidity’s default initialization, but reject the patch when the optimizer already removes them.

### CTL-17 — use logarithmic search for sorted state

**P0 · A · never**

replace linear scans of sorted checkpoints or epochs with reviewed lower/upper-bound searches. maintain sortedness as a protocol invariant.

### CTL-18 — increment pointers in assembly loops

**P2 · B · never**

use start/end pointers rather than recomputing `base + i * width` each iteration. prove fixed width, exact termination, and offset arithmetic.

## 9. external calls, errors, and events

### EXT-01 — use version-correct custom errors

**P1 · A · safe**

for Solidity 0.8.25:

```solidity
error Unauthorized(address caller);

function execute() external {
    if (msg.sender != owner) revert Unauthorized(msg.sender);
}
```

do not generate `require(condition, CustomError())`; custom-error arguments to `require` were introduced after Solidity 0.8.25. use explicit `if` and `revert` for this target.[^REF-07]

### EXT-02 — use selector-only errors narrowly

**P2 · B · never**

for parameterless errors in closed assembly-heavy libraries, four-byte revert data may be sufficient. this degrades diagnostics and must be asserted byte-for-byte.

### EXT-03 — remove long revert strings

**P1 · A · safe**

replace them with custom errors and maintain human-readable explanations in NatSpec and client-side error maps.

### EXT-04 — avoid external self-calls

**P1 · A · guarded**

extract an internal implementation rather than invoking `this.foo()`. preserve modifiers, `msg.sender`, `msg.value`, and reentrancy semantics explicitly.

### EXT-05 — balance inlining against code size

**P1 · A · never**

let the optimizer decide first. source flattening may reduce a jump while multiplying bytecode at several call sites.

### EXT-06 — use external libraries as a fleet/code-size trade

**P1 · A · never**

external libraries share code but introduce linking and `DELEGATECALL` overhead. keep hot arithmetic internal and model fleet break-even.

### EXT-07 — define the return-data contract for every low-level call

**P0 · A · never**

specify accepted lengths and values, EOA behavior, copy limits, failure propagation, and malformed-return policy.

### EXT-08 — expose a controlled multicall when composition is common

**P1 · A · never**

define `CALL` versus `DELEGATECALL`, `msg.value` accounting, reentrancy across subcalls, and atomicity.

### EXT-09 — group warm accesses only when operations commute

**P1 · A · never**

reordering a batch by token, market, or account may reduce cold accesses, but can change prices, limits, logs, and MEV semantics.[^REF-10]

### EXT-10 — mark a function payable only when receiving ETH is harmless

**P2 · B · never**

removing the nonpayable call-value check is a small optimization with a potentially permanent trapped-ETH or accounting consequence.

### EXT-11 — minimize event data without harming observability

**P1 · A · never**

remove duplicated or derivable values and unnecessary topics only after specifying indexer queries, forensic requirements, and reconstruction rules.

### EXT-12 — use pull settlement instead of push loops

**P0 · A · never**

record claimable balances or cumulative entitlements and let each recipient withdraw. prove no double claim, reentrancy safety, and conservation.

### EXT-13 — use a mature safe-transfer implementation

**P0 · A · never**

accept the intended ERC-20 success forms—commonly no return data or exact `true`—while rejecting false and malformed responses. token balance semantics such as fee-on-transfer and rebasing require separate handling.

Solady and Seaport both contain heavily optimized implementations of this pattern.[^REF-29][^REF-28]

### EXT-14 — never use `transfer` or `send` as a reentrancy proof

**P0 · A · never**

the 2300-gas stipend is not a stable security boundary. use explicit call-result handling and reentrancy-safe state design.[^REF-34]

## 10. deployment and architecture

### DEP-01 — use ERC-1167 clones for homogeneous fleets

**P0 · A · never**

use audited clone construction, atomic initialization, a locked implementation, and an instance-count/call-count break-even.[^REF-33]

### DEP-02 — use clone immutable arguments conditionally

**P1 · B · never**

append read-heavy permanent configuration to clone code rather than storing it. prove argument offsets and prevent direct implementation calls from spoofing the argument convention. Solady contains a production-oriented implementation corpus for this technique.[^REF-30]

### DEP-03 — justify proxies by lifecycle and governance

**P0 · A · never**

shared implementation deployment savings do not automatically justify permanent delegation overhead, initialization risk, storage complexity, and upgrade authority.

### DEP-04 — consider a singleton architecture

**P0 · A · never**

a singleton can share code, custody, warm state, and accounting across logical instances. it also turns instance isolation into one large security domain. Uniswap v4 is the strongest current production reference for the pattern.[^REF-24]

### DEP-05 — net system-level transfers

**P0 · A · never**

compute final asset movement and execute the minimum transfers. prove conservation under fees, rebasing, callbacks, and insolvency paths.[^REF-24]

### DEP-06 — split rare code from the hot runtime

**P1 · B · never**

move bulky migration, administration, or rarely used computation into immutable helpers when runtime size is binding. avoid unsafe delegatecalled migration modules.

### DEP-07 — minimize constructor work and initcode

**P1 · A · never**

precompute off-chain, use commitments, constants, immutables, or safe lazy initialization instead of large constructor loops and initialization writes.

### DEP-08 — enforce code-size and initcode budgets

**P0 · A · safe**

Ethereum limits deployed runtime code and meters/limits initcode. track linked artifacts in CI with margin for future changes.[^REF-13][^REF-37]

### DEP-09 — use `CREATE2` where deterministic addressing removes state

**P1 · A · never**

derive instance addresses instead of maintaining a registry when the salt and initcode format can be canonicalized. prove collision, front-running, and versioning behavior.

### DEP-10 — amortize approvals through a shared authorization layer

**P1 · A · never**

Permit2 demonstrates packed allowances, batched transfers, and bitmap nonces, but adds a shared systemic dependency and signature-phishing surface.[^REF-25][^REF-26]

### DEP-11 — lazily initialize records

**P1 · A · never**

derive zero/default state until first use. define an unambiguous initialization sentinel and prevent first-touch races.

### DEP-12 — calculate architecture break-even

**P0 · A · safe**

for direct deployments, clones, proxies, SSTORE2, singletons, and external libraries, model:

```text
total =
    deployments * deployment_cost
  + calls * runtime_cost
  + calldata_cost
  + persistent_state_cost
  + operational_and_security_cost
```

## 11. Yul and inline assembly

### YUL-01 — use `assembly ("memory-safe")` only after proving it

**P0 · A · never**

a correct annotation preserves optimizer freedom. a false annotation is a correctness bug, not an optimistic hint.

memory-using assembly without a valid memory-safe contract can disable optimizer memory reasoning around the function; falsely asserting safety permits undefined behavior.[^REF-05]

### YUL-02 — preserve Solidity’s memory conventions

**P0 · A · never**

respect:

```text
0x00–0x3f  scratch
0x40       free-memory pointer
0x60       zero slot
0x80+      ordinary allocation
```

restore the free-memory pointer and zero slot before returning to Solidity whenever the block mutates them.[^REF-06]

### YUL-03 — clean dirty upper bits

**P0 · A · never**

mask unsigned narrow values and `signextend` signed values before hashing, comparing full words, or merging packed slots.[^REF-05]

### YUL-04 — use direct `CALLDATALOAD` only with complete bounds validation

**P2 · A · never**

truncated calldata reads zero beyond the end; a manual decoder must not accept a malformed input because absent bytes appear as valid zero fields.

### YUL-05 — use one mask-and-merge packed-slot update

**P2 · A · never**

load the slot, clear the field mask, merge the range-checked value, and store once. generate constants from a layout specification rather than handwriting them independently.

### YUL-06 — centralize `TLOAD` and `TSTORE`

**P1 · A · never**

on 0.8.25, wrap transient access in reviewed assembly helpers with namespaced slots, chain gates, and lifecycle documentation.[^REF-01][^REF-09]

### YUL-07 — use fixed-shape scratch-memory hashing

**P2 · A · never**

retain a canonical `abi.encode` reference and differential-test every assembly hash helper.

### YUL-08 — construct minimal call data

**P2 · A · never**

for fixed simple ABIs, write selector and arguments at exact offsets and call with the smallest correct span. clean address and narrow integer inputs first.

### YUL-09 — use unsafe array access only after a dominating bound proof

**P2 · A · never**

encapsulate the primitive and make the proof visible at every call site. OpenZeppelin’s explicit `unsafeAccess` naming is the right design signal.[^REF-32]

### YUL-10 — cast pointers only across identical representations

**P2 · C · never**

pointer reinterpretation is valid only when header, element layout, lifetime, and mutability are identical. never forge storage pointers.

### YUL-11 — return and revert exact spans

**P2 · A · never**

every byte between pointer and pointer-plus-length becomes externally visible returndata. assert raw bytes in tests.

### YUL-12 — avoid custom dispatch except in extreme stable interfaces

**P2 · C · never**

a custom dispatcher duplicates selector routing, payability, length checks, and decoding. use it only after code splitting, optimizer tuning, and architectural alternatives fail.

### YUL-13 — use `EXTCODECOPY` for code-resident immutable data

**P2 · A · never**

verify code existence, size, sentinel prefix, offsets, and cold account cost. an EOA or wrong data contract must not silently decode as valid zero bytes.[^REF-10][^REF-30]

### YUL-14 — call precompiles with exact failure handling

**P2 · A · never**

construct the specified input, verify call success and output shape, and test chain-specific precompile availability.

## 12. production evidence

### Aave v3

reusable motifs:

- packed reserve configuration words
- two user-state bits per reserve
- stable reserve IDs
- reserve caches
- cumulative indexes and lazy accrual
- maximum-value allowance sentinel
- conditional writes
- centralized validation

Aave’s v3 codebase and public audit corpus make these patterns useful evidence rather than gas-golf folklore.[^REF-15][^REF-16][^REF-17][^REF-18]

### Uniswap v3

reusable motifs:

- tick bitmaps
- bounded bit scanning
- full-precision `mulDiv`
- highly specialized pool state transitions
- avoidance of redundant external-account checks on known call paths

v3 core is a mature, heavily reviewed reference implementation for these patterns.[^REF-19][^REF-20][^REF-21]

### Uniswap v4

reusable motifs:

- singleton state and custody
- one unlock/callback execution boundary
- transient lock state
- transaction-local currency deltas
- nonzero-obligation counter
- final zero-delta settlement
- direct transient and persistent slot-read helpers

the main lesson is architectural: transient storage is used to remove intermediate settlement and state writes, not merely to replace one persistent boolean.[^REF-22][^REF-23][^REF-24]

### Permit2

reusable motifs:

- `uint160 amount`, `uint48 expiration`, and `uint48 nonce` in one slot
- maximum allowance sentinel
- storage references
- bounded batch loops
- unordered nonce bitmap
- shared approval infrastructure

[^REF-25][^REF-26]

### Seaport

reusable motifs:

- specialized basic-order entrypoint
- fixed calldata offsets
- selective decoding
- exact memory reuse
- manual event encoding
- compact token calls
- exact/no-return ERC-20 compatibility
- bounded revert bubbling
- function-specialization bypasses

Seaport is a strong reference for what assembly-heavy optimization looks like after substantial review. it is not evidence that every protocol should adopt the same complexity.[^REF-27][^REF-28]

### Solady

reusable motifs:

- scratch-memory hashing
- selector-only errors
- minimal token transfer encoding
- SSTORE2
- clone variants and immutable arguments
- bitmaps and packed maps
- transient reentrancy guards
- direct return-data construction

Solady is best treated as a corpus of specialist implementations and differential-test targets. its repository emphasizes extensive testing while still requiring users to validate the exact adopted code and revision.[^REF-29][^REF-30]

### OpenZeppelin

reusable motifs:

- `ShortStrings`
- audited ERC-1167 clones
- full-precision math
- explicit unsafe array-access primitives
- maintainability-first optimization policy

OpenZeppelin’s implementations are a useful counterweight to highly compressed assembly: isolate unsafe primitives, preserve readable interfaces, and make the reason for each low-level optimization legible.[^REF-31][^REF-32][^REF-33][^REF-36]

## 13. rejected universal rules

an agent must not emit these as unconditional recommendations:

| id | claim to reject | correction |
|---|---|---|
| MYTH-01 | `++i` is always cheaper than `i++` | inspect optimized output; the compiler frequently normalizes them |
| MYTH-02 | every loop increment needs manual `unchecked` | canonical loops are automatically handled on 0.8.25[^REF-02] |
| MYTH-03 | use `uint8` or `uint16` everywhere | narrow widths mainly help through storage packing |
| MYTH-04 | packing always wins | independently hot fields can become more expensive[^REF-04] |
| MYTH-05 | calldata is always cheaper | copies, caller locations, mutation, and code size determine the result |
| MYTH-06 | `external` is always cheaper than `public` | visibility is not a standalone gas proof |
| MYTH-07 | constants always beat immutables | deployment, code size, per-instance values, and reference count matter |
| MYTH-08 | `abi.encodePacked` is a cheaper drop-in replacement | it changes encoding semantics and can create collisions |
| MYTH-09 | assembly always wins | the compiler may already generate equal or better code |
| MYTH-10 | via-IR always wins | benchmark both pipelines |
| MYTH-11 | maximum optimizer runs is optimal | runs is a lifecycle trade-off[^REF-03] |
| MYTH-12 | cache every array length | storage length can matter; memory/calldata often does not |
| MYTH-13 | shifts are always cheaper than multiply or divide | the compiler normally performs constant strength reduction |
| MYTH-14 | delete storage for profit | refunds are reduced, capped, and lifecycle-dependent[^REF-12] |
| MYTH-15 | `SELFDESTRUCT` recycles deployed contracts | Cancun semantics no longer delete an existing contract except in the creation transaction[^REF-14] |
| MYTH-16 | `transfer` and `send` prevent reentrancy | gas stipends are not a security invariant[^REF-34] |
| MYTH-17 | private functions are cheaper | call graph and optimizer output determine cost |
| MYTH-18 | explicitly initialize every zero | defaults and optimizer removal make this commonly redundant |
| MYTH-19 | prewarm every slot or account | the warm-up itself has a cost[^REF-10] |
| MYTH-20 | `require(condition, CustomError())` works on 0.8.25 | use explicit `if` and `revert`[^REF-07] |
| MYTH-21 | `MCOPY` obsoletes every copy helper | specialized decoding and buffer construction remain distinct[^REF-01] |
| MYTH-22 | `memory-safe` is merely an optimization hint | it is a correctness assertion[^REF-05] |
| MYTH-23 | branchless code is always cheaper | only artifact benchmarks decide |
| MYTH-24 | gas savings are portable across EVM chains | fork and fee models differ |
| MYTH-25 | events are always cheaper than storage | events cannot be consumed by future on-chain logic |
| MYTH-26 | clones and proxies are always cheaper | deployment/runtime break-even may never be reached |
| MYTH-27 | SSTORE2 is always cheaper | immutable size, reads, account warming, and copy costs determine break-even |
| MYTH-28 | unchecked arithmetic is safe after ordinary unit tests | every intermediate bound needs a durable proof |

## 14. agent evaluation workflow

1. read the exact compiler, pipeline, optimizer, EVM target, metadata, and linking configuration;
2. establish reproducible gas and code-size baselines;
3. classify cost by storage, calls, transfers, calldata, memory, hashing, loops, deployment, and state growth;
4. identify architectural candidates before local peepholes;
5. remove candidates already handled by Solidity 0.8.25;
6. cross-check every candidate against the rejected-rule section;
7. attach preconditions, proof obligations, failure modes, and production evidence;
8. classify the candidate as safe, guarded, or never-autofix;
9. patch only safe or guarded candidates;
10. compile and inspect optimized IR, assembly, runtime bytecode, initcode, and size;
11. run unit, differential, fuzz, invariant, fork, malformed-input, adversarial-callee, and adversarial-token tests as applicable;
12. report the complete cost vector and break-even;
13. require explicit human approval for storage layout, ABI, assembly, transient storage, arithmetic-model, and architectural changes.

## 15. release gate

an optimization is not complete until:

- compiler and settings are pinned;
- known compiler bugs are reviewed;
- before and after artifacts are reproducible;
- representative cold/warm, first/repeat, success/failure, and boundary scenarios are measured;
- deployment, runtime, calldata, persistent-state, and system costs are reported separately;
- ABI and storage-layout diffs are empty or explicitly versioned and migrated;
- code-size headroom remains acceptable;
- differential and invariant tests pass;
- assembly memory, bounds, dirty-bit, call, and returndata proofs are documented;
- the review records why the complexity is worth maintaining.

## 16. research support

automated gas-analysis research broadly supports three conclusions:

1. real contracts contain recurring detectable gas-waste patterns;
2. storage behavior and asymptotic structure dominate many local source transformations;
3. equivalence checking is necessary for aggressive bytecode or assembly optimization.

PeCatch, GASOL, ebso, and SuperStack provide useful foundations for detectors, cost models, and equivalence validation, but none removes the need to benchmark the exact compiler artifact and protocol state.[^REF-35][^REF-38][^REF-39][^REF-40]

## footnote definitions

[^REF-01]: [Solidity Team — Solidity 0.8.25 release announcement](https://www.soliditylang.org/blog/2024/03/14/solidity-0.8.25-release-announcement/).
[^REF-02]: [Solidity Team — Solidity 0.8.22 release announcement](https://www.soliditylang.org/blog/2023/10/25/solidity-0.8.22-release-announcement/).
[^REF-03]: [Solidity 0.8.25 documentation — The Optimizer](https://docs.soliditylang.org/en/v0.8.25/internals/optimizer.html).
[^REF-04]: [Solidity 0.8.25 documentation — Layout of State Variables in Storage and Transient Storage](https://docs.soliditylang.org/en/v0.8.25/internals/layout_in_storage.html).
[^REF-05]: [Solidity 0.8.25 documentation — Inline Assembly](https://docs.soliditylang.org/en/v0.8.25/assembly.html).
[^REF-06]: [Solidity 0.8.25 documentation — Layout in Memory](https://docs.soliditylang.org/en/v0.8.25/internals/layout_in_memory.html).
[^REF-07]: [Solidity 0.8.25 documentation — Errors and the Revert Statement](https://docs.soliditylang.org/en/v0.8.25/contracts.html#errors-and-the-revert-statement).
[^REF-08]: [Solidity 0.8.25 documentation — List of Known Bugs](https://docs.soliditylang.org/en/v0.8.25/bugs.html).
[^REF-09]: [EIP-1153 — Transient storage opcodes](https://eips.ethereum.org/EIPS/eip-1153).
[^REF-10]: [EIP-2929 — Gas cost increases for state access opcodes](https://eips.ethereum.org/EIPS/eip-2929).
[^REF-11]: [EIP-2200 — Structured definitions for net gas metering](https://eips.ethereum.org/EIPS/eip-2200).
[^REF-12]: [EIP-3529 — Reduction in refunds](https://eips.ethereum.org/EIPS/eip-3529).
[^REF-13]: [EIP-3860 — Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860).
[^REF-14]: [EIP-6780 — SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780).
[^REF-15]: [Aave v3 core — ReserveConfiguration.sol](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/configuration/ReserveConfiguration.sol).
[^REF-16]: [Aave v3 core — UserConfiguration.sol](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/configuration/UserConfiguration.sol).
[^REF-17]: [Aave v3 core — BorrowLogic.sol](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/logic/BorrowLogic.sol).
[^REF-18]: [Aave v3 core repository](https://github.com/aave/aave-v3-core).
[^REF-19]: [Uniswap v3 core — TickBitmap.sol](https://github.com/Uniswap/v3-core/blob/main/contracts/libraries/TickBitmap.sol).
[^REF-20]: [Uniswap v3 core — FullMath.sol](https://github.com/Uniswap/v3-core/blob/main/contracts/libraries/FullMath.sol).
[^REF-21]: [Uniswap v3 core repository](https://github.com/Uniswap/v3-core).
[^REF-22]: [Uniswap v4 core — CurrencyDelta.sol](https://github.com/Uniswap/v4-core/blob/main/src/libraries/CurrencyDelta.sol).
[^REF-23]: [Uniswap v4 core — NonzeroDeltaCount.sol](https://github.com/Uniswap/v4-core/blob/main/src/libraries/NonzeroDeltaCount.sol).
[^REF-24]: [Uniswap v4 core repository](https://github.com/Uniswap/v4-core).
[^REF-25]: [Permit2 — SignatureTransfer.sol](https://github.com/Uniswap/permit2/blob/main/src/SignatureTransfer.sol).
[^REF-26]: [Permit2 — AllowanceTransfer.sol](https://github.com/Uniswap/permit2/blob/main/src/AllowanceTransfer.sol).
[^REF-27]: [Seaport core — BasicOrderFulfiller.sol](https://github.com/ProjectOpenSea/seaport-core/blob/main/src/lib/BasicOrderFulfiller.sol).
[^REF-28]: [Seaport repository](https://github.com/ProjectOpenSea/seaport).
[^REF-29]: [Solady — SafeTransferLib.sol](https://github.com/Vectorized/solady/blob/main/src/utils/SafeTransferLib.sol).
[^REF-30]: [Solady repository](https://github.com/Vectorized/solady).
[^REF-31]: [OpenZeppelin Contracts v5.0.2 — ShortStrings.sol](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.2/contracts/utils/ShortStrings.sol).
[^REF-32]: [OpenZeppelin Contracts v5.0.2 — Arrays.sol](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.2/contracts/utils/Arrays.sol).
[^REF-33]: [OpenZeppelin Contracts v5.0.2 — Clones.sol](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.2/contracts/proxy/Clones.sol).
[^REF-34]: [Slither detector documentation — dangerous strict equalities and transfer/send-related guidance](https://github.com/crytic/slither/wiki/Detector-Documentation).
[^REF-35]: [He et al. — How to Save My Gas Fees: Understanding and Detecting Real-World Gas Issues in Solidity Programs / PeCatch](https://arxiv.org/abs/2403.02661).
[^REF-36]: [OpenZeppelin Contracts v5.0.2 — Math.sol](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.2/contracts/utils/math/Math.sol).
[^REF-37]: [EIP-170 — Contract code size limit](https://eips.ethereum.org/EIPS/eip-170).
[^REF-38]: [Albert et al. — GASOL: Gas Analysis and Optimization for Ethereum Smart Contracts](https://arxiv.org/abs/1912.11929).
[^REF-39]: [Nagele and Schett — Blockchain Superoptimizer / ebso](https://arxiv.org/abs/2005.05912).
[^REF-40]: [Albert et al. — SuperStack: Superoptimization of Stack-Bytecode via Greedy, Constraint-Based, and SAT Techniques](https://dl.acm.org/doi/10.1145/3656431).

## citation table

| id | source | type | link |
|---|---|---|---|
| REF-01 | Solidity 0.8.25 release announcement | compiler release note | [source](https://www.soliditylang.org/blog/2024/03/14/solidity-0.8.25-release-announcement/) |
| REF-02 | Solidity 0.8.22 release announcement | compiler release note | [source](https://www.soliditylang.org/blog/2023/10/25/solidity-0.8.22-release-announcement/) |
| REF-03 | Solidity 0.8.25: The Optimizer | versioned compiler documentation | [source](https://docs.soliditylang.org/en/v0.8.25/internals/optimizer.html) |
| REF-04 | Solidity 0.8.25: storage layout | versioned compiler documentation | [source](https://docs.soliditylang.org/en/v0.8.25/internals/layout_in_storage.html) |
| REF-05 | Solidity 0.8.25: inline assembly | versioned compiler documentation | [source](https://docs.soliditylang.org/en/v0.8.25/assembly.html) |
| REF-06 | Solidity 0.8.25: memory layout | versioned compiler documentation | [source](https://docs.soliditylang.org/en/v0.8.25/internals/layout_in_memory.html) |
| REF-07 | Solidity 0.8.25: errors and revert | versioned compiler documentation | [source](https://docs.soliditylang.org/en/v0.8.25/contracts.html#errors-and-the-revert-statement) |
| REF-08 | Solidity 0.8.25: known bugs | versioned compiler documentation | [source](https://docs.soliditylang.org/en/v0.8.25/bugs.html) |
| REF-09 | EIP-1153: transient storage | EIP | [source](https://eips.ethereum.org/EIPS/eip-1153) |
| REF-10 | EIP-2929: cold/warm state access | EIP | [source](https://eips.ethereum.org/EIPS/eip-2929) |
| REF-11 | EIP-2200: net `SSTORE` metering | EIP | [source](https://eips.ethereum.org/EIPS/eip-2200) |
| REF-12 | EIP-3529: reduced refunds | EIP | [source](https://eips.ethereum.org/EIPS/eip-3529) |
| REF-13 | EIP-3860: initcode metering and limit | EIP | [source](https://eips.ethereum.org/EIPS/eip-3860) |
| REF-14 | EIP-6780: changed `SELFDESTRUCT` semantics | EIP | [source](https://eips.ethereum.org/EIPS/eip-6780) |
| REF-15 | Aave v3 `ReserveConfiguration.sol` | production source | [source](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/configuration/ReserveConfiguration.sol) |
| REF-16 | Aave v3 `UserConfiguration.sol` | production source | [source](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/configuration/UserConfiguration.sol) |
| REF-17 | Aave v3 `BorrowLogic.sol` | production source | [source](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/logic/BorrowLogic.sol) |
| REF-18 | Aave v3 core repository | production repository / review corpus | [source](https://github.com/aave/aave-v3-core) |
| REF-19 | Uniswap v3 `TickBitmap.sol` | production source | [source](https://github.com/Uniswap/v3-core/blob/main/contracts/libraries/TickBitmap.sol) |
| REF-20 | Uniswap v3 `FullMath.sol` | production source | [source](https://github.com/Uniswap/v3-core/blob/main/contracts/libraries/FullMath.sol) |
| REF-21 | Uniswap v3 core repository | production repository / review corpus | [source](https://github.com/Uniswap/v3-core) |
| REF-22 | Uniswap v4 `CurrencyDelta.sol` | production source | [source](https://github.com/Uniswap/v4-core/blob/main/src/libraries/CurrencyDelta.sol) |
| REF-23 | Uniswap v4 `NonzeroDeltaCount.sol` | production source | [source](https://github.com/Uniswap/v4-core/blob/main/src/libraries/NonzeroDeltaCount.sol) |
| REF-24 | Uniswap v4 core repository | production repository / review corpus | [source](https://github.com/Uniswap/v4-core) |
| REF-25 | Permit2 `SignatureTransfer.sol` | production source | [source](https://github.com/Uniswap/permit2/blob/main/src/SignatureTransfer.sol) |
| REF-26 | Permit2 `AllowanceTransfer.sol` | production source | [source](https://github.com/Uniswap/permit2/blob/main/src/AllowanceTransfer.sol) |
| REF-27 | Seaport `BasicOrderFulfiller.sol` | production source | [source](https://github.com/ProjectOpenSea/seaport-core/blob/main/src/lib/BasicOrderFulfiller.sol) |
| REF-28 | Seaport repository | production repository / review corpus | [source](https://github.com/ProjectOpenSea/seaport) |
| REF-29 | Solady `SafeTransferLib.sol` | production library source | [source](https://github.com/Vectorized/solady/blob/main/src/utils/SafeTransferLib.sol) |
| REF-30 | Solady repository | optimized-library corpus | [source](https://github.com/Vectorized/solady) |
| REF-31 | OpenZeppelin v5.0.2 `ShortStrings.sol` | versioned library source | [source](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.2/contracts/utils/ShortStrings.sol) |
| REF-32 | OpenZeppelin v5.0.2 `Arrays.sol` | versioned library source | [source](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.2/contracts/utils/Arrays.sol) |
| REF-33 | OpenZeppelin v5.0.2 `Clones.sol` | versioned library source | [source](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.2/contracts/proxy/Clones.sol) |
| REF-34 | Slither detector documentation | security-tool documentation | [source](https://github.com/crytic/slither/wiki/Detector-Documentation) |
| REF-35 | PeCatch paper | research paper | [source](https://arxiv.org/abs/2403.02661) |
| REF-36 | OpenZeppelin v5.0.2 `Math.sol` | versioned library source | [source](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.2/contracts/utils/math/Math.sol) |
| REF-37 | EIP-170: contract code-size limit | EIP | [source](https://eips.ethereum.org/EIPS/eip-170) |
| REF-38 | GASOL paper | research paper | [source](https://arxiv.org/abs/1912.11929) |
| REF-39 | Blockchain Superoptimizer / ebso paper | research paper | [source](https://arxiv.org/abs/2005.05912) |
| REF-40 | SuperStack paper | research paper | [source](https://dl.acm.org/doi/10.1145/3656431) |
