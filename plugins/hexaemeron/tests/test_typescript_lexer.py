"""The shared lexer retains the Horos TypeScript lexical boundary."""

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import typescript_lexer as ts  # noqa: E402


def kinds(source):
    spans, _ = ts.lex(source)
    return [(kind, source[start:end]) for kind, start, end in spans]


def only(source, kind):
    return [text for current, text in kinds(source) if current == kind]


def comments(source, *, tsx=False):
    classify = getattr(ts, "comment_spans", None)
    if classify is None:
        raise AssertionError("the shared lexer has no comment-span entry point")
    spans, errors = classify(source, tsx=tsx)
    if errors:
        raise AssertionError(f"unexpected comment-span errors: {errors}")
    return [source[start:end] for _, start, end in spans]


class SliceCountingSource(str):
    """Expose suffix copies made by a scanner without timing assertions."""

    def __new__(cls, value):
        instance = super().__new__(cls, value)
        instance.suffix_slice_count = 0
        return instance

    def __getitem__(self, key):
        if isinstance(key, slice) and key.stop is None:
            self.suffix_slice_count += 1
        return super().__getitem__(key)


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

    def test_comment_spans_open_template_substitutions_only(self):
        source = (
            "const raw = `// not a comment`;\n"
            "const value = `${item // line comment\n"
            "  + `${other /* nested comment */}`}`;\n"
        )
        self.assertEqual(
            ["// line comment", "/* nested comment */"],
            comments(source),
        )

    def test_tsx_comment_spans_exclude_child_text_and_keep_code_comments(self):
        source = (
            "const view = (\n"
            "  <p>// visible child text\n"
            "    <span>/* nested child text */</span>\n"
            "    {/* real JSX comment */}\n"
            "  </p>\n"
            "); // real trailing comment\n"
        )
        self.assertEqual(
            ["/* real JSX comment */", "// real trailing comment"],
            comments(source, tsx=True),
        )

    def test_tsx_unicode_element_child_text_is_not_a_comment(self):
        source = (
            "const view = <É>// visible child text</É>;\n"
            "// real trailing comment\n"
        )
        self.assertEqual(["// real trailing comment"], comments(source, tsx=True))

    def test_comment_spans_do_not_let_division_hide_a_later_comment(self):
        source = "const ratio = {} / 2; // real comment\n"
        for tsx in (False, True):
            with self.subTest(tsx=tsx):
                self.assertEqual(["// real comment"], comments(source, tsx=tsx))

    def test_tsx_generic_component_type_arguments_keep_trailing_comment(self):
        source = "const view = <Foo<Item> value={item} />; // real comment\n"
        self.assertEqual(["// real comment"], comments(source, tsx=True))

    def test_tsx_unterminated_element_returns_a_named_error(self):
        _, errors = ts.comment_spans("const view = <p>", tsx=True)
        self.assertEqual(1, len(errors))
        self.assertIn("unterminated JSX element", errors[0][1])

    def test_comment_scanner_accepts_depth_64_and_refuses_depth_65(self):
        accepted = "const value = " + "{" * 64 + "0" + "}" * 64 + ";\n"
        refused = "const value = " + "{" * 65 + "0" + "}" * 65 + ";\n"
        self.assertEqual([], ts.comment_spans(accepted)[1])
        _, errors = ts.comment_spans(refused)
        self.assertEqual([(78, "nesting exceeds supported depth")], errors)

    def test_template_comment_scan_does_not_repeatedly_call_complete_lexer(self):
        source = "const value = `" + "".join("${item}" for _ in range(80)) + "`;\n"
        with mock.patch.object(ts, "lex", wraps=ts.lex) as complete_lex:
            _, errors = ts.comment_spans(source)
        self.assertEqual([], errors)
        self.assertLessEqual(complete_lex.call_count, 1)

    def test_tsx_candidates_do_not_search_the_remaining_suffix_repeatedly(self):
        source = "const value = " + " + ".join("<Name>" for _ in range(80)) + ";\n"
        with mock.patch.object(ts.re, "search", wraps=ts.re.search) as tail_search:
            ts.comment_spans(source, tsx=True)
        self.assertLessEqual(tail_search.call_count, 1)

    def test_many_valid_jsx_elements_do_not_copy_remaining_suffixes(self):
        source = SliceCountingSource(
            "const views = ["
            + ", ".join("<A>child text</A>" for _ in range(80))
            + "]; // real comment\n"
        )
        spans, errors = ts.comment_spans(source, tsx=True)
        self.assertEqual([], errors)
        self.assertEqual(0, source.suffix_slice_count)
        self.assertEqual(
            ["// real comment"],
            [str.__getitem__(source, slice(start, end)) for _, start, end in spans],
        )

    def test_many_valid_self_closing_elements_are_a_clean_linear_scan(self):
        source = SliceCountingSource(
            "const views = ["
            + ", ".join("<Name />" for _ in range(256))
            + "];\n"
        )
        spans, errors = ts.comment_spans(source, tsx=True)
        self.assertEqual([], errors)
        self.assertEqual([], spans)
        self.assertEqual(0, source.suffix_slice_count)


if __name__ == "__main__":
    unittest.main()
