# Study: validate the state shape at `load_state`

Assuming, unless corrected:

1. Issue 321 is the held Fiat frontier job. Completing it advances `fiat-v4.9.1` to `fiat-v5.9.1` on the evolution axis; it is not another generation entry.
2. The exact starting ref is `main` at `6980aef4c33ece8614b21e4ef8ff32dd19c3e7fc`, and the controller-created run branch is `fiat/fiat-next-validate-the-shape-of-the-state-load-s`.
3. The stored state format remains version 1. This run checks the container shape that version already writes; it does not migrate or rewrite state.
4. The four acceptance paths are `config`, `receipts`, `steps`, and each step's `audit.rounds`. The validator also checks the intermediate containers needed to reach them and each list member it later treats as an object.
5. A shape fault is controller-state corruption, so every command exits 1 with the same single-line diagnosis before it reads the malformed value. The message names the JSON path and expected kind without echoing the value.
6. Existing semantic checks keep their ownership. This run does not turn the state file into a complete declarative schema or validate every receipt payload.
7. Python 3 and the standard library remain the implementation boundary. No dependency, subprocess, network call, storage-layout change or CI change is needed.
8. Every later local Fiat commit follows the permanent delivery rule: `git commit -S`, successful `git verify-commit`, and exactly one copy of each required Shoggoth trailer. The Surveyor phase creates no commit.

## 1. Problem statement

`load_state` proves only that `.hexaemeron/state.json` exists and parses as JSON. It can return a scalar, or a mapping whose `config`, `receipts`, `steps`, or per-step `audit.rounds` value has the wrong type. Callers then disagree about the fault: some use `as_dict` and continue with an empty mapping, while others index or iterate the same value and raise a raw Python traceback. The audit record measured this class across 676 malformed shapes and retained whole-state load validation as Fiat's held frontier.

The working prototype validates the required container spine once, inside `load_state`, before returning state to any caller. It uses a deterministic order and emits a stable diagnosis such as:

```text
hexctl: error: state key 'steps[0].audit.rounds' must be an array
```

The message names only the path and expected JSON kind. It does not include the malformed value. `status`, `next`, `verify`, and a mutating command must return the same line and exit 1 for the same specimen, with no traceback and no change to the state or ledger. `verify` therefore reports the shape fault before its fingerprint or phase-consistency checks rather than reaching a different failure by another path.

The demo creates one valid temporary run, writes four invalid copies with wrong-type `config`, `receipts`, `steps`, and `steps[0].audit.rounds`, and invokes the command matrix over each copy. It also covers a non-object root, non-object step, non-object `audit`, non-object round entry, missing required container, valid study-phase state, valid audit rounds, and a state from before `fiat-v4.9.1`. The focused proof is:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
```

The repository proof is:

```bash
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
```

## 2. Prior art

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` already has one read boundary. `load_state` catches invalid JSON and file errors, then returns `json.load` unchanged. Every state-backed command enters through that function, and `verify_run` calls it before checking the hash-chained ledger. That call graph makes a single load-time validator sufficient for command and `verify` parity.

The controller has partial local defences rather than a state contract. `as_dict` prevents stored nulls from escaping selected chained reads; `max_rounds_of` names an invalid `config.audit.max_rounds`; `current_step` names an absent current step; and `verify_run` checks the ledger fingerprint, merge order, and open-step consistency. These checks remain useful after the new structural gate. They do not establish that the state returned by `load_state` has the containers every reader assumes.

The audit history supplies the failure evidence and the scope:

- The receipted-lint run found that 356 of 676 malformed state shapes raised from `solidity_round` when `config` or `receipts` was not an object. `as_dict` closed that call site, and later rounds removed four more stored-null tracebacks.
- Those rounds repeatedly retained `load_state` validation as the larger controller-robustness job. The final round moved it from an audit lead into Fiat's held frontier and stated that `verify` still did not check round shape.
- The original controller audit already distinguishes syntactically unreadable JSON from well-formed JSON with the wrong shape: F-03 gave invalid JSON a clean `state file unreadable` error, while F-01 bound state bytes to the ledger. This run adds the missing layer between those two checks.

The last two merged pull requests that changed Fiat were read:

- [PR 364](https://github.com/wildcat-finance/skills/pull/364) bound commit receipts and publication topology, published `fiat-v4.9.1`, and deliberately retained the held `load_state` job byte for byte. Its post-push recovery confirms that state compatibility must fail closed without rewriting recorded history.
- [PR 365](https://github.com/wildcat-finance/skills/pull/365) integrated that generation. Its carried-forward section names issue 321 as the next held job and issue 363 as the separate stale delegated-task identity failure. The source-bound packet and permanent signing gates shipped there must stay intact.

Outside this repository, JSON Schema Draft 2020-12 names object and array shape precisely, and RFC 6901 supplies a standard pointer syntax. Neither is adopted as a runtime dependency. The state has four small heterogeneous container families, and the controller already uses Python list-index paths in its diagnostics; a short standard-library validator is cheaper to read and preserves existing message style.

The versioning contract adds a suite-wide duty that is not limited to Fiat files. Before integration, the Scribe must cold-read and reconcile all mutable first-party marketplace prose: the root selection and runtime prose; all 14 plugin landing READMEs and runtime contracts; canonical first-party skill and evolution prose; first-party agent and reference prose; and mutable marketplace, manifest, and runtime-description fields. Generated Promise Machine copies, vendored Pashov instructions, content-addressed evidence, fixtures, historical audit text, and completed studies are evidence or generated boundaries rather than mutable marketplace prose. The review records which in-scope surfaces were unchanged and edits every surface made stale by state validation, the `fiat-v5.9.1` frontier, or the issue 363 successor. `tests/test_marketplace_prose.py`, version propagation, and Promise Machine remain mechanical gates rather than substitutes for the cold read.

## 3. Constraints and non-goals

The build starts from `6980aef4c33ece8614b21e4ef8ff32dd19c3e7fc`. It preserves state version 1, controller JSON output, the append-only ledger, directive packets, receipt ordering, signature gates, and the existing exit-1 treatment for unreadable or corrupt state.

The load-time shape contract is deliberately limited to containers the controller treats structurally:

- the root is an object;
- `config` and its required mapping sections are objects;
- top-level `receipts` is an object;
- `steps` is an array, and every step is an object;
- each step's `receipts` and `audit` values are objects;
- each `audit.rounds` value is an array, and every round is an object.

Required containers are named when absent. Multiple faults resolve in the documented order: root, `config`, `receipts`, `steps`, then step and round order. Existing field-level checks still decide values such as phase names, `max_rounds`, branch names, receipt contents, findings counts, lint exits, commit identities, and integration topology.

Non-goals are a JSON Schema file, a new state version, dataclass conversion, automatic repair, state quarantine, receipt-payload validation, a rewrite of `as_dict`, stronger claims about ledger truth, issue 363's task-name binding, or any change to agent packet fields. The validator reports what it observed and leaves inspection and manual recovery available.

**Always.** Capture each wrong-shape case red before the fix; run the focused and complete suites before a commit; run Imprimatur over shipped prose; run the three tree lints and `git diff --check`; keep the exact signed-commit and GitHub-verification rules already enforced by Fiat.

**Ask first.** Add a dependency; change state version, receipt shape, directive schema, exit-code policy, CI, a public runtime interface, or any trust boundary beyond reading the existing local state file.

**Never.** Echo malformed state values or credentials in a diagnosis; accept a wrong kind through coercion; rewrite the state to make validation pass; weaken the ledger fingerprint; delete a failing specimen; edit vendored or generated material; change issue 363's scope silently; or claim a test, lint, signature, or remote check ran when it did not.

## 4. Design options

### Option A: guard each reader

Add `isinstance` or `as_dict` at every index, iteration, and chained read. This keeps each diff small, but preserves the measured failure mode: one caller gets fixed while the next caller can interpret or raise on the same state differently. It cannot guarantee `verify` parity without repeating the checks there.

### Option B: validate the container spine in `load_state` (chosen)

Parse JSON, run one ordered `validate_state_shape` function, then return only a state whose required containers have the kinds readers assume. A small path-aware helper reports `object` or `array` without printing the value. Every command and `verify` inherit the same result because they already share `load_state`.

This is the cheapest construction that meets the held acceptance condition. Its trade is stricter treatment of old or hand-edited state that partial guards previously read through as empty. Compatibility fixtures therefore cover real prior state shapes, and the validator checks only the existing container spine rather than guessing semantics for heterogeneous receipts.

### Option C: validate a JSON Schema document

Draft 2020-12 could describe more of state version 1 and produce machine-readable paths. It adds a schema truth surface and either a dependency or a local schema engine. The state is small enough that this costs more comprehension and drift risk than the held job warrants.

### Option D: deserialize into typed classes

Dataclasses or typed dictionaries would make internal assumptions visible, but conversion touches every state reader and writer, raises migration and round-trip questions, and risks changing stored bytes that the ledger fingerprints. That is a state-model redesign, not the requested validation gate.

## 5. Risk register seed

```risk-register
validation-bypass | load_state return before any controller reader receives state | every return crosses one validator and a monkeypatched bypass makes the command matrix fail
path-diagnostic-drift | error path for config receipts steps and nested rounds | table-driven tests require the exact same named path and expected kind across status next verify and record
validation-order | a state carrying more than one malformed container | the first diagnosis follows root config receipts steps then ascending step and round index order
legacy-state-rejection | state files created before fiat-v5.9.1 | archived and constructed legacy fixtures with the existing container spine still load status and verify as before
semantic-scope-creep | heterogeneous receipt and field payloads below the container spine | validator accepts existing payload variants and leaves established field validators authoritative
secret-echo | malformed values held in config or receipts | diagnostics contain only the bounded JSON path and expected kind and never repr or serialise the value
verify-parity | load_state validation beside ledger fingerprint and phase checks | verify emits the identical shape fault before ledger checks for each malformed specimen
partial-write | syntactically valid but structurally incomplete state after an interrupted or manual write | missing required containers receive a named refusal and neither state nor ledger is modified
round-indexing | non-object steps audits rounds or round members | each intermediate kind is checked before indexing and the message names the exact indexed path
frontier-arithmetic | fiat-v4.9.1 held job replaced after completion | exactly one evolution row produces fiat-v5.9.1 with a recomputed frontier digest and the issue 363 successor
marketplace-prose-drift | suite-wide mutable first-party prose after Fiat behaviour and frontier change | cold-read inventory is recorded and marketplace prose version and Promise Machine gates pass after every stale surface is reconciled
signing-provenance | every Fiat-created local and pushed commit in this run | controller receipts retain local signature exact trailer and GitHub valid-verification enforcement
```

The Warden treats `validation-bypass`, `verify-parity`, `partial-write`, and `secret-echo` as the hardest boundaries. A successful type matrix does not establish semantic correctness outside the named container contract.

## 6. Glossary seeds

| Term | Meaning | Boundary |
| --- | --- | --- |
| Container spine | The required object and array paths a state reader must traverse before field-level logic starts. | It does not validate every leaf. |
| State-shape fault | Valid JSON whose required container is absent or has the wrong JSON kind. | Invalid JSON remains an unreadable-file fault. |
| Named path | A stable path such as `config` or `steps[0].audit.rounds` in the refusal. | The value at that path is not printed. |
| Command parity | Every command entering through `load_state` receives the same diagnosis for the same state bytes. | Later command-specific checks may still differ on well-shaped state. |
| Legacy-compatible state | Older state whose existing container spine meets the same version-1 shape. | Compatibility does not waive ledger verification. |
| Successor frontier | The next concrete Fiat job recorded only after issue 321 completes. | Here it is issue 363, backed by the observed stale task name. |

## 7. Sources

- [Issue 321](https://github.com/wildcat-finance/skills/issues/321), held `load_state` frontier acceptance.
- [Issue 363](https://github.com/wildcat-finance/skills/issues/363), observed stale delegated-task identity and successor acceptance.
- Exact start: Git commit `6980aef4c33ece8614b21e4ef8ff32dd19c3e7fc`.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, especially `load_state`, `as_dict`, `current_step`, `max_rounds_of`, `cmd_next`, `cmd_status`, and `verify_run`.
- `plugins/hexaemeron/tests/test_hexctl.py`, especially `TestFuzzRegressions`, `TestSolidityRoundClassifier`, and delegation lifecycle coverage.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `EVOLUTION.md`, and `plugins/hexaemeron/skills/VERSIONING.md`.
- `audit/AUDIT.md`, “Receipted lint rounds” and “Fiat delegation packets”.
- [PR 364](https://github.com/wildcat-finance/skills/pull/364) and [PR 365](https://github.com/wildcat-finance/skills/pull/365), the last two merged pull requests that changed Fiat.
- `tests/test_marketplace_prose.py`, `tests/test_version_propagation.py`, and `scripts/promise_machine.py`.
- Promise Machine contract `promise-machine/v1` and the Hexaemeron runtime contract.
- JSON Schema Draft 2020-12 and RFC 6901, considered identifiers rather than new runtime dependencies.

## 8. Signals, and the questions behind them

This controller is invoked from a terminal and does not run unattended, so Ephoros requires no log, metric, trace, or alert surface. The existing exit status and stderr are the signals.

1. “Which part of state is malformed?” The refusal names the exact bounded path.
2. “What shape did the controller require?” The same line names `object` or `array`.
3. “Did `verify` diagnose the same state contract?” The command matrix compares its exact stderr and exit code with the other commands.
4. “Did the controller alter evidence while refusing it?” The fixture compares state and ledger bytes before and after every command.

No new event is stored in the ledger because a malformed state cannot safely authorise a mutation. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) remains the signal-content authority.

## 9. Boundaries, per capability

The state file is local but not trusted merely because the controller created its path: interrupted writes, manual edits, restored archives, and a controller upgrade can all present different bytes. The value at the boundary is a version-1 container shape. The control is parse, ordered kind validation, then return; failure leaves the exact source untouched.

Diagnostics cross into a terminal and may be copied into audit records. Their value is a repairable path and expected kind. The control uses fixed schema labels and bounded paths derived from validator traversal, never the input value, Python `repr`, a receipt payload, or raw file text.

The ledger is a separate evidence boundary. Shape validation occurs before fingerprint and phase-consistency checks because those checks themselves index state. Passing shape validation authorises only those later checks to run; it does not strengthen their evidence or prove the state true. [Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) remains the filesystem and diagnostic-boundary authority.

No new subprocess, URL, credential, dependency, secret store, generated input, or output file is introduced.

## 10. The budget, or its absence

No performance improvement is claimed, so Metron has no before-and-after budget. Validation walks the already loaded container spine once and does not perform I/O beyond the existing state read. The build may not add a second parse or recursive copy merely for validation.

The exact functional check is the focused controller suite:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl
```

If implementation introduces a performance claim or a new measurable state-size ceiling, [Metron](../plugins/hexaemeron/skills/metron/SKILL.md) must define and record that measurement before the change is kept.

## 11. The fail-closed posture

A missing or wrong-kind required container stops `load_state` with exit 1 before any directive, status presentation, ledger verification, or mutation. The validator does not coerce, default, delete, quarantine, repair, or rewrite the source. Recovery is to inspect the named path, restore or repair the real state evidence, and rerun `verify`.

Each shape begins as an Elenchus guard: write the valid fixture, change one path, capture the traceback or divergent pre-fix result, assert the path-naming refusal and unchanged bytes after the fix, then prove the guard fails when the validator call or path check is removed. Existing valid lifecycle and archived-state fixtures remain green. [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns that failure workflow.

## 12. Decisions and their homes

The central load-time gate, minimal container spine, deterministic validation order, value-free error format, exit-1 policy, and `verify` ordering are expensive to reverse. The implementation and stable messages live in `hexctl.py`; red-to-green behaviour lives in `test_hexctl.py`; the public operating boundary is reconciled in Fiat's `SKILL.md` only where the cold read shows it is stale.

The completed frontier decision lives in one `EVOLUTION.md` row: `fiat-v5.9.1`, evolution axis, frontier revision `state-shape-validation`, and a digest recomputed from the new frontier line. The successor is issue 363: bind each Surveyor, Mason, Warden, and Scribe task identity to the current issue or topic, step where applicable, and role; reproduce it across resume and compaction; and reject or replace a stale handle that names another issue. That target is evidenced by the issue 320 failure and remains outside this implementation.

The suite-wide prose reconciliation is recorded in the final audit and integration pull-request evidence, with changed paths in their normal first-party homes. No standalone ADR is expected because state version and stored bytes do not change; if implementation requires a migration or widens the schema beyond this study, the study must be amended before code changes. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) remains the record-placement authority.
