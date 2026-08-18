# Retiring entries

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

## Access

Only the entry owner may retire it. The admin cannot.

## Effect

Retirement sets `Retired` and emits `EntryRetired`. It does not free the
identifier, reduce the total, or refund the creation fee.

## Why the total does not decrease

The total counts all created entries. Decreasing it would move the capacity
target and let the deployment exceed its stated lifetime bound.
