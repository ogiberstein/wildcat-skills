---
name: lemma
description: Turn Solidity solc standard JSON inputs or Markdown document trees into validated JSONL chunks with source locations and separate quotation, model, and embedding text. Use when asked to run Lemma, prepare Solidity or Markdown for retrieval, generate citation-aware chunks, or inspect Lemma output. Do not use it to embed, index, retrieve, or answer from the chunks.
---

# Lemma

Use Lemma to create chunks. Stop at the JSONL output unless the user separately
asks for another system to consume it.

`$SKILL_DIR` is the directory containing this file. Resolve `$PLUGIN_ROOT` as
`$SKILL_DIR/../..` and run the bundled commands from there.

## Choose the chunker

- Use `chunkers/solidity.py` for one or more solc standard JSON input files.
- Use `chunkers/markdown.py` for a directory of Markdown documents.
- If the request is only to inspect or validate an existing JSONL file, read
  `schema.py` and apply its `Chunk` and `validate()` contract. Do not rerun a
  chunker without its source input.

Read the target repository's instructions before writing output. Keep generated
JSONL outside the plugin directory unless the plugin repository itself is the
named target.

## Chunk Solidity

Prefer the included pinned compiler wrapper when Docker or Podman is available:

```bash
cd "$PLUGIN_ROOT"
python3 chunkers/solidity.py \
  --input /absolute/path/to/standard-input.json \
  --solc ./solc-container \
  --include 'src/**' \
  --out /absolute/path/to/chunks.jsonl
```

Repeat `--input` to merge compilation units and repeat `--include` for more
source patterns. Use `--expect-solc VERSION` when the requested corpus pins a
compiler version. Use `--solc solc` only when the user asks for a local compiler
or the container runtime is unavailable and the local compiler version is
acceptable.

The first container run may fetch the pinned image. The compiler process itself
runs without network access.

## Chunk Markdown

For a GitBook tree:

```bash
cd "$PLUGIN_ROOT"
python3 chunkers/markdown.py \
  --root /absolute/path/to/docs \
  --summary SUMMARY.md \
  --exclude SUMMARY.md \
  --out /absolute/path/to/chunks.jsonl
```

Pass `--summary ''` when the tree has no GitBook navigation. Add an `--exclude`
for every instruction file, generated directory, or unrelated subtree that
must not enter the corpus. When a compatible manifest already declares the
exclusions, pass it with `--manifest` and select its source with `--source`.

Markdown anchors follow GitBook behavior. Do not claim that they match another
renderer without checking that renderer separately.

## Accept the result

Both chunkers validate before writing. Accept the JSONL only when the command
exits zero and reports that it wrote the requested file. On failure, report the
named error and do not use an earlier or partial output.

Preserve these distinctions downstream:

- `display_text` holds source text used for quotation;
- `model_text` holds text prepared for model context;
- `embed_text` holds text prepared for embedding; and
- `synthesised: true` means the chunk is assembled and is not a verbatim quote.

Read [`INVARIANTS.md`](../../INVARIANTS.md) when changing the chunkers, judging a
guarantee, or investigating unexpected output. Run the two bundled test files
after any code change.
