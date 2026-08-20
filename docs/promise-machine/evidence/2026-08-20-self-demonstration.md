# Promise Machine self-demonstration

- Date: 2026-08-20
- Candidate base: `f2b76d0cb1a8973c744bf879b38c6df72884f904`
- Host: macOS, Python 3.14.6, Forge 1.7.1 and uv 0.12.5
- Codex: `codex-cli 0.147.0`
- Claude Code: 2.1.234
- Evidence class: observed local command and resolver transcripts

This record demonstrates repository conformance and the discovery state that
the available host controls could inspect. It does not turn repository
correctness into a claim about model judgement. The two unavailable manual
surfaces remain named below.

## Result

| Surface | Observed result | Boundary |
| --- | --- | --- |
| Complete repository gate | Pass | 14 plugins, 28 canonical skills, 23 governed skills, five vendored skills, one router and one overlay |
| Runtime coverage | Pass | 14 plugin copies and 29 level-2 or level-3 runtime bindings |
| Checker timing | Pass | 0.11 seconds real time against a five-second budget |
| Codex package and resolver state | Pass | 14 release-candidate packages installed; one qualified Protasis and one unversioned suite router in the model-visible registry |
| Codex picker screenshot | Not observed | Computer control refused access to the Codex app; no screenshot is claimed |
| Claude package state | Pass | 14 release-candidate packages installed and Hexaemeron exposes Protasis |
| Claude slash invocation | Not observed | The invocation stopped at an expired OAuth token with HTTP 401; no model result is claimed |
| Host-neutral discovery | Pass | The only `SKILL.md` below `.agents/skills/` is `promise-machine`; its routes resolve to the three tested runtime contracts |

## Deterministic gates

The following suites ran from their shipped boundaries and returned zero
failures unless a skip is shown.

| Gate | Result | Evidence boundary |
| --- | --- | --- |
| Root repository suite | 104 passed | `tests/` |
| Alexandria | 255 passed | plugin Python suite |
| Ariadne | 632 passed, six skipped | plugin Python suite |
| Berean release verifier and evaluation suite | 151 passed | plugin Python suite and shipped fixtures |
| Brevitas | 21 passed | plugin Python suite |
| Hermes | 14 passed | shipped harness tests |
| Hexaemeron | 474 passed | plugin test runner |
| Imprimatur | 62 passed | skill test runner |
| Horos | 212 passed | plugin Python suite |
| Janus Python suite | 14 passed | plugin Python suite |
| Janus Foundry harness | 24 passed | `plugins/janus/harness/` |
| Lemma Markdown and Solidity harnesses | zero failures | two shipped script suites |
| Lazarus | 364 passed in its pinned uv environment | plugin Python suite |
| Pandects Python suite | 116 passed | plugin Python suite |
| Pandects Foundry suite | 79 passed | `plugins/pandects/` |
| Probitas | 276 passed | plugin Python suite |
| Sapheneia | nine passed | plugin Python suite |
| Tabularium | 134 passed | plugin Python suite |

Janus and Pandects emitted their expected Foundry warnings and passed. No
Solidity file differs from the preceding Step 8 branch, so the suite-wide
Solidity audit remained waived. The two named Foundry suites still ran because
their evidence contracts changed during this delivery.

The timing transcript was:

```text
clean: 14 plugin(s), 14 copy/copies
real 0.11
user 0.08
sys 0.03
```

## Codex observation

The supported marketplace installer refreshed `wildcat-labs` from the
published Step 8 branch. `codex plugin list` then reported all 14 packages as
installed and enabled at the package versions declared by this release,
including Hexaemeron 1.5.1, Berean 0.1.1 and Janus 0.1.1.

The model-visible prompt resolver was inspected with:

```bash
codex debug prompt-input '/prot'
```

The relevant registry lines were:

```text
promise-machine: ... (file: r8/promise-machine/SKILL.md)
berean:berean: ... (file: r6/berean/0.1.1/skills/berean/SKILL.md)
hexaemeron:protasis: ... (file: r7/protasis/SKILL.md)
janus:janus: ... (file: r6/janus/0.1.1/skills/janus/SKILL.md)
```

There was no bare `protasis`, `berean` or `janus` skill entry. The installed
ledgers reported `protasis-v2.2.0`, `berean-v0.1.0` and `janus-v0.1.0`.
The Promise Machine entry carried no version.

Computer control returned `Computer Use is not allowed to use the app
'com.openai.codex' for safety reasons.` The picker screenshot required by the
runbook was therefore not observable from this task. The resolver transcript
is evidence of the registry Codex sends to the model, not evidence of how the
picker rendered it.

## Claude Code observation

The supported marketplace installer refreshed the local candidate and
installed all 14 packages. `claude plugin details hexaemeron@wildcat-labs`
reported Hexaemeron 1.5.1 and a 13-skill component inventory containing
`protasis`. Its installed ledger reported `protasis-v2.2.0`.

The exact command invocation was attempted:

```text
/hexaemeron:protasis Return only the current canonical Protasis version from
the installed skill ledger, followed by the canonical SKILL.md path.
```

Claude Code stopped before resolving a model response:

```text
Failed to authenticate. API Error: 401 OAuth access token has expired.
Re-authenticate to continue.
```

The package and component discovery are observed. Successful slash execution
is not observed and is not inferred from installation.

## Host-neutral observation

Searching for `SKILL.md` exactly two levels below `.agents/skills/` returned:

```text
.agents/skills/promise-machine/SKILL.md
```

The router linked to the Hexaemeron, Berean and Janus runtime contracts. Those
contracts selected `skills/protasis/SKILL.md`, `skills/berean/SKILL.md` and
`skills/janus/SKILL.md`; their ledgers reported `protasis-v2.2.0`,
`berean-v0.1.0` and `janus-v0.1.0`. No version field occurred in the router.

## Remaining host evidence

Two observations require a user-controlled host boundary:

1. restart the Codex desktop app and capture the `/prot` picker after the final
   `main` marketplace refresh;
2. re-authenticate Claude Code and capture a successful
   `/hexaemeron:protasis` invocation after the final refresh.

Neither missing observation weakens the deterministic contract results above.
Neither is represented as complete.
