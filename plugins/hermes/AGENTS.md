# Hermes runtime contract

Hermes is one Agent Skill. Its canonical instructions are in
`skills/hermes/SKILL.md`; read that file in full before working on Solidity gas
usage. The `README.md` beside it is for repository browsing and is not the
instruction source.

## Capabilities and paths

- The agent needs text-file read and write access plus a shell in the user's
  target repository.
- The target needs Git, Python 3, Foundry, and a clean working tree. If one is
  absent, follow the refusal in `SKILL.md` rather than estimating a result.
- Resolve `scripts/hermes.py` and `references/optimisation-catalogue.md` from
  `skills/hermes/`, regardless of the current working directory.
- Run the harness in the target Foundry repository. Do not use this plugin
  checkout as the target unless the user explicitly names it.

## Interpretation

- `$hermes`, `/hermes:hermes`, and a plain request to use Hermes are equivalent
  activation forms.
- Shell snippets describe commands to execute, not text to paraphrase.
- A non-zero harness exit is a rejected gate. Do not continue, weaken a check,
  or report the candidate as accepted.
- `result.json` with status `accepted` and exit code 0 is the only acceptance
  signal. Report the evidence directory with the result.
- Repository issue, branch, review, and approval rules still apply before
  Hermes changes target source.
