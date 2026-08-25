"""Guard Imprimatur's offset-preserving source-prose boundary."""

from pathlib import Path
import inspect
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PLUGIN_ROOT / "skills" / "imprimatur" / "scripts"
SCRIPT = SCRIPT_DIR / "imprimatur.py"
sys.path.insert(0, str(SCRIPT_DIR))

import imprimatur as imprimatur_module  # noqa: E402


build = imprimatur_module.build
SourceExtractionError = getattr(imprimatur_module, "SourceExtractionError", ValueError)
extract_source_prose = getattr(imprimatur_module, "extract_source_prose", None)
SOURCE_MODE = (
    extract_source_prose is not None
    and "source_suffix" in inspect.signature(build).parameters
)


def term_hits(source: str, suffix: str, term: str = "leverage") -> list[dict]:
    if not SOURCE_MODE:
        raise AssertionError("Imprimatur has no source-prose mode")
    return [
        hit
        for hit in build(source, source_suffix=suffix)["hits"]
        if hit["term"] == term
    ]


class SourceExtractionTests(unittest.TestCase):
    def test_indented_solidity_natspec_keeps_source_coordinates(self):
        source = (
            "contract Example {\n"
            "    /// @notice Leverage the underlying primitive.\n"
            "}\n"
        )
        hits = term_hits(source, ".sol")
        self.assertEqual([(2, 17)], [(hit["line"], hit["col"]) for hit in hits])

    def test_solidity_block_comments_are_prose_but_strings_are_not(self):
        source = (
            'contract Example { string constant X = "/* Leverage only data */";\n'
            "    /** Leverage the checked primitive. */\n"
            "}\n"
        )
        hits = term_hits(source, ".sol")
        self.assertEqual([2], [hit["line"] for hit in hits])

    def test_solidity_code_does_not_license_a_gated_comment_term(self):
        self.assertTrue(SOURCE_MODE, "Imprimatur has no source-prose mode")
        source = "NamedIdentifier value; // Orthogonal to the framing.\n"
        hits = [
            hit
            for hit in build(source, source_suffix=".sol")["hits"]
            if hit["term"] == "orthogonal"
        ]
        self.assertEqual([(1, 27)], [(hit["line"], hit["col"]) for hit in hits])

    def test_python_comments_and_owned_docstrings_are_prose(self):
        source = (
            '"""Leverage the module primitive."""\n'
            'ordinary = "Leverage is only data"\n'
            '"Leverage is a later expression, not a docstring"\n'
            "class Example:\n"
            '    """Leverage the class primitive."""\n'
            "    async def run(self):\n"
            '        """Leverage the function primitive."""\n'
            "        # Leverage the comment primitive.\n"
            "        return ordinary\n"
        )
        hits = term_hits(source, ".py")
        self.assertEqual([1, 5, 7, 8], [hit["line"] for hit in hits])

    def test_typescript_literals_urls_templates_and_regexes_are_not_comments(self):
        source = (
            'const url = "https://example.test/Leverage";\n'
            "const template = `// Leverage only data`;\n"
            r"const pattern = /https?:\/\/Leverage/;" "\n"
            "// Leverage the helper.\n"
        )
        hits = term_hits(source, ".ts")
        self.assertEqual([4], [hit["line"] for hit in hits])

    def test_tsx_jsdoc_is_prose_but_jsx_strings_are_not(self):
        source = (
            'const view = <p title="// Leverage only data">text</p>;\n'
            "/** Leverage the rendered helper. */\n"
        )
        hits = term_hits(source, ".tsx")
        self.assertEqual([2], [hit["line"] for hit in hits])

    def test_each_mask_has_the_source_length_and_line_terminators(self):
        self.assertTrue(SOURCE_MODE, "Imprimatur has no source-prose mode")
        cases = {
            ".sol": "contract C {\n  // prose\n}\n",
            ".py": '"""prose\nline"""\nvalue = 1\n',
            ".ts": "const x = 1;\n/* prose\nline */\n",
            ".tsx": "const x = <p />;\n// prose\n",
        }
        for suffix, source in cases.items():
            with self.subTest(suffix=suffix):
                masked = extract_source_prose(source, suffix)
                self.assertEqual(len(source), len(masked))
                self.assertEqual(
                    [index for index, char in enumerate(source) if char in "\r\n"],
                    [index for index, char in enumerate(masked) if char in "\r\n"],
                )

    def test_malformed_supported_source_refuses_a_clean_result(self):
        self.assertTrue(SOURCE_MODE, "Imprimatur has no source-prose mode")
        cases = {
            ".sol": "contract C { /* never closes",
            ".py": "def broken(:\n    pass\n",
            ".ts": "const value = `never closes;",
            ".tsx": "const view = <p title=\"never closes;",
        }
        for suffix, source in cases.items():
            with self.subTest(suffix=suffix):
                with self.assertRaises(SourceExtractionError):
                    build(source, source_suffix=suffix)

    def test_markdown_and_include_code_keep_their_existing_meanings(self):
        self.assertTrue(SOURCE_MODE, "Imprimatur has no source-prose mode")
        markdown = "    Leverage hidden in indented Markdown.\n"
        self.assertEqual(0, build(markdown)["defects"])
        solidity = "contract C { function leverage() external {} }\n"
        self.assertEqual(
            0,
            build(solidity, source_suffix=".sol")["defects"],
        )
        self.assertGreater(
            build(solidity, source_suffix=".sol", skip_code=False)["defects"],
            0,
        )

    def test_cli_reports_each_path_and_original_coordinates(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            clean = root / "clean.py"
            finding = root / "finding.sol"
            clean.write_text("# The helper returns one value.\n", encoding="utf-8")
            finding.write_text(
                "contract Example {\n"
                "    /// @notice Leverage the underlying primitive.\n"
                "}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(clean),
                    str(finding),
                    "--max-defects",
                    "0",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn(f"=== {clean} ===", result.stdout)
        self.assertIn(f"=== {finding} ===", result.stdout)
        self.assertIn("2:17", result.stdout)

    def test_cli_returns_two_without_a_partial_clean_report_on_extraction_error(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            clean = root / "clean.sol"
            broken = root / "broken.ts"
            clean.write_text("// The helper returns one value.\n", encoding="utf-8")
            broken.write_text("const value = `never closes;", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(clean), str(broken)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn(f"imprimatur: {broken}:1:15:", result.stderr)
        self.assertIn("unterminated template literal", result.stderr)


if __name__ == "__main__":
    unittest.main()
