"""Keep every audit byte present when issue 429 started."""

from pathlib import Path
import contextlib
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "audit-prefixes.json"
AUDIT_PATHS = (
    "audit/AUDIT.md",
    "plugins/ariadne/audit/AUDIT.md",
    "plugins/hexaemeron/audit/AUDIT.md",
    "plugins/pandects/audit/AUDIT.md",
    "plugins/probitas/audit/AUDIT.md",
    "plugins/tabularium/audit/AUDIT.md",
)
ROOT_SUITE_JOBS = (
    (".github/workflows/janus.yml", "contracts"),
    (".github/workflows/lazarus.yml", "tests"),
    (".github/workflows/pandects.yml", "catalogue"),
)


def workflow_job(path, job):
    """Return one top-level workflow job without importing a YAML package."""
    lines = path.read_text(encoding="utf-8").splitlines()
    marker = f"  {job}:"
    try:
        start = lines.index(marker)
    except ValueError as exc:
        raise ValueError(f"{path}: workflow job {job} is missing") from exc
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("  ")
            and not lines[index].startswith("    ")
            and lines[index].endswith(":")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def check_prefix(data, expected):
    size = expected["bytes"]
    if len(data) < size:
        raise ValueError(f"{expected['path']}: protected prefix was shortened")
    prefix = data[:size]
    digest = hashlib.sha256(prefix).hexdigest()
    if digest != expected["sha256"]:
        raise ValueError(f"{expected['path']}: protected prefix digest changed")
    lines = prefix.count(b"\n")
    if lines != expected["lines"]:
        raise ValueError(f"{expected['path']}: protected prefix line count changed")


def check_starting_ref(data, expected):
    """Refuse a fixture that re-blesses bytes absent from its named commit."""
    if len(data) != expected["bytes"]:
        raise ValueError(f"{expected['path']}: starting ref byte length disagrees")
    if hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise ValueError(f"{expected['path']}: starting ref digest disagrees")
    if data.count(b"\n") != expected["lines"]:
        raise ValueError(f"{expected['path']}: starting ref line count disagrees")


def source_at(ref, path):
    return subprocess.run(
        ["git", "--no-replace-objects", "show", f"{ref}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def current_source(root, path, prefix_bytes):
    """Read one descriptor-bound protected prefix without following an alias."""
    relative = Path(path)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError(f"{path}: protected path traverses a symlink")
    if (
        not isinstance(prefix_bytes, int)
        or isinstance(prefix_bytes, bool)
        or prefix_bytes < 0
    ):
        raise ValueError(f"{path}: protected prefix byte length is invalid")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_only = getattr(os, "O_DIRECTORY", 0)
    non_blocking = getattr(os, "O_NONBLOCK", 0)
    if (
        not no_follow
        or not directory_only
        or not non_blocking
        or os.open not in os.supports_dir_fd
    ):
        raise ValueError(f"{path}: protected path traverses a symlink")
    close_exec = getattr(os, "O_CLOEXEC", 0)
    directory_flags = os.O_RDONLY | close_exec | no_follow | directory_only
    file_flags = os.O_RDONLY | close_exec | no_follow | non_blocking
    directory_descriptor = None
    next_descriptor = None
    file_descriptor = None
    try:
        directory_descriptor = os.open(
            os.path.realpath(root), directory_flags
        )
        if not stat.S_ISDIR(os.fstat(directory_descriptor).st_mode):
            raise ValueError(f"{path}: protected path traverses a symlink")
        for component in relative.parts[:-1]:
            next_descriptor = os.open(
                component, directory_flags, dir_fd=directory_descriptor
            )
            if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                raise ValueError(f"{path}: protected path traverses a symlink")
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
            next_descriptor = None
        file_descriptor = os.open(
            relative.parts[-1], file_flags, dir_fd=directory_descriptor
        )
        if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
            raise ValueError(f"{path}: protected path traverses a symlink")
        with os.fdopen(file_descriptor, "rb") as handle:
            file_descriptor = None
            return handle.read(prefix_bytes)
    except OSError as exc:
        raise ValueError(f"{path}: protected path traverses a symlink") from exc
    finally:
        for descriptor in (
            file_descriptor,
            next_descriptor,
            directory_descriptor,
        ):
            if descriptor is not None:
                with contextlib.suppress(OSError):
                    os.close(descriptor)


class AuditPrefixIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_identity_and_current_prefixes(self):
        self.assertEqual(self.fixture["schema"], "fiat-audit-prefixes/v1")
        self.assertEqual(
            self.fixture["starting_ref"],
            "ced4e6f439021b7509833ed5da66348c86d22f01",
        )
        self.assertEqual(
            tuple(item["path"] for item in self.fixture["prefixes"]),
            AUDIT_PATHS,
        )
        for expected in self.fixture["prefixes"]:
            with self.subTest(path=expected["path"]):
                check_starting_ref(
                    source_at(self.fixture["starting_ref"], expected["path"]),
                    expected,
                )
                check_prefix(
                    current_source(ROOT, expected["path"], expected["bytes"]),
                    expected,
                )

    def test_root_suite_ci_jobs_fetch_the_pinned_starting_ref(self):
        checkout = (
            "      - uses: actions/checkout@v4\n"
            "        with:\n"
            "          fetch-depth: 0"
        )
        for relative, job in ROOT_SUITE_JOBS:
            with self.subTest(path=relative, job=job):
                body = workflow_job(ROOT / relative, job)
                self.assertIn(
                    "run: python3 -m unittest discover -s tests -v", body
                )
                self.assertIn(checkout, body)

    def test_a_changed_prefix_cannot_be_reblessed_in_the_fixture(self):
        expected = self.fixture["prefixes"][2]
        original = source_at(self.fixture["starting_ref"], expected["path"])
        changed = bytearray(original)
        changed[10] ^= 1
        reblessed = {
            **expected,
            "sha256": hashlib.sha256(changed).hexdigest(),
        }

        check_prefix(bytes(changed), reblessed)
        with self.assertRaisesRegex(ValueError, "starting ref digest disagrees"):
            check_starting_ref(original, reblessed)

    def test_edit_truncate_and_insertion_fail_while_append_passes(self):
        expected = self.fixture["prefixes"][2]
        original = current_source(ROOT, expected["path"], expected["bytes"])

        edited = bytearray(original)
        edited[10] ^= 1
        with self.assertRaisesRegex(ValueError, "digest changed"):
            check_prefix(bytes(edited), expected)
        with self.assertRaisesRegex(ValueError, "shortened"):
            check_prefix(original[:-1], expected)
        with self.assertRaisesRegex(ValueError, "digest changed"):
            check_prefix(original[:10] + b"x" + original[10:], expected)

        check_prefix(original + b"\nfuture round\n", expected)

    def test_a_substituted_protected_path_is_refused(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(os.path.realpath(raw_root))
            outside = root / "moved"
            outside.mkdir()
            (outside / "AUDIT.md").write_bytes(b"preserved bytes")

            final_alias = root / "AUDIT.md"
            final_alias.symlink_to(outside / "AUDIT.md")
            with self.assertRaisesRegex(ValueError, "traverses a symlink"):
                current_source(root, "AUDIT.md", 1)

            final_alias.unlink()
            ancestor_alias = root / "audit"
            ancestor_alias.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "traverses a symlink"):
                current_source(root, "audit/AUDIT.md", 1)

    def test_a_raced_path_substitution_is_refused(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(os.path.realpath(raw_root))
            audit_dir = root / "audit"
            audit_dir.mkdir()
            candidate = audit_dir / "AUDIT.md"
            candidate.write_bytes(b"inside")
            moved = audit_dir / "before-swap.md"
            outside = root / "outside.md"
            outside.write_bytes(b"outside")
            real_open = os.open
            real_read_bytes = Path.read_bytes
            swapped = False

            def swap():
                nonlocal swapped
                if not swapped:
                    swapped = True
                    candidate.rename(moved)
                    candidate.symlink_to(outside)

            def racing_open(target, flags, *args, **kwargs):
                if target == "AUDIT.md" and "dir_fd" in kwargs:
                    swap()
                return real_open(target, flags, *args, **kwargs)

            def racing_read_bytes(path):
                if path == candidate:
                    swap()
                return real_read_bytes(path)

            with (
                mock.patch.object(os, "open", side_effect=racing_open),
                mock.patch.object(Path, "read_bytes", racing_read_bytes),
                self.assertRaisesRegex(ValueError, "traverses a symlink"),
            ):
                current_source(root, "audit/AUDIT.md", 1)

    def test_descriptor_walk_closes_every_open_descriptor_on_failure(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(os.path.realpath(raw_root))
            audit_dir = root / "audit"
            audit_dir.mkdir()
            (audit_dir / "AUDIT.md").write_bytes(b"inside")
            real_fstat = os.fstat
            inspected = []

            def failing_child_stat(descriptor):
                inspected.append(descriptor)
                if len(inspected) == 2:
                    raise OSError("synthetic child fstat failure")
                return real_fstat(descriptor)

            with (
                mock.patch.object(os, "fstat", side_effect=failing_child_stat),
                self.assertRaisesRegex(ValueError, "traverses a symlink"),
            ):
                current_source(root, "audit/AUDIT.md", 1)

            still_open = []
            for descriptor in inspected:
                try:
                    real_fstat(descriptor)
                except OSError:
                    continue
                still_open.append(descriptor)
                os.close(descriptor)
            self.assertEqual(still_open, [])

    def test_reader_requests_only_the_protected_prefix(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(os.path.realpath(raw_root))
            path = root / "AUDIT.md"
            path.write_bytes(b"protected" + b"future" * 10_000)
            real_fdopen = os.fdopen
            requests = []

            class TrackingHandle:
                def __init__(self, handle):
                    self.handle = handle

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.handle.close()

                def read(self, size=-1):
                    requests.append(size)
                    return self.handle.read(size)

            def tracking_fdopen(descriptor, mode):
                return TrackingHandle(real_fdopen(descriptor, mode))

            with mock.patch.object(os, "fdopen", side_effect=tracking_fdopen):
                self.assertEqual(
                    current_source(root, "AUDIT.md", len(b"protected")),
                    b"protected",
                )
            self.assertEqual(requests, [len(b"protected")])

    def test_reader_refuses_without_descriptor_relative_open(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(os.path.realpath(raw_root))
            (root / "AUDIT.md").write_bytes(b"protected")
            with (
                mock.patch.object(os, "supports_dir_fd", set()),
                self.assertRaisesRegex(ValueError, "traverses a symlink"),
            ):
                current_source(root, "AUDIT.md", len(b"protected"))


if __name__ == "__main__":
    unittest.main()
