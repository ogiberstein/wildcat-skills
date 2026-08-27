# Goldfinch receipt inclusion delivery proof

## Authority and source boundary

This record covers Fiat issue 383, Step 5, `Ship and demonstrate the Goldfinch
receipt proof`. Implementation started from signed parent
`c883ff1cb3e86080884175088cfba403146a6269` on
`fiat/383-prove-receipts-against-the-captured-header-s-step-4-carry-the-proof-through-release`.
The implementation branch is
`fiat/383-prove-receipts-against-the-captured-header-s-step-5-ship-and-demonstrate-the-goldfin`.

The controlling evidence for the final Files boundary is:

| Record | SHA-256 | Authority |
| --- | --- | --- |
| Study | `f8dd4bad531e8dbc236fec0bf0580d4a6a3a6284ce293a57a4d37af8555f9b79` | Design facts |
| Canonical runbook after the Step 5 Files amendments | `3177299cf04829a1de2586c08cc5398f554e988bf7bb0394e013674d366aff81` | Step contract |
| Effective Step 5 | `2ab8efb073ed71d3a7d9c590f721c4756daabb546c76051f217d877210513e5f` | Implementation packet |
| Implementation packet state | `be7ece5732424cd67ab5a9cbc7bcd38a40c51fa71e16ed1b7f265aadae12b9eb` | Implementation hand-off |
| Audit directive state | `4dc757ae7b97cf2718f724a09efc14b17dc0a95f9f613d89fb49296dfed3343e` | Audit round packet |
| Entry-repair amendment | `8df12aee81fc0b381793c659920314bb8124382fa8432c313e380c5607a8d015` | Entry repair |
| Lazarus marketplace-copy Files amendment | `508be2c58135a2b0c6aeb180343c7f9a4b2e56e3efe8adec4e24ad1feb453cb5` | Two prose copies |
| Manifest writer-selection Files amendment | `86ff0bd9c61febf3f087cb9da259902692f2805282afdbd8ea38150cbc8714d9` | Cause fix |
| Receipt fixture restamp Files amendment | `7ca1ee04ab6910d5f19769bd249156c31d0f02239dc79655bcb7b4de8d6e3544` | Version propagation |
| Preservation-guide Files amendment | `2423b45f020338cef35c7d6b234104ae7cb65a44a21533c10d4eadf820160880` | Governed context repair |

Each repair added only the paths named by its receipt. The Step 5 implementation
worker ran no controller command, network capture, push, publication, merge or
issue mutation. The Fiat orchestrator separately receipted the amendments,
implementation and this audit directive.

## Shipped artefacts and claims

The fixed fixture at `plugins/lazarus/examples/goldfinch-v1` verifies to:

| Field | Verified value | Evidence class |
| --- | --- | --- |
| Ethereum block | `0xc7da16` | Header bound |
| Block hash | `0x41119192a8acdaae5ab06ca8f1d5943fd7ca2fb0a14323642dd6daf74eed2cfc` | Header bound |
| Receipts root | `0xaf03b0508121deb9ed0282a8961dc0ea695a97244a42ed2b0af04cb9bbc6226e` | Recomputed |
| Ordered consensus receipts | 224 | Recomputed |
| Target trie index | `0xbf` | Receipt-trie proved |
| Target consensus logs | 110 | Receipt-trie proved |
| Filtered consensus-log projection | 5 | Receipt-trie proved |
| Receipt-trie-proved relations | 2 | Recomputed count |
| Evidence counts | `proof_backed=2`, `header_bound=1`, `recorded_rpc=5`, `receipt_trie_proved=2` | Recomputed inventory |
| Transaction-hash attribution | `recorded_rpc` | Recorded only |

The public fixture copies the six captured source components from
`plugins/lazarus/tests/fixtures/receipt-proof-v1` byte for byte: `anchors.jsonl`,
`header.json`, `plan.json`, `proofs.jsonl`, `receipt-witness.json` and
`rpc.jsonl`. Its own `demo.py` and manifest make the published demonstration a
separate deterministic fixture. The internal manifest-v2 was restamped from
writer 0.1.0 to 0.2.0 without changing any raw source component.

| Artefact identity | SHA-256 | Digest scope |
| --- | --- | --- |
| Goldfinch v1 fixture digest | `64c4fdb4ae977e5588f6ceb14e8ba42992d7cfa958ce46e66ecb8bacc885c0e5` | Semantic manifest identity |
| Goldfinch v1 manifest file | `a8c9bbf98fe25b985be53d0829e863ff72bfd456361c19f7d0b19bfea1a3b2d2` | Raw file bytes |
| Ariadne state-fixture/v2 statement file | `076abcbefb1ada13d01c50d709584412e55e9ec32c72b2986ad7ebb53fb88e90` | Raw file bytes |
| Goldfinch v1 release digest | `a374e87b6f9d082edfef2bf698c1a19330e67c756a1bd23601889a41b6c7a5f7` | Semantic release identity |
| Goldfinch v1 release file | `21f354926f6ad356d42946d69080d37026028b475ba1eee1a6aee59fcab4be1b` | Raw file bytes |
| Restamped internal receipt manifest file | `f9bd4a3e9192ec4d472b4b9127fd66871f87d5b60f75b34a3f82c7d6e1213558` | Raw file bytes |
| Restamped internal fixture digest | `a88218e27b979a67941bd66f04eec9e0d1208178697c0c3f59a245f22dba0eec` | Semantic manifest identity |

`goldfinch-v1-release` contains the exact fixture copy, the deterministic
state-fixture/v2 statement and release-v2 binding. The statement and release
carry `receipts_root` and the count of two scoped relations. They explicitly do
not claim that the receipt trie attributes a transaction hash, that the block
is canonical, or that the recorded providers are independent.

The historical Goldfinch release remains byte-identical:

| Historical identity | SHA-256 | Digest scope |
| --- | --- | --- |
| Goldfinch v0 fixture digest | `d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49` | Semantic manifest identity |
| Goldfinch v0 manifest file | `c37cd789e5386a1347abd4dff24c8b1db96cdab771df4eb4d63056ba56145fa9` | Raw file bytes |
| Goldfinch v0 statement file | `d8b262278ffd4db76e449a2bfce4629903a70e7f4ad7c1f3a6ebbfb1f112555e` | Raw file bytes |
| Goldfinch v0 release file | `ec5c9b8091286de8713b6daf6cfdeaa7e9cfa6177b96c10a2ed20ffd6654bcff` | Raw file bytes |

Writer 0.2.0 stamps new output. An exact deterministic rebuild of the existing
historical manifest-v1 preserves writer 0.1.0. Installable package versions are
Lazarus 1.1.2 and Ariadne 1.2.2. The governed skill labels are `lazarus-v2.2.0` and
`ariadne-v2.2.0`; those are separate version axes.

## Elenchus guards

Four observed failures were localised before the final run:

1. The index mutation failed while canonical witness bytes were being written,
   before the helper's original verification-only exception boundary. The
   helper now treats rejection during mutation write or final verification as
   the same expected fail-closed result. The index mutation test fails if that
   rejection disappears.
2. Raising the writer to 0.2.0 caused the unchanged Goldfinch v0 demo's
   byte-identical manifest rebuild to relabel manifest-v1. The first repair then
   selected writer 0.1.0 by schema and mislabeled fresh plan-v1 captures made by
   writer 0.2.0. Manifest construction now preserves writer 0.1.0 only for an
   exact existing historical rebuild; fresh manifest-v1 and manifest-v2 output
   use writer 0.2.0. Both demonstrations, a fresh plan-v1 capture and the v0/v1
   coexistence tests guard the distinction.
3. The first full Lazarus run found the Step 2/3 receipt fixture and capture
   digest still pinned to writer 0.1.0. The manifest-v2 and its exact capture
   digest pin moved together to 0.2.0; all six raw source components stayed
   byte-identical. The deterministic receipt rebuild and recapture tests guard
   the restamp.
4. Ariadne's documentation checks refused three cross-plugin relative links in
   the new receipt hand-off prose. The prose now names the Lazarus paths and
   command boundary without creating links outside Ariadne's plugin root. The
   existing documentation-link suite guards that ownership boundary.
5. The cold read omitted an unmarked marketplace context in the preservation
   guide. Its stale frontier and receipt claims remained public while the proof
   called a five-copy marker inventory complete. The guide now carries the
   governed current block, describes both release versions and passes the
   structural prose gate; the 165-file inventory includes its exact bytes.

The end-to-end demonstration independently rejects a one-byte consensus
receipt, index, consensus log, receipts root, evidence count and release
mutation. A coherent transaction-hash rewrite leaves the root and both proved
relations unchanged. A one-source rewrite is rejected as
`recorded RPC transaction hash disagreement`, without `root` or `proved` in the
diagnostic.

## Discipline evidence

**Phylax.** Step 5 performed no provider capture. It reused the fixed bounded
source captured under Step 3's request, byte, time, secret-union and atomic
controls. Fixture verification, statement capture, release build and release
verification accept local paths only. The demo patches both socket connection
entry points to fail on use and reports `network=denied`. No dependency changed.
An independent `strace -f -e trace=network` run observed no socket, connect,
bind, listen, accept, endpoint send/receive or socket-option syscall.

**Ephoros.** The demo emits one canonical JSON line with correlation ID
`goldfinch-v1-offline-demo`. It includes the safe block identity, root, bounded
counts, scoped relation, versions, digests and named mutation verdicts. Tests
refuse extra lines and scan the event for topics, data, RPC URL forms,
credentials and bearer material. Receipt bodies and log payloads are absent.

**Metron.** No performance claim is made. The test durations below establish
only that the fixed offline checks completed in the locked environment; they do
not promise provider speed, replay throughput or a performance budget.

**Hypomnema.** ADR-036 holds the full ordered-witness decision and rejected
alternatives. `plugins/lazarus/docs/receipt-inclusion-proofs.md` holds the
operator boundary. Ariadne's state-fixture guide holds the statement boundary.
This proof holds the shipped evidence. The Lazarus and Ariadne evolution ledgers
each contain exactly one new row for their own version axis.

## Complete mutable marketplace inventory

The cold read used the same mutable marker boundary as
`tests/test_marketplace_prose.py`: every first-party Markdown file containing a
`marketplace-context` block, excluding historical audit records and the three
vendored Pashov skill roots. It also read the root collective README, both root
marketplace registries, every plugin's two host manifests, and every shipped
`agents/openai.yaml`. For each sorted path, inventory digest material is
`path`, a NUL byte, the file SHA-256 and a newline.

The 111 context-bearing Markdown paths are:

| Plugin | Count | Exact path set |
| --- | ---: | --- |
| Alexandria | 14 | `plugins/alexandria/{AGENTS.md,README.md,docs/{address-index.md,compound-v3-harvest.md,credit-view.md,data-dictionary.md,raw-releases.md,runbook.md,study.md},examples/{README.md,compound-v3-phase0-v0/README.md,credit-history-v0/README.md},schemas/README.md,skills/alexandria/SKILL.md}` |
| Ariadne | 14 | `plugins/ariadne/{AGENTS.md,README.md,docs/{capturing-a-dataset.md,capturing-a-release.md,capturing-a-state-fixture.md,conformance.md,dataset.md,design.md,solidity-release.md,state-fixture.md},examples/README.md,skills/ariadne/SKILL.md,tests/fixtures/{dataset-release/README.md,forge-project/README.md}}` |
| Berean | 9 | `plugins/berean/{AGENTS.md,README.md,docs/{answers.md,design.md,influences.md,release-policy.md,spec.md},examples/goldfinch-demo-v0/README.md,skills/berean/SKILL.md}` |
| Brevitas | 3 | `plugins/brevitas/{AGENTS.md,README.md,skills/brevitas/SKILL.md}` |
| Hermes | 4 | `plugins/hermes/{AGENTS.md,README.md,skills/hermes/{SKILL.md,references/optimisation-catalogue.md}}` |
| Hexaemeron | 6 | `plugins/hexaemeron/{AGENTS.md,README.md,agents/{mason.md,scribe.md,surveyor.md,warden.md}}` |
| Horos | 2 | `plugins/horos/{AGENTS.md,README.md}` |
| Janus | 3 | `plugins/janus/{AGENTS.md,README.md,skills/janus/SKILL.md}` |
| Lazarus | 6 | `plugins/lazarus/{AGENTS.md,README.md,docs/{preservation-release.md,runbook.md,study.md},skills/lazarus/SKILL.md}` |
| Lemma | 15 | `plugins/lemma/{AGENTS.md,INVARIANTS.md,README.md,baseline/{README.md,docs/{README.md,SUMMARY.md,concepts/{entries.md,fixed-point.md},reference/{contracts.md,errors.md},user-guide/{day-to-day-usage/{README.md,creating.md,retiring.md},troubleshooting.md}}},skills/lemma/SKILL.md}` |
| Pandects | 8 | `plugins/pandects/{AGENTS.md,README.md,adapters/medusa/README.md,docs/{applicability.md,design.md,writing-a-law.md},integrations/wildcat/APPLICABILITY.md,skills/pandects/SKILL.md}` |
| Probitas | 8 | `plugins/probitas/{AGENTS.md,README.md,assets/dossier-template.md,docs/{adding-a-venue.md,example-dossier.md},skills/probitas/{SKILL.md,references/{gates.md,venues.md}}}` |
| Sapheneia | 3 | `plugins/sapheneia/{AGENTS.md,README.md,skills/sapheneia/SKILL.md}` |
| Tabularium | 16 | `plugins/tabularium/{AGENTS.md,README.md,docs/{adding-an-adapter.md,compound-v3-preservation.md,euler-preservation-runbook.md,euler-preservation-study.md,release-policy.md},examples/{compound-v3-phase0-v0/{DATA-DICTIONARY.md,README.md},euler-v1-v0/{DATA-DICTIONARY.md,README.md},euler-v2-v0/{DATA-DICTIONARY.md,README.md},goldfinch-v0/{DATA-DICTIONARY.md,README.md}},skills/tabularium/SKILL.md}` |

The remaining exact path sets are `README.md`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`plugins/*/{.claude-plugin/plugin.json,.codex-plugin/plugin.json}`, and the 23
existing `plugins/*/skills/*/agents/openai.yaml` files. The complete inventory
therefore contains 165 files. Its final aggregate digest is
`5ab4e518211de5f4ae8b016dbb39ef1743595615c6c9ef2d7d100198e656cad7`;
the 114 context/root surfaces digest to
`30a559bd825b075f2153dad022e19faa30b65d46378032a5bc3a201d480dd1de`,
and the 51 host prose files digest to
`b643311cb5e533a50f9d662539b9770f974d219e3a0192483ad9abddebfb0d0b`.

Lazarus's six mutable context copies now carry the same completed frontier and
successor job. Ariadne retains its grounded-agent frontier text and digest byte
for byte; only its receipt-aware hand-off explanation and generation metadata
changed. Both host manifests and the Claude marketplace carry package versions
1.1.2 and 1.2.2. The Agents marketplace has no version or prose field for these
plugins and remained unchanged. All unrelated frontier claims remained
unchanged, and the marketplace-prose gate found no disagreement to file.

## Verification ledger

All commands ran from the final Step 5 worktree in the locked Python 3.12.3
environment at `/tmp/fiat383-r6-venv.iPGZQK`. The final exhaustive exits and
counts are recorded here after the final bytes are fixed.

| Gate | Result | Evidence |
| --- | --- | --- |
| Exact Step 5 entry combined runner | exit 0, 1259 tests, 85.516 seconds | Entry report |
| Warden source-bound entry runner | exit 0, 1,270 tests, 96.324 seconds | Report SHA-256 `410f723d860c7c3ae5ecd9e738fe9797ed6898b83a1a3fc115ea12e5411976a7` |
| New and legacy Goldfinch/release/scaffold focus | exit 0, 49 tests | Focused unittest output |
| Marketplace, version and evolution focus | exit 0, 36 tests | Focused unittest output |
| Ariadne plugin suite | exit 0, 689 tests | Combined-runner output |
| Lazarus plugin suite | exit 0, 582 tests | Combined-runner output |
| Final combined receipt-delivery runner | exit 0, 1,271 tests, 93.171 seconds | Report SHA-256 `217b368e207bac22d5fc81501a92e5bf47de5ff801a5d07b213d29d106fec68a` |
| Root suite | exit 0, 396 tests in 29.833 seconds | Root unittest output |
| Promise Machine, demonstrations, repository lints and currency checks | exit 0 | Command exits |

The signed implementation and Warden commits plus the final clean-tree check are
the last evidence items; no push, publication or controller transition belongs
to this record.
