# Lazarus implementation runbook

<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence. **Current frontier:** Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented.
<!-- marketplace-context:end -->

Build the study's proof-checked, exact-request Ethereum fixture in stacked
Fiat `chain` branches. Each pull request leaves all repository tests green.

## Step 1: Scaffold the Lazarus plugin

**Goal.** Add the plugin shell, pinned Python toolchain, CI, and reviewed design
documents without capture or replay.

**Entry.** `main` at `83fef6634a560860b930a532861dbfff8cbb3442`.

**Exit.** `plugins/lazarus/` contains its runtime contract, canonical skill,
host manifests, agent metadata, MIT licence, package shell, dependency pins,
study, and runbook. The portable entrypoint, both marketplace manifests, root
inventory and instructions, and Lazarus CI include it. `python3 -m unittest
discover -s tests` and `python3 -m unittest discover -s plugins/lazarus/tests
-t plugins/lazarus` pass.

**Files.** `plugins/lazarus/{AGENTS.md,LICENSE,README.md,requirements.txt}`,
`plugins/lazarus/.claude-plugin/plugin.json`,
`plugins/lazarus/.codex-plugin/plugin.json`,
`plugins/lazarus/docs/{study.md,runbook.md}`,
`plugins/lazarus/scripts/lazarus_lib/{__init__.py,version.py}`,
`plugins/lazarus/skills/lazarus/{SKILL.md,README.md,agents/openai.yaml}`,
`plugins/lazarus/tests/{__init__.py,support.py,test_scaffold.py}`,
`.agents/skills/lazarus/SKILL.md`, `.agents/plugins/marketplace.json`,
`.claude-plugin/marketplace.json`, `.github/workflows/lazarus.yml`,
`AGENTS.md`, `README.md` and `tests/test_portable_skills.py`.

**Tests.** Cover manifest parsing, skill/readme identity, portable routing,
documented entrypoints, version pins, and Lazarus in the root portable inventory.

## Step 2: Define deterministic fixtures and manifests

**Goal.** Implement versioned plan, header, RPC-record, proof-record, and
manifest formats with deterministic encoding, safe paths, and digest checks.

**Entry.** The pushed tip of `step-1-scaffold-the-lazarus-plugin`.

**Exit.** The library validates built-in JSON Schemas; rejects duplicate keys
and unsafe paths; writes canonical JSON and JSONL; derives exact request keys;
builds a confined manifest; and verifies every length and SHA-256 digest.
`python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus`
passes offline.

**Files.** `plugins/lazarus/schemas/{plan-v1.json,header-v1.json,rpc-record-v1.json,proof-record-v1.json,manifest-v1.json}`,
`plugins/lazarus/scripts/lazarus_lib/{canonical.py,errors.py,paths.py,schemas.py,records.py,manifest.py}`,
`plugins/lazarus/scripts/lazarus.py`, and
`plugins/lazarus/tests/{test_canonical.py,test_paths.py,test_schemas.py,test_records.py,test_manifest.py}`.

**Tests.** Cover stable bytes across insertion order and rebuilds, exact request
keys, quantities, addresses, duplicate keys, traversal, absolute paths,
symlinks, digest and size mismatches, unknown schemas, extra files, and limits.

## Step 3: Verify headers, accounts, storage and code

**Goal.** Add offline Ethereum header and EIP-1186 account/storage proof checks
with explicit proof-backed and recorded-evidence boundaries.

**Entry.** The pushed tip of `step-2-define-deterministic-fixtures-and-manifests`.

**Exit.** `lazarus verify <fixture>` recomputes the fork-appropriate header hash;
checks account inclusion or absence against `stateRoot`, storage inclusion or
absence against each proved root, response fields against decoded leaves, and
code against `codeHash`; reports evidence counts separately; and rejects any
mutation. The plugin suite passes offline.

**Files.** `plugins/lazarus/scripts/lazarus_lib/{hexvalue.py,rlp.py,trieproof.py,header.py,proofs.py,verifier.py}`,
`plugins/lazarus/tests/fixtures/execution-api/`, and
`plugins/lazarus/tests/{test_hexvalue.py,test_rlp.py,test_trieproof.py,test_header.py,test_proofs.py,test_verifier.py}`.

**Tests.** Import compact EIP-1186 vectors. Mutate every proof node, malformed
or overlong RLP, compact paths, embedded or hashed nodes, empty accounts, zero
slots, mismatched keys, values wider than 256 bits, roots, hashes, and code.

## Step 4: Capture a finite plan safely

**Goal.** Capture one fixed block, declared RPC calls, and required proofs
without persisting provider secrets.

**Entry.** The pushed tip of `step-3-verify-headers-accounts-storage-and-code`.

**Exit.** `lazarus capture --plan <plan> --rpc-url <url> --out <directory>`
brackets the named block, prefers EIP-1898 hash selectors, records required and
optional requests, checks proofs and code, sanitises failures, and atomically
writes one deterministic fixture. A fake local RPC covers the path; the plugin
suite passes offline.

**Files.** `plugins/lazarus/scripts/lazarus_lib/{rpc.py,capture.py,scrub.py,limits.py}`,
`plugins/lazarus/tests/{fake_rpc.py,test_rpc.py,test_capture.py,test_scrub.py,test_limits.py}`,
and the Step 2 schemas where capture-only constraints require an additive
clarification.

**Tests.** Cover fixed number and expected-hash resolution, effective-tag
rejection, equivocation, EIP-1898 fallback, required and optional failures,
proof rejection before finalisation, response order, limits, interrupted
writes, URL userinfo, query keys, bearer headers, cookies, and secret errors.

## Step 5: Replay exact requests and fail closed

**Goal.** Serve a verified fixture over loopback JSON-RPC with exact matches, no
provider client, and a stable miss.

**Entry.** The pushed tip of `step-4-capture-a-finite-plan-safely`.

**Exit.** `lazarus replay <fixture>` verifies before binding; answers captured
single and batch requests with caller JSON-RPC identifiers; handles
notifications; rejects writes; and returns `-32070` plus a capture-plan
fragment on a miss. It has no provider or fallback. Socket-blocked tests prove
a miss stays on loopback; the plugin suite passes offline.

**Files.** `plugins/lazarus/scripts/lazarus_lib/{replay.py,server.py}`,
`plugins/lazarus/tests/{test_replay.py,test_server.py,test_no_network.py}`, and
`plugins/lazarus/README.md` for the verified local replay command.

**Tests.** Cover reordered request-object keys, exact values, caller IDs,
notifications, mixed batches, malformed JSON-RPC, unsupported and write
methods, invalid fixtures, stable miss payloads, concurrency, loopback, and
blocked outbound sockets.

## Step 6: Ship and run the Goldfinch demonstration

**Goal.** Prove the prototype with an offline-verifiable Goldfinch fixture and
an application test using ordinary JSON-RPC.

**Entry.** The pushed tip of `step-5-replay-exact-requests-and-fail-closed`.

**Exit.** `plugins/lazarus/examples/goldfinch-v0/` contains the fixed plan,
header, proof-backed account/code/slot data, named receipt, small log query,
schemas, and manifest. The demo verifies, starts replay, reads the committed
code, slot, receipt, and logs, observes a miss for `0x1`, rejects a one-nibble
proof mutation, and rebuilds identical manifest bytes and digests. `python3
plugins/lazarus/examples/goldfinch-v0/demo.py` and every root `AGENTS.md` check pass.

**Files.** `plugins/lazarus/examples/goldfinch-v0/{README.md,plan.json,header.json,rpc.jsonl,proofs.jsonl,manifest.json,demo.py}`,
`plugins/lazarus/examples/goldfinch-v0/schemas/`,
`plugins/lazarus/tests/test_goldfinch.py`, `plugins/lazarus/README.md`,
`README.md` and `specs/lazarus.md`.

**Tests.** Add the end-to-end demo, byte-for-byte rebuild, replay miss, proof
mutation, no-network guard, and repository regression. Record exact totals.
