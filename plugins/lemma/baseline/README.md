# Baseline corpus

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

A small invented corpus produces the numbers in
[`../INVARIANTS.md`](../INVARIANTS.md). An unreproducible baseline is not evidence.

Everything here is fabricated: four Solidity sources describe a nonexistent
registry and nine Markdown documents describe its use. Nothing corresponds to a
deployed system. The prose exists for chunking, not reading.

```bash
baseline/regenerate --solc /path/to/solc
```

Each run builds `standard-input.json` from `solidity/src/`; committing its copied
sources would permit silent drift. The chunker could then read stale code and
cite bytes absent from the named file. `standard_input.py` builds the input and
serves as the shortest example of its format.

## What it is chosen to exercise

Solidity covers an interface, abstract base, concrete inheritor, and library;
natspec on declarations and parameters; custom errors, event, enum, struct,
modifier, public immutable and constant getters; an `@inheritdoc` override; and
`using ... for`. These exercise surface chunks, inheritance, and ABI checks.

Markdown is a GitBook-shaped tree: `SUMMARY.md` has three nav sections and a
nested entry; documents include varied headings, fenced code, an HTML comment,
a table, and standalone bold troubleshooting boundaries. `SUMMARY.md` is
navigation and remains outside the chunked set.

## The compiler is gated

The `INVARIANTS.md` figures use solc 0.8.25, the version resolved by the
`solc-container` digest. `regenerate` defaults to `--expect-solc 0.8.25`, so any
other compiler fails non-zero instead of printing different numbers.

Change the `regenerate` default and recorded figures in the same commit as the
`solc-container` digest.

```bash
baseline/regenerate --expect 0.8.26   # record against a different compiler
baseline/regenerate --no-expect       # see what an ungated run produces
```

## Regenerating after a change

Move the baseline in the same commit when a chunker intentionally changes its
numbers. An unexpected change is the signal this corpus provides.
