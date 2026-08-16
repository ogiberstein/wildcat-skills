# Adding a venue adapter

An adapter translates one venue's preserved records without promoting its
terms into universal credit claims. Start with a small source fixture and keep
the native record attached to every mapped row.

1. **Validate the source.** Define the required collections, field types,
   address and transaction shapes, numeric bounds and duplicate-identifier
   rules. Reject malformed input before writing output.
2. **Define each mapping.** Give every source entity a venue-qualified action,
   canonical family and versioned mapping rule. Explain what the venue means by
   terms such as repayment, cure, default or write-down.
3. **Record provenance.** Set the source kind and contract, entity collection,
   source identifier and selector, adapter name and version, and mapping-rule
   version. One covered source entity must yield one traceable selector.
4. **Declare coverage.** Count the collections mapped as events and every
   unsupported collection present in the source. Add evidence limits and known
   semantic gaps rather than dropping them silently.
5. **Add fixtures and tests.** Include a focused valid fixture plus malformed,
   duplicate, numeric-bound, ordering and coverage-drift cases. Test a
   deterministic repeat build and an offline rebuild from preserved bytes.
6. **Publish a new release.** Add source, capture, canonical and coverage files
   under a new release directory. Do not alter an earlier interpretation.

Review the venue's economic meaning as well as its JSON shape. If a common
family would imply more than the native event establishes, narrow the action
or leave that entity unsupported until the distinction can be represented.
