# Entries

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

An entry is the registry's unit of state. Its identifier is unique for the
deployment's lifetime and is never reused after retirement.

## Identifier assignment

Callers supply identifiers because the registry does not own their namespace.
Creation reverts with `DuplicateEntry` when an identifier is taken.

## Status transitions

An entry moves through three states.

| Status | Meaning | Set by |
| --- | --- | --- |
| `Pending` | Reserved but not yet usable | Construction only |
| `Active` | Usable | `create` |
| `Retired` | Permanently closed | `retire` |

Transitions are deliberately one-way; `Retired` cannot return to `Active`.

## Capacity

Capacity is immutable and fixed at construction. This trades extension
flexibility for a guarantee: growth after capacity requires a new deployment
and address.
