# Wildcat Labs skills

Agent skills written and used by [Wildcat Labs](https://wildcat.finance).

This is where we publish workflows and agent contracts that are worth keeping.
Each plugin has a narrow job, a clear trigger and the instructions, code,
evidence or tests that job needs. Read a plugin before running it: skills can
execute commands and edit source.

## Choose the job, then the plugin

The names are memorable; the boundaries matter more. This is the short map of
what each plugin does, where it hands work over and what is honestly left to
build.

| Plugin | Use it for | Try this instead | Current frontier |
| --- | --- | --- | --- |
| [Alexandria](./plugins/alexandria) | Preserving heterogeneous lending-source bytes, then deriving and querying reviewed credit views. | Tabularium for semantic event mapping; Probitas for a dossier. | Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented. |
| [Ariadne](./plugins/ariadne) | Binding an artefact digest to build, test, review and deployment evidence. | An external Sigstore or cosign verifier for signatures. | The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented. |
| [Brevitas](./plugins/brevitas) | Enforcing mechanical volume and structure budgets on engineering review prose while preserving evidence. | Imprimatur for vocabulary; Vulgate for register; Sapheneia for AuDHD interaction shape. | The linter has not been forward-tested across a held cross-model corpus of engineering reviews, and preservation of counterexamples and reproduction steps remains agent-checked. |
| [Hermes](./plugins/hermes) | Measuring one Solidity gas-optimisation class through fail-closed Foundry checks. | Pandects or the audit skills for broader behavioural and security work. | No complete, reproducible live Wildcat evidence bundle is published. |
| [Hexaemeron](./plugins/hexaemeron) | Running an explicit, receipted delivery loop, ranking frontier work with Kronos, or using its fuzzing, audit and prose skills separately. | A named bundled skill when the controller is unnecessary. | The bundled Solidity audit suite has not yet been exercised in a published end-to-end Fiat delivery. |
| [Lemma](./plugins/lemma) | Producing source-linked chunks from Solidity compiler inputs or Markdown. | An embedding, index, retrieval or answering system for every later stage. | Callable-surface ABI validation does not independently check return types or state mutability. |
| [Lazarus](./plugins/lazarus) | Capturing a finite fixed-block Ethereum fixture, checking proof-backed state and replaying exact requests without fallback. | Alexandria for a lending archive; Tabularium for event interpretation. | Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented. |
| [Pandects](./plugins/pandects) | Supplying executable credit laws, broken specimens and reduced counterexamples. | Fizz for a protocol-specific fuzz harness. | The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records. |
| [Probitas](./plugins/probitas) | Building a sourced counterparty dossier from declared addresses, without identity inference or a Wildcat verdict. | Alexandria for archived inputs. | Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented. |
| [Sapheneia](./plugins/sapheneia) | Shaping the agent's own replies so an AuDHD reader can see the action, boundaries, state and evidence. | Imprimatur for prose linting; Vulgate or another voice mask for register. | Cross-model behaviour has not yet been held against a published AuDHD task corpus. |
| [Tabularium](./plugins/tabularium) | Mapping preserved venue-native records into reproducible, venue-qualified credit events. | Alexandria for raw harvesting; Probitas for a dossier. | Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented. |

## Plugins

### Alexandria

[Alexandria](./plugins/alexandria) keeps heterogeneous lending data unchanged,
then derives only the credit rows a reviewed mapping can defend.

The full account, what it ships and who it is for live in [Alexandria's README](./plugins/alexandria/README.md).

### Ariadne

[Ariadne](./plugins/ariadne) binds a release to the evidence behind it, in a statement another person can check.

The full account, what it ships and who it is for live in [Ariadne's README](./plugins/ariadne/README.md).

### Brevitas

[Brevitas](./plugins/brevitas) is the final structural pass for audit findings,
security reviews, gas analysis, `invariant` discussion, diff review and protocol
commentary. It controls line count, finding shape, headings, tables, code fences
and connective prose. Imprimatur still owns vocabulary, Vulgate owns register,
and Sapheneia owns AuDHD interaction shape.

The full account, what it ships and who it is for live in [Brevitas's README](./plugins/brevitas/README.md).

### Hermes

[Hermes](./plugins/hermes) treats Solidity gas work as a verification problem.

The full account, what it ships and who it is for live in [Hermes's README](./plugins/hermes/README.md).

### Hexaemeron

[Hexaemeron](./plugins/hexaemeron) takes a topic from nothing to a working prototype through one receipted loop.

The full account, what it ships and who it is for live in [Hexaemeron's README](./plugins/hexaemeron/README.md).

### Lemma

[Lemma](./plugins/lemma) turns Solidity compiler inputs and Markdown documents
into JSONL chunks. The two chunkers share one schema and keep source text used
for quotation separate from text prepared for a model or embedder.

The full account, what it ships and who it is for live in [Lemma's README](./plugins/lemma/README.md).

### Lazarus

[Lazarus](./plugins/lazarus) preserves the finite part of historical Ethereum
state and RPC evidence that one application test needs, then replays only the
requests in that fixture.

The full account, what it ships and who it is for live in [Lazarus's README](./plugins/lazarus/README.md).

### Pandects

[Pandects](./plugins/pandects) is a corpus of executable laws for credit
contracts. Each law is a Solidity component with a deliberately broken
contract it is proven to catch, a reduced counterexample, and a statement of
the accounting model and observables it requires.

The catalogue holds ten laws across conservation, accrual and withdrawal
claims. Nine are exact.

The full account, what it ships and who it is for live in [Pandects's README](./plugins/pandects/README.md).

### Probitas

[Probitas](./plugins/probitas) builds a sourced dossier on what a counterparty has done across on-chain lending venues.

The full account, what it ships and who it is for live in [Probitas's README](./plugins/probitas/README.md).

### Sapheneia

[Sapheneia](./plugins/sapheneia) shapes the agent's own replies for AuDHD
engineers. It keeps the next action, task boundary, done condition, current
state, evidence and unknowns visible from turn to turn.

The full account, what it ships and who it is for live in [Sapheneia's README](./plugins/sapheneia/README.md).

### Tabularium

[Tabularium](./plugins/tabularium) preserves on-chain credit events in a form
another person can rebuild after the endpoint that served them is gone.

The full account, what it ships and who it is for live in [Tabularium's README](./plugins/tabularium/README.md).

## Who these are for

Scored out of 10 for doing the job, not for reading the output. A marketer can quote a verified gas number without having any use for Hermes itself.

| Role | Alexandria | Ariadne | Brevitas | Hermes | Hexaemeron | Lemma | Lazarus | Pandects | Probitas | Sapheneia | Tabularium |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Developers | 8 | 8 | 8 | 9 | 9 | 6 | 8 | 8 | 4 | 8 | 7 |
| Security and audit | 8 | 9 | 10 | 7 | 8 | 4 | 8 | 9 | 5 | 7 | 7 |
| Marketing | 1 | 1 | 1 | 3 | 6 | 1 | 1 | 1 | 1 | 3 | 1 |
| Business development | 6 | 2 | 2 | 2 | 5 | 1 | 2 | 2 | 9 | 4 | 3 |
| Finance | 8 | 1 | 2 | 3 | 4 | 1 | 2 | 2 | 7 | 4 | 7 |
| Legal | 3 | 3 | 2 | 1 | 4 | 1 | 2 | 2 | 4 | 4 | 2 |

Five is the barrier. At or above it, the plugin's entry carries a worked example of what that role would use it for. Below it there is no example, because there is no honest one to give. These are engineering tools, and a 2 means we could not find a reason for that desk to open the plugin rather than read what it produced.

## Install

### Codex

Add the Wildcat Labs marketplace from the Codex CLI, then list configured
sources or fetch later updates:

```bash
codex plugin marketplace add wildcat-finance/skills
codex plugin marketplace list
codex plugin marketplace upgrade wildcat-labs
```

After adding it, restart the ChatGPT desktop app, open the Plugins Directory,
select **Wildcat Labs**, and install the plugin you need.

See OpenAI's [plugin packaging documentation](https://developers.openai.com/plugins/build/plugins) for the marketplace workflow.

### Claude Code

Add the same marketplace and install a plugin from inside Claude Code:

```text
/plugin marketplace add wildcat-finance/skills
/plugin install alexandria@wildcat-labs
/plugin install ariadne@wildcat-labs
/plugin install brevitas@wildcat-labs
/plugin install hermes@wildcat-labs
/plugin install hexaemeron@wildcat-labs
/plugin install lemma@wildcat-labs
/plugin install lazarus@wildcat-labs
/plugin install pandects@wildcat-labs
/plugin install probitas@wildcat-labs
/plugin install sapheneia@wildcat-labs
/plugin install tabularium@wildcat-labs
```

If the install summary asks for it, run `/reload-plugins`.

#### Invoke

Claude namespaces plugin skills, so each entry skill answers as:

```text
/alexandria:alexandria
/ariadne:ariadne
/brevitas:brevitas
/hermes:hermes
/hexaemeron:fiat "<topic>"
/lemma:chunk
/lazarus:lazarus
/pandects:pandects
/probitas:probitas
/sapheneia:sapheneia
/tabularium:tabularium
```

#### Hexaemeron's phase skills

These answer on their own, without the controller:

```text
/hexaemeron:protasis
/hexaemeron:elenchus
/hexaemeron:phylax
/hexaemeron:ephoros
/hexaemeron:metron
/hexaemeron:hypomnema
```

See Anthropic's [skills](https://code.claude.com/docs/en/skills) and [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) documentation for the underlying format.

### Local agents

Agents that support the open Agent Skills convention can discover the eleven
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
Use Alexandria to preserve this lending-data capture and query its source-bound credit view.
Use Ariadne to capture this release in an evidence statement, run its gates, and report its signature state without checking signatures.
Use Brevitas to enforce evidence-preserving structural budgets on this engineering review.
Use Hermes to optimise gas in this Foundry repository.
Use Hexaemeron Fiat to take "<topic>" through the delivery loop.
Use Hexaemeron Fizz to generate a stateful fuzz suite.
Use Hexaemeron Phylax to harden the off-chain surface of this change, or name Protasis, Elenchus, Ephoros, Metron or Hypomnema.
Use Lemma to chunk this Solidity standard input into JSONL.
Use Lazarus to capture, verify or replay this finite historical Ethereum fixture.
Use Pandects to check this credit protocol against the executable laws in the corpus.
Use Probitas to build a dossier on this counterparty from the addresses they declared.
Use Sapheneia to shape your replies for an AuDHD reader for the rest of this task.
Use Tabularium to build and verify a source-bound Goldfinch, Euler v1 or Euler V2 credit-event release.
```

Fiat remains explicit-only. Mentioning a similar delivery task does not start
the controller unless the user names Hexaemeron or Fiat and asks to run it.

## Use

Alexandria needs Python 3 and nothing else. Its checked-in demonstration and
all verification paths run offline. Ask:

```text
Use $alexandria to preserve this lending-data capture, derive its reviewed credit rows, and query the declared address without hiding coverage gaps.
```

The release contracts, mapping boundary and refusal rules live in
[Alexandria's `SKILL.md`](./plugins/alexandria/skills/alexandria/SKILL.md).

Ariadne needs Python 3 and nothing else. Capturing from a Foundry project needs
that project's build output, which `forge build` already wrote. Ask:

```text
Use $ariadne to capture this release in an evidence statement, run its gates, and report its signature state without checking signatures.
```

The gates, the predicate and the refusals live in [Ariadne's `SKILL.md`](./plugins/ariadne/skills/ariadne/SKILL.md).

Brevitas needs Python 3 and no third-party package. Ask:

```text
Use $brevitas to compress this engineering review without dropping addresses, transaction hashes, file:line references, numbers, counterexamples or reproduction steps.
```

The budgets, evidence precedence and exception rule live in
[Brevitas's `SKILL.md`](./plugins/brevitas/skills/brevitas/SKILL.md).

Hermes needs Python 3, Git and [Foundry](https://getfoundry.sh/) available in the target repository. Start Codex from a clean Foundry worktree, then ask:

```text
Use $hermes to optimise gas in this repository. Work one optimisation class at a time and keep the complete verification record.
```

The full command contract, layout rules and property standard live in [Hermes's `SKILL.md`](./plugins/hermes/skills/hermes/SKILL.md).

Hexaemeron needs Python 3, Git and `gh` in the target repository (plus [Foundry](https://getfoundry.sh/) when the run ships Solidity). Ask:

```text
Use $hexaemeron to take "<topic>" from study to a merged delivery, one receipted phase at a time.
```

The loop, the receipt contract and the controller reference live in [Hexaemeron's `SKILL.md`](./plugins/hexaemeron/skills/fiat/SKILL.md).

Lemma needs Python 3.10 or later. Solidity input also needs `solc`, Docker, or
Podman. Ask:

```text
Use $chunk to turn this Solidity standard input into validated JSONL chunks.
```

The command selection and output rules live in [Lemma's `chunk` skill](./plugins/lemma/skills/chunk/SKILL.md).

Lazarus needs Python 3.11 or later and the packages pinned in its lock file.
Capture is the only command that needs an archive RPC; verification, replay and
the shipped Goldfinch demonstration run offline. Ask:

```text
Use $lazarus to capture this finite historical fixture, verify its proof-backed state, and replay only its exact requests.
```

The evidence boundary, refusal rules and commands live in [Lazarus's `SKILL.md`](./plugins/lazarus/skills/lazarus/SKILL.md).

Pandects needs Python 3, and [Foundry](https://getfoundry.sh/) for the campaign
its runner knows. Ask:

```text
Use $pandects to check this credit protocol against the executable laws in the corpus.
```

The laws, their broken specimens and the engine boundary live in
[Pandects's `SKILL.md`](./plugins/pandects/skills/pandects/SKILL.md).

Probitas needs Python 3 and nothing else. Neither shipped venue asks for a key, and `--fixtures` runs it with no network at all. Ask:

```text
Use $probitas to build a sourced dossier on "<entity>" from the addresses they declared.
```

The sequence, the five gates and the refusals live in [Probitas's `SKILL.md`](./plugins/probitas/skills/probitas/SKILL.md).

Sapheneia needs no runtime dependency. Ask:

```text
Use $sapheneia to shape your replies for an AuDHD reader throughout this task.
```

The activation contract and ten ranked rules live in
[Sapheneia's `SKILL.md`](./plugins/sapheneia/skills/sapheneia/SKILL.md).

Tabularium needs Python 3.9 or later and nothing else. Its shipped releases and
tests use no network. Ask:

```text
Use $tabularium to rebuild the checked-in Euler V2 release and verify it offline.
```

The mapping, release rules and evidence boundary live in
[Tabularium's `SKILL.md`](./plugins/tabularium/skills/tabularium/SKILL.md).

## Repository layout

```text
.claude-plugin/marketplace.json   one entry per plugin
.agents/plugins/marketplace.json  the same set, host-neutral
.agents/skills/<name>/SKILL.md    a portable entrypoint per plugin, and per phase skill
plugins/<name>/
├── .claude-plugin/plugin.json    host manifests; discovery and installation only
├── .codex-plugin/plugin.json
├── AGENTS.md                     runtime contract and selection table
├── README.md                     landing page
├── tests/
└── skills/<skill>/SKILL.md       canonical instructions, one directory per skill
```

Every plugin has that shape. What each adds beyond it:

| Plugin | Skills | Also carries |
| --- | --- | --- |
| Alexandria | `alexandria` | docs, examples, schemas, scripts |
| Ariadne | `ariadne` | audit, docs, examples, schemas, scripts |
| Brevitas | `brevitas` | evals |
| Hermes | `hermes` | references and scripts inside the skill |
| Hexaemeron | `fiat`, `kronos`, `imprimatur`, `vulgate`, the vendored `x-ray`, `solidity-auditor` and `fizz`, and `protasis`, `elenchus`, `phylax`, `ephoros`, `metron`, `hypomnema` | agents, audit, docs |
| Lazarus | `lazarus` | docs, examples, schemas, scripts, pinned requirements |
| Lemma | `chunk` | chunkers, baseline, schema, solc container, tools |
| Pandects | `pandects` | Solidity under `src` and `test`, adapters, catalogue, specimens, integrations, audit |
| Probitas | `probitas` | assets, audit, docs, scripts |
| Sapheneia | `sapheneia` | nothing further |
| Tabularium | `tabularium` | audit, docs, examples, schemas, scripts |

Codex and Claude Code load the same skill directory. The host manifests only handle discovery and installation; each plugin's instructions, harness and acceptance conditions stay shared. Target-repository instructions still apply. More will turn up here as they become useful enough to keep.

Local agents load the same canonical directories through the portable
entries. The portable layer translates discovery and tool vocabulary; it does
not weaken a skill's checks or invent receipts for work that did not run.

# Wildcat Commons

Wildcat Labs spends much of its time on trust roots, attestation,
accountability and verification. That follows from the sphere it works in. In
private credit, trust is the most valuable currency there is, and a promise is
worth only as much as the evidence and recourse behind it.

Doing that work keeps exposing the same missing tools: a durable public record
of on-chain credit, shared laws for credit implementations, agents that can show
their sources, a conformance suite for hooks and a way to replay chain state
after the original infrastructure is gone. Carrying evidence with a release was
the first of them, and `ariadne` above is the answer to it. Preserving the credit
record was the next, and `tabularium` now has Goldfinch and two Euler protocol
generations. `pandects` now
carries the shared credit laws. `lazarus` preserves and replays a finite slice
of historical state. Another protocol, auditor, researcher or agent builder
should be able to use each one without needing to use Wildcat. `alexandria`
now keeps the heterogeneous raw record and serves a reviewed address view to
`probitas` without making either one own the other's claims.

What remains, listed alphabetically:

- `berean`, a release manifest and evaluation corpus for agents that must
  support answers with exact documents and chain state.
- `janus`, a conformance suite for what contract hooks may observe and change
  before and after a host action.

These are tools we wanted and then needed. Their formats, datasets, properties,
fixtures and tests become more useful when other teams can inspect, run and
improve them, so that is who they are for too.

If Wildcat Labs means what it says about the Commons, publishing only the work
that happens to be convenient is not enough. Fine. We'll do it ourselves.
