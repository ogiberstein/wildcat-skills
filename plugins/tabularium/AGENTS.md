# Tabularium runtime contract

Tabularium contains one Agent Skill. Select from this table, then read the
chosen `SKILL.md` in full.

| Skill | Canonical instructions | Select when |
| --- | --- | --- |
| `tabularium` | `skills/tabularium/SKILL.md` | Build or verify a preserved, sourced ledger of on-chain credit events |

`skills/tabularium/README.md` is a copy of that file, kept identical so the
directory renders when browsed. Read either; a test fails if they diverge.

## Translate tool names by capability

The canonical skill may name host tools. A local agent must map them to
equivalent capabilities:

| Instruction term | Required capability |
| --- | --- |
| `Read` | Read the named file completely or at the stated range |
| `Write` or `Edit` | Create or patch the named file |
| `Bash` | Execute the command in a shell and inspect its exit status |
| `Glob`, `Grep`, or `find` | Enumerate or search files with the stated pattern |
| `AskUserQuestion` | Ask the stated question through structured UI or concise text |

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, output files and exit codes when using an equivalent
local tool. A non-zero exit means the requested operation did not succeed.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`, unless
  that file defines it differently.
- `$PLUGIN_ROOT` means this `plugins/tabularium/` directory.
- The tool's own commands are relative to `$PLUGIN_ROOT`, so
  `scripts/tabularium.py` resolves here and not in the user's target
  repository.
- Names such as `tabularium:tabularium` and `/tabularium:tabularium` are
  logical aliases. Load the canonical path from the table above.

## Network and side effects

The plugin reaches no network. `build` reads the source and capture manifest
named by its flags, then writes canonical JSONL and a coverage manifest only
to the named output paths. Every artefact must sit inside the coverage
manifest's directory. `verify` reads those local files, rebuilds expected event
bytes and writes nothing.

## What this skill must refuse

- No path escape. Absolute paths, parent traversal, symlinks and release
  artefacts outside the manifest directory are refused.
- No verification by declared digest alone. `verify` rebuilds canonical bytes
  from the bound source and checks one-to-one source selectors.
- No publisher-authenticity claim. The release is unsigned; offline
  verification proves internal consistency, not publisher identity or
  authenticity.
- No rewriting raw evidence. Each mapping retains the source record beside its
  interpretation rather than replacing it.
- No semantic flattening. Venue-qualified meanings must not be promoted to a
  universal claim about repayment, delinquency or default.
- No identity inference or score. The ledger records sourced events; it does
  not identify people or rate a counterparty.
- No chain-proof claim. The captured block is what the hosted indexer reported;
  neither it nor each event is independently proved against Ethereum here.

If a build, verification, source check or test did not run, say so plainly and
do not describe it as successful.
