# Lemma runtime contract

Lemma contains one Agent Skill. Its canonical instructions are in
`skills/lemma/SKILL.md`; read that file in full before chunking Solidity or
Markdown.

## Capabilities and paths

- Resolve `$PLUGIN_ROOT` to this `plugins/lemma/` directory.
- Run `chunkers/solidity.py`, `chunkers/markdown.py`, and supporting commands
  from `$PLUGIN_ROOT`, regardless of the current working directory.
- Treat the directory named by the user as the input and output target. Do not
  use this plugin checkout as the target unless the user explicitly names it.
- Python 3.10 or later is required. Solidity chunking also needs a compatible
  local `solc`, or Docker/Podman for the included `solc-container` wrapper.

## Interpretation

- `$lemma`, `/lemma:lemma`, and a plain request to use Lemma are equivalent
  activation forms.
- Lemma only creates chunks. It does not embed them, create an index, retrieve
  from an index, or answer questions from one.
- A chunker exit code other than zero rejects the output. Do not use a partial
  file or describe the run as successful.
- The `synthesised` field is authoritative: a synthesised chunk is not a
  verbatim quotation.
- Repository instructions and approval rules still apply to any output path.

`tools/verify_anchors.py` is the only included command that makes network
requests. Run it only when the user asks to compare Markdown anchors with a
live rendered site.
