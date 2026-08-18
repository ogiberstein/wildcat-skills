---
name: chunk
description: Turn Solidity solc standard JSON inputs or Markdown document trees into validated JSONL chunks with source locations and separate quotation, model, and embedding text. Use when asked to run Lemma, invoke lemma:chunk, prepare Solidity or Markdown for retrieval, generate citation-aware chunks, or inspect Lemma output. Do not use it to embed, index, retrieve, or answer from the chunks.
metadata:
  version: "0.1.0"
---

# Chunk with Lemma

## Frontier

Chunk owns its chunking and validation frontier, not Hexaemeron's delivery or
Solidity frontier. [EVOLUTION.md](EVOLUTION.md) holds its version, target, next
job, and maturity. Do not run or recommend another pass once it is mature.

<!-- marketplace-context:start -->
## Where this sits

Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text.

**Use another tool when.** It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent.

**Current frontier.** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

Create chunks and stop at JSONL unless the user separately asks another system
to consume it.

Set `$PLUGIN_ROOT` to `$SKILL_DIR/../..` and run bundled commands there.

## Choose the chunker

- Use `chunkers/solidity.py` for one or more solc standard JSON input files.
- Use `chunkers/markdown.py` for a directory of Markdown documents.
- To inspect or validate existing JSONL, read `schema.py` and apply `Chunk` and
  `validate()`. Do not rerun a chunker without source input.

Read target-repository instructions before writing. Keep generated JSONL outside
the plugin unless that repository is the named target.

## Chunk Solidity

With Docker or Podman, prefer the pinned compiler wrapper:

```bash
cd "$PLUGIN_ROOT"
python3 chunkers/solidity.py \
  --input /absolute/path/to/standard-input.json \
  --solc ./solc-container \
  --include 'src/**' \
  --out /absolute/path/to/chunks.jsonl
```

Repeat `--input` for compilation units and `--include` for source patterns. Use
`--expect-solc VERSION` for a pinned corpus. Use `--solc solc` only by request,
or when no container runtime exists and the local version is acceptable.

The first container run may fetch the image; the compiler itself has no network.

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

Pass `--summary ''` without GitBook navigation. Add `--exclude` for every
instruction file, generated directory, or unrelated subtree outside the corpus.
For compatible manifest exclusions, pass `--manifest` and choose `--source`.

Markdown anchors follow GitBook. Check another renderer before claiming parity.

## Accept the result

Both chunkers validate before writing. Accept JSONL only after exit zero and a
report that the requested file was written. Otherwise report the named error;
do not use earlier or partial output.

Preserve these distinctions downstream:

- `display_text` holds source text used for quotation;
- `model_text` holds text prepared for model context;
- `embed_text` holds text prepared for embedding; and
- `synthesised: true` marks assembled, non-verbatim text.

Read [`INVARIANTS.md`](../../INVARIANTS.md) before changing chunkers, judging a
guarantee, or investigating output. Run both test files after code changes.
