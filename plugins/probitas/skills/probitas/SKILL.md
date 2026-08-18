---
name: probitas
description: >
  Build a sourced dossier on a counterparty who wants an undercollateralised
  market: what they borrowed across lending venues, whether they gave it back,
  and what could not be established. Use when someone names an entity and the
  wallet addresses it has declared and asks for diligence, borrowing history,
  repayment record, delinquency history, or an underwriting writeup. Do not use
  for questions about a single market's own numbers, and never to work out
  which individual controls an address.
metadata:
  version: "0.2.0"
---

# Probitas

## Frontier

Probitas owns its own counterparty-diligence frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.
This prose generation moved from 0.1.0 to 0.2.0; the frontier did not move.

<!-- marketplace-context:start -->
## Where this sits

Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict.

**Use another tool when.** Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty.

**Current frontier.** Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.
<!-- marketplace-context:end -->

Wildcat lends without collateral. Nothing stands between a lender and a total
loss except a judgement about the borrower, so the counterparty record is the
whole of the security. This assembles that record from public sources and hands
it over without a verdict attached.

`$SKILL_DIR` is the directory holding this file. The tool lives at
`$SKILL_DIR/../../scripts/probitas.py`; resolve it from where you loaded this
skill.

## Day to day

**Business development.** A counterparty asks for a market and someone has to
decide whether their word is worth anything. Give this the addresses they
declared and it comes back with what they borrowed elsewhere, whether they gave
it back, and a list of the venues nobody could check, so the thin parts of the
record are visible rather than absent.

**Finance.** Exposure to a name that also borrows in three other places. The
dossier states each position's venue, the amounts as exact on-chain integers,
and whether anything was left unpaid after a liquidation, which is the number
that ends up mattering.

**Security and audit.** A document arrives asserting things about a
counterparty and you have to decide whether to believe it. Run `verify` against
the evidence file it came with: every figure in the document has to trace back
to a record with a transaction hash, and one that does not fails the check by
arithmetic rather than by your reading it closely.

## The sequence

Run the first four commands in order; the final collect form is the Alexandria
alternative. Do not skip verify.

```bash
python3 scripts/probitas.py venues

python3 scripts/probitas.py collect \
  --entity "<name>" --address 0x... [--address 0x...] \
  [--inferred 0x...] --out evidence.json
python3 scripts/probitas.py render evidence.json --out dossier.md
python3 scripts/probitas.py verify dossier.md evidence.json
python3 scripts/probitas.py collect \
  --entity "<name>" --address 0x... \
  --alexandria-index alexandria.sqlite --out evidence.json
```

`collect` runs every venue adapter over the declared addresses and writes the
evidence file. A record cannot enter that file without a transaction hash, a
URL or a document reference, because the schema will not represent one.

The final form uses verified Alexandria releases through an explicit disposable
index instead of live or fixture adapters.

This path keeps Goldfinch and Clearpool as venue IDs and records Alexandria's
release, component, capture, row and evidence identities. It combines
per-chain coverage conservatively and leaves every unharvested registry venue
visible as a gap. A zero-row venue is empty only when complete archive coverage
includes every requested address, venue, chain and time boundary and the
mapping has no unsupported records. It does not infer a person, default, full
repayment or current balance.

The checked-in Alexandria `credit-history-v0` example exercises this explicit
index path offline and checks the resulting evidence and dossier against fixed
receipts. It does not alter the normal live and fixture routes.

`render` builds the document in the order the specification sets: coverage and
what could not be established stand ahead of anything that reads like a
conclusion, and findings against addresses the counterparty did not declare sit
in their own section at the end.

`verify` reads both together and checks the five gates, printing one line each.
Exit 0 means the dossier may ship. Exit 1 names the gate that stopped it.

## Your part, and its limit

Write the narrative sections from the evidence file and nothing else. The
summary, and any commentary on a venue, are yours. Everything above them is
rendered from records.

You may not introduce a figure the evidence does not contain. Gate 3 rebuilds,
from the evidence alone, every number and hash a truthful dossier could carry,
and fails the document on any it finds that is not in that set. An invented
transaction hash, a rounded amount, a market that was never there: each of
those fails the run rather than shipping in it. This is not a formality to work
around. It is the reason a lender who did not run the tool can trust the
output.

If the evidence is thin, say it is thin. A borrower who used a fresh address
for every market has a short record, and a short record is not a bad one. The
dossier has to say which of those it is looking at.

## The five gates

1. **Address provenance.** Declared, provably linked, and inferred stay in
   separate sections. An inferred address never feeds a conclusion.
2. **Coverage is stated.** Every venue in the registry gets a row, and a venue
   that was queried says over what block range. Silence about a venue would be
   an omission; a row saying nobody checked is a gap, and a gap is not a clean
   record.
3. **Sourcing is total.** Every assertion carries a transaction hash, a URL or
   a document reference, and every figure in the document traces back to a
   record.
4. **Negative space is explicit.** What could not be established gets its own
   section, ahead of any summary.
5. **No score without a rubric.** This version emits no rating, following the
   specification's own lean toward evidence without one. The gate is
   implemented anyway, so whoever adds a rubric later finds the check standing.

See [the gates](references/gates.md) for what each one does mechanically, and
[venue coverage](references/venues.md) for what is checked and what is not.

## What this never does

- **No personal data.** No names of individuals, no social handles, no
  employment history, and no attempt to work out which human is behind an
  address. The evidence schema refuses a value key that names a person, so this
  is a property of the tool rather than a rule you have to remember at two in
  the morning.
- **No social graph.** The counterparty graph covers relationships the
  counterparty declared and relationships visible on chain between the declared
  addresses. Nothing is inferred from off-chain association.
- **No unsourced assertion.** A claim without a citation is dropped, not
  softened into a hedge.
- **No verdict from Wildcat.** The lender reaches their own conclusion. Wildcat
  Labs does not vet borrowers, and a dossier that arrives with our judgement
  attached would make us the underwriter we chose not to be.

If someone asks you to work out who is behind an address, say plainly that
probitas covers entities and addresses and that a dossier which starts
profiling people is a different product and a worse one. Then carry on with the
part you can do.

## When a gate fails

Fix the document, not the gate. A gate 3 failure naming a figure means the
narrative asserts something the evidence does not support: cut the sentence or
find the record. A gate 2 failure means coverage is incomplete, which is a
collection problem rather than a writing one. Never edit `verify` to make a
dossier pass.
