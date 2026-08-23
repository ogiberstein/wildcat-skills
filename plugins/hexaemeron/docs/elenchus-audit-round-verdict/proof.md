# Elenchus audit-round verdict proof

This proof records the issue 327 demonstration run on 2026-08-22. It used the
checkout controller at
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, SHA-256
`01efd29fcc0b1198aa62989291c1dbe4713d7c26cccbba40a1fbe4b210884870`,
from step 3's parent `024a64d9265ca21551cfab4a969657e7cefef2ad`.
The run exercised a fresh repository and the worktree created by `hexctl init`.
No network, credential, Solidity target, or raw signature output entered the
record.

## Reproduction boundary

Run these commands from the repository root with Python 3.12 and a configured
Git signing key. The names below keep the generated repository under the
current run's ignored `.hexaemeron` directory.

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel)
DEMO_ROOT=$(mktemp -d "$PROJECT_ROOT/.hexaemeron/issue327-step3-XXXXXX")
DEMO_ORIGIN="$DEMO_ROOT/origin"
HEXCTL="$PROJECT_ROOT/plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
mkdir "$DEMO_ORIGIN"
git -C "$DEMO_ORIGIN" init -b main
git -C "$DEMO_ORIGIN" config user.name "Dave Coleman"
git -C "$DEMO_ORIGIN" config user.email "dave@wildcat.finance"
git -C "$DEMO_ORIGIN" commit -S --allow-empty -m "demo base"
python3.12 "$HEXCTL" --dir "$DEMO_ORIGIN" init \
  --topic "issue 327 proof" --base main
DEMO_RUN="$DEMO_ORIGIN/tmp/fiat/fiat-issue-327-proof"
cp "$PROJECT_ROOT/.hexaemeron/study.md" "$DEMO_RUN/.hexaemeron/study.md"
cp "$PROJECT_ROOT/.hexaemeron/runbook.md" "$DEMO_RUN/.hexaemeron/runbook.md"
cp "$PROJECT_ROOT/.hexaemeron/steps.json" "$DEMO_RUN/.hexaemeron/steps.json"
python3.12 "$HEXCTL" --dir "$DEMO_RUN" done study \
  --artifact "$DEMO_RUN/.hexaemeron/study.md" \
  --skills hexaemeron:protasis,hexaemeron:imprimatur
python3.12 "$HEXCTL" --dir "$DEMO_RUN" done runbook \
  --artifact "$DEMO_RUN/.hexaemeron/runbook.md" \
  --steps-file "$DEMO_RUN/.hexaemeron/steps.json"
```

Call `next` twice before the implementation receipt. Decode both JSON objects,
require them to be equal, and retain only the Mason `brief.runbook_step`.
Create the branch and implementation commit named by that packet. Every
commit owned by the proof uses one exact copy of each required trailer.

```bash
MASON_ONE=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
MASON_TWO=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
test "$MASON_ONE" = "$MASON_TWO"
STEP_BRANCH=$(python3.12 -c \
  'import json,sys; print(json.loads(sys.argv[1])["brief"]["branch"])' \
  "$MASON_ONE")
STEP_BASE=$(python3.12 -c \
  'import json,sys; print(json.loads(sys.argv[1])["brief"]["branch_from"])' \
  "$MASON_ONE")
git -C "$DEMO_RUN" switch -c "$STEP_BRANCH" "$STEP_BASE"
git -C "$DEMO_RUN" commit -S --allow-empty \
  -m "issue 327 proof implementation" \
  -m "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>" \
  -m "Wildcat-Origin: shoggoth"
IMPLEMENTATION=$(git -C "$DEMO_RUN" rev-parse HEAD)
python3.12 "$HEXCTL" --dir "$DEMO_RUN" done implement \
  --branch "$STEP_BRANCH" --commit "$IMPLEMENTATION" \
  --tests "disposable proof fixture"
python3.12 "$HEXCTL" --dir "$DEMO_RUN" record security_suite \
  '"waived: issue 327 proof has no Solidity target"'
WARDEN_ONE=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
WARDEN_TWO=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
test "$WARDEN_ONE" = "$WARDEN_TWO"
python3.12 - "$MASON_ONE" "$WARDEN_ONE" <<'PY'
import json
import sys
mason = json.loads(sys.argv[1])
warden = json.loads(sys.argv[2])
assert mason["brief"]["runbook_step"] == warden["brief"]["runbook_step"]
assert sorted(warden["brief"]["runbook_step"]) == [
    "markdown", "number", "path", "sha256", "title",
]
PY
```

The decoded Mason and Warden packets carried the same five-field
`runbook_step`. Its Markdown was the exact byte range from the Step 1 heading
up to the Step 2 heading in the receipted runbook. The observed packet evidence
was:

| Subject | Schema or status | SHA-256 |
| --- | --- | --- |
| Mason packet | repeated object equal | `02478d8912af6c67a0686f1a624eb2faedae02996e2a3fea93005cd0992fd248` |
| Warden packet | repeated object equal | `422cde350000b866a8e97b4627710603b19cfc8a69c3b3c2743c4c2c6e09fe3c` |
| `runbook_step` | `markdown`, `number`, `path`, `sha256`, `title` | `f26bc20915be744183a6f572b2758f0442dc22607b95dd7bd6b174b11d1c6524` |
| Step 1 Markdown | exact source bytes | `4da25cd2d9e8e046016501d69dd0289de2cf3dad78f0e486f59dc7d4fd7515ef` |
| Receipted runbook | source artefact | `82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85` |

The Warden brief had exactly `audit_log_path`, `plugin_root`, `risk_register`,
`round`, `runbook_step`, `security_suite`, `stacked_branch`, and
`step_branch`. The step number was 1 and the title was `Bind the runbook test
command to the Elenchus contract`.

## Refusals, null, and legacy state

Create one signed candidate fix from the implementation head, then take
SHA-256 digests of `.hexaemeron/state.json` and
`.hexaemeron/ledger.jsonl`. Invoke these three commands with the non-Solidity
lint receipts appended to each command:

```bash
signed_fix() {
  git -C "$DEMO_RUN" commit -S --allow-empty -m "$1" \
    -m "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>" \
    -m "Wildcat-Origin: shoggoth" >/dev/null
  git -C "$DEMO_RUN" rev-parse HEAD
}
LINT_ARGS=(--phylax-exit 0 --ephoros-exit 0 --hypomnema-exit 0)
FIX_1=$(signed_fix "issue 327 proof fix guarded")
sha256sum "$DEMO_RUN/.hexaemeron/state.json" \
  "$DEMO_RUN/.hexaemeron/ledger.jsonl"
```

```bash
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --fixes-commit "$FIX_1" "${LINT_ARGS[@]}"
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --elenchus-verdict guarded "${LINT_ARGS[@]}"
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --fixes-commit "$FIX_1" --elenchus-verdict unknown "${LINT_ARGS[@]}"
sha256sum "$DEMO_RUN/.hexaemeron/state.json" \
  "$DEMO_RUN/.hexaemeron/ledger.jsonl"
```

Each command exited 2. The first named the missing verdict and all four
accepted values, the second named the missing fix, and the third was rejected
by the closed command-line enum. The raw file digests before and after each
refusal were identical:

| Case | Exit | State SHA-256 | Ledger SHA-256 |
| --- | ---: | --- | --- |
| fix without verdict | 2 | `a900979d51daa29cbdc7099782150aaa18c8d4f02beeff675c3f26e241111544` | `71c3510f2085c6b5f95e9da1b962ddfa8451498943cd07959634f9ad04e4f10b` |
| verdict without fix | 2 | `a900979d51daa29cbdc7099782150aaa18c8d4f02beeff675c3f26e241111544` | `71c3510f2085c6b5f95e9da1b962ddfa8451498943cd07959634f9ad04e4f10b` |
| unknown verdict | 2 | `a900979d51daa29cbdc7099782150aaa18c8d4f02beeff675c3f26e241111544` | `71c3510f2085c6b5f95e9da1b962ddfa8451498943cd07959634f9ad04e4f10b` |

A no-fix round with one finding and the three zero lint exits then recorded an
explicit JSON null in both state and ledger. State SHA-256 was
`e22594db09b2d94491ed5740785ef5c798c5b7ebd51a9a18312dd6956ed7c983`;
ledger SHA-256 was
`150bd0093ebe95b60e52a9261bb3892f34534af74f35fce863069f8c3895af42`.

```bash
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  "${LINT_ARGS[@]}"
```

The proof removed that round's `elenchus_verdict` key from both files to model
a pre-generation round. It recomputed the canonical compact state fingerprint,
replaced the last ledger entry's `state`, and recomputed that entry's hash over
the entry without its old `hash` field. The resulting state fingerprint was
`8d91511463c9291b778b4ae7651bec59b10fbe83746274a9379b5dbad91b30bd`;
the ledger tail hash was
`10f38d4d5931e8f0efa201656c69053cc30f2f39579b89da3d3f815454370ebb`.
Raw state and ledger file digests were respectively
`b4b5b109d3a78b8c98ccddb53121853f8b8269102f87d4bd26ef064e88c82a42`
and `c7ef85eeb9a7172c1f748eb2a4d53618b6d87977c8d7445336d21a0d14e0681a`.

```bash
python3.12 - "$DEMO_RUN" <<'PY'
import hashlib, json, sys
from pathlib import Path
meta = Path(sys.argv[1]) / ".hexaemeron"
state_path, ledger_path = meta / "state.json", meta / "ledger.jsonl"
state = json.loads(state_path.read_text())
state["steps"][0]["audit"]["rounds"][-1].pop("elenchus_verdict")
compact = lambda value: json.dumps(
    value, sort_keys=True, separators=(",", ":")
).encode()
state_fingerprint = hashlib.sha256(compact(state)).hexdigest()
state_path.write_text(json.dumps(state, indent=2) + "\n")
entries = [json.loads(line) for line in ledger_path.read_text().splitlines()]
entries[-1]["data"].pop("elenchus_verdict")
entries[-1]["state"] = state_fingerprint
unsigned = {key: value for key, value in entries[-1].items() if key != "hash"}
entries[-1]["hash"] = hashlib.sha256(compact(unsigned)).hexdigest()
ledger_path.write_text("".join(
    json.dumps(entry, sort_keys=True) + "\n" for entry in entries
))
PY
```

`status`, `next`, and `verify` each exited 0 after the edit. `next` returned
`audit-round` round 2. A later verified fix round exited 0, and `done audit`
later exited 0 without adding the missing legacy field.

```bash
python3.12 "$HEXCTL" --dir "$DEMO_RUN" status
python3.12 "$HEXCTL" --dir "$DEMO_RUN" next
python3.12 "$HEXCTL" --dir "$DEMO_RUN" verify
```

## Four preserved verdicts

Four signed, single-commit ranges followed the legacy round. `git
verify-commit` exited 0 for every head, each message held one exact copy of the
two provenance trailers, and each controller receipt listed only that new head
in `verified_commits`.

```bash
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --fixes-commit "$FIX_1" --elenchus-verdict guarded "${LINT_ARGS[@]}"
FIX_2=$(signed_fix "issue 327 proof fix unguarded")
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --fixes-commit "$FIX_2" --elenchus-verdict unguarded "${LINT_ARGS[@]}"
FIX_3=$(signed_fix "issue 327 proof fix passed")
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --fixes-commit "$FIX_3" --elenchus-verdict passed "${LINT_ARGS[@]}"
FIX_4=$(signed_fix "issue 327 proof fix inconclusive")
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 0 \
  --fixes-commit "$FIX_4" --elenchus-verdict inconclusive \
  "${LINT_ARGS[@]}"
python3.12 "$HEXCTL" --dir "$DEMO_RUN" next
python3.12 "$HEXCTL" --dir "$DEMO_RUN" done audit
python3.12 "$HEXCTL" --dir "$DEMO_RUN" verify
for FIX in "$FIX_1" "$FIX_2" "$FIX_3" "$FIX_4"; do
  git -C "$DEMO_RUN" verify-commit "$FIX" >/dev/null 2>&1
done
```

| Label | Commit | Round | Findings | Verdict | State SHA-256 | Ledger SHA-256 |
| --- | --- | ---: | ---: | --- | --- | --- |
| `fix-1` | `0757a1ad86d46a34f7825f9545d9da85249f4585` | 2 | 1 | `guarded` | `9b7da5a3f09080a28e4c6c7177b8dc70d52465e54df0f0467bba82e041f5379d` | `508499d4f673d900a230a8092019cacc5a8d3b8d01277e5f9d725fbdd8fec8b8` |
| `fix-2` | `7a619049738680fc9c72d8135c0f21ccb4b3d74d` | 3 | 1 | `unguarded` | `31ff495beb0119e0dafa5b888f8a70d02b8371f53b9a2f707ab9082d9f64dcde` | `28e881d35a7ac2c019c782ea0cce0faa4336ec85ace9a08aed4f48cd5504272a` |
| `fix-3` | `8d75c7ed11a9354e77fda3e60c2d005be205c9a1` | 4 | 1 | `passed` | `6c58341dd01dbaca17ad1fd81c5fc1538ae0f12b5390ee7c79ce3e427556ca61` | `9347130c94b28cc45eaaf2fd9def98d367df6a1433f97023052e38beba9013f5` |
| `fix-4` | `afa46b5241c17663ce1dd17033687e9e5f9c4e7c` | 5 | 0 | `inconclusive` | `e7e2ed0bcf7b07fd5257d875b61ba5c116342bfbad561067fd3e9aa22add0b8e` | `90c76851cb08f124b93a63be55fe8e5ab24c47dd89bcdf67a1bfafa7304f0137` |

The final state remained version 1 and moved the step to `prose`. Its five
rounds exposed `missing`, `guarded`, `unguarded`, `passed`, and `inconclusive`
in order. Final `verify` exited 0. Final state SHA-256 was
`d6952962cb3b8861ccbef5e9c6209e4e582a4bb57372ecbf055ebca74de97909`;
final ledger SHA-256 was
`0ea8be93c18297f4da48aa57e9ac5d68311de6f4f358df638b964ed90d8815ff`.
The successful generated boundary was removed after these assertions.

```bash
python3.12 - "$DEMO_ROOT" "$PROJECT_ROOT/.hexaemeron" <<'PY'
from pathlib import Path
import shutil, sys
boundary = Path(sys.argv[1]).resolve()
expected_parent = Path(sys.argv[2]).resolve()
assert boundary.parent == expected_parent
assert boundary.name.startswith("issue327-step3-")
shutil.rmtree(boundary)
PY
```

## Study and release reconciliation

The receipted study changed once during step 2. Its prior SHA-256 was
`06f8e81b95c7ceba26ada998fe62b57a87d9afa3eea10a31813862842851abe0`,
its amended SHA-256 is
`e416668d0adb0c986ee1080b92ba9f6c07f151ba7b13ecf776b664a75dc26870`,
and the exact 888 appended bytes have SHA-256
`51e378a68b0c39a59b8ba0051b35a8b8ecc6a691446c5862bfbe34eae095debb`.
The committed copy keeps its five repository-relative skill links instead of
the live `.hexaemeron` paths. It therefore moved from
`46531ccad9b908c4af8faa6e13d8ab5842c2032a96ce9e6feb5134bf1f15bf8e`
to `425152f8d8573197f33dcb491892f937798d4fe3b66ec612d8ce8ea05967852f`
after the same 888-byte amendment was appended.

The runbook has a separate one-byte discrepancy already recorded by the run:
the receipted file is 11,430 bytes at
`82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85`;
the committed copy is its first 11,429 bytes at
`a98c67bda303bac1b3aea09817059a07d9dc45a64472847854be7547c4bd555c`.
Only the receipted file's final newline is absent from the committed copy.

The final cold read found no stale release surface:

| Surface | Observed value | Disposition |
| --- | --- | --- |
| Elenchus frontmatter and ledger | `1.2.0`, `elenchus-v1.2.0`, mature | generation row retains the mature frontier; issue 453 stays deferred |
| Fiat frontmatter and ledger | `5.12.1`, `fiat-v5.12.1`, frontier SHA-256 `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa` | generation row retains issue 363's exact held target |
| Protasis frontmatter and ledger | `4.6.0`, `protasis-v4.6.0` | generation row retains the amendment-check frontier |
| Warden and audit loop | four exact values; checked and recorded, not report-byte attestation | issue 453 still owns stronger binding and blocking |
| both plugin manifests and both marketplaces | Hexaemeron `1.5.5` | all package surfaces agree |
| version constants | Hexaemeron `1.5.5`; three skill versions above | tests name the same release |
| Promise coverage | controller SHA-256 `01efd29f...884870` on all three Fiat runtime bindings | canonical promise text and field maps are unchanged |

Issue 429 remains the downstream schema and synopsis work. Issue 453 remains
the report-evidence binding and production gate. Neither was implemented or
closed here.
