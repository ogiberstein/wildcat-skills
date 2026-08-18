"""The skeleton map prints structure instead of the file, and fails plainly."""

from pathlib import Path
import io
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

import horos  # noqa: E402

FIXTURE = '''"""A fixture module.

Longer prose the map must not print.
"""


def top(a, b=1) -> int:
    """Add things up."""
    return a + b


@staticmethod
def decorated(*args, **kwargs):
    return args


class Outer(dict):
    """Holds an inner class."""

    def method(self, x):
        return x

    class Inner:
        async def fetch(self, url):
            """Get one thing."""
            return url
'''

EXPECTED = """module: A fixture module.
def top(a, b=1) -> int:  # Add things up.
@staticmethod
def decorated(*args, **kwargs):
class Outer(dict):  # Holds an inner class.
    def method(self, x):
    class Inner:
        async def fetch(self, url):  # Get one thing.
"""


def write(root, name, content):
    path = Path(root) / name
    path.write_text(content, encoding="utf-8")
    return str(path)


class MapTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def map(self, path):
        out = io.StringIO()
        code = horos.map_file(path, out=out)
        return code, out.getvalue()

    def test_the_fixture_skeleton_is_pinned(self):
        path = write(self.root, "fixture.py", FIXTURE)
        code, output = self.map(path)
        self.assertEqual(code, 0)
        self.assertEqual(output, EXPECTED)

    def test_the_map_never_prints_bodies_or_long_docstrings(self):
        path = write(self.root, "fixture.py", FIXTURE)
        _, output = self.map(path)
        self.assertNotIn("return a + b", output)
        self.assertNotIn("Longer prose", output)

    def test_a_module_without_a_docstring_says_so(self):
        path = write(self.root, "bare.py", "x = 1\n")
        code, output = self.map(path)
        self.assertEqual(code, 0)
        self.assertEqual(output, "module: (no docstring)\n")

    def test_a_syntax_error_is_a_report_not_a_traceback(self):
        path = write(self.root, "broken.py", "def broken(:\n")
        code, output = self.map(path)
        self.assertEqual(code, 1)
        self.assertIn("syntax error", output)
        self.assertIn("line 1", output)

    def test_an_unregistered_suffix_is_refused_naming_the_supported_list(self):
        path = write(self.root, "notes.txt", "words\n")
        code, output = self.map(path)
        self.assertEqual(code, 2)
        self.assertIn("map supports", output)
        self.assertIn(".py", output)

    def test_a_missing_file_is_a_plain_message(self):
        code, output = self.map(str(Path(self.root) / "absent.py"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", output)


if __name__ == "__main__":
    unittest.main()
