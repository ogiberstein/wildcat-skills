# The dataset predicate

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

Type URI: `https://ariadne.wildcat.finance/dataset/v1`.

Its subject is a released set of data files. What it adds to the core block is
the part that makes a dataset release checkable rather than merely published:
which inputs it was derived from, which tool turned them into the released
files, what interval it claims to describe, and where inside that interval it
describes nothing.

This document states the shape. The gates are enforced in
`scripts/ariadne_lib/predicates/dataset.py`, the published shape is
`schemas/dataset-v1.json`, and the two are held together by
`tests/test_schema_drift.py`.

## The fields

| Field | Holds | Checked by |
| --- | --- | --- |
| `producer` | The tool, its version, the argv that ran, and a digest over its parameters | gate 2 |
| `inputs` | Each upstream input: name, locator, and either a digest or a recorded absence | gate 2, inputs check |
| `dataset_subjects` | Each released file: name, path, digest, record count | gate 2 |
| `coverage` | The dimension, its bounds, and the gaps inside them | coverage check |
| `deltas` | Baseline and current sides, and the record-level differences | gate 5 |
| `claims` | What was checked, against which subject digest | gates 1 and 3 |
| `commands` | What was run, and whether a replay must match byte for byte | gates 3 and 6 |

Every field is required. There is no optional block: a release derived from
nothing upstream records an empty `inputs` array, which says the question was
asked and answered.

## Gate 2 here: the environment is recoverable

Recoverable means somebody else can produce the same files. That takes the
producing tool and its version, the argv that ran, a digest over the parameters
it was given, and a digest or a recorded absence for every input. Each
`dataset_subjects` digest must also be a subject of the statement, so the
predicate cannot describe files the statement does not cover.

A tool name and a version on their own fail, for the same reason a bare compiler
version fails in the Solidity release predicate: without the parameters nobody
gets the same bytes back.

## Gate 5 here: a comparison names both sides

The baseline is a named prior release with a digest, or `null` with a reason. A
first release carries the null and the reason rather than leaving the block out,
because an absent `deltas` block reads as nothing having changed instead of as
there being nothing to change from.

Record-level differences recorded against a null baseline fail. There was no
prior release to differ from.

## The coverage check

Not one of the seven. It is gate 3's rule applied to the field a dataset can
most easily use to mislead: an interval printed with no gaps reads as complete.

- `dimension` and both bounds are required.
- `start` must not exceed `end`.
- Every gap must sit inside the bounds, and must carry a reason.
- Gaps must not overlap each other.
- An absent `gaps` key fails. An empty array passes, and asserts that the
  producer looked.

## The inputs check

An input carries a digest, or a disposition from the core vocabulary with a
reason. An input with neither fails: a locator on its own records nothing about
what was read, and nothing about whether it could be read at all.

## What this predicate does not do

Nothing here reaches a network. An input that cannot be digested from disk is
recorded absent with a reason rather than fetched. Nothing signs, and nothing
reports a signature as checked.
