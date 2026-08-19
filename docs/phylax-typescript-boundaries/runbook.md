# Runbook: Phylax TypeScript boundary checks

## Build order

This topic is one capability. The shared lexer, the three rules, their fixtures,
the application scan and the frontier receipt form one review boundary. Splitting
the lexer from its first consumer would leave an unused module on a green branch
and make neither half demonstrate the held job.

## Step 1: Reuse the Horos lexer and enforce TypeScript boundaries

**Goal.** Add source-local TypeScript checks for unsafe raw HTML, persisted
session credentials and runtime-selected fetch hosts, using Horos's proven lexer
contract without creating a runtime dependency on the separately installed
Horos plugin.

**Entry.** Start from `b95f332379a9ed9fdacbbbd26fc194eb93ad757a` on
the controller's run branch `fiat/extend-the-lint-to-the-typescript-surface-coveri`.
The validation copy of `wildcat-app-v2` is read-only at
`9b8b6d5d6db06428c5b539f267623277b65315cd`.

**Exit.** The step is complete when all of the following commands exit zero,
the app command prints `clean`, and the final status command prints nothing:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_typescript_lexer
python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py .hexaemeron/validation/wildcat-app-v2
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
git -C .hexaemeron/validation/wildcat-app-v2 status --porcelain
```

The shared lexer copy retains Horos provenance and the source offsets, span
kinds and error behaviour used by `lex(source)`. The Phylax checker emits
`P005`, `P006` and `P007` for the unsafe fixtures defined in the study, preserves
`P000` through `P004`, applies reason-bearing TypeScript suppressions, and keeps
text and JSON output compatible. The committed study and runbook describe the
source-local limit. `SKILL.md` describes the expanded mechanical subset. The
Phylax ledger advances exactly once under `VERSIONING.md` and records either one
evidenced next job or `None -- mature`.

**Files.** Create or change only these planned paths, plus audit and pull-request
artefacts required by later Fiat phases:

- `plugins/hexaemeron/lib/typescript_lexer.py`
- `plugins/hexaemeron/skills/phylax/scripts/phylax.py`
- `plugins/hexaemeron/tests/test_typescript_lexer.py`
- `plugins/hexaemeron/tests/test_phylax_checker.py`
- `plugins/hexaemeron/skills/phylax/SKILL.md`
- `plugins/hexaemeron/skills/phylax/EVOLUTION.md`
- `docs/phylax-typescript-boundaries/study.md`
- `docs/phylax-typescript-boundaries/runbook.md`

If the repository's import layout requires an empty
`plugins/hexaemeron/lib/__init__.py`, it is part of the shared-module scaffold.
Do not change Horos source, the pinned application, CI, dependencies or vendored
files.

**Tests.** Add a focused shared-lexer test module derived from Horos's lexer
fixtures. It must cover complete span reconstruction, strings, comments, nested
templates, regex versus division and unterminated input. Extend the Phylax test
module with at least one unsafe fixture and two safe neighbours for each of
`P005`, `P006` and `P007`, TypeScript suppression cases, exact finding lines,
secret-free text and JSON output, and a mixed Python/TypeScript invocation.
The current Hexaemeron suite has 135 test methods and the root suite has 24;
both totals must stay at or above those baselines and every test must pass.

## Step checks

Protasis runbook checks: 10 of 10 satisfied. The study answers all seven study
items; assumptions and checkable criteria are recorded; the chosen design names
its source-copy trade; always, ask-first and never boundaries are concrete; the
single step has goal, entry, exit, files and tests; every exit names a command;
the step provides its own scaffold and demonstration; dependency order is
trivial; and no module decomposition was required.
