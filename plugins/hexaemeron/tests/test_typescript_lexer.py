"""The shared lexer retains the Horos TypeScript lexical boundary."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import typescript_lexer as ts  # noqa: E402


def kinds(source):
    spans, _ = ts.lex(source)
    return [(kind, source[start:end]) for kind, start, end in spans]


def only(source, kind):
    return [text for current, text in kinds(source) if current == kind]


class TypeScriptLexerTests(unittest.TestCase):
    def test_spans_reconstruct_the_complete_source(self):
        source = 'const a = "x"; // done\nconst b = /two/g;\n'
        spans, errors = ts.lex(source)
        self.assertEqual([], errors)
        self.assertEqual(source, "".join(source[start:end] for _, start, end in spans))

    def test_strings_and_both_comment_forms_are_separate_spans(self):
        source = '// line\n/* block\nstill */ const value = "a\\\"b";\n'
        self.assertEqual(["// line"], only(source, "line_comment"))
        self.assertEqual(["/* block\nstill */"], only(source, "block_comment"))
        self.assertEqual(['"a\\\"b"'], only(source, "string"))

    def test_templates_nest_two_deep(self):
        source = "const value = `a${ {b: `c${d}e`} }f`;\n"
        self.assertEqual(["`a${ {b: `c${d}e`} }f`"], only(source, "template"))

    def test_regex_is_distinguished_from_division(self):
        source = "const match = /[a/b]+/gi; const ratio = total / 2;\n"
        self.assertEqual(["/[a/b]+/gi"], only(source, "regex"))

    def test_unterminated_construct_reports_offset_and_covers_remainder(self):
        source = "const value = `open ${name};\n"
        spans, errors = ts.lex(source)
        self.assertEqual(1, len(errors))
        self.assertEqual(source.index("`"), errors[0][0])
        self.assertIn("unterminated template", errors[0][1])
        self.assertEqual(("template", source.index("`"), len(source)), spans[-1])

    def test_multiline_jsx_attribute_string_is_one_span(self):
        source = (
            '<Tooltip value="first line\n'
            '  second line" />\n'
        )
        spans, errors = ts.lex(source)
        self.assertEqual([], errors)
        self.assertEqual(
            ['"first line\n  second line"'],
            [source[start:end] for kind, start, end in spans if kind == "string"],
        )


if __name__ == "__main__":
    unittest.main()
