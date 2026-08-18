# Wildcat Labs skills

Agent skills written and used by [Wildcat Labs](https://wildcat.finance).
Read a plugin before running it: skills can execute commands and edit source.

- Plugin READMEs hold the detail, examples and current Next Fiat jobs.
- [`AGENTS.md`](./AGENTS.md) defines local-agent loading and repository checks.

## Choose the job, then the plugin

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

Alexandria preserves raw lending inputs under SHA-256, verifies releases
offline and derives only reviewed credit rows. Compound v3 Phase 0 pins 28
production Comets on 10 chains and records one provider-reported witness; it
does not establish interval history or an independent chain proof.

- Run [`alexandria.py`](./plugins/alexandria/scripts/alexandria.py).
- Read the [skill](./plugins/alexandria/skills/alexandria/SKILL.md),
  [harvest specification](./plugins/alexandria/docs/compound-v3-harvest.md),
  [credit-history-v0](./plugins/alexandria/examples/credit-history-v0/README.md)
  and [Compound v3 Phase 0 release](./plugins/alexandria/examples/compound-v3-phase0-v0/README.md).

### Ariadne

Ariadne binds a release digest to build, test, review and deployment evidence
with [in-toto](https://github.com/in-toto/attestation) statements and
[DSSE](https://github.com/secure-systems-lab/dsse) envelopes. Its 7 gates keep
absence, deltas, replay limits and external signature verification explicit.

- Run [`ariadne.py`](./plugins/ariadne/scripts/ariadne.py).
- Read the [skill](./plugins/ariadne/skills/ariadne/SKILL.md),
  [predicate](./plugins/ariadne/docs/solidity-release.md),
  [schema](./plugins/ariadne/schemas/solidity-release-v1.json) and
  [audit](./plugins/ariadne/audit/AUDIT.md). The suite carries 310 tests.

### Brevitas

Brevitas limits engineering-review structure after vocabulary and register
passes. Evidence outranks its 5-line finding and 15-line fence budgets:
addresses, hashes, `file:line` references, numbers, counterexamples,
reproduction steps and establishment limits survive.

- Run [`brevitas.py`](./plugins/brevitas/skills/brevitas/scripts/brevitas.py).
- Read the [skill](./plugins/brevitas/skills/brevitas/SKILL.md); it includes 3
  audit-derived cases and source-preservation checks.

### Hermes

Hermes measures one Solidity gas change through 6 fail-closed gates with
[Foundry](https://getfoundry.sh/): `forge snapshot`, `forge test`, `forge
snapshot --diff`, `forge test --gas-report`, pinned and unpinned tests, storage
and selector checks, then targeted evidence for persistent-state unchecked
arithmetic.

- Run [`hermes.py`](./plugins/hermes/skills/hermes/scripts/hermes.py).
- Read the [skill](./plugins/hermes/skills/hermes/SKILL.md) and its
  [12 optimisation classes](./plugins/hermes/skills/hermes/references/optimisation-catalogue.md).

### Hexaemeron

Hexaemeron runs an explicit study, runbook, implementation, audit, prose and
delivery loop. `hexctl` records hash-chained receipts; Fiat does not activate
unless the user names Hexaemeron or Fiat and asks to run it.

- Read [Fiat](./plugins/hexaemeron/skills/fiat/SKILL.md), run
  [`hexctl.py`](./plugins/hexaemeron/skills/fiat/scripts/hexctl.py), or select
  [`imprimatur`](./plugins/hexaemeron/skills/imprimatur),
  [`vulgate`](./plugins/hexaemeron/skills/vulgate) or
  [`kronos`](./plugins/hexaemeron/skills/kronos) separately.
- the Pashov Audit Group suite vendored verbatim (MIT; `LICENSE` and `NOTICE.md` in each skill directory);
- The Hexaemeron and Imprimatur suites record 124 and 55 tests; see the
  [audit](./plugins/hexaemeron/audit/AUDIT.md).

### Lemma

Lemma turns Solidity compiler inputs or Markdown into source-linked JSONL and
stops before embedding, indexing, retrieval or answering. Python 3.10 or later
is required; Solidity also needs pinned `solc`, Docker or Podman.

- Read the [`chunk` skill](./plugins/lemma/skills/chunk/SKILL.md).

### Lazarus

Lazarus captures a fixed-block Ethereum fixture, verifies EIP-1186 proof-backed
state and replays only exact recorded RPC requests without fallback. Capture
needs an archive RPC; verification and replay run offline on Python 3.11 or
later with the lockfile's 4 pinned dependencies.

- Read the [skill](./plugins/lazarus/skills/lazarus/SKILL.md); the suite has 144
  tests and a proof-checked Goldfinch demonstration.

### Pandects

Pandects supplies executable credit laws and broken specimens.
The catalogue holds ten laws across conservation, accrual and withdrawal. Nine are exact.
The 10 laws cover 3 families and its campaigns distinguish Foundry, Echidna
and Medusa evidence.

- Read the [plugin](./plugins/pandects) for laws, adapters and commands.

### Probitas

Probitas builds a sourced dossier from declared addresses without identity
inference or a score. Five gates separate address status, require venue and
block-range coverage, trace every figure, state unknowns and forbid an
unpublished rubric. It ships 11 fixtures, 15 registry venues and 276 tests;
`--fixtures` runs without a network.

- Run [`probitas.py`](./plugins/probitas/scripts/probitas.py).
- Read the [skill](./plugins/probitas/skills/probitas/SKILL.md),
  [example dossier](./plugins/probitas/docs/example-dossier.md),
  [adapter guide](./plugins/probitas/docs/adding-a-venue.md) and
  [audit](./plugins/probitas/audit/AUDIT.md).

### Sapheneia

Sapheneia shapes the agent's own replies for AuDHD engineers. Its 10 ranked
rules keep the action, boundary, state, evidence, unknowns and next step visible
without changing facts, diagnosis or register.

- Read the [skill](./plugins/sapheneia/skills/sapheneia/SKILL.md).

### Tabularium

Tabularium requires Python 3.9 or later and maps preserved records into
reproducible credit events. Goldfinch's
34 borrow and 477 repay entities produce 511 rows; Euler v1 and Euler V2 remain
venue-qualified. Compound v3 Phase 0 rebuilds 2 ordered calls and a signed
principal transition from 0 to `-6349137978`. A clean offline run establishes
internal consistency, not publisher authenticity or an independent chain proof.

- Run [`tabularium.py`](./plugins/tabularium/scripts/tabularium.py).
- Read the [skill](./plugins/tabularium/skills/tabularium/SKILL.md), adapter
  [guide](./plugins/tabularium/docs/adding-an-adapter.md),
  [release policy](./plugins/tabularium/docs/release-policy.md), releases
  [goldfinch-v0](./plugins/tabularium/examples/goldfinch-v0/README.md),
  [euler-v1-v0](./plugins/tabularium/examples/euler-v1-v0/README.md),
  [euler-v2-v0](./plugins/tabularium/examples/euler-v2-v0/README.md) and
  [Compound v3 Phase 0](./plugins/tabularium/examples/compound-v3-phase0-v0/README.md).
- Schemas: canonical events [v1](./plugins/tabularium/schemas/canonical-event-v1.json)
  and [v2](./plugins/tabularium/schemas/canonical-event-v2.json); coverage
  [v1](./plugins/tabularium/schemas/coverage-manifest-v1.json) and
  [v2](./plugins/tabularium/schemas/coverage-manifest-v2.json). The suite has
  135 tests; see its [audit](./plugins/tabularium/audit/AUDIT.md).

## Who these are for

Scores are out of 10 for doing the job. Five is the barrier for a worked
role-specific example; below 5, the role should read the output instead.

| Role | Alexandria | Ariadne | Brevitas | Hermes | Hexaemeron | Lemma | Lazarus | Pandects | Probitas | Sapheneia | Tabularium |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Developers | 8 | 8 | 8 | 9 | 9 | 6 | 8 | 8 | 4 | 8 | 7 |
| Security and audit | 8 | 9 | 10 | 7 | 8 | 4 | 8 | 9 | 5 | 7 | 7 |
| Marketing | 1 | 1 | 1 | 3 | 6 | 1 | 1 | 1 | 1 | 3 | 1 |
| Business development | 6 | 2 | 2 | 2 | 5 | 1 | 2 | 2 | 9 | 4 | 3 |
| Finance | 8 | 1 | 2 | 3 | 4 | 1 | 2 | 2 | 7 | 4 | 7 |
| Legal | 3 | 3 | 2 | 1 | 4 | 1 | 2 | 2 | 4 | 4 | 2 |

## Install

### Codex

```bash
codex plugin marketplace add wildcat-finance/skills
codex plugin marketplace list
codex plugin marketplace upgrade wildcat-labs
```

Restart the ChatGPT desktop app, open the Plugins Directory and install from
Wildcat Labs. See OpenAI's [packaging documentation](https://developers.openai.com/plugins/build/plugins).

### Claude Code

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

Run `/reload-plugins` when the install summary asks. Claude uses qualified
names such as `/alexandria:alexandria`, `/ariadne:ariadne`,
`/brevitas:brevitas`, `/hermes:hermes`, `/hexaemeron:fiat "<topic>"`,
`/lemma:chunk`, `/lazarus:lazarus`, `/pandects:pandects`,
`/probitas:probitas`, `/sapheneia:sapheneia` and
`/tabularium:tabularium`. See Anthropic's [skills](https://code.claude.com/docs/en/skills)
and [marketplace](https://code.claude.com/docs/en/plugin-marketplaces) docs.

### Local agents

Host-neutral entries live under [`.agents/skills`](./.agents/skills). Keep the
repository layout intact: entries route to canonical plugin instructions rather
than copying them. The host manifests change discovery, not skill meaning.

### Invocation

```text
Use $alexandria to preserve this lending-data capture, derive its reviewed credit rows, and query the declared address without hiding coverage gaps.
Use $ariadne to capture this release in an evidence statement, run its gates, and report its signature state without checking signatures.
Use $brevitas to compress this engineering review without dropping addresses, transaction hashes, file:line references, numbers, counterexamples or reproduction steps.
Use $hermes to optimise gas in this repository. Work one optimisation class at a time and keep the complete verification record.
Use $hexaemeron to take "<topic>" from study to a merged delivery, one receipted phase at a time.
Use $chunk to turn this Solidity standard input into validated JSONL chunks.
Use $lazarus to capture this finite historical fixture, verify its proof-backed state, and replay only its exact requests.
Use $pandects to check this credit protocol against the executable laws in the corpus.
Use $probitas to build a sourced dossier on "<entity>" from the addresses they declared.
Use $sapheneia to shape your replies for an AuDHD reader throughout this task.
Use $tabularium to rebuild the checked-in Euler V2 release and verify it offline.
```

## Wildcat Commons

The Commons work publishes reusable records, laws and replay boundaries rather
than keeping them inside Wildcat. Remaining public-good candidates:

- `berean`: release manifest and evaluation corpus for source-grounded agents.
- `janus`: conformance suite for what hooks may observe and change around a host action.

These tools carry their own evidence and establishment limits so another team
can inspect, run and improve them without adopting Wildcat.
