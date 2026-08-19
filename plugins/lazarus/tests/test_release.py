"""Writing a preservation release, and refusing to write one.

The release is the artefact somebody keeps. So the tests that matter most are
not the ones where it is written: they are the ones where it is not, and nothing
is left behind for a later reader to mistake for a release.
"""

import copy
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

from lazarus_lib.binding import CHECKS
from lazarus_lib.canonical import dump, dumps, loads
from lazarus_lib.errors import FormatError, IntegrityError, LazarusError, PathError
from lazarus_lib.manifest import build_manifest, write_manifest
from lazarus_lib.records import write_proof_records, write_rpc_records
from lazarus_lib.release import (
    FIXTURE_DIRECTORY,
    RELEASE_NAME,
    STATEMENT_NAME,
    build_release,
    release_digest,
    write_release,
)
from lazarus_lib.verifier import verify_fixture

from . import support

COMPONENTS = ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl")
STATE_FIXTURE_TYPE = "https://ariadne.wildcat.finance/state-fixture/v1"
CLI = support.PLUGIN_ROOT / "scripts" / "lazarus.py"


def write_fixture(root: Path, *, hash_source=None):
    """A fixture that verifies, built from synthetic material.

    `hash_source` changes one string nothing verifies against, which is enough
    to make a second fixture that verifies to a different digest.
    """
    material = support.synthetic_fixture_material()
    if hash_source is not None:
        material["plan"]["block"]["hash_source"] = hash_source
    dump(root / "plan.json", material["plan"])
    dump(root / "header.json", material["header"])
    write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
    write_proof_records(root / "proofs.jsonl", material["proof_records"])
    manifest = build_manifest(
        root,
        COMPONENTS,
        chain_id="0x1",
        block_number=material["header"]["number"],
        block_hash=material["header"]["hash"],
    )
    write_manifest(root, manifest)
    return material


def statement_for(root: Path):
    """A statement that binds, built from what the fixture verifies to.

    Written here rather than captured, so these tests do not depend on another
    plugin being installed. The shape is the one Ariadne writes.
    """
    report = verify_fixture(root)
    manifest = report["manifest"]
    subjects = [
        {
            "name": entry["path"],
            "path": entry["path"],
            "digest": {"sha256": entry["sha256"]},
            "bytes": entry["bytes"],
        }
        for entry in manifest["components"]
    ]
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": STATE_FIXTURE_TYPE,
        "subject": [
            {"name": entry["name"], "digest": entry["digest"]} for entry in subjects
        ]
        + [{"name": "synthetic-v0", "digest": {"sha256": report["fixture_digest"]}}],
        "predicate": {
            "chain": {
                "chain_id": int(manifest["chain_id"], 16),
                "block_number": int(report["block_number"], 16),
                "block_hash": report["block_hash"],
                "state_root": report["state_root"],
            },
            "evidence": dict(report["evidence_counts"]),
            "replay": {"reaches_network": False, "canonical_chain_claim": False},
            "fixture_subjects": subjects,
        },
    }


class Prepared:
    """A fixture, a statement beside it, and somewhere to write."""

    def __init__(self, directory):
        self.root = Path(directory)
        self.fixture = self.root / "fixture-source"
        self.fixture.mkdir()
        write_fixture(self.fixture)
        self.statement = self.root / "statement.json"
        self.document = statement_for(self.fixture)
        self.write_statement(self.document)
        self.out = self.root / "release"

    def write_statement(self, document):
        self.statement.write_bytes(json.dumps(document, indent=2).encode())

    def release(self, **changes):
        return write_release(
            changes.get("fixture", self.fixture),
            changes.get("statement", self.statement),
            changes.get("out", self.out),
        )

    def staged(self):
        return sorted(
            path.name for path in self.out.parent.glob(".*") if path.is_dir()
        )


class WrittenReleaseTests(unittest.TestCase):
    def test_a_release_holds_the_fixture_the_statement_and_the_document(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            self.assertTrue((prepared.out / FIXTURE_DIRECTORY).is_dir())
            self.assertTrue((prepared.out / STATEMENT_NAME).is_file())
            self.assertTrue((prepared.out / RELEASE_NAME).is_file())

    def test_the_fixture_copy_verifies_to_the_same_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            copied = verify_fixture(prepared.out / FIXTURE_DIRECTORY)
            self.assertEqual(
                copied["fixture_digest"], document["fixture"]["fixture_digest"]
            )

    def test_the_statement_is_the_bytes_that_were_handed_over(self):
        """A re-encoded document is a different document, and the release
        digests the bytes."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            written = (prepared.out / STATEMENT_NAME).read_bytes()
            self.assertEqual(written, prepared.statement.read_bytes())
            import hashlib

            self.assertEqual(
                document["statement"]["sha256"], hashlib.sha256(written).hexdigest()
            )

    def test_the_document_records_what_verification_established(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            report = verify_fixture(prepared.fixture)
            self.assertEqual(
                document["verified"]["evidence_counts"], report["evidence_counts"]
            )
            self.assertEqual(document["verified"]["block_hash"], report["block_hash"])
            self.assertIs(document["verified"]["canonical_chain_claim"], False)

    def test_the_document_names_every_check_the_binding_made(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            self.assertEqual(document["binding"]["checks"], list(CHECKS))

    def test_the_document_on_disk_is_the_document_returned(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            self.assertEqual(loads((prepared.out / RELEASE_NAME).read_bytes()), document)

    def test_the_release_digest_covers_the_document(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            self.assertEqual(document["release_digest"], release_digest(document))
            for field in ("fixture", "statement", "verified", "binding"):
                edited = copy.deepcopy(document)
                edited[field] = {"tampered": True}
                with self.subTest(field=field):
                    self.assertNotEqual(release_digest(edited), document["release_digest"])

    def test_nothing_is_staged_once_the_release_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            self.assertEqual(prepared.staged(), [])


class RefusedReleaseTests(unittest.TestCase):
    """Every one of these must also leave nothing behind."""

    def refuse(self, prepared, error=LazarusError, **changes):
        with self.assertRaises(error) as caught:
            prepared.release(**changes)
        out = Path(changes.get("out", prepared.out))
        self.assertFalse(out.exists(), "an output directory was left behind")
        self.assertEqual(prepared.staged(), [], "a staged directory was left behind")
        return caught.exception

    def test_a_statement_claiming_more_than_the_records_support_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = copy.deepcopy(prepared.document)
            document["predicate"]["evidence"]["proof_backed"] += 4
            document["predicate"]["evidence"]["recorded_rpc"] = 0
            prepared.write_statement(document)
            error = self.refuse(prepared, IntegrityError)
            self.assertIn("proof_backed", str(error))
            self.assertIn("more than the records support", str(error))

    def test_a_statement_about_another_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = copy.deepcopy(prepared.document)
            document["predicate"]["chain"]["block_hash"] = "0x" + "99" * 32
            prepared.write_statement(document)
            self.refuse(prepared, IntegrityError)

    def test_a_fixture_that_does_not_verify_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            component = prepared.fixture / "plan.json"
            component.write_bytes(
                component.read_bytes().replace(b"ethereum-mainnet", b"ethereum-testnet")
            )
            error = self.refuse(prepared, IntegrityError)
            self.assertIn("plan.json", str(error))

    def test_an_output_that_already_exists_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.out.mkdir()
            with self.assertRaises(FormatError) as caught:
                prepared.release()
            self.assertIn("already exists", str(caught.exception))
            self.assertEqual(sorted(prepared.out.iterdir()), [])

    def test_an_output_that_is_a_file_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.out.write_bytes(b"not a release")
            with self.assertRaises(FormatError):
                prepared.release()

    def test_an_output_inside_the_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            error = self.refuse(
                prepared, FormatError, out=prepared.fixture / "release"
            )
            self.assertIn("inside the fixture", str(error))

    def test_an_output_that_is_the_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with self.assertRaises(FormatError) as caught:
                prepared.release(out=prepared.fixture)
            self.assertIn("is the fixture", str(caught.exception))

    def test_a_fixture_inside_the_output_is_refused(self):
        """The output already exists here, so the absence check the other cases
        make does not apply; the overlap is what is being refused."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with self.assertRaises(FormatError) as caught:
                prepared.release(out=prepared.root)
            self.assertIn("sits inside", str(caught.exception))
            self.assertEqual(prepared.staged(), [])

    def test_an_output_whose_parent_does_not_exist_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            error = self.refuse(
                prepared, FormatError, out=prepared.root / "missing" / "release"
            )
            self.assertIn("parent", str(error))

    @unittest.skipIf(
        hasattr(os, "geteuid") and os.geteuid() == 0,
        "root ignores directory permissions, so there is nothing to refuse",
    )
    def test_an_output_that_cannot_be_written_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            closed = prepared.root / "closed"
            closed.mkdir(mode=0o500)
            try:
                with self.assertRaises(OSError):
                    prepared.release(out=closed / "release")
            finally:
                closed.chmod(0o700)

    def test_a_statement_that_is_not_json_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.statement.write_bytes(b"{not json")
            self.refuse(prepared)

    def test_a_statement_that_is_not_an_object_is_refused(self):
        """Refused by the binding, in the words it uses for every other shape it
        will not read, rather than by a second check here saying the same thing."""
        for text in (b"[]", b'"a statement"', b"12345", b"null", b"true"):
            with tempfile.TemporaryDirectory() as directory:
                prepared = Prepared(directory)
                prepared.statement.write_bytes(text)
                with self.subTest(statement=text):
                    error = self.refuse(prepared, FormatError)
                    self.assertIn("statement must be an object", str(error))

    def test_an_output_that_is_a_dangling_symlink_is_refused(self):
        """`exists` follows the link and says no. The name is still taken, and
        a rename onto it would replace the link rather than write beside it."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.out.symlink_to(prepared.root / "nothing-here")
            with self.assertRaises(FormatError) as caught:
                prepared.release()
            self.assertIn("already exists", str(caught.exception))
            self.assertTrue(prepared.out.is_symlink())
            self.assertEqual(prepared.staged(), [])

    def test_a_statement_carrying_a_number_json_should_not_have_is_refused(self):
        """`json.loads` accepts NaN and Infinity. Nothing downstream would."""
        for text in (b'{"a": NaN}', b'{"a": Infinity}', b'{"a": -Infinity}'):
            with tempfile.TemporaryDirectory() as directory:
                prepared = Prepared(directory)
                prepared.statement.write_bytes(text)
                with self.subTest(statement=text):
                    self.refuse(prepared)

    def test_a_statement_naming_one_key_twice_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.statement.write_bytes(b'{"_type": "a", "_type": "b"}')
            self.refuse(prepared)

    def test_a_statement_that_is_not_a_regular_file_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            error = self.refuse(
                prepared, PathError, statement=prepared.root / "not-there.json"
            )
            self.assertIn("regular file", str(error))

    def test_a_statement_that_is_a_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            somewhere = prepared.root / "a-directory"
            somewhere.mkdir()
            self.refuse(prepared, PathError, statement=somewhere)

    def test_a_statement_that_is_a_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            link = prepared.root / "linked.json"
            link.symlink_to(prepared.statement)
            error = self.refuse(prepared, PathError, statement=link)
            self.assertIn("symlink", str(error))

    def test_a_statement_larger_than_the_read_cap_is_refused(self):
        from lazarus_lib.canonical import MAX_JSON_BYTES

        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.statement.write_bytes(b'{"a": "' + b"x" * MAX_JSON_BYTES + b'"}')
            error = self.refuse(prepared, FormatError)
            self.assertIn(str(MAX_JSON_BYTES), str(error))

    def test_a_staged_directory_already_in_the_way_is_refused(self):
        """Its name is not a release, and a run that overwrote it would be
        writing over whatever left it there."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            (prepared.root / (".%s.staged" % prepared.out.name)).mkdir()
            with self.assertRaises(FormatError) as caught:
                prepared.release()
            self.assertIn("staged", str(caught.exception))
            self.assertFalse(prepared.out.exists())

    def test_a_fixture_that_is_not_there_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            self.refuse(prepared, fixture=prepared.root / "no-fixture")


class KilledRunTests(unittest.TestCase):
    def test_a_run_killed_while_writing_leaves_no_release(self):
        """The copy is the longest part, so that is where the kill lands."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib import release as module

            original = module._copy_fixture

            def killed(*arguments, **keywords):
                original(*arguments, **keywords)
                raise KeyboardInterrupt("killed mid-write")

            module._copy_fixture = killed
            try:
                with self.assertRaises(KeyboardInterrupt):
                    prepared.release()
            finally:
                module._copy_fixture = original
            self.assertFalse(prepared.out.exists())
            self.assertEqual(prepared.staged(), [])

    def test_a_copy_of_another_fixture_leaves_no_release(self):
        """A copy that verifies is not enough. It has to verify to the digest
        the release records, or the release describes a fixture it does not
        hold."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            other = prepared.root / "other-fixture"
            other.mkdir()
            write_fixture(other, hash_source="a second synthetic offline test vector")
            from lazarus_lib import release as module

            original = module._copy_fixture

            def elsewhere(source, target, manifest):
                original(other, target, verify_fixture(other)["manifest"])

            module._copy_fixture = elsewhere
            try:
                with self.assertRaises(IntegrityError) as caught:
                    prepared.release()
            finally:
                module._copy_fixture = original
            self.assertIn("verifies to", str(caught.exception))
            self.assertFalse(prepared.out.exists())
            self.assertEqual(prepared.staged(), [])

    def test_a_copy_that_does_not_verify_leaves_no_release(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib import release as module

            original = module._copy_fixture

            def short(source, target, manifest):
                original(source, target, manifest)
                (target / "plan.json").write_bytes(b"{}")

            module._copy_fixture = short
            try:
                with self.assertRaises(IntegrityError):
                    prepared.release()
            finally:
                module._copy_fixture = original
            self.assertFalse(prepared.out.exists())
            self.assertEqual(prepared.staged(), [])


class OneReadTests(unittest.TestCase):
    """The decision the module docstring leads with, pinned.

    Verification and binding both need the manifest. Reading it twice reads two
    states, and nothing after the first read would notice a component changing
    between them.
    """

    def test_the_binding_is_given_the_manifest_the_report_was_computed_from(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib import release as module

            original = module.bind
            seen = {}

            def watched(statement, manifest, report):
                seen["manifest"] = manifest
                seen["report"] = report
                return original(statement, manifest, report)

            module.bind = watched
            try:
                prepared.release()
            finally:
                module.bind = original
            self.assertIs(seen["manifest"], seen["report"]["manifest"])

    def test_a_release_records_the_digest_the_report_carried(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            report = verify_fixture(prepared.fixture)
            self.assertEqual(
                document["fixture"]["fixture_digest"],
                report["manifest"]["fixture_digest"],
            )


class DocumentTests(unittest.TestCase):
    def test_a_document_the_schema_refuses_is_not_returned(self):
        """The block hash comes out of verification lowercased. A report that
        carried it otherwise would build a document the schema refuses, and the
        release must not be the thing that discovers this later."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            report = verify_fixture(prepared.fixture)
            report["block_hash"] = report["block_hash"].upper().replace("0X", "0x")
            with self.assertRaises(FormatError):
                build_release(prepared.document, b"{}", report, list(CHECKS))

    def test_a_document_with_no_checks_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            report = verify_fixture(prepared.fixture)
            with self.assertRaises(FormatError):
                build_release(prepared.document, b"{}", report, [])

    def test_a_check_that_names_nothing_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            report = verify_fixture(prepared.fixture)
            for name in ("", "   ", "\u200b"):
                with self.subTest(check=repr(name)), self.assertRaises(FormatError):
                    build_release(prepared.document, b"{}", report, [name])


class CopyTests(unittest.TestCase):
    def test_the_copy_holds_the_manifest_and_every_component(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            copied = prepared.out / FIXTURE_DIRECTORY
            held = {
                path.relative_to(copied).as_posix()
                for path in copied.rglob("*")
                if path.is_file()
            }
            self.assertEqual(held, {"manifest.json"} | set(COMPONENTS))

    def test_the_copy_is_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            for relative in ("manifest.json",) + COMPONENTS:
                with self.subTest(component=relative):
                    self.assertEqual(
                        (prepared.out / FIXTURE_DIRECTORY / relative).read_bytes(),
                        (prepared.fixture / relative).read_bytes(),
                    )

    def test_a_file_the_manifest_does_not_list_does_not_ride_along(self):
        """Verification refuses an unlisted file, so this cannot happen through
        the command. The copy is driven by the manifest anyway."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib.release import _copy_fixture

            report = verify_fixture(prepared.fixture)
            (prepared.fixture / "stowaway.txt").write_bytes(b"not listed")
            target = prepared.root / "copy"
            _copy_fixture(prepared.fixture, target, report["manifest"])
            self.assertFalse((target / "stowaway.txt").exists())

    def test_the_copy_is_not_writable_by_anybody_else(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            mode = stat.S_IMODE(os.stat(prepared.out / FIXTURE_DIRECTORY).st_mode)
            self.assertEqual(mode & (stat.S_IWGRP | stat.S_IWOTH), 0)


class ReproducibleTests(unittest.TestCase):
    def test_two_runs_over_one_fixture_and_statement_agree(self):
        """A release nobody can rebuild is a release nobody can check."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            first = prepared.release()
            again = prepared.root / "release-again"
            second = write_release(prepared.fixture, prepared.statement, again)
            self.assertEqual(first, second)
            self.assertEqual(
                (prepared.out / RELEASE_NAME).read_bytes(),
                (again / RELEASE_NAME).read_bytes(),
            )
            for relative in ("manifest.json",) + COMPONENTS:
                with self.subTest(component=relative):
                    self.assertEqual(
                        (prepared.out / FIXTURE_DIRECTORY / relative).read_bytes(),
                        (again / FIXTURE_DIRECTORY / relative).read_bytes(),
                    )


class DigestIdentityTests(unittest.TestCase):
    """The claim the digest function's docstring makes, held to.

    A field added to the schema and not to the identity is a digest that quietly
    stops covering part of the document. This is the test that makes that a
    failure rather than a discovery.
    """

    def test_the_digest_covers_every_field_the_schema_requires(self):
        from lazarus_lib.schemas import _schema

        required = set(_schema("release", 1)["required"]) - {"release_digest"}
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            for field in sorted(required):
                edited = copy.deepcopy(document)
                edited[field] = "changed"
                with self.subTest(field=field):
                    self.assertNotEqual(
                        release_digest(edited),
                        document["release_digest"],
                        "%s is required by the schema and not covered by the digest"
                        % field,
                    )

    def test_the_digest_does_not_cover_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            edited = copy.deepcopy(document)
            edited["release_digest"] = "f" * 64
            self.assertEqual(release_digest(edited), release_digest(document))


class RenameWindowTests(unittest.TestCase):
    """What a lost race costs, recorded rather than assumed.

    The output name is free when a run begins and the copy takes time. Between
    the last check and the rename the name is still unheld. Rename replaces an
    empty directory and nothing else, so these tests record where the boundary
    sits.
    """

    def race(self, prepared, prepare):
        from lazarus_lib import release as module

        original = module.os.replace

        def racing(source, target, *arguments, **keywords):
            path = Path(target)
            if not path.exists() and not path.is_symlink():
                prepare(path)
            return original(source, target, *arguments, **keywords)

        module.os.replace = racing
        try:
            return prepared.release()
        finally:
            module.os.replace = original

    def test_a_directory_holding_anything_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)

            def prepare(path):
                path.mkdir()
                (path / "someone-elses.txt").write_bytes(b"mine")

            with self.assertRaises(OSError):
                self.race(prepared, prepare)
            self.assertTrue((prepared.out / "someone-elses.txt").is_file())
            self.assertEqual(prepared.staged(), [])

    def test_a_file_in_the_way_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with self.assertRaises(OSError):
                self.race(prepared, lambda path: path.write_bytes(b"mine"))
            self.assertEqual(prepared.out.read_bytes(), b"mine")
            self.assertEqual(prepared.staged(), [])

    def test_a_symlink_in_the_way_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with self.assertRaises(OSError):
                self.race(
                    prepared, lambda path: path.symlink_to(prepared.root / "nowhere")
                )
            self.assertTrue(prepared.out.is_symlink())
            self.assertEqual(prepared.staged(), [])

    def test_an_output_that_appears_during_the_copy_is_refused(self):
        """The check before the rename, which the long part of the run makes
        worth making."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib import release as module

            original = module._copy_fixture

            def slow(source, target, manifest):
                original(source, target, manifest)
                prepared.out.mkdir()

            module._copy_fixture = slow
            try:
                with self.assertRaises(FormatError) as caught:
                    prepared.release()
            finally:
                module._copy_fixture = original
            self.assertIn("appeared while it was built", str(caught.exception))
            self.assertTrue(prepared.out.is_dir())
            self.assertEqual(prepared.staged(), [])


class StagedNameTests(unittest.TestCase):
    def test_a_staged_name_taken_by_something_else_is_refused(self):
        for kind in ("symlink", "file", "directory"):
            with tempfile.TemporaryDirectory() as directory:
                prepared = Prepared(directory)
                staged = prepared.root / (".%s.staged" % prepared.out.name)
                if kind == "symlink":
                    staged.symlink_to(prepared.root / "nowhere")
                elif kind == "file":
                    staged.write_bytes(b"not a staging directory")
                else:
                    staged.mkdir()
                with self.subTest(kind=kind):
                    with self.assertRaises(FormatError) as caught:
                        prepared.release()
                    self.assertIn("staged", str(caught.exception))
                    self.assertTrue(staged.exists() or staged.is_symlink())
                    self.assertFalse(prepared.out.exists())


class ModeTests(unittest.TestCase):
    def test_nothing_in_a_release_is_readable_by_anybody_else(self):
        """A release is not published by being written. Whoever hands it over
        opens it up deliberately."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            for path in [prepared.out] + sorted(prepared.out.rglob("*")):
                mode = stat.S_IMODE(path.stat().st_mode)
                with self.subTest(path=path.name):
                    self.assertEqual(
                        mode & (stat.S_IRWXG | stat.S_IRWXO),
                        0,
                        "%s is %s" % (path, oct(mode)),
                    )


class CommandTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(CLI), "release", *[str(a) for a in arguments]],
            capture_output=True,
            text=True,
        )

    def test_the_command_writes_a_release_and_prints_the_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            result = self.run_cli(
                prepared.fixture, "--statement", prepared.statement, "--out", prepared.out
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("release: ", result.stdout)
            self.assertIn("proof-backed: 3", result.stdout)
            self.assertIn("header-bound: 1", result.stdout)
            self.assertIn("recorded-rpc: 1", result.stdout)
            for check in CHECKS:
                self.assertIn(check, result.stdout)

    def test_the_command_refuses_a_statement_that_claims_more(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = copy.deepcopy(prepared.document)
            document["predicate"]["evidence"]["proof_backed"] += 1
            prepared.write_statement(document)
            result = self.run_cli(
                prepared.fixture, "--statement", prepared.statement, "--out", prepared.out
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("more than the records support", result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertFalse(prepared.out.exists())

    def test_the_command_validates_the_document_it_wrote(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            self.run_cli(
                prepared.fixture, "--statement", prepared.statement, "--out", prepared.out
            )
            checked = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "validate",
                    "release",
                    str(prepared.out / RELEASE_NAME),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)


if __name__ == "__main__":
    unittest.main()
