"""Whether a statement describes this fixture, and whether it claims more.

Something else writes the statement. Ariadne's `capture-state-fixture` is the
one this was built against, but nothing here imports it, runs it, or assumes it
produced the document: a statement is JSON somebody handed over, and it gets the
treatment every other document from outside gets.

The check that matters is the evidence one, and it is worth saying exactly why it
cannot be skipped.

Lazarus recomputes the three counts from the proof and RPC records and refuses a
manifest that disagrees with them. Ariadne reads the counts from the manifest and
does not re-derive them, deliberately: re-deriving would mean reimplementing
Lazarus's judgement about which records were checked against the state root, and
a capture that arrived at a larger number would perform the upgrade it exists to
prevent. Both choices are right on their own.

The consequence is a gap neither tool can close alone. Edit one integer in a
manifest, recompute the fixture digest so the document is entirely
self-consistent, and `lazarus verify` refuses it while `ariadne
capture-state-fixture` accepts it and writes a statement that verifies clean,
reporting six proof-backed records where two exist. Four recorded RPC responses
presented as proved state.

So the numbers a statement is held to here come from `verify_fixture`, never from
the manifest. The manifest is the part a producer can edit; the verified report is
what the records actually support.

Every other field the statement states about this capture is compared too. A
field nothing compares is a field a producer writes freely, and a reader has no
way to tell which half of a bound document was checked.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from .errors import FormatError, IntegrityError, ResourceLimitError
from .manifest import MAX_COMPONENTS
from .text import listed, visible

IN_TOTO_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
"""The envelope the predicate is read inside.

A predicate type says how to read `predicate`; the statement type says the
document is the kind of thing that has one. Without it a bare object carrying the
right two strings binds as though it were an attestation.
"""

STATE_FIXTURE_TYPE = "https://ariadne.wildcat.finance/state-fixture/v1"
"""The predicate this binding understands.

Named rather than accepted from the statement, because a binding that took
whichever type it was handed would bind a fixture to a document making claims in
a vocabulary nothing here has read.
"""

EVIDENCE_CLASSES = ("proof_backed", "header_bound", "recorded_rpc")
"""The three classes, spelled as this plugin spells them everywhere else."""

REPLAY_CLAIMS = ("reaches_network", "canonical_chain_claim")
"""The two things verification does not do, which the statement must not say it does."""

MAX_FIXTURE_SUBJECTS = MAX_COMPONENTS
"""A statement cannot describe more components than a fixture can hold.

Taken from the manifest's own limit rather than restated, so the two cannot
drift apart into a statement this accepts and no fixture can satisfy.
"""

MAX_SUBJECTS = 2 * MAX_COMPONENTS
"""The in-toto subject list may name more than the fixture's components.

The capture itself is one, and a producer may have others. The cap is a bound on
work rather than a claim about what belongs there.
"""

CHECKS = (
    "statement-type",
    "predicate-type",
    "chain-and-block",
    "evidence-counts",
    "replay-claims",
    "components-declared",
    "components-complete",
    "subjects-cover-components",
)
"""Every check this module makes, in the order it makes them.

The names go into the release document, so a reader knows which questions were
asked rather than inferring them from the release existing.
"""


def _object(value: Any, what: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FormatError(f"{what} must be an object, got {type(value).__name__}")
    return value


def _member(node: dict[str, Any], key: str, what: str) -> Any:
    if key not in node:
        raise FormatError(f"{what} has no {key}")
    return node[key]


def _whole_number(value: Any) -> bool:
    """`True` is an integer in Python and one record if nothing looks."""
    return isinstance(value, int) and not isinstance(value, bool)


def _hex_quantity(value: Any, what: str) -> int:
    """A verified hex quantity as the integer a statement writes it as."""
    if not isinstance(value, str) or not value.startswith("0x"):
        raise FormatError(f"{what} is not a hex quantity: {value!r}")
    try:
        return int(value, 16)
    except ValueError:
        raise FormatError(f"{what} is not a hex quantity: {value!r}") from None


def _named(entry: dict[str, Any], what: str, seen: set[str]) -> str:
    """A name that names something, and names it once.

    Compared in composed form. Two Unicode spellings of one name are one name to
    a reader, and a duplicate that gets past this rule by being spelled the other
    way is the ambiguity the rule exists to refuse.
    """
    name = _member(entry, "name", what)
    if not isinstance(name, str) or not visible(name):
        raise FormatError(f"{what} names nothing: {name!r}")
    settled = unicodedata.normalize("NFC", name)
    if settled in seen:
        raise IntegrityError(
            f"statement uses the name {name} twice; a reader matching a subject "
            "by name cannot tell which digest was meant"
        )
    seen.add(settled)
    return name


def _verified_manifest(manifest: Any) -> dict[str, Any]:
    """The fields this binding reads out of a manifest, present and shaped.

    Not a second verification: `verify_manifest` did that, and a caller who
    skipped it is not caught here. It is the difference between a refusal naming
    the field and a traceback out of the middle of a comparison, for a caller who
    handed over the manifest read off disk rather than the verified one.
    """
    manifest = _object(manifest, "manifest")
    _member(manifest, "chain_id", "manifest")
    components = _member(manifest, "components", "manifest")
    if not isinstance(components, list) or not components:
        raise FormatError("manifest components must be a non-empty array")
    for index, entry in enumerate(components):
        what = f"manifest component {index + 1}"
        entry = _object(entry, what)
        path = _member(entry, "path", what)
        if not isinstance(path, str) or not visible(path):
            raise FormatError(f"{what} path names nothing: {path!r}")
        digest = _member(entry, "sha256", what)
        if not isinstance(digest, str) or not visible(digest):
            raise FormatError(f"{what} has no sha256 digest: {digest!r}")
        size = _member(entry, "bytes", what)
        if not _whole_number(size) or size < 0:
            raise FormatError(f"{what} bytes is {size!r} rather than a byte count")
    return manifest


def _verified_report(report: Any) -> dict[str, Any]:
    """The fields this binding reads out of a verified report, present and shaped."""
    report = _object(report, "report")
    for field in ("block_hash", "block_number", "state_root"):
        value = _member(report, field, "report")
        if not isinstance(value, str) or not visible(value):
            raise FormatError(f"report {field} names nothing: {value!r}")
    counts = _object(
        _member(report, "evidence_counts", "report"), "report evidence_counts"
    )
    for name in EVIDENCE_CLASSES:
        value = _member(counts, name, "report evidence_counts")
        if not _whole_number(value) or value < 0:
            raise FormatError(
                f"report {name} count is {value!r} rather than a number of records"
            )
    if set(counts) != set(EVIDENCE_CLASSES):
        raise IntegrityError(
            "state-fixture/v1 binding refuses evidence classes outside its vocabulary"
        )
    header = _object(_member(report, "header_bound", "report"), "report header_bound")
    _member(header, "canonical_chain_claim", "report header_bound")
    return report


def predicate_type_of(statement: dict[str, Any]) -> str:
    """The type a statement declares, checked for shape before it is compared."""
    found = _member(_object(statement, "statement"), "predicateType", "statement")
    if not isinstance(found, str) or not visible(found):
        raise FormatError(f"statement predicateType names nothing: {found!r}")
    return found


def _check_statement_type(statement: dict[str, Any]) -> None:
    found = _member(statement, "_type", "statement")
    if not isinstance(found, str) or not visible(found):
        raise FormatError(f"statement _type names nothing: {found!r}")
    if found != IN_TOTO_STATEMENT_TYPE:
        raise IntegrityError(
            f"statement _type is {found!r} and this binds "
            f"{IN_TOTO_STATEMENT_TYPE}; a predicate type is read inside an "
            "envelope, and there is no envelope here"
        )


def _check_predicate_type(statement: dict[str, Any]) -> None:
    found = predicate_type_of(statement)
    if found != STATE_FIXTURE_TYPE:
        raise IntegrityError(
            f"statement is a {found} and this binds {STATE_FIXTURE_TYPE}; a "
            "binding cannot speak for claims in a vocabulary it has not read"
        )


def _check_chain_and_block(
    predicate: dict[str, Any], manifest: dict[str, Any], report: dict[str, Any]
) -> None:
    """The four fields naming which capture the statement is about.

    The block hash alone would leave the other three free: a statement pinning the
    right hash while naming another chain, another height and another state root
    reads as though all four were corroborated, and one of them was.
    """
    chain = _object(_member(predicate, "chain", "statement predicate"), "statement chain")

    found = _member(chain, "block_hash", "statement chain")
    expected = report["block_hash"]
    if not isinstance(found, str) or found.lower() != expected:
        raise IntegrityError(
            f"statement pins block {found!r} and the fixture verifies to "
            f"{expected}; the statement describes a different capture"
        )

    chain_id = _member(chain, "chain_id", "statement chain")
    expected_chain = _hex_quantity(manifest["chain_id"], "manifest chain_id")
    if not _whole_number(chain_id) or chain_id != expected_chain:
        raise IntegrityError(
            f"statement names chain {chain_id!r} and the fixture is chain "
            f"{expected_chain}"
        )

    number = _member(chain, "block_number", "statement chain")
    expected_number = _hex_quantity(report["block_number"], "verified block number")
    if not _whole_number(number) or number != expected_number:
        raise IntegrityError(
            f"statement names block number {number!r} and the verified header is "
            f"block {expected_number}"
        )

    state_root = _member(chain, "state_root", "statement chain")
    expected_root = report["state_root"]
    if not isinstance(state_root, str) or state_root.lower() != expected_root:
        raise IntegrityError(
            f"statement names state root {state_root!r} and the verified header "
            f"has {expected_root}; every proof in this fixture was checked "
            "against the header's root, not the statement's"
        )


def _check_evidence_counts(predicate: dict[str, Any], report: dict[str, Any]) -> None:
    """The rule this module exists for.

    Compared against the recomputed counts rather than the manifest's, and in
    both directions. A statement claiming fewer records than the fixture holds is
    wrong too: it describes a fixture nobody has, and the next reader cannot tell
    which of the two is the mistake.
    """
    evidence = _object(_member(predicate, "evidence", "statement predicate"), "evidence")
    verified = report["evidence_counts"]
    unknown = sorted(set(evidence) - set(EVIDENCE_CLASSES))
    if unknown:
        raise IntegrityError(
            "statement counts evidence in classes this fixture does not have: "
            + listed(unknown)
        )
    for name in EVIDENCE_CLASSES:
        if name not in evidence:
            raise IntegrityError(
                f"statement has no {name} count; a class left out reads as "
                "nothing of that kind rather than as nobody having said"
            )
        claimed = evidence[name]
        if not _whole_number(claimed):
            raise IntegrityError(
                f"statement {name} count is {claimed!r} rather than a whole "
                "number of records"
            )
        if claimed != verified[name]:
            direction = "more" if claimed > verified[name] else "fewer"
            raise IntegrityError(
                f"statement claims {claimed} {name} record(s) and the fixture "
                f"verifies to {verified[name]}: {direction} than the records "
                "support"
            )


def _check_replay_claims(predicate: dict[str, Any], report: dict[str, Any]) -> None:
    """Both of the two things a replay does not establish.

    `canonical_chain_claim` is the one that matters most: a self-consistent header
    is not proof that it belongs to Ethereum's canonical chain. `reaches_network`
    is the same shape of claim pointed the other way, and a statement saying
    verification went to a node would have a reader believe the records were
    corroborated live. Neither happened, so neither may be said.
    """
    replay = _object(_member(predicate, "replay", "statement predicate"), "statement replay")
    for field in REPLAY_CLAIMS:
        claimed = _member(replay, field, "statement replay")
        if claimed is not False:
            raise IntegrityError(
                f"statement records {field} as {claimed!r}; verification reads "
                "recorded bytes offline and claims neither"
            )
    if report["header_bound"]["canonical_chain_claim"] is not False:
        raise IntegrityError(
            "the verified report claims the canonical chain, which no Lazarus "
            "build establishes"
        )


def _declared_components(predicate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    subjects = _member(predicate, "fixture_subjects", "statement predicate")
    if not isinstance(subjects, list) or not subjects:
        raise FormatError("statement fixture_subjects must be a non-empty array")
    if len(subjects) > MAX_FIXTURE_SUBJECTS:
        raise ResourceLimitError(
            f"statement describes {len(subjects)} components and a fixture holds "
            f"at most {MAX_FIXTURE_SUBJECTS}"
        )
    found: dict[str, dict[str, Any]] = {}
    names: set[str] = set()
    for index, entry in enumerate(subjects):
        what = f"statement fixture subject {index + 1}"
        entry = _object(entry, what)
        _named(entry, what, names)
        path = _member(entry, "path", what)
        if not isinstance(path, str) or not visible(path):
            raise FormatError(f"{what} path names nothing: {path!r}")
        if path in found:
            raise IntegrityError(
                f"statement names {path} twice; one file cannot carry two digests"
            )
        found[path] = entry
    return found


def _check_components(predicate: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Both directions, and the digests in between.

    A component the statement names and the fixture lacks is a statement about a
    file nobody has. A component the fixture holds and the statement omits is a
    file the statement's own subject list does not cover, which is the silent
    absence this plugin refuses everywhere else.
    """
    declared = _declared_components(predicate)
    held = {entry["path"]: entry for entry in manifest["components"]}

    absent = sorted(set(declared) - set(held))
    if absent:
        raise IntegrityError(
            "statement names components the fixture does not hold: "
            + listed(absent)
        )
    missing = sorted(set(held) - set(declared))
    if missing:
        raise IntegrityError(
            "statement does not name components the fixture holds: "
            + listed(missing)
        )

    for path in sorted(held):
        entry = declared[path]
        digest = _object(
            _member(entry, "digest", f"statement fixture subject {path}"),
            f"statement fixture subject {path} digest",
        )
        claimed = digest.get("sha256")
        if claimed != held[path]["sha256"]:
            raise IntegrityError(
                f"statement digests {path} as {claimed!r} and the fixture holds "
                f"{held[path]['sha256']}"
            )
        size = _member(entry, "bytes", f"statement fixture subject {path}")
        if not _whole_number(size) or size != held[path]["bytes"]:
            raise IntegrityError(
                f"statement sizes {path} at {size!r} and the fixture holds "
                f"{held[path]['bytes']} bytes"
            )


def _check_subjects(statement: dict[str, Any], manifest: dict[str, Any]) -> None:
    """The list an in-toto reader actually reads.

    `predicate.fixture_subjects` is where the detail lives, but a policy engine
    handed this statement matches on `subject`. A component described in the
    predicate and absent from the subject list is bound here and invisible there.
    """
    subjects = _member(statement, "subject", "statement")
    if not isinstance(subjects, list) or not subjects:
        raise FormatError("statement subject must be a non-empty array")
    if len(subjects) > MAX_SUBJECTS:
        raise ResourceLimitError(
            f"statement lists {len(subjects)} subjects and this reads at most "
            f"{MAX_SUBJECTS}"
        )
    digests: set[str] = set()
    names: set[str] = set()
    for index, entry in enumerate(subjects):
        what = f"statement subject {index + 1}"
        entry = _object(entry, what)
        _named(entry, what, names)
        digest = _object(_member(entry, "digest", what), f"{what} digest")
        claimed = digest.get("sha256")
        if not isinstance(claimed, str) or not visible(claimed):
            raise FormatError(f"{what} has no sha256 digest: {claimed!r}")
        digests.add(claimed.lower())
    uncovered = sorted(
        entry["path"]
        for entry in manifest["components"]
        if entry["sha256"] not in digests
    )
    if uncovered:
        raise IntegrityError(
            "statement subject list does not cover components the fixture holds: "
            + listed(uncovered)
        )


def bind(
    statement: dict[str, Any],
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> list[str]:
    """Check a statement against a verified fixture; return the checks made.

    `report` is what `verify_fixture` returned, not what the manifest claims. The
    caller has to have verified the fixture, because everything the evidence check
    is worth depends on the counts having been recomputed from the records.

    Raises on the first disagreement rather than collecting them. A statement that
    disagrees about the block it pins is not a document whose component list is
    worth reading, and a release is refused whole.
    """
    statement = _object(statement, "statement")
    manifest = _verified_manifest(manifest)
    report = _verified_report(report)
    predicate = _object(
        _member(statement, "predicate", "statement"), "statement predicate"
    )
    _check_statement_type(statement)
    _check_predicate_type(statement)
    _check_chain_and_block(predicate, manifest, report)
    _check_evidence_counts(predicate, report)
    _check_replay_claims(predicate, report)
    _check_components(predicate, manifest)
    _check_subjects(statement, manifest)
    return list(CHECKS)
