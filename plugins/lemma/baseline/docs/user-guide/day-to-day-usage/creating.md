# Creating entries

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

## Call

Creation is admin-only. The admin supplies an identifier and amount; the call
returns the charged fee.

## Before you start

Check that the identifier is unused and capacity remains. Both failures revert
instead of returning status, so simulation is the cheapest check.

## What the fee depends on

The fee is a rounded-up proportion of the amount. Changes affect later creations
only because the charge is computed once and not stored.
