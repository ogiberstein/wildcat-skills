"""The scan's universe: tracked by default, widened on request, walked
when git cannot answer."""

from pathlib import Path
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

GIT = shutil.which("git")


def write(root, relpath, content):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        content = content.encode("utf-8")
    path.write_bytes(content)
    return path


def git(root, *args):
    subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-C", root, *args],
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


@unittest.skipIf(GIT is None, "git unavailable")
class UniverseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        write(self.root, ".gitignore", "ignored.wasm\n")
        write(self.root, "src/app.py", "x = 1\n")
        write(self.root, "tracked.wasm", b"\x00asm\x01\x00\x00\x00")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "seed")
        # Local products that never entered git.
        write(self.root, "untracked.wasm", b"\x00asm\x01\x00\x00\x00")
        write(self.root, "ignored.wasm", b"\x00asm\x01\x00\x00\x00")

    def paths(self, include_untracked=False):
        result = horos.scan_tree(self.root, include_untracked=include_untracked)
        listed = [entry["path"] for entry in result["entries"]]
        return result, listed

    def test_the_default_universe_is_tracked_only(self):
        result, listed = self.paths()
        self.assertEqual(result["universe"], "tracked")
        self.assertIn("tracked.wasm", listed)
        self.assertNotIn("untracked.wasm", listed)
        self.assertNotIn("ignored.wasm", listed)

    def test_include_untracked_widens_but_never_to_ignored(self):
        result, listed = self.paths(include_untracked=True)
        self.assertEqual(result["universe"], "tracked+untracked")
        self.assertIn("tracked.wasm", listed)
        self.assertIn("untracked.wasm", listed)
        self.assertNotIn("ignored.wasm", listed)

    def test_a_non_git_tree_walks_the_filesystem(self):
        with tempfile.TemporaryDirectory() as plain:
            write(plain, "loose.wasm", b"\x00asm\x01\x00\x00\x00")
            result = horos.scan_tree(plain)
            self.assertEqual(result["universe"], "filesystem")
            self.assertIn(
                "loose.wasm", [entry["path"] for entry in result["entries"]]
            )

    def test_the_boundary_document_records_its_universe(self):
        document = horos.boundary_document(horos.scan_tree(self.root))
        self.assertEqual(document["universe"], "tracked")

    def test_check_reproduces_the_committed_universe(self):
        result = horos.scan_tree(self.root, include_untracked=True)
        horos.write_boundary(self.root, horos.boundary_document(result))
        out = io.StringIO()
        code = horos.check_tree(self.root, out=out)
        self.assertEqual(code, 0)
        self.assertIn("boundary matches the tree", out.getvalue())

    def test_an_aggregated_directory_counts_only_universe_files(self):
        write(self.root, "node_modules/dep/package.json", '{"name": "dep"}\n')
        write(self.root, "node_modules/dep/index.js", "module.exports = 1\n")
        git(self.root, "add", "-f", "node_modules")
        git(self.root, "commit", "-q", "-m", "vendor")
        write(self.root, "node_modules/dep/local-cache.js", "cache\n" * 10)
        result = horos.scan_tree(self.root)
        entry = {e["path"]: e for e in result["entries"]}["node_modules/"]
        self.assertEqual(entry["files"], 2)


MINIFIED = "var a=1;" * 400 + "\n"


@unittest.skipIf(GIT is None, "git unavailable")
class BindingDirectoryTests(unittest.TestCase):
    """A hard directory entry must cover at least one file in the universe.

    Without this, a boundary check answers differently on two machines: an
    ignored build directory or a stray worktree is present in one checkout and
    absent from the other, so the check drifts against local state instead of
    against the tree.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        write(self.root, ".gitignore", "node_modules/\nout/\nvendor-only/\n")
        write(self.root, "src/app.py", "value = 1\n")

    def paths(self, result):
        return [entry["path"] for entry in result["entries"]]

    def test_a_vendored_name_holding_nothing_tracked_earns_no_entry(self):
        write(self.root, "node_modules/dep/package.json", '{"name": "dep"}\n')
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "tracked")
        self.assertNotIn("node_modules/", self.paths(horos.scan_tree(self.root)))

    def test_a_corroborated_generated_name_holding_nothing_tracked_earns_no_entry(self):
        write(self.root, "out/bundle.min.js", MINIFIED)
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "tracked")
        self.assertNotIn("out/", self.paths(horos.scan_tree(self.root)))

    def test_one_tracked_file_is_enough_to_bind_the_directory(self):
        write(self.root, "node_modules/dep/package.json", '{"name": "dep"}\n')
        git(self.root, "add", "-f", "node_modules/dep/package.json", "src", ".gitignore")
        git(self.root, "commit", "-q", "-m", "one tracked")
        write(self.root, "node_modules/dep/local-cache.js", "cache\n" * 20)
        write(self.root, "node_modules/other/index.js", "module.exports = 2\n")
        entries = {entry["path"]: entry for entry in horos.scan_tree(self.root)["entries"]}
        self.assertIn("node_modules/", entries)
        self.assertEqual(entries["node_modules/"]["files"], 1)

    def test_an_attribute_matched_directory_holding_nothing_tracked_earns_no_entry(self):
        write(self.root, ".gitattributes", "vendor-only/** linguist-vendored\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "attributes")
        write(self.root, "vendor-only/lib.js", "module.exports = 3\n")
        self.assertNotIn("vendor-only/", self.paths(horos.scan_tree(self.root)))

    def test_the_filesystem_fallback_still_binds_an_untracked_directory(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        write(outside.name, "node_modules/dep/package.json", '{"name": "dep"}\n')
        result = horos.scan_tree(outside.name)
        self.assertEqual(result["universe"], "filesystem")
        self.assertIn("node_modules/", self.paths(result))


if __name__ == "__main__":
    unittest.main()
