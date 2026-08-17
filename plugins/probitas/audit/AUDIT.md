# Audit log: probitas

<!-- marketplace-context:start -->
> **Record status.** This is a historical audit record; findings and dispositions below are preserved as evidence. Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict. Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty. **Current frontier:** Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.
<!-- marketplace-context:end -->

Every security review of this plugin, in the order they happened, including the
ones that found nothing and the ones whose fixes were wrong and had to be
fixed again.

Probitas ships Markdown and Python and no Solidity, so the usual contract
audit tooling has nothing to point at. Each round below is a manual read of
what changed since the last one, plus whatever mechanical sweep the change
deserved: randomised input over the sanitiser, mutation of every field in a
fixture, forged tampering of a rendered document.

Rounds that found nothing are recorded too. A log that only lists findings
tells you what was caught and not what was looked at.

## Step 1, round 1 -- 2026-08-15

Reviewed: the whole of `cb0f8f9`. Two plugin manifests, two root marketplace
manifests, SKILL.md, two reference stubs, README, LICENSE, committed study and
runbook, one test module, one CI workflow, `.gitignore`.

Only two concerns are live at this step, since there is no code yet: how
arguments and paths are handled, and whether the output is deterministic.
Everything about sourcing, personal data, untrusted input and venue drift was
checked as absent rather than sound.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | .github/workflows/probitas.yml | The workflow declared no `permissions` block, so the job ran with whatever default token scope the repository grants. It reads a checkout and runs unittest and needs nothing else. | fixed in 3d1b0f1 |
| S1-R1-02 | info | plugins/probitas/tests/test_manifests.py | A missing marketplace entry raised `StopIteration` from a generator rather than failing the assertion, which reports as an error with no useful message. | fixed in 3d1b0f1 |
| S1-R1-03 | info | .github/workflows/probitas.yml | Actions are pinned to floating major tags (`actions/checkout@v4`, `actions/setup-python@v5`) rather than commit digests, so an upstream tag move changes what runs. | accepted |

Checked and clean:

- All four JSON manifests parse. Names agree, versions agree across both
  plugin manifests and the SKILL.md frontmatter.
- The SKILL.md frontmatter description is 492 characters, inside the limit,
  and states both when to trigger and when not to.
- No credential, key or token anywhere in the tree.
- Nothing in the diff executes a shell, evaluates a string, opens a socket or
  writes outside the repository. `test_manifests.py` reads five files by
  absolute path derived from `__file__` and does nothing else.
- The `pull_request` trigger is the safe form rather than `pull_request_target`,
  so a fork's code never runs with this repository's secrets.
- `.gitignore` covers `__pycache__`, which the first commit attempt had
  otherwise carried into the tree.
- LICENSE is the Apache-2.0 text with the copyright line filled in.

Leads not pursued: S1-R1-03. Digest pinning is the stricter posture and worth
taking when this plugin moves into the public marketplace repository, but the
workflow now holds a read-only token, handles no secrets, and publishes
nothing, so a tag move can at most break the build. Recorded rather than fixed
so that whoever hardens the marketplace repository finds it already written
down.

## Step 1, round 2 -- 2026-08-15

Reviewed: the round 1 fixes for regressions, then the tree again.

The `permissions` block sits at the workflow level and so covers every job,
which is what was wanted. `marketplace_entry` is a helper rather than a test,
since its name does not begin with `test_`, and the six tests still pass.
Neither fix introduced anything.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | info | audit/AUDIT.md | The audit log sat at the repository root. This repository will hold four plugins before long and a top-level `audit/` belongs to none of them. A plugin should carry its own log inside its own directory. | fixed in 3ef025f |
| S1-R2-02 | low | .github/workflows/probitas.yml | The README and the study both claim Python 3.9 or later, and CI tested 3.11 alone. An untested compatibility claim is a claim that quietly stops being true. | fixed in 3ef025f |

Leads not pursued: none.

## Step 1, round 3 -- 2026-08-15

Reviewed: the tree with both rounds of fixes applied.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Nothing found. Checked this round:

- Every relative link in every Markdown file in the repository resolves to a
  file that exists, across all 9 documents.
- Both Python files parse. Neither uses syntax younger than 3.9, so the
  compatibility claim the matrix now tests is one the code can meet.
- The workflow file carries no tab characters and both new keys sit at the
  level they need to.
- The audit log now lives beside the plugin it belongs to.
- The round 2 fixes introduced no regression: six tests, all passing.

Leads not pursued: S1-R1-03 remains accepted, for the reason recorded under
round 1. Nothing else is open.

## Step 2, round 1 -- 2026-08-15

Reviewed: `72499d1`. The evidence model, the CLI, the venue registry, the
adapter protocol and the sanitiser. First step with executable code in it, so
everything is live except venue drift, which needs an adapter to be wrong
about.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | scripts/probitas_lib/evidence.py | A URL source was accepted with any non-space characters in it, and the renderer writes a source into a Markdown link. `https://x/y)](https://evil/` closes the link early and takes the rest of the document with it. Sources arrive from adapters, which is to say from the network. | fixed in c316dc2 |
| S2-R1-02 | high | scripts/probitas_lib/evidence.py | Passing the same address as both declared and inferred silently kept whichever came last, so an inferred address could be read as declared. Gate 1 exists to keep those tiers from blurring and this blurred them. | fixed in c316dc2 |
| S2-R1-03 | medium | scripts/probitas_lib/evidence.py | `values` took any key. The study says the evidence file has no field a person's identity fits in, and nothing enforced it, so `values={"director_name": ...}` was a legal record. | fixed in c316dc2 |
| S2-R1-04 | low | scripts/probitas_lib/evidence.py | A non-scalar value was coerced with `str()`, so a dict or list would reach the dossier as a Python repr. Sources and values were also unbounded in length. | fixed in c316dc2 |
| S2-R1-05 | low | scripts/probitas_lib/sanitise.py | Truncation ran before Markdown escaping, so a string of metacharacters at the cap came back over it, and a cut could land mid-escape and leave a dangling backslash. | fixed in c316dc2 |

Checked and clean:

- `_wire` tests `bool` before `int`, which matters because `bool` subclasses
  `int` in Python and a flag would otherwise serialise as `"True"`.
- `run_adapter` catches `Exception` rather than `BaseException`, so a
  keyboard interrupt still stops the run instead of being logged as a venue
  error.
- `collect` raises a gap for `unimplemented`, `unconfigured` and `error`, and
  correctly does not raise one for `empty`. A venue that was checked and found
  nothing is a finding, not a hole.
- No shell invocation, no `eval`, no `subprocess` outside the test suite, and
  no network call anywhere in this step's code.
- Serialisation sorts records, coverage rows and gaps, so two runs over the
  same findings produce the same bytes.

Leads not pursued: the personal-data guard is a key-name check, so an adapter
determined to smuggle an identity could still put one in a value. Every adapter
in this plugin is ours and the check catches the accident rather than the
attack, which is the threat that matters here. Recorded rather than deepened.

## Step 2, round 2 -- 2026-08-15

Reviewed: the round 1 fixes, then the tree again. Round 1's third fix turned
out to overreach, which is the case for running a second round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | scripts/probitas_lib/evidence.py | The personal-key guard refused `market_name`, `token_name` and `market_age`. A market has a name and so does a token, and the Wildcat adapter in step 3 needs both. A guard that blocks the data the next step depends on gets loosened by whoever hits it, which is worse than a guard that never fired. | fixed in 4c377b1 |
| S2-R2-02 | low | scripts/probitas_lib/evidence.py | A `doc:` reference could carry a pipe, which breaks out of a Markdown table cell. Round 1 refused the link metacharacters and missed the table one. | fixed in 4c377b1 |

The fix for S2-R2-01 is an explicit list of keys that name a thing rather than
a person, checked before the guard. The guard itself stays broad: a false
positive costs one line in that list, and a false negative puts a person in a
dossier.

Checked for regressions from round 1:

- The source pattern still accepts an ordinary transaction hash, an ordinary
  URL and an ordinary document reference. The three permitted kinds are tested
  directly rather than only in the negative.
- Truncation now strips a trailing backslash before appending the ellipsis, so
  a cut landing mid-escape cannot leave a dangling one. Tested.
- The duplicate-address check compares tiers rather than addresses, so the same
  address given twice in the same tier is still fine. Tested both ways.

Leads not pursued: none.

## Step 2, round 3 -- 2026-08-15

Reviewed: the tree with both rounds applied, plus a randomised sweep over the
sanitiser and the source classifier. 20,000 generated strings drawn from
printable ASCII plus a zero width space, a right-to-left override, a byte order
mark, a non-breaking space, a null, an unassigned codepoint and every Markdown
metacharacter. The sweep is what found both of these; neither was visible by
reading.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | medium | scripts/probitas_lib/evidence.py | Round 1 excluded link syntax from a URL source and round 2 excluded a pipe from a document reference, and between them nobody excluded a pipe from a URL. Sources render inside a Markdown table, so `https://x/a|b` invents a column. | fixed in 7038d88 |
| S2-R3-02 | medium | scripts/probitas_lib/evidence.py | A URL source could carry a control or format character. A right-to-left override inside a URL makes it display as a different address than the one it points at, in a document whose whole purpose is that a reader can check the citation. Nulls, byte order marks and zero-width spaces got through the same hole. | fixed in 7038d88 |

The second is refused rather than stripped. Quietly rewriting a citation is
worse than rejecting it: the operator finds out either way, and only one of
those tells them.

Sweep results after the fixes, over 40,000 generated sources and 25,000
generated names:

- No unexpected exception and no output over the length cap.
- No control or format character survives `clean()`.
- No accepted source carries link syntax, table syntax, whitespace or a
  control character once normalised. Surrounding whitespace is still
  forgiven, which is deliberate and tested.
- Serialisation is identical across 200 shuffles of the same twelve records.

Leads not pursued: none.

## Step 2, round 4 -- 2026-08-15

Reviewed: the tree with all three rounds of fixes, and the round 3 fixes for
regressions.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Nothing found. Checked this round:

- The randomised sweep comes back clean on every count: no unexpected
  exception, nothing over the length cap, no control or format character
  surviving `clean()`, no accepted source carrying link or table syntax once
  normalised, and identical output across 200 shuffles of the same records.
- Refusing control characters in a source did not also refuse the ordinary
  ones. All three permitted kinds still classify, and surrounding whitespace
  is still stripped rather than rejected, which is tested in both directions.
- 13 Python files, none using syntax newer than 3.9, so the CI matrix runs
  what the README claims.
- The CLI answers `--help` and a bare `collect` writes nine coverage rows and
  nine gaps for a subject with no adapters to run, which is the behaviour gate
  2 is for.
- 74 tests, all passing.

Leads not pursued: the personal-data guard remains a key-name check, accepted
under step 2 round 1 for the reason recorded there. Nothing else is open.

## Step 3, round 1 -- 2026-08-15

Reviewed: `19ac7a9`. The Wildcat adapter, the GraphQL client, the endpoint
table, four fixtures and their tests. First step that talks to the network, so
five concerns land at once: coverage misreporting, untrusted input, numeric
handling, drift between fixtures and the live venue, and determinism.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | scripts/probitas_lib/adapters/wildcat.py | Both pagination loops were `while True` with no ceiling. A venue answering a full page every time pages for ever, and the operator sees a command that never returns rather than a venue that failed. | fixed in c90d13c |
| S3-R1-02 | medium | scripts/probitas_lib/graphql.py | `urlopen` follows redirects. The https check happens on the URL that was asked for, not the one that answered, so an endpoint could hand the client to plain http or to another host and the reply would still arrive looking like data from the venue. | fixed in c90d13c |
| S3-R1-03 | low | scripts/probitas_lib/adapters/wildcat.py | The market id came off the network and went into a record value without being checked. It is an address, and taking the venue's word for its shape would let a bad response put arbitrary text in a table cell. | fixed in c90d13c |
| S3-R1-04 | low | scripts/probitas_lib/adapters/wildcat.py | Pairing a delinquency entry with its cure trusted the query's ordering, and a repeated entry with no cure between overwrote the start. Both produce a wrong number of seconds attached to a named borrower, and the second understates it, which is the dangerous direction. | fixed in c90d13c |

The pagination ceiling raises rather than truncating. Stopping quietly at a cap
would put a partial history under a coverage row reading `checked`, which is
the failure gate 2 exists to prevent.

Checked and clean:

- Every record from all three fixtures carries a transaction hash as its
  source, asserted directly rather than assumed.
- Market names and token symbols go through the sanitiser before they reach a
  record. Borrower addresses are validated, and a market returned for an
  address the operator did not ask about raises rather than being reported.
- No emitted key names a person. The two that name a thing, `market_name` and
  `token_symbol`, are the ones the entity list was widened for in step 2.
- Amounts arrive as decimal strings and stay integers. No `float` appears
  anywhere in the adapter, asserted across every record of every fixture.
- A GraphQL `errors` payload raises. That one matters: a subgraph answering
  HTTP 200 with an error block would otherwise read as a borrower with no
  history, which is the same shape as a clean record.
- An unexpected response shape raises through six separate mutations of a
  fixture: a dropped field, a dropped collection, a hash that is not a hash, an
  amount that is not a number, `markets` as an object, and a market belonging
  to someone else.
- Reading a fixture does not mutate it, so a test cannot pass because an
  earlier one moved the ground.
- The suite makes no network request. Every CLI test now passes `--fixtures`,
  which was a fix in the implementation itself: a test that quietly makes a
  live request passes on a laptop, fails in CI behind a proxy, and tells you
  nothing either way.

Leads not pursued: a withdrawal batch that expired with no expiry event indexed
is cited to the transaction that created the market. That transaction did not
cause the expiry, so the citation identifies the market rather than the event.
Dropping the finding would hide it and reporting it uncited would break gate 3,
so it stays, and the reference in step 4 will say plainly what that citation
points at.

## Step 3, round 2 -- 2026-08-15

Reviewed: the round 1 fixes for regressions, then the adapter again with the
divergence risk in mind.

The `for ... else` on both pagination loops raises only when the loop finishes
without breaking, which is what was wanted. `build_opener` replaces the default
redirect handler because `_NoRedirects` subclasses it, so the refusal is real
rather than an unused class. Neither fix changed what the fixtures produce.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | medium | scripts/probitas_lib/adapters/wildcat.py | `marketClosedEvent` and a batch's `expiration` were read with `.get`, so a renamed field would read as "no such event" rather than raising. Every closed market would silently report as still open, and every unpaid expired batch would lose its citation. This is the divergence the issue says has to raise, and it did not. | fixed in f04e478 |
| S3-R2-02 | low | scripts/probitas_lib/adapters/wildcat.py | Validating the market id raised `ValueError` while every other refusal in the adapter raised `WildcatShapeError`, so a caller had to know which layer complained. | fixed in f04e478 |
| S3-R2-03 | low | scripts/probitas_lib/adapters/wildcat.py | The fixture directory name went into the coverage row unsanitised. It is operator input, but the operator may be pasting, and a directory named with a pipe breaks the table cell it lands in. | fixed in f04e478 |

Checked and clean:

- The pagination ceiling is 200 pages of 100, so twenty thousand markets before
  it gives up, and it gives up loudly.
- A redirect raises before any body is read, so a moved endpoint cannot answer
  as though it were the one that was asked.
- Sorting delinquency records changed nothing for the fixtures, which were
  already ordered, and the out-of-order test proves the sort is doing work.
- The repeated-entry test holds the understating direction still: three records
  with two entries and one cure report six days, not one.

Leads not pursued: none new. The withdrawal batch citation from round 1 stands
as recorded.

## Step 3, round 3 -- 2026-08-15

Reviewed: the adapter with both rounds applied, under a mutation sweep. Every
key in all three fixtures dropped in turn, then every scalar corrupted in turn,
asking each time whether the adapter raised or quietly produced a different
record set. 1,266 mutations. Fourteen changed the output without raising.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R3-01 | high | scripts/probitas_lib/adapters/wildcat.py | Every flag was read with `bool()`, which is true for any non-empty value the venue might send. A field turning from `false` into a string made a healthy market report as delinquent, a cure report as an entry, and, worst of the set, a withdrawal batch that expired unpaid report as settled and drop out of the dossier entirely. Eight of the fourteen silent mutations were this one bug. | fixed in be54fdd |

The remaining six are `name` and `asset.symbol` on each fixture. Both are free
text, so a changed name changing the record is the adapter working. They are
listed here so the count is accounted for rather than rounded down.

After the fix the sweep reports six, all of them those two fields.

Checked and clean:

- Dropping any key raises. Corrupting any integer, hash, address or flag
  raises. Nothing in the response can now make a finding disappear without
  the run failing first.
- The 121 tests still pass, including the three fixtures' expected record
  counts, so the guard did not tighten past what real data does.

Leads not pursued: none.

## Step 3, round 4 -- 2026-08-15

Reviewed: the adapter with all three rounds applied, and the round 3 fix for
regressions.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Nothing found. Checked this round:

- The mutation sweep now reports six silent changes, all of them a market name
  or a token symbol, both free text where a changed name changing the record
  is the adapter working rather than failing.
- The live run against mainnet still returns 22 records across three real
  markets for a real borrower, every one carrying a transaction hash, with the
  coverage row naming the endpoint and the block range from the arch
  controller deployment. The boolean guard did not tighten past what the
  subgraph actually sends.
- 18 Python files, none using syntax newer than 3.9.
- Two runs over the same fixture produce byte-identical output.
- 123 tests, all passing.

Leads not pursued: the withdrawal batch citation recorded under round 1 stays
as it is, and the reference in step 4 will say what that citation points at.
Nothing else is open.

## Step 4, round 1 -- 2026-08-15

Reviewed: `59690d0`. The template, the renderer, the formatting helpers and the
five gates. The gates are the security surface of the whole tool, so this round
attacked them rather than read them: every way of writing a figure so a sieve
does not see it, and every way of satisfying a gate on the evidence while the
document says something else.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | high | scripts/probitas_lib/formatting.py | A figure grouped with spaces walked past the sieve entirely. `9 000 000` split into three fragments, none of them four digits, so an invented amount written that way passed gate 3 without a mark. | fixed in 61a8444 |
| S4-R1-02 | high | scripts/probitas_lib/formatting.py | A hash or address written without its `0x` was invisible for the same reason: not all digits, no prefix to recognise. Sixty-four hex characters passed as prose. | fixed in 61a8444 |
| S4-R1-03 | high | scripts/probitas_lib/gates.py | Gate 2 checked the evidence and only that the document had a Coverage heading. Deleting a row from the rendered table passed, because the file the reader never sees was still complete. | fixed in 61a8444 |
| S4-R1-04 | high | scripts/probitas_lib/gates.py | Gate 4 checked that the negative space section was non-empty, not that it said anything. Replacing the gaps table with "Nothing of note" passed while nine venues went unmentioned. | fixed in 61a8444 |
| S4-R1-05 | medium | scripts/probitas_lib/gates.py | Gate 1 tracked addresses and not findings. A row moved out of the inferred section took its citation with it and read as part of the record, with no address on the line to catch it. | fixed in 61a8444 |

Four of the five are the same mistake in different clothes: checking the
evidence rather than the document. The evidence is generated by code that
cannot lie; the document is written by a model. Gates that only read the
evidence are gates pointed the wrong way.

The sieve now runs three passes: word boundaries, then numbers grouped with
spaces, then bare hex. It fails closed on formatting it did not produce, so a
correct figure regrouped by hand fails too. That is deliberate and now written
into the reference: teaching it every way to group a thousand is how the spaced
evasion gets back in.

Checked and clean:

- Digits from another script fail rather than pass. Arabic-Indic numerals
  satisfy `str.isdigit`, so they become tokens, and a token that is not in the
  evidence fails. The safe direction.
- Prose carrying no figures passes untouched, which is the point: the gate
  checks assertions of fact rather than tone.
- Rendering is byte-identical across runs, and a market name carrying escaped
  Markdown cannot add a cell to its table row.
- Amounts scale by token decimals through integer arithmetic. No float appears
  anywhere in the formatting path, and one wei of an 18-decimal token still
  prints exactly.
- Gate 5 does not fire on the shipped template, asserted directly, so the one
  document every run produces cannot trip its own check.
- The skipped test in this round's first pass is gone. It skipped because the
  fixture produced no inferred findings, which meant the strongest gate 1 case
  was never exercised; it now builds a record against an undeclared address and
  runs for real.

Leads not pursued: a figure written in words, "nine million rather than
9,000,000", passes the sieve. Catching it means parsing English numerals and
then deciding what they refer to, which is a different tool. The gate checks
figures; a claim in words is the operator's to check, and the reference says
so rather than leaving it implied.

## Step 4, round 2 -- 2026-08-15

Reviewed: the round 1 fixes, then the gates against a forgery sweep and against
live mainnet data.

The sweep applies 23 tamperings a model could plausibly make to a document
between `render` and `verify`: inventing a hash prefixed, bare and uppercase;
inventing a market, a block number and a date; an amount invented, rounded,
shifted by a decimal place, grouped with spaces and grouped with underscores; a
citation altered by one character; the gaps replaced with a denial; the
negative space heading renamed; the summary hoisted above it; a coverage row
deleted; every unimplemented row deleted; five shapes of rating; and a link to a
document no record mentions. All 23 caught. Six benign documents, including
prose with no figures, prose naming small numbers, a denial of rating and a
figure quoted exactly as rendered, all pass. No false alarms.

Then the whole pipeline against a real mainnet borrower with 18-decimal tokens,
which the fixtures do not cover. 22 records, three markets, two real
delinquencies, one cured inside the grace period and one that ran past it. All
five gates pass, and tampering with a real 18-decimal amount is caught.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R2-01 | low | scripts/probitas_lib/gates.py | Round 1's gate 2 fix looked for each venue anywhere in the Coverage section. A venue named in another venue's note would stand in for its own missing row. No note currently names another venue, so the hole was latent rather than open, but notes change. | fixed in 498ae55 |
| S4-R2-02 | low | scripts/probitas_lib/render.py | `load` checked that each block was present, not that it was a list. An evidence file with `records` as an object would fail somewhere further in with an error about neither records nor evidence. | fixed in 498ae55 |

Gate 2 is now anchored to the first cell of a table row rather than to a
substring of the section.

Checked for regressions from round 1:

- The three-pass sieve agrees with itself on live data. An 18-decimal amount
  renders as `901,881.630000000000000000`, which the bare-hex pass sees as an
  18-character hex run, and the checker derives the same token from the raw
  value because both sides call the same helpers.
- Gate 1 following findings rather than addresses did not start firing on
  ordinary documents: the citation search is over shortened forms, which are
  what the renderer prints.
- Gate 4 requiring every gap to be named did not break the empty fixture, where
  the gaps are the eight venues with no adapter.

Leads not pursued: a figure written in words still passes, as recorded in round
1. A bare URL in prose is sieved for figures but not checked against the record
sources, since only Markdown links are parsed; writing a naked URL into a
dossier is not a thing the renderer does and the figures inside it are still
caught.

## Step 4, round 3 -- 2026-08-15

Reviewed: the tree with both rounds applied, and the round 2 fixes for
regressions.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Nothing found. Checked this round:

- The forgery sweep still catches all 23 tamperings and still raises no false
  alarm on the six benign documents. Anchoring gate 2 to a table row did not
  cost it anything.
- The step 3 mutation sweep still reports six silent changes, all of them a
  market name or token symbol, unchanged by anything in this step.
- The live pipeline runs clean end to end, and rendering the same live evidence
  twice gives identical bytes.
- 23 Python files, none using syntax newer than 3.9.
- No test in the suite opens a socket. Every network call is mocked at the
  opener and every adapter test reads a fixture.
- 183 tests, all passing, none skipped.

Leads not pursued: the two recorded in earlier rounds stand. A figure written
in words passes the sieve, and a bare URL in prose is sieved for figures but
not matched against record sources. Both are written down in the gates
reference rather than left for a reader to discover.

## Step 4, after the audit closed -- 2026-08-15

The review for this step had already closed on round 3 when CI failed on
Python 3.9, having passed locally on 3.14. So this fix arrived after the fact
and is not numbered as a round: three rounds ran and three is what the list
above says. Recorded because the fix is real and the reason for it is worth
keeping.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R4-01 | low | plugins/probitas/tests/test_graphql.py | Round 2 silenced a `ResourceWarning` by closing a mocked `HTTPError`. On Python 3.9 an `HTTPError` built with no file object raises `KeyError` when closed, so the fix broke the oldest interpreter the README claims to support while passing on the newest. | fixed in 2bc32fc |

The error now carries a real empty file object, which closes cleanly on both.
The suite also passes with `-W error::ResourceWarning`, so the warning is gone
rather than hidden.

This is the version matrix earning its keep. It went in as step 1 round 2 on
the argument that an untested compatibility claim is a claim that quietly stops
being true, and this is the first time it caught one.

It also says something about round ordering: an audit that closes before CI has
run on every supported interpreter closes early. Worth waiting for the matrix
before the last round in future steps.

## Step 5, round 1 -- 2026-08-15

Reviewed: `68676c9`. The Morpho Blue adapter, four fixtures, the demo path and
the registry additions. Same treatment as step 3: read the code, then run a
mutation sweep over every key in every fixture, dropping each in turn and
corrupting each in turn.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R1-01 | high | scripts/probitas_lib/adapters/morpho.py | An unrecognised transaction type was skipped in silence. If Morpho renamed `Borrow`, every borrow record would vanish, the coverage row would read `empty`, and a borrower with a history would present as one with none. This is the divergence failure the Wildcat adapter was built to avoid, reintroduced here. Six of the fourteen silent mutations were this one bug. | fixed in 9d961da |
| S5-R1-02 | high | scripts/probitas_lib/adapters/morpho.py | `repaidAssets` is denominated in the loan asset and `seizedAssets` in the collateral asset, and the two have different decimals. Both were filed under one `token_decimals`, so anyone scaling the seizure by it got a figure wrong by up to twelve orders of magnitude. Confirmed against live data: a real liquidation repaid USDC at six decimals and seized sNUSD at eighteen. | fixed in 9d961da |
| S5-R1-03 | medium | scripts/probitas_lib/adapters/morpho.py | The adapter queries mainnet only, and the coverage note did not say so. Morpho runs on other chains, so a reader could take a clean Morpho row as covering all of them. | fixed in 9d961da |

The first fix distinguishes a type the adapter ignores on purpose from one it
has never seen. `Supply`, `Withdraw`, `SupplyCollateral` and
`WithdrawCollateral` are listed and skipped, because lending money says nothing
about whether someone repays what they take. Anything in neither table raises.

The second now reads `collateralAsset` alongside `loanAsset` and keeps the two
scales apart, with the seizure renamed to `seized_collateral` so nothing about
the field invites the wrong division. A market with no collateral asset still
records the seizure, without decimals, rather than dropping it.

After the fixes the sweep reports eight silent changes, all of them a loan or
collateral symbol, where a changed name changing the record is the adapter
working.

Checked and clean:

- Every record from all three fixtures carries a transaction hash.
- A float amount raises rather than being rounded. The API returns some amounts
  as JSON numbers and others as strings, and `int(1.5)` is 1 without complaint,
  which is how a wrong figure gets a citation attached to it.
- A liquidation is recorded as a liquidation and never as a default or a
  delinquency, with the record stating that the position was collateralised.
  Bad debt gets its own record, cited to the same transaction.
- A transaction for an address the operator did not ask about raises rather
  than being reported.
- A borrower with no Morpho activity yields `empty`, not `error`.
- Adding this venue touched `adapters/`, the registry, the CLI adapter table
  and its own tests. The evidence model, the gates and the graphql client are
  untouched, which is the answer to whether the interface was worth having.

Leads not pursued: the registry gained MetaMorpho, Morpho Vaults V2 and Morpho
Midnight during this step, all unimplemented. That is not a finding but it is
worth recording why they went in: a coverage row reading `morpho-blue checked`
would otherwise imply Morpho was checked, when three further surfaces on that
protocol were not. Written up as issue 16.

## Step 5, round 2 -- 2026-08-15

Reviewed: the round 1 fixes for regressions, then both adapters side by side,
which is what a second venue makes possible.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R2-01 | medium | scripts/probitas_lib/adapters/wildcat.py | Round 1 made the Morpho coverage row say `ethereum mainnet only` and left the Wildcat row saying nothing about its chain. Wildcat is deployed on Plasma as well as mainnet, the adapter queries one of them, and a row reading `checked` invites a reader to take it for both. The fix that landed for one venue was needed for the other. | fixed in 02eca61 |

Regenerating the committed example dossier was part of this: the demo test
compares it against a fresh run, so a coverage note changing anywhere makes it
stale and the suite says so rather than letting the shipped example drift.

Checked for regressions from round 1:

- Raising on an unknown transaction type did not catch the four types the
  adapter ignores on purpose. Both directions are tested.
- Separating the loan and collateral scales did not break a market with no
  collateral asset, which still records the seizure and simply carries no
  decimals for it.
- A live run over two real borrowers across both venues returns 24 records, 22
  from Wildcat and two from Morpho, with all five gates passing.
- The forgery sweep from step 4 still catches all 23 tamperings with no false
  alarm, so nothing in this step weakened the gates.
- 26 Python files, none using syntax newer than 3.9.

Leads not pursued: none.

## Step 5, round 3 -- 2026-08-15

Reviewed: the tree with both rounds applied, with the CI matrix run first this
time rather than after the close. That is the correction step 4 called for: an
audit that closes before the oldest supported interpreter has seen the code
closes early, and step 4 found that out the expensive way.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Nothing found. Checked this round:

- CI green on Python 3.9 and 3.13 before this round rather than after it.
- 217 tests, all passing, none skipped, and the suite is clean under
  `-W error::ResourceWarning`.
- The Morpho mutation sweep reports eight silent changes, all of them a loan or
  collateral symbol. The step 3 Wildcat sweep still reports six, all of them a
  market name or token symbol. Both are free text where a changed name changing
  the record is the adapter working.
- The step 4 forgery sweep still catches all 23 tamperings with no false alarm,
  so two new venues and three new registry entries moved nothing in the gates.
- The committed example dossier passes all five gates and matches what the demo
  path produces, asserted by the suite rather than by having looked once.

Leads not pursued: the ones recorded in earlier steps stand. A figure written
in words passes the gate 3 sieve; a bare URL in prose is sieved for figures but
not matched against record sources; and the Wildcat withdrawal batch with no
indexed expiry is cited to the transaction that created the market. All three
are written into the gates reference rather than left for a reader to find.

## Venue research, after the build finished -- 2026-08-15

Follow-on work after the build finished, probing the four venues the registry
had down as "not yet probed", plus Aave v4, and writing the findings up for a
general reader.

Reviewed: the registry rewrite and the contributor guide. No code changed
beyond the registry table, so the only live concern is coverage misreporting.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| VR-01 | medium | scripts/probitas_lib/registry.py | Aave v3 was recorded as needing a paid Graph gateway key. It does not: `api.aave.com/graphql` answers keyless with `userBorrows` and `userPositions`. The registry was telling every dossier a venue was out of reach when it was one adapter away. | fixed |
| VR-02 | low | scripts/probitas_lib/registry.py | Four venues carried the note "Not yet probed", which is honest but useless to a reader deciding what to do about them. All four now carry what a live request actually returned. | fixed |
| VR-03 | low | scripts/probitas_lib/registry.py | Aave v4 has been live on Ethereum mainnet since March 2026 and had no entry, so a dossier covering an Aave borrower would have been silently version-blind. | fixed |

Every claim in the rewritten registry and in `docs/adding-a-venue.md` came from
a request made during this pass, not from documentation:

- `api.aave.com/graphql` returned `{"chains":[{"chainId":1,"name":"Ethereum"}]}`
  and named `userBorrows`, `userSupplies`, `userPositions`, `borrow` and
  `assetBorrowHistory` in its errors.
- `api.centrifuge.io` introspected to 90-odd query fields and returned three of
  24 mainnet pools.
- `api.clearpool.finance` returned a 403 bot challenge. Not worked around, and
  the guide says plainly that it will not be.
- `api.goldfinch.finance` does not resolve; `api.truefi.io` resolves and does
  not answer.
- `api.thegraph.com` returns 301 for all four hosted-service paths, confirming
  the route is gone rather than moved.

Protocol status came from public reporting rather than from an endpoint, and is
attributed as such in the guide: Goldfinch winding down in June 2026, TrueFi's
token migration completing in May 2026, and Aave v4's mainnet launch in March
2026.

Checked and clean:

- 217 tests still pass. The registry grew from 12 entries to 13 and the
  coverage counts moved with it, which the CLI tests assert directly.
- Every relative link in every Markdown file under the plugin resolves.
- The committed example dossier was regenerated, since a coverage table with a
  new row makes it stale, and the demo test compares the two.
- No endpoint, key or hostname belonging to Wildcat appears anywhere in the
  tree. The archive node discussed in issue 12 is named nowhere in the code.

Leads not pursued: none. The Aave request shape was left unestablished on a
first pass and then established properly, which is the better outcome and took
reading the published schema rather than guessing at it. `aave/aave-v4-sdk`
carries the whole thing at `packages/graphql/schema.graphql`. The working
`activities` query is in the guide, verified against a live borrow returning an
exact on-chain integer and a transaction hash, so the next person writing that
adapter starts from a query rather than from a hunch.

## Editorial pass over the merged tree -- 2026-08-15

An editorial pass over the whole of the shipped prose at once, which became
possible only once every branch was merged and the documents could be read as
one set rather than five.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| PP-01 | medium | README.md | Two contradictory miscounts. The venue section said "the other ten" and, nine lines later, "four of the eleven gaps", where the true figures are eleven and six. A README that miscounts its own coverage is poor advertising for a tool whose case rests on counting coverage honestly. | fixed |
| PP-02 | medium | README.md | The quickstart ran against `tests/fixtures/defaulted` while claiming, two paragraphs above, to produce the committed example dossier. The example comes from `tests/fixtures/demo`. Anyone following the README got a different document from the one it showed them. | fixed |
| PP-03 | low | README.md | "Drop `--fixtures` to run against the live Wildcat subgraph" was written when Wildcat was the only adapter. There are two now. | fixed |
| PP-04 | low | README.md, references/venues.md | Two venues were named differently from their registry display names, so a reader grepping for what `probitas venues` printed would miss them. | fixed |
| PP-05 | low | docs/study.md, docs/runbook.md | Both read as descriptions of the tool when they are the plan written before any code existed, and both contain decisions the build later reversed. A reader landing on `docs/` had no way to tell. | superseded; both deleted, see below |

The counts are now checked rather than asserted in prose. `tests/test_docs.py`
derives them from the registry and fails if the README, the venues reference or
the contributor guide disagrees, and it also fails if the README's quickstart
names a fixture other than the one the committed example was built from. Ten
tests, and they are the reason PP-01 through PP-04 cannot come back.

The plan documents were marked rather than rewritten, on the argument that a
record of what was believed at the start is worth keeping. That call was
overruled and they are gone. See the entry below.

Also done, with no finding attached:

- Verbatim repetition across the shipped documents went from four shared
  sentences to none. Each document is entered on its own, so the facts stay in
  all of them, said in each document's own voice rather than pasted.
- The README was restructured to put running the thing above explaining it. It
  previously buried the commands under a heading called Status.
- A test now walks the whole plugin tree for internal endpoints and credential
  patterns, since this directory is bound for a public repository. Its needles
  are assembled at runtime so they appear in no file, including its own, which
  means nothing is exempt from the scan.

Leads not pursued: none. The two plan documents were deleted in the pass below
rather than left marked.

## Deleting the plan documents -- 2026-08-15

The pass above kept `docs/study.md` and
`docs/runbook.md` with a note saying they were the plan rather than the
outcome. That was the wrong call and it was overruled: both are deleted.

The argument for keeping them was archaeological, and archaeology is not what
`docs/` is for. Someone opening that directory wants to know what the tool does
now. A document that describes a nine-venue registry, an Aave that cannot be
reached and test counts the build overtook is not made safe by a banner
admitting as much; it is a wrong document with a disclaimer, and a reader who
skims the banner is worse off than one who never found the file. Git has the
history if anyone genuinely wants what the plan said.

The risk register that lived in the study was briefly rescued into this file
and then cut as well, for the same reason: it described what someone expected
to go wrong before anything existed, and this log records what actually did.
The concerns it named survive where they belong, written into the rounds that
acted on them.

`docs/` now holds the contributor guide and the example dossier, both of which
describe the tool as it stands.

The same cut then reached this file. The risk register had been rescued to the
top of it and was removed on the second pass, because it described what someone
expected to go wrong before any code existed and this log records what actually
did. Round entries that referred to its items by number now name the concern
instead, so a reader does not need a numbered list to follow them.

This file was rewritten to be read cold at the same time. It previously assumed
a reader knew the delivery process that produced it, naming that process's
machinery in passing as though everyone had the same. None of that helps
someone auditing the plugin. What survives is what was reviewed, what was
found, and what was done about it.

Leads not pursued: none.

## The README again -- 2026-08-15

The editorial pass two entries above fixed four factual errors in the README
and added tests to hold the venue counts still. It did not look at whether the
rest of the page still described the tool, and it did not.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| RM-01 | medium | README.md | The quickstart gave no working directory. Its commands are relative to `plugins/probitas` while the test command below them says "from the repository root", so a reader working down the page hit an error on the first block. | fixed |
| RM-02 | medium | README.md | "Three synthetic borrowers ship" was written when Wildcat was the only adapter. Nine ship, four of them for Morpho, and the two Morpho liquidations are the pair that keeps the distinction between a covered liquidation and one that cost somebody money. | fixed |
| RM-03 | medium | README.md | `--inferred` was undocumented. The page explains gate 1 and the separation of declared from inferred addresses, and never showed how to supply one, so a reader could not exercise the feature the gate exists for. | fixed |
| RM-04 | low | README.md | `verify` was described as exiting 0 without saying it exits 1 and names the gate on a breach, which is the exit code anyone wiring this into anything would want. | fixed |

The pattern is the same one as last time. A page edited in place across five
steps keeps whatever was true when each paragraph was written, and nothing
notices, because prose has no compiler. Counts were fixed last time and the
surface drifted this time.

So the surface is now checked too. Four more tests derive the subcommands and
the `collect` flags from the argument parser, count the fixture directories on
disk, and require the working directory to be stated. Each was confirmed to
bite by breaking the README four ways and watching the suite fail each time.

That is eight assertions over a README, which is more than most projects would
want. It is proportionate here: this plugin's whole claim is that it does not
let a document drift from the facts underneath it, and a README making a claim
its own tests do not check would be the wrong advertisement for that.

Leads not pursued: none.

## The description was too narrow -- 2026-08-15

Every copy of the one-line description said this was a dossier for
undercollateralised lending. It reads two venues, one of which is
overcollateralised, and nine of the eleven it cannot read yet are
overcollateralised too.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| DS-01 | medium | specs/probitas.md, README.md, both plugin manifests, marketplace entry, openai.yaml, docs/adding-a-venue.md | The description conflated who you would run this on with what it reads. Undercollateralised lending is the reason to want the tool; the coverage is wherever the counterparty borrowed, most of which is collateralised. Anyone reading the manifest would have concluded it did not apply to them. | fixed |
| DS-02 | low | specs/probitas.md | The specification still said "unbuilt spec" months after it was built. | fixed |
| DS-03 | low | README.md (repository root) | The table row described probitas as an idea rather than as something shipped, and did not link to it. | fixed |

The distinction is now stated rather than left implicit, in the specification
and in the plugin README both. The motive is our own exposure and the coverage
is wider than the motive, and an overcollateralised venue still says plenty: a
liquidation says a price moved, a bad debt says somebody was not made whole,
and a missed maturity says what it says anywhere.

Three tests hold the six copies together. They assert that the short
description is identical across the Codex interface block, the marketplace
entry and the agent metadata, that both plugin manifests describe the plugin
the same way, and that the narrow phrasing does not come back. Six copies of a
sentence is five opportunities for one of them to rot.

Leads not pursued: the three sibling specifications in `specs/` still say
"unbuilt spec", which is true of all three.

## Portable entrypoints and the shared plugin shape -- 2026-08-15

Applying the layout that `wildcat-finance/skills` adopted for Hermes and
Hexaemeron, so probitas can move into that repository without being reshaped
on the way, and so an agent that has learned one plugin here has learned all
of them.

Nothing about the tool changed. What changed is how an agent finds it and what
it is told before it runs.

Added:

- `AGENTS.md` at the repository root: what the repository holds, how to load a
  skill, and the rule that anything added to `plugins/` carries the same set of
  files. That rule is the point of this pass rather than a side effect.
- `.agents/skills/probitas/SKILL.md`: a host-neutral entrypoint that routes to
  the runtime contract instead of restating it, for agents implementing the
  Agent Skills discovery convention.
- `plugins/probitas/AGENTS.md`: the selection table, a mapping from host tool
  names to capabilities, how the placeholders resolve, what the network side
  effects are, and what the skill refuses to do.
- `plugins/probitas/skills/probitas/README.md`: a copy of the `SKILL.md` beside
  it, so the directory renders when browsed.
- A `Day to day` section in the skill, and a desk score table in the repository
  README.

The scoring rule is the marketplace repository's: out of ten per desk for doing
the job rather than reading the output, and five is the barrier. At or above
it a desk gets a worked example; below it none, because there is no honest one
to give. Probitas scores 9 for business development, 7 for finance and 5 for
security and audit, so three desks get examples. Marketing gets 1 and gets
nothing, which is the correct outcome rather than a gap.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| PE-01 | low | plugins/probitas/skills/probitas/README.md | A copy of a file beside the original is a drift risk by construction. A shadow that has fallen behind is worse than no shadow, because a reader has no way to tell which of the two is current. | fixed |

Ten tests hold the shape. They check that the portable entrypoint's name
matches its directory and its links resolve, that the runtime contract points
at skills that exist, that the shadow is byte-identical to its `SKILL.md`, that
every plugin directory has both a contract and an entrypoint, that both
marketplace manifests list the same plugins, and that a desk scoring five or
more has an example while one scoring less does not.

Confirmed to bite rather than assumed: the shadow was drifted by a word, a
below-barrier desk was given an example, the entrypoint name was changed away
from its directory, and the contract was pointed at a skill that does not
exist. The suite failed on all four.

Leads not pursued: none.
