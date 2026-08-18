# Venue coverage

<!-- marketplace-context:start -->
> **Marketplace context: Probitas.** Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict. Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty. **Current frontier:** Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.
<!-- marketplace-context:end -->

Fifteen venues in the registry, four of them with adapters. The other eleven
still get a row in every dossier, saying plainly that nobody checked. That is
gate 2 doing its job.

[Adding a venue](../../../docs/adding-a-venue.md) covers what each gap is and
what closing one takes. This file is the short form.

Run `python3 scripts/probitas.py venues` for the current state; this file
explains why it looks the way it does.

## What ships

| Venue | Source | Auth |
| --- | --- | --- |
| Wildcat | Public Goldsky subgraph, Ethereum mainnet | none |
| Morpho Blue | `blue-api.morpho.org/graphql`, Ethereum mainnet | none |
| Euler v1 | Canonical proxy log through `mainnet.gateway.tenderly.co` | none |
| Euler v2 | `v3.euler.finance`, Ethereum mainnet event ledger | none |

All four adapters name their chain in the coverage note. Wildcat is deployed on
Plasma as well and Morpho on several chains, and a row that says only `checked`
would let a reader take one chain's silence for all of them.

## What does not, and why

- MetaMorpho vaults: same keyless API as Morpho Blue, not collected; a
  counterparty can appear as a curator, not a borrower.
- Morpho Vaults V2: same API, separate allocation surface.
- Morpho Midnight: different keyless REST API on Base,
  `api.morpho.org/v0/midnight`; fixed maturities.
- Centrifuge: keyless GraphQL at `api.centrifuge.io`, clean introspection, 24
  mainnet pools; needs only an adapter.
- Aave v3: keyless `api.aave.com/graphql` with `userBorrows` and
  `userPositions`; no introspection, but errors name fields.
- Aave v4: live on Ethereum mainnet since March 2026 through the same
  first-party API; v3 and v4 borrowers are one counterparty.
- Maple Finance: answers without introspection or a published schema, so its
  query shape cannot be established without guessing.
- Compound v3: no first-party API answered; The Graph gateway needs a paid key.
- Goldfinch: wound down in June 2026 after defaults; needs a gateway key; its
  record names who did not repay.
- Clearpool: live behind a 403 bot challenge; access needs an agreement, not a
  workaround.
- TrueFi: restructured through a token migration completing May 2026; no public
  endpoint answered.

Six of the eleven need only an adapter. The rest are blocked on somebody else's
key, bot protection or documentation.

## The four venues read differently, and the dossier says so

**Wildcat is undercollateralised.** Nothing stood between the lender and a loss
except the borrower, so a missed reserve ratio is about conduct. This is the
only venue where a borrower chose their own terms and can be measured against
them.

**Morpho Blue is overcollateralised.** The collateral answered the question and
nobody was relying on the borrower's word, so a liquidation says a price moved
and the protocol closed a position. Reporting one as a default would be the
wrong claim about a named company. Bad debt is the exception, and it gets a record of
its own: a liquidation that failed to cover the debt is a loss somebody else
absorbed.

**Euler v1 is overcollateralised and proxy-scoped.** The adapter reads exact
borrow, repayment and liquidation amounts from the canonical mainnet proxy
log. It filters by the indexed borrower, checks every event block hash before
using its timestamp, and reports the finalized RPC boundary.

**Euler v2 is overcollateralised and EVC-scoped.** The adapter reads borrow,
repayment and liquidation events from the V3 ledger, files them under the EVC
owner and retains the touched subaccount. Interest accrual is omitted because
it is not a new draw. Liquidations retain debt and collateral decimals and are
not called defaults.

**Morpho Midnight is fixed-maturity**, which is why it is worth building next.
A maturity is a date by which the money was due, so it is the only venue
outside Wildcat where repayment timeliness has an answer rather than a story
about a price.

## Wildcat, in detail

What the adapter emits, one record per event, each citing its own transaction:

- `market_terms`: reserve ratio, rate, grace period and penalty rate set by the
  borrower.
- `market_standing`: drawn, repaid, penalty interest accrued and current
  delinquency state.
- `borrow`, `repayment`: each draw and repayment.
- `delinquency_entered`: liquidity held against the reserve requirement.
- `delinquency_cured`: recovery time and whether it passed the grace period.
- `withdrawal_batch_expired_unpaid`: a lender requested money and did not get it.
- `market_closed`: the borrower closed the market.

Two readings this adapter gets right and a naive one does not.

`timeDelinquent` is signed and runs negative while a market is healthy. It is
negative on live mainnet markets right now. Read as a duration it invents a
delinquency out of a clean record, so `isDelinquent` is the flag that decides.

A cured delinquency is not a default. A borrower who went short and came back
inside the grace period paid no penalty interest, and the dossier says so, with
the span and the verdict. That distinction is the one a hand-assembled writeup
usually loses, and one of the synthetic fixtures exists to hold it still.

## Morpho Blue, in detail

- `borrow`, `repayment`: each draw and repayment against a Blue market.
- `liquidation`: the collateralised position closed; this is not labelled a default.
- `bad_debt`: liquidation did not cover the debt; lenders lost money.

Repaid and seized are different assets with different decimals, so they carry
their own scales: `token_decimals` for the loan and `collateral_decimals` for
what was taken. One scale for both is a figure wrong by orders of magnitude.

The supply side is ignored on purpose, and the ignored types are listed rather
than assumed. Lending money says nothing about whether someone repays what they
take, but a type in neither table means the venue changed its vocabulary, and
that raises rather than dropping records in silence.

## Coverage over the whole chain

The Wildcat block range starts at the arch controller deployment, block
18686645 on mainnet. The Morpho range starts at 18919623, the earliest market
creation across all 1,727 mainnet markets, taken by paging the API rather than
by trusting an announcement. Before those blocks there was nothing on either
venue to have a history in, so they are the honest lower bounds.

Euler v1 queries the canonical proxy from block 0 through a finalized block.
Euler v2 reports its own complete indexed range on every activity response. The
adapter refuses partial, syncing or category-incomplete coverage and records
the common mainnet range across all requested EVC owners.
