"""Scoped entry, and the reproducibility a scoped gate depends on.

Every test here is a fixture for a success criterion this run has not built
yet, so each one is marked as an expected failure. A step that satisfies its
criterion turns the fixture into an unexpected success, which fails the suite
until the decorator comes off: the marker cannot be left behind by accident.
"""

from pathlib import Path
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

GIT = shutil.which("git")

MINIFIED = "var a=1;" * 400 + "\n"


def write(root, relpath, content):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def git(root, *args):
    subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-C", root, *args],
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


def repository():
    """A tracked tree with one ignored build directory holding nothing tracked."""
    tmp = tempfile.TemporaryDirectory()
    root = tmp.name
    git(root, "init", "-q")
    write(root, ".gitignore", "out/\n")
    write(root, "src/app.py", "value = 1\n")
    write(root, "plugins/thing/module.py", "value = 2\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "tracked tree")
    write(root, "out/bundle.min.js", MINIFIED)
    return tmp, root


class PhantomEntryTests(unittest.TestCase):
    """Criterion 4: a directory holding no tracked file is not a hard entry."""

    @unittest.skipIf(GIT is None, "git unavailable")
    @unittest.expectedFailure
    def test_an_ignored_directory_earns_no_hard_entry(self):
        tmp, root = repository()
        self.addCleanup(tmp.cleanup)
        result = horos.scan_tree(root)
        phantom = [
            entry for entry in result["entries"]
            if entry["path"].startswith("out/")
        ]
        self.assertEqual(phantom, [])


class MachineIndependentCheckTests(unittest.TestCase):
    """Criterion 5: check answers the same whatever untracked state is present."""

    @unittest.skipIf(GIT is None, "git unavailable")
    @unittest.expectedFailure
    def test_check_is_clean_beside_an_ignored_build_directory(self):
        tmp, root = repository()
        self.addCleanup(tmp.cleanup)
        shutil.rmtree(os.path.join(root, "out"))
        horos.write_boundary(root, horos.boundary_document(horos.scan_tree(root)))
        horos.write_candidates(root, horos.candidates_document(horos.scan_tree(root)))
        write(root, "out/bundle.min.js", MINIFIED)
        out = io.StringIO()
        self.assertEqual(horos.check_tree(root, out=out), 0, out.getvalue())


class ScopedCheckTests(unittest.TestCase):
    """Criterion 7: a descendant scope resolves the one ancestor boundary."""

    @unittest.skipIf(GIT is None, "git unavailable")
    @unittest.expectedFailure
    def test_a_descendant_scope_resolves_the_ancestor_boundary(self):
        tmp, root = repository()
        self.addCleanup(tmp.cleanup)
        shutil.rmtree(os.path.join(root, "out"))
        horos.write_boundary(root, horos.boundary_document(horos.scan_tree(root)))
        horos.write_candidates(root, horos.candidates_document(horos.scan_tree(root)))
        out = io.StringIO()
        scope = os.path.join(root, "plugins", "thing")
        self.assertEqual(horos.check_tree(scope, out=out), 0, out.getvalue())


if __name__ == "__main__":
    unittest.main()
