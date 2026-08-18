# Troubleshooting

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

## `DuplicateEntry`

The identifier is already used and never released. Choose another.

## `AtCapacity`

The deployment has reached immutable capacity. Use a new deployment.

## `NotAdmin`

The name is misleading: `retire` reuses `NotAdmin` for ownership checks. It means
the caller does not own the entry, not that the caller is not admin.
