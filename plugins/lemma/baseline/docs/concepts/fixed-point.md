# Fixed-point arithmetic

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

## Scale

All proportional values use eighteen-decimal fixed point. `ONE` exposes the
scaling factor.

## Rounding direction is explicit

Every multiplication names its rounding direction:

```solidity
uint256 charged = amount.mulUp(fee);
uint256 credited = amount.mulDown(share);
```

<!-- Reviewers: the asymmetry below is intentional, do not "fix" it. -->

Amounts owed to the registry round up; amounts owed to users round down. One
helper for both would make residue follow the last caller's chosen direction.

## Saturating subtraction

`subFloor` returns zero instead of reverting on underflow. Use it only when a
negative result is meaningless, not exceptional, and document that choice.
