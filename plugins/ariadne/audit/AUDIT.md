# Ariadne audit log

<!-- marketplace-context:start -->
> **Record status.** This is a historical audit record; findings and dispositions below are preserved as evidence. Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** Dataset, state-fixture and grounded-agent predicates are specified but not implemented.
<!-- marketplace-context:end -->

One section per round. A round with no findings is still a round and still gets
written down.

The Pashov suite (`x-ray`, `solidity-auditor`, `fizz`) is waived for this
build and the waiver is on the run's ledger: ariadne ships Python, and the only
Solidity in the repository will be a fixture contract compiled to produce test
material. The waiver covers why those tools did not run. It does not cover
skipping the look, so each round is a review of the step's diff against the
risks listed in [`docs/design.md`](../docs/design.md).

## Step 1, round 1 -- 2026-08-16

Reviewed: the whole of `scripts/ariadne_lib/` and `scripts/ariadne.py` as
introduced by commit `0c5270d`, against risks 1 to 4 and 8 of the register
(canonicalisation, base64 variance, digest confusion, gate bypass by omission,
untrusted JSON).

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `scripts/ariadne_lib/digests.py` | `agree` returned true when the only algorithm two digest sets shared was an unsupported one, so a subject match could rest on sha1 alone while sha256 and sha512 never met | fixed in this round: agreement now requires a shared supported algorithm, and any shared algorithm that disagrees still sinks the match |
| S1-R1-02 | medium | `scripts/ariadne.py` | JSON nested deeply enough to exhaust the stack raised `RecursionError` out of `inspect`, printing a traceback and exiting 1, the code reserved for a breached gate | fixed in this round: the parsers catch it and refuse the input, so it exits 2 |
| S1-R1-03 | low | `scripts/ariadne_lib/digests.py` | `of_tree` read anything `os.walk` listed as a file, so a fifo in a source tree would block the read until something wrote to it | fixed in this round: anything that is not a regular file is refused, in the same spirit as the existing symlink refusal |
| S1-R1-04 | low | `scripts/ariadne_lib/envelope.py` | `read` dispatched on the presence of `payload`, so an envelope missing `payloadType` was read as a statement and told its `_type` was absent | fixed in this round: dispatch is on `_type`, and each shape gets its own message |

Checked and found sound:

- Base64 leniency (risk 2). Python 3.9 and 3.14 both refuse excess data after
  padding and both refuse embedded whitespace, so the decoder does not accept
  strings a Go verifier would reject. Verified by running the cases on both.
- Payload preservation (risk 1). The bytes decoded from an envelope are kept
  and never re-serialised, asserted by `test_payload_bytes_survive_a_read_unchanged`.
- Signature wording (risk 10). `test_no_signature_state_claims_an_author_or_a_verification`
  asserts no state string contains a word implying a check that did not happen.

Leads not pursued:

- **Input size cap.** `inspect` reads a whole file into memory with no bound. A
  cap belongs with the other untrusted-input bounds in step 2, which owns
  `verify` and its depth, size and duplicate-key refusals. Left open
  deliberately rather than half-built here.
- **Canonical base64.** Requiring the payload string to be the exact canonical
  encoding of its bytes would catch a class of encoder disagreement, and would
  also reject the unpadded form DSSE permits. Considered and rejected:
  accepting both alphabets and optional padding is the documented behaviour,
  and the bytes are what get checked.
- **Empty directories in a tree digest.** Two trees differing only by an empty
  directory digest the same. It changes no compilation input, and the fix
  would be a listing format nobody else reads.

## Step 1, round 2 -- 2026-08-16

Reviewed: the same tree with round 1's fixes applied, looking first for
regressions those fixes could have introduced and then at what the first pass
did not cover. The four fixes hold: `agree` still matches on a shared supported
algorithm, the non-regular-file refusal does not touch an ordinary build tree,
and dispatch on `_type` reaches the envelope path for every envelope.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | `scripts/ariadne_lib/statement.py` | A statement carrying fields Statement v1 does not define was accepted, and this tool showed only the fields it knew. A `predicate_type` beside the real `predicateType`, or any other planted field, would read one way here and another way in a consumer that looked at it | fixed in this round: unknown top-level fields are refused by name |
| S1-R2-02 | medium | `scripts/ariadne_lib/statement.py` | A subject's `uri`, `mediaType` and `annotations` were parsed and then dropped, so re-emitting a subject produced a different document from the signed one | fixed in this round: descriptor fields are carried through, and a field outside the ResourceDescriptor shape is refused |
| S1-R2-03 | low | `scripts/ariadne_lib/envelope.py` | Envelope and signature objects accepted undefined fields, so material a producer meant as part of the envelope could sit there unread | fixed in this round: both shapes refuse fields DSSE does not define |
| S1-R2-04 | low | `scripts/ariadne_lib/envelope.py` | A document that was neither shape got whichever error came first rather than being told it was neither | fixed in this round |

Leads not pursued:

- **Refusing undefined fields may cost interoperability.** A producer that adds
  a field to the envelope now gets a refusal rather than a shrug. Taken
  deliberately: this tool exists to refuse documents that look fine and are
  not, and relaxing it later is one line. Recorded here so the choice is
  visible if a real producer trips over it.
- **Duplicate JSON keys.** `json.loads` keeps the last value for a repeated
  key, so a document with two `predicateType` entries parses as one. The
  refusal belongs with the other untrusted-input bounds in step 2, and is
  listed in that step's exit conditions.

## Step 1, round 3 -- 2026-08-16

Reviewed: the tree with rounds 1 and 2 applied. The unknown-field refusals hold
and round-trip a descriptor's other fields unchanged. This round looked at what
happens when the filesystem refuses, which the first two passes did not.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | `scripts/ariadne_lib/digests.py` | `os.walk` drops directories it cannot read and reports nothing, so a tree digest over a partly unreadable tree succeeded while covering less than the caller believed. Silent absence, in the one place the whole project is about not having any | fixed in this round: an unreadable directory raises rather than being skipped |
| S1-R3-02 | low | `scripts/ariadne_lib/digests.py` | `of_file` let an `OSError` escape, so a caller catching `DigestError` around a digest would not catch an unreadable file | fixed in this round |

Leads not pursued: none. The remaining open items are the two carried from
round 1 and round 2, both belonging to step 2's untrusted-input bounds.

## Step 1, round 4 -- 2026-08-16

Reviewed: the code once more against the register, then the shipped prose
against the code. In a project whose subject is not overclaiming, a document
describing a capability the code does not have is the same defect as a gate
that does not fire.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | low | `AGENTS.md` | The runtime contract said the tool writes only where `--out` points. No subcommand at this version writes anything, and no `--out` exists | fixed in this round: it says the tool writes nothing yet, and what will hold when a writing subcommand arrives |
| S1-R4-02 | low | `skills/ariadne/SKILL.md` | The exit-code line offered 1 for a breached gate without saying that no subcommand here can return it, since the gates arrive with the verifier | fixed in this round |

Register items with nothing to review yet, named so the coverage is legible:
gate bypass by omission (the gates land in step 2), replay as code execution
(step 5), capture reading outside the project and secrets in statements (step
4), and missing-baseline degradation (step 3).

Leads not pursued: none.

## Step 1, round 5 -- 2026-08-16

Reviewed: the step's whole diff with all twelve fixes applied. Re-read
`digests.py`, `statement.py`, `envelope.py`, `registry.py` and `ariadne.py` end
to end looking for regressions the fixes could have introduced, and re-ran
every suite on Python 3.9 and 3.14: 87 plugin tests, 9 repository contract
tests, and probitas's 422 to confirm nothing here disturbed it.

No findings.

One observation short of a finding, recorded rather than fixed: `Statement` and
`Subject` validate what arrives through `from_dict` and trust what a caller
passes to the constructor directly. Every path into them from outside this
plugin goes through `from_dict`, and a type check on an internal constructor
would be ceremony.

Leads not pursued: the two carried items, an input size cap and a
duplicate-key refusal, both of which step 2 owns and names in its exit
conditions.

## Step 2, round 1 -- 2026-08-16

Reviewed: `gates.py`, `verify.py`, `core_predicate.py` and `safejson.py`, from
the position of a producer who wants a statement that passes while hiding
something. The two carried items from step 1 are closed by this step's bounds.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `scripts/ariadne_lib/verify.py` | A registered predicate type suppressed the line saying gates 2 and 5 went unchecked, while nothing ran them. Registering a module was enough to make two gates disappear from the report, which is the exact silence gate 3 exists to refuse | fixed in this round: a predicate contributes by exposing `check(statement)`, its gates are run and reported, and a module without one is named as registered but exposing no checks |
| S2-R1-02 | low | `scripts/ariadne_lib/gates.py` | Gates 4 and 7 scan keys, and nothing said so. A reader could take a clean run as covering the prose in a `reason` string | fixed in this round: the limit is stated in the gate and in `docs/conformance.md`, beside what the check does buy |
| S2-R1-03 | low | `scripts/ariadne_lib/safejson.py` | `--max-bytes 0` refused every document with a message about a cap, rather than about the caller's own argument | fixed in this round: non-positive bounds are refused by name |

Checked and found sound:

- The key walk reaches dictionaries nested inside lists inside dictionaries, so
  a verdict key cannot hide one level down. Asserted in `test_gates.py`.
- The depth counter reads bytes and ignores brackets inside strings, including
  after an escaped quote, so a document cannot smuggle depth past it in a
  string literal.
- The size cap is applied to the file on disk and again to the bytes read, so
  a file that grows between the two checks is refused rather than read.
- The bounds apply to the payload inside an envelope as well as to the envelope,
  since both arrived from the same stranger.

Leads not pursued:

- **Homoglyph keys.** `normalise_key` folds case and separators but not
  scripts, so a key spelling `safe` with a Cyrillic character passes gate 4.
  Considered and left: the gate refuses the shapes that let a careless
  statement read as a careful one, and a producer willing to build a homoglyph
  key could simply omit the verdict instead. Worth revisiting if a real
  producer ever trips it.
- **One subject standing in for another.** In a statement with several
  subjects, gate 1 cannot tell that a claim about one names the digest of
  another. Recorded in `docs/conformance.md` under what the gates do not catch.

## Step 2, round 2 -- 2026-08-16

Reviewed: the tree with round 1 applied, starting from the new code path that
round introduced. Running a predicate's own checks means the verifier now calls
code it did not write, which is a boundary that did not exist before.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | `scripts/ariadne_lib/verify.py` | A predicate module raising inside `check` took the whole run down: exit 1, the code that means a gate was breached, with the core gates that did pass buried under a traceback. A predicate returning something that was not a gate broke the report later, further from the cause | fixed in this round: a raising or misbehaving predicate fails a gate of its own and the core gates still report |
| S2-R2-02 | medium | `scripts/ariadne.py` | A fifo passed to `verify` reported a size of zero, passed the cap, and blocked the read until something wrote to it. The same shape as the tree-digest fifo in step 1, in the subcommand a stranger's file actually arrives at | fixed in this round: anything that is not a regular file is refused, and a path that does not exist says so rather than being described as irregular |
| S2-R2-03 | low | `scripts/ariadne.py` | Every input error printed the path twice, once from the caller and once from inside the message | fixed in this round |

Checked and measured:

- The depth scan costs 0.07 seconds over 4 MB, so the byte-level pass over a
  document at the 8 MB cap is not a way to tie the tool up.
- A predicate that returns an empty list of gates counts as having checked
  nothing, and the report says gates 2 and 5 went unchecked. That is the
  honest reading and it is deliberate.

Leads not pursued: none new.

## Step 2, round 3 -- 2026-08-16

Reviewed: the gates again, hunting for producer-chosen content the key scan
does not reach, and the report's own wording.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | medium | `scripts/ariadne_lib/gates.py` | Gates 4 and 7 scanned the predicate only. A subject's `annotations` are producer-chosen too, so a rating in `subject[0].annotations` passed both gates while sitting in the signed bytes | fixed in this round: the scan covers the predicate and every subject's descriptor fields |
| S2-R3-02 | low | `scripts/ariadne_lib/verify.py` | A failure from a predicate's own check printed as "gate 0", a number no gate has | fixed in this round: it prints as a check rather than borrowing a gate number |

Checked and found sound in round 3:

- A predicate raising no longer reaches the caller, and the core gates still
  print. Asserted by `test_a_predicate_that_raises_fails_its_own_gate_rather_than_the_run`.
- `os.path.exists` before `isfile` keeps a typo'd path saying "no such file"
  rather than describing it as irregular.
- The key walk recurses at most as deep as the parser allowed, which the depth
  cap already bounds at 64.

Leads not pursued: none new.

## Step 2, round 4 -- 2026-08-16

Reviewed: the step's whole diff with three rounds applied. Swept fourteen
malformed predicates through every core gate -- a null predicate, a claims
block that is an object, a claim whose subject is an array, an argv of
integers, an empty output digest, a verdict three lists deep -- and confirmed
each gate reported rather than raised, and that every line rendered. Re-ran the
suite on Python 3.9 and 3.14.

No findings.

Leads not pursued: the two carried from round 1, homoglyph keys and one subject
standing in for another in a multi-subject statement, both recorded in
`docs/conformance.md` under what the gates do not catch.

## Step 3, round 1 -- 2026-08-16

Reviewed: `predicates/solidity_release.py`, `deltas.py` and the published
schema, from the position of a producer who wants a release statement that
passes while the evidence behind it is looser than it looks. Swept twelve
malformed predicates and five malformed delta inputs through the checks first;
nothing raised.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | `scripts/ariadne_lib/predicates/solidity_release.py` | Gate 5 checked that both delta sides carried a digest, but not that the current side was this release. A statement could compare two artefacts it does not cover and present the result as its own history | fixed in this round: the current side has to be a subject of the statement |
| S3-R1-02 | medium | `scripts/ariadne_lib/predicates/solidity_release.py` | `source.commit` and an audit's `covered_revision` accepted any string, so `main` or `release/v1` passed. A branch names whatever it pointed at that day, which is the thing gate 1 exists to refuse | fixed in this round: both have to be a git object id, sha1 or sha256 |
| S3-R1-03 | low | `scripts/ariadne_lib/predicates/solidity_release.py` | Delta sections with no changes in them counted as content, so a first release carrying empty sections beside a null baseline failed with a message about recording changes it had not recorded | fixed in this round: emptiness is decided by `deltas.empty` |

Checked and found sound:

- `missing()` treats `false` and `0` as present, so an optimiser turned off and
  a `runs` of zero are settings rather than absences. Asserted in
  `test_an_optimizer_turned_off_is_a_setting_not_an_absence`.
- `confirmed_against_chain` is checked for presence separately, so recording
  `false` is not read as leaving the field out.
- Every release subject's creation and runtime digest has to be a subject of
  the statement, so the bytecode the predicate describes is the bytecode the
  statement covers.

Leads not pursued:

- **Address and transaction shape.** A deployment's `address` and `creation_tx`
  are not checked for hex shape. Step 4 writes them from capture rather than by
  hand, and a malformed address is visible to any reader; a regex here would
  buy less than it costs in false refusals for chains that format differently.

## Step 3, round 2 -- 2026-08-16

Reviewed: the predicate with round 1 applied, starting from the new emptiness
check, which turned out to have widened a hole rather than closed one.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | medium | `scripts/ariadne_lib/predicates/solidity_release.py` | Nothing checked that a delta section was an object, and `deltas.empty` reads a string as empty. `"abi": "everything changed"` passed gate 5 and printed "no differences recorded" | fixed in this round: a section that is not an object fails |
| S3-R2-02 | low | `scripts/ariadne_lib/predicates/solidity_release.py` | `compiler`, `compiler_version` and `evm_version` accepted any type, so a version of `8` passed and printed as one | fixed in this round |
| S3-R2-03 | low | `scripts/ariadne_lib/predicates/solidity_release.py` | The field check reported a missing `claims` block alongside gate 3 reporting the same thing, telling a reader that two separate things went wrong | fixed in this round: absence is left to the gate that owns each field |

Checked and found sound:

- The revision check did not break the fixtures, which carry real 40-character
  object ids.
- A delta whose current side is a subject still passes, and the fixture set
  covers both the passing and the breaching case.

Leads not pursued: none new.

## Step 3, round 3 -- 2026-08-16

Reviewed: gate 5 one level down, inside the sections rather than at their edges,
and confirmed that dropping the duplicate absence report in round 2 left every
required field still reported by the gate that owns it.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R3-01 | medium | `scripts/ariadne_lib/predicates/solidity_release.py` | Gate 5 held both sides of the comparison to a digest, and then let a `changed`, `moved` or `retyped` entry inside a section name one side or neither. A delta saying `transfer` changed, without saying from what to what, is the diff nobody can act on | fixed in this round: every entry in a both-sided section names both, and every list inside a section has to be a list |

Checked and found sound:

- Every required field is still reported when absent: source, build and
  release_subjects by gate 2, deltas by gate 5, claims and commands by core
  gate 3. Walked each case by hand after round 2 removed the duplicate.

Leads not pursued: none new.

## Step 3, round 4 -- 2026-08-16

Reviewed: the two artefacts that describe this predicate against each other. The
drift test compares required-field lists, which left the fields' own shapes free
to disagree.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R4-01 | medium | `schemas/solidity-release-v1.json` | The published schema accepted any string for `source.commit` and `covered_revision`, while the validator refuses a branch name. A producer building to the schema would have got a refusal here for something their own tooling said was fine | fixed in this round: the schema carries the same pattern, and the drift test compares it against the validator's |

Leads not pursued: none new.

## Step 3, round 5 -- 2026-08-16

Reviewed: the step's whole diff with four rounds applied. Re-swept twelve
malformed predicates and five malformed delta inputs, confirmed every check
reports rather than raises, re-ran the fixture set through the CLI, and re-ran
the suite on Python 3.9 and 3.14.

No findings.

Leads not pursued: the address and transaction shape check carried from round 1,
which step 4 makes moot by writing those fields from capture rather than by
hand.

## Step 4, round 1 -- 2026-08-16

Reviewed: `capture/foundry.py` and `scrub.py`, from the position of somebody
whose credential is about to be published inside a signed document. Ran the
scrubber over a list of real-shaped secrets first: a Postgres URL with a
password, an inline private key, a GitHub token, an AWS access key id, and
several things that must survive, such as an address and a transaction hash.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | medium | `scripts/ariadne_lib/scrub.py` | An inline `PRIVATE_KEY=0x...` passed through untouched. The scrubber only looked at the value half of an assignment when the name was a flag it knew, and a key reaches a command line without a flag in front of it more often than with one | fixed in this round: the value half of any assignment goes through the same redaction as a bare argument |
| S4-R1-02 | medium | `scripts/ariadne_lib/capture/foundry.py` | `--repository` was recorded verbatim, so a URL carrying `user:token@` in front of its host put the token into the statement. Nothing scrubbed it, because the scrubber ran over the build command only | fixed in this round: the repository loses its userinfo and keeps the rest, since the URL has to survive for a reader to follow it |
| S4-R1-03 | low | `docs/capturing-a-release.md` | The heading said capture does not carry your secrets, which is broader than what it does. It scrubs the build command and the repository URL, and records reasons and scopes as written | fixed in this round: the heading says what is scrubbed, and the section says prose is not |

Checked and found sound:

- An address and a short hash survive the scrubber; a 32-byte hex string does
  not, which is the shape a private key takes on a command line.
- A contract with no creation bytecode is left out of the release subjects, so
  an interface does not become a claim about an artefact that does not exist.
- The newest build-info is chosen by modification time, so an older build left
  in the directory does not decide the statement.

Leads not pursued:

- **Short key formats.** A twenty-character AWS access key id passes the
  32-character threshold. Lowering it would start redacting contract names and
  ordinary flags, and the argument-shaped cases that matter are covered by the
  flag list and the assignment rule.

## Step 4, round 2 -- 2026-08-16

Reviewed: the capture path with round 1 applied, this time following what
happens on a project that is not the fixture: a bigger syntax tree, no lock
file, a mistyped argument.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R2-01 | medium | `scripts/ariadne_lib/capture/foundry.py` | The build record carried a `dependency_lock_digest` with nothing saying what it was over. On a project with no lock file the digest is of the source directory, so gate 2 could pass with a reader believing a lock had been pinned | fixed in this round: `build.dependency_lock_source` names the file or `src/`, and the schema carries it |
| S4-R2-02 | medium | `scripts/ariadne_lib/capture/foundry.py` | Artefacts were parsed with a depth cap of 512. The fixture reaches 19, but an artefact carries a syntax tree, and a real contract with long expression chains would have been refused as if it were hostile | fixed in this round: artefacts parse to 4096, with the reason recorded beside the constant |
| S4-R2-03 | low | `scripts/ariadne_lib/capture/foundry.py` | `--tests probably-fine` wrote a statement whose disposition this tool's own verifier rejects, sending the reader to look for the fault in the gates rather than in what they typed | fixed in this round: capture refuses an invented disposition and lists the real ones |
| S4-R2-04 | low | `scripts/ariadne_lib/capture/foundry.py` | `os.path.commonpath` raises on paths that cannot be compared, which would have escaped as a traceback rather than a refusal | fixed in this round |

Leads not pursued: none new.

## Step 4, round 3 -- 2026-08-16

Reviewed: what capture writes when a project holds more than the fixture's one
contract, which is the case the fixture cannot exercise on its own.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R3-01 | medium | `scripts/ariadne_lib/capture/foundry.py` | The delta's current side named the first release subject's runtime bytecode. With more than one contract that is an arbitrary pick, and the comparison covers all of them | fixed in this round: both sides name a digest over the whole build, and that bundle is a subject of the statement so gate 5 still holds |
| S4-R3-02 | medium | `scripts/ariadne_lib/capture/foundry.py` | A contract present in the previous build and gone from this one produced nothing at all. An ABI diff cannot show it, because there is no ABI left to diff, so the removal disappeared | fixed in this round: `deltas.contracts` records what was added and removed, and the predicate and schema carry the section |

Leads not pursued: none new.

## Step 4, round 4 -- 2026-08-16

Reviewed: the step's whole diff with three rounds applied. Built a synthetic
two-contract project against the one-contract fixture, in both directions, to
exercise the paths the fixture alone cannot: a contract added, a contract
removed, and a bundle digest over more than one artefact. Both statements
verify with nothing on the unchecked list, and the contracts section names the
right side each way round. Re-ran the suite on Python 3.9 and 3.14 and the
demo path through the CLI.

No findings.

Leads not pursued: the short key formats carried from round 1.

## Step 5, round 1 -- 2026-08-16

Reviewed: `replay.py` and its subcommand, from the position of somebody who
wrote the statement and would like it to run something. Swept six hostile
command shapes through the plan first.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R1-01 | high | `scripts/ariadne.py` | `replay --allow-execution` ran a statement's commands without checking the statement. Running commands out of a document nobody has verified is taking instructions from it on trust, which is the habit this tool exists to break | fixed in this round: execution refuses a statement that does not verify, and prints the gates it broke |
| S5-R1-02 | medium | `scripts/ariadne_lib/replay.py` | A non-string argument reached `subprocess` and raised there. Gate 6 refuses that shape, but replay does not get to assume the gates ran | fixed in this round: a command whose argv is not a list of strings is refused |
| S5-R1-03 | medium | `scripts/ariadne_lib/replay.py` | The path-separator check used this platform's separator, so `..\evil` was runnable on POSIX and refused on Windows. A portable format that answers differently by platform is not portable | fixed in this round: both separators are refused everywhere |
| S5-R1-04 | low | `scripts/ariadne_lib/replay.py` | `sh` named as the program handed back exactly what `shell=False` was avoiding | fixed in this round: a shell named as the program is refused, and the module says plainly that this is a guard rather than a sandbox |

Checked and found sound:

- Nothing runs without `--allow-execution`, asserted by a test that plans a
  `touch` and then checks the file is absent.
- A semicolon inside an argument reaches the program as an argument.
- A missing program, a timeout and a failing exit status are each reported
  rather than raised, and each makes the result not ok.
- An output digest that cannot be recomputed is reported as not compared, not
  as a match.

Leads not pursued:

- **Sandboxing.** `env PATH=/tmp sh` still runs, because `env` is not a shell
  and this is not a sandbox. Replay runs the program named, under the caller's
  own account, after printing the plan and taking an explicit flag. Saying that
  plainly is worth more than a blocklist that implies otherwise, and the module
  docstring says it.

## Step 5, round 2 -- 2026-08-16

Reviewed: the shipped examples rather than the code that reads them, on the
grounds that an example is a document making claims like any other.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R2-01 | medium | `examples/` | The examples quote digests taken from the committed fixture. Rebuild the fixture, forget the examples, and they go on describing bytecode that no longer exists, while still verifying | fixed in this round: a test re-captures from the fixture and compares the release subjects, so drift fails the suite |
| S5-R2-02 | medium | `examples/README.md` | The examples record that tests and a fuzz campaign passed. Nobody ran either against a nine-line escrow contract; capture takes those dispositions from its caller and they were supplied by hand | fixed in this round: the README says which parts came from the compiler and which were written for illustration |

Checked and found sound:

- Both tampered copies differ from their example in one place, asserted by
  comparing the subject arrays and build records, so neither passes for the
  wrong reason.
- Every example records its deployment as unconfirmed against a chain.

Leads not pursued: none new.

## Step 5, round 3 -- 2026-08-16

Reviewed: every command printed in a shipped document, run as written from the
directory the document names, and the whole step's diff once more. `capture`
then `verify` exits 0 with seven gate lines and three checks; the tampered
example exits 1; `replay` prints its plan and runs nothing; `inspect` reports
the predicate as registered and the statement as unsigned; the README's test
command finds all 298 tests. Re-ran the suite on Python 3.9 and 3.14.

No findings.

Leads not pursued: sandboxing, carried from round 1 and stated in
`replay.py`'s own docstring.

