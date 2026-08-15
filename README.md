# Wildcat Labs skills

Agent skills written and used by [Wildcat Labs](https://wildcat.finance).

This is where we publish workflows that have earned more than a prompt. Each plugin gets a narrow job, a clear trigger, and whatever scripts, references and tests it needs to make the result checkable. Read a plugin before running it: skills can execute commands and edit source.

## Plugins

### Hermes

[Hermes](./plugins/hermes) treats Solidity gas work as a verification problem.

Gas changes are easy to praise and surprisingly easy to get wrong. Hermes takes one optimisation class at a time through a fail-closed Foundry run:

1. Seal a clean baseline with `forge snapshot` and a green `forge test`.
2. Apply exactly one declared optimisation class.
3. Prove the saving with `forge snapshot --diff`, reject every positive delta, and capture `forge test --gas-report`.
4. Run the full test suite again with the pinned fuzz seed, then once more unpinned.
5. Diff storage layouts and method identifiers for every recorded contract. Any layout change to a hook, role provider, proxied contract or other protected contract aborts the run.
6. For unchecked arithmetic that can affect persistent state, asset accounting, external calls, permissions, or rounding, run the existing targeted differential or property test before accepting the candidate.

A candidate only clears Hermes when every gate clears. The run leaves behind `result.json`, command logs, gas comparisons, the Solidity diff, storage layouts and method maps, so the number and the safety case can be reviewed together.

Hermes includes:

- the executable [`hermes.py`](./plugins/hermes/skills/hermes/scripts/hermes.py) harness;
- a catalogue of [12 optimisation classes](./plugins/hermes/skills/hermes/references/optimisation-catalogue.md);
- Codex metadata for explicit or automatic invocation; and
- a test suite covering accepted runs and representative failures across Gates 2 to 6.

#### Day to day

**Developers.** A gas change shaves a few hundred units off a hot path and nobody can say whether behaviour moved with it. Run Hermes on that one optimisation class and the review arrives with the snapshot diff, both fuzz passes, the storage layout comparison and a `result.json`, rather than a number and an assurance.

**Security and audit.** A gas change arrives from outside the team. Instead of reading it for intent, put it through Gate 5 to see whether any protected contract's storage layout or method identifiers moved, and Gate 6 for unchecked arithmetic that reaches persistent state.


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

#### Day to day

**Developers.** A half-formed idea and a week to find out whether it holds. Hexaemeron turns it into a study, a runbook of discrete steps, and one issue and one pull request per step, with the audit suite run against each before it is pushed.

**Security and audit.** You want the Pashov suite over a contract and nothing else. `x-ray`, `solidity-auditor` and `fizz` are vendored whole and run on their own, without taking on the loop around them.

**Marketing.** A launch post reads like a machine wrote it. `imprimatur` says what is wrong with it across three tiers and `vulgate` rewrites it in house voice. Neither needs the controller, and neither needs installing separately.

**Business development.** An integration document has to be accurate about what the protocol does and readable by someone who is not an engineer. The study phase produces the first and the prose masks produce the second.

### Probitas

[Probitas](./plugins/probitas) builds a sourced dossier on what a counterparty has done across on-chain lending venues.

Undercollateralised lending is the reason to want one: nothing stands between a lender and a total loss except a judgement about the borrower, and that judgement usually gets assembled by hand out of whatever whoever is asking happens to remember. The tool is not limited to that case. Most on-chain borrowing is collateralised and it still tells you plenty, because a liquidation says a price moved, a bad debt says somebody was not made whole, and a missed maturity says what it says anywhere.

Two halves, doing different jobs. A deterministic collector queries venue adapters and writes an evidence file in which a record cannot exist without a transaction hash, a URL or a document reference. The model writes the narrative from that file, and a gate checker reads the document and the evidence together before either ships.

Five gates decide whether a dossier is honest enough to hand to a lender:

1. Declared, provably linked and inferred addresses stay in separate sections.
2. Every venue in the registry gets a coverage row, and a venue that was queried says over what block range. Silence about a venue would read as a clean record.
3. Every assertion carries a citation, and every figure in the document traces back to a record.
4. What could not be established gets its own section, ahead of anything that reads like a conclusion.
5. No score without a rubric printed beside it. This version emits none.

Gate 3 is the one that does the work. It rebuilds, from the evidence alone, every number and hash a truthful dossier could carry, then fails the document on any figure that is not in that set. An invented transaction hash, an amount rounded in the retelling, a market that was never there: each fails the run rather than shipping in it.

Probitas includes:

- the executable [`probitas.py`](./plugins/probitas/scripts/probitas.py) collector, renderer and gate checker, standard library only;
- adapters for [Wildcat](https://wildcat.finance) and Morpho Blue, and eleven further venues carried as named gaps rather than silence;
- nine synthetic borrower fixtures, including the cured delinquency that a hand-assembled writeup usually reads as a default;
- a [committed example dossier](./plugins/probitas/docs/example-dossier.md) that the tests regenerate and compare, so it cannot drift;
- [a guide to closing a coverage gap](./plugins/probitas/docs/adding-a-venue.md) that assumes no knowledge of Wildcat; and
- 234 tests and an audit log ([`audit/AUDIT.md`](./plugins/probitas/audit/AUDIT.md)) recording every round, including the fixes that were wrong the first time.

#### Day to day

**Business development.** A counterparty asks for a market and someone has to decide whether their word is worth anything. Give this the addresses they declared and it comes back with what they borrowed elsewhere, whether they gave it back, and a list of the venues nobody could check, so the thin parts of the record are visible rather than absent.

**Finance.** Exposure to a name that also borrows in three other places. The dossier states each position's venue, the amounts as exact on-chain integers, and whether anything was left unpaid after a liquidation, which is the number that ends up mattering.

**Security and audit.** A document arrives asserting things about a counterparty and you have to decide whether to believe it. Run `verify` against the evidence file it came with: every figure in the document has to trace back to a record with a transaction hash, and one that does not fails the check by arithmetic rather than by your reading it closely.

## Who these are for

Scored out of 10 for doing the job, not for reading the output. A marketer can quote a verified gas number without having any use for Hermes itself.

| Role | Hermes | Hexaemeron | Probitas |
| --- | --- | --- | --- |
| Developers | 9 | 9 | 4 |
| Security and audit | 7 | 8 | 5 |
| Marketing | 3 | 6 | 1 |
| Business development | 2 | 5 | 9 |
| Finance | 3 | 4 | 7 |
| Legal | 1 | 4 | 4 |

Five is the barrier. At or above it, the plugin's entry carries a worked
example of what that role would use it for. Below it there is no example,
because there is no honest one to give. A low score means we could not find a
reason for that desk to open the plugin rather than read what it produced.

Probitas scores 9 for business development because the dossier is the job, 7
for finance because the same record describes counterparty exposure, and 5 for
security and audit because `verify` checks somebody else's document against
its evidence. Its 4s for developers and legal reflect useful output rather
than a strong reason for either desk to operate the plugin. Marketing has no
credible operating case, so it scores 1.

## Install

### Codex

Add the Wildcat Labs marketplace from the Codex CLI:

```bash
codex plugin marketplace add wildcat-finance/skills
```

Restart the ChatGPT desktop app, open the Plugins Directory, select **Wildcat Labs**, and install **Hermes**, **Hexaemeron** or **Probitas**.

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
/plugin install hermes@wildcat-labs
/plugin install hexaemeron@wildcat-labs
/plugin install probitas@wildcat-labs
```

If the install summary asks for it, run `/reload-plugins`. Claude namespaces plugin skills, so Hermes is available as:

```text
/hermes:hermes
```

and Hexaemeron's entry skill as:

```text
/hexaemeron:fiat "<topic>"
```

Probitas is available as:

```text
/probitas:probitas
```

See Anthropic's [skills](https://code.claude.com/docs/en/skills) and [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) documentation for the underlying format.

### Local agents

Agents that support the open Agent Skills convention can discover the three
host-neutral entries under [`.agents/skills`](./.agents/skills). Point the
agent at this repository and include that directory in its project skill
search path. Keep the repository layout intact: each entry routes to the
canonical plugin instructions instead of copying them.

A file-reading agent without automatic skill discovery should begin with
[`AGENTS.md`](./AGENTS.md). That file identifies the entrypoints, path rules,
and plugin-specific runtime contracts. Named tools in vendored skills describe
capabilities; the Hexaemeron contract maps them to file, shell, search,
planning, question, and subagent operations available in a local runtime.

Plain-text activation works alongside host syntax:

```text
Use Hermes to optimise gas in this Foundry repository.
Use Hexaemeron Fiat to take "<topic>" through the delivery loop.
Use Hexaemeron Fizz to generate a stateful fuzz suite.
Use Probitas to build a dossier on this counterparty from the addresses they declared.
```

Fiat remains explicit-only. Mentioning a similar delivery task does not start
the controller unless the user names Hexaemeron or Fiat and asks to run it.

## Use

Hermes needs Python 3, Git and [Foundry](https://getfoundry.sh/) available in the target repository. Start Codex from a clean Foundry worktree, then ask:

```text
Use $hermes to optimise gas in this repository. Work one optimisation class at a time and keep the complete verification record.
```

The full command contract, layout rules and property standard live in [Hermes's `SKILL.md`](./plugins/hermes/skills/hermes/SKILL.md).

Hexaemeron needs Python 3, Git and `gh` in the target repository (plus [Foundry](https://getfoundry.sh/) when the run ships Solidity). Ask:

```text
Use $hexaemeron to take "<topic>" from study to a pushed prototype, one receipted phase at a time.
```

The loop, the receipt contract and the controller reference live in [Hexaemeron's `SKILL.md`](./plugins/hexaemeron/skills/fiat/SKILL.md).

Probitas needs Python 3 and nothing else. Neither shipped venue asks for a key, and `--fixtures` runs it with no network at all. Ask:

```text
Use $probitas to build a sourced dossier on "<entity>" from the addresses they declared.
```

The sequence, the five gates and the refusals live in [Probitas's `SKILL.md`](./plugins/probitas/skills/probitas/SKILL.md).

## Repository layout

```text
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins/
├── hermes/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   └── skills/
│       └── hermes/
│           ├── SKILL.md
│           ├── agents/
│           ├── references/
│           └── scripts/
├── hexaemeron/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── agents/
│   ├── audit/
│   ├── tests/
│   └── skills/
│       ├── fiat/
│       ├── imprimatur/
│       ├── vulgate/
│       ├── x-ray/
│       ├── solidity-auditor/
│       └── fizz/
└── probitas/
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json
    ├── AGENTS.md
    ├── audit/
    ├── docs/
    ├── scripts/
    ├── tests/
    └── skills/
        └── probitas/
```

Codex and Claude Code load the same skill directory. The host manifests only handle discovery and installation; each plugin's instructions, harness and acceptance conditions stay shared. Target-repository instructions still apply. More will turn up here as they become useful enough to keep.

Local agents load the same canonical directories through the two portable
entries. The portable layer translates discovery and tool vocabulary; it does
not weaken a skill's checks or invent receipts for work that did not run.
