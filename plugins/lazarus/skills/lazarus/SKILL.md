---
name: lazarus
description: >
  Capture, verify and replay the finite part of historical Ethereum state and
  exact JSON-RPC evidence required by an application test. Use when an archive
  endpoint or old protocol may disappear and the user needs a deterministic,
  proof-checked fixture with a fail-closed local replay boundary. Never use it
  to describe receipts, logs, calls or traces as state-proof-backed evidence.
metadata:
  version: "0.1.0"
---

# Lazarus

## Frontier

Lazarus owns the state-fixture preservation frontier, not Hexaemeron's delivery
or Solidity frontier. [EVOLUTION.md](EVOLUTION.md) holds its version, target,
next job, and maturity. Do not run another frontier pass once it is mature.

<!-- marketplace-context:start -->
## Where this sits

Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests.

**Use another tool when.** Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence.

**Current frontier.** Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented.
<!-- marketplace-context:end -->

Lazarus turns a finite historical Ethereum capture plan into a deterministic
fixture whose exact JSON-RPC answers survive the original provider.

`$SKILL_DIR` is this file's directory. Resolve the command at
`$SKILL_DIR/../../scripts/lazarus.py`. It implements finite capture, offline
formats, manifests, proof verification, and exact verified loopback replay.

## Available offline commands

Declared fork-test reads become a reviewable fixture; unexpected reads become
visible misses. The fixture keeps a closed venue's block, finite coverage, and
evidence classes together. Incident tests get stable historical inputs while
calls, receipts, logs, and traces remain recorded evidence.

```bash
python3 scripts/lazarus.py capture \
  --plan <plan.json> --rpc-url <url> --out <fixture-directory>
python3 scripts/lazarus.py validate schemas
python3 scripts/lazarus.py validate plan <plan.json>
python3 scripts/lazarus.py build-manifest <fixture-directory> \
  --component plan.json --component header.json \
  --chain-id 0x1 --block-number <quantity> --block-hash <hash>
python3 scripts/lazarus.py verify <fixture-directory>
python3 scripts/lazarus.py replay <fixture-directory>
```

`verify` checks schema versions, safe paths, canonical manifest bytes, and every
component length and SHA-256 digest. It recomputes the fork-appropriate header
hash; verifies EIP-1186 account and storage inclusion or absence against the
state root; compares response fields with decoded leaves; hashes code against
the proved `codeHash`; and reports proof-backed, header-bound, and recorded-RPC
counts. The [study](../../docs/study.md) explains the design; the
[runbook](../../docs/runbook.md) records implementation.

`capture` brackets the plan's fixed number and expected hash, prefers EIP-1898
hash selectors, safely falls back to the fixed number, checks the closing
header, verifies the fixture, then atomically finalises it. Required request or
proof failures leave no fixture. Optional failures retain only a stable
sanitised error. URL credentials, query values, bearer tokens, cookies, and raw
provider errors never enter the fixture.

`replay` verifies before binding `127.0.0.1`. It answers exact method-and-
parameter matches, preserves caller identifiers, handles single requests,
batches, and notifications, and returns `-32070` with a capture-plan fragment
on a miss. It rejects write and unsupported methods and has no provider client
or fallback.

## Fixture boundary

A fixture keeps three evidence classes separate:

1. Proof-backed state. Account and storage values verify through EIP-1186
   against the captured header's `stateRoot`; code verifies against the proved
   `codeHash`.
2. Header-bound data. The header hash and fields are checked internally.
   An external chain anchor is still required to call that header canonical.
3. Recorded RPC evidence. Exact method, parameters and result or sanitised
   error bytes are preserved for calls, receipts, logs and traces without a
   trie-proof claim.

Replay is exact-request replay, not arbitrary EVM execution from partial state.
Request keys canonicalise object member order only; values, array order,
omissions, quantities, and block selectors remain exact.

## What capture must require

- An explicit Ethereum mainnet plan whose effective form fixes one block
  number and expected block hash.
- Exact JSON-RPC method and parameter pairs, required or optional status and
  expected evidence class.
- A finite list of account addresses and sorted, unique 32-byte storage slots.
- Limits for requests, components, time and bytes.
- A second matching header read when number-based provider fallback is used.

Provider credentials are runtime inputs and never enter output, diagnostics,
or digest material.

## What verify must establish

- Built-in schema versions and their registered bytes.
- Safe relative component paths, exact lengths and SHA-256 digests.
- The fork-appropriate header hash and expected block identity.
- Account and storage inclusion or absence proofs against the header state
  root, response values against decoded leaves and code against `codeHash`.
- Separate counts for proof-backed, header-bound and recorded evidence.

A self-consistent header does not establish Ethereum canonical-chain
membership. Report the expected hash and external provenance without upgrading
the local check.

## What replay must guarantee

Replay verifies in-process before binding loopback. It has no capture URL or
fallback provider. An absent request returns the stable Lazarus miss and a
capture-plan fragment; replay never invents zero or leaves loopback.

## What this never does

- Replace an archive node or capture unbounded state.
- Execute arbitrary `eth_call` from partial state in the first format.
- Prove logs or receipts against `receiptsRoot`.
- Treat client trace output as portable proof.
- Capture pending state, subscriptions or write methods.
- Hold a private key, sign a transaction or make an Ariadne publisher claim.
- Claim proof-backed status for any value that did not pass the offline trie
  and code checks.
