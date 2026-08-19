# Capturing a state fixture

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The state-fixture and grounded-agent predicates remain unimplemented; the dataset predicate now ships with its schema, gates, conformance fixtures and capture path.
<!-- marketplace-context:end -->

`capture-state-fixture` reads a Lazarus fixture directory that already exists and
writes a statement of type `https://ariadne.wildcat.finance/state-fixture/v1`. It
runs no capture, reaches no network, and re-derives nothing.

```bash
python3 scripts/ariadne.py capture-state-fixture \
  --fixture ../lazarus/examples/goldfinch-v0 \
  --name goldfinch-v0 \
  --capture-tool lazarus \
  --capture-command python3 \
  --capture-command scripts/lazarus.py \
  --capture-command verify \
  --capture-command examples/goldfinch-v0 \
  --first-capture-reason 'first preservation release of this fixture' \
  --out fixture.json

python3 scripts/ariadne.py verify fixture.json
```

Exit 0, with seven gate lines and three further checks.

## The counts are read, not computed

This is the rule the capture exists for.

Lazarus separates what was proved against the state root from what an endpoint
merely said, and it writes the three counts into its manifest. This capture copies
them across. It does not open `proofs.jsonl` and count the records, and it does not
decide which of them were checked.

The reason is not convenience. Deciding that means reimplementing Lazarus's judgement
from its files, and a capture that reimplemented it and arrived at a larger number
would have upgraded recorded evidence into proved evidence. Lazarus's own skill
forbids describing one class as another, and this is where a tool reading its output
would most easily do it by accident.

So the counts are read, the manifest is checked against its own directory, and a
manifest that disagrees with the files beside it is refused rather than corrected.

## What it checks

**The manifest against the directory, in both directions.** A component the manifest
declares and the directory lacks is a statement describing a file nobody has. A file
the directory holds and the manifest does not declare is a file the fixture digest
does not cover, with nothing saying so. Both are refused. The manifest itself is the
one exception, because it cannot list its own digest.

**Every declared digest and byte count.** Each component is re-digested from disk and
compared against what the manifest claims. A disagreement is refused with both values
in the message.

**The pin.** The chain id and the block number arrive as hex quantity strings, which
is right on the wire and wrong to compare: `"0xc7da16" < "0x2"` is true, because that
orders text. They become integers here, and a leading zero is refused because two
spellings of one number would give two statements for one fixture.

The block hash is lowercased, since Lazarus accepts either case and this predicate
accepts only lowercase. That is a conversion between two spellings of one value. The
all-zero hash is not converted into acceptability: it matches the shape and identifies
nothing.

**The state root, where there is one.** It comes from `header.json`. A fixture with no
header, or a header with no state root, produces a statement with no state root, and
that is deliberate: a capture that recorded responses and proved nothing has no use
for one. The predicate's evidence check is what refuses a proof-backed count without
it, and when that combination appears the capture writes a failed claim beside it
saying why, so a reader sees the reason before running `verify`.

## What you supply, and why

**`--capture-tool`.** Required, no default. The manifest carries a `tool_version` and
does not name the tool that wrote it. Reading a Lazarus-shaped manifest and writing
`lazarus` into the field gate 2 reads as the thing that made the fixture would be this
capture asserting something nobody recorded.

**`--capture-command`.** Required, one flag per argv word. The command that produced
the fixture is not in the fixture.

**`--capture-version`.** Optional, and checked rather than used. Supplying one that
disagrees with the manifest is refused, because the manifest is what the tool wrote.
Supplying nothing takes the manifest's version, which is the same thing without the
opportunity to disagree.

**`--previous` and `--previous-name`, or `--first-capture-reason`.** A first capture
carries a null baseline and says why, as every predicate here does. A comparison
identifies both sides by a digest over the component listing and records no
per-component difference, because naming one needs a component identity across two
captures that this tool does not have. A skipped claim says so.

**`--parameter`.** Optional, repeatable, `key=value`. They are digested into
`parameters_digest`, sorted, so the same parameters give the same digest whatever
order they arrived in.

## What you cannot supply

`reaches_network` and `canonical_chain_claim` are written false and are not flags.

Ariadne reaches no network, and neither tool re-derives a chain, so false is the only
honest value for either. A flag would imply a producer could set them, and a producer
who could set `canonical_chain_claim` to true would be recording something nothing
established.

## What it does not establish

A clean capture and a clean verify are narrower than they look.

It does not check the proofs. It checks that a count of proof-backed records has a
state root behind it. Whether those proofs verify is Lazarus's own `verify`, and this
capture records a skipped claim saying it did not re-run one.

It does not cross-check the counts against the components. A manifest claiming one
proof-backed record while listing no proofs file is refused nowhere here, because the
count comes from the manifest and the manifest is what Lazarus wrote. Checking it
would mean deciding which file holds proofs, which is the reimplementation the first
section is about.

It does not establish that the pinned block is canonical. Nothing in either tool
re-derives a chain.

## Refusals you may meet

| Message | What to do |
| --- | --- |
| `fixture <dir> has no manifest.json` | Name a Lazarus fixture directory, not its parent |
| `manifest.json declares <path>, which the fixture does not hold` | The fixture is incomplete; re-run the Lazarus capture |
| `fixture holds <path>, which manifest.json does not declare` | Remove the stray file, or re-run the capture so the manifest covers it |
| `manifest.json says <path> digests to <a> and it digests to <b>` | The file changed after the manifest was written |
| `manifest.json is schema_version <n> and this capture reads 1` | A later manifest may spell the counts differently; this build will not guess |
| `--capture-version says <a> and manifest.json says <b>` | Drop the flag, or correct it |
| `<path> is a symlink` | Its target is outside what the fixture digest covers |
