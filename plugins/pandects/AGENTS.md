# Pandects runtime contract

Pandects contains one Agent Skill. Select from this table, then read the chosen
`SKILL.md` in full.

| Skill | Canonical instructions | Select when |
| --- | --- | --- |
| `pandects` | `skills/pandects/SKILL.md` | Check a credit protocol against executable laws, or write a new law for the corpus |

`skills/pandects/README.md` is a copy of that file, kept identical so the
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
tool. A non-zero exit from a check means the check failed; do not report a run
as clean when it exited 1.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`, unless
  that file defines it differently.
- `$PLUGIN_ROOT` means this `plugins/pandects/` directory.
- The tool's own commands are relative to `$PLUGIN_ROOT`, so
  `scripts/pandects.py` resolves there and not in the user's target repository.
- Names such as `pandects:pandects` and `/pandects:pandects` are logical
  aliases. Load the canonical path from the table above.

## Network and side effects

Nothing here reaches the network, and the Solidity has no dependency to fetch.
`forge` compiles and runs the corpus locally; `pandects.py` reads the catalogue
and prints.

Running the corpus against a target compiles and executes that target's code in
a local EVM. Treat a target repository as the user's, and obey its own
instructions before writing anything into it.

## What this skill must refuse

These are properties of the tool rather than reminders, and a local agent must
not route around them:

- No law without its six parts. A component, a specimen it catches, a reduced
  counterexample, an applicability contract, justified bounds, and an
  identifier matching its catalogue entry. The checker enforces this; do not
  add a law by editing the catalogue alone.
- No implementation names in a law. Laws read `ICreditObservables`, and the
  three that need a withdrawal queue read `IWithdrawalQueueObservables` on top
  of it. A protocol's own names belong in the adapter that implements them.
- No revert as a verdict. A law returns `(bool held, string detail)`, whether it
  judges one state or a pair of observations, because a revert under
  `fail_on_revert = false` carries no verdict at all.
- No pair law held on a pair it cannot judge. A pair spanning real time is a
  state of the world and the law holds; a pair nobody could have meant is a
  mistake by whoever built it and the law refuses. Never the other way round.
- No campaign reported under an engine that did not run. Name the engine, its
  configuration and its seed, or report nothing. An engine that did not run is
  absent from a search record; a value nobody could read is absent rather than
  null; a campaign killed by its timeout is neither passed nor failed.
- No pair law reported over a target nobody routed calls through. The observing
  adapter does not offer them, and a driving adapter that recorded no call has
  judged nothing however its properties read. `recordedCalls` is what tells the
  two apart.
- No tolerance without its arithmetic. An epsilon that made a test pass is the
  thing being refused.
- No claim that a law is true. The corpus says a law held under a search that
  is described; it does not say the protocol is safe.

If a lint, a test, a compile or a campaign did not run, say so plainly and do
not describe its result.
