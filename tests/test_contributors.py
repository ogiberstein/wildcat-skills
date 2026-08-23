"""Hold the contributor generator's host-identity set equal to Fiat's.

ADR-016 names one mechanical set of runtime host identities and Fiat's
controller owns it. scripts/contributors.py keeps a copy so it stays a
standalone root script with no cross-plugin import. A copy that nothing checks
stops agreeing, so these tests read the frozensets straight out of hexctl.py's
syntax tree and compare them. Either side edited alone fails here.
"""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import contributors  # noqa: E402

HEXCTL = REPOSITORY_ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
SET_NAMES = ("HOST_IDENTITY_NAMES", "HOST_IDENTITY_EMAILS", "HOST_PR_LOGINS")


def frozensets_from_source(path: Path) -> dict[str, frozenset]:
    """Read `NAME = frozenset({...})` module-level literals without importing."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, frozenset] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in SET_NAMES:
            continue
        call = node.value
        if (
            not isinstance(call, ast.Call)
            or not isinstance(call.func, ast.Name)
            or call.func.id != "frozenset"
            or len(call.args) != 1
        ):
            raise AssertionError(f"{target.id} in {path.name} is not a frozenset literal")
        found[target.id] = frozenset(ast.literal_eval(call.args[0]))
    return found


class HostSetParity(unittest.TestCase):
    """The generator's copy of the host set matches Fiat's declaration."""

    @classmethod
    def setUpClass(cls):
        cls.declared = frozensets_from_source(HEXCTL)

    def test_hexctl_declares_every_expected_set(self):
        self.assertEqual(sorted(self.declared), sorted(SET_NAMES))
        for name in SET_NAMES:
            self.assertTrue(self.declared[name], f"{name} is empty in hexctl.py")

    def test_host_identity_names_match(self):
        self.assertEqual(
            contributors.HOST_IDENTITY_NAMES,
            self.declared["HOST_IDENTITY_NAMES"],
        )

    def test_host_identity_emails_match(self):
        self.assertEqual(
            contributors.HOST_IDENTITY_EMAILS,
            self.declared["HOST_IDENTITY_EMAILS"],
        )

    def test_host_pr_logins_match(self):
        self.assertEqual(
            contributors.HOST_PR_LOGINS,
            self.declared["HOST_PR_LOGINS"],
        )

    def test_is_host_identity_agrees_on_every_declared_entry(self):
        """Equal sets are not enough; the predicate over them must also agree."""
        for name in sorted(self.declared["HOST_IDENTITY_NAMES"]):
            self.assertTrue(
                contributors.is_host_identity(name, "person@example.com"),
                f"{name!r} is a declared host name but was not recognised",
            )
            self.assertTrue(
                contributors.is_host_identity(name.upper(), "person@example.com"),
                f"{name!r} must be recognised case-insensitively",
            )
        for email in sorted(self.declared["HOST_IDENTITY_EMAILS"]):
            self.assertTrue(
                contributors.is_host_identity("A Person", email),
                f"{email!r} is a declared host email but was not recognised",
            )

    def test_a_human_author_is_not_a_host_identity(self):
        self.assertFalse(contributors.is_host_identity("Dave Coleman", "dave@example.com"))
        self.assertFalse(contributors.is_host_identity("Radu P", "radu@example.com"))
        self.assertFalse(contributors.is_host_identity("", ""))


class LoginGrammar(unittest.TestCase):
    """Only a login that cannot carry Markdown reaches an artefact."""

    def test_accepts_real_login_shapes(self):
        for login in ("kethcode", "radup1337", "a", "a-b", "A1", "x" * 39):
            self.assertTrue(contributors.valid_login(login), login)

    def test_rejects_markdown_and_out_of_range(self):
        for login in (
            "",
            "x" * 40,
            "-leading",
            "trailing-",
            "has space",
            "[link](http://example.com)",
            "back`tick",
            "under_score",
            "claude[bot]",
            "app/claude",
            "semi;colon",
            "new\nline",
        ):
            self.assertFalse(contributors.valid_login(login), login)

    def test_host_logins_are_recognised(self):
        for login in sorted(contributors.HOST_PR_LOGINS):
            self.assertTrue(contributors.is_host_login(login), login)
        self.assertTrue(contributors.is_host_login("CLAUDE[BOT]"))
        self.assertFalse(contributors.is_host_login("kethcode"))


if __name__ == "__main__":
    unittest.main()
