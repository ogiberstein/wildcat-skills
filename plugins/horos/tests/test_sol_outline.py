"""The Solidity outliner slices keyword-led declarations and confesses the rest."""

from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

from languages.solidity import solidity as sol  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN / "examples" / "fixture-sol" / "Market.sol"

EXPECTED = """module: SPDX-License-Identifier: MIT
pragma solidity ^0.8.20
import { IERC20 } from "./interfaces/IERC20.sol"
import "./libraries/MathUtils.sol"
type Duration is uint32
using MathUtils for uint256
error MarketClosed(address market)
struct LenderStatus
enum MarketState
uint256 constant BIP
interface IMarketEvents
    event Borrow(uint256 assetAmount)
    event DebtRepaid(address indexed from, uint256 assetAmount)
abstract contract MarketBase is IMarketEvents
    IERC20 public immutable asset
    uint256 public totalSupply
    mapping(address => LenderStatus) internal _lenders
    modifier onlyOpen()
    constructor(IERC20 _asset)
    function state() public view virtual returns (MarketState)
    receive() external payable
    function borrow(
    uint256 assetAmount
    ) external onlyOpen returns (uint256 normalized)
library MarketMath
    function rayDiv(uint256 x, uint256 y) internal pure returns (uint256)
contract Market is MarketBase
    constructor(IERC20 _asset) MarketBase(_asset)
    function state() public pure override returns (MarketState)
declarations: 26
unparsed: none
"""


def run(source):
    out = io.StringIO()
    code = sol.outline("Test.sol", source, out)
    return code, out.getvalue()


class SolOutlineTests(unittest.TestCase):
    def test_the_fixture_outline_is_pinned(self):
        source = FIXTURE.read_text(encoding="utf-8")
        out = io.StringIO()
        code = sol.outline(str(FIXTURE), source, out)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), EXPECTED)

    def test_bodies_never_leak_into_the_outline(self):
        source = FIXTURE.read_text(encoding="utf-8")
        _, output = run(source)
        self.assertNotIn("mstore", output)
        self.assertNotIn("totalSupply +=", output)
        self.assertNotIn("function fake()", output)

    def test_hex_and_unicode_strings_are_inert(self):
        code, output = run(
            'contract C {\n\tbytes constant B = hex"00ff";\n'
            '\tstring constant U = unicode"gm \\u2603";\n'
            "\tfunction f() external {}\n}\n"
        )
        self.assertEqual(code, 0)
        self.assertIn("    function f() external", output.splitlines())
        self.assertIn("unparsed: none", output)

    def test_a_contract_keyword_inside_a_string_is_not_a_declaration(self):
        _, output = run('string constant S = "contract Fake {";\ncontract Real {}\n')
        lines = output.splitlines()
        self.assertIn("contract Real", lines)
        self.assertFalse(any(line.startswith("contract Fake") for line in lines))

    def test_an_inheritance_list_rides_in_the_head(self):
        _, output = run("contract C is A, B(1) {\n\tuint256 x;\n}\n")
        self.assertIn("contract C is A, B(1)", output.splitlines())

    def test_a_multiline_head_with_override_list_slices_whole(self):
        code, output = run(
            "contract C is A {\n\tfunction f(\n\t\tuint256 x\n\t) public virtual"
            " override(A) returns (uint256) {\n\t\treturn x;\n\t}\n}\n"
        )
        self.assertEqual(code, 0)
        self.assertIn(") public virtual override(A) returns (uint256)", output)
        self.assertNotIn("return x", output)

    def test_state_variables_stop_before_initialisers(self):
        _, output = run("contract C {\n\tuint256 public fee = 500;\n}\n")
        self.assertIn("    uint256 public fee", output.splitlines())
        self.assertNotIn("500", output)

    def test_an_abstract_contract_walks_its_members(self):
        _, output = run("abstract contract A {\n\tfunction f() external virtual;\n}\n")
        lines = output.splitlines()
        self.assertIn("abstract contract A", lines)
        self.assertIn("    function f() external virtual", lines)

    def test_an_unmatched_statement_is_confessed_by_line(self):
        code, output = run("uint256 constant X = 1;\nif (true) { revert(); }\n")
        self.assertEqual(code, 0)
        self.assertIn("unparsed: 1 region(s): line 2", output)

    def test_an_unterminated_string_confesses_the_remainder(self):
        code, output = run('contract C {}\nstring constant S = "open\ncontract D {}\n')
        self.assertEqual(code, 1)
        self.assertIn("lexer: unterminated string at line 2", output)
        self.assertNotIn("unparsed: none", output)

    def test_a_bodyless_interface_function_slices_to_its_semicolon(self):
        _, output = run("interface I {\n\tfunction f() external returns (uint256);\n}\n")
        self.assertIn("    function f() external returns (uint256)", output.splitlines())

    def test_the_sol_suffix_dispatches_through_the_registry(self):
        import horos  # noqa: E402  (registry dispatch under test)

        out = io.StringIO()
        self.assertEqual(horos.map_file(str(FIXTURE), out=out), 0)
        self.assertIn(".sol", __import__("languages").supported())

    def test_module_header_falls_back_when_absent(self):
        _, output = run("pragma solidity ^0.8.0;\n")
        self.assertIn("module: (no header comment)", output)


if __name__ == "__main__":
    unittest.main()
