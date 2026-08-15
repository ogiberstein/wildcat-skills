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
6. For unchecked arithmetic in or feeding accrual code, run the existing targeted differential or property test before accepting the candidate.

A candidate only clears Hermes when every gate clears. The run leaves behind `result.json`, command logs, gas comparisons, the Solidity diff, storage layouts and method maps, so the number and the safety case can be reviewed together.

Hermes includes:

- the executable [`hermes.py`](./plugins/hermes-gas-optimiser/skills/hermes-gas-optimiser/scripts/hermes.py) harness;
- a catalogue of [12 optimisation classes](./plugins/hermes-gas-optimiser/skills/hermes-gas-optimiser/references/optimisation-catalogue.md);
- Codex metadata for explicit or automatic invocation; and
- a test suite covering accepted runs and representative failures across Gates 2 to 6.

The ideas are cheap. The evidence is the job.

## Install

### Codex

Add the Wildcat Labs marketplace from the Codex CLI:

```bash
codex plugin marketplace add wildcat-finance/skills
```

Restart the ChatGPT desktop app, open the Plugins Directory, select **Wildcat Labs**, and install **Hermes Gas Optimiser**.

To inspect configured sources or fetch later updates:

```bash
codex plugin marketplace list
codex plugin marketplace upgrade wildcat-labs
```

See OpenAI's [plugin packaging documentation](https://developers.openai.com/plugins/build/plugins) for the marketplace workflow.

### Claude Code

Add the same marketplace and install Hermes from inside Claude Code:

```text
/plugin marketplace add wildcat-finance/skills
/plugin install hermes-gas-optimiser@wildcat-labs
```

If the install summary asks for it, run `/reload-plugins`. Claude namespaces plugin skills, so Hermes is available as:

```text
/hermes-gas-optimiser:hermes-gas-optimiser
```

See Anthropic's [skills](https://code.claude.com/docs/en/skills) and [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) documentation for the underlying format.

## Use

Hermes needs Python 3, Git and [Foundry](https://getfoundry.sh/) available in the target repository. Start Codex from a clean Foundry worktree, then ask:

```text
Use $hermes-gas-optimiser to optimise gas in this repository. Work one optimisation class at a time and keep the complete verification record.
```

The full command contract, layout rules and accrual proof standard live in [Hermes's `SKILL.md`](./plugins/hermes-gas-optimiser/skills/hermes-gas-optimiser/SKILL.md).

## Repository layout

```text
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins/
└── hermes-gas-optimiser/
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json
    └── skills/
        └── hermes-gas-optimiser/
            ├── SKILL.md
            ├── agents/
            ├── references/
            └── scripts/
```

Codex and Claude Code load the same skill directory. The host manifests only handle discovery and installation; Hermes's instructions, harness and acceptance conditions stay shared. Target-repository instructions still apply. More will turn up here as they become useful enough to keep.
