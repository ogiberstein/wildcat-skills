# The state-fixture predicate

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The state-fixture and grounded-agent predicates remain unimplemented; the dataset predicate now ships with its schema, gates, conformance fixtures and capture path.
<!-- marketplace-context:end -->

Type URI: `https://ariadne.wildcat.finance/state-fixture/v1`.

A state fixture is the finite part of historical chain state an application test
needs, captured so the test survives the archive endpoint that served it. Lazarus
produces them. This predicate is how one gets published with evidence a stranger
can check.

The thing it exists to refuse is a fixture that claims more than its producer did.
Lazarus records three classes of evidence and its skill forbids describing one as
another. A statement that shifts a count between the columns, or drops a column,
turns a recorded response into a proof without anybody having to say so.

## The fields

**`chain`** -- the pin: `chain_id`, `block_number`, `block_hash`, and
`state_root` where there is one. The first three together, because any one alone
leaves a reader guessing: a block number without a hash does not say which of two
blocks at that height, and a hash without a chain does not say which chain.

`state_root` is required by what the statement claims rather than by its shape. A
capture that recorded a header and some responses and proved nothing against the
trie has no use for one, and refusing it would refuse an honest fixture. A capture
claiming proof-backed records needs one, and the evidence check below is where
that is enforced -- deliberately, so the rule reaches statements gate 2 accepts
rather than only ones it has already refused.

Both numbers are integers. A Lazarus manifest writes them as hex quantity strings,
which is right on the wire and wrong to compare: `"0xc7da16" < "0x2"` is true,
because that orders text. The capture path converts and this predicate refuses the
wire form rather than ordering it as a string.

**`capture`** -- `tool`, `tool_version`, `command`, `parameters_digest`. A fixture
is only as reproducible as the thing that wrote it, and a tool name with a version
does not say what it was told to do.

**`fixture_subjects`** -- one per component file: `name`, `path`, `digest`,
`bytes`. Each digest has to be a subject of the statement, so the predicate cannot
describe files the statement does not cover. Paths are fixture-relative; an
absolute one, or one carrying a `..` segment, describes a file the fixture does
not hold.

**`evidence`** -- the three counts, spelled as Lazarus spells them in its manifest
schema:

| Class | Means |
| --- | --- |
| `proof_backed` | Checked against the pinned block's state root |
| `header_bound` | Tied to the captured header, without a trie proof |
| `recorded_rpc` | A response an endpoint gave, recorded and not proved |

**`replay`** -- `reaches_network` and `canonical_chain_claim`. Both are recorded
rather than assumed, and both have to be false.

**`deltas`** -- the comparison against an earlier capture of the same block. Both
sides carry a `name` and a `digest`. The one section is `components`. A first
capture carries `"baseline": null` with a `reason`.

**`claims`** and **`commands`** -- the core blocks, checked by gates 1, 3 and 6
like any other predicate's.

## The two gates it owns

**Gate 2, the environment is recoverable.** The pin and the capture record above,
in full, plus every component digest being a subject of the statement. The message
names what is missing rather than saying the record is incomplete.

**Gate 5, deltas name both sides.** A comparison fails when either side cannot be
identified by digest. The current side is checked whenever it is present, on a
first capture as much as on a comparison. That branch went unchecked on the
Solidity release predicate until the run that added this type closed it.

## The two checks it owns

**The evidence check.** All three class keys present, each a non-negative whole
number, and nothing counted as proved without a proof.

A class left out is the quietest of the three failures. It reads as nothing of
that kind having been captured, when what happened is that nobody said. So the key
is required and a fixture that proved nothing writes a zero.

A count of `true` is refused. Python makes `True` an integer, so a check that only
asked whether the value was a number would read a producer's mistake as one
proof-backed record.

The last rule is the one this type would be worthless without: a `proof_backed`
count above zero needs a `state_root` to have been proved against. With no state
root there was nothing to check against, so the count describes work that could
not have happened.

Gate 2 does not require the root, which is what lets this rule do work. An earlier
draft required it there, and the rule became unreachable: every statement it would
have refused had already failed gate 2, so it read as the safeguard this type
exists for while guarding nothing. Writing the conformance fixture is what
surfaced that, because the fixture could not breach the check alone.

**The replay check.** `reaches_network` false, because a replay that falls back to
an endpoint is not a fixture, and the endpoint is the thing a fixture exists to
outlive. `canonical_chain_claim` false, because a block hash and a state root pin
a block, not its place in a chain nothing here re-derived.

Both fields have to be present. `False` is the value, not the default: a producer
who left the key out has not made the decision the field records.

## What this predicate does not establish

Worth stating plainly, because a clean verify is narrower than it looks.

It does not establish that the pinned block is canonical. Nothing in Ariadne or
Lazarus re-derives a chain, and `canonical_chain_claim` being false is the record
of that rather than a formality.

It does not check the proofs. It checks that a count of proof-backed records has a
state root behind it. Whether those proofs verify is Lazarus's own `verify`, and a
statement records the result as a claim like any other.

Nor does it cross-check the counts against the components. A statement claiming one
proof-backed record while listing no proofs file verifies, because this predicate
reads a statement and not a fixture directory. Reading the two together is what the
capture path does, and a statement it wrote carries counts taken from the manifest
rather than from its caller.

It does not upgrade recorded evidence. A `recorded_rpc` count is a count of
responses somebody wrote down. No gate here makes one stronger, and the split
exists so that nobody reading the statement can be misled into thinking one did.

## The published schema

[`schemas/state-fixture-v1.json`](../schemas/state-fixture-v1.json) describes the
shape for another producer to read. A drift test holds it to the field tables in
the module, so a field added to one and not the other fails the suite.

The schema expresses more of the rules than an earlier draft of it did. Draft
2020-12 has `if`/`then`, so the conditional state-root rule is in there: a
`proof_backed` count above zero makes `state_root` required. A component path that
would leave the fixture is refused by a pattern rather than left to the verifier.
Round 2 of the step that added this type found both by comparing the two on the
same documents, and a test now holds them to the same verdict on fifteen shapes.

One rule is beyond any schema, rather than beyond this one. A schema describes the
predicate body, and whether a component digest also appears in the statement's
`subject` array is a fact about the document around the predicate. No keyword
reaches it, so `fail-gate2-state-fixture-component-not-a-subject.json` is the single
fixture the schema accepts and the verifier refuses. A test names it as the one
allowed exception, so a second one cannot appear quietly.

The other thing a schema cannot express is the reason. It can refuse an all-zero
state root with a pattern and it cannot say that the value identifies nothing, and a
producer reading a pattern mismatch learns less than one reading a gate line. So
both ship, and the verifier is the one that explains itself.

## Running it

```bash
python3 scripts/ariadne.py verify tests/fixtures/conformance/pass-state-fixture.json
```

Exit 0, with seven gate lines and three further checks. The fixture is a real
capture: the digests, the byte counts and the evidence counts are the ones Lazarus
wrote for `plugins/lazarus/examples/goldfinch-v0`.
