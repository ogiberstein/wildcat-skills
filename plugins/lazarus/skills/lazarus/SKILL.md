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

Lazarus turns a finite historical Ethereum capture plan into a deterministic
fixture and calls its exact JSON-RPC answers back into a local test after the
original provider is gone.

`$SKILL_DIR` is the directory holding this file. The command lives at
`$SKILL_DIR/../../scripts/lazarus.py`; resolve it from where you loaded this
skill. This build implements finite capture plus the offline format, manifest
and proof-verification layer, with exact verified replay over loopback.

## Day to day

**Protocol engineering.** A fork test depends on a paid archive endpoint and
one old block. Its declared reads become a reviewable fixture, and an
unexpected read becomes a visible miss instead of a hidden provider call.

**Research.** A closed venue's state needs to remain inspectable after its
front end and hosted data disappear. The fixture keeps the block, finite
coverage and evidence classes together.

**Security.** An incident test needs stable historical inputs. Account and
storage values are checked against the captured state root, while calls,
receipts, logs and client traces remain labelled as recorded evidence.

## Available offline commands

The current build validates versioned documents and binds their bytes in a
manifest:

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

`verify` checks schema versions, safe paths, canonical manifest bytes and every
declared component length and SHA-256 digest. It then recomputes the
fork-appropriate header hash; verifies EIP-1186 account and storage inclusion
or absence against the header state root; checks response fields against the
decoded leaves; and hashes captured code against the proved `codeHash`. It
reports separate proof-backed, header-bound and recorded-RPC evidence counts.
Read the checked-in
[study](../../docs/study.md) for the selected design and the
[runbook](../../docs/runbook.md) for implementation status.

`capture` resolves and brackets the plan's fixed number and expected hash. It
prefers EIP-1898 hash selectors for proofs and code, safely falls back to the
fixed number, checks the closing header, verifies the complete fixture and
only then atomically finalises the output directory. Required request or proof
failures leave no fixture. Optional provider failures retain only a stable
sanitised error. URL credentials, query values, bearer tokens, cookies and raw
provider errors are not fixture material.

`replay` verifies the fixture in the same process before binding to
`127.0.0.1`. It answers only exact method-and-parameter matches, preserves the
caller's identifier, handles single requests, batches and notifications, and
returns error `-32070` with a capture-plan fragment on a miss. It rejects
write and unsupported methods and has no provider client or fallback setting.

## Fixture boundary

A fixture separates three classes rather than lending one class the strength
of another:

1. **Proof-backed state.** Account and storage values verify through EIP-1186
   against the captured header's `stateRoot`; code verifies against the proved
   `codeHash`.
2. **Header-bound data.** The header hash and fields are checked internally.
   An external chain anchor is still required to call that header canonical.
3. **Recorded RPC evidence.** Exact method, parameters and result or sanitised
   error bytes are preserved for calls, receipts, logs and traces without a
   trie-proof claim.

Replay is exact request replay, not arbitrary EVM execution from a partial
world state. Object member order is canonicalised for a request key; values,
array order, omitted fields, quantities and block selectors remain exact.

## What capture must require

- An explicit Ethereum mainnet plan whose effective form fixes one block
  number and expected block hash.
- Exact JSON-RPC method and parameter pairs, required or optional status and
  expected evidence class.
- A finite list of account addresses and sorted, unique 32-byte storage slots.
- Limits for requests, components, time and bytes.
- A second matching header read when number-based provider fallback is used.

Provider credentials are runtime inputs. They never enter output, diagnostics
or digest material.

## What verify must establish

- Built-in schema versions and their registered bytes.
- Safe relative component paths, exact lengths and SHA-256 digests.
- The fork-appropriate header hash and expected block identity.
- Account and storage inclusion or absence proofs against the header state
  root, response values against decoded leaves and code against `codeHash`.
- Separate counts for proof-backed, header-bound and recorded evidence.

A self-consistent header is not proof that it belongs to Ethereum's canonical
chain. Report the expected hash and its external provenance without upgrading
the local check.

## What replay must guarantee

Replay verifies the fixture in the same process before binding to loopback. It
has no capture URL and no fallback provider. A request absent from the fixture
returns the stable Lazarus miss error and a capture-plan fragment. It never
invents a zero value or leaves loopback to answer a miss.

## What this never does

- Replace an archive node or capture unbounded state.
- Execute arbitrary `eth_call` from partial state in the first format.
- Prove logs or receipts against `receiptsRoot`.
- Treat client trace output as portable proof.
- Capture pending state, subscriptions or write methods.
- Hold a private key, sign a transaction or make an Ariadne publisher claim.
- Claim proof-backed status for any value that did not pass the offline trie
  and code checks.
