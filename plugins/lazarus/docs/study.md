# Lazarus study

<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence. **Current frontier:** Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented.
<!-- marketplace-context:end -->

## Problem and evidence boundary

Lazarus preserves the finite historical Ethereum state and JSON-RPC responses
one application test reads after its archive endpoint, credential, or protocol
front end disappears. It serves protocol engineers, researchers, and security
reviewers without overstating what the named block establishes.

1. Proof-backed state is an account or storage value checked through an
   `eth_getProof` Merkle Patricia proof against the header `stateRoot`; code
   is checked against the proved `codeHash`.
2. Header-bound data has locally checked fields, encoding, and hash. That does
   not establish that the header belongs to Ethereum's canonical chain.
3. Recorded RPC evidence preserves the exact `eth_call`, `eth_getLogs`,
   receipt, or client-trace response under its request without calling it a
   state proof.

The `plugins/lazarus` prototype accepts an Ethereum mainnet capture plan for
one finalised block, exact requests, accounts, and slots. It resolves the block
once; excludes `latest` and `pending` from the effective plan; stores the
header, number, hash, parent hash, and state root; records exact method,
parameters, result or sanitised error; checks declared `eth_getProof` account,
storage, absence, and code claims offline; writes schema-checked deterministic
files bound by component SHA-256 digests; serves exact requests locally with a
documented miss containing method and parameters; and verifies and replays
without network access or the capture URL.

The demonstration at `plugins/lazarus/examples/goldfinch-v0/` uses Ethereum
mainnet Goldfinch market `0x8bbd80f88e662e56b918c353da635e210ece93c6`,
the first row in Tabularium's checked-in release. It captures the account,
code, slot `0x0`, receipt
`0xa46a744d6d52528a660c1d99a4edde403504fe7a308118c7cc947819583ce699`,
and a small log query at one fixed block.

1. Verify the fixture offline.
2. Start replay.
3. Read its code, slot, receipt, and logs through ordinary JSON-RPC and obtain
   the committed answers.
4. Request `0x1` and receive a Lazarus miss, not `0x0` or a network result.
5. Change one proof nibble and observe verification fail.
6. Rebuild identical manifest bytes and digests from the captured files.

The market is a replay subject, not evidence that `0x0` has a business
meaning. This first test does not interpret Goldfinch storage or execute an
arbitrary EVM against partial state. Exact-request replay removes the original
RPC and exposes finite coverage; flexible execution can follow once the format
and proof verifier are stable.

## Prior art

### Repository and organisation

- `specs/lazarus.md` requires declared scope, block-hash identity, exact proof
  claims, missing-data failure, secret removal, deterministic rebuilding, and
  finite coverage. Lazarus was unbuilt on the starting ref.
- `specs/preservation-runbook.md` places Lazarus between an archive node and a
  preservation release: state-derived values need `eth_getProof`, events stay
  source records, and Goldfinch is the first case.
- `plugins/tabularium/examples/goldfinch-v0/` contains 34 borrow rows and 477
  repay rows. Its `coverage.json` says block 25,764,670 came from a hosted
  indexer, events lack independently checked block identities, and derived
  values lack state proofs. Its JSONL, confined paths, component digests, and
  coverage reports are the local format precedent.
- `plugins/ariadne/scripts/ariadne_lib/` supplies safe JSON, path confinement,
  SHA-256 subjects, scrubbing, and offline verification. `specs/ariadne.md`
  reserves a state-fixture predicate for block hash, ancestry, accounts, slots,
  and separate proof-backed and recorded values. Lazarus produces its subject;
  signing stays elsewhere.
- `plugins/probitas/` keeps unavailable sources visible and tests live
  adapters with offline fixtures. Lazarus misses must be equally visible.
- Root `AGENTS.md` and `tests/test_portable_skills.py` require a canonical
  `SKILL.md`, portable entrypoint, plugin contract, Claude and Codex manifests,
  marketplace entries, and tests.

Unmerged branch `codex/mnemosyne-synthesis` at `0d929a0` contains
`specs/mnemosyne.md`. It keeps Lazarus, Tabularium, and Ariadne as separate
verifiers whose claim boundaries survive composition. It is prior art, not a
`main` dependency. The recovered OpenCode session
`ses_ff5057204ffe26V8p4QM5Kh9PL`, “Lazarus prior-art spike research,” had no
final report; each technical conclusion used here was rechecked against its
named source.

The prototype began in `laurenceday/wildcat-skills-todo` before review and
publication in `wildcat-finance/skills`. Wildcat's Foundry fork tests need a
small application-specific set of calls and storage reads, not an Ethereum
database. Goldfinch's wind-down also exposed endpoint loss: Tabularium's source
was a served Graph deployment and its release records the hosted indexer's
block as a limitation. Lazarus preserves state that logs cannot derive.

### Ethereum and client tools

EIP-1186 and `ethereum/execution-apis` define `eth_getProof` fields:
`address`, `accountProof`, `balance`, `codeHash`, `nonce`,
`storageHash`, and `storageProof`; each storage entry has `key`, `value`,
and `proof`. Account and storage paths are `keccak256(address)` under
`stateRoot` and `keccak256(left_pad_32(slot))` under the proved storage
root. Hex RLP-node lists prove inclusion or non-existence; absence cannot be
inferred from a missing object.

The execution API's `tests/eth_getProof/` vectors include
`get-account-proof-with-storage.io` and a block-hash request. They test
interoperability better than the EIP example but do not promise historical
retention. Capture records a capability failure rather than assuming public
RPC archive access. EIP-1898 hash selectors, including `requireCanonical`,
are preferred where supported; otherwise fixed-number calls are bracketed by
matching expected-hash header reads.

At Foundry commit `3c16e2361f18f2cecc975e1d5a8d17330d92ced7` and
`foundry-core` commit `8b3ea9453789ba0d9d8ebf0fc4ee0fed9e4add8f`, fork
caches live under `~/.foundry/cache/rpc/<chain>/<block>/`. Their JSON holds
`meta`, `accounts`, `storage`, and `block_hashes`, with newer zstd
output. Storage maps addresses to hex slot/value pairs. Recent Anvil also uses
`storage-<keccak256(rpc-url)>.json`, resolves a fork block hash at startup,
and retains block hashes.

This remains a cache. On an account, slot, or block-hash miss,
`SharedBackend` fetches and writes provider data. Metadata contains the block
environment and hosts, but account and slot values lack EIP-1186 proofs.
Completeness is implicit, a new read reaches the provider, and Anvil dump/load
describes local state rather than a finite proof-labelled capture. Lazarus may
borrow the ergonomics without calling the cache verified or complete.

Execution-specification state tests carry an execution environment, full
pre-allocation, transaction, expected post-state roots, and log hashes.
Blockchain tests carry pre-allocation, genesis RLP and header, blocks, last
block hash, and post-allocation. Clients can reconstruct tries and check
consensus-critical execution. Ordinary fixtures do not carry EIP-1186 proofs
for arbitrary historical reads. Optional `--witness` output remains
test-block execution input, so these formats are vectors rather than a capture
plan.

Geth's struct logger reports program counter, opcode, remaining gas, gas cost,
call depth, and optional memory, stack, return data, and storage. `callTracer`
emits call frames; `prestateTracer` emits touched accounts and slots, with a
diff mode for changes. Those are trie leaves, not cryptographic proofs.
`debug_traceCall` may regenerate historical state; `reexec` defaults to 128
and documented regeneration can take minutes. Trace namespaces, names,
defaults, and encodings vary by client. Lazarus records client, version,
tracer, options, and exact response without claiming cross-client canonical
output or proof for every value.

Reth's `debug_executionWitness` and `debug_executionWitnessByBlockHash` map
hashed trie nodes to preimages for re-executing a whole block and recomputing
its state root. This may become an importer, but it is broader than Geth
`prestateTracer` and does not describe arbitrary application calls, receipts,
or log ranges. The first prototype should not add a second completeness model.

Tenderly virtual testnets, simulations, archive RPC products, Anvil forks,
Reth databases, and Erigon snapshots preserve historical state but keep a
service dependency or large client-specific artefact. None combines a declared
finite request set, EIP-1186 labels, deterministic release bytes, and an exact
local miss. They are capture sources and comparisons, not the format.

## Constraints and design

The original implementation started from clean `main` at
`83fef6634a560860b930a532861dbfff8cbb3442` in
`laurenceday/wildcat-skills-todo`, where no Lazarus plugin existed.

Python 3.11 or newer owns the CLI, deterministic writer, and local HTTP server,
matching Ariadne, Probitas, and Tabularium. A pinned Ethereum trie stack
(`eth-hash` with Keccak, `rlp`, and `trie`) may sit behind one verifier
module; do not write new Keccak or Merkle Patricia code or add Web3 just for
JSON-RPC. Once dependencies are installed, every repository test runs offline.

Canonical output uses UTF-8, ASCII schema keys, lexicographically sorted object
keys, compact separators, no floating point, and one trailing newline for
JSONL. Ethereum hex quantities become integers only for bounded comparisons.
SHA-256 identifies fixture files and releases; Keccak-256 remains the trie and
code hash.

Capture URLs and headers are runtime inputs, never fixture, diagnostic, or
digest material. Only safe metadata such as an allowed client-family/version
probe may persist. Scrub URL user information, query strings, API keys,
cookies, and arbitrary provider errors.

The effective plan has a fixed block number and expected hash; tags may be
resolved before storage, but `latest` and `pending` never persist. The first
profile covers Ethereum mainnet's current Merkle Patricia trie. L2 roots,
Verkle state, pre-Byzantium receipt differences, and chain-specific extensions
need separate profiles.

The prototype does not:

- replace an archive node, capture unbounded state, execute arbitrary local
  `eth_call`, or infer dynamic slots;
- prove logs or receipts against `receiptsRoot`, or infer canonicality or
  finality from an internally consistent header;
- normalise `debug_` or `trace_` clients, capture pending state, mempool,
  subscriptions, or writes;
- collect keys, sign transactions, use a live provider during replay, publish,
  sign, or merge a Mnemosyne release;
- rewrite Tabularium's Goldfinch release or provide a Foundry state backend.

Replay begins with `eth_chainId`, `eth_getBlockByHash`,
`eth_getBlockByNumber`, `eth_getBalance`, `eth_getTransactionCount`,
`eth_getCode`, `eth_getStorageAt`, `eth_getProof`, `eth_call`,
`eth_getLogs`, `eth_getTransactionByHash`, and
`eth_getTransactionReceipt`. Other read-only methods may be recorded as
unproved exact method/parameter evidence. Writes and subscriptions are rejected.

Four options were considered:

1. A warmed Foundry `storage.json` is short and supports local execution, but
   completeness is accidental, misses reach the provider, values lack proofs,
   internals own the format, and scope is not reviewable.
2. The selected deterministic cassette stores an explicit plan, checked
   header, exact responses, EIP-1186 proofs, and digest manifest. It verifies
   offline; exact method-plus-parameters misses return JSON-RPC errors and plan
   entries; calls, logs, receipts, and traces stay recorded evidence. Ordinary
   JSON tools can inspect it, and uncaptured state cannot be implied.
3. A revm database could execute arbitrary calls and expose absent slots, but
   adds hardfork, environment, precompile, override, block-history, dynamic
   dependency, and client-parity questions. It can consume a stable fixture
   later; its results would be new calculations.
4. A Reth witness, Erigon snapshot, or client database supports wider
   execution and block completeness but is large, client-bound, and aimed at
   blocks rather than application calls. It can become an optional importer.

## Selected format and verification details

The selected layout is:

```text
fixture/
  manifest.json  component digests, versions, and evidence counts
  plan.json      chain, block, methods, accounts, and slots
  header.json    full header, recomputed hash, and state root
  rpc.jsonl      canonical exact requests and results or errors
  proofs.jsonl   account/storage proofs and verification results
  schemas/       pinned JSON Schemas for this fixture version
```

The request key is SHA-256 of canonical JSON containing only `method` and
`params`; caller `id` is excluded then copied to the response. Object member
order is canonicalised, while arrays, values, omitted fields, quantities,
addresses, and selectors stay exact. Do not coerce `0x0`, `0x00`, decimal
zero, or `latest`.

Each request has a name, exact method and parameters, `required`, and expected
evidence class. Proof targets have an address and sorted unique 32-byte slots.
The effective plan records chain ID, block number, and hash. Capture fails on
header disagreement, required-method failure, a returned object naming another
block, or an invalid proof. Optional failure persists as a sanitised error and
manifest count.

For each account proof:

1. Recompute the fork-appropriate RLP header hash and compare the expected hash.
2. Traverse `accountProof` from `stateRoot` with `keccak256(address)`.
3. RLP-decode nonce, balance, storage root, and code hash.
4. Compare response fields with the leaf.
5. Traverse each storage proof with `keccak256(slot32)` and compare its value.
6. Keccak-hash captured code and compare the proved code hash.

Absence must terminate under trie rules and yield the documented empty account
or zero slot. Missing nodes are errors. Duplicate RLP nodes, malformed compact
paths, overlong RLP, values wider than 256 bits, and response keys different
from planned slots fail.

`manifest.json` records schema and tool versions, plan and block identity,
component lengths and SHA-256 digests, evidence counts, optional failures, and
the fixture digest. It cannot hash itself. The fixture digest hashes canonical
JSON of the versioned identity and sorted component path/length/digest triples.
Paths are relative, slash-normalised, confined, and not symlinks.

Replay verifies in-process, binds loopback, and has no capture URL, proxy, or
fallback. An exact miss returns `-32070` with canonical `method`, `params`,
and a recapture plan fragment. Batches are per-item, notifications have no
response, and writes fail even if a malformed fixture contains one.

## Risks and terms

- False chain identity: recompute the header hash, require and provenance the
  expected hash, and leave consensus finality external.
- Provider equivocation: resolve once, prefer EIP-1898 hash selectors, and
  bracket number fallback with the same header.
- Proof-verifier errors: pin trie code and use execution-apis vectors,
  independent negatives, and every-node mutations for RLP lengths, hex-prefix
  paths, embedded/hashed nodes, empty accounts, and zero slots.
- Code substitution: `eth_getProof` proves `codeHash`, so hash
  `eth_getCode` locally and reject mismatch.
- Evidence inflation: require an evidence class per record and report
  proof-backed state separately from calls, logs, receipts, and traces.
- Request-key drift: canonicalise syntax only; preserve address case,
  omissions, quantities, tags, canonical request bytes, and digest.
- Silent provider access: ship no provider client in replay; block non-loopback
  sockets and assert misses make no outbound attempt.
- Dynamic calls and client traces: keep calls exact, defer EVM execution until
  access discovery has a miss protocol, and store client/version/method/options
  with opaque trace results from Geth, Reth, Erigon, or hosted providers.
- Secret disclosure: allowlist metadata, scrub errors, test userinfo, query,
  headers, bearer tokens, and scan every output before finalisation.
- Parser and resource attacks: reject absolute paths, traversal, symlinks,
  duplicate keys, oversized fields, excessive nesting, invalid UTF-8, and
  unexpected files before proofs; apply request/component limits before
  allocation and stream logs, traces, and proof arrays as JSONL.
- Arithmetic drift: accept canonical unsigned 256-bit hex quantities, reject
  negative, over-wide, and leading-zero values, and never use floating point.
- Nondeterminism: sort by request key or proof target; keep wall time outside
  identity or explicit; exclude completion order, dictionary order, host paths,
  and generated IDs from uncontrolled bytes.
- Schema substitution and upgrades: select a built-in version and check bundled
  schema digests; reject unknown majors; retain old verifiers; give corrections
  new fixture IDs naming the superseded digest.
- Key custody: hold no signing or transaction key. Ariadne signing remains
  external, and unsigned fixtures receive no publisher claim.

Terms:

- Capture plan: versioned chain, block, requests, proof targets, limits, and
  omissions fixed before collection.
- Effective plan: the plan after resolving one block number and expected hash.
- Fixture: the digest-bound plan, header, records, proofs, schemas, and manifest.
- Request record: exact JSON-RPC method/parameters with result or sanitised error.
- Request key: SHA-256 of canonical `method` and exact `params`.
- Proof target: an account address and finite slots required by EIP-1186.
- Proof-backed state: a value checked against the header state root.
- Header-bound data: data checked against the header without a canonical anchor.
- Recorded RPC evidence: an exact provider response without a stronger claim.
- Replay and replay miss: an exact result, or the explicit absent-key error.
- Coverage: planned requests and proof targets answered, failed, or omitted.
- Capability failure: a sanitised unsupported/unserved optional method record.
- Fixture digest: SHA-256 of versioned fields and sorted component digests.
- Chain anchor: external evidence for canonical membership of the checked hash.
- State witness: transition-execution trie nodes and state, broader than the
  first Lazarus exact-request fixture.

## Sources

### Prototype repository and archived research

- `laurenceday/wildcat-skills-todo`, starting commit
  `83fef6634a560860b930a532861dbfff8cbb3442`: `specs/lazarus.md`,
  `specs/preservation-runbook.md`, `specs/ariadne.md`,
  `plugins/tabularium/examples/goldfinch-v0/`, `plugins/ariadne/`,
  `plugins/probitas/`, root `AGENTS.md`, and `tests/test_portable_skills.py`.
- Unmerged local/remote `codex/mnemosyne-synthesis` at `0d929a0`:
  `specs/mnemosyne.md` and `mnemosyne/README.md`.
- OpenCode session `ses_ff5057204ffe26V8p4QM5Kh9PL`, “Lazarus prior-art
  spike research,” is a trail rather than an authority.

### Ethereum specifications and vectors

- EIP-1186, `eth_getProof`: `https://eips.ethereum.org/EIPS/eip-1186`.
- EIP-1898 selectors: `https://eips.ethereum.org/EIPS/eip-1898`.
- Execution APIs: `https://github.com/ethereum/execution-apis/blob/main/src/eth/state.yaml`
  and `src/schemas/state.yaml`.
- Proof vectors: `https://github.com/ethereum/execution-apis/tree/main/tests/eth_getProof`,
  especially `get-account-proof-with-storage.io` and
  `get-account-proof-blockhash.io`.
- Execution-specification fixture docs:
  `https://github.com/ethereum/execution-specs/blob/forks/amsterdam/docs/running_tests/test_formats/state_test.md`
  and `blockchain_test.md`.
- Release and generation:
  `https://github.com/ethereum/execution-specs` and
  `docs/library/execution_testing_fixtures.md`.
- JSON-RPC 2.0: `https://www.jsonrpc.org/specification`.
- JSON Schema 2020-12: `https://json-schema.org/draft/2020-12`.
- RFC 8785 comparison: `https://www.rfc-editor.org/rfc/rfc8785`.

### Clients and developer tools

- Foundry `3c16e2361f18f2cecc975e1d5a8d17330d92ced7`:
  `crates/config/src/lib.rs`, `crates/evm/core/src/fork/database.rs`,
  `crates/evm/core/src/fork/multi.rs`, and `crates/anvil/src/config.rs`.
- `foundry-core` `8b3ea9453789ba0d9d8ebf0fc4ee0fed9e4add8f`:
  `crates/fork-db/src/cache.rs` and `crates/fork-db/src/backend.rs`.
- Anvil: `https://getfoundry.sh/anvil/`.
- Geth tracers:
  `https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers`.
- Geth `debug_traceCall` and `reexec`:
  `https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-debug`.
- Reth witnesses: `https://reth.rs/jsonrpc/debug/` and
  `https://reth.rs/docs/reth_rpc_api/clients/trait.DebugApiClient.html`.
