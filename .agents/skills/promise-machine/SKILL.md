---
name: promise-machine
description: Route any Wildcat Labs skill request through the Promise Machine contract to one canonical skill without widening its evidence, boundary or authorised transition.
---

# Promise Machine router

This is the suite's only host-neutral discovery entry. It has no behavioural
version and owns no domain promise. Read the [root runtime
contract](../../../AGENTS.md) first; that contract loads the suite law and sets
the repository-wide selection boundary.

## Select one runtime contract

Match the request to the narrowest row, read that runtime contract in full and
use its selection table to load exactly one canonical `SKILL.md`. Load another
canonical skill only when the selected workflow requires a named handoff.

| Request | Runtime contract | Canonical selection |
| --- | --- | --- |
| Preserve lending inputs or derive a reviewed credit view | [Alexandria](../../../plugins/alexandria/AGENTS.md) | `alexandria` |
| Bind a release digest to its evidence record | [Ariadne](../../../plugins/ariadne/AGENTS.md) | `ariadne` |
| Verify a protocol agent against pinned corpora and chain reads | [Berean](../../../plugins/berean/AGENTS.md) | `berean` |
| Constrain the volume and structure of engineering prose | [Brevitas](../../../plugins/brevitas/AGENTS.md) | `brevitas` |
| Measure one Solidity gas-optimisation class | [Hermes](../../../plugins/hermes/AGENTS.md) | `hermes` |
| Run receipted delivery or a named specification, audit, debugging, hardening, telemetry, measurement or record-keeping phase | [Hexaemeron](../../../plugins/hexaemeron/AGENTS.md) | One named Hexaemeron skill |
| Classify evidenced reading sinks | [Horos](../../../plugins/horos/AGENTS.md) | `horos` |
| Check hook effects around a host action | [Janus](../../../plugins/janus/AGENTS.md) | `janus` |
| Preserve finite historical Ethereum state and exact RPC traffic | [Lazarus](../../../plugins/lazarus/AGENTS.md) | `lazarus` |
| Produce source-linked Solidity or Markdown chunks | [Lemma](../../../plugins/lemma/AGENTS.md) | `lemma` |
| Apply executable credit laws | [Pandects](../../../plugins/pandects/AGENTS.md) | `pandects` |
| Build a declared-address counterparty dossier | [Probitas](../../../plugins/probitas/AGENTS.md) | `probitas` |
| Shape the agent's own replies for an AuDHD reader | [Sapheneia](../../../plugins/sapheneia/AGENTS.md) | `sapheneia` |
| Build a venue-qualified credit-event release | [Tabularium](../../../plugins/tabularium/AGENTS.md) | `tabularium` |

## Preserve the selected promise

The canonical skill and its runtime contract are authoritative. Invocation
aliases change only how a request reaches that skill. They never strengthen an
evidence class, erase a refusal or recovery path, widen scope, or authorise a
more consequential transition.

If no row matches, stop at inspection and explain the uncovered boundary. Do
not improvise a new suite capability or treat this router as permission to run
Fiat, Kronos or any external action.
