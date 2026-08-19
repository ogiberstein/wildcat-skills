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
from .paths import read_confined_bytes, validate_relative_path
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

    statement_bytes = _read_statement(statement_path)
    statement = loads(statement_bytes)
    if not isinstance(statement, dict):
        raise FormatError("statement must be a JSON object")

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
        (staged / STATEMENT_NAME).write_bytes(statement_bytes)
        (staged / RELEASE_NAME).write_bytes(dumps(release) + b"\n")
        os.replace(staged, destination)
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    return release


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
        written.write_bytes(data)
