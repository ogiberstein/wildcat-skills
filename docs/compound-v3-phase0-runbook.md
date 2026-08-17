# Compound v3 Phase 0 runbook

Issue: https://github.com/wildcat-finance/skills/issues/68

## Step 1: Ship the Compound v3 method proof

**Goal.** Pin the production Comet registry, preserve a bounded old/recent
Ethereum RPC corpus under Alexandria, and rebuild one real transaction into
ordered call, storage-write and signed-principal facts under Tabularium.

**Entry.** `main` at
`4651b1b2acec809e3f23db945b85222878bae74d`, issue 68 open, clean tracked
worktree, and the Solidity-security-suite waiver recorded because this step
changes Python, JSON evidence and prose rather than Solidity.

**Exit.** The registry contains 28 production markets on 10 chains at Comet
commit `f766f51583c23acc33b2a7824654ef2029a96804` and binds the four Ethereum
USDC deployment files. Alexandria preserves exact request and response bytes
for the named old and recent transactions, records every method gate and
verifies the release offline. Tabularium consumes only that release and emits
two ordered calls, every relevant repeated `SSTORE`, and the signed principal
transition from 0 to `-6349137978`. Two socket-denied rebuilds match committed
bytes. The synthetic two-borrower fixture is labelled as conformance evidence,
not a mined transaction. All prior release truth bytes remain unchanged.

**Implementation.** Add Alexandria's explicit `compound_v3_phase0.py` network
boundary, pinned registry generator, capture/check modules, schemas, raw
release, example and hostile tests. Add Tabularium's `compound-witness`
commands, Ethereum Keccak implementation and vectors, execution-fact and
witness schemas, checked-in witness, example and hostile tests. Do not widen
Euler schema v2.

**Prose.** Cold-read every mutable first-party marketplace surface. After the
prototype ships, rotate Alexandria to the first resumable, reconciled Ethereum
USDC interval collector and Tabularium to the Phase 1 canonical adapter and
specimen. Keep mined debt-to-debt transfer discovery and Euler v3 coverage
visible as evidence gaps. Preserve vendored and historical prose.

**Verification.** Run the repository-prescribed Python matrix, Pandects
`forge build` and `forge test`, both socket-denied example rebuilds,
frontmatter, link, manifest, schema, generated-document, marketplace-frontier
and protected-file checks. Run Imprimatur and Proscribed over changed prose,
apply Vulgate only as a content-preserving rewrite, run `git diff --check`, and
repeat the root suite from the committed tree.
