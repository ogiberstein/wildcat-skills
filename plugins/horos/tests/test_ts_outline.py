"""The TypeScript outliner slices declarations verbatim and confesses the rest."""

from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

from languages.typescript import typescript as ts  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN / "examples" / "fixture-ts" / "market.ts"

EXPECTED = """module: A fixture market module for the Horos TypeScript outliner.
import { WildcatSDK } from "@wildcatfi/wildcat-sdk"
import type { Address } from "./types"
export const DEFAULT_TIMEOUT = 30_000
export type MarketFilter = {
export interface MarketSnapshot
export enum MarketState
export const fetchSnapshot = async (
function formatApr(bips: number): string
@sealed
export class MarketWatcher
    private readonly seen
    constructor(private readonly sdk: WildcatSDK)
    async refresh(filter: MarketFilter): Promise<MarketSnapshot[]>
    private track(snapshot: MarketSnapshot): MarketSnapshot
    get count(): number
export namespace MarketMath
    export function toRay(value: bigint): bigint
export default MarketWatcher
declarations: 17
unparsed: 1 region(s): lines 63-65
"""


def run(source):
    out = io.StringIO()
    code = ts.outline("test.ts", source, out)
    return code, out.getvalue()


class OutlineTests(unittest.TestCase):
    def test_the_fixture_outline_is_pinned(self):
        source = FIXTURE.read_text(encoding="utf-8")
        out = io.StringIO()
        code = ts.outline(str(FIXTURE), source, out)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), EXPECTED)

    def test_bodies_never_leak_into_the_outline(self):
        source = FIXTURE.read_text(encoding="utf-8")
        _, output = run(source)
        self.assertNotIn("this.seen.set", output)
        self.assertNotIn("10n ** 27n", output)

    def test_a_function_head_spanning_lines_is_sliced_whole(self):
        code, output = run(
            "export function join(\n  a: string,\n  b: string\n): string {\n  return a + b;\n}\n"
        )
        self.assertEqual(code, 0)
        self.assertIn("export function join(\n  a: string,\n  b: string\n): string", output)

    def test_an_interface_head_keeps_its_extends_clause(self):
        _, output = run("interface A extends B<C> {\n  x: number;\n}\n")
        self.assertIn("interface A extends B<C>", output)

    def test_a_class_keyword_inside_a_template_is_not_a_declaration(self):
        # The const's verbatim line may quote the template text; the hazard
        # is structural: no class declaration, no body, exactly one entry.
        _, output = run("const t = `class Fake {`;\nexport const after = 2;\n")
        lines = output.splitlines()
        self.assertFalse(any(line.startswith("class") for line in lines))
        self.assertIn("const t = `class Fake {`", lines)
        self.assertIn("export const after = 2", lines)
        self.assertIn("declarations: 2", output)
        self.assertIn("unparsed: none", output)

    def test_module_level_statements_are_confessed_by_line(self):
        code, output = run("const a = 1;\nif (a) {\n  console.log(a);\n}\n")
        self.assertEqual(code, 0)
        self.assertIn("unparsed: 1 region(s): lines 2-4", output)

    def test_a_clean_file_reports_no_regions(self):
        _, output = run("export const a = 1;\n")
        self.assertIn("unparsed: none", output)
        self.assertIn("declarations: 1", output)

    def test_a_lexer_error_confesses_the_remainder_and_exits_one(self):
        code, output = run("export const a = 1;\nconst s = 'open\nmore();\n")
        self.assertEqual(code, 1)
        self.assertIn("lexer: unterminated string at line 2", output)
        self.assertIn("unparsed:", output)
        self.assertNotIn("unparsed: none", output)

    def test_a_file_without_a_header_comment_says_so(self):
        _, output = run("export const a = 1;\n")
        self.assertIn("module: (no header comment)", output)

    def test_the_tsx_suffix_dispatches_too(self):
        import horos  # noqa: E402  (registry dispatch under test)

        out = io.StringIO()
        path = str(PLUGIN / "examples" / "fixture-ts" / "market.ts")
        self.assertEqual(horos.map_file(path, out=out), 0)
        self.assertIn(".tsx", __import__("languages").supported())


if __name__ == "__main__":
    unittest.main()
