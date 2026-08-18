# Hexaemeron runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Hexaemeron.** Hexaemeron runs an explicit, receipted delivery loop and also exposes its fuzzing, audit-readiness, security-review and prose skills on their own. Use Hermes for measured gas work, Pandects for reviewed credit laws, and Lemma when the output needed is source-linked retrieval chunks. **Current frontier:** The bundled Solidity audit suite has not yet been exercised in a published end-to-end Fiat delivery.
<!-- marketplace-context:end -->

Hexaemeron contains these Agent Skills. Read the selected `SKILL.md` in full;
do not start `fiat` merely because another skill matches.

- `fiat`, `skills/fiat/SKILL.md`: explicit requests to start, resume, or report
  a Hexaemeron delivery run.
- `fizz`, `skills/fizz/SKILL.md`: stateful Solidity fuzz suites.
- `fizz-convert`, `skills/fizz/skills/fizz-convert/SKILL.md`: pending
  `PROPERTIES.md` entries to Solidity assertions.
- `fizz-sync`, `skills/fizz/skills/fizz-sync/SKILL.md`: reconcile an existing
  Fizz harness with changed source.
- `x-ray`, `skills/x-ray/SKILL.md`: prepare a Solidity protocol for audit.
- `solidity-auditor`, `skills/solidity-auditor/SKILL.md`: audit Solidity source
  for security findings.
- `imprimatur`, `skills/imprimatur/SKILL.md`: lint shipped prose against the
  banned lexicon.
- `vulgate`, `skills/vulgate/SKILL.md`: change register without changing content.
- `kronos`, `skills/kronos/SKILL.md`: rank eligible frontiers and send the
  best held job through Fiat repeatedly.
- `protasis`, `skills/protasis/SKILL.md`: decide whether a study or runbook is
  buildable before implementation.
- `elenchus`, `skills/elenchus/SKILL.md`: find a failure's cause and guard it
  with a test.
- `phylax`, `skills/phylax/SKILL.md`: harden off-chain inputs, subprocesses,
  fetched hosts, secrets, dependencies, and model output.
- `ephoros`, `skills/ephoros/SKILL.md`: choose diagnostic events, metrics,
  traces, and alerts.
- `metron`, `skills/metron/SKILL.md`: baseline slow work, change one thing,
  remeasure, and keep or revert on the numbers.
- `hypomnema`, `skills/hypomnema/SKILL.md`: record decisions where readers
  will find them.

Each first-party directory named above carries an `EVOLUTION.md` ledger governed
by `skills/VERSIONING.md`. Read the selected skill's ledger before proposing a
frontier run. A `mature` frontier is a hard stop unless a maintainer recorded an
evidenced epoch reopening. Kronos is terminal and excludes itself from selection.

## Translate tool names by capability

Map named host tools to these capabilities:

- `Read`: read the named file completely or at the stated range.
- `Write` or `Edit`: create or patch the named file.
- `Bash`: execute the command and inspect its exit status.
- `Glob`, `Grep`, or `find`: enumerate or search the stated pattern.
- `ToolSearch`: inspect available tools before choosing one.
- `AskUserQuestion`: ask through structured UI or concise text.
- `TodoWrite`: maintain a durable plan with the same states and transitions.
- `Agent` or `Task`: run the role prompt in an isolated agent context.
- Background or parallel calls: start independent work concurrently and wait
  at the named barrier.

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, wait barriers, output files, and stop conditions when
using an equivalent local tool.

If the runtime cannot select the named model family, use its configured model
and say that the requested family was unavailable. Omit unsupported model
arguments. Never claim that Sonnet, Opus, or another model ran when it did not.

If the runtime has no subagent facility, run each supplied role prompt
separately and save each raw result before synthesis. Keep roles separate and
finish every role named by the skill before crossing its wait barrier. Stop
when the requested workflow depends on isolation that the runtime cannot
preserve.

## Resolve placeholders

- `$SKILL_DIR` and `{SKILL_PATH}` mean the directory containing the active
  `SKILL.md`, unless that file defines them differently.
- `$PLUGIN_ROOT` means this `plugins/hexaemeron/` directory.
- `{PROJECT_ROOT}` means the user's target repository, not this plugin
  directory.
- `{SUITE_DIR}` and `{META_DIR}` are relative to `{PROJECT_ROOT}` unless the
  user supplied absolute paths.
- Names such as `hexaemeron:fizz` and `/hexaemeron:fiat` are logical skill
  aliases. Load the local canonical path from the list above.
- Fiat's controller path is relative to the exact active Fiat instruction
  file, never to `{PROJECT_ROOT}` or a GitHub URL.

## Side effects and truthfulness

Read the target repository's instructions before writing. Ask for any approval
the runtime or repository requires. Preserve every fail-closed check in the
canonical skill. If a command, audit role, lint, test, issue write, or push did
not happen, state that plainly and do not create its receipt.
