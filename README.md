# Wildcat Labs skills

Agent skills written and used by [Wildcat Labs](https://wildcat.finance).

This is where we publish workflows that have earned more than a prompt. Each plugin gets a narrow job, a clear trigger, and whatever scripts, references and tests it needs to make the result checkable. Read a plugin before running it: skills can execute commands and edit source.

## Plugins

### Hermes gas optimiser

[Hermes](./plugins/hermes-gas-optimiser) treats Solidity gas work as a verification problem.

Gas changes are easy to praise and surprisingly easy to get wrong. Hermes takes one optimisation class at a time through a fail-closed Foundry run:

1. Seal a clean baseline with `forge snapshot` and a green `forge test`.
2. Apply exactly one declared optimisation class.
3. Prove the saving with `forge snapshot --diff`, reject every positive delta, and capture `forge test --gas-report`.
4. Run the full test suite again with the pinned fuzz seed, then once more unpinned.
5. Diff storage layouts and method identifiers for every recorded contract. Any layout change to a hook, role provider, proxied contract or other protected contract aborts the run.
6. For unchecked arithmetic that can affect persistent state, asset accounting, external calls, permissions, or rounding, run the existing targeted differential or property test before accepting the candidate.

A candidate only clears Hermes when every gate clears. The run leaves behind `result.json`, command logs, gas comparisons, the Solidity diff, storage layouts and method maps, so the number and the safety case can be reviewed together.

Hermes includes:

- the executable [`hermes.py`](./plugins/hermes-gas-optimiser/skills/hermes-gas-optimiser/scripts/hermes.py) harness;
- a catalogue of [12 optimisation classes](./plugins/hermes-gas-optimiser/skills/hermes-gas-optimiser/references/optimisation-catalogue.md);
- Codex metadata for explicit or automatic invocation; and
- a test suite covering accepted runs and representative failures across Gates 2 to 6.

#### Gate 3: quantify the gas change

Run the baseline diff and gas report. Every declared target must have a deterministic saving, and no deterministic snapshot row may regress.

#### Gate 4: prove behaviour is unchanged

Run the complete test suite again with the pinned fuzz seed, then repeat it without the pin.

#### Gate 5: preserve layouts and selectors

Compare every recorded storage layout and method map before and after the candidate. Any change to a protected contract rejects the run.

#### Gate 6: prove state-sensitive unchecked arithmetic

Unchecked arithmetic that can affect persistent state or externally visible results needs an existing targeted differential or property test. Other candidates record why this gate does not apply.

### Hexaemeron

[Hexaemeron](./plugins/hexaemeron) takes a topic from nothing to a working prototype through one receipted loop.

Let there be light. A deterministic controller (`hexctl`) decides what comes next and refuses to advance without a receipt; state and a hash-chained ledger survive context resets, so resume is the same command.

1. Study the topic and write a linted study file.
2. Derive a runbook of discrete, self-contained steps.
3. Per step: file an issue with `TODO`, `Acceptance Criteria`, and `User Value / Need` checklists.
4. Implement the least complicated construction that satisfies the issue.
5. Run the vendored Pashov suite (`x-ray`, `solidity-auditor`, `fizz`) in rounds until a round comes back clean or the remaining leads are judged not worth another pass, fixes on a stacked branch.
6. Rewrite every shipped document and the PR text through the bundled `imprimatur` lint and `vulgate` voice mask.
7. Push the PR, reconcile the issue, move to the next step.

Hexaemeron includes:

- the executable [`hexctl.py`](./plugins/hexaemeron/skills/fiat/scripts/hexctl.py) controller with a tamper-evident ledger (`verify` proves both chain and state);
- the [`imprimatur`](./plugins/hexaemeron/skills/imprimatur) three-tier prose lint and the [`vulgate`](./plugins/hexaemeron/skills/vulgate) voice mask, invokable on their own;
- the Pashov Audit Group suite vendored verbatim (MIT; `LICENSE` and `NOTICE.md` in each skill directory);
- Codex metadata for explicit or automatic invocation; and
- 32 controller tests, 56 lint tests, and a fuzz-audit log ([`audit/AUDIT.md`](./plugins/hexaemeron/audit/AUDIT.md)) covering the controller's own surfaces.

## Code findings

What the plugins turn up in real repositories collects here, each entry carrying the record behind it and whatever it failed to clear. The ideas are cheap. The evidence is the job.

### Hermes: `BaseAccessControls.grantRoles` memory parameters

The first live Hermes pass found that [`BaseAccessControls.grantRoles`](./plugins/hermes-gas-optimiser/examples/v2-protocol-v2.1.0/README.md) receives two read-only dynamic arrays through `memory` despite being external. The recorded candidate moves both parameters to `calldata`, avoiding the ABI copy. The candidate is published as a finding, not an accepted optimisation: its Gate 3 gas-report command did not complete.

## Install

### Codex

Add the Wildcat Labs marketplace from the Codex CLI:

```bash
codex plugin marketplace add wildcat-finance/skills
```

Restart the ChatGPT desktop app, open the Plugins Directory, select **Wildcat Labs**, and install **Hermes Gas Optimiser** or **Hexaemeron**.

To inspect configured sources or fetch later updates:

```bash
codex plugin marketplace list
codex plugin marketplace upgrade wildcat-labs
```

See OpenAI's [plugin packaging documentation](https://developers.openai.com/plugins/build/plugins) for the marketplace workflow.

### Claude Code

Add the same marketplace and install either plugin from inside Claude Code:

```text
/plugin marketplace add wildcat-finance/skills
/plugin install hermes-gas-optimiser@wildcat-labs
/plugin install hexaemeron@wildcat-labs
```

If the install summary asks for it, run `/reload-plugins`. Claude namespaces plugin skills, so Hermes is available as:

```text
/hermes-gas-optimiser:hermes-gas-optimiser
```

and Hexaemeron's entry skill as:

```text
/hexaemeron:fiat "<topic>"
```

See Anthropic's [skills](https://code.claude.com/docs/en/skills) and [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) documentation for the underlying format.

## Use

Hermes needs Python 3, Git and [Foundry](https://getfoundry.sh/) available in the target repository. Start Codex from a clean Foundry worktree, then ask:

```text
Use $hermes-gas-optimiser to optimise gas in this repository. Work one optimisation class at a time and keep the complete verification record.
```

The full command contract, layout rules and property standard live in [Hermes's `SKILL.md`](./plugins/hermes-gas-optimiser/skills/hermes-gas-optimiser/SKILL.md).

Hexaemeron needs Python 3, Git and `gh` in the target repository (plus [Foundry](https://getfoundry.sh/) when the run ships Solidity). Ask:

```text
Use $hexaemeron to take "<topic>" from study to a pushed prototype, one receipted phase at a time.
```

The loop, the receipt contract and the controller reference live in [Hexaemeron's `SKILL.md`](./plugins/hexaemeron/skills/fiat/SKILL.md).

## Repository layout

```text
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins/
├── hermes-gas-optimiser/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   └── skills/
│       └── hermes-gas-optimiser/
│           ├── SKILL.md
│           ├── agents/
│           ├── references/
│           └── scripts/
└── hexaemeron/
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json
    ├── agents/
    ├── audit/
    ├── tests/
    └── skills/
        ├── fiat/
        ├── imprimatur/
        ├── vulgate/
        ├── x-ray/
        ├── solidity-auditor/
        └── fizz/
```

Codex and Claude Code load the same skill directory. The host manifests only handle discovery and installation; each plugin's instructions, harness and acceptance conditions stay shared. Target-repository instructions still apply. More will turn up here as they become useful enough to keep.
