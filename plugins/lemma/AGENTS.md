# Lemma runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

Lemma contains one Agent Skill, `chunk`. Its canonical instructions are in
`skills/chunk/SKILL.md`; read it in full before chunking Solidity or Markdown.

## Capabilities and paths

- Resolve `$PLUGIN_ROOT` to this `plugins/lemma/` directory.
- Run `chunkers/solidity.py`, `chunkers/markdown.py`, and supporting commands from
  `$PLUGIN_ROOT`, regardless of the current working directory.
- Use the user-named directory for input and output. Use this checkout only when
  the user names it.
- Require Python 3.10 or later. Solidity also needs compatible local `solc` or
  Docker/Podman for the included `solc-container` wrapper.

## Interpretation

- `$chunk`, `/lemma:chunk`, and a plain request to use Lemma are equivalent.
- Lemma creates chunks only. It does not embed, index, retrieve, or answer.
- Reject output after a non-zero chunker exit. Do not use a partial file or call
  the run successful.
- `synthesised` is authoritative: a synthesised chunk is not verbatim quotation.
- Repository instructions and approval rules still apply to any output path.

## Network access

Only `tools/verify_anchors.py` makes network requests. Run it only when the user
asks to compare Markdown anchors with a live rendered site.
