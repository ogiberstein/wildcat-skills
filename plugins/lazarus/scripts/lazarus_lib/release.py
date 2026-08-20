"""Write a preservation release: a fixture, a statement about it, and the bind.

A release is three things in one directory. The fixture is a byte-for-byte copy
of a directory that verifies. The statement is the bytes somebody handed over,
unaltered, because the release digests them and a re-encoded document is a
different document. The release file records what verification established and
which checks the binding made.

Two decisions are worth stating.

**One read of the directory, not two.** Verification and binding both need the
manifest, and reading it twice means reading two states: a component can change
between the two reads, and nothing after the first read would notice. So
`verify_fixture` hands back the manifest its report was computed from, and the
binding is given that rather than a second read.

**The output appears whole or not at all.** Everything is built in a staging
directory beside the destination and moved into place with one rename. A run
that dies halfway leaves a directory whose name starts with a dot and is not a
release, rather than half of one that reads as whole.

The fixture copy is verified again after it is written, and its digest compared
to the original's. Copying is where bytes go missing, and a release holding a
fixture nobody has verified is the thing this exists to prevent.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any

from .binding import bind, predicate_type_of
from .canonical import MAX_JSON_BYTES, dumps, loads
from .errors import FormatError, IntegrityError, PathError
from .manifest import MANIFEST_NAME, MAX_COMPONENT_BYTES
from .paths import (
    confined_directory,
    read_confined_bytes,
    validate_relative_path,
)
from .schemas import validate_document
from .verifier import verify_fixture
from .version import __version__

FIXTURE_DIRECTORY = "fixture"
"""Where the fixture copy sits inside a release."""

STATEMENT_NAME = "statement.json"
"""Where the statement sits inside a release, beside the fixture rather than in it."""

RELEASE_NAME = "release.json"
"""The document binding the other two."""


def release_digest(release: dict[str, Any]) -> str:
    """A digest over everything the release says except the digest itself.

    Built from named fields rather than by deleting a key, so a field added to
    the schema and not to this identity is a test failure rather than a digest
    that quietly stops covering it.
    """
    identity = {
        "schema_version": release["schema_version"],
        "tool_version": release["tool_version"],
        "fixture": release["fixture"],
        "statement": release["statement"],
        "verified": release["verified"],
        "binding": release["binding"],
    }
    return hashlib.sha256(dumps(identity)).hexdigest()


def build_release(
    statement: dict[str, Any],
    statement_bytes: bytes,
    report: dict[str, Any],
    checks: list[str],
) -> dict[str, Any]:
    """The release document for a fixture that verified and a statement that bound."""
    release: dict[str, Any] = {
        "schema_version": 1,
        "tool_version": __version__,
        "fixture": {
            "path": FIXTURE_DIRECTORY,
            "fixture_digest": report["fixture_digest"],
        },
        "statement": {
            "path": STATEMENT_NAME,
            "sha256": hashlib.sha256(statement_bytes).hexdigest(),
            "predicate_type": predicate_type_of(statement),
        },
        "verified": {
            "block_hash": report["block_hash"],
            "evidence_counts": dict(report["evidence_counts"]),
            "canonical_chain_claim": False,
        },
        "binding": {"checks": list(checks)},
        "release_digest": "0" * 64,
    }
    release["release_digest"] = release_digest(release)
    return validate_document("release", release)


def write_release(
    fixture: str | Path,
    statement_path: str | Path,
    out: str | Path,
) -> dict[str, Any]:
    """Verify a fixture, bind a statement to it, and write the release.

    Nothing is written until both pass. The return value is the release document,
    so a caller printing a summary reads what was written rather than recomputing
    it.
    """
    source = Path(fixture)
    destination = Path(out)
    _refuse_overlap(source, destination)
    if destination.exists() or destination.is_symlink():
        raise FormatError(f"release output already exists: {destination}")
    parent = destination.parent
    if not parent.is_dir():
        raise FormatError(f"release output has no parent directory: {parent}")

    _refuse_statement_inside(source, statement_path)
    statement_bytes = _read_statement(statement_path)
    # A document that is not an object is refused by the binding, which says so
    # in the same words it uses for every other shape it will not read. A second
    # check here would be a second authority on one question.
    statement = loads(statement_bytes)

    report = verify_fixture(source)
    checks = bind(statement, report["manifest"], report)
    release = build_release(statement, statement_bytes, report, checks)

    staged = parent / f".{destination.name}.staged"
    if staged.exists() or staged.is_symlink():
        raise FormatError(f"a staged release is already in the way: {staged}")
    try:
        staged.mkdir(mode=0o700)
        _copy_fixture(source, staged / FIXTURE_DIRECTORY, report["manifest"])
        copied = verify_fixture(staged / FIXTURE_DIRECTORY)
        if copied["fixture_digest"] != report["fixture_digest"]:
            raise IntegrityError(
                "the fixture copy verifies to "
                f"{copied['fixture_digest']} and the original to "
                f"{report['fixture_digest']}"
            )
        _write_owner_only(staged / STATEMENT_NAME, statement_bytes)
        _write_owner_only(staged / RELEASE_NAME, dumps(release) + b"\n")
        if destination.exists() or destination.is_symlink():
            # Checked again because the copy takes time and the name was free
            # when the run began. This narrows the window rather than closing
            # it: between here and the rename the name is still unheld, and
            # rename replaces an empty directory. Nothing else -- a file, a
            # symlink, a directory holding anything -- can be replaced, so what
            # a lost race costs is an empty directory, and a process that can
            # win it can rewrite the finished release anyway.
            raise FormatError(f"release output appeared while it was built: {destination}")
        os.replace(staged, destination)
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    return release


def verify_release(directory: str | Path) -> dict[str, Any]:
    """Read a release back and check every claim it makes about itself.

    Everything the write did is done again from the bytes on disk: the fixture
    copy is verified, the statement beside it is bound to that verification, and
    the document is held to both. Nothing is taken from the document except the
    two paths it names, because a document checking itself against its own
    numbers checks nothing.

    This is also where the release digest is checked. `validate release` answers
    whether a document is well formed, the way `validate manifest` does; whether
    its digests hold is this question, and it is asked here.
    """
    root = Path(directory)
    release = validate_document(
        "release", loads(_read_inside(root, RELEASE_NAME, "release document"))
    )
    if release["release_digest"] != release_digest(release):
        raise IntegrityError(
            "the release digest does not cover this document; it records "
            f"{release['release_digest']} and the document digests to "
            f"{release_digest(release)}"
        )
    _refuse_unlisted(root, release)

    statement_bytes = _read_inside(
        root, release["statement"]["path"], "statement"
    )
    held = hashlib.sha256(statement_bytes).hexdigest()
    if held != release["statement"]["sha256"]:
        raise IntegrityError(
            f"the statement digests to {held} and the release records "
            f"{release['statement']['sha256']}"
        )
    statement = loads(statement_bytes)

    fixture = confined_directory(root, release["fixture"]["path"])
    report = verify_fixture(fixture)
    if report["fixture_digest"] != release["fixture"]["fixture_digest"]:
        raise IntegrityError(
            f"the fixture verifies to {report['fixture_digest']} and the release "
            f"records {release['fixture']['fixture_digest']}"
        )

    declared = predicate_type_of(statement)
    if declared != release["statement"]["predicate_type"]:
        raise IntegrityError(
            f"the statement is a {declared} and the release records a "
            f"{release['statement']['predicate_type']}"
        )

    checks = bind(statement, report["manifest"], report)
    if checks != release["binding"]["checks"]:
        raise IntegrityError(
            "the release records checks this binding does not make: recorded "
            f"{', '.join(release['binding']['checks'])}; made "
            f"{', '.join(checks)}"
        )

    verified = release["verified"]
    if verified["block_hash"] != report["block_hash"]:
        raise IntegrityError(
            f"the release records block {verified['block_hash']} and the fixture "
            f"verifies to {report['block_hash']}"
        )
    if verified["evidence_counts"] != report["evidence_counts"]:
        raise IntegrityError(
            "the release records evidence counts the fixture does not verify to: "
            f"recorded {verified['evidence_counts']}, verified "
            f"{report['evidence_counts']}"
        )
    # `verified.canonical_chain_claim` is not checked here. The schema pins it to
    # false, so a document claiming it does not get this far, and the binding
    # already refuses a report that claims it. A third check would be a third
    # authority on one question.
    return {
        "release_digest": release["release_digest"],
        "fixture_digest": report["fixture_digest"],
        "block_hash": report["block_hash"],
        "evidence_counts": dict(report["evidence_counts"]),
        "predicate_type": declared,
        "statement_sha256": held,
        "checks": list(checks),
    }


def _read_inside(root: Path, relative: str, what: str) -> bytes:
    """One file from inside a release, through no-follow descriptors."""
    try:
        # read_confined_bytes normalises the path itself, and doing it here as
        # well would be a second authority saying the same thing.
        return read_confined_bytes(root, relative, max_bytes=MAX_JSON_BYTES)
    except PathError as error:
        # Not nested: read_confined_bytes speaks about fixture components, and a
        # release document is not one. The cause is kept on the exception.
        raise PathError(f"cannot read the {what}: {relative}") from error


def _refuse_unlisted(root: Path, release: dict[str, Any]) -> None:
    """A release holds the document, the statement and the fixture, and no more.

    The same rule the fixture manifest applies to its own directory. A file the
    document does not account for is a file a reader has no reason to trust and
    no way to check, sitting inside something whose whole claim is that every
    part of it was checked.
    """
    fixture = validate_relative_path(release["fixture"]["path"]).split("/")[0]
    allowed = {RELEASE_NAME, validate_relative_path(release["statement"]["path"])}
    found: set[str] = set()
    for entry in sorted(Path(root).iterdir()):
        if entry.is_symlink():
            raise PathError(f"release holds a symlink: {entry.name}")
        found.add(entry.name)
    extra = sorted(found - allowed - {fixture})
    if extra:
        raise IntegrityError("release holds files it does not account for: " + ", ".join(extra))


def _refuse_overlap(source: Path, destination: Path) -> None:
    """Neither directory may sit inside the other.

    A release written inside the fixture would be covered by the fixture digest
    it records, and a fixture read from inside the release output would be read
    while it was being written.
    """
    first = source.resolve()
    second = destination.resolve()
    if first == second:
        raise FormatError("release output is the fixture directory")
    if second.is_relative_to(first):
        raise FormatError(
            f"release output {destination} sits inside the fixture it describes"
        )
    if first.is_relative_to(second):
        raise FormatError(
            f"fixture {source} sits inside the release output {destination}"
        )


def _refuse_statement_inside(source: Path, statement_path: str | Path) -> None:
    """A statement about a fixture may not be a file inside it.

    The case refuses itself either way -- an unlisted file fails verification,
    and a listed one would have to carry its own digest, which no file can. Both
    refusals name something else, and a reader chasing a digest mismatch would
    spend a while getting to the reason. The reason is that the fixture digest
    would cover the statement made about the fixture, which is the same rule the
    release document is held to.
    """
    handed = Path(statement_path)
    try:
        resolved = handed.resolve()
        inside = source.resolve()
    except (OSError, RuntimeError) as error:
        # Skipping the check because the path could not be resolved would be the
        # quiet failure this plugin refuses everywhere else. A symlink loop is
        # the case that gets here, and pathlib reports that one as a RuntimeError
        # rather than as the OSError the kernel gave it.
        raise PathError(f"cannot resolve {handed}: {error}") from error
    if resolved.is_relative_to(inside):
        raise FormatError(
            f"statement {handed} sits inside the fixture it describes; the "
            "fixture digest would cover the statement made about it"
        )


def _read_statement(path: str | Path) -> bytes:
    """The statement's bytes, read once, capped, and never re-encoded."""
    handed = Path(path)
    if handed.is_symlink():
        raise PathError(f"statement is a symlink: {handed}")
    if not handed.is_file():
        raise PathError(f"statement is not a regular file: {handed}")
    data = handed.read_bytes()
    if len(data) > MAX_JSON_BYTES:
        raise FormatError(f"statement exceeds {MAX_JSON_BYTES} bytes: {len(data)}")
    return data


def _copy_fixture(source: Path, target: Path, manifest: dict[str, Any]) -> None:
    """Copy the manifest and every component it lists, and nothing else.

    Driven by the verified manifest rather than by walking the directory, so a
    file the manifest does not list cannot ride along into the copy. Verification
    of the source already refused any such file, and this keeps the copy honest
    even if that ever stops being true.
    """
    target.mkdir(mode=0o700, parents=True)
    for relative in [MANIFEST_NAME] + [
        entry["path"] for entry in manifest["components"]
    ]:
        normalised = validate_relative_path(relative)
        data = read_confined_bytes(
            source, normalised, max_bytes=MAX_COMPONENT_BYTES
        )
        written = target / normalised
        written.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _write_owner_only(written, data)


def _write_owner_only(path: Path, data: bytes) -> None:
    """Write a new file the owner can read and nobody else can.

    The same mode `atomic_write_confined` uses for a fixture component. A release
    is not published by being written; whoever wants to hand it over opens it up
    deliberately.
    """
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
