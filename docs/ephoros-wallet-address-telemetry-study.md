# Study: Ephoros catches telemetry keyed by wallet address across Python and TypeScript

Assuming, unless corrected:

1. The run starts from `main` at `6412c85d7cfd352e21fcc3dc0d8cef39a0649976`. The
   TypeScript conformance corpus is the read-only shallow clone of
   `wildcat-app-v2` at `/home/user/wildcat-finance/wildcat-app-v2`, HEAD
   `564a189`. Neither that clone nor any vendored directory is edited.
2. "Telemetry keyed by wallet address" means an address in a key position of a
   telemetry sink: a metric label, a dashboard key, or a log index. An address
   inside an event's fields or message stays legal, which is the line
   `ephoros/SKILL.md` already draws in prose: where an address is genuinely
   needed to diagnose, it goes in an event, never in a metric label or a
   dashboard axis.
3. E005 is the new finding code. E000 to E004 keep their numbers and firing
   conditions, with one exception decided in item 4: a metric label whose name
   is address-shaped reports E005 rather than E002, and a guard test pins the
   move.
4. Python 3.11 and the standard library remain the implementation boundary.
   The TypeScript surface is read through the attributed Horos lexer already
   vendored at `plugins/hexaemeron/lib/typescript_lexer.py`, the same way
   `phylax.py` reads it. No Node invocation, no tree-sitter, no new
   dependency.
5. `console.*` in TypeScript is treated the way `print` is treated in Python:
   command-line output rather than telemetry, outside the lint's claim.
   Logger objects (the app's `@wildcatfi/wildcat-sdk` `logger`), metric
   clients and analytics sinks are inside it.
6. This is frontier work under
   [skills#322](https://github.com/wildcat-finance/skills/issues/322).
   Closing it moves the evolution counter, `ephoros-v0.2.0` to
   `ephoros-v0.3.0`, replaces the held next job with a successor, and owes the
   cold read of mutable first-party marketplace prose that the versioning
   contract requires of every frontier run.
7. Phylax is untouched: P000 to P007 keep their numbers, and nothing phylax
   owns (secrets, session storage, fetch hosts, sanitisers, personal-data
   linkage caches) moves into ephoros.

I will proceed on these assumptions unless corrected.

## 1. Problem statement

`ephoros/SKILL.md` forbids indexing telemetry by wallet address, and today that
rule is read by a person. The checker at
`plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` reads Python and a
block-YAML subset, and nothing reads the TypeScript application at all. Build
E005: a bounded rule that reports an address used as a metric label, a
dashboard key or a log index, in Python and in TypeScript, for Wildcat
contributors and for the Fiat gates that run the tree lints on every step.

A working prototype is established by these commands:

- `python3 -m unittest plugins.hexaemeron.tests.test_ephoros_checker` reports
  one E005 for each of the three acceptance shapes -- an address as a metric
  label, as a dashboard key, and as a log index -- each held by a fixture in
  Python and by a fixture in TypeScript, and each observed red before the
  recogniser lands. Negative fixtures prove an address inside an event's
  fields or message, a react-query `queryKey`, and a plain storage key do not
  fire.
- `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
  scripts` exits 0 over this marketplace.
- `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py
  /home/user/wildcat-finance/wildcat-app-v2` exits 0 over the pinned
  application clone, now reading its 882 tracked `.ts`/`.tsx` files.
- `python3 plugins/hexaemeron/tests/run_tests.py` passes: the Hexaemeron
  plugin suite.
- `python3 -m unittest discover -s tests` passes: the root suite of
  `/home/user/skills`.
- `python3 -m unittest tests.test_evolution_contract` accepts the
  `ephoros-v0.3.0` row with its successor job.

The demo path is that block of commands, run in order on the finished tree.

## 2. Prior art

**In this repository.** `ephoros.py` ships E000 to E004. E002 is the nearest
neighbour and the reason this job is still unmet. Its `UNBOUNDED` identifier
regex at `ephoros.py:33` already carries an `address|wallet` fragment, and it
fires only when a call site passes a `labels`, `labelnames`, `label_names`,
`tags` or `attributes` keyword whose value is a literal dict, list, tuple or
set of string label names. It misses the Prometheus instance style
`counter.labels(wallet_address=addr)`, says nothing about dashboard keys or
log indexes, and reads no TypeScript, because the checker walks only `.py`,
`.yaml` and `.yml` files. The held frontier in `ephoros/EVOLUTION.md` names
exactly this gap. `phylax.py` is the architectural precedent for the missing
language: P005 to P007 read `.ts`/`.tsx` through
`plugins/hexaemeron/lib/typescript_lexer.py` (absorbed from Horos at commit
`b95f332`, never executing inspected source), cap reads at 1 MiB with `P000`
fail-closed, and honour `// phylax: allow <why>`.

**The last two merged pull requests that changed ephoros, both read.**

- [skills#426](https://github.com/wildcat-finance/skills/pull/426), "Drop the
  sibling-handoff paragraph from every skill surface" (merged 2026-08-21).
  It removed one paragraph from `ephoros/SKILL.md` among 34 files and
  re-pinned four Promise Machine digests, ephoros among them. Carried forward
  in its body: the unlabelled routing clause inside 118 marketplace-context
  blocks was deliberately left as a separate decision. It stays open here by
  name: it is a marketplace-wide prose decision, not ephoros lint work, and
  this run's prose reconciliation touches ephoros context blocks only where
  the frontier sentence moves.
- [skills#356](https://github.com/wildcat-finance/skills/pull/356), "Require
  local runbook annotations on alert rules" (merged 2026-08-21). It shipped
  E004 and the generic block-YAML machinery across eight audit rounds plus
  post-cap closure. Its body fixes the boundary this study keeps: ephoros owns
  annotation presence, Hypomnema H003 and H007 own resolution and target
  shape, and remote URLs and configuration dialects sit outside. Both remain
  non-goals here, restated in item 3.

**Audit records, read before the options below were drawn.** `audit/AUDIT.md`
and `plugins/hexaemeron/audit/AUDIT.md`, every round touching ephoros, phylax
or telemetry rules:

- "Ephoros alert-runbook annotations" rounds `E319-S2-R1` through `E319-S2-R8`
  and two post-cap closures resolved sixteen findings, nearly all in the
  hand-rolled YAML lexing boundary: suppression state inside quoted and block
  scalars, cross-line quote state, plain-scalar continuations and folds. That
  history is design evidence here: scanning unmasked text is where those
  defects lived, so the TypeScript pass rides the existing masked lexer
  rather than raw regex (option D below is rejected on it).
- Accepted-not-pursued leads carried forward by name: **non-HTTP URI schemes**
  and **unquoted hashes in plain scalar paths** remain outside the documented
  relative-path prototype (`E319-S2-R1` leads). They stay outside here too:
  E005 adds no pointer handling, so neither lead is reopened.
- "Phylax TypeScript boundaries" (2026-08-19) added the 1 MiB TypeScript read
  cap with `P000` fail-closed because the checker had read untrusted files
  whole. E005's TypeScript pass inherits the same bound, as a register entry.
- "Receipted lint rounds", integrate note (2026-08-19): no CI workflow runs
  the Hexaemeron suite, so lint and suite evidence is local. Still true;
  touching CI stays ask-first and this run does not claim it.
- `plugins/hexaemeron/audit/AUDIT.md` holds no ephoros finding; its F-01 to
  F-10 concern `hexctl.py`, `hook_gate.py` and the vendored prose lint, and
  its accepted leads (`os.replace` atomicity, concurrent `hexctl`, ANSI
  passthrough) do not touch this job.

**The real telemetry surfaces, surveyed rather than assumed.**

- This marketplace's Python: the tree lints run clean today
  (`ephoros.py plugins tests scripts` exits 0, verified on the starting ref).
  Ariadne, Tabularium and Lazarus handle addresses as data -- captures,
  witnesses, releases -- and none of them keys a metric, dashboard or log
  store by one. The only label-kwarg vocabulary in tree is the checker's own.
- `wildcat-app-v2` at `564a189`, 882 tracked TypeScript files: its telemetry
  is Hotjar (`Hotjar.init` in `src/components/HotjarConsent/index.tsx`,
  consent-gated, with no identify or event call), the SDK logger imported from
  `@wildcatfi/wildcat-sdk/dist/utils/logger` used as `logger.debug(...)`
  template messages, and 164 `console.*` lines including address-bearing
  templates in `src/app/api/mla/[market]/route.ts:72`. One logger call,
  `src/app/[locale]/borrower/market/[address]/hooks/useGetLenders.ts:30`,
  interpolates lender addresses into a message: an event-shaped use E005
  leaves alone under assumption 2. `package.json` names no prom-client,
  Sentry, PostHog, Datadog or Mixpanel. react-query `queryKey` arrays carry
  addresses throughout (`src/config/query-keys.ts`), and
  `src/utils/timestamp.ts` keys localStorage by `${TIMESTAMP_KEY}_${address}`:
  cache and storage keys, not telemetry sinks, so the recognisers are scoped
  to sinks and neither fires. The three workflow YAMLs carry no alert entries
  and no address keys.

The three acceptance shapes therefore exist in neither tree today: the
fixtures supply them, and the clean-run criterion over the read-only clone is
satisfiable without a single suppression pragma.

## 3. Constraints and non-goals

- Starting ref: `main` at `6412c85d7cfd352e21fcc3dc0d8cef39a0649976`.
  `wildcat-app-v2` pinned at `564a189`, read-only.
- Python 3.11, standard library only. The TypeScript lexer already in
  `plugins/hexaemeron/lib/` is the one permitted reader; this repository's
  plugins run on stdlib by convention (`phylax/SKILL.md` states it as the
  house default, and Lazarus's four pinned packages are the stated exception),
  verified against the tree: no ephoros or phylax script imports outside the
  standard library and the plugin `lib`.
- Finding codes are stable interfaces. E000 to E004 keep their numbers and
  behaviour, except the address-named metric-label subset of E002, which E005
  claims (item 4). P000 to P007 are untouched.
- The rule boundary: ephoros stops at the presence and shape of telemetry;
  phylax owns secrets, session storage, fetch hosts, sanitisers and the
  personal-data linkage section. Item 9 draws the line once.
- Non-goals, each deliberate: a TypeScript analogue of E001 (message built by
  formatting); any `console.*` discipline (assumption 5); the `lenders-name`
  address-to-name cache in the application, which is phylax's personal-data
  linkage concern, not telemetry shape; remote runbook URLs and configuration
  dialects (carried from skills#356); dataflow or rename tracking -- the rule
  is lexical, like every other rule in this checker, so an address flowing
  through an innocently named variable passes; CI changes.
- **Always.** Both suites (`python3 -m unittest discover -s tests`,
  `python3 plugins/hexaemeron/tests/run_tests.py`) before a commit; the
  imprimatur lint on every shipped document; the focused checker tests, the
  evolution and version-propagation gates, Promise Machine, and the Phylax,
  Ephoros and Hypomnema tree lints before each step closes.
- **Ask first.** Adding a dependency (tree-sitter or any YAML/TS parser);
  touching CI; changing a public checker interface beyond adding E005;
  widening the walk to new suffixes beyond `.ts`/`.tsx`; editing anything in
  the application clone.
- **Never.** Edit vendored directories or the read-only clone; weaken an
  existing rule to make a tree pass; delete a failing test; commit a
  credential; claim a command ran when it did not.

## 4. Design options

**A. One rule, one checker, the shared lexer (chosen).** Add E005 inside
`ephoros.py`. Python: extend the existing `ast.NodeVisitor` with three
recognisers -- an address-named or 40-hex-literal metric label (both the
`labels=[...]` constructor style E002 sees and the `.labels(wallet=...)`
instance style it misses), an address-shaped key on a dashboard-named target,
and an address-shaped key or `index=` argument on a log-named target.
TypeScript: add `check_typescript` importing `lib.typescript_lexer` exactly as
`phylax.py:27-31` does, mask comments and strings, and recognise the mirrored
three shapes over the masked source, with the 1 MiB cap, `E000` fail-closed on
lexer errors, and `// ephoros: allow <why>` beside the existing `#` form.
YAML: an address-named key under a `labels:` mapping of a supported alert
entry rides the block-YAML pass E004 already owns. The trade: lexical
recognition sees named shapes only, so a renamed address passes -- accepted,
because every rule in this checker (and in phylax) makes the same trade, and
the fixtures pin exactly what is claimed.

**B. A separate TypeScript scanner.** A second script (Python, or Node running
the TypeScript compiler API) invoked beside `ephoros.py`. Rejected: executing
Node against inspected source breaks the precedent phylax states in its own
SKILL.md (the lint never invokes Node or loads the target's dependencies), and
a second entry point splits one gate into two invocations that can drift apart
in walks, caps and suppression rules.

**C. tree-sitter for a real TypeScript AST.** Deeper recognition, fewer
lexical misses. Rejected: an ask-first native dependency against the stdlib
convention, a grammar to vendor and pin, and a comprehension cost the whole
plugin has so far refused to pay. Nothing in the acceptance needs more than
key-position recognition.

**D. Raw regex over unmasked TypeScript text.** Cheapest to write. Rejected on
this run's own audit evidence: the sixteen `E319` findings were almost all
unmasked-text boundary defects, and the masked lexer that avoids the class
already sits in `plugins/hexaemeron/lib/`.

A is the pick: it is the cheapest to comprehend that meets the acceptance --
one checker, one walk, one suppression grammar, and an architecture the
repository has already audited once in phylax.

One sub-decision rides the pick. An address-named metric label matches both
E002's `UNBOUNDED` regex and E005. One concern gets one code: E005 claims the
address-shaped subset (`address`, `wallet`, `addr` fragments and 40-hex
literals), E002 keeps every other unbounded fragment (`hash`, `tx`, `url`,
`error` and the rest), and a guard test pins that the label `wallet_address`
now yields E005 and not E002. No consumer's output changes in practice: both
trees are clean of address labels today, so no existing finding moves. The
decision is recorded where item 12 puts it.

## 5. Risk register seed

The audit loop should look hardest at the checker's own input boundary and at
the two clean-run claims, because those are where this run can fail quietly.
The `E319` rounds spent sixteen findings on exactly the first class.

```risk-register
ts-lexer-input | untrusted TypeScript read by the shared lexer | the 1 MiB cap applies before lexing, lexer errors fail closed as E000, and no inspected source is executed or imported
false-positive-cache-keys | react-query queryKey arrays and storage keys in the read-only clone | the recognisers are scoped to telemetry sinks, and the clone run exits 0 with zero suppression pragmas
rule-boundary-drift | the ephoros and phylax line over the same TypeScript files | E005 reads telemetry shape only, and no P004 to P007 pattern or personal-data concern is duplicated or moved
e002-reassignment | call sites whose label names are address-shaped | a guard test pins E005 claiming the subset and E002 keeping the rest, observed red before the change
suppression-parity | the TypeScript pragma beside the Python one | a reasoned ephoros allow comment suppresses in both comment styles and a bare pragma suppresses nothing, each tested
yaml-label-keys | address-named keys in supported block-YAML label mappings | the recogniser stays inside the E004 block-YAML subset and the accepted URI and hash leads stay outside
fixture-exclusion | fixture trees under the tree-lint walks | the caught specimens live under fixtures directories the walk already skips, so the clean-run criteria stay honest
walk-widening | node_modules or build output under a scanned root | the TypeScript walk excludes node_modules the way the Python walk excludes __pycache__, held by a test
```

The prose the block cannot carry: `false-positive-cache-keys` is the risk that
decides whether this design survives contact with the application. The survey
in item 2 says the clone's address flows are messages, cache keys and storage
keys; if a recogniser drafted in the runbook fires on any of them, the fix is
narrowing the recogniser, never a pragma in a read-only tree and never a
weaker fixture.

## 6. Glossary seeds

- Address key: a wallet address, or an identifier naming one (`address`,
  `wallet`, `addr` fragments, or a `0x` 40-hex literal), in a key position.
- Telemetry sink: a call surface that stores or emits operational signals: a
  logger object, a metric client, an analytics client, a dashboard or panel
  structure, a log store.
- Metric label: a name in a bounded label set on a metric series (`labels=`,
  `labelnames=`, `tags=`, `attributes=`, or `.labels(...)`).
- Dashboard key: a key that selects a dashboard axis, panel or series.
- Log index: a key by which a log store is partitioned or looked up, as
  opposed to a field inside one event.
- Masked source: TypeScript text with comments and string bodies blanked by
  the shared lexer, so recognisers cannot match inside either.
- Event field: a queryable key-value inside one emitted event; the legal home
  for an address that diagnosis genuinely needs.
- Reasoned pragma: `# ephoros: allow <why>` or `// ephoros: allow <why>` on
  the finding line or the line above; a bare pragma suppresses nothing.

## 7. Sources

- `plugins/hexaemeron/skills/ephoros/SKILL.md`, `EVOLUTION.md`,
  `scripts/ephoros.py`, `agents/openai.yaml` -- the skill, its held job, the
  checker.
- `plugins/hexaemeron/skills/phylax/SKILL.md`, `scripts/phylax.py`,
  `plugins/hexaemeron/lib/typescript_lexer.py` -- the boundary owner and the
  TypeScript precedent.
- `plugins/hexaemeron/tests/test_ephoros_checker.py`,
  `tests/fixtures/ephoros/` -- the fixture and test conventions E005 extends.
- [skills#322](https://github.com/wildcat-finance/skills/issues/322) -- the
  held job and acceptance.
- [skills#356](https://github.com/wildcat-finance/skills/pull/356) and
  [skills#426](https://github.com/wildcat-finance/skills/pull/426) -- the last
  two merged pull requests that changed ephoros.
- `audit/AUDIT.md` -- the `E319` rounds, "Phylax TypeScript boundaries" and
  "Receipted lint rounds"; `plugins/hexaemeron/audit/AUDIT.md` -- the plugin's
  own two rounds.
- `docs/ephoros-alert-runbook-annotations-study.md` -- the E004 study whose
  boundary decisions this study inherits.
- `/home/user/wildcat-finance/wildcat-app-v2` at `564a189`: `package.json`,
  `src/components/HotjarConsent/index.tsx`, `src/config/query-keys.ts`,
  `src/utils/timestamp.ts`, `src/app/api/mla/[market]/route.ts`,
  `src/app/[locale]/borrower/market/[address]/hooks/useGetLenders.ts`.

## 8. Signals, and the questions behind them

None, and here is why: the deliverable is a lint invoked from a terminal and
from Fiat gates, and a terminal lint has no three-in-the-morning question --
it runs, prints findings, and exits. Its visibility contract is its exit code
and finding lines, which the receipted rounds already record.
[ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal
must carry, and this run changes what that skill enforces, not what this run
itself must emit.

## 9. Boundaries, per capability

This step opens one boundary: the checker now reads untrusted TypeScript from
an outside repository. What is worth taking at it is the checker's own
runtime -- memory, time, or a crafted file that wedges the lexer -- and the
control is the one phylax already audited: a 1 MiB read cap enforced before
lexing, `E000` fail-closed on any construct the lexer cannot terminate, and no
execution or import of inspected source. That feeds the `ts-lexer-input`
register line rather than replacing it.

The boundary between the two lints, drawn once as the issue asks:
[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns what crosses trust
boundaries -- secrets in source or output (P004), raw HTML and sanitisers
(P005), session credentials in persisted storage (P006), fetch hosts (P007),
and the personal-data and address-linkage judgement sections, including caches
that pair addresses with names. Ephoros owns the presence and shape of the
telemetry a step leaves behind -- and E005 is the one address rule that is
telemetry shape rather than boundary control: an address used as a metric
label, dashboard key or log index. The same `.ts` file may carry findings from
both lints; no pattern is owned by both.

## 10. The budget, or its absence

None is set, and here is why: the checker gains one AST pass and one lexical
pass whose per-file work is bounded by the 1 MiB cap, the same shape phylax
already runs over the identical 882-file tree with no recorded budget and no
complaint in any receipted round. A budget without a recorded baseline would
be taste, which [metron](../plugins/hexaemeron/skills/metron/SKILL.md) --
owner of what a budget carries and how it is checked -- refuses; if a tree-run
ever feels slow, the first act is metron's baseline of
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py <tree>`, not a
number invented here.

## 11. The fail-closed posture

The lint stops rather than guesses: an unreadable file, an oversized file, an
unparseable Python module or a TypeScript construct the lexer cannot terminate
each report `E000` and fail the run; findings exit 1; a bad invocation exits
2. A bare pragma suppresses nothing. During the audit loop, every fix follows
the guard-test convention this run's prior art already practises: the failing
case lands as a test observed red before the fix and kept green after, the way
all sixteen `E319` resolutions were evidenced.
[elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage
order and the guard rule; this study only names where they will apply.

## 12. Decisions and their homes

Two decisions here are expensive to reverse, and
[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each lives.

- **E005's scope and the E002 subset move.** Once published, other tools cite
  the codes, so reassigning the address-shaped labels later would change
  recorded findings. Home: the `ephoros-v0.3.0` evolution row in
  `plugins/hexaemeron/skills/ephoros/EVOLUTION.md` and the mechanical-subset
  section of its `SKILL.md`, which is where E004's equivalent decision lives.
- **The ephoros/phylax line over shared TypeScript files.** It binds two
  skills that evolve on separate ledgers, so it outlives both checkers'
  internals. Home: an architecture decision record under `docs/decisions/`
  (next free number ADR-008), pointed at from both SKILL.md boundary
  sentences rather than restated in them.
