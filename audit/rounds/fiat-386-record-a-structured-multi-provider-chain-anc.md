# Issue 386: record a structured multi-provider chain anchor

## Step 1, round 1 -- 2026-08-25

Non-Solidity round over commit
`d917f41034743cb9d27db5e2da6eb27319f59ffb` on
`fiat/386-record-a-structured-multi-provider-chain-anc-step-1-define-the-anchor-formats`
against parent branch `fiat/386-record-a-structured-multi-provider-chain-anc`
at `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`. Security receipt:
`waived: issue 386 changes Lazarus Python, JSON schemas, tests, and documentation; no Solidity or Pashov security-suite target applies`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. The review covered all 16 changed paths against Step 1 at
effective SHA-256
`d861773977ffd121ac84e8b1da8b0e160396d1951869e3888293c0ab92f643a6`
and the risk register in `.hexaemeron/study.md` at SHA-256
`f16d14e2182f872d95e56b4485218a264286a845f80b2857960dcd32c14442fd`.
Plan v2 retains the complete plan-v1 shape and adds only 1 to 32 sorted, unique
source identifiers. Anchor records are closed, bounded, schema-digest-pinned,
UTC-checked, source-sorted, and source-unique; neither plan nor record admits a
provider URL, header, raw error, independence claim, or canonical-chain claim.
The temporary capture guard refuses plan v2 before client construction or
staging. The tracked study and runbook match the receipted bytes, and existing
manifest and release schemas are unchanged.

The focused schema, record, scaffold, and runner set reports 61/61. The source-
owned runner reports 386/386 Lazarus tests, and the root suite reports 350/350.
Phylax exits 0 over `plugins tests`; Ephoros exits 0 over `plugins tests`;
Hypomnema exits 0 over `README.md AGENTS.md .agents plugins docs`.

Leads not pursued: live provider disagreement, runtime secret scanning, shared
network budgets, atomic multi-provider finalisation, digest-bound one-read
verification, exact plan-to-record coverage, and anchored release compatibility
are not reachable in this format-only step. Step 1 refuses plan-v2 capture;
Steps 2 and 3 own those transitions. These remain required risk-register
checks, not accepted risks.
