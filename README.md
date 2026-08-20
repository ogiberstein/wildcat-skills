# Wildcat Labs skills

Agent skills written and used by [Wildcat Labs](https://wildcat.finance).

This is where we publish workflows and agent contracts that are worth keeping.
Each plugin has a narrow job, a clear trigger and the instructions, code,
evidence or tests that job needs. Read a plugin before running it: skills can
execute commands and edit source.

## Plugins

### Alexandria

[Alexandria](./plugins/alexandria) keeps heterogeneous lending data unchanged,
then derives only the credit rows a reviewed mapping can defend.


### Ariadne

[Ariadne](./plugins/ariadne) binds a release to the evidence behind it, in a statement another person can check.


### Berean

[Berean](./plugins/berean) releases evidence-backed protocol agents: the
corpus pinned by digest, every citation provable as exact bytes, every live
value bound to a chain and block, and promotion held to an evaluation record,
all checkable without the model that produced the answers.


### Brevitas

[Brevitas](./plugins/brevitas) is the final structural pass for audit findings,
security reviews, gas analysis, `invariant` discussion, diff review and protocol
commentary. It controls line count, finding shape, headings, tables, code fences
and connective prose. Imprimatur still owns vocabulary, Vulgate owns register,
and Sapheneia owns AuDHD interaction shape.


### Hermes

[Hermes](./plugins/hermes) treats Solidity gas work as a verification problem.


### Hexaemeron

[Hexaemeron](./plugins/hexaemeron) takes a topic from nothing to a working prototype through one receipted loop.


### Horos

[Horos](./plugins/horos) decides what an agent does not read. It classifies a
repository's token sinks with evidence and emits the boundary agents consult
before reading, so the budget goes to the code that matters.


### Janus

[Janus](./plugins/janus) tests a contract hook at the threshold it controls:
what it may observe and change before a host action, what it may change after,
and what it must never touch. A host adapter and a JSON manifest state the
permitted effects; a stateful Foundry harness records the real storage writes,
call targets, value movements and gas across each threshold and fails when the
delta exceeds the manifest. The first adapter is Wildcat's v2.5 market hooks.


### Lemma

[Lemma](./plugins/lemma) turns Solidity compiler inputs and Markdown documents
into JSONL chunks. The two chunkers share one schema and keep source text used
for quotation separate from text prepared for a model or embedder.


### Lazarus

[Lazarus](./plugins/lazarus) preserves the finite part of historical Ethereum
state and RPC evidence that one application test needs, then replays only the
requests in that fixture. It also writes a preservation release: the fixture, an
Ariadne statement about it, and a document binding the two, which a stranger can
read back years later without either tool's authors.


### Pandects

[Pandects](./plugins/pandects) is a corpus of executable laws for credit
contracts. Each law is a Solidity component with a deliberately broken
contract it is proven to catch, a reduced counterexample, and a statement of
the accounting model and observables it requires.

The catalogue holds ten laws across conservation, accrual and withdrawal
claims. Nine are exact.


### Probitas

[Probitas](./plugins/probitas) builds a sourced dossier on what a counterparty has done across on-chain lending venues.


### Sapheneia

[Sapheneia](./plugins/sapheneia) shapes the agent's own replies for AuDHD
engineers. It keeps the next action, task boundary, done condition, current
state, evidence and unknowns visible from turn to turn.


### Tabularium

[Tabularium](./plugins/tabularium) preserves on-chain credit events in a form
another person can rebuild after the endpoint that served them is gone.


## Who these are for

Scored out of 10 for doing the job, not for reading the output. A marketer can quote a verified gas number without having any use for Hermes itself.

| Role | Alexandria | Ariadne | Berean | Brevitas | Hermes | Hexaemeron | Horos | Janus | Lemma | Lazarus | Pandects | Probitas | Sapheneia | Tabularium |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Developers | 8 | 8 | 8 | 8 | 9 | 9 | 8 | 8 | 6 | 8 | 8 | 4 | 8 | 7 |
| Security and audit | 8 | 9 | 7 | 10 | 7 | 8 | 2 | 9 | 4 | 8 | 9 | 5 | 7 | 7 |
| Marketing | 1 | 1 | 2 | 1 | 3 | 6 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 1 |
| Business development | 6 | 2 | 5 | 2 | 2 | 5 | 1 | 2 | 1 | 2 | 2 | 9 | 4 | 3 |
| Finance | 8 | 1 | 3 | 2 | 3 | 4 | 1 | 1 | 1 | 2 | 2 | 7 | 4 | 7 |
| Legal | 3 | 3 | 3 | 2 | 1 | 4 | 1 | 2 | 1 | 2 | 2 | 4 | 4 | 2 |

Five is the barrier. At or above it, the plugin's entry carries a worked example of what that role would use it for. Below it there is no example, because there is no honest one to give. These are engineering tools, and a 2 means we could not find a reason for that desk to open the plugin rather than read what it produced.

## Current status

The short map of what each plugin does and what is honestly left to build.

| Plugin | Use it for | Current frontier |
| --- | --- | --- |
| [Alexandria](./plugins/alexandria) | Preserving heterogeneous lending-source bytes, then deriving and querying reviewed credit views. | Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented. |
| [Ariadne](./plugins/ariadne) | Binding an artefact digest to build, test, review and deployment evidence. | The grounded-agent predicate remains unimplemented; the state-fixture predicate now ships with its schema, gates, conformance fixtures and a capture path that reads a Lazarus fixture's evidence counts rather than recomputing them. |
| [Berean](./plugins/berean) | Releasing and verifying evidence-backed protocol agents against pinned corpora, preserved chain reads and an evaluation record. | The reference release answers against a frozen demonstration corpus and preserved Goldfinch mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release. |
| [Brevitas](./plugins/brevitas) | Enforcing mechanical volume and structure budgets on engineering review prose while preserving evidence. | The linter has not been forward-tested across a held cross-model corpus of engineering reviews, and preservation of counterexamples and reproduction steps remains agent-checked. |
| [Hermes](./plugins/hermes) | Measuring one Solidity gas-optimisation class through fail-closed Foundry checks. | No complete, reproducible live Wildcat evidence bundle is published. |
| [Hexaemeron](./plugins/hexaemeron) | Running an explicit, receipted delivery loop, ranking frontier work with Kronos, or using its fuzzing, audit and prose skills separately. | The bundled Solidity audit suite has not yet been exercised in a published end-to-end Fiat delivery. |
| [Horos](./plugins/horos) | Classifying a repository's token sinks with evidence and emitting the reading boundary agents respect. | The reopened scope is complete: the three home repositories carry graded boundaries, candidates, censuses and adoption stanzas, with the product pull requests awaiting their own review gates; no evidenced improvement remains. |
| [Janus](./plugins/janus) | Stating and enforcing what a contract hook may observe and change around a host action, checked by a manifest and a stateful Foundry harness. | Janus ships the Wildcat v2.5 host adapter and its seven gates against modeled hooks, and no second host adapter yet shows the manifest format holds for another callback model. |
| [Lemma](./plugins/lemma) | Producing source-linked chunks from Solidity compiler inputs or Markdown. | Callable-surface ABI validation does not independently check return types or state mutability. |
| [Lazarus](./plugins/lazarus) | Capturing a finite fixed-block Ethereum fixture, checking proof-backed state, replaying exact requests without fallback, and releasing the fixture with a statement a stranger can check. | Receipts and logs are recorded RPC evidence only; nothing proves them against the captured header's receiptsRoot. |
| [Pandects](./plugins/pandects) | Supplying executable credit laws, broken specimens and reduced counterexamples. | The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records. |
| [Probitas](./plugins/probitas) | Building a sourced counterparty dossier from declared addresses, without identity inference or a Wildcat verdict. | Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented. |
| [Sapheneia](./plugins/sapheneia) | Shaping the agent's own replies so an AuDHD reader can see the action, boundaries, state and evidence. | Cross-model behaviour has not yet been held against a published AuDHD task corpus. |
| [Tabularium](./plugins/tabularium) | Mapping preserved venue-native records into reproducible, venue-qualified credit events. | Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented. |

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
/plugin install berean@wildcat-labs
/plugin install brevitas@wildcat-labs
/plugin install hermes@wildcat-labs
/plugin install hexaemeron@wildcat-labs
/plugin install janus@wildcat-labs
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
/berean:berean
/brevitas:brevitas
/hermes:hermes
/hexaemeron:fiat "<topic>"
/hexaemeron:kronos
/janus:janus
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

Agents that support the open Agent Skills convention can discover the
nineteen host-neutral entries under [`.agents/skills`](./.agents/skills). Point the
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
Use Berean to verify this release's citations, chain readings and promotion record against its pinned corpus.
Use Brevitas to enforce evidence-preserving structural budgets on this engineering review.
Use Hermes to optimise gas in this Foundry repository.
Use Hexaemeron Fiat to take "<topic>" through the delivery loop.
Use Hexaemeron Fizz to generate a stateful fuzz suite.
Use Hexaemeron Kronos to rank the held frontier jobs and run the best through Fiat until none remain.
Use Hexaemeron Protasis to say whether this study and runbook are ready to build from.
Use Hexaemeron Elenchus to find the root cause of this failure and guard it with a test.
Use Hexaemeron Phylax to harden the off-chain surface of this change.
Use Hexaemeron Ephoros to choose the events, metrics and alerts this step must emit.
Use Hexaemeron Metron to baseline this slow path, change one thing and keep or revert on the numbers.
Use Hexaemeron Hypomnema to record this decision where the next person will find it.
Use Janus to check what this hook may observe and change around a host action, against a conformance manifest.
Use Lemma to chunk this Solidity standard input into JSONL.
Use Lazarus to capture, verify or replay this finite historical Ethereum fixture.
Use Pandects to check this credit protocol against the executable laws in the corpus.
Use Probitas to build a dossier on this counterparty from the addresses they declared.
Use Sapheneia to shape your replies for an AuDHD reader for the rest of this task.
Use Tabularium to build and verify a source-bound Goldfinch, Euler v1 or Euler V2 credit-event release.
```

Fiat remains explicit-only. Mentioning a similar delivery task does not start
the controller unless the user names Hexaemeron or Fiat and asks to run it.

## Publish

Work lands here, in the public repository. What reaches an installed plugin
depends on how that machine added the marketplace, and the two routes differ in
who fetches the repository.

### Git-backed, which needs no publishing step

A marketplace added with `/plugin marketplace add wildcat-finance/skills`, or the
Codex equivalent, is a clone the host pulls with the operator's own git
credentials. Pushing to `main` is the whole of publishing. To pick up new
commits:

```bash
claude plugin marketplace update wildcat-labs
claude plugin update hexaemeron@wildcat-labs
```

Inside a session that is `/plugin marketplace update` and
`/plugin update <plugin>@wildcat-labs`. In a provisioning script, pass `--yes`.

### Organisation-distributed, through the private mirror

A marketplace distributed through
[Organization settings > Plugins](https://claude.ai/admin-settings/plugins) is
read server-side by the Claude GitHub App, and that repository has to be private
or internal. Hence the second repository:

- `wildcat-finance/skills` is public and holds the work.
- `wildcat-finance/skills-marketplace` is private. A scheduled job in that
  repository force-pushes every branch and tag from the public one into it. Its
  cron asks for every five minutes; GitHub's scheduler has been delivering closer
  to every twenty, so treat the interval as observed rather than declared.

So the mirror is the publishing pipeline, and there is nothing to package or
upload: organisation sync packages each plugin itself during distribution, which
is why nobody installing needs access to a separate source repository. To
release, merge to `main`, let the mirror run, and let organisation sync read it.
Compare the two heads rather than waiting a fixed time, because a merge that
lands a minute after a mirror run waits for the next one:

```bash
gh api repos/wildcat-finance/skills/commits/main --jq '.sha'
gh api repos/wildcat-finance/skills-marketplace/commits/main --jq '.sha'
```

The job also takes a manual trigger, which is the way to release without waiting
for the schedule:

```bash
gh workflow run sync-skills-marketplace.yml --repo wildcat-finance/skills-marketplace
```

Two constraints follow from that route rather than from taste. Plugin sources in
`.claude-plugin/marketplace.json` stay relative paths, `./plugins/<name>`, so
sync packages each plugin out of the mirror instead of fetching it from
somewhere it may not be able to authenticate to. And a version bump is only
released once it has crossed all three links: merged here, mirrored there,
distributed by sync. An installed plugin can sit a whole evolution behind while
every one of those looks healthy.

### Which route a machine is on

Read it rather than assuming, because the update commands above only work on one
of them. A git-backed install holds a git checkout; an organisation-distributed
one holds an extracted package under an opaque identifier, with a marketplace id
and no remote, ref or commit recorded anywhere. Hexaemeron's Fiat states the
same distinction, and what to do about a controller behind its own repository, in
[plugin-currency.md](./plugins/hexaemeron/skills/fiat/references/plugin-currency.md).

Anthropic's [marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces)
carries the source rules, and the
[organisation plugin workflow](https://support.claude.com/en/articles/13837433)
carries the admin side.

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

Berean needs Python 3.9 or later and nothing else. Its checked-in reference
release and every verification path run offline. Ask:

```text
Use $berean to verify this release's citations, chain readings and promotion record against its pinned corpus.
```

The release contract, the gates and the refusals live in
[Berean's `SKILL.md`](./plugins/berean/skills/berean/SKILL.md).

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
| Berean | `berean` | docs, examples, schemas, scripts |
| Brevitas | `brevitas` | evals |
| Hermes | `hermes` | references and scripts inside the skill |
| Hexaemeron | `fiat`, `kronos`, `imprimatur`, `vulgate`, the vendored `x-ray`, `solidity-auditor` and `fizz`, and `protasis`, `elenchus`, `phylax`, `ephoros`, `metron`, `hypomnema` | agents, audit, docs |
| Janus | `janus` | a Foundry harness, hook-manifest schema, hostile reference hooks, the Wildcat host adapter, scripts |
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
`probitas` without making either one own the other's claims. Agents that can
show their sources were the next gap, and `berean` now carries the release
contract, verifier and evaluation corpus for them. The conformance suite for
hooks was the last, and [`janus`](./plugins/janus) now states what a hook may
observe and change around a host action and checks a hook against that
manifest, with the Wildcat v2.5 seam as its first host adapter.

Both tools the Commons had named as still missing now ship.

These are tools we wanted and then needed. Their formats, datasets, properties,
fixtures and tests become more useful when other teams can inspect, run and
improve them, so that is who they are for too.

If Wildcat Labs means what it says about the Commons, publishing only the work
that happens to be convenient is not enough. Fine. We'll do it ourselves.
