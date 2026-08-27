## Step 1, round 1 -- 2026-08-27T04:24:29Z

Audit schema: fiat-audit-round/v2

Covered: window-partial-lines=not-applicable; string-at-line-start=not-applicable; comment-invited-exclusion=not-applicable; monotone-narrowing=not-applicable; boundary-regeneration=not-applicable; recall-loss-docstring=not-applicable; evidence-wording=not-applicable; prose-reconciliation=not-applicable; corroboration-flow=not-applicable

Not checked: the study's technical claims against plugins/horos source (no rule code changed this step; the later code steps gate them), and the horos unit suites (no fixes commit, so the Elenchus runner was not invoked). Coverage note: every register id names classifier behaviour changed in later steps; this diff adds two verbatim doc copies and touches no code, hence not-applicable across the register.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/horos/docs/marker-self-exclusion/study.md | hypomnema exited 1 with five H001 hits (phylax and ephoros exited 0 on both copies): relative discipline links resolve to nothing at the copy location — line 341 `../ephoros/SKILL.md`, 359 `../phylax/SKILL.md`, 379 `../metron/SKILL.md`, 391 `../elenchus/SKILL.md`, 407 `../hypomnema/SKILL.md`. The copy is byte-identical to the receipted study (sha256 3316b6fa5635a60ba6376f4717c2c89999f5ccd17e77cab9700cfa4bb400625f), the runbook copy matches the run runbook (sha256 2d23073ee22ac939151ec9c9878b9257af30355776b16835f0fda58c79190d4d), and editing the links would break the byte fidelity this step exists to provide; the links dangle in the receipted original too. | accepted |

Leads not pursued: adding a sibling README in plugins/horos/docs/marker-self-exclusion/ stating the copies are verbatim and the discipline links resolve relative to the hexaemeron skills tree — not pursued because the runbook step names exactly the two copies and an extra file is the controller's call, not an audit fix; raised in the round report instead.

## Step 1, round 2 -- 2026-08-27T04:37:13Z

Audit schema: fiat-audit-round/v2

Covered: window-partial-lines=not-applicable; string-at-line-start=not-applicable; comment-invited-exclusion=reviewed; monotone-narrowing=not-applicable; boundary-regeneration=reviewed; recall-loss-docstring=not-applicable; evidence-wording=not-applicable; prose-reconciliation=not-applicable; corroboration-flow=not-applicable

Not checked: the study's technical claims against plugins/horos source (the later code steps gate them). Coverage note: boundary-regeneration and comment-invited-exclusion move from round 1's not-applicable to reviewed because round 2 exercised both -- the committed boundary drifted and was regenerated, and content-invited self-exclusion was observed on the study copy itself; the remaining ids still name classifier behaviour that changes only in later steps. Round 2 gates: phylax, ephoros and hypomnema all exit 0 on both copies; the step Elenchus runner (horos suite) ran 217 tests OK with its report at .hexaemeron/elenchus-step-1.txt; the root suite (unittest discover -s tests) ran 399 tests OK.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/horos/docs/marker-self-exclusion/study.md | round 1's five dangling discipline links (lines 341, 359, 379, 391, 407) now target `../../../hexaemeron/skills/<name>/SKILL.md` for ephoros, phylax, metron, elenchus and hypomnema, each verified to resolve from the file's directory; fixed on the step branch in commit 6f36bee9560638376e3609bfd5831661dc118390 (signed, verify-commit good); byte fidelity was dropped as a requirement by the controller, and the pinned receipted original .hexaemeron/study.md was not touched | fixed |
| S1-R2-01 | medium | .horos/boundary.json | pre-existing at step commit 8942785: the committed boundary was stale because the committed study copy quotes the marker 'do not edit' inside its first 4096 bytes and self-excludes under the current rule -- a fresh scan adds a hard generated entry (bytes 26602, evidence: marker 'do not edit' in the first 4096 bytes) and tests/test_boundary_currency.py failed at unmodified HEAD, verified by stashing round 2's link edit, which sits past byte 4096 and cannot have caused it; regenerated via `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and committed as 52b33a59feb01cc081ccbabb27fe64149c1603a7 (signed, verify-commit good); this is the run's motivating self-exclusion defect surfacing on its own spec copy, and the entry un-excludes when a later step narrows the rule and regenerates the boundary | fixed |

Leads not pursued: the sibling README in plugins/horos/docs/marker-self-exclusion/ explaining the copy convention, carried from round 1 (the controller's call, not an audit fix); no new guard test for spec-copy boundary currency, because tests/test_boundary_currency.py already fails on any drift and is the guard that caught S1-R2-01.

## Step 1, round 3 -- 2026-08-27T04:40:24Z

Audit schema: fiat-audit-round/v2

Covered: window-partial-lines=not-applicable; string-at-line-start=not-applicable; comment-invited-exclusion=reviewed; monotone-narrowing=not-applicable; boundary-regeneration=reviewed; recall-loss-docstring=not-applicable; evidence-wording=not-applicable; prose-reconciliation=not-applicable; corroboration-flow=not-applicable

Not checked: the study's technical claims against plugins/horos source (the later code steps gate them); the seven not-applicable ids still name classifier behaviour that changes only in later steps. Round 3 gates against the fixed tree at 52b33a59feb01cc081ccbabb27fe64149c1603a7: phylax, ephoros and hypomnema all exit 0 on both copies; horos.py check exits 0 (boundary matches the tree); the horos suite ran 217 tests OK and the root suite ran 399 tests OK, both under the GIT_CONFIG prefix. The round-2 diff 8942785..52b33a5 re-reviewed in full: study.md carries exactly the five link retargets, and .horos/boundary.json carries exactly the one self-exclusion entry for the study copy plus the two count fields that follow from it; no regressions, nothing else rode in.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the sibling README in plugins/horos/docs/marker-self-exclusion/ explaining the copy convention, carried from rounds 1 and 2 (the controller's call, not an audit fix); the committed boundary's files_walked count (1654) absorbed four untracked working files present at scan time -- not pursued as a finding because drift comparison in horos.py (drifted paths, a symmetric entries-only compare) never reads the counts, so the snapshot is cosmetic metadata with no gate effect.

## Step 2, round 1 -- 2026-08-27T05:15:02Z

Audit schema: fiat-audit-round/v2

Covered: window-partial-lines=reviewed; string-at-line-start=reviewed; comment-invited-exclusion=reviewed; monotone-narrowing=reviewed; boundary-regeneration=reviewed; recall-loss-docstring=reviewed; evidence-wording=reviewed; prose-reconciliation=not-applicable; corroboration-flow=reviewed

Not checked: prose-reconciliation is gated by its own dedicated late step (tests/test_marketplace_prose.py did pass inside the root suite); the metron step-exit medians were taken from the step report, not re-measured this round -- before median 114.3 ms (spread 106.4-124.5), after median 110.1 ms (spread 108.5-129.1), five runs each, same session, -3.7%. Round 1 gates: phylax, ephoros and hypomnema all exit 0 on horos.py and test_classify.py (re-run exit 0 on the fixed horos.py); the horos suite ran 228 tests OK and the root suite 399 tests OK under the GIT_CONFIG prefix, before and after the fix; horos.py check . exits 0 (boundary matches the tree); the committed census byte-matches a fresh scan --census --json. Red observed independently: with b1cf533's horos.py restored the suite fails with 30 failures, then goes green on restore. Window arithmetic probed beyond the shipped tests: an offset landing on the previous line's newline binds the following banner at that exact offset; a banner as the file's true last line binds with and without a trailing newline; a marker split by the 4096-byte prefix edge stays readable (fail-open); a multibyte run ahead of a late banner still binds; a CRLF late banner binds; a CR-only large file is intercepted at the prefix as a blob candidate before any window runs. Monotone narrowing verified structurally (the gate is a pure filter over the same decoded text both passes always read, every other rule is untouched, and corroboration hits can only decrease) and observationally: the boundary diff only removes or re-words entries, never adds one, and the 102,496-byte drop in bytes_generated is exactly the study's predicted 69,062 plus the audit log (6,832) and the study copy (26,602), both boundary entries that post-date the study's prediction. The promise-machine diff at a85380d is exactly one sha256 line and that digest matches the step's horos.py bytes; the fields map is unchanged. SKILL.md is untouched by the step diff and its security-review carve-out stands. The four sample-corroborated directory entries rest on blob geometry or package-manager structure and survive the regenerated scan.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | low | plugins/horos/skills/horos/scripts/horos.py | contained_window_lines drops its first fragment even when the window offset lands exactly on a line's first byte, so a wholly contained comment-led banner at that position stays readable (probed: readable at offset size//2), while the docstring claimed every window past byte zero begins mid-line -- the safety argument overclaimed; the behaviour is conservative, bounded to one line per window and fail-open, so the fix corrects the docstring to state the blind first-fragment drop and its recall cost, with the promise-machine digest bumped alongside; fixed in commit 3bc7b2e1a8decbd3487453e88bdec2bab49acdb9 (signed, verify-commit good) | fixed |

Leads not pursued: the window pass splits on the newline byte only while the prefix pass uses splitlines, so a CR-only late banner can never bind in a window -- not pursued because reaching a window requires the prefix to pass, a CR-only prefix is intercepted as a blob candidate first, and the miss is recall-only and fail-open; a banner in the unwindowed gap between the two windows stays readable -- the pre-existing two-window sampling, unchanged by this step; a census currency guard -- the pre-step committed census was stale (it lacked the .png and .pdf rows entirely) and this step's regeneration corrected that in passing, while the study already carries the counts-comparison guard as an open lead; reading one byte before the window offset so a line starting exactly at the offset is kept -- a mid-run recall expansion that is the controller's call, with S2-R1-01 fixing the docstring instead.
