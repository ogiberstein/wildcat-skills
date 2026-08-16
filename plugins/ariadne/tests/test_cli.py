"""The two subcommands that exist at this point, and their exit codes."""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import envelope, statement  # noqa: E402

STATEMENT = {
    "_type": statement.STATEMENT_TYPE,
    "subject": [{"name": "Escrow", "digest": {"sha256": "ab" * 32}}],
    "predicateType": "https://ariadne.wildcat.finance/example/v1",
    "predicate": {"claims": []},
}


def run(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ariadne.main(argv)
    return code, out.getvalue(), err.getvalue()


class PredicatesTests(unittest.TestCase):
    def test_predicates_lists_the_solidity_release_predicate(self):
        code, out, _ = run(["predicates"])
        self.assertEqual(code, 0)
        self.assertIn("https://ariadne.wildcat.finance/solidity-release/v1", out)

    def test_predicates_json_carries_the_type_and_summary(self):
        code, out, _ = run(["predicates", "--json"])
        self.assertEqual(code, 0)
        found = json.loads(out)
        self.assertEqual(
            [entry["type"] for entry in found],
            ["https://ariadne.wildcat.finance/solidity-release/v1"],
        )
        self.assertTrue(all(entry["summary"] for entry in found))


class InspectTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, name, content):
        path = os.path.join(self.root, name)
        with open(path, "wb") as handle:
            handle.write(content if isinstance(content, bytes) else content.encode())
        return path

    def test_a_bare_statement_is_reported_unsigned(self):
        path = self.write("statement.json", json.dumps(STATEMENT))
        code, out, _ = run(["inspect", path])
        self.assertEqual(code, 0)
        self.assertIn("unsigned", out)
        self.assertIn("Escrow", out)
        self.assertIn("not registered here", out)

    def test_an_envelope_is_unwrapped_and_reported(self):
        wrapped = envelope.wrap(json.dumps(STATEMENT).encode("utf-8"))
        path = self.write("envelope.json", wrapped.to_json())
        code, out, _ = run(["inspect", path, "--json"])
        self.assertEqual(code, 0)
        found = json.loads(out)
        self.assertEqual(found["predicateType"], STATEMENT["predicateType"])
        self.assertFalse(found["predicateTypeKnown"])
        self.assertIn("unsigned", found["signatureState"])

    def test_a_missing_file_exits_two(self):
        code, _, err = run(["inspect", os.path.join(self.root, "absent.json")])
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)

    def test_a_malformed_statement_exits_two_with_the_reason(self):
        path = self.write("bad.json", json.dumps({"_type": "wrong"}))
        code, _, err = run(["inspect", path])
        self.assertEqual(code, 2)
        self.assertIn("_type", err)

    def test_a_deeply_nested_file_exits_two_rather_than_one(self):
        """Exit 1 means a gate was breached. Unreadable input is exit 2, and an
        escaping RecursionError would have reported the wrong one."""
        depth = 200000
        path = self.write("deep.json", '{"a":' * depth + "1" + "}" * depth)
        code, _, err = run(["inspect", path])
        self.assertEqual(code, 2)
        self.assertIn("nested deeper", err)

    def test_no_subcommand_prints_help_and_exits_two(self):
        code, _, _ = run([])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
