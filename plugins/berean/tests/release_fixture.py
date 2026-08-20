"""One small, fully synthetic release the release and promotion tests share.

Everything here is fabricated: the corpus describes an invented registry,
the read records are made up, and the block hash is a stated constant. The
conformance fixture under `fixtures/conformance/pass-release/` is this
builder's output committed verbatim, and a test regenerates it to hold the
committed bytes still.
"""

import os

from berean_lib import canonical, corpus, citations, digests, reads, release

DOC = (
    "# Registry terms\n\n"
    "The pause flag halts new entries. Version 3 keeps it set.\n"
).encode("utf-8")
CHAIN_ID = 1
BLOCK_NUMBER = 1000000
BLOCK_HASH = "0x" + "ab" * 32
CONTRACT = "0x" + "8b" * 20
QUESTION_FAMILIES = ("registry state", "documented behaviour")
REFUSAL_CONDITIONS = ("questions outside the registry", "evidence past the pinned block")
SOURCE_NOTE = "synthetic conformance fixture; every record fabricated for the tests"


def read_record():
    method = "eth_getStorageAt"
    params = [CONTRACT, "0x0", hex(BLOCK_NUMBER)]
    return {
        "schema_version": 1,
        "request_key": reads.request_key(method, params),
        "method": method,
        "params": params,
        "required": True,
        "evidence": "recorded-rpc",
        "outcome": {"result": "0x" + "00" * 31 + "01"},
    }


def span(needle):
    start = DOC.index(needle.encode("utf-8"))
    return start, start + len(needle.encode("utf-8"))


def answer_document(record):
    needle = "The pause flag halts new entries."
    start, end = span(needle)
    return {
        "format": "berean-answer/v1",
        "question": "Is the pause flag set?",
        "kind": "answer",
        "refusal": None,
        "sentences": [
            {
                "text": "The terms say the pause flag halts new entries.",
                "source_class": "document",
                "evidence": ["c1"],
            },
            {
                "text": "Slot zero reads one at the pinned block.",
                "source_class": "chain_read",
                "evidence": ["r1"],
            },
            {
                "text": "You said your desk treats a set flag as a hold.",
                "source_class": "user_supplied",
                "evidence": [],
            },
        ],
        "citations": [
            {
                "id": "c1",
                "format": citations.FORMAT,
                "doc": "terms.md",
                "byte_start": start,
                "byte_end": end,
                "sha256": digests.of_bytes(DOC[start:end]),
                "display_text": needle,
            }
        ],
        "reads": [
            {
                "id": "r1",
                "chain_id": CHAIN_ID,
                "block_number": BLOCK_NUMBER,
                "request_key": record["request_key"],
            }
        ],
        "discrepancies": [],
    }


def refusal_document():
    return {
        "format": "berean-answer/v1",
        "question": "What will the flag read next month?",
        "kind": "refusal",
        "refusal": {
            "boundary": "evidence past the pinned block",
            "detail": "the release reads one block and predicts nothing",
        },
        "sentences": [],
        "citations": [],
        "reads": [],
        "discrepancies": [],
    }


def eval_report(document, cases_sha256):
    from berean_lib import promote

    return {
        "format": promote.REPORT_FORMAT,
        "corpus_digest": document["corpus"]["corpus_digest"],
        "cases_sha256": cases_sha256,
        "answers_digest": promote.answers_digest(document),
        "cases": 2,
        "passed": 2,
        "failed": 0,
        "failures": [],
    }


def write_json(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(canonical.dumps(value) + "\n")


def build(directory):
    """Assemble the synthetic release into `directory` and return its document."""
    corpus_root = os.path.join(directory, "corpus")
    os.makedirs(corpus_root, exist_ok=True)
    with open(os.path.join(corpus_root, "terms.md"), "wb") as handle:
        handle.write(DOC)
    manifest = corpus.build(corpus_root, "v1")
    corpus.write(manifest, os.path.join(directory, "corpus-manifest.json"))

    record = read_record()
    with open(os.path.join(directory, "reads.jsonl"), "w", encoding="utf-8") as handle:
        handle.write(canonical.dumps(record) + "\n")

    write_json(os.path.join(directory, "answers", "a1.json"), answer_document(record))
    write_json(os.path.join(directory, "answers", "a2.json"), refusal_document())

    cases = {"placeholder": "eval cases land in step 5; these bytes are pinned all the same"}
    write_json(os.path.join(directory, "evals", "cases.json"), cases)
    cases_sha256 = digests.of_file(os.path.join(directory, "evals", "cases.json"))

    # The report depends on the answers and corpus, never on release.json,
    # so it can be written before the release document that pins it.
    preview = {
        "corpus": {"corpus_digest": manifest["corpus_digest"]},
        "answers": [
            {
                "path": f"answers/{name}",
                "sha256": digests.of_file(os.path.join(directory, "answers", name)),
            }
            for name in sorted(os.listdir(os.path.join(directory, "answers")))
        ],
    }
    write_json(
        os.path.join(directory, "evals", "report.json"),
        eval_report(preview, cases_sha256),
    )

    return release.build(
        directory,
        "v0",
        QUESTION_FAMILIES,
        REFUSAL_CONDITIONS,
        {"chains": [CHAIN_ID], "contracts": [CONTRACT]},
        "answers-only",
        reads_context={
            "chain_id": CHAIN_ID,
            "block_number": BLOCK_NUMBER,
            "block_hash": BLOCK_HASH,
            "source": SOURCE_NOTE,
        },
        evals_paths={"cases": "evals/cases.json", "report": "evals/report.json"},
    )
