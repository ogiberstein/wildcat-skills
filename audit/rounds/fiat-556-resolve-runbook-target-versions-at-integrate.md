# Issue 556: resolve runbook target versions at integrate time

Rounds for the run on branch
`fiat/556-resolve-runbook-target-versions-at-integrate`, off `main` at
`8e6480230a5f43c57aef4f9a6c52f4c602d86790`. The run's audit record is this
file; `audit/AUDIT.md` is unchanged.

## Step 1, round 1 -- 2026-08-24

Non-Solidity round over Mason commit
`77458260d3fb0386a2d60b062a91e6c2c636ece4`. Two findings, both fixed on the
named audit branch in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/skills/protasis/scripts/protasis.py` | The relation row and path checks rejected C0 controls and DEL but accepted C1 and Unicode format controls. An otherwise valid path containing U+0080 or U+202E returned no P006 finding, despite the closed contract refusing control characters. | fixed in this round: one printable-boundary check now covers the complete row and the path helper; both code points are regression cases in `test_unsafe_paths_refuse` |
| S1-R1-02 | medium | `plugins/hexaemeron/skills/protasis/scripts/protasis.py` | Five P006 messages interpolated a runbook-controlled target id, ledger path, or relation value. A row can occupy almost the 2 MiB document cap; a refusal then copies source content into output instead of naming only the failed field and check. | fixed in this round: P006 diagnostics are value-free, and `test_relation_findings_do_not_echo_runbook_controlled_values` covers the invalid-id, duplicate-path, unknown-relation, and concrete-token paths |

### Evidence

The Warden red report is
`.elenchus/fiat-556-step-1-warden-round1-red.json`, SHA-256
`4f5d633f93444d39e5f86c1036cfbbedf84ef4d9da8b5cb071c22915c7a4dd9f`.
It records `elenchus.unittest.v1`, 1,057 tests, six assertion failures, zero
errors, and zero skips while the worktree diff contained the guards and no
product fix. The fixed-tree report is
`tmp/elenchus/fiat-556-step-1.json`, SHA-256
`2a6d37d37d479e94097a3a283db04b0c59881cfce198755572b78846ee5f3405`.
It records 1,057 tests, zero failures, zero errors, and zero skips.

Mason's earlier evidence remains intact. The first parser red is
`.elenchus/fiat-556-step-1-mason-red.json` with 1,055 tests and 22 assertion
failures. The link-placement red is
`.elenchus/fiat-556-step-1-link-conflict-red.json` with 1,056 tests and two
assertion failures. Both have zero errors and zero skips. Mason's signed commit
has parent `8e6480230a5f43c57aef4f9a6c52f4c602d86790`, a good local Shoggoth
signature, and exactly one co-author trailer and one origin trailer.

The fixed tree passes 89 focused Protasis tests, 350 root tests, all 71 Promise
Machine coverage rows, and the 1,057-test Hexaemeron report above. Phylax,
Ephoros, and Hypomnema exit 0 over the changed product paths. Both Promise
Machine commands are clean. Protasis accepts the receipted study and amended
runbook, and Horos reports that the boundary matches the tree.

The bounded Sapheneia record pass preserves every finding, qualification,
identifier, path, hash, count, verdict, and status. Imprimatur scores this file
100.0 with zero defects. Brevitas reports B011 only: the required findings
table has two data rows. It stays one row per actual finding; adding a third
would change the round's finding count.

The tracked study is byte-identical to the receipted study at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`.
Its five relative skill links resolve from `docs/fiat-version-relations-study.md`.
The tracked runbook is byte-identical to the amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
The misplaced plugin-local study path is absent. The changed product paths are
six paths, all authorised by the amended Step 1 Files field; no other product
file changed.

### Risk register

Four risk-register concerns are reachable in this step. `relation-block-shape`
surfaced S1-R1-01; every other malformed, duplicate, misplaced, oversized,
blank, decoy, and lexical path case is green. `literal-compatibility` is green
for a missing block, a partial target list, and every concrete-token position.
`diagnostic-leak` surfaced S1-R1-02. `promise-overclaim` is green: the Protasis
Promise names a lexical structure verdict and disclaims suitability, version
selection, and integration-base knowledge.

The other 19 concerns are not reachable in Step 1 and are not claimed as
reviewed here: `anchor-substitution`, `generation-arithmetic`, `frontier-drift`,
`ledger-history-rewrite`, `metadata-mismatch`, `multi-target-partial`,
`base-ref-race`, `run-ref-race`, `post-check-race`,
`remote-evidence-failure`, `git-object-shape`, `sync-carriage`,
`revalidation-coverage`, `resolution-staleness`, `state-history-growth`,
`self-hosted-collision`, `legacy-state`, `receipt-replay`, and
`interrupted-resolution` belong to later steps.

Leads not pursued: none.

## Step 1, round 2 -- 2026-08-25

Zero findings over signed audit-tip commit
`4278196365a8d288e1224be3e864cd505a4f7697`. Its parent is Mason commit
`77458260d3fb0386a2d60b062a91e6c2c636ece4`; both local signatures verify.
Round 1 remains the unchanged 79-line prefix of this record.

### Evidence

Independent hostile probes refused all 33 C0 controls, 32 C1 controls, 12
bidi controls, 170 Unicode format controls, 19 other sampled nonprinting code
points, and 13 unsafe path forms. Five concrete-token positives refused; five
near tokens and the legacy no-block case stayed accepted. Six controlled-value
cases produced seven value-free P006 messages, at most 80 characters. A
maximum-size 2 MiB row produced one 75-character P006 message without echoing
its contents.

The fixed tree passes 89 focused Protasis tests, 350 root tests, and the full
1,057-test Hexaemeron report with zero failures, errors, or skips. The report
is `tmp/elenchus/fiat-556-step-1.json`, SHA-256
`2a6d37d37d479e94097a3a283db04b0c59881cfce198755572b78846ee5f3405`.
The identical Round 1 green report remains preserved at
`.elenchus/fiat-556-step-1-warden-round1-green.json`; every earlier red report
also remains present.

Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
The Protasis Promise still limits P006 to lexical structure and disclaims
relation suitability, version selection, and integration-base knowledge.
Phylax, Ephoros, and Hypomnema exit 0 over their complete repository paths and
this record. Horos reports that the boundary matches the tree.

The tracked study remains byte-identical to its receipt at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
all five relative skill links resolve. The tracked runbook remains
byte-identical to its amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
The misplaced plugin-local study path is absent. All six product paths remain
inside the amended Step 1 Files field, and `audit/AUDIT.md` remains unchanged.

The bounded Sapheneia pass preserves the full Round 1 prefix and every Round 2
hash, count, qualification, path, and status. Imprimatur scores this record
100.0 with zero defects. Brevitas reports B011 only, from the required two-row
Round 1 findings table; this zero-finding round adds no finding row.

### Risk register

The four Step 1 concerns are green. `relation-block-shape` covers malformed,
duplicate, decoy, nonprinting, and unsafe path inputs. `literal-compatibility`
covers near tokens, partial declarations, and no-block runbooks.
`diagnostic-leak` covers the maximum-size and controlled-value probes.
`promise-overclaim` remains bounded by the Promise text. The other 19 study
concerns belong to later steps and receive no claim in this round.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-25

Non-Solidity round over signed Mason commit
`c924b4766b6bc8011ba52b1caff0faace443aeae`, whose parent is the audited Step
1 tip `417c2a876df77ac2a3d04e6378d959bca6299fc1`. Three findings were fixed on
the named audit branch in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Relation anchor reads honoured local Git replacement refs. Replacing the named commit, or replacing both selected blobs, let `done runbook` record `fiat-v9.9.9` while `anchor_commit` still named the native `fiat-v1.2.3` commit. Branch-point derivation also accepted grafted ancestry. | fixed in this round: relation ref, ancestry, tree, size, and blob reads bypass replacement refs; grafts refuse; branch refs are reread; commit, two-blob, and graft specimens guard the boundary |
| S2-R1-02 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The metadata regex searched all of `SKILL.md`. A body example containing `  version: "1.2.3"` stood in for absent frontmatter, and a file whose frontmatter named another skill still anchored as `fiat`. | fixed in this round: one bounded parser reads only the first closed YAML frontmatter, requires the exact target name, and takes one numeric version from the `metadata` mapping |
| S2-R1-03 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | A 5,000-digit counter matched the label grammar, then escaped as Python's decimal-conversion exception instead of the controller's value-free malformed-label refusal. | fixed in this round: conversion-limit failure returns the existing malformed-label result; the 5,000-digit specimen guards it, while `7.99.13` projects to `7.100.13` without SemVer reset |

### Evidence

The Warden pre-fix report is
`tmp/elenchus/fiat-556-step-2-warden-round-1-red.json`, SHA-256
`a00dfe45c6c2eacfbfc8a09e0554c216c4aabf54c09f40c833ed6342f7db6762`.
It records `elenchus.unittest.v1`, 1,081 tests, four assertion failures, one
error, and zero skips while the diff from Mason's commit contained the five
new guards and no Warden product repair. The fixed-tree report is
`.elenchus/fiat-556-step-2-warden-round1-green.json`, SHA-256
`d27a91f360cb57639a240f6a865c07b792f6af52d9cc564e10744a0b63a0c1fb`.
It records 1,084 tests with zero failures, errors, or skips.

Mason's causal matrix remains at
`tmp/elenchus/fiat-556-step-2-red-matrix.json`, SHA-256
`38805d0e89fdceb632b7fa54860dec9a990770606a6bec08932f5e04f128adc9`:
1,073 tests, nine assertion failures, six errors, and zero skips. Its canonical
green report remains unchanged at `tmp/elenchus/fiat-556-step-2.json`, SHA-256
`3fe2ea15aea672bb4deaae16a85c18f80260a10c2ef697ee5fef8ffc08a2be72`:
1,076 tests with zero failures, errors, or skips.

The fixed tree passes 26 focused relation tests and all 350 root tests.
Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
Phylax, Ephoros, and Hypomnema exit 0 over the complete repository paths.
Horos reports that the boundary matches the tree. The tracked study remains
byte-identical to its receipt at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the tracked runbook remains byte-identical to its amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All five product paths remain inside Step 2's Files field, and
`audit/AUDIT.md` remains unchanged.

The bounded Sapheneia pass preserves every finding, counterexample, path,
commit, hash, count, severity, qualification, and status in the required
round shape. It changes no existing audit byte. Imprimatur scores the complete
record 100.0 with zero defects. Brevitas accepts the new Step 2 append; the
complete append-only file retains only its inherited B011 at the two-row Step
1 findings table.

### Risk register

`anchor-substitution`, `metadata-mismatch`, and `generation-arithmetic`
surfaced S2-R1-01 through S2-R1-03. `multi-target-partial` is green for one,
two, partial, reordered, and one-bad-target capture. `git-object-shape` is
green for unsafe, missing, tree, symlink, submodule, non-UTF-8, oversized, and
native-object cases. `literal-compatibility`, `legacy-state`,
`receipt-replay`, `diagnostic-leak`, and `promise-overclaim` are green within
Step 2's anchor and packet boundary. Live base and run snapshots, frontier and
ledger drift, remote failures, sync carriage, revalidation coverage, stale or
capped resolution history, the terminal parent race, self-hosted collision,
and interrupted resolution belong to Steps 3 and 4 and receive no claim here.

Leads not pursued: none.

The first source-bound mechanical guard run against preliminary signed Warden
object `eeb9fe8f508fe1a316d3cdbcb52dc41b49267ec9` was inconclusive because the
5,000-digit counter specimen let the known parent `ValueError` register as a
unittest error. The guard now translates that exact old exception into an
assertion failure; no product repair changed in response.

## Step 2, round 2 -- 2026-08-25

Non-Solidity correctness round over signed Warden tip
`30a929065c65b3d41df6a1fb75087acdb7d08d5b`. Three residual findings were
fixed on the exact Step 2 audit branch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Relation Git reads still inherited repository-substitution variables. `GIT_DIR` redirected the same branch names to an attacker repository and receipted `fiat-v9.9.9`; `GIT_ALTERNATE_OBJECT_DIRECTORIES` also changed command output, and a repository-local alternate remained admissible. | fixed in this round: relation reads discard inherited `GIT_*` state, disable global and system configuration and lazy fetching, retain fixed argv with `--end-of-options`, and refuse a populated repository alternate before either an exact-start or derived-start read |
| S2-R2-02 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | A crafted shallow boundary changed the unique merge base from the real run start to an earlier commit, so the controller could anchor the wrong ledger and skill bytes. | fixed in this round: relation capture requires a non-shallow repository before accepting an exact or derived starting commit |
| S2-R2-03 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | With `PYTHONINTMAXSTRDIGITS=0`, a 5,000-digit label was accepted and persisted instead of receiving the value-free malformed-label refusal. A stored surrogate in `frontier_revision` escaped as a traceback during `status`, `next`, and `verify`. | fixed in this round: ASCII counters have an explicit 128-digit pre-conversion limit and matching stored-state maximum; invalid UTF-8 scalar values reach the stable field-specific refusal without encoding first |

### Evidence

The Warden pre-fix report is
`tmp/elenchus/fiat-556-step-2-warden-round-2-red.json`, SHA-256
`1d36cdea1bf33c25e274cfb6412663f5212e99e39d790f86e14432fdfc63b0b0`.
It records `elenchus.unittest.v1`, 1,089 tests, seven assertion failures, zero
errors, and zero skips. The fixed-tree report is
`.elenchus/fiat-556-step-2-warden-round2-final-green.json`, SHA-256
`29d2a7eed48962b1cae726b225f9441ab935d936200263200052763bce278ac1`.
It records 1,090 tests with zero failures, errors, or skips.

The fixed tree passes 32 focused relation tests, the 397-test controller and
Fiat contract gate, and all 350 root tests. Promise Machine reports 14 clean
plugin copies and 71 of 71 covered promises. Phylax, Ephoros, and Hypomnema
exit 0 over the complete repository paths. Horos reports that the boundary
matches the tree. The tracked study remains byte-identical to its receipt at
SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the tracked runbook remains byte-identical to its amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All four changed product paths are admitted by Step 2's Files field, and
`audit/AUDIT.md` remains unchanged.

The prior 12,780-byte audit record is the exact prefix of this append, SHA-256
`3d60fef2a407c3611d78a649220d1d4d479a7c2b6c677c36ce62eca03f0aa02c`.
The bounded Sapheneia comparison preserves all three findings, severities,
counterexamples, paths, hashes, counts, qualifications, statuses, and later
step boundaries. Imprimatur reports zero defects. Brevitas accepts the new
round; the complete file retains only its inherited B011 at the two-row Step
1 findings table.

### Risk register

`anchor-substitution`, `git-object-shape`, `generation-arithmetic`,
`diagnostic-leak`, and `legacy-state` surfaced S2-R2-01 through S2-R2-03.
`multi-target-partial` remains green for one, two, partial, reordered, and
one-bad-target capture. Exact starting-commit reads now cover ref and worktree
drift, replacement refs, grafts, inherited Git state, repository alternates,
and shallow history. Top-level `SKILL.md` identity, all anchor fields,
all-or-nothing state and ledger capture, explicit `resolution: null`, Promise
declarations, literal-only byte identity, no-block Git silence, and legacy v1
replay remain green.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, revalidation coverage, stale or capped resolution history, terminal
parent races, self-hosted collision, and interrupted resolution belong to
Steps 3 and 4 and receive no claim here.

Lead not pursued: recomputing every native Git object identity after direct
object-store corruption. This round refuses the observed substitution paths;
native object-store integrity remains Git's repository boundary.

## Step 2, round 3 -- 2026-08-25

Non-Solidity correctness audit over signed Warden tip
`f9d6cac2d33e25ce4ae1cea845b4c0aef493956c`. Three residual findings were
fixed on the exact Step 2 audit branch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Receipt replay accepted a tree SHA in `anchor_commit`. `status` and `next` read target blobs from that tree and returned success even though the stored object did not establish the promised starting commit. | fixed in this round: replay resolves the stored SHA through `^{commit}`, requires the stored SHA to name that commit object directly, and refuses before reading either target blob |
| S2-R3-02 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | After a valid receipt, adding a populated repository-local alternate or a shallow boundary left `status` and `next` green. Initial capture checked full-history repository state, but replay did not re-establish it. | fixed in this round: every relation-bearing replay repeats the native graft, alternate, and shallow checks before exact commit and blob reads; inherited `GIT_*` scrubbing and `--no-replace-objects` remain in force |
| S2-R3-03 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | A `SKILL.md` with canonical `name` or nested `metadata.version` plus the same protected key in quoted YAML spelling was receipted. The parser selected the canonical line while the real frontmatter identity remained duplicate and ambiguous. | fixed in this round: the accepted subset counts plain, single-quoted, and double-quoted spellings of `name`, `metadata`, and nested `version`, then requires one canonical occurrence with the matching skill and numeric version |

### Evidence

The causal pre-fix report is
`tmp/elenchus/fiat-556-step-2-warden-round-3-red.json`, SHA-256
`ee8e5032530b7ed3024545b305348a984cffcd3c5fac607b937b43ef9763dafc`.
It records `elenchus.unittest.v1`, 1,095 tests, eight assertion failures, zero
errors, and zero skips. The five new guard methods and no Warden product fix
were present. The failures are the two quoted-key receipts and the `status`
and `next` acceptance of a tree anchor, a post-receipt alternate, and a
post-receipt shallow boundary.

The repaired-tree report is
`.elenchus/fiat-556-step-2-warden-round3-precommit-green.json`, SHA-256
`47fd37514f781eaa6f57b97bc60618be7cd3508baef66a541a6d89d95eaff8c9`.
It records `elenchus.unittest.v1`, 1,095 tests with zero failures, errors, or
skips. The fixed tree passes 37 focused relation tests, the 434-test controller
and Fiat companion gate, and all 350 root tests. All 16 non-Solidity suite
commands in `AGENTS.md` are green; Lazarus contributes 364 tests under its
pinned Python 3.13 lockfile runtime.

Mason's causal matrix remains
`tmp/elenchus/fiat-556-step-2-red-matrix.json`, SHA-256
`38805d0e89fdceb632b7fa54860dec9a990770606a6bec08932f5e04f128adc9`:
1,073 tests, nine assertion failures, six errors, and zero skips. The canonical
green remains `tmp/elenchus/fiat-556-step-2.json`, SHA-256
`3fe2ea15aea672bb4deaae16a85c18f80260a10c2ef697ee5fef8ffc08a2be72`:
1,076 tests with zero failures, errors, or skips.

Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
Phylax, Ephoros, and Hypomnema each exit 0 on the complete repository paths.
Horos reports that the boundary matches the tree. Python compilation and
`git diff --check` are clean. The receipted study remains at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook bytes remain at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All three product paths are admitted by Step 2's Files field, and
`audit/AUDIT.md` remains unchanged.

The prior 17,402-byte audit record is the exact prefix of this round, SHA-256
`872da975ff1fab131d52cafec58c57776f9951ca5ed1c79fdda94e2928ba522f`.
The bounded Sapheneia comparison preserves every finding, severity,
counterexample, path, hash, count, qualification, status, scope exclusion,
and unpursued lead. Imprimatur and Brevitas accept the new append; the
complete file retains only its inherited B011 at the two-row Step 1 table.

### Risk register

`anchor-substitution`, `git-object-shape`, `metadata-mismatch`,
`receipt-replay`, `diagnostic-leak`, `legacy-state`, and
`literal-compatibility` surfaced S2-R3-01 through S2-R3-03 or received new
adjacent guards. One, two, partial, reordered, and one-bad-target capture;
counter arithmetic and non-SemVer treatment; every anchored ledger, skill,
evolution, epoch, and frontier field; all-or-nothing multi-target refusal;
state and ledger receipt matching; malformed and tampered anchors; explicit
`resolution: null`; Promise declarations; and legacy v1 replay remain green.
The no-block specimen now runs `done runbook`, `status`, and `next` behind a
refusing Git wrapper without a call, while its directive stays byte-identical.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, resolution receipt recovery, stale or capped resolution history,
terminal parent races, and the self-hosted collision remain Steps 3 and 4 and
receive no Step 2 claim.

Leads not pursued: recomputing every native Git object identity after direct
object-store corruption. The guarded substitutions, stored object type, and
full-history state now refuse or reconstruct from native objects; physical
object-store integrity remains Git's repository boundary.
