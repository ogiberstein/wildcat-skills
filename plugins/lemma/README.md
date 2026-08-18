# Lemma

<!-- marketplace-context:start -->
## In one line

Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text.

**Try something else when.** It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent.

**Current frontier.** Callable-surface ABI validation does not independently check return types or state mutability.

**Next Fiat job.** Use /hexaemeron:fiat to make callable-surface ABI validation cover return types and state mutability as well as names and input types, with any divergence rejecting the output. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Lemma turns Solidity compiler inputs and Markdown documents into one JSONL
schema with source data that separates quotation from assembled text.

It does not embed, index, retrieve, or answer. Python 3.10 or later is the only
runtime dependency. Solidity also needs `solc`; Docker or Podman can run the
pinned compiler through the included wrapper.

The `chunk` skill is `lemma:chunk` (`/lemma:chunk` in Claude Code). It names the
operation. `lemmatise` already means reducing words to dictionary forms in
natural-language processing, which Lemma does not do.

## Solidity

Pass one or more solc standard JSON input files:

```bash
python3 chunkers/solidity.py \
  --input path/to/standard-input.json \
  --solc ./solc-container \
  --include 'src/**' \
  --out chunks.jsonl
```

Use `--solc solc` for a local compiler. Add `--expect-solc 0.8.25` to reject any
other version.

## Markdown

Pass a document root and, for GitBook documentation, its `SUMMARY.md`:

```bash
python3 chunkers/markdown.py \
  --root docs \
  --summary SUMMARY.md \
  --exclude SUMMARY.md \
  --out chunks.jsonl
```

Pass `--summary ''` without GitBook navigation. Use `--exclude` for agent
instructions, generated pages, or anything else outside the corpus.

Both commands validate before writing. Reject the JSONL after a non-zero exit.

## Output

[`schema.py`](schema.py) defines `Chunk` and its text fields:

- `display_text`: source text used for quotation;
- `model_text`: text prepared for model context;
- `embed_text`: text prepared for embedding; and
- `synthesised`: true for assembled `display_text`, which is not verbatim.

The calling pipeline can add build provenance with `schema.stamp()`.

## Checks

Run the standard-library tests from `plugins/lemma`:

```bash
python3 tests/test_markdown.py
python3 tests/test_solidity.py
```

Compiler-dependent tests are opt-in with
`python3 tests/test_solidity.py --solc ./solc-container`.

[`INVARIANTS.md`](INVARIANTS.md) records guarantees, limits, and the reproducible
baseline. `baseline/regenerate` rebuilds it.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
