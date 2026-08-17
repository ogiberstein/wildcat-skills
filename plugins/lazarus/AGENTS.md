# Lazarus runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence. **Current frontier:** Preservation-pipeline integration and an Ariadne state-fixture predicate remain follow-on work.
<!-- marketplace-context:end -->

Lazarus contains one Agent Skill. Select it from this table, then read the
chosen `SKILL.md` in full.

| Skill | Canonical instructions | Select when |
| --- | --- | --- |
| `lazarus` | `skills/lazarus/SKILL.md` | Capture, verify or replay a finite historical Ethereum fixture |

`skills/lazarus/README.md` is a copy of that file, kept identical so the
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
- `$PLUGIN_ROOT` means this `plugins/lazarus/` directory.
- The command path is `$PLUGIN_ROOT/scripts/lazarus.py`. The current build
  implements format validation, finite capture, manifest construction and
  offline verification and exact loopback replay.
- Names such as `lazarus:lazarus`, `/lazarus:lazarus` and `$lazarus` are
  logical aliases. Load the canonical path from the table above.

## Network and side effects

`capture` is the only networked command. It uses only the explicit RPC URL,
brackets one fixed block, verifies proofs before atomically finalising output
and discards provider error prose. Format validation, manifest construction
and fixture verification reach no network. `build-manifest` writes only
`manifest.json` beneath its explicit fixture root. `verify` checks schemas,
safe paths, canonical manifest bytes, component sizes and SHA-256 digests,
then verifies the header, EIP-1186 account and storage proofs, proved response
fields and captured code. `replay` verifies before binding loopback.
It has no provider, proxy or fallback.

## What this skill must refuse

- No moving block in an effective plan. `latest` and `pending` are resolved or
  rejected before the stored plan is written.
- No proof claim for an ordinary RPC result. Logs, receipts, calls and traces
  remain recorded evidence.
- No silent live fallback. An uncaptured replay request is a visible miss.
- No secret persistence. Provider URLs, headers, credentials and raw provider
  errors do not enter a fixture or its diagnostics.
- No unsafe fixture path. Absolute paths, parent traversal and symlinks are
  rejected.
- No canonical-chain claim from a self-consistent header alone. The expected
  block hash needs an external provenance record.
- No proof claim for an account, storage slot or code blob unless the current
  `verify` command checked it against the captured header state root.

If capture, verification, replay or a test did not run, say so plainly and do
not describe its result as successful.
