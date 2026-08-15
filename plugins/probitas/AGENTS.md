# Probitas runtime contract

Probitas contains one Agent Skill. Select from this table, then read the chosen
`SKILL.md` in full.

| Skill | Canonical instructions | Select when |
| --- | --- | --- |
| `probitas` | `skills/probitas/SKILL.md` | Build a sourced dossier on what a counterparty did across on-chain lending venues |

`skills/probitas/README.md` is a copy of that file, kept identical so the
directory renders when browsed. Read either; a test fails if they diverge.

## Translate tool names by capability

The canonical skill was written for hosts that name their tools. A local agent
must map those names to equivalent capabilities:

| Instruction term | Required capability |
| --- | --- |
| `Read` | Read the named file completely or at the stated range |
| `Write` or `Edit` | Create or patch the named file |
| `Bash` | Execute the command in a shell and inspect its exit status |
| `Glob`, `Grep`, or `find` | Enumerate or search files with the stated pattern |
| `AskUserQuestion` | Ask the stated question through structured UI or concise text |

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, output files and exit codes when using an equivalent local
tool. `verify` exiting non-zero means the dossier does not ship; do not report a
run as clean when it exited 1.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`, unless
  that file defines it differently.
- `$PLUGIN_ROOT` means this `plugins/probitas/` directory.
- The tool's own commands are relative to `$PLUGIN_ROOT`, so
  `scripts/probitas.py` resolves there and not in the user's target repository.
- Names such as `probitas:probitas` and `/probitas:probitas` are logical
  aliases. Load the canonical path from the table above.

## Network and side effects

Without `--fixtures`, `collect` makes outbound requests to public venue APIs.
It sends the addresses it was given and nothing else, and it needs no
credential for either shipped venue. Ask for whatever approval the runtime or
the target repository requires before running it against a live counterparty,
and prefer a fixture directory when demonstrating rather than investigating.

`collect`, `render` and `verify` write only where `--out` points. Nothing else
in the plugin writes outside its own directory.

## What this skill must refuse

These are properties of the tool rather than reminders, and a local agent must
not route around them:

- No personal data. The evidence schema rejects a value key that names a
  person, so an adapter cannot record one. Do not add a field to carry one, and
  do not answer a question about which individual controls an address.
- No unsourced assertion. A record cannot exist without a transaction hash, a
  URL or a document reference. If a figure has no record behind it, drop the
  claim rather than softening it.
- No score without a rubric printed beside it. This version emits none.
- No silent gap. A venue nobody checked gets a row saying so. Never present an
  unchecked venue as a clean one, and never delete a coverage row to tidy a
  document.

If a lint, a test, a network call or a gate did not run, say so plainly and do
not describe its result.
