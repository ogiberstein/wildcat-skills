# Contract surface

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

## Registry

Concrete deployment inheriting `RegistryBase`.

### create

Creates an entry. Admin only; reverts on duplicate identifiers or capacity.

### retire

Retires an entry. Owner only.

### setFee

Sets the creation fee. Admin only; applies to the next creation.

## RegistryBase

Abstract storage and access control; never deployed alone.

### entry

Returns an identifier's entry, or a zeroed entry when none exists.

### total

Returns the number of entries ever created.
