"""Fixture-root confinement without symlink or traversal shortcuts."""

from __future__ import annotations

import os
import errno
from pathlib import Path, PurePosixPath
import secrets
import stat

from .errors import PathError, ResourceLimitError

MAX_FIXTURE_ENTRIES = 8192


def validate_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise PathError("component path must be a non-empty string")
    if "\x00" in value or "\\" in value:
        raise PathError(f"unsafe component path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/"):
        raise PathError(f"absolute component path is forbidden: {value}")
    if any(part in ("", ".", "..") for part in path.parts):
        raise PathError(f"component path is not normalised: {value}")
    normalised = path.as_posix()
    if normalised != value:
        raise PathError(f"component path is not slash-normalised: {value}")
    return normalised


def list_fixture_files(
    root: str | Path, *, max_entries: int = MAX_FIXTURE_ENTRIES
) -> set[str]:
    root_path = Path(root)
    if root_path.is_symlink():
        raise PathError(f"fixture root is a symlink: {root_path}")
    files: set[str] = set()
    for entry_number, path in enumerate(root_path.rglob("*"), 1):
        if entry_number > max_entries:
            raise ResourceLimitError(
                f"fixture entry count exceeds {max_entries}"
            )
        relative = path.relative_to(root_path).as_posix()
        try:
            details = path.lstat()
        except OSError as exc:
            raise PathError(f"fixture entry is unavailable: {relative}") from exc
        if stat.S_ISLNK(details.st_mode):
            raise PathError(f"symlink component is forbidden: {relative}")
        if stat.S_ISREG(details.st_mode):
            files.add(validate_relative_path(relative))
        elif not stat.S_ISDIR(details.st_mode):
            raise PathError(f"non-regular fixture entry is forbidden: {relative}")
    return files


def read_confined_bytes(
    root: str | Path,
    relative: str,
    *,
    max_bytes: int,
) -> bytes:
    """Read one regular component through no-follow directory descriptors."""

    parent, name = _open_parent(root, relative)
    descriptor: int | None = None
    try:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(name, flags, dir_fd=parent)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise PathError(f"component is not a regular file: {relative}")
        if before.st_size > max_bytes:
            raise ResourceLimitError(f"component exceeds {max_bytes} bytes: {relative}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ResourceLimitError(f"component exceeds {max_bytes} bytes: {relative}")
        after = os.fstat(descriptor)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise PathError(f"component changed while it was read: {relative}")
        return data
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise PathError(f"symlink component is forbidden: {relative}") from exc
        raise PathError(f"cannot read fixture component: {relative}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def atomic_write_confined(root: str | Path, relative: str, data: bytes) -> None:
    """Replace one fixture file without following its previous inode."""

    parent, name = _open_parent(root, relative)
    temporary = f".{name}.{secrets.token_hex(8)}.tmp"
    created = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, 0o600, dir_fd=parent)
        created = True
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
        created = False
        os.fsync(parent)
    except OSError as exc:
        raise PathError(f"cannot write fixture component: {relative}") from exc
    finally:
        if created:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def _open_parent(root: str | Path, relative: str) -> tuple[int, str]:
    normalised = validate_relative_path(relative)
    parts = PurePosixPath(normalised).parts
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        current = os.open(Path(root), directory_flags)
    except OSError as exc:
        raise PathError(f"fixture root is unavailable: {root}") from exc
    try:
        if not stat.S_ISDIR(os.fstat(current).st_mode):
            raise PathError(f"fixture root is not a directory: {root}")
        for part in parts[:-1]:
            following = os.open(part, directory_flags, dir_fd=current)
            os.close(current)
            current = following
        return current, parts[-1]
    except OSError as exc:
        os.close(current)
        raise PathError(f"component parent is unavailable: {relative}") from exc
    except Exception:
        os.close(current)
        raise
