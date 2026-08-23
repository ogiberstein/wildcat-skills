#!/usr/bin/env python3
"""Render and check bounded, deterministic views of Fiat audit logs."""

import argparse
import contextlib
import datetime
import hashlib
import os
import posixpath
import re
import secrets
import stat
import sys


SYNOPSIS_SCHEMA = "fiat-audit-synopsis/v1"
AUDIT_SCHEMA = "fiat-audit-round/v1"
SOURCE_NAME = "AUDIT.md"
SYNOPSIS_NAME = "AUDIT_SYNOPSIS.md"
SOURCE_BYTES_MAX = 16 * 1024 * 1024
H2_RECORDS_MAX = 10_000
PHYSICAL_LINE_BYTES_MAX = 1024 * 1024
FINDINGS_HEADER = "| id | severity | file | finding | status |"
FINDINGS_SEPARATOR = "| --- | --- | --- | --- | --- |"
ZERO_FINDING_ROW = "| -- | -- | -- | none | -- |"
ELENCHUS_VERDICTS = ("guarded", "unguarded", "passed", "inconclusive", "null")
COVERAGE_VALUES = ("reviewed", "not-applicable")
STRICT_HEADING_RE = re.compile(
    r"## .+, step [1-9][0-9]*, round [1-9][0-9]* -- "
    r"(?P<timestamp>[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z)",
    re.ASCII,
)
OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd
UNLINK_SUPPORTS_DIR_FD = os.unlink in os.supports_dir_fd


class SynopsisError(Exception):
    """A bounded refusal safe to show without source content."""


def _root_path(supplied):
    try:
        lexical = os.path.abspath(os.fspath(supplied))
        os.fsencode(lexical)
        info = os.lstat(lexical)
    except (OSError, TypeError, ValueError, UnicodeError):
        raise SynopsisError("repository root is not a readable directory") from None
    if stat.S_ISLNK(info.st_mode):
        raise SynopsisError("repository root is a symlink")
    if not stat.S_ISDIR(info.st_mode):
        raise SynopsisError("repository root is not a directory")
    real = os.path.realpath(lexical)
    return real


def _relative_path(relative):
    if not isinstance(relative, str) or not relative:
        raise SynopsisError("path must be a non-empty repository-relative string")
    try:
        os.fsencode(relative)
    except (ValueError, UnicodeError):
        raise SynopsisError("path is not a valid filesystem path") from None
    if os.path.isabs(relative) or "\\" in relative:
        raise SynopsisError(f"path escapes repository: {relative!r}")
    normal = posixpath.normpath(relative)
    if normal in ("", ".", "..") or normal.startswith("../"):
        raise SynopsisError(f"path escapes repository: {relative!r}")
    if normal != relative:
        raise SynopsisError(f"path is not canonical: {relative!r}")
    return normal


def _directory_descriptor(root, components, label):
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_only = getattr(os, "O_DIRECTORY", 0)
    if not no_follow or not directory_only or not OPEN_SUPPORTS_DIR_FD:
        raise SynopsisError(f"platform cannot safely access {label}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | no_follow | directory_only
    descriptor = None
    try:
        descriptor = os.open(root, flags)
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise SynopsisError("repository root changed kind during access")
        for component in components:
            child = None
            try:
                child = os.open(component, flags, dir_fd=descriptor)
                if not stat.S_ISDIR(os.fstat(child).st_mode):
                    raise SynopsisError(f"{label} has a non-directory component")
                os.close(descriptor)
                descriptor = child
                child = None
            finally:
                if child is not None:
                    with contextlib.suppress(OSError):
                        os.close(child)
        return descriptor
    except OSError:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        raise SynopsisError(f"{label} cannot be accessed") from None
    except Exception:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        raise


def read_regular_bytes(root, relative, label, *, missing_ok=False):
    """Read one contained regular file once through a no-follow descriptor walk."""
    root = _root_path(root)
    relative = _relative_path(relative)
    components = relative.split("/")
    lexical = os.path.join(root, *components)
    try:
        info = os.lstat(lexical)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise SynopsisError(f"{label} is missing: {relative}") from None
    except OSError:
        raise SynopsisError(f"{label} cannot be inspected: {relative}") from None
    if stat.S_ISLNK(info.st_mode):
        raise SynopsisError(f"{label} is a symlink: {relative}")
    if not stat.S_ISREG(info.st_mode):
        raise SynopsisError(f"{label} is not a regular file: {relative}")
    if os.path.realpath(lexical) != lexical:
        raise SynopsisError(f"{label} traverses a symlink: {relative}")

    no_follow = getattr(os, "O_NOFOLLOW", 0)
    non_blocking = getattr(os, "O_NONBLOCK", 0)
    if not no_follow or not non_blocking:
        raise SynopsisError(f"platform cannot safely read {label}")
    parent = _directory_descriptor(root, components[:-1], label)
    descriptor = None
    try:
        descriptor = os.open(
            components[-1],
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | no_follow | non_blocking,
            dir_fd=parent,
        )
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise SynopsisError(f"{label} is not a regular file: {relative}")
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise SynopsisError(f"{label} changed during access: {relative}")
        chunks = []
        remaining = SOURCE_BYTES_MAX + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
    except OSError:
        raise SynopsisError(f"{label} cannot be read: {relative}") from None
    finally:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        with contextlib.suppress(OSError):
            os.close(parent)
    if len(data) > SOURCE_BYTES_MAX:
        raise SynopsisError(
            f"{label} exceeds {SOURCE_BYTES_MAX:,}-byte cap: {relative}"
        )
    return data


def _physical_lines(source_path, data):
    if len(data) > SOURCE_BYTES_MAX:
        raise SynopsisError(
            f"{source_path}: source exceeds {SOURCE_BYTES_MAX:,}-byte cap"
        )
    raw_lines = data.split(b"\n")
    if data.endswith(b"\n"):
        raw_lines.pop()
    if not data:
        raw_lines = []
    for number, line in enumerate(raw_lines, 1):
        if len(line) > PHYSICAL_LINE_BYTES_MAX:
            raise SynopsisError(
                f"{source_path}: physical line {number} exceeds "
                f"{PHYSICAL_LINE_BYTES_MAX:,}-byte cap"
            )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise SynopsisError(f"{source_path}: source is not UTF-8") from None
    lines = text.split("\n")
    if text.endswith("\n"):
        lines.pop()
    if not text:
        lines = []
    return lines


def _is_h2(line):
    return line == "##" or line.startswith("## ")


def _table_cells(line):
    trailing_slashes = len(line) - 1 - len(line[:-1].rstrip("\\"))
    if (
        len(line) < 2
        or not line.startswith("|")
        or not line.endswith("|")
        or trailing_slashes % 2
    ):
        return []
    cells = [""]
    slashes = 0
    for character in line[1:-1]:
        if character == "|" and slashes % 2 == 0:
            cells.append("")
        else:
            cells[-1] += character
        slashes = slashes + 1 if character == "\\" else 0
    return [cell.strip() for cell in cells]


def _field(line, label, record_number, source_path):
    prefix = f"{label}: "
    if not line.startswith(prefix):
        raise SynopsisError(
            f"{source_path}: strict record {record_number} is missing {label}"
        )
    value = line[len(prefix):]
    if not value or value != value.strip():
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed {label}"
        )
    return value


def _strict_candidate(record):
    if any(line.startswith("###") for line in record[1:]):
        return False
    markers = (
        "Audit schema: ",
        "Covered: ",
        "Not checked: ",
        "Elenchus verdict: ",
        FINDINGS_HEADER,
    )
    has_schema = any(line.startswith(markers[0]) for line in record[1:])
    has_strict_shape = STRICT_HEADING_RE.fullmatch(record[0]) is not None and any(
        any(line.startswith(marker) for marker in markers[1:4])
        or line == FINDINGS_HEADER
        for line in record[1:]
    )
    return has_schema or has_strict_shape


def _strict_lines(record, record_number, source_path):
    record = list(record)
    if record and record[-1] == "":
        record.pop()
    match = STRICT_HEADING_RE.fullmatch(record[0])
    if match is None:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed heading"
        )
    timestamp = match.group("timestamp")
    try:
        parsed = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has invalid UTC timestamp"
        ) from None
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != timestamp:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has non-canonical timestamp"
        )

    def exact(index, expected, label):
        if index >= len(record) or record[index] != expected:
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has malformed {label}"
            )
        return index + 1

    index = exact(1, "", "heading separator")
    if index >= len(record):
        raise SynopsisError(f"{source_path}: strict record {record_number} is truncated")
    schema = _field(record[index], "Audit schema", record_number, source_path)
    if schema != AUDIT_SCHEMA:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has unsupported schema"
        )
    index = exact(index + 1, "", "Audit schema separator")
    if index >= len(record):
        raise SynopsisError(f"{source_path}: strict record {record_number} is truncated")
    covered = _field(record[index], "Covered", record_number, source_path)
    dispositions = {}
    for raw in covered.split(";"):
        item = raw.strip()
        if item.count("=") != 1:
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has malformed Covered"
            )
        risk_id, value = (part.strip() for part in item.split("=", 1))
        if (
            not re.fullmatch(r"[a-z0-9][a-z0-9-]*", risk_id)
            or risk_id in dispositions
            or value not in COVERAGE_VALUES
        ):
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has malformed Covered"
            )
        dispositions[risk_id] = value
    if not dispositions:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed Covered"
        )
    index = exact(index + 1, "", "Covered separator")
    if index >= len(record):
        raise SynopsisError(f"{source_path}: strict record {record_number} is truncated")
    _field(record[index], "Not checked", record_number, source_path)
    index = exact(index + 1, "", "Not checked separator")
    if index >= len(record):
        raise SynopsisError(f"{source_path}: strict record {record_number} is truncated")
    verdict = _field(record[index], "Elenchus verdict", record_number, source_path)
    if verdict not in ELENCHUS_VERDICTS:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has invalid Elenchus verdict"
        )
    index = exact(index + 1, "", "Elenchus verdict separator")
    index = exact(index, FINDINGS_HEADER, "findings header")
    index = exact(index, FINDINGS_SEPARATOR, "findings separator")
    rows = []
    while index < len(record) and record[index] != "":
        cells = _table_cells(record[index])
        if len(cells) != 5 or any(not cell for cell in cells):
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has malformed findings row"
            )
        rows.append(record[index])
        index += 1
    if not rows or (ZERO_FINDING_ROW in rows and rows != [ZERO_FINDING_ROW]):
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed findings table"
        )
    index = exact(index, "", "findings separator")
    if index >= len(record):
        raise SynopsisError(f"{source_path}: strict record {record_number} is truncated")
    _field(record[index], "Leads not pursued", record_number, source_path)
    if index + 1 != len(record):
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has trailing content"
        )
    return record


def _table_extent(record, start):
    end = start
    while end < len(record) and record[end].startswith("|"):
        end += 1
    return range(start, end)


def _risk_table(record, index):
    cells = _table_cells(record[index])
    if not cells or cells[0].strip("` ").lower() != "risk id":
        return False
    if index + 1 >= len(record):
        return False
    separator = _table_cells(record[index + 1])
    return len(separator) == len(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in separator
    )


def _legacy_lines(record):
    selected = {0}
    fields = {
        "audit-schema": "Audit schema: ",
        "covered": "Covered: ",
        "not-checked": "Not checked: ",
        "elenchus-verdict": "Elenchus verdict: ",
    }
    missing = []
    for slug, prefix in fields.items():
        matches = [index for index, line in enumerate(record) if line.startswith(prefix)]
        if matches:
            selected.update(matches)
        else:
            missing.append(f"[missing legacy field: {slug}]")

    index = 1
    while index < len(record):
        if (
            record[index] == FINDINGS_HEADER
            and index + 1 < len(record)
            and record[index + 1] == FINDINGS_SEPARATOR
        ):
            extent = _table_extent(record, index)
            selected.update(extent)
            index = extent.stop
            continue
        if _risk_table(record, index):
            extent = _table_extent(record, index)
            selected.update(extent)
            index = extent.stop
            continue
        index += 1

    leads = [
        index for index, line in enumerate(record) if "Leads not pursued" in line
    ]
    if leads:
        end = len(record)
        while end > leads[0] and record[end - 1] == "":
            end -= 1
        selected.update(range(leads[0], end))
    else:
        missing.append("[missing legacy field: leads-not-pursued]")

    retained = [record[0], *missing]
    retained.extend(record[index] for index in sorted(selected - {0}))
    return retained


def render_source(source_path, data):
    """Render one source from captured bytes without touching the filesystem."""
    source_path = _relative_path(source_path)
    lines = _physical_lines(source_path, data)
    starts = [index for index, line in enumerate(lines) if _is_h2(line)]
    if not starts:
        raise SynopsisError(f"{source_path}: source has no raw H2 records")
    if len(starts) > H2_RECORDS_MAX:
        raise SynopsisError(
            f"{source_path}: source exceeds {H2_RECORDS_MAX:,} H2 record cap"
        )
    starts.append(len(lines))
    records = []
    for number in range(1, len(starts)):
        record = lines[starts[number - 1]:starts[number]]
        if _strict_candidate(record):
            retained = _strict_lines(record, number, source_path)
        else:
            retained = _legacy_lines(record)
        records.append("<br>".join(retained))

    source_digest = hashlib.sha256(data).hexdigest()
    metadata = (
        f"Synopsis schema={SYNOPSIS_SCHEMA} | source={source_path} | "
        f"source_sha256={source_digest} | h2_count={len(records)}"
    )
    rendered = ("\n".join([metadata, *records]) + "\n").encode("utf-8")
    source_lines = len(lines)
    synopsis_lines = len(records) + 1
    if synopsis_lines * 100 >= source_lines * 15:
        raise SynopsisError(
            f"{source_path}: 15% line budget failed "
            f"(source_lines={source_lines}, synopsis_lines={synopsis_lines})"
        )
    return {
        "source": source_path,
        "bytes": rendered,
        "source_lines": source_lines,
        "synopsis_lines": synopsis_lines,
        "h2_count": len(records),
        "source_sha256": source_digest,
        "synopsis_sha256": hashlib.sha256(rendered).hexdigest(),
        "budget": "pass",
    }


def discover_sources(root):
    """Discover sorted regular **/audit/AUDIT.md paths without following links."""
    root = _root_path(root)
    discovered = []
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        kept = []
        for name in sorted(names):
            candidate = os.path.join(directory, name)
            try:
                info = os.lstat(candidate)
            except OSError:
                raise SynopsisError("repository discovery cannot inspect a directory") from None
            if stat.S_ISLNK(info.st_mode):
                if name == "audit":
                    relative = os.path.relpath(candidate, root).replace(os.sep, "/")
                    raise SynopsisError(f"audit directory is a symlink: {relative}")
                continue
            if name in (".git", ".hexaemeron"):
                continue
            kept.append(name)
        names[:] = kept
        if os.path.basename(directory) != "audit" or SOURCE_NAME not in files:
            continue
        candidate = os.path.join(directory, SOURCE_NAME)
        relative = os.path.relpath(candidate, root).replace(os.sep, "/")
        try:
            info = os.lstat(candidate)
        except OSError:
            raise SynopsisError(f"audit source cannot be inspected: {relative}") from None
        if stat.S_ISLNK(info.st_mode):
            raise SynopsisError(f"audit source is a symlink: {relative}")
        if not stat.S_ISREG(info.st_mode):
            raise SynopsisError(f"audit source is not a regular file: {relative}")
        discovered.append(_relative_path(relative))
    discovered.sort()
    if not discovered:
        raise SynopsisError("repository contains no **/audit/AUDIT.md source")
    return discovered


def _output_path(source):
    return posixpath.join(posixpath.dirname(source), SYNOPSIS_NAME)


def _write_all(descriptor, data):
    view = memoryview(data)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("zero-byte temporary write")
        view = view[written:]


def atomic_replace(root, relative, data):
    """Flush and replace one sibling through its directory descriptor."""
    root = _root_path(root)
    relative = _relative_path(relative)
    components = relative.split("/")
    if components[-1] != SYNOPSIS_NAME:
        raise SynopsisError(f"output is not a {SYNOPSIS_NAME} sibling: {relative}")
    lexical = os.path.join(root, *components)
    mode = 0o644
    try:
        current = os.lstat(lexical)
    except FileNotFoundError:
        current = None
    except OSError:
        raise SynopsisError(f"synopsis output cannot be inspected: {relative}") from None
    if current is not None:
        if stat.S_ISLNK(current.st_mode):
            raise SynopsisError(f"synopsis output is a symlink: {relative}")
        if not stat.S_ISREG(current.st_mode):
            raise SynopsisError(f"synopsis output is not a regular file: {relative}")
        mode = stat.S_IMODE(current.st_mode)
    if not UNLINK_SUPPORTS_DIR_FD:
        raise SynopsisError("platform cannot safely replace a synopsis")

    parent = _directory_descriptor(root, components[:-1], "synopsis directory")
    temporary = None
    descriptor = None
    try:
        for _ in range(128):
            candidate = f".{SYNOPSIS_NAME}.{secrets.token_hex(8)}.tmp"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent,
                )
                temporary = candidate
                break
            except FileExistsError:
                continue
        if descriptor is None:
            raise SynopsisError(f"synopsis temporary name exhausted: {relative}")
        try:
            os.fchmod(descriptor, mode)
            _write_all(descriptor, data)
            os.fsync(descriptor)
        except OSError:
            raise SynopsisError(f"synopsis temporary write failed: {relative}") from None
        finally:
            with contextlib.suppress(OSError):
                os.close(descriptor)
            descriptor = None
        try:
            os.replace(
                temporary,
                components[-1],
                src_dir_fd=parent,
                dst_dir_fd=parent,
            )
            temporary = None
            os.fsync(parent)
        except OSError:
            raise SynopsisError(f"synopsis atomic replacement failed: {relative}") from None
    finally:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        if temporary is not None:
            with contextlib.suppress(OSError):
                os.unlink(temporary, dir_fd=parent)
        with contextlib.suppress(OSError):
            os.close(parent)

    committed = read_regular_bytes(root, relative, "synopsis output")
    if committed != data:
        raise SynopsisError(
            f"synopsis post-write bytes differ: {relative}; "
            f"expected_sha256={hashlib.sha256(data).hexdigest()}; "
            f"actual_sha256={hashlib.sha256(committed).hexdigest()}"
        )


def validate_committed_synopsis(root, source_path, source_bytes):
    """Render captured source bytes and require its committed sibling verbatim."""
    rendered = render_source(source_path, source_bytes)
    output = _output_path(source_path)
    committed = read_regular_bytes(root, output, "audit synopsis", missing_ok=True)
    if committed is None:
        raise SynopsisError(f"audit synopsis is missing: {output}")
    actual = hashlib.sha256(committed).hexdigest()
    if committed != rendered["bytes"]:
        raise SynopsisError(
            f"audit synopsis is stale: {output}; "
            f"source_lines={rendered['source_lines']}; "
            f"synopsis_lines={rendered['synopsis_lines']}; budget=pass; "
            f"source_sha256={rendered['source_sha256']}; "
            f"fresh_sha256={rendered['synopsis_sha256']}; "
            f"committed_sha256={actual}"
        )
    return rendered["synopsis_sha256"]


def process_repository(root, *, write):
    root = _root_path(root)
    rendered = []
    for source in discover_sources(root):
        source_bytes = read_regular_bytes(root, source, "audit source")
        item = render_source(source, source_bytes)
        item["output"] = _output_path(source)
        committed = read_regular_bytes(
            root, item["output"], "audit synopsis", missing_ok=True
        )
        item["committed_bytes"] = committed
        item["committed_sha256"] = (
            hashlib.sha256(committed).hexdigest() if committed is not None else "missing"
        )
        rendered.append(item)

    if write:
        for item in rendered:
            atomic_replace(root, item["output"], item["bytes"])
            item["committed"] = "written"
            item["committed_sha256"] = item["synopsis_sha256"]
    else:
        for item in rendered:
            if item["committed_bytes"] is None:
                raise SynopsisError(f"audit synopsis is missing: {item['output']}")
            if item["committed_bytes"] != item["bytes"]:
                raise SynopsisError(
                    f"audit synopsis is stale: {item['output']}; "
                    f"source_lines={item['source_lines']}; "
                    f"synopsis_lines={item['synopsis_lines']}; budget=pass; "
                    f"source_sha256={item['source_sha256']}; "
                    f"fresh_sha256={item['synopsis_sha256']}; "
                    f"committed_sha256={item['committed_sha256']}"
                )
            item["committed"] = "match"
    for item in rendered:
        item.pop("bytes", None)
        item.pop("committed_bytes", None)
    return rendered


def _diagnostic(item):
    return (
        f"{item['source']}: source_lines={item['source_lines']} "
        f"synopsis_lines={item['synopsis_lines']} budget={item['budget']} "
        f"source_sha256={item['source_sha256']} "
        f"fresh_sha256={item['synopsis_sha256']} "
        f"committed_sha256={item['committed_sha256']} "
        f"committed={item['committed']}"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="write or check deterministic Fiat audit synopses"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("root", help="real repository root")
    args = parser.parse_args(argv)
    try:
        results = process_repository(args.root, write=args.write)
    except SynopsisError as error:
        print(f"audit_synopsis: error: {error}", file=sys.stderr)
        return 2
    for item in results:
        print(_diagnostic(item))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
