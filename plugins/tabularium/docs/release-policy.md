# Release and supersession policy

A Tabularium release is immutable once published. Keep its `source.json`,
`capture.json`, `events.jsonl` and `coverage.json` bytes at their original
paths and digests. Documentation may point readers to a newer interpretation,
but it must not replace the historical files.

When an adapter, schema or mapping rule changes:

1. give the changed interpretation a new version;
2. build it in a new release directory with a new release identifier;
3. preserve the earlier source, canonical and coverage bytes;
4. state which release is superseded and why;
5. describe changed rows, coverage and semantic assumptions; and
6. let downstream users choose a version rather than silently mixing them.

A correction can reuse source bytes only when their digest is unchanged. A new
capture boundary or corrected raw record is new source evidence and must be
published separately. Offline verification establishes internal consistency,
not publisher identity, authenticity or an independent chain proof.
