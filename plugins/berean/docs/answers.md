# Answer records

<!-- marketplace-context:start -->
> **Marketplace context: Berean.** Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it. Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence. **Current frontier:** The reference release answers against a frozen demonstration corpus and preserved Goldfinch mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
<!-- marketplace-context:end -->

The `berean-answer/v1` vocabulary, and why each enum is closed. The schema
is [answer-v1.json](../schemas/answer-v1.json); the checks live in
`scripts/berean_lib/answers.py`.

## Source classes

Four, and exactly four: `document`, `chain_read`, `calculation`,
`user_supplied`. Every factual sentence carries one. The set is closed at
read time because widening it is how a fifth class appears in one answer,
verifies nowhere, and reads to a human as though it verified somewhere.

- `document` sentences cite byte-exact citations into the pinned corpus.
- `chain_read` sentences cite preserved read records by recomputed request
  key, and the read names the chain and block the release declared.
- `calculation` sentences derive from evidence already in the answer, so a
  number with no visible inputs has nowhere to hide.
- `user_supplied` sentences carry no evidence at all. The fact came from
  the asker; attaching an artefact to it would dress a claim as a check.
  Their retention is the release's declaration, not the answer's.

The classes never upgrade. A recorded read does not become proof-backed
here, and a document claim does not become a chain reading because the
chain happens to agree with it.

## Time domains

A document speaks as of its version; a read speaks as of its block. When
the two disagree about a subject, the answer carries a `discrepancies`
entry naming the citation, the read and the disagreement. The checker
proves both sides exist and resolve; whether an answer that stayed silent
should have declared one is an evaluation question, and the eval corpus
carries those cases.

## Refusals

A refusal is `kind: "refusal"` with a named boundary and nothing else: no
sentences, no citations, no reads. The emptiness is enforced, because a
refusal that also answers is an answer that dodged its evidence rules.

## Evidence hygiene

Ids are unique, every evidence reference resolves, and evidence nothing
cites is refused. An answer carries only the evidence it uses, so a reader
auditing one sentence is never sent through artefacts the answer merely
decorated itself with.
