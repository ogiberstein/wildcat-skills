"""Answer records: classified sentences, proven evidence, clean refusals.

An answer document carries every factual sentence with exactly one source
class and the evidence ids behind it. A refusal is the other kind of
answer: it names the evidence boundary it could not satisfy and carries
nothing else. `check` proves what can be proved mechanically: shape,
closed vocabularies, citation spans against the pinned corpus, read keys
against the preserved records and the declared chain and block, and both
sides of every declared disagreement. Whether a sentence should have been
written at all is the evaluation corpus's job, not this module's.
"""

from . import BereanError
from . import citations as citations_lib
from . import jsonio
from . import reads as reads_lib
from .corpus import Check

FORMAT = "berean-answer/v1"
FIELDS = (
    "format",
    "question",
    "kind",
    "refusal",
    "sentences",
    "citations",
    "reads",
    "discrepancies",
)
KINDS = ("answer", "refusal")
SOURCE_CLASSES = ("document", "chain_read", "calculation", "user_supplied")
SENTENCE_FIELDS = ("text", "source_class", "evidence")
READ_FIELDS = ("id", "chain_id", "block_number", "request_key")
REFUSAL_FIELDS = ("boundary", "detail")
DISCREPANCY_FIELDS = ("subject", "document_evidence", "chain_evidence", "note")
MAX_SENTENCES = 500
_ID_KINDS = {"document": "citation", "chain_read": "read"}


def validate(answer):
    """Hold an answer document to its closed tables and vocabularies."""
    jsonio.require(answer, FIELDS, "answer")
    if answer["format"] != FORMAT:
        raise BereanError(f"answer format is {answer['format']!r}, not {FORMAT!r}")
    jsonio.stated(answer["question"], "question")
    if answer["kind"] not in KINDS:
        raise BereanError(f"unknown answer kind: {answer['kind']!r}")
    for name in ("sentences", "citations", "reads", "discrepancies"):
        if not isinstance(answer[name], list):
            raise BereanError(f"{name} is not a list")

    if answer["kind"] == "refusal":
        jsonio.require(answer["refusal"], REFUSAL_FIELDS, "refusal")
        jsonio.stated(answer["refusal"]["boundary"], "refusal boundary")
        jsonio.stated(answer["refusal"]["detail"], "refusal detail")
        for name in ("sentences", "citations", "reads", "discrepancies"):
            if answer[name]:
                raise BereanError(f"a refusal carries no {name}")
        return answer

    if answer["refusal"] is not None:
        raise BereanError("an answer carries no refusal block")
    if not answer["sentences"]:
        raise BereanError("an answer carries at least one sentence")
    if len(answer["sentences"]) > MAX_SENTENCES:
        raise BereanError(f"answer over the {MAX_SENTENCES} sentence ceiling")

    citation_ids = _collect_ids(answer["citations"], "citation", _validate_citation)
    read_ids = _collect_ids(answer["reads"], "read", _validate_read)

    used = set()
    for index, sentence in enumerate(answer["sentences"]):
        jsonio.require(sentence, SENTENCE_FIELDS, f"sentence {index}")
        jsonio.stated(sentence["text"], f"sentence {index} text")
        source_class = sentence["source_class"]
        if source_class not in SOURCE_CLASSES:
            raise BereanError(f"sentence {index} has no source class: {source_class!r}")
        evidence = sentence["evidence"]
        if not isinstance(evidence, list):
            raise BereanError(f"sentence {index} evidence is not a list")
        if source_class == "user_supplied":
            if evidence:
                raise BereanError(
                    f"sentence {index} is user_supplied and cites evidence; "
                    "a supplied fact has no artefact behind it"
                )
            continue
        if not evidence:
            raise BereanError(f"sentence {index} ({source_class}) cites no evidence")
        for ref in evidence:
            if source_class == "document" and ref not in citation_ids:
                raise BereanError(f"sentence {index} cites unknown citation: {ref!r}")
            if source_class == "chain_read" and ref not in read_ids:
                raise BereanError(f"sentence {index} cites unknown read: {ref!r}")
            if source_class == "calculation" and ref not in citation_ids | read_ids:
                raise BereanError(f"sentence {index} derives from unknown evidence: {ref!r}")
            used.add(ref)

    for index, item in enumerate(answer["discrepancies"]):
        jsonio.require(item, DISCREPANCY_FIELDS, f"discrepancy {index}")
        jsonio.stated(item["subject"], f"discrepancy {index} subject")
        jsonio.stated(item["note"], f"discrepancy {index} note")
        if item["document_evidence"] not in citation_ids:
            raise BereanError(f"discrepancy {index} names an unknown citation")
        if item["chain_evidence"] not in read_ids:
            raise BereanError(f"discrepancy {index} names an unknown read")

    unused = (citation_ids | read_ids) - used - {
        item["document_evidence"] for item in answer["discrepancies"]
    } - {item["chain_evidence"] for item in answer["discrepancies"]}
    if unused:
        raise BereanError(
            f"evidence nothing cites: {', '.join(sorted(unused))}; "
            "an answer carries only the evidence it uses"
        )
    return answer


def _collect_ids(items, what, validator):
    ids = set()
    for index, item in enumerate(items):
        validator(item, index)
        identifier = item["id"]
        if identifier in ids:
            raise BereanError(f"{what} id used twice: {identifier!r}")
        ids.add(identifier)
    return ids


def _validate_citation(item, index):
    if not isinstance(item, dict) or "id" not in item:
        raise BereanError(f"citation {index} has no id")
    jsonio.stated(item["id"], f"citation {index} id")
    body = {key: value for key, value in item.items() if key != "id"}
    citations_lib.validate(body)


def _validate_read(item, index):
    jsonio.require(item, READ_FIELDS, f"read {index}")
    jsonio.stated(item["id"], f"read {index} id")
    jsonio.whole_number(item["chain_id"], f"read {index} chain_id")
    jsonio.whole_number(item["block_number"], f"read {index} block_number")
    from . import digests

    digests.check_hex(item["request_key"], f"read {index} request_key")


def check(answer, manifest, root, records, chain_id, block_number):
    """Prove or refuse one answer; named checks out, model not required."""
    checks = []
    try:
        validate(answer)
        checks.append(Check("answer-shape", True))
    except BereanError as error:
        return [Check("answer-shape", False, str(error))]

    if answer["kind"] == "refusal":
        checks.append(Check("answer-refusal", True, answer["refusal"]["boundary"]))
        return checks

    bad = []
    for item in answer["citations"]:
        body = {key: value for key, value in item.items() if key != "id"}
        for result in citations_lib.check(body, manifest, root):
            if not result.passed:
                bad.append(f"{item['id']}: {result.name} ({result.detail})")
    if bad:
        checks.append(Check("answer-citations", False, "; ".join(bad)))
    else:
        checks.append(Check("answer-citations", True))

    bad = []
    for item in answer["reads"]:
        if item["chain_id"] != chain_id or item["block_number"] != block_number:
            bad.append(
                f"{item['id']}: names chain {item['chain_id']} block {item['block_number']}, "
                f"not the declared chain {chain_id} block {block_number}"
            )
        elif item["request_key"] not in records:
            bad.append(f"{item['id']}: no preserved record for {item['request_key']}")
    if bad:
        checks.append(Check("answer-reads", False, "; ".join(bad)))
    else:
        checks.append(Check("answer-reads", True))

    unclassified = [
        str(index)
        for index, sentence in enumerate(answer["sentences"])
        if sentence["source_class"] not in SOURCE_CLASSES
    ]
    checks.append(
        Check("answer-classes", not unclassified, ", ".join(unclassified))
    )

    checks.append(Check("answer-domains", True, f"{len(answer['discrepancies'])} declared"))
    return checks
