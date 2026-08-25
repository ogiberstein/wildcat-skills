## Step 1, round 1 -- 2026-08-25T10:54:06Z

Audit schema: fiat-audit-round/v2

Covered: signed-lineage=reviewed; receipt-provenance=reviewed; merge-parent-order=reviewed; base-drift=reviewed; conflict-resolution=reviewed; controller-regression=reviewed; version-collision=not-applicable; audit-prefix-divergence=reviewed; audit-record-relocation=reviewed; synopsis-name-collision=reviewed; schema-topology=reviewed; synopsis-drift=reviewed; partial-write=reviewed; path-boundary=reviewed; attribution-loss=reviewed; scope-creep=reviewed; integration-key-defect=reviewed

Not checked: the waived Pashov Solidity suite, native Windows execution, live integration, Step 2 release allocation, and final publication

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | A source change after planning could let the writer return success with stale output, and a post-write refusal could leave writer-owned destinations changed. | fixed in this commit; source currency and exact refusal rollback guards added |

Leads not pursued: `origin/main` advanced from `c4650f02a979e859ce36374779eac9cd70744288` to `55c60852ead94812596cb9ea91ca11bf1b08f260`, so integration must use the receipted product-first sync and Step 2 must re-resolve release predecessors; issues 557, 608, 453, 369, and 363 remain open and outside this step; cross-file crash atomicity remains the documented generator limit, while caught refusals now restore every attempted destination; Horos reported new synopsis candidates without hard-classifying them; the inherited unclosed-file `ResourceWarning` at `plugins/hexaemeron/tests/test_hexctl.py:5796` remains outside this finding
