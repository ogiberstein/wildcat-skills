# Writing a law

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

Seven steps cover the six required parts. A law with fewer is refused by
`python3 scripts/pandects.py check`, which names the missing part rather than
the file.

## 1. Decide what shape it is

Ask whether a single state can violate it.

Conservation can: the sums agree or they do not, and no history is needed. That
is a `Law`, and it reads one target.

Accrual cannot. Debt falling without payment is invisible in any one state,
however wrong that state is, because the violation is in the transition. That
is a `PairLaw`, and it judges two `Observation`s.

Three pair laws compare a system with its past. One compares two systems that
start identically and advance over the same span by different routes. State
which pair the law expects.

## 2. State it in terms a law may read

`ICreditObservables`, and `IWithdrawalQueueObservables` if it needs a
withdrawal queue. Nothing else, ever.

"Debt never decreases between repayments" cannot be checked: no observable
says a repayment happened. A law asking the harness would be about the harness.
Instead require held assets to rise by at least the debt fall, which separates
a repayment from a write-off from outside.

Check the statement against the sound reference before writing any Solidity.
Two laws in the accrual family were written, checked, and found false of a
correct system before a line of them existed.

## 3. Write the component

It returns `(bool held, string detail)` and never reverts to mean violated.

A campaign uses `fail_on_revert = false` because valid credit calls often
revert. A reverting law therefore gives no verdict. The checker refuses
`require`, `assert` and `revert` in a component.

Sums go in an `unchecked` block with the overflow reported as a violation. In
0.8 an overflow reverts, and a law that overflowed would fall silent exactly
where the numbers went furthest wrong.

Name the compared quantities in `detail` for the reader returning six months
later.

## 4. Write the specimen

A contract that breaks this law and no other, inheriting from `Sound` so the
defect is the diff rather than a paragraph claiming there is one. Say
"deliberately broken" in it; the checker looks for those words, because a
broken credit contract that does not say so gets copied.

A specimen that breaks two laws proves neither. The diagonals in
`test/Corpus.t.sol` and `test/Pairs.t.sol` reject it. Use a compensating move to
keep other laws satisfied: the write-off specimen charges itself against
accrued fees, so conservation holds while borrower debt disappears.

## 5. Reduce the failure

Write a deterministic replay under `test/counterexamples/`, with no fuzzer,
seed or engine. Check the hand reduction against the engines: Echidna reduced
two conservation cases from a hundred units to one.

Assert the intermediate quantities, not just the verdict. A counterexample that
only asserts the law fires stops being evidence the moment somebody changes the
specimen.

## 6. Say where it applies, and what it costs

The applicability carries the accounting model, the assumptions and the
observables required. Write the assumptions that would make the law false if
they did not hold, not the ones that sound careful.

Bounds are `exact` or an object naming the arithmetic that produces the
tolerance. An epsilon chosen because it made a test pass is the thing being
refused. The corpus has one tolerance, and it reads: linear accrual on
principal truncates once per step, so `n` steps and one step over the same span
differ by at most `n - 1`.

## 7. File it

Add the entry to `catalogue/pandects.json` and the rendering to
`docs/catalogue.md`. A component in `src/laws/` that no entry claims is a
finding, and so is a document that names a law the catalogue does not have.

Extend `src/campaigns/Specimens.sol` so Echidna and Medusa reach the specimen
under both prefixes, then run both engines.
