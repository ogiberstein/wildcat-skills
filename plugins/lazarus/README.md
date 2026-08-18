# Lazarus

<!-- marketplace-context:start -->
## In one line

Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests.

**Try something else when.** Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence.

**Current frontier.** Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented.

**Next Fiat job.** Use /hexaemeron:fiat to bind a Lazarus fixture through an Ariadne state-fixture predicate in the first end-to-end Goldfinch preservation release without upgrading recorded RPC evidence into proof-backed state. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Each deterministic fixture binds a capture plan, fixed block header, exact
JSON-RPC records, and EIP-1186 account and storage proofs. The current build
captures and verifies versioned plan, header, RPC record, proof record, and
manifest formats. It writes canonical JSON and JSONL, confines paths, derives
exact request keys, checks digests, header hashes, EIP-1186 proofs, and captured
code, then serves only captured requests over loopback. A miss fails closed.

## Evidence boundary

- Proof-backed state uses EIP-1186 against the header's `stateRoot`; captured
  code is checked against the proved `codeHash`.
- Header-bound data is internally consistent with the named header, which alone
  does not establish Ethereum canonical-chain membership.
- Recorded RPC evidence preserves an exact response, receipt, log query, call,
  or trace without claiming a state proof.

The [study](./docs/study.md) records prior art and the selected exact-request
cassette. The [runbook](./docs/runbook.md) splits the prototype into six steps.

## Capture and offline commands

```bash
python3 scripts/lazarus.py capture \
  --plan <plan.json> --rpc-url <url> --out <fixture>
python3 scripts/lazarus.py validate schemas
python3 scripts/lazarus.py validate plan <plan.json>
python3 scripts/lazarus.py build-manifest <fixture> \
  --component plan.json --component header.json \
  --chain-id 0x1 --block-number <quantity> --block-hash <hash>
python3 scripts/lazarus.py verify <fixture>
python3 scripts/lazarus.py replay <fixture>
```

Only `capture` receives a provider URL. It brackets one fixed block, checks
proofs and code, removes provider error prose, and atomically finalises the
fixture. `verify` repeats format, digest, header, trie, and code checks offline.
`replay` verifies before binding, returns a stable capture-plan fragment for a
miss, and has no provider fallback.

## Goldfinch demonstration

[`examples/goldfinch-v0`](./examples/goldfinch-v0) is an Ethereum mainnet
fixture for a Goldfinch market at block `0xc7da16`: a proof-backed account,
contract code and storage slot, plus the named receipt and a five-log query as
recorded RPC evidence. Run it without a provider:

```bash
python3 plugins/lazarus/examples/goldfinch-v0/demo.py
```

The demo verifies before replay, reads four committed results through loopback
JSON-RPC, observes a `-32070` miss for slot `0x1`, rejects a one-nibble proof
mutation, and rebuilds the same manifest bytes.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
```

CI installs the resolved `requirements.lock` under supported Python versions
before running both suites.
