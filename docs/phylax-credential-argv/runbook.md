# Runbook: flag credential-named values in subprocess argv

- capability: flag credential-named values in resolved subprocess argv.
- boundary: inspect the source-local `args` expression only.
- delivery shape: one atomic implementation and verification step.

## Construction

The chosen construction walks the `args` expression of calls resolved by
`_starts_process` and applies P004 to matching `ast.Name` nodes. Splitting the
fixture, visitor change, governed prose and generation row would leave an
intermediate branch either red or misdescribed, so one step both scaffolds the
specification and runs the final demonstration.

## Implementation boundary

The step may change only the named checker, tests, governed Phylax prose,
generation evidence, tracked study and runbook, and regenerated Horos boundary.
Fiat's later audit and pull-request artefacts remain separate phase outputs.

## Step 1: Enforce credential-free subprocess argv

**Goal.** Report P004 when a credential-named value appears in the inline argv
expression of a resolved subprocess runner, without widening the finding beyond
argv or changing an existing finding contract.

**Entry.** The controller's run branch
`fiat/325-phylax-credential-argv-r2` at
`4408597bcd0130b0cee8bd7aab0b55d64ff957c7`, with `.hexaemeron/study.md`
receipted at SHA-256
`7bb214f42361f33a8b4ab71f5f9ad22b9a2c88431311b5abff482b50935154d0` and
the focused Phylax suite green at 46 tests under Python 3.9.6 and 3.12.13.

**Exit.** The committed study and runbook match the receipted artefacts. A
focused guard first reproduces the missing P004 finding, then passes after the
visitor inspects only the first positional `args` expression or, when it is
absent, the explicit `args=` expression of a resolved runner. Module imports,
module aliases, direct imports and direct-import aliases report; inline list
concatenation reports without gaining P002. Ordinary argv values, a local
`run`, an unrelated `.call` and an `env=`-only credential stay clean. A
reason-bearing suppression clears the new finding, a bare pragma does not, and
text and JSON results never contain the fixture credential value. P000-P003,
the existing P004 writer check, CLI arguments, output schemas and exit codes
remain unchanged.

`plugins/hexaemeron/skills/phylax/SKILL.md` names command arguments in P004's
mechanical scope, and the Promise Machine coverage digest is recomputed for the
changed canonical bytes. `plugins/hexaemeron/skills/phylax/EVOLUTION.md` moves
once to `phylax-v1.2.0` on the generation axis while retaining frontier status
`mature`, revision `off-chain-boundary-controls`, current-frontier text, next
job `None -- mature` and digest
`3d0057bb195f303c0e40b5782bf59ab0cba53e3172478c6a331d5990236ac604`.
The tracked-file boundary is regenerated and current. The step is complete
when every command below exits zero and both `cmp` commands produce no output:

```bash
cmp .hexaemeron/study.md docs/phylax-credential-argv/study.md
cmp .hexaemeron/runbook.md docs/phylax-credential-argv/runbook.md
uv run --python 3.12.13 python -m unittest plugins.hexaemeron.tests.test_phylax_checker
uv run --python 3.12.13 python plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
uv run --python 3.12.13 python plugins/hexaemeron/tests/run_tests.py
uv run --python 3.12.13 python -m unittest discover -s tests
uv run --python 3.12.13 python -m unittest tests.test_evolution_contract
uv run --python 3.12.13 python scripts/promise_machine.py check
uv run --python 3.12.13 python plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/phylax-credential-argv/study.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/phylax-credential-argv/runbook.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/phylax-credential-argv/*.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md
(
  for file in docs/phylax-credential-argv/study.md docs/phylax-credential-argv/runbook.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md; do
    uv run --python 3.12.13 python plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file" || exit
  done
)
uv run --python 3.12.13 python plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
uv run --python 3.12.13 python plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
uv run --python 3.12.13 python plugins/horos/skills/horos/scripts/horos.py scan . --write
uv run --python 3.12.13 python plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Create or change only these planned paths, plus pull-request
artefacts required by Fiat's later phases:

- `plugins/hexaemeron/skills/phylax/scripts/phylax.py`
- `plugins/hexaemeron/tests/test_phylax_checker.py`
- `plugins/hexaemeron/skills/phylax/SKILL.md`
- `plugins/hexaemeron/skills/phylax/EVOLUTION.md`
- `tests/promise_machine_coverage.json`
- `docs/phylax-credential-argv/study.md`
- `docs/phylax-credential-argv/runbook.md`
- `.horos/boundary.json`
- `audit/AUDIT.md` when the audit phase records its rounds

**Tests.** Add the hostile argv specimen before the visitor change and record
its missing P004 result. Cover module, module-alias, direct-import and
direct-import-alias runners; positional and keyword `args`; list
concatenation; the four safe neighbours above; reason-bearing and bare
suppressions; unchanged P001/P002 classification; and secret-free text and JSON
rendering. Preserve all 46 existing focused tests and add at least 13 bounded
cases. Run the focused suite after the red-to-green change, then every exit
command above.

**Disciplines.** phylax: untrusted Python source reaches a new argv-only P004
check, closed by existing runner resolution, source-local AST walking, safe
neighbours and secret-free diagnostics. ephoros: none, the checker adds no
unattended service and preserves its existing path, line, code and exit
signals. metron: none, no performance claim or speed-motivated edit is
authorised. elenchus: the missed hostile specimen is captured red before the
cause-level visitor change and every regression must turn green before broader
gates run. hypomnema: the tracked study and runbook hold the build contract,
the audit file holds round evidence, and the Phylax generation row records the
source-local decision without reopening the mature frontier.
