"""The C++ outliner slices declarations verbatim and confesses the rest."""

from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

from languages.cpp import cpp  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN / "examples" / "fixture-cpp" / "market.hpp"

EXPECTED = """module: A fixture market header for the Horos C++ outliner.
#include <cstdint>
#include <map>
#include <string>
#define MARKET_VERSION 2
#define MARKET_JOIN(a, b)
namespace wildcat::market
enum class State : uint8_t
struct Snapshot
    std::string address
    uint64_t capacity
    double apr
using SnapshotMap = std::map<std::string, Snapshot>
typedef unsigned int BasisPoints
constexpr char const* kQuery
class MarketWatcher
    explicit MarketWatcher(SnapshotMap initial):
    m_snapshots(std::move(initial))
    Snapshot const& refresh(std::string const& address)
    template <typename Predicate>
    SnapshotMap filtered(Predicate _keep) const
    static MarketWatcher fromQuery(std::string const& query = kQuery)
    SnapshotMap m_snapshots
    uint64_t m_refreshes
template <typename T>
T clampApr(T value, T low, T high)
std::string formatApr(double apr)
extern "C"
int market_abi_version(void)
static_assert(MARKET_VERSION == 2, "fixture version drift")
declarations: 26
unparsed: none
"""


def run(source):
    out = io.StringIO()
    code = cpp.outline("test.hpp", source, out)
    return code, out.getvalue()


class CppOutlineTests(unittest.TestCase):
    def test_the_fixture_outline_is_pinned(self):
        source = FIXTURE.read_text(encoding="utf-8")
        out = io.StringIO()
        code = cpp.outline(str(FIXTURE), source, out)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), EXPECTED)

    def test_bodies_never_leak_into_the_outline(self):
        source = FIXTURE.read_text(encoding="utf-8")
        _, output = run(source)
        self.assertNotIn("out[address] = snapshot", output)
        self.assertNotIn("value < low", output)

    def test_a_raw_string_with_a_custom_delimiter_is_inert(self):
        code, output = run(
            'const char* q = R"x(quote " and paren ) and class Fake { )" )x";\n'
            "int real();\n"
        )
        self.assertEqual(code, 0)
        self.assertIn("int real()", output.splitlines())
        self.assertNotIn("class Fake", "\n".join(
            line for line in output.splitlines() if line.startswith("class")
        ))
        self.assertIn("unparsed: none", output)

    def test_a_define_with_a_brace_never_leaks_into_the_mask(self):
        code, output = run("#define OPEN {\nint f();\nint g();\n")
        self.assertEqual(code, 0)
        lines = output.splitlines()
        self.assertIn("int f()", lines)
        self.assertIn("int g()", lines)
        self.assertIn("#define OPEN {", lines)

    def test_a_multiline_directive_is_one_span(self):
        code, output = run("#define JOIN(a, b) \\\n\ta##b\nint after();\n")
        self.assertEqual(code, 0)
        self.assertIn("int after()", output.splitlines())
        self.assertIn("unparsed: none", output)

    def test_a_digit_separator_is_not_a_character_literal(self):
        code, output = run("int big = 1'000'000;\nint after();\n")
        self.assertEqual(code, 0)
        self.assertIn("int after()", output.splitlines())
        self.assertIn("unparsed: none", output)

    def test_allman_braces_keep_the_body_with_its_head(self):
        code, output = run("int f(int x)\n{\n\treturn x;\n}\nint g();\n")
        self.assertEqual(code, 0)
        lines = output.splitlines()
        self.assertIn("int f(int x)", lines)
        self.assertIn("int g()", lines)
        self.assertNotIn("return x;", output)

    def test_a_template_prefix_emits_like_a_decorator(self):
        _, output = run("template <typename T>\nclass Box { T value; };\n")
        lines = output.splitlines()
        self.assertIn("template <typename T>", lines)
        self.assertIn("class Box", lines)

    def test_access_labels_are_skipped_without_confession(self):
        _, output = run("class C {\npublic:\n\tint f();\nprivate:\n\tint x;\n};\n")
        self.assertNotIn("public", output)
        self.assertIn("    int f()", output.splitlines())
        self.assertIn("unparsed: none", output)

    def test_a_constructor_without_a_return_type_slices(self):
        _, output = run("class C {\n\tC(int x): m_x(x) {}\n};\n")
        self.assertIn("    C(int x):", output.splitlines()[2])

    def test_namespaces_recurse(self):
        _, output = run("namespace a {\nnamespace b {\nint f();\n}\n}\n")
        lines = output.splitlines()
        self.assertIn("namespace a", lines)
        self.assertIn("namespace b", lines)
        self.assertIn("int f()", lines)

    def test_an_unmatched_statement_is_confessed_by_line(self):
        code, output = run("int x = 1;\nfor (;;) { spin(); }\n")
        self.assertEqual(code, 0)
        self.assertIn("unparsed: 1 region(s): line 2", output)

    def test_an_unterminated_raw_string_confesses_the_remainder(self):
        code, output = run('int a = 1;\nconst char* q = R"x(open\nint later();\n')
        self.assertEqual(code, 1)
        self.assertIn("lexer: unterminated raw string at line 2", output)
        self.assertNotIn("unparsed: none", output)

    def test_the_cpp_suffixes_dispatch_through_the_registry(self):
        import horos  # noqa: E402  (registry dispatch under test)

        out = io.StringIO()
        self.assertEqual(horos.map_file(str(FIXTURE), out=out), 0)
        supported = __import__("languages").supported()
        for suffix in (".cpp", ".h", ".hpp"):
            self.assertIn(suffix, supported)


if __name__ == "__main__":
    unittest.main()
