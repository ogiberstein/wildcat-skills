# The corpus against a Wildcat market

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

`WildcatMarketModel.sol` is a reduced model, not the market contracts. It keeps
batched withdrawals, an untouchable reserve, delinquency and a penalty rate.

Ten laws. Seven apply without qualification, and one did not until this model
was corrected. Three do not. This integration records what the design
promises, not only what a law needs.

Echidna found one after this document had claimed the law held, against the
shipped adapter. That is evidence for testing the corpus on a real design.

## The seven

| Law | Holds | Because |
| --- | --- | --- |
| `conservation/value-conserved/v1` | yes | Every operation moves value between two sides, including accrual, which raises debt and claims together |
| `conservation/reserves-backed-by-claims/v1` | yes | A market cannot earmark more than lenders are owed |
| `conservation/held-assets-partitioned/v1` | yes | Borrowable liquidity is derived, and the required reserve comes out of it before the borrower is offered anything |
| `claims/reserves-cover-payable/v1` | yes | Payability is derived from what has actually been set aside, so a delinquent market declares fewer batches payable rather than lying about them |
| `accrual/debt-falls-only-against-payment/v1` | yes | Debt falls only in `repay`, against assets arriving |
| `accrual/no-accrual-at-rest/v1` | yes | Interest accrues in `advance` and nowhere else, and borrowing removes from held assets what it adds to debt |
| `claims/pooled-claims-cover-open-batches/v1` | yes, once corrected | The fee is capped against what the open batches are owed; it was capped against the earmark, and that let it reach value already promised. See below |

## The fee cap, and the law that found it

`claims/pooled-claims-cover-open-batches/v1` holds only after the model
correction recorded here.

The model capped a protocol fee against `reserved()`, the queue earmark. An
earmark cannot exceed holdings. A solvent market earmarks its whole queue, but
an illiquid market earmarks only what it has. The gap became a fee taken from
value promised to waiting lenders. `delinquent` already said the quantities
diverge when the market is in trouble; the fee cap ignored it.

A market holding 200 against one batch owed 1000 permitted a fee of 800. Every
one of the other nine laws held on the state that left behind: the books balance,
because the value moved from claims to fees; reserves stay within claims; the
partition holds; payability is still derived from the reserves, so the market
never declared more payable than it had; debt never moved, so neither accrual law
had anything to say; and each batch kept its own recorded amount, so nothing was
written down. Only the pool behind those amounts had shrunk.

The cap now measures open-batch debt. The same market permits no fee because
nothing is unrequested. The state was found before the law was written.

This is a correction to a reduced model. What the deployed market contracts do
about fees while a batch is outstanding is not read here and is not established
either way by this document.

## Batch granularity, and what the ordering law means here

`claims/queue-order-preserved/v1` holds, and reading it as a per-lender promise
would be wrong.

A Wildcat market pools same-cycle requests and pays each batch pro rata. No
lender inside a batch is ahead of another; batches settle oldest first.

The law says no claim is paid while an older claim is still owed something. At
batch granularity that is exactly what the design guarantees, and the extension
here exposes batches rather than lenders for that reason. At lender granularity
it would be false, and trivially: a pro-rata payment leaves every lender in the
batch partly paid.

The unit decides the result.
`test_a_batch_paid_pro_rata_does_not_break_the_ordering` asserts that the
pooled case is not a queue jump.

## An open batch is not yet a recorded claim

`claims/recorded-claim-never-shrinks/v1` does not hold over an open batch, and
does hold over a closed one.

The law says a recorded claim keeps its owed amount. A Wildcat batch
accumulates while it is open: a second request in the same cycle joins the batch
and the amount owed on it rises. Echidna found that against
`WildcatMarketCampaign` within a few hundred calls, and the property is expected
to fail there.

For individual claims, a later amount change is the defect. In a batched
design, an open batch is still being assembled. The law starts when any payment
closes the batch; its amount is then fixed.

`test_an_open_batch_grows_and_the_claim_law_refuses_it` and
`test_a_closed_batch_satisfies_the_claim_law` are the two halves, asserted
rather than described.

Whether the law should be relaxed to say a recorded claim is never written
*down* -- which would still catch the specimen it was built for, and would hold
over an open batch -- is a real question and not one this integration should
answer on its own. It is recorded as a lead in `audit/AUDIT.md`.

## Path independence, and the condition on it

`accrual/path-independent/v1` holds while the market is solvent and stops
holding once penalty accrual is running.

Base interest is linear on principal, so route splitting changes cost only
within the law's derived bound.

The penalty is different. It runs only once the market has been delinquent for
longer than the grace period, and the grace timer advances when the market is
poked. A market that crosses into delinquency mid-span therefore owes a
different penalty depending on how often somebody updated it: advanced once
across a year from a fresh delinquency, it pays no penalty at all, because the
grace was unspent at the moment the charge was computed. Advanced in two halves,
it pays the penalty for the whole second half.

This path dependence is outside the law once the penalty rate is on.
`test_a_penalised_market_is_not_path_independent` watches it happen rather than
describing it, and `test_a_solvent_market_is_path_independent` holds the other
half.

## Delinquency arrives with the request

Borrowing cannot make a market delinquent: the required reserve is
subtracted before the borrower is offered anything. What makes a market
delinquent is a lender asking to leave a market whose liquidity has already gone
out of the door, and no amount of care at borrow time prevents that.

This is why the model bounds a withdrawal request by the lender's claims rather
than by what the market holds. A model that refused the request would have no
way to reach the situation the whole design is built around.

## What is not modelled

Per-lender accounting, so nothing here says anything about one lender's share of
a batch. The scaling index, so amounts are in the asset throughout. Market
expiry, borrower authorisation, the sentinel, and every access control. Each of
those matters to a market and none of them changes what the laws read.
