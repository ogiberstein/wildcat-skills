# Invariants

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

This records chunker guarantees, defects that explain design choices or fixtures,
and residual weak points. It omits past findings that explain neither.

The central risk is a verified-looking citation to the wrong bytes, source,
contract, or fragment. A crash stops the build and is safer.

## Current invariants

### Shared schema and citation invariants

**I1: display text is byte-exact source.** For `synthesised: false`, slice
`display_text` from source bytes before decoding. Solc offsets are bytes, not
Python characters.

**I2: assembled chunks are labeled.** Contract headers, callable surfaces, and
document indexes combine regions and carry `synthesised: true`; never render them
as verbatim quotes.

**I3: IDs are unique after source namespacing.** Solidity IDs include path,
contract, signature, and canonical parameter types. Markdown duplicate headings
are disambiguated. The merged pipeline rejects collisions across sources.

**I4: evidence and model input remain separate.** Comment removal changes
`model_text`; it never changes `display_text`. `embed_text` is composed from
structured state rather than parsed back from a previous rendered string.

**I5: schema validation is fatal.** Empty required fields or visible model text,
invalid source types or tiers, duplicate IDs, wrong synthesized flags, and
oversize model or embedding text stop the build.

**I6: provenance is pipeline-owned.** Chunkers emit source-local facts. The
calling pipeline applies corpus build ID, resolved source ref, tier, protocol
version, deployment status, and per-document legal metadata, via
`schema.stamp()`.

### Solidity invariants

**S1: deployed inputs define the corpus.** The chunker consumes every configured
deployment `standard-input.json`. Compilation errors, unexpected solc under
`--expect-solc`, invalid source-unit paths, and empty selections are fatal.

**S2: comment removal preserves code.** Keep strings with comment delimiters,
Unicode and hex literals, escaped quotes, division, and CR line endings. Retain
only solc-attached documentation as natspec; mid-body `///` and `/** */` are
ordinary comments.

**S3: signatures distinguish semantic types.** Canonical signatures preserve
struct, enum, contract, fully qualified type, array, and payable-address
distinctions while removing data-location syntax.

**S4: inheritance follows compiler order.** Exposure walks
`linearizedBaseContracts` and keeps the first definition of a signature. Public
state-variable getters occupy their signature slot, derived overrides shadow
bases, and constructors are not inherited.

**S5: compilation-unit merging only adds evidence.** Union exposure and OR
override state across units. Absence from one unit does not erase another.

**S6: callable surfaces agree with the ABI.** Public and external functions and
getters are compared with the compiler ABI by full input signature. A divergence
stops the build.

**S7: deduplicated declarations remain retrievable.** Identical model text may
fold into one chunk, but alias IDs and breadcrumbs are preserved in structured
detail and embedding text.

### Markdown invariants

**M1: only rendered structure creates boundaries.** Headings inside code fences,
HTML comments, raw HTML blocks, inline code, lazy list continuation, and lazy
blockquote continuation do not become section boundaries.

**M2: hidden comments do not enter model text.** Remove comment bytes but retain
visible same-line text. Keep comment syntax in valid code spans. Treat unmatched
or escaped backticks as literal, not unbounded hiding delimiters.

**M3: anchors follow renderer behavior.** Inline markup is reduced to rendered
text before slugging. Duplicate suffixes count every parsed heading, including
headings filtered from chunk output. Page titles have no fragment, and the
renderer-specific handling for entities, mentions, punctuation, leading digits,
and length limits is reproduced.

**M4: navigation failures are explicit.** A requested unreadable `SUMMARY.md`
or a hierarchy that places zero emitted documents is fatal. Included documents
missing from navigation and navigation entries missing from output are reported.

**M5: short documents do not disappear silently.** Section-size filtering may
remove noise, but a document with no surviving section is emitted as a
whole-document chunk. Coverage counts emitted documents rather than discovered
filenames.

**M6: pinned refs determine all bytes.** Symlinked documents, symlinked
navigation, paths outside the root, and unreadable sources are rejected.

**M7: template chrome does not enter model text.** Remove GitBook `{% … %}` bytes
even beside prose, while keeping wrapped text. A live chunk once carried
`{% hint style="info" %}` beside prose into an answer. Keep tags in fences or
valid code spans, and treat unclosed `{%` as literal. Display text stays
byte-exact because only model-text span selection strips tags.

## Why the implementation has these shapes

The following defect classes were found and fixed under adversarial review.
Each fix has a regression fixture in the current suites.

### Byte and character offsets diverge

Solc byte offsets once sliced decoded Python strings, corrupting Solidity after
non-ASCII text while leaving plausible code. A later variant treated a byte
length as characters and could extend natspec into a function body. Source and
documentation stay in bytes until the selected region is decoded.

### Self-derived checks can certify the wrong object

Several green checks measured a proxy rather than the production value:

- the oversize guard measured `model_text` although the embedder receives the
  larger `embed_text`;
- callable-surface validation compared ABI names instead of signatures;
- Markdown hierarchy coverage counted discovered files rather than emitted
  documents; and
- merge tests reproduced the merge loop instead of calling it.

Current validation targets the actual embedded string, full ABI input
signatures, emitted document paths, and production entry points.

### Re-parsing generated text creates attacker-controlled delimiters

Embedding text once split its base on a human-readable marker that natspec could
contain. Later text vanished from retrieval while its citation survived. Each
update now composes embedding text from model text, breadcrumb, exposure, and
aliases.

### Handwritten syntax approximations need fail-safe direction

The Markdown scanner historically mistook raw HTML, setext thematic breaks,
lazy continuation, multi-line code spans, and closing tags for structure. The
current state machine covers the constructs that affect heading or comment
visibility. Where inline interpretation remains ambiguous, it resolves toward
not-code, which can remove visible text from model context but does not admit
reader-hidden instructions.

### Compiler facts should replace lexical guesses

Recognizing natspec by `///` or `/** */` preserved documentation-shaped function
body comments. The chunker now keeps only solc's attached documentation range.

The same principle applies to inheritance order and ABI surfaces: compiler
linearization and ABI output are stronger evidence than a parallel source-level
approximation.

### Fail-open selection creates plausible incomplete corpora

Typoed include patterns, unreadable navigation, zero emitted documents, and
empty model text once produced successful commands. Each now stops the build.
Warnings remain for non-fatal coverage information, but absence of the selected
corpus is not a warning condition.

## Recorded baseline

`baseline/regenerate` produced this from the small, invented `baseline/` corpus
with solc 0.8.25, resolved by the `solc-container` digest. These numbers reproduce
from a clone.

Solidity figures depend on the compiler AST. `regenerate` passes `--expect-solc`,
so a change fails instead of printing new numbers (S1). This corpus happens to
produce byte-identical chunks on 0.8.25 and 0.8.26; it does not exercise a
difference between those releases and does not prove compiler independence.

```text
Solidity: 25 chunks from 1 compilation unit
  0 duplicate bodies folded; 0 alias IDs retained
  5 synthesised chunks
  13 chunks attributed to a concrete contract
  0 unreachable public/external functions
  model p99 761 characters; maximum 761; limit 24,000
  by kind: Enum 1, Error 3, Event 2, Function 12, Modifier 1, Struct 1,
           contract 2, interface 1, library 1, surface 1

Markdown entry ref: 38 chunks from 9 documents; 9/9 placed; 9 indexes
  34 chunks in SUMMARY; median 141 characters; p99 568; maximum 568
Markdown current: 49 chunks from 9 documents; 9/9 placed; 9 indexes
  44 chunks in SUMMARY; median 143 characters; p99 589; maximum 589
```

The entry-ref Markdown figures retain the source evidence tokens for this prose
pass. The current figures reproduce from the rewritten corpus. Move the current
baseline with intentional chunker or corpus changes; investigate unexpected ones.

## A note on numbering

`S*` and `M*` name these invariants, not suite cases: `test_solidity.py` prints
`I4` through `I29`; `test_markdown.py` prints `M1` through `M24`. The Markdown
prefix collision is accidental. Several cases usually cover one invariant, so
`M3` here does not mean suite case `M3`.

Both suites print a per-run assertion total. Treat it as a regression signal;
adding source legitimately changes it.

## Residual weak points

**Include matching uses `fnmatch`.** Patterns such as `src/**` do not have shell
globstar semantics. The manifest's current selections are tested, but every
pattern change should inspect the resolved file list.

**Assembly has no special chunk.** Inline assembly remains inside its enclosing
function and may embed poorly when opcode-heavy.

**ABI comparison is not total.** Callable-surface validation compares callable
names and input types. It does not independently check return types or state
mutability.

**The Markdown inline scanner is intentionally incomplete.** It is not a full
CommonMark inline parser; link titles, autolinks, and reference definitions are
not modeled. The covered boundary is hidden text and heading structure.

**Anchor behavior is empirical.** GitBook publishes no slug specification.
`verify_anchors.py` compares pinned sources with the live site through the same
`assign_anchors()` implementation. A live site that has advanced beyond the
pinned ref reduces the comparable denominator, so fewer verified pages indicates
docs drift rather than proof of correctness.

**Whole-document fallbacks use a different grain.** A short document emitted as
one chunk has no overlapping sections, but retrieval quality for these coarse
chunks has not been measured separately.

**Compiler pinning depends on invocation.** `--expect-solc` checks a version and
the build records the compiler. Only `./solc-container` pins the compiler
artifact by image digest; a developer can deliberately pass a local binary.

**The oversize limit has headroom rather than operational history.** The current
maximums are well below the limit. Synthetic fixtures exercise rejection, but no
pinned source has approached it.

## Verification commands

```bash
python3 tests/test_markdown.py
python3 tests/test_solidity.py --solc ./solc-container
```

After a docs or platform change, inspect the renderer fit with
`python3 tools/verify_anchors.py --help`.
