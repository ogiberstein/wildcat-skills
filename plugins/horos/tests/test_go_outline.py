"""The Go outliner slices keyword-led declarations and confesses the rest."""

from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

from languages.go import go  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN / "examples" / "fixture-go" / "market.go"

EXPECTED = """module: Package market is a fixture for the Horos Go outliner.
package market
import (
    "fmt"
    "math/big"
import "errors"
const DefaultTimeout
const (
    StateOpen
    StateDelinquent
    StateClosed
var registry
var (
    ErrNotFound
    maxRetries  int
type Address [20]byte
type MarketFilter = func(*Market) bool
type Market struct
type (
    Snapshot struct
    Watcher interface
func FetchSnapshot(addr Address, block uint64) (*Snapshot, error)
func (m *Market) FormatAPR() string
func Filter[T any](items []T, keep func(T) bool) []T
func joinLabels(
\tprefix string,
\tlabels ...string,
) string
declarations: 24
unparsed: none
"""


def run(source):
    out = io.StringIO()
    code = go.outline("test.go", source, out)
    return code, out.getvalue()


class GoOutlineTests(unittest.TestCase):
    def test_the_fixture_outline_is_pinned(self):
        source = FIXTURE.read_text(encoding="utf-8")
        out = io.StringIO()
        code = go.outline(str(FIXTURE), source, out)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), EXPECTED)

    def test_bodies_never_leak_into_the_outline(self):
        source = FIXTURE.read_text(encoding="utf-8")
        _, output = run(source)
        self.assertNotIn("registry[fmt.Sprintf", output)
        self.assertNotIn("out = append", output)

    def test_a_raw_string_spans_lines_and_keeps_backslashes_plain(self):
        code, output = run(
            "package p\n\nvar tmpl = `line one \\n\nfunc fake() {\n`\n\nfunc Real() {}\n"
        )
        self.assertEqual(code, 0)
        lines = output.splitlines()
        self.assertIn("func Real()", lines)
        self.assertNotIn("func fake()", output)
        self.assertIn("var tmpl", lines)

    def test_rune_literals_holding_quotes_do_not_derail(self):
        code, output = run(
            "package p\n\nconst quote = '\"'\nconst escaped = '\\''\n\nfunc F() {}\n"
        )
        self.assertEqual(code, 0)
        self.assertIn("func F()", output.splitlines())
        self.assertIn("unparsed: none", output)

    def test_a_method_keeps_its_receiver_in_the_slice(self):
        _, output = run("package p\n\nfunc (s *Store) Get(k string) int { return 0 }\n")
        self.assertIn("func (s *Store) Get(k string) int", output.splitlines())

    def test_a_bodyless_func_is_sliced_whole(self):
        _, output = run("package p\n\nfunc add(x, y int) int\n")
        self.assertIn("func add(x, y int) int", output.splitlines())

    def test_an_unmatched_statement_is_confessed_by_line(self):
        code, output = run("package p\n\nfmt.Println(1)\n")
        self.assertEqual(code, 0)
        self.assertIn("unparsed: 1 region(s): line 3", output)

    def test_an_unterminated_string_confesses_the_remainder(self):
        code, output = run('package p\n\nvar s = "open\nfunc After() {}\n')
        self.assertEqual(code, 1)
        self.assertIn("lexer: unterminated string at line 3", output)
        self.assertNotIn("unparsed: none", output)

    def test_grouped_const_with_iota_emits_every_member(self):
        _, output = run("package p\n\nconst (\n\tA = iota\n\tB\n\tC\n)\n")
        lines = output.splitlines()
        for name in ("A", "B", "C"):
            self.assertIn(f"    {name}", lines)

    def test_a_group_comment_line_emits_nothing(self):
        _, output = run('package p\n\nimport (\n\t// stdlib\n\t"fmt"\n)\n')
        lines = [line for line in output.splitlines() if line.startswith("    ")]
        self.assertEqual(lines, ['    "fmt"'])

    def test_the_go_suffix_dispatches_through_the_registry(self):
        import horos  # noqa: E402  (registry dispatch under test)

        out = io.StringIO()
        self.assertEqual(horos.map_file(str(FIXTURE), out=out), 0)
        self.assertIn(".go", __import__("languages").supported())

    def test_module_header_falls_back_when_absent(self):
        _, output = run("package p\n")
        self.assertIn("module: (no header comment)", output)


if __name__ == "__main__":
    unittest.main()
