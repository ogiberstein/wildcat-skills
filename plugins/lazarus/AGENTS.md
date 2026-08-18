# Lazarus runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence. **Current frontier:** Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented.
<!-- marketplace-context:end -->

Lazarus has one Agent Skill:

- `lazarus`: read `skills/lazarus/SKILL.md` in full to capture, verify or
  replay a finite historical Ethereum fixture.

That `SKILL.md` is the only canonical instruction document. Do not add a
sibling browsing README.

## Translate tool names by capability

Map canonical tool names to these local capabilities:

- `Read`: read the named file completely or at the stated range.
- `Write` or `Edit`: create or patch the named file.
- `Bash`: run the command and inspect its exit status.
- `Glob`, `Grep`, or `find`: enumerate or search the stated pattern.
- `AskUserQuestion`: ask through structured UI or concise text.

Tool names are capabilities, not required API identifiers. Preserve arguments,
ordering, output files, and exit codes. A non-zero exit means failure.

## Resolve placeholders

- `$SKILL_DIR` is the active `SKILL.md` directory unless it says otherwise.
- `$PLUGIN_ROOT` means this `plugins/lazarus/` directory.
- `$PLUGIN_ROOT/scripts/lazarus.py` implements format validation, finite
  capture, manifest construction, offline verification, and exact loopback replay.
- `lazarus:lazarus`, `/lazarus:lazarus`, and `$lazarus` are aliases for the
  canonical skill above.

## Network and side effects

Only `capture` uses the network, and only through the explicit RPC URL. It
brackets one fixed block, verifies proofs before atomic finalisation, and drops
provider error prose. Format validation, manifest construction, and fixture
verification stay offline. `build-manifest` writes only `manifest.json` under
the explicit fixture root. `verify` checks schemas, safe paths, canonical
manifest bytes, sizes, SHA-256 digests, the header, EIP-1186 account and storage
proofs, proved fields, and captured code. `replay` verifies before binding
loopback and has no provider, proxy or fallback.

## What this skill must refuse

- No moving block: resolve or reject `latest` and `pending` before writing the
  effective plan.
- No proof claim for ordinary RPC results; logs, receipts, calls, and traces
  remain recorded evidence.
- No silent live fallback. An uncaptured replay request is a visible miss.
- No secret persistence. Provider URLs, headers, credentials, and raw provider
  errors do not enter a fixture or its diagnostics.
- No unsafe fixture path. Absolute paths, parent traversal and symlinks are
  rejected.
- No canonical-chain claim from a self-consistent header; the expected block
  hash needs external provenance.
- No proof claim for an account, storage slot or code blob unless the current
  `verify` command checked it against the captured header state root.

If capture, verification, replay, or a test did not run, say so and do not
describe it as successful.
