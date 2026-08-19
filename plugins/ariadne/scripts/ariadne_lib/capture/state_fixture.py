"""Read a Lazarus fixture directory into a statement.

A capture reads what is already there rather than producing it, so what ends up in
the statement is what the fixture actually contains. Nothing here reaches a network,
and nothing here guesses.

The evidence counts are the point. They come from the manifest verbatim, because
Lazarus wrote them and Lazarus is the only thing that knows which of its records were
checked against the state root. Recomputing them here would mean reimplementing that
judgement from the files, and a capture that recomputed one and got a larger number
would upgrade recorded evidence into proved evidence -- the one thing Lazarus's own
skill forbids outright. So the counts are read, the manifest digest is checked, and a
manifest that disagrees with its own directory is refused rather than corrected.

What the caller supplies, and why the files cannot answer it:

- **The tool name.** The manifest carries a `tool_version` and does not name the
  tool that wrote it. Reading a Lazarus-shaped manifest and writing "lazarus" into
  the field gate 2 reads as the thing that made the fixture would be this capture
  asserting something nobody recorded. The version comes from the manifest, and a
  version supplied by the caller that disagrees with it is refused.
- **The command.** The argv that produced the fixture is not in the fixture.
- **A previous capture, or the reason there is none.** Same as every other predicate
  here: a first capture carries a null baseline and says why.

What the caller cannot supply:

- **`reaches_network` and `canonical_chain_claim`.** Both are written false and
  neither is a parameter. Ariadne reaches no network, and neither tool re-derives a
  chain, so the honest value is the only value and offering a flag would imply
  otherwise.
"""

import json
import os
import tempfile

from .. import digests
from ..predicates import state_fixture as predicate
from . import tree
from .tree import CaptureError, confined

MANIFEST = "manifest.json"
HEADER = "header.json"

MAX_MANIFEST_BYTES = 4 * 1024 * 1024
"""A manifest listing a thousand components is a few hundred kilobytes. A cap keeps
a mistaken path from reading a multi-gigabyte file into memory to parse it."""

MANIFEST_REQUIRED = (
    "schema_version",
    "tool_version",
    "chain_id",
    "block",
    "components",
    "evidence_counts",
    "fixture_digest",
)
"""What this capture reads out of a manifest, which is a subset of what Lazarus's own
schema requires. `optional_failures` is required there and not read here, because
nothing in this predicate carries it."""

SCHEMA_VERSION = 1
"""The one manifest version this capture understands. A later one may spell the
evidence counts differently, and reading it as though it did not would be the
upgrade this capture exists to refuse."""


def refuse_constant(token):
    """Refuse `NaN`, `Infinity` and `-Infinity`, which `json.loads` accepts.

    They are a Python extension rather than JSON, and every comparison against a
    `nan` is false including `!=`, so one reaching a count would be neither refused
    nor ordered.
    """
    raise CaptureError(
        "manifest carries %s, which is not JSON; every comparison against it is "
        "false, including one that would refuse it" % token
    )


def read_json(path, what):
    """One document from the fixture, read with a cap and no extensions."""
    try:
        size = os.path.getsize(path)
    except OSError as error:
        raise CaptureError("cannot read %s: %s" % (what, error))
    if size > MAX_MANIFEST_BYTES:
        raise CaptureError(
            "%s is %d bytes, over the %d this capture will read"
            % (what, size, MAX_MANIFEST_BYTES)
        )
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as error:
        raise CaptureError("cannot read %s: %s" % (what, error))
    try:
        found = json.loads(raw.decode("utf-8"), parse_constant=refuse_constant)
    except UnicodeDecodeError as error:
        raise CaptureError("%s is not UTF-8: %s" % (what, error))
    except ValueError as error:
        raise CaptureError("%s is not JSON: %s" % (what, error))
    if not isinstance(found, dict):
        raise CaptureError(
            "%s is a %s rather than an object" % (what, type(found).__name__)
        )
    return found


def quantity(value, what):
    """A hex quantity string from the wire, as the integer this predicate compares.

    `"0xc7da16" < "0x2"` is true, because that orders text. The predicate refuses the
    wire form for that reason, so the conversion happens here or not at all.
    """
    if not isinstance(value, str) or not value.startswith("0x"):
        raise CaptureError(
            "%s must be a 0x-prefixed hex quantity, got %r" % (what, value)
        )
    body = value[2:]
    if not body or not all(character in "0123456789abcdef" for character in body):
        raise CaptureError(
            "%s must be lowercase hex after the prefix, got %r" % (what, value)
        )
    if len(body) > 1 and body[0] == "0":
        # Lazarus's own schema refuses a leading zero, and two spellings of one
        # number would give two statements for one fixture.
        raise CaptureError(
            "%s has a leading zero, which is two spellings of one number: %r"
            % (what, value)
        )
    return int(body, 16)


def hash32(value, what):
    """A 32-byte hash, lowercased for the predicate and refused if it is unset.

    Lazarus accepts either case for a block hash and this predicate accepts only
    lowercase, because two spellings of one value compare unequal. Lowercasing here
    is a conversion between two things that are the same. The all-zero value is not
    lowercased into acceptability: it matches the shape and identifies nothing.
    """
    if not isinstance(value, str):
        raise CaptureError("%s must be a string, got %s" % (what, type(value).__name__))
    lowered = value.lower()
    if not predicate.hash32(lowered):
        raise CaptureError(
            "%s is not a 32-byte hash that identifies something: %r" % (what, value)
        )
    return lowered


def manifest_of(root):
    """The manifest, checked for the fields this capture reads."""
    path = os.path.join(root, MANIFEST)
    if not os.path.isfile(path):
        raise CaptureError(
            "fixture %s has no %s; a fixture directory is one Lazarus wrote"
            % (root, MANIFEST)
        )
    found = read_json(path, MANIFEST)
    absent = [field for field in MANIFEST_REQUIRED if field not in found]
    if absent:
        raise CaptureError("%s is missing %s" % (MANIFEST, ", ".join(absent)))
    if found["schema_version"] != SCHEMA_VERSION:
        raise CaptureError(
            "%s is schema_version %r and this capture reads %d; a later manifest may "
            "spell the evidence counts differently"
            % (MANIFEST, found["schema_version"], SCHEMA_VERSION)
        )
    if not isinstance(found["tool_version"], str) or not found["tool_version"].strip():
        raise CaptureError("%s tool_version names no version" % MANIFEST)
    if not isinstance(found["block"], dict):
        raise CaptureError("%s block must be an object" % MANIFEST)
    for field in ("number", "hash"):
        if field not in found["block"]:
            raise CaptureError("%s block is missing %s" % (MANIFEST, field))
    if not isinstance(found["components"], list) or not found["components"]:
        raise CaptureError("%s components must be a non-empty array" % MANIFEST)
    return found


def state_root_of(root):
    """The state root, from the header Lazarus captured.

    Absent is not fatal here. A capture that proved nothing against the trie has no
    use for a root, and the predicate's evidence check is what refuses a proof-backed
    count without one. Refusing here would refuse an honest fixture.
    """
    path = os.path.join(root, HEADER)
    if not os.path.isfile(path):
        return None
    header = read_json(path, HEADER)
    if "state_root" not in header:
        return None
    return hash32(header["state_root"], "%s state_root" % HEADER)


def evidence_of(manifest):
    """The three counts, read from the manifest and not recomputed.

    Recomputing one would mean deciding for Lazarus which of its records were checked
    against the state root, and a capture that decided a larger number would upgrade
    recorded evidence into proved evidence. Reading them keeps the judgement where it
    was made, and the predicate's own check is what refuses a count the pin cannot
    support.
    """
    counts = manifest["evidence_counts"]
    if not isinstance(counts, dict):
        raise CaptureError("%s evidence_counts must be an object" % MANIFEST)
    unknown = sorted(set(counts) - set(predicate.EVIDENCE_CLASSES))
    if unknown:
        raise CaptureError(
            "%s evidence_counts carries %s, which is not a class this predicate "
            "defines; a count in an unknown class is a count nobody can read"
            % (MANIFEST, ", ".join(unknown))
        )
    out = {}
    for name in predicate.EVIDENCE_CLASSES:
        if name not in counts:
            raise CaptureError(
                "%s evidence_counts has no %s; a class left out reads as nothing of "
                "that kind rather than as nobody having said" % (MANIFEST, name)
            )
        value = counts[name]
        if not predicate.whole_number(value) or not 0 <= value <= predicate.MAX_COUNT:
            raise CaptureError(
                "%s evidence_counts %s must be a whole number of records from 0 to "
                "%d, got %r" % (MANIFEST, name, predicate.MAX_COUNT, value)
            )
        out[name] = value
    return out


def components_of(root, manifest):
    """One entry per component the manifest declares, checked against the directory.

    Both directions. A component the manifest declares and the directory lacks is a
    statement describing a file nobody has; a file the directory holds and the
    manifest does not declare is a file the fixture digest does not cover, which is
    the silent absence every other refusal here exists for.
    """
    declared = {}
    for index, entry in enumerate(manifest["components"]):
        label = "component %d" % (index + 1)
        if not isinstance(entry, dict):
            raise CaptureError("%s %s is not an object" % (MANIFEST, label))
        for field in ("path", "bytes", "sha256"):
            if field not in entry:
                raise CaptureError("%s %s is missing %s" % (MANIFEST, label, field))
        path = entry["path"]
        if not predicate.usable_path(path):
            raise CaptureError(
                "%s %s path %r is not a fixture-relative path; a reader resolving it "
                "against the fixture would land outside it" % (MANIFEST, label, path)
            )
        if path in declared:
            raise CaptureError(
                "%s declares %s twice; one file cannot carry two digests, and the "
                "fixture digest is over this listing" % (MANIFEST, path)
            )
        if not predicate.whole_number(entry["bytes"]) or entry["bytes"] < 0:
            raise CaptureError(
                "%s %s bytes must be a whole number of bytes, got %r"
                % (MANIFEST, label, entry["bytes"])
            )
        if not isinstance(entry["sha256"], str):
            raise CaptureError(
                "%s %s sha256 must be a string, got %s"
                % (MANIFEST, label, type(entry["sha256"]).__name__)
            )
        declared[path] = entry

    present = dict(tree.files(root, "fixture"))
    missing = sorted(set(declared) - set(present))
    if missing:
        raise CaptureError(
            "%s declares %s, which the fixture does not hold"
            % (MANIFEST, ", ".join(missing))
        )
    # The manifest is one of the files, and it cannot list its own digest.
    undeclared = sorted(set(present) - set(declared) - {MANIFEST})
    if undeclared:
        raise CaptureError(
            "fixture holds %s, which %s does not declare; the fixture digest would "
            "not cover it and nothing would say so"
            % (", ".join(undeclared), MANIFEST)
        )

    out = []
    for path in sorted(declared):
        entry = declared[path]
        absolute = present[path]
        found = digests.of_file(absolute)
        if found["sha256"] != entry["sha256"]:
            raise CaptureError(
                "%s says %s digests to %s and it digests to %s; a manifest that "
                "disagrees with its own directory is not a fixture this will "
                "describe" % (MANIFEST, path, entry["sha256"], found["sha256"])
            )
        size = os.path.getsize(absolute)
        if size != entry["bytes"]:
            raise CaptureError(
                "%s says %s is %d bytes and it is %d"
                % (MANIFEST, path, entry["bytes"], size)
            )
        out.append({"name": path, "path": path, "digest": found, "bytes": size})
    return out


def parameters_digest(parameters):
    """A digest over the parameters this capture was given, canonically serialised."""
    return digests.of_bytes(
        json.dumps(dict(parameters or {}), sort_keys=True).encode("utf-8")
    )


def bundle(entries):
    """One digest over the whole component listing.

    Both sides of a delta name this rather than one component's digest, because a
    comparison is about the fixture and not about its manifest.

    The manifest's own `fixture_digest` is not used for this. It is Lazarus's digest
    over Lazarus's listing, computed a way this tool has not reimplemented, and
    presenting it as the digest of what Ariadne read would be asserting a derivation
    nobody here performed.
    """
    return digests.of_bytes(
        json.dumps(
            [[entry["path"], entry["digest"]] for entry in entries], sort_keys=True
        ).encode("utf-8")
    )


def claim(name, subject, disposition, reason=None, detail=None):
    out = {"name": name, "subject": subject, "disposition": disposition}
    if reason:
        out["reason"] = reason
    if detail:
        out["detail"] = detail
    return out


def capture(
    fixture,
    name,
    capture_tool,
    capture_command,
    capture_version=None,
    parameters=None,
    previous=None,
    previous_name=None,
    first_capture_reason=None,
):
    """A state-fixture statement, read from a Lazarus fixture directory on disk."""
    if not isinstance(capture_tool, str) or not capture_tool.strip():
        raise CaptureError(
            "--capture-tool is required; the manifest carries a version and does not "
            "name the tool that wrote it, and gate 2 reads this field as the thing "
            "that made the fixture"
        )
    if not capture_command or not all(
        isinstance(word, str) and word.strip() for word in capture_command
    ):
        raise CaptureError(
            "--capture-command is required, as an argv nobody has to guess at"
        )
    if not isinstance(name, str) or not name.strip():
        raise CaptureError(
            "--name is required; it identifies the current side of the comparison "
            "and names the fixture among the statement's subjects"
        )

    root = confined(fixture, "fixture")
    manifest = manifest_of(root)
    if capture_version is not None and capture_version != manifest["tool_version"]:
        raise CaptureError(
            "--capture-version says %r and %s says %r; the manifest is what the tool "
            "wrote" % (capture_version, MANIFEST, manifest["tool_version"])
        )

    entries = components_of(root, manifest)
    current = bundle(entries)
    state_root = state_root_of(root)
    evidence = evidence_of(manifest)

    chain = {
        "chain_id": quantity(manifest["chain_id"], "%s chain_id" % MANIFEST),
        "block_number": quantity(
            manifest["block"]["number"], "%s block number" % MANIFEST
        ),
        "block_hash": hash32(manifest["block"]["hash"], "%s block hash" % MANIFEST),
    }
    if state_root is not None:
        chain["state_root"] = state_root

    if previous:
        if not previous_name:
            raise CaptureError("--previous needs --previous-name to identify it")
        previous_root = confined(previous, "previous fixture")
        if previous_root == root:
            raise CaptureError(
                "--previous is the same directory as --fixture; a comparison against "
                "itself records nothing"
            )
        previous_manifest = manifest_of(previous_root)
        deltas = {
            "baseline": {
                "name": previous_name,
                "digest": bundle(components_of(previous_root, previous_manifest)),
            },
            "current": {"name": name, "digest": current},
        }
    else:
        if not isinstance(first_capture_reason, str) or not first_capture_reason.strip():
            raise CaptureError(
                "a fixture with no --previous needs --first-capture-reason; a null "
                "baseline carries the reason there is nothing to compare against"
            )
        deltas = {
            "baseline": None,
            "current": {"name": name, "digest": current},
            "reason": first_capture_reason,
        }

    claims = [
        claim(
            "digest and byte count read from the component on disk",
            entry["digest"],
            "passed",
            detail={"path": entry["path"], "bytes": entry["bytes"]},
        )
        for entry in entries
    ]
    claims.append(
        claim(
            "evidence counts read from the manifest",
            current,
            "passed",
            detail=dict(evidence),
        )
    )
    if evidence[predicate.PROVED] and state_root is None:
        # Unreachable through the predicate, which refuses the statement, but the
        # claim is written before the statement is verified and a reader of the
        # capture's output should see why it will fail.
        claims.append(
            claim(
                "state proofs checked against the pinned root",
                current,
                "failed",
                reason=(
                    "the manifest counts proof-backed records and the fixture "
                    "carries no state root to have proved them against"
                ),
            )
        )
    else:
        claims.append(
            claim(
                "state proofs re-checked by this capture",
                current,
                "skipped",
                reason=(
                    "this capture reads what Lazarus recorded and does not re-verify "
                    "a trie proof; the counts come from the manifest and re-deriving "
                    "one would put a judgement in the statement that Ariadne did not "
                    "make"
                ),
            )
        )
    claims.append(
        claim(
            "the pinned block placed on the canonical chain",
            current,
            "skipped",
            reason=(
                "neither tool re-derives a chain, so whether this block is canonical "
                "is not established here"
            ),
        )
    )
    if previous:
        claims.append(
            claim(
                "component-level comparison against the baseline",
                current,
                "skipped",
                reason=(
                    "both sides are identified by digest and no per-component "
                    "difference is recorded, because naming one needs a component "
                    "identity across two captures that this tool does not have"
                ),
            )
        )

    body = {
        "chain": chain,
        "capture": {
            "tool": capture_tool,
            "tool_version": manifest["tool_version"],
            "command": list(capture_command),
            "parameters_digest": parameters_digest(parameters),
        },
        "fixture_subjects": entries,
        "evidence": evidence,
        "replay": {"reaches_network": False, "canonical_chain_claim": False},
        "deltas": deltas,
        "claims": claims,
        "commands": [],
    }

    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": entry["name"], "digest": entry["digest"]} for entry in entries
        ]
        + [{"name": name, "digest": current}],
        "predicateType": predicate.TYPE,
        "predicate": body,
    }


def write(path, body):
    """Write a statement so a reader never sees half of one.

    The temporary file lands in the same directory so the replace is on one
    filesystem.
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
