"""Secrets in a build command, and paths that leave the project."""

import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import scrub  # noqa: E402
from ariadne_lib.capture import foundry  # noqa: E402

FIXTURES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "forge-project"
)
V2 = os.path.join(FIXTURES, "v2")
SECRET = "9f4b2c8e1a7d3f6b0c5e8a2d4f7b1c3e"  # phylax: allow scrubbing fixture, not a live credential
# Shaped like a credential without imitating any provider's prefix: a
# scanner that flags test data is a scanner people learn to bypass.
KEY = "ariadne_TESTONLY_A1b2C3d4E5f6G7h8I9j0K1"


class ScrubTests(unittest.TestCase):
    def test_a_url_keeps_its_scheme_and_loses_the_rest(self):
        self.assertEqual(
            scrub.token("https://eth-mainnet.example/v2/" + SECRET),
            "https://<redacted>",
        )

    def test_a_key_shaped_token_is_redacted(self):
        self.assertEqual(scrub.token(KEY), "<redacted>")

    def test_a_long_ordinary_word_survives(self):
        self.assertEqual(
            scrub.token("--optimizer-runs-are-not-secrets-at-all-here"),
            "--optimizer-runs-are-not-secrets-at-all-here",
        )

    def test_an_address_survives_because_a_statement_needs_it(self):
        address = "0x" + "e5" * 20
        self.assertEqual(scrub.token(address), address)

    def test_a_thirty_two_byte_hex_string_is_redacted(self):
        self.assertEqual(scrub.token("0x" + "ab" * 32), "<redacted>")

    def test_the_value_after_a_secret_flag_goes_whatever_it_looks_like(self):
        self.assertEqual(
            scrub.argv(["forge", "test", "--rpc-url", "http://localhost:8545"]),
            ["forge", "test", "--rpc-url", "<redacted>"],
        )

    def test_a_flag_joined_by_an_equals_sign_is_caught_too(self):
        self.assertEqual(
            scrub.argv(["forge", "test", "--private-key=" + SECRET]),
            ["forge", "test", "--private-key=<redacted>"],
        )

    def test_the_count_of_redactions_is_available_for_the_record(self):
        """One argument changed: the flag itself stays so the line still reads."""
        self.assertEqual(
            scrub.redacted(["forge", "build", "--rpc-url", "https://x.example/" + KEY]),
            1,
        )
        self.assertEqual(
            scrub.redacted(
                ["forge", "build", "--rpc-url", "https://x.example", "--api-key", KEY]
            ),
            2,
        )

    def test_an_inline_assignment_loses_its_value(self):
        """A key reaches a command line without a flag more often than with one."""
        self.assertEqual(
            scrub.argv(["forge", "script", "PRIVATE_KEY=0x" + "ab" * 32]),
            ["forge", "script", "PRIVATE_KEY=<redacted>"],
        )

    def test_a_secret_flag_joined_by_an_equals_sign_loses_its_whole_value(self):
        self.assertEqual(
            scrub.argv(["forge", "test", "--fork-url=https://x.example/" + KEY]),
            ["forge", "test", "--fork-url=<redacted>"],
        )

    def test_an_ordinary_assignment_keeps_its_shape(self):
        self.assertEqual(
            scrub.argv(["forge", "build", "--optimizer-runs=200"]),
            ["forge", "build", "--optimizer-runs=200"],
        )

    def test_a_repository_url_loses_its_credentials_and_keeps_its_path(self):
        self.assertEqual(
            scrub.credentials("https://user:" + KEY + "@github.com/w/x"),
            "https://github.com/w/x",
        )
        self.assertEqual(
            scrub.credentials("https://github.com/w/x"), "https://github.com/w/x"
        )
        self.assertEqual(scrub.credentials("git@github.com:w/x.git"), "git@github.com:w/x.git")

    def test_an_ordinary_build_command_is_untouched(self):
        command = ["forge", "build", "--sizes"]
        self.assertEqual(scrub.argv(command), command)
        self.assertEqual(scrub.redacted(command), 0)


class CaptureScrubbingTests(unittest.TestCase):
    def test_a_planted_secret_does_not_reach_the_statement(self):
        statement = foundry.capture(
            V2,
            repository="https://github.com/wildcat-finance/example-escrow",
            commit="9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a",
            build_command=[
                "forge",
                "build",
                "--rpc-url",
                "https://eth-mainnet.example/v2/" + SECRET,
                "--etherscan-api-key",
                KEY,
            ],
        )
        body = json.dumps(statement)
        self.assertNotIn(SECRET, body)
        self.assertNotIn(KEY, body)
        self.assertIn("<redacted>", body)

    def test_a_repository_url_carrying_a_token_is_recorded_without_it(self):
        statement = foundry.capture(
            V2,
            repository="https://user:" + KEY + "@github.com/wildcat-finance/example",
            commit="9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a",
        )
        self.assertEqual(
            statement["predicate"]["source"]["repository"],
            "https://github.com/wildcat-finance/example",
        )
        self.assertNotIn(KEY, json.dumps(statement))

    def test_the_statement_records_how_many_arguments_were_redacted(self):
        statement = foundry.capture(
            V2,
            repository="https://github.com/wildcat-finance/example-escrow",
            commit="9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a",
            build_command=["forge", "build", "--rpc-url", "https://x.example/" + KEY],
        )
        command = statement["predicate"]["commands"][0]
        self.assertEqual(command["detail"]["redacted_arguments"], 1)


class PathTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_a_project_whose_out_is_a_symlink_elsewhere_is_refused(self):
        project = os.path.join(self.root, "project")
        os.makedirs(project)
        os.symlink(os.path.join(V2, "out"), os.path.join(project, "out"))
        with self.assertRaises(foundry.CaptureError) as caught:
            foundry.confined(project, "--project")
        self.assertIn("resolves outside it", str(caught.exception))

    def test_a_path_with_a_traversal_that_lands_outside_is_refused(self):
        with self.assertRaises(foundry.CaptureError):
            foundry.confined(os.path.join(V2, "..", "..", "..", "nowhere"), "--project")

    def test_a_traversal_that_lands_back_inside_the_project_is_allowed(self):
        """`..` is not itself the problem; leaving the project is."""
        found = foundry.confined(os.path.join(V2, "src", ".."), "--project")
        self.assertEqual(found, os.path.realpath(V2))

    def test_a_missing_directory_is_refused(self):
        with self.assertRaises(foundry.CaptureError):
            foundry.confined(os.path.join(self.root, "absent"), "--project")

    def test_an_empty_path_is_refused(self):
        with self.assertRaises(foundry.CaptureError):
            foundry.confined("", "--project")


if __name__ == "__main__":
    unittest.main()
