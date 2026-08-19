"""Read a dataset release on disk into a statement.

A capture reads what is already there rather than producing it, so what ends up
in the statement is what the release actually contains. Nothing here reaches a
network, and nothing here guesses.

Three things the caller has to supply, because the files cannot answer them:

- **Coverage.** A directory of records does not say which interval it was meant
  to describe, so it cannot say where it falls short of one. Both bounds and
  every gap come from the caller.
- **Inputs.** What a release was derived from is not recoverable from the
  release. An input is named with a digest, or recorded absent with a reason.
- **Record counts, except for line-delimited JSON.** One record per line is
  unambiguous, so `.jsonl` and `.ndjson` are counted here. Every other format
  needs the count stated, and a file whose count is neither derivable nor stated
  is refused rather than guessed at.

Record-level deltas are never computed here. Telling which records changed
between two releases needs a record identity this tool does not have, and
inventing one would put a difference in the statement that nobody established.
With `--previous`, both sides are identified and the comparison records no
differences, and a skipped claim says why.
"""

import json
import os
import tempfile

from .. import digests
from ..predicates import dataset as predicate

MAX_RELEASE_FILES = 4096
"""A release is somebody's output directory rather than a stranger's archive, but
a cap keeps a mistaken `--release /` from walking a filesystem."""

LINE_DELIMITED = (".jsonl", ".ndjson")
"""Formats where one record per line is the format, not an assumption."""

REFUSED_NAMES = frozenset({".git", "__pycache__"})
"""Directories that have no business in a data release.

Skipping them quietly would be the silent absence this whole tool refuses: the
bundle digest would cover part of the tree while the statement said nothing about
the rest. Refusing says which directory to remove, and the caller decides.
"""


class CaptureError(ValueError):
    """A release that cannot be captured, with the reason a caller can act on."""


def confined(path, what):
    """Resolve a directory, refusing anything that is not one.

    `realpath` collapses `..` and follows symlinks, so the resolved path is what
    every later containment check compares against.
    """
    if not path:
        raise CaptureError("%s is required" % what)
    resolved = os.path.realpath(path)
    if not os.path.isdir(resolved):
        raise CaptureError("%s %s is not a directory" % (what, path))
    return resolved


def inside(root, path, what):
    """The resolved path, or a refusal when it leaves the root.

    A symlink inside the release pointing out of it is the case this catches:
    the file reads fine, and its digest would describe something the release does
    not contain.
    """
    resolved = os.path.realpath(path)
    try:
        shared = os.path.commonpath([root, resolved])
    except ValueError as error:
        raise CaptureError("%s %s: cannot place it inside %s (%s)" % (what, path, root, error))
    if shared != root:
        raise CaptureError("%s %s resolves outside the release" % (what, path))
    return resolved


def files(root):
    """Every file in the release, as (relative path, absolute path), sorted.

    Sorted because the statement has to come out the same way twice.

    Nothing is skipped. `os.walk` does not descend a symlinked directory, so
    leaving one in place would drop everything under it from both the statement
    and the bundle digest, with nothing recording that anything was dropped. That
    is the silent absence the gates exist to refuse, so a symlinked directory is
    refused here instead.
    """
    found = []
    for directory, names, entries in os.walk(root):
        for name in sorted(names):
            here = os.path.join(directory, name)
            shown = os.path.relpath(here, root)
            if name in REFUSED_NAMES:
                raise CaptureError(
                    "release holds %s; remove it or name a directory that holds "
                    "only the release" % shown
                )
            if os.path.islink(here):
                raise CaptureError(
                    "%s is a symlink to a directory; its contents would be left "
                    "out of the statement and out of the release digest without "
                    "anything saying so" % shown
                )
        names[:] = sorted(names)
        for name in sorted(entries):
            absolute = os.path.join(directory, name)
            relative = os.path.relpath(absolute, root)
            found.append((relative, absolute))
            if len(found) > MAX_RELEASE_FILES:
                raise CaptureError(
                    "release holds more than %d files; name a narrower directory"
                    % MAX_RELEASE_FILES
                )
    if not found:
        raise CaptureError("release %s holds no files" % root)
    return found


def line_count(path):
    """Non-empty lines in a file, read in blocks rather than whole.

    A release file is larger than a build artefact, sometimes by orders of
    magnitude, so nothing here holds one in memory.
    """
    total = 0
    partial = False
    try:
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(65536), b""):
                total += block.count(b"\n")
                partial = not block.endswith(b"\n")
    except OSError as error:
        raise CaptureError("cannot read %s: %s" % (path, error))
    if partial:
        # A final record with no trailing newline is still a record.
        total += 1
    return total


def record_count(relative, absolute, stated):
    """The count for one file: stated by the caller, or derived where it can be."""
    if relative in stated:
        return stated[relative]
    if os.path.splitext(relative)[1].lower() in LINE_DELIMITED:
        return line_count(absolute)
    raise CaptureError(
        "%s is not line-delimited JSON, so its record count cannot be derived; "
        "state it with --record-count %s=<n>" % (relative, relative)
    )


def subjects(root, stated_counts):
    """One entry per released file, digested and counted."""
    out = []
    for relative, absolute in files(root):
        inside(root, absolute, "release file")
        if os.path.islink(absolute):
            raise CaptureError(
                "%s is a symlink; a digest over its target would describe "
                "something the release does not contain" % relative
            )
        out.append(
            {
                "name": relative,
                "path": relative,
                "digest": digests.of_file(absolute),
                "record_count": record_count(relative, absolute, stated_counts),
            }
        )
    return out


def bundle(entries):
    """One digest over a whole release.

    Both sides of a delta name this rather than one file's digest. With more than
    one file, picking the first would name an artefact the comparison is only
    partly about.
    """
    return digests.of_bytes(
        json.dumps(
            [[entry["name"], entry["digest"]] for entry in sorted(entries, key=lambda e: e["name"])],
            sort_keys=True,
        ).encode("utf-8")
    )


def parameters_digest(parameters):
    """A digest over the producer's parameters, canonically serialised.

    Sorted keys, so the same parameters give the same digest whatever order they
    arrived in.
    """
    return digests.of_bytes(
        json.dumps(dict(parameters or {}), sort_keys=True).encode("utf-8")
    )


def coverage(dimension, start, end, gaps):
    """The coverage block, with the gaps the caller recorded.

    An empty gap list is written rather than omitted. The predicate refuses an
    absent `gaps` key on purpose, because that is the difference between a
    producer who looked and one who did not.
    """
    if not dimension:
        raise CaptureError("a coverage dimension is required")
    for name, value in (("start", start), ("end", end)):
        if not predicate.whole_number(value):
            raise CaptureError("coverage %s must be a whole number, got %r" % (name, value))
    if start > end:
        raise CaptureError("coverage starts at %d and ends at %d" % (start, end))
    out = {"dimension": dimension, "start": start, "end": end, "gaps": []}
    for entry in gaps or ():
        for field in ("start", "end", "reason"):
            if field not in entry:
                raise CaptureError("a gap needs %s" % field)
        if not predicate.whole_number(entry["start"]) or not predicate.whole_number(entry["end"]):
            raise CaptureError("gap bounds must be whole numbers")
        if entry["start"] > entry["end"]:
            raise CaptureError(
                "a gap starts at %d and ends at %d" % (entry["start"], entry["end"])
            )
        if entry["start"] < start or entry["end"] > end:
            raise CaptureError(
                "a gap runs %d to %d, outside the coverage %d to %d"
                % (entry["start"], entry["end"], start, end)
            )
        out["gaps"].append(
            {"start": entry["start"], "end": entry["end"], "reason": entry["reason"]}
        )
    return out


def claim(name, subject, disposition, reason=None, detail=None):
    out = {"name": name, "subject": subject, "disposition": disposition}
    if reason:
        out["reason"] = reason
    if detail:
        out["detail"] = detail
    return out


def capture(
    release,
    name,
    coverage_dimension,
    coverage_start,
    coverage_end,
    gaps=None,
    inputs=None,
    producer_tool="ariadne",
    producer_version=None,
    producer_command=None,
    parameters=None,
    record_counts=None,
    previous=None,
    previous_name=None,
    first_release_reason=None,
):
    """A dataset release statement, read from a release directory on disk."""
    root = confined(release, "release")
    entries = subjects(root, dict(record_counts or {}))
    current = bundle(entries)

    if previous:
        if not previous_name:
            raise CaptureError("--previous needs --previous-name to identify it")
        previous_root = confined(previous, "previous release")
        baseline = {
            "name": previous_name,
            "digest": bundle(subjects(previous_root, dict(record_counts or {}))),
        }
        deltas = {"baseline": baseline, "current": {"name": name, "digest": current}}
    else:
        if not first_release_reason:
            raise CaptureError(
                "a release with no --previous needs --first-release-reason; a null "
                "baseline carries the reason there is nothing to compare against"
            )
        deltas = {
            "baseline": None,
            "current": {"name": name, "digest": current},
            "reason": first_release_reason,
        }

    claims = [
        claim(
            "digest and record count read from the released file",
            entry["digest"],
            "passed",
            detail="%s, %d record(s)" % (entry["path"], entry["record_count"]),
        )
        for entry in entries
    ]
    if previous:
        claims.append(
            claim(
                "record-level comparison against the baseline",
                current,
                "skipped",
                reason=(
                    "telling which records changed needs a record identity this "
                    "capture does not have, so both sides are identified and no "
                    "differences are recorded"
                ),
            )
        )

    body = {
        "producer": {
            "tool": producer_tool,
            "tool_version": producer_version or "unstated",
            "command": list(producer_command or ["ariadne", "capture-dataset"]),
            "parameters_digest": parameters_digest(parameters),
        },
        "inputs": list(inputs or []),
        "dataset_subjects": entries,
        "coverage": coverage(coverage_dimension, coverage_start, coverage_end, gaps),
        "deltas": deltas,
        "claims": claims,
        "commands": [],
    }

    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": entry["name"], "digest": entry["digest"]} for entry in entries]
        + [{"name": name, "digest": current}],
        "predicateType": predicate.TYPE,
        "predicate": body,
    }


def write(path, body):
    """Write a statement so a reader never sees half of one.

    A capture that died mid-write used to leave a truncated file where the next
    run would read it as complete. The temporary file lands in the same directory
    so the replace is on one filesystem.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    handle = tempfile.NamedTemporaryFile(
        mode="w", dir=directory, prefix=".ariadne-", suffix=".tmp", delete=False
    )
    try:
        with handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
