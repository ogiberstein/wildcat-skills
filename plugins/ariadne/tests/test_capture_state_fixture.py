"""Reading a Lazarus fixture directory into a statement.

The shipped fixture is the one this capture was written against, so the tests that
matter most run over it rather than over a mock: a capture that only works on a tree
this file built is a capture nobody has tried.
"""

import copy
import hashlib
import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, registry, verify  # noqa: E402
import ariadne_lib.predicates  # noqa: F401,E402
from ariadne_lib.capture import state_fixture as capture  # noqa: E402
from ariadne_lib.predicates import state_fixture as predicate  # noqa: E402

GOLDFINCH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))),
    "plugins", "lazarus", "examples", "goldfinch-v0",
)

COMMAND = ["python3", "scripts/lazarus.py", "verify", "examples/goldfinch-v0"]
REASON = "first capture of this block; nothing earlier to compare against"


def read_json(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def taken(root, **overrides):
    arguments = {
        "name": "goldfinch-v0",
        "capture_tool": "lazarus",
        "capture_command": COMMAND,
        "first_capture_reason": REASON,
    }
    arguments.update(overrides)
    return capture.capture(root, **arguments)


def report_for(statement):
    return verify.report(
        envelope.read(json.dumps(statement).encode("utf-8")), registry.DEFAULT
    )


class SkipUnlessGoldfinch(unittest.TestCase):
    def setUp(self):
        if not os.path.isdir(GOLDFINCH):
            self.skipTest("Lazarus is not beside this plugin in this checkout")


class TheShippedFixtureTests(SkipUnlessGoldfinch):
    def test_it_captures_and_verifies_clean(self):
        report = report_for(taken(GOLDFINCH))
        self.assertTrue(
            report.ok, "\n".join(g.line() for g in report.gates if not g.passed)
        )
        self.assertFalse(report.unchecked)

    def test_the_pin_is_the_one_the_manifest_carries(self):
        manifest = read_json(os.path.join(GOLDFINCH, "manifest.json"))
        header = read_json(os.path.join(GOLDFINCH, "header.json"))
        chain = taken(GOLDFINCH)["predicate"]["chain"]
        self.assertEqual(chain["chain_id"], int(manifest["chain_id"], 16))
        self.assertEqual(chain["block_number"], int(manifest["block"]["number"], 16))
        self.assertEqual(chain["block_hash"], manifest["block"]["hash"].lower())
        self.assertEqual(chain["state_root"], header["state_root"].lower())

    def test_the_counts_are_read_rather_than_computed(self):
        """The rule this capture exists for. Recomputing one would mean deciding
        for Lazarus which of its records were checked against the state root."""
        manifest = read_json(os.path.join(GOLDFINCH, "manifest.json"))
        body = taken(GOLDFINCH)["predicate"]
        self.assertEqual(body["evidence"], manifest["evidence_counts"])

    def test_every_component_the_manifest_declares_is_described(self):
        manifest = read_json(os.path.join(GOLDFINCH, "manifest.json"))
        body = taken(GOLDFINCH)["predicate"]
        self.assertEqual(
            sorted(entry["path"] for entry in body["fixture_subjects"]),
            sorted(entry["path"] for entry in manifest["components"]),
        )

    def test_every_component_digest_is_a_subject(self):
        statement = taken(GOLDFINCH)
        covered = {
            json.dumps(entry["digest"], sort_keys=True) for entry in statement["subject"]
        }
        for entry in statement["predicate"]["fixture_subjects"]:
            with self.subTest(path=entry["path"]):
                self.assertIn(json.dumps(entry["digest"], sort_keys=True), covered)

    def test_replay_is_written_closed_and_is_not_a_parameter(self):
        body = taken(GOLDFINCH)["predicate"]
        self.assertIs(body["replay"]["reaches_network"], False)
        self.assertIs(body["replay"]["canonical_chain_claim"], False)

    def test_the_version_comes_from_the_manifest(self):
        manifest = read_json(os.path.join(GOLDFINCH, "manifest.json"))
        body = taken(GOLDFINCH)["predicate"]
        self.assertEqual(body["capture"]["tool_version"], manifest["tool_version"])

    def test_a_stated_version_that_disagrees_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            taken(GOLDFINCH, capture_version="9.9.9")
        self.assertIn("the manifest is what the tool wrote", str(caught.exception))

    def test_a_stated_version_that_agrees_is_accepted(self):
        manifest = read_json(os.path.join(GOLDFINCH, "manifest.json"))
        self.assertTrue(
            report_for(taken(GOLDFINCH, capture_version=manifest["tool_version"])).ok
        )

    def test_capture_is_deterministic(self):
        self.assertEqual(taken(GOLDFINCH), taken(GOLDFINCH))

    def test_it_records_that_it_did_not_recheck_the_proofs(self):
        body = taken(GOLDFINCH)["predicate"]
        skipped = [c for c in body["claims"] if c["disposition"] == "skipped"]
        reasons = " ".join(c["reason"] for c in skipped)
        self.assertIn("does not re-verify", reasons)
        self.assertIn("canonical", reasons)


class CopiedFixtureTests(SkipUnlessGoldfinch):
    """A copy of the shipped fixture, damaged one way at a time."""

    def setUp(self):
        super(CopiedFixtureTests, self).setUp()
        self.root = tempfile.mkdtemp(prefix="ariadne-fixture-")
        self.fixture = os.path.join(self.root, "goldfinch-v0")
        shutil.copytree(GOLDFINCH, self.fixture)
        self.addCleanup(shutil.rmtree, self.root, True)

    def manifest(self):
        with open(os.path.join(self.fixture, "manifest.json")) as handle:
            return json.load(handle)

    def rewrite(self, manifest):
        with open(os.path.join(self.fixture, "manifest.json"), "w") as handle:
            json.dump(manifest, handle)

    def refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            taken(self.fixture)
        return str(caught.exception)

    def test_the_copy_captures_clean(self):
        """The control. Without it every refusal below could be the copy."""
        self.assertTrue(report_for(taken(self.fixture)).ok)

    def test_a_missing_manifest_is_refused(self):
        os.unlink(os.path.join(self.fixture, "manifest.json"))
        self.assertIn("has no manifest.json", self.refused())

    def test_a_manifest_that_is_not_json_is_refused(self):
        with open(os.path.join(self.fixture, "manifest.json"), "w") as handle:
            handle.write("{not json")
        self.assertIn("is not JSON", self.refused())

    def test_a_manifest_that_is_a_list_is_refused(self):
        with open(os.path.join(self.fixture, "manifest.json"), "w") as handle:
            handle.write("[]")
        self.assertIn("rather than an object", self.refused())

    def test_a_manifest_carrying_nan_is_refused(self):
        """`json.loads` accepts NaN as a Python extension, and every comparison
        against it is false including the one that would refuse it."""
        with open(os.path.join(self.fixture, "manifest.json"), "w") as handle:
            handle.write('{"schema_version": 1, "evidence_counts": {"proof_backed": NaN}}')
        self.assertIn("which is not JSON", self.refused())

    def test_each_manifest_field_this_capture_reads_is_required(self):
        for field in capture.MANIFEST_REQUIRED:
            manifest = self.manifest()
            del manifest[field]
            self.rewrite(manifest)
            with self.subTest(field=field):
                self.assertIn(field, self.refused())
            self.rewrite(self.manifest())
            shutil.rmtree(self.fixture)
            shutil.copytree(GOLDFINCH, self.fixture)

    def test_a_later_schema_version_is_refused(self):
        manifest = self.manifest()
        manifest["schema_version"] = 2
        self.rewrite(manifest)
        self.assertIn("this capture reads 1", self.refused())

    def test_a_boolean_schema_version_is_refused(self):
        """`True == 1` in Python, so a plain inequality let `true` through the one
        check that refuses a manifest this capture cannot read. Found by sweeping
        the manifest with values that satisfy a presence test."""
        manifest = self.manifest()
        manifest["schema_version"] = True
        self.rewrite(manifest)
        self.assertIn("schema_version", self.refused())

    def test_a_fixture_digest_that_is_not_a_digest_is_refused(self):
        """The field is required and unused. Requiring it and accepting any value
        would be a presence test carrying nothing, and it would let this capture
        call a document a Lazarus manifest on the strength of a key holding
        `{"a": 1}`."""
        for value in (None, "", "   ", 0, True, [], {}, {"a": 1}, "beef",
                      "F" * 64, "0x" + "a" * 64):
            manifest = self.manifest()
            manifest["fixture_digest"] = value
            self.rewrite(manifest)
            with self.subTest(fixture_digest=value):
                self.assertIn("fixture_digest", self.refused())

    def test_a_real_fixture_digest_is_accepted(self):
        manifest = self.manifest()
        manifest["fixture_digest"] = "a" * 64
        self.rewrite(manifest)
        self.assertTrue(report_for(taken(self.fixture)).ok)

    def test_the_capture_does_not_use_the_manifests_fixture_digest(self):
        """It is Lazarus's digest over Lazarus's listing, by a method this tool has
        not reimplemented. Presenting it as the digest of what Ariadne read would
        assert a derivation nobody here performed."""
        manifest = self.manifest()
        before = taken(self.fixture)["predicate"]["deltas"]["current"]["digest"]
        manifest["fixture_digest"] = "b" * 64
        self.rewrite(manifest)
        after = taken(self.fixture)["predicate"]["deltas"]["current"]["digest"]
        self.assertEqual(before, after)
        self.assertNotIn("b" * 64, json.dumps(taken(self.fixture)))

    def test_a_missing_header_leaves_the_state_root_out(self):
        """A capture that proved nothing has no use for one, and the predicate's
        evidence check is what refuses a proof-backed count without it."""
        os.unlink(os.path.join(self.fixture, "header.json"))
        manifest = self.manifest()
        manifest["components"] = [
            c for c in manifest["components"] if c["path"] != "header.json"
        ]
        manifest["evidence_counts"] = {
            "proof_backed": 0,
            "header_bound": 0,
            "recorded_rpc": 4,
        }
        self.rewrite(manifest)
        body = taken(self.fixture)["predicate"]
        self.assertNotIn("state_root", body["chain"])
        self.assertTrue(report_for(taken(self.fixture)).ok)

    def test_a_missing_header_beside_proved_records_fails_the_statement(self):
        """The capture writes it, and the predicate refuses it. The claim written
        beside it says why, so a reader of the capture's output sees the reason
        before running verify."""
        os.unlink(os.path.join(self.fixture, "header.json"))
        manifest = self.manifest()
        manifest["components"] = [
            c for c in manifest["components"] if c["path"] != "header.json"
        ]
        self.rewrite(manifest)
        statement = taken(self.fixture)
        report = report_for(statement)
        self.assertFalse(report.ok)
        failed = [g.name for g in report.gates if not g.passed]
        self.assertEqual(failed, ["evidence"])
        stated = [c for c in statement["predicate"]["claims"] if c["disposition"] == "failed"]
        self.assertTrue(stated)
        self.assertIn("no state root", stated[0]["reason"])

    def test_a_component_the_directory_lacks_is_refused(self):
        os.unlink(os.path.join(self.fixture, "plan.json"))
        self.assertIn("which the fixture does not hold", self.refused())

    def test_a_file_the_manifest_does_not_declare_is_refused(self):
        with open(os.path.join(self.fixture, "notes.txt"), "w") as handle:
            handle.write("added later\n")
        message = self.refused()
        self.assertIn("notes.txt", message)
        self.assertIn("does not declare", message)

    def test_a_digest_that_disagrees_is_refused(self):
        with open(os.path.join(self.fixture, "plan.json"), "ab") as handle:
            handle.write(b"\n")
        self.assertIn("and it digests to", self.refused())

    def test_a_byte_count_that_disagrees_is_refused(self):
        manifest = self.manifest()
        for entry in manifest["components"]:
            if entry["path"] == "plan.json":
                entry["bytes"] = entry["bytes"] + 1
        self.rewrite(manifest)
        message = self.refused()
        self.assertIn("plan.json", message)
        self.assertIn("bytes", message)

    def test_a_component_path_leaving_the_fixture_is_refused(self):
        manifest = self.manifest()
        manifest["components"][0]["path"] = "../outside.json"
        self.rewrite(manifest)
        self.assertIn("fixture-relative", self.refused())

    def test_a_component_declared_twice_is_refused(self):
        manifest = self.manifest()
        manifest["components"].append(dict(manifest["components"][0]))
        self.rewrite(manifest)
        self.assertIn("twice", self.refused())

    def test_an_evidence_class_left_out_is_refused(self):
        for name in predicate.EVIDENCE_CLASSES:
            manifest = self.manifest()
            del manifest["evidence_counts"][name]
            self.rewrite(manifest)
            with self.subTest(evidence_class=name):
                self.assertIn(name, self.refused())
            self.rewrite(self.manifest())
            shutil.rmtree(self.fixture)
            shutil.copytree(GOLDFINCH, self.fixture)

    def test_an_unknown_evidence_class_is_refused(self):
        manifest = self.manifest()
        manifest["evidence_counts"]["trusted_oracle"] = 3
        self.rewrite(manifest)
        self.assertIn("trusted_oracle", self.refused())

    def test_a_boolean_count_is_refused(self):
        manifest = self.manifest()
        manifest["evidence_counts"]["header_bound"] = True
        self.rewrite(manifest)
        self.assertIn("whole number", self.refused())

    def test_a_count_over_the_ceiling_is_refused(self):
        manifest = self.manifest()
        manifest["evidence_counts"]["recorded_rpc"] = predicate.MAX_COUNT + 1
        self.rewrite(manifest)
        self.assertIn("whole number", self.refused())

    def test_a_symlinked_component_is_refused(self):
        target = os.path.join(self.fixture, "plan.json")
        moved = os.path.join(self.root, "plan.json")
        shutil.move(target, moved)
        os.symlink(moved, target)
        self.assertIn("symlink", self.refused())

    def test_a_hex_quantity_with_a_leading_zero_is_refused(self):
        """Two spellings of one number would give two statements for one fixture."""
        manifest = self.manifest()
        manifest["block"]["number"] = "0x0c7da16"
        self.rewrite(manifest)
        self.assertIn("leading zero", self.refused())

    def test_a_decimal_block_number_is_refused(self):
        manifest = self.manifest()
        manifest["block"]["number"] = 13097494
        self.rewrite(manifest)
        self.assertIn("hex quantity", self.refused())

    def test_an_unset_block_hash_is_refused(self):
        manifest = self.manifest()
        manifest["block"]["hash"] = predicate.ZERO_HASH
        self.rewrite(manifest)
        self.assertIn("identifies something", self.refused())

    def test_an_uppercased_block_hash_is_lowered_rather_than_refused(self):
        """Lazarus accepts either case and this predicate accepts only lowercase,
        so the conversion belongs here. It is the same value."""
        manifest = self.manifest()
        manifest["block"]["hash"] = manifest["block"]["hash"].upper().replace("0X", "0x")
        self.rewrite(manifest)
        body = taken(self.fixture)["predicate"]
        self.assertEqual(body["chain"]["block_hash"], manifest["block"]["hash"].lower())

    def test_a_comparison_against_a_previous_capture(self):
        other = os.path.join(self.root, "goldfinch-v1")
        shutil.copytree(GOLDFINCH, other)
        statement = taken(
            self.fixture, previous=other, previous_name="goldfinch-v0",
            name="goldfinch-v1", first_capture_reason=None,
        )
        report = report_for(statement)
        self.assertTrue(report.ok, [g.line() for g in report.gates if not g.passed])
        deltas = statement["predicate"]["deltas"]
        self.assertEqual(deltas["baseline"]["name"], "goldfinch-v0")
        self.assertEqual(deltas["current"]["name"], "goldfinch-v1")

    def test_a_comparison_against_itself_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            taken(self.fixture, previous=self.fixture, previous_name="itself")
        self.assertIn("records nothing", str(caught.exception))


class ArgumentTests(SkipUnlessGoldfinch):
    def test_the_tool_name_has_no_default(self):
        for value in (None, "", "   "):
            with self.subTest(tool=value):
                with self.assertRaises(capture.CaptureError) as caught:
                    taken(GOLDFINCH, capture_tool=value)
                self.assertIn("does not name the tool", str(caught.exception))

    def test_the_command_is_required_as_an_argv(self):
        for value in (None, [], ["forge", ""], ["forge", "  "], [1]):
            with self.subTest(command=value):
                with self.assertRaises(capture.CaptureError):
                    taken(GOLDFINCH, capture_command=value)

    def test_a_name_is_required(self):
        for value in (None, "", "   "):
            with self.subTest(name=value):
                with self.assertRaises(capture.CaptureError):
                    taken(GOLDFINCH, name=value)

    def test_a_first_capture_needs_its_reason(self):
        for value in (None, "", "   "):
            with self.subTest(reason=value):
                with self.assertRaises(capture.CaptureError) as caught:
                    taken(GOLDFINCH, first_capture_reason=value)
                self.assertIn("--first-capture-reason", str(caught.exception))

    def test_a_previous_needs_its_name(self):
        with self.assertRaises(capture.CaptureError) as caught:
            taken(GOLDFINCH, previous=GOLDFINCH, previous_name=None)
        self.assertIn("--previous-name", str(caught.exception))

    def test_a_fixture_that_is_not_a_directory_is_refused(self):
        with self.assertRaises(capture.CaptureError):
            taken(os.path.join(GOLDFINCH, "manifest.json"))

    def test_the_parameters_digest_covers_the_parameters(self):
        one = taken(GOLDFINCH, parameters={"a": 1})
        two = taken(GOLDFINCH, parameters={"a": 2})
        same = taken(GOLDFINCH, parameters={"a": 1})
        self.assertNotEqual(
            one["predicate"]["capture"]["parameters_digest"],
            two["predicate"]["capture"]["parameters_digest"],
        )
        self.assertEqual(
            one["predicate"]["capture"]["parameters_digest"],
            same["predicate"]["capture"]["parameters_digest"],
        )

    def test_the_parameters_digest_does_not_depend_on_key_order(self):
        one = taken(GOLDFINCH, parameters={"a": 1, "b": 2})
        two = taken(GOLDFINCH, parameters={"b": 2, "a": 1})
        self.assertEqual(
            one["predicate"]["capture"]["parameters_digest"],
            two["predicate"]["capture"]["parameters_digest"],
        )


class WriteTests(unittest.TestCase):
    def test_a_statement_is_replaced_rather_than_truncated(self):
        directory = tempfile.mkdtemp(prefix="ariadne-write-")
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "statement.json")
        capture.write(path, '{"first": true}')
        capture.write(path, '{"second": true}')
        with open(path) as handle:
            self.assertEqual(json.load(handle), {"second": True})
        leftovers = [n for n in os.listdir(directory) if n.startswith(".ariadne-")]
        self.assertEqual(leftovers, [])

    def test_a_failed_write_leaves_no_temporary_file(self):
        directory = tempfile.mkdtemp(prefix="ariadne-write-")
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "statement.json")

        # `write` takes text. Handing it something else fails inside the `with`,
        # which is the moment the temporary file exists and the replace has not
        # happened. An earlier version of this test subclassed `str` and overrode
        # `__len__`, which `handle.write` never calls, so it raised nothing and
        # passed for the wrong reason.
        with self.assertRaises(TypeError):
            capture.write(path, 12345)
        leftovers = [n for n in os.listdir(directory) if n.startswith(".ariadne-")]
        self.assertEqual(leftovers, [])
        self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
