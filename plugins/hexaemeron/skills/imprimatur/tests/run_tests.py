#!/usr/bin/env python3
"""Test suite for the imprimatur lexicon.

Three groups:

  true positives   text that must be flagged
  false positives  legitimate technical prose that must stay clean
  behaviour        gate mechanics, masking, hook contract, self-lint

The false-positive corpus is the one that matters. Adding a term that fires on
it means the term needs gating, not banning.
"""

from __future__ import annotations

import json
import inspect
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from imprimatur import (  # noqa: E402
    SourceExtractionError,
    build,
    extract_source_prose,
    read_text,
)

PASS, FAIL = "ok", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((PASS if condition else FAIL, name, detail))


def families(text: str, **kw) -> set[str]:
    return {h["family"] for h in build(text, **kw)["hits"]}


# --------------------------------------------------------------- true positives

TRUE_POSITIVES = [
    ("origin term", "The qualifier here is load-bearing.", "structural_metaphor"),
    ("drift: heavy lifting", "The modifier does the heavy lifting.", "structural_metaphor"),
    ("drift: crux", "That is the crux of the disagreement.", "structural_metaphor"),
    ("drift: operative word", "Note the operative word in clause 4.", "structural_metaphor"),
    ("claude tic", "That's a great question about the cap table.", "claude_tic"),
    ("version-of-this", "There's a version of this where the deed is signed first.", "claude_tic"),
    ("hedge pivot", "It's worth noting that the deadline moved.", "hedge_pivot"),
    ("closer", "At the end of the day, the borrower repays.", "closer"),
    ("brochure", "Let's delve into the ecosystem.", "brochure"),
    ("consultant", "We should leverage the existing rails.", "consultant"),
    ("invented confidence", "Everything should work now.", "invented_confidence"),
    ("empty hedge", "Generally speaking, it depends.", "empty_hedge"),
    ("cosplay", "The vibes are off on this one.", "register_cosplay"),
    ("negation correction", "This isn't just a protocol, it's a promise.", "negation_correction"),
    ("not because but", "Not because it failed, but because it never ran.", "not_x_but_y"),
    ("em dash", "The market cleared — eventually.", "em_dash"),
    ("apology theatre", "I apologise for the confusion in the last message.", "apology_theatre"),
    ("generic title case", "## Evidence Changes Everything", "title_case_heading"),
    ("gated no referent", "This approach is orthogonal to the framing.", "mathematical"),
    ("intensifier no number", "The rate is materially different this quarter.", "intensifier"),
]

for label, text, want in TRUE_POSITIVES:
    got = families(text)
    check(f"positive/{label}", want in got, f"want {want}, got {sorted(got) or 'nothing'}")


# -------------------------------------------------------------- false positives
# Legitimate prose from the domains this organisation writes in. Any hit here is
# a bug in the lexicon, not a defect in the text.

FALSE_POSITIVES = [
    (
        "solidity postmortem",
        "The denomination bug in `BorrowingBaseLib` treated the base as 18-decimal "
        "while the asset was USDC at 6. Blast radius was 4 markets on Ethereum "
        "mainnet, none with non-zero borrows.",
    ),
    (
        "maths with definition",
        "The two libraries are orthogonal in the sense that neither imports the other.",
    ),
    (
        "maths with identifier",
        "The withdrawal queue is orthogonal to `CrossMarketCapLib`, which never reads it.",
    ),
    (
        "quantified intensifier",
        "The rate is materially different: 4.2% against 11.8% last quarter.",
    ),
    (
        "security terms with referent",
        "The attack surface of `BorrowAgent.sol` is two external functions. "
        "The escape hatch at line 212 lets a borrower exit without the hook.",
    ),
    (
        "legal scope qualifier",
        "Broadly, the Borrower may not vary the terms; the exception in clause 7.3 "
        "permits variation on 30 days' notice.",
    ),
    (
        "honest status report",
        "Edited `verifyToken` at `auth.ts:42` to the new API. Tests not run. "
        "Next: `npm test -- auth.spec.ts`.",
    ),
    (
        "style guide citing bans",
        'The banned terms are "load-bearing", "at the end of the day", and "delve".',
    ),
    (
        "backticked citation",
        "Replace `leverage` with use, and `utilise` with use.",
    ),
    (
        "anaphora inherits evidence",
        "The `PeriodicTermHooks` contract sets the term length. It is orthogonal to "
        "the rate model.",
    ),
    (
        "sentence case heading",
        "## The three passes\n\nEach pass runs in order.",
    ),
    (
        "suite product headings",
        "# Wildcat Labs Skills\n\n## The Promise Machine\n",
    ),
    (
        "genuine enumeration",
        "Preserve scope, risk, and uncertainty in every rewrite.",
    ),
]

for label, text in FALSE_POSITIVES:
    r = build(text)
    check(
        f"clean/{label}",
        r["defects"] == 0,
        "; ".join(f"{h['family']}:{h['term']!r}" for h in r["hits"]),
    )


# ------------------------------------------------------------------- behaviour

def test_promise_machine_licensed_scope_qualifier_is_preserved() -> bool:
    text = (
        "Broadly, the Borrower may not vary the terms; clause 7.3 permits "
        "variation on 30 days' notice."
    )
    return build(text)["defects"] == 0 and text.startswith("Broadly,")


def test_promise_machine_missing_gate_evidence_is_refused() -> bool:
    return "mathematical" in families("This approach is orthogonal to the framing.")


def test_promise_machine_subject_mode_mismatch_is_refused() -> bool:
    text = 'He said "load-bearing" again.'
    return build(text)["defects"] == 0 and build(text, strict=True)["defects"] > 0


def test_promise_machine_clean_lint_does_not_establish_truth() -> bool:
    report = build("The Moon is made of cheese.")
    return report["defects"] == 0 and "factual_accuracy" not in report


def test_promise_machine_failure_recovers_without_erasing_the_term() -> bool:
    bad = "This approach is orthogonal to the framing."
    repaired = "The two libraries are orthogonal in the sense that neither imports the other."
    return (
        build(bad)["defects"] > 0
        and build(repaired)["defects"] == 0
        and "orthogonal" in repaired
    )


check(
    "promise-machine/licensed scope qualifier is preserved",
    test_promise_machine_licensed_scope_qualifier_is_preserved(),
)
check(
    "promise-machine/missing gate evidence is refused",
    test_promise_machine_missing_gate_evidence_is_refused(),
)
check(
    "promise-machine/subject mode mismatch is refused",
    test_promise_machine_subject_mode_mismatch_is_refused(),
)
check(
    "promise-machine/clean lint does not establish truth",
    test_promise_machine_clean_lint_does_not_establish_truth(),
)
check(
    "promise-machine/failure recovers without erasing the term",
    test_promise_machine_failure_recovers_without_erasing_the_term(),
)

# Evidence must not bleed across sentences.
bleed = "This approach is orthogonal to the framing. The `verifyToken` helper is fine."
check("gate/no cross-sentence bleed", "mathematical" in families(bleed))

# Definitional escape.
check("gate/definitional", "mathematical" not in families("It is orthogonal in that neither calls the other."))

# Numeral licenses.
check("gate/numeral", "mathematical" not in families("The 3 modules are orthogonal."))

# Mention vs use.
check("mask/mention exempt", build('He said "load-bearing" again.')["defects"] == 0)
check("mask/strict counts it", build('He said "load-bearing" again.', strict=True)["defects"] > 0)

# Fenced code is not prose.
check("mask/code fence", build("```\nload-bearing = True\n```")["defects"] == 0)

# Source files retain comments and Python docstrings at their original offsets.
solidity = "contract C {\n    /// @notice Leverage the underlying primitive.\n}\n"
solidity_report = build(solidity, source_suffix=".sol")
solidity_hit = next((h for h in solidity_report["hits"] if h["term"] == "leverage"), None)
check(
    "source/solidity indented NatSpec",
    solidity_hit is not None and (solidity_hit["line"], solidity_hit["col"]) == (2, 17),
    f"got {solidity_hit}",
)

python_source = (
    '"""Leverage the module primitive."""\n'
    'ordinary = "Leverage is only data"\n'
    'def run():\n'
    '    """Leverage the function primitive."""\n'
    '    # Leverage the comment primitive.\n'
    '    return ordinary\n'
)
python_report = build(python_source, source_suffix=".py")
check(
    "source/python comments and docstrings",
    [h["line"] for h in python_report["hits"] if h["term"] == "leverage"] == [1, 4, 5],
    str([(h["line"], h["col"]) for h in python_report["hits"]]),
)

for suffix, source, wanted_line in [
    (".ts", 'const text = "// Leverage only data";\n// Leverage the helper.\n', 2),
    (".tsx", 'const view = <p>{"/* Leverage only data */"}</p>;\n/** Leverage the view. */\n', 2),
]:
    report = build(source, source_suffix=suffix)
    hits = [h for h in report["hits"] if h["term"] == "leverage"]
    check(
        f"source/{suffix[1:]} comments exclude literals",
        len(hits) == 1 and hits[0]["line"] == wanted_line,
        str([(h["line"], h["col"]) for h in hits]),
    )

for suffix in (".ts", ".tsx"):
    source = "const ratio = {} / 2; // Leverage the real comment.\n"
    hits = [
        hit
        for hit in build(source, source_suffix=suffix)["hits"]
        if hit["term"] == "leverage"
    ]
    check(
        f"source/{suffix[1:]} division keeps later comment",
        [(hit["line"], hit["col"]) for hit in hits] == [(1, 26)],
        str([(hit["line"], hit["col"]) for hit in hits]),
    )

generic_jsx = (
    "const view = <Foo<Item> value={item} />; "
    "// Leverage the real comment.\n"
)
generic_hits = [
    hit
    for hit in build(generic_jsx, source_suffix=".tsx")["hits"]
    if hit["term"] == "leverage"
]
check(
    "source/tsx generic component keeps later comment",
    [(hit["line"], hit["col"]) for hit in generic_hits] == [(1, 45)],
    str([(hit["line"], hit["col"]) for hit in generic_hits]),
)

generic_arrow = (
    "const f = <T /* Leverage the type helper. */ = unknown,>"
    "(x: T) => x; // Leverage the trailing helper.\n"
)
try:
    generic_arrow_hits = [
        hit
        for hit in build(generic_arrow, source_suffix=".tsx")["hits"]
        if hit["term"] == "leverage"
    ]
except SourceExtractionError as exc:
    generic_arrow_hits = []
    generic_arrow_detail = str(exc)
else:
    generic_arrow_detail = str(
        [(hit["line"], hit["col"]) for hit in generic_arrow_hits]
    )
check(
    "source/tsx generic arrow comments",
    len(generic_arrow_hits) == 2,
    generic_arrow_detail,
)

slash_sources = [
    'const ratio = {} / "a/b".length;',
    'let x = 1; const ratio = x++ / "a/b".length;',
    'const ratio = function(): Value & {} {} / "a/b".length;',
    'const value = /Leverage//2;',
    "if (ok) /[/*]Leverage/.test(value);",
    "while (ok) /[//]Leverage/.test(value);",
]
slash_goal_ok = True
slash_goal_detail = []
for prefix in slash_sources:
    source = prefix + " // Leverage the real helper.\n"
    try:
        hits = [
            hit
            for hit in build(source, source_suffix=".tsx")["hits"]
            if hit["term"] == "leverage"
        ]
    except SourceExtractionError as exc:
        slash_goal_ok = False
        slash_goal_detail.append(str(exc))
        continue
    positions = [(hit["line"], hit["col"]) for hit in hits]
    expected = [(1, source.rindex("Leverage") + 1)]
    slash_goal_ok = slash_goal_ok and positions == expected
    slash_goal_detail.append(str(positions))
check(
    "source/tsx slash lexical goals",
    slash_goal_ok,
    "; ".join(slash_goal_detail),
)

alias_sources = [
    "type Alias = string",
    "type Alias = [string, number]",
    "type Alias = Foo<Bar>",
    "type Alias = { value: string }",
    "type Alias<T> = T extends string ? First : Second",
    "type Alias = (value: string) => number",
]
alias_goal_ok = True
alias_goal_detail = []
for alias in alias_sources:
    source = alias + "\n/[/*]Leverage/.test(value); // Leverage the helper.\n"
    try:
        hits = [
            hit
            for hit in build(source, source_suffix=".tsx")["hits"]
            if hit["term"] == "leverage"
        ]
    except SourceExtractionError as exc:
        alias_goal_ok = False
        alias_goal_detail.append(str(exc))
        continue
    positions = [(hit["line"], hit["col"]) for hit in hits]
    expected = [(2, source.rindex("Leverage") - source.index("\n"))]
    alias_goal_ok = alias_goal_ok and positions == expected
    alias_goal_detail.append(str(positions))
check(
    "source/tsx type alias restores regex goal",
    alias_goal_ok,
    "; ".join(alias_goal_detail),
)

declaration_sources = [
    "type Alias<T = string> = <U extends T = T>(value: U) => U",
    'import Foo = require("foo")',
    'import type { Foo } from "foo"',
    'export { Foo } from "foo"',
    'export * from "foo"',
    "export as namespace Library",
    "declare const value: Map<string, Array<number>>",
    "let value: Map<string, Array<number>>",
    "let first = 1, value: Map<string, Array<number>>",
    "class C<T extends string = string> { value!: T }",
    "interface I<T extends string = string> { value: T }",
    "function f<T extends string = string>(value: T): Promise<T | { value: T }>",
]
declaration_goal_ok = True
declaration_goal_detail = []
for suffix in (".ts", ".tsx"):
    for declaration in declaration_sources:
        source = declaration + "\n/[/*]Leverage/.test(value); // Leverage the helper.\n"
        try:
            hits = [
                hit
                for hit in build(source, source_suffix=suffix)["hits"]
                if hit["term"] == "leverage"
            ]
        except SourceExtractionError as exc:
            declaration_goal_ok = False
            declaration_goal_detail.append(f"{suffix}:{exc}")
            continue
        positions = [(hit["line"], hit["col"]) for hit in hits]
        expected = [(2, source.rindex("Leverage") - source.index("\n"))]
        declaration_goal_ok = declaration_goal_ok and positions == expected
        declaration_goal_detail.append(f"{suffix}:{positions}")
check(
    "source/typescript declaration boundaries restore regex goal",
    declaration_goal_ok,
    "; ".join(declaration_goal_detail),
)

false_comment_regex = (
    "declare const value: string\n"
    "/[/*] Leverage hidden [*/]/.test(value); "
    "// Leverage the helper.\n"
)
false_comment_hits = [
    hit
    for hit in build(false_comment_regex, source_suffix=".ts")["hits"]
    if hit["term"] == "leverage"
]
check(
    "source/typescript declaration regex stays code",
    [(hit["line"], hit["col"]) for hit in false_comment_hits]
    == [(2, false_comment_regex.rindex("Leverage") - false_comment_regex.index("\n"))],
    str([(hit["line"], hit["col"]) for hit in false_comment_hits]),
)

restricted_statement_sources = [
    (
        ".ts",
        "while (ok) { break\n/[/*]Leverage[*/]/.test(value); } "
        "// Leverage the actual helper.\n",
    ),
    (
        ".tsx",
        "outer: while (ok) { continue /* label trivia */ outer\n"
        "/[/*]Leverage[*/]/.test(value); } "
        "// Leverage the actual helper.\n",
    ),
    (
        ".ts",
        "while (ok) { debugger\n/[/*]Leverage[*/]/.test(value); } "
        "// Leverage the actual helper.\n",
    ),
    (
        ".tsx",
        "while (ok) { break\n<p>// Leverage is raw child text</p>; } "
        "// Leverage the actual helper.\n",
    ),
]
restricted_statement_ok = True
restricted_statement_detail = []
for suffix, source in restricted_statement_sources:
    try:
        hits = [
            hit
            for hit in build(source, source_suffix=suffix)["hits"]
            if hit["term"] == "leverage"
        ]
    except SourceExtractionError as exc:
        restricted_statement_ok = False
        restricted_statement_detail.append(f"{suffix}:{exc}")
        continue
    expected_offset = source.rindex("Leverage")
    expected = (
        source.count("\n", 0, expected_offset) + 1,
        expected_offset - source.rfind("\n", 0, expected_offset),
    )
    positions = [(hit["line"], hit["col"]) for hit in hits]
    restricted_statement_ok = restricted_statement_ok and positions == [expected]
    restricted_statement_detail.append(f"{suffix}:{positions}")
check(
    "source/typescript restricted statements restore expression goal",
    restricted_statement_ok,
    "; ".join(restricted_statement_detail),
)

declaration_sequences = [
    (
        "declare const item: Map<string, Array<number>>\n"
        "type Alias = string\n"
        "function read<T>(value: T): T\n"
    ),
    (
        "declare const item: Map<string, Array<number>>\n"
        "class Example {}\n"
    ),
    (
        "function read<T>(value: T): Map<string, Array<number>>\n"
        "type Alias = string\n"
    ),
]
declaration_sequence_ok = True
declaration_sequence_detail = []
for suffix in (".ts", ".tsx"):
    for prefix in declaration_sequences:
        source = (
            prefix
            + "/[/*]Leverage[*/]/.test(value); "
            "// Leverage the actual helper.\n"
        )
        try:
            hits = [
                hit
                for hit in build(source, source_suffix=suffix)["hits"]
                if hit["term"] == "leverage"
            ]
        except SourceExtractionError as exc:
            declaration_sequence_ok = False
            declaration_sequence_detail.append(f"{suffix}:{exc}")
            continue
        expected_offset = source.rindex("Leverage")
        expected = (
            source.count("\n", 0, expected_offset) + 1,
            expected_offset - source.rfind("\n", 0, expected_offset),
        )
        positions = [(hit["line"], hit["col"]) for hit in hits]
        declaration_sequence_ok = declaration_sequence_ok and positions == [expected]
        declaration_sequence_detail.append(f"{suffix}:{positions}")
check(
    "source/typescript declaration state survives sequences",
    declaration_sequence_ok,
    "; ".join(declaration_sequence_detail),
)

bodyless_function_sequence = (
    "declare function f(): void\n"
    "/[a]/.test(value);\n"
    'const ratio = {} / "a/b".length; // Leverage the helper.\n'
)
bodyless_function_hits = [
    hit
    for hit in build(bodyless_function_sequence, source_suffix=".ts")["hits"]
    if hit["term"] == "leverage"
]
check(
    "source/typescript bodyless declaration state does not leak",
    [(hit["line"], hit["col"]) for hit in bodyless_function_hits] == [(3, 37)],
    str([(hit["line"], hit["col"]) for hit in bodyless_function_hits]),
)

class_member_source = (
    "class Outer {\n"
    "  class = C\n"
    "  ratio = {} / /* Leverage the field helper. */ 2\n"
    "}\n"
)
class_member_hits = [
    hit
    for hit in build(class_member_source, source_suffix=".ts")["hits"]
    if hit["term"] == "leverage"
]
check(
    "source/typescript class member names do not leak declaration state",
    [(hit["line"], hit["col"]) for hit in class_member_hits] == [(3, 19)],
    str([(hit["line"], hit["col"]) for hit in class_member_hits]),
)

contextual_word_source = (
    "interface = value\n"
    "const ratio = {} / /* Leverage the expression helper. */ 2\n"
)
contextual_word_hits = [
    hit
    for hit in build(contextual_word_source, source_suffix=".ts")["hits"]
    if hit["term"] == "leverage"
]
check(
    "source/typescript contextual declaration word does not leak state",
    [(hit["line"], hit["col"]) for hit in contextual_word_hits] == [(2, 23)],
    str([(hit["line"], hit["col"]) for hit in contextual_word_hits]),
)

dynamic_import_source = (
    'import("pkg")\n'
    "/ /* Leverage the division helper. */ 2; // ordinary trailing\n"
)
dynamic_import_hits = [
    hit
    for hit in build(dynamic_import_source, source_suffix=".ts")["hits"]
    if hit["term"] == "leverage"
]
check(
    "source/typescript dynamic import keeps expression division state",
    [(hit["line"], hit["col"]) for hit in dynamic_import_hits] == [(2, 6)],
    str([(hit["line"], hit["col"]) for hit in dynamic_import_hits]),
)

touching_regex_comment = "const value = /Leverage/// Leverage the helper.\n"
touching_hits = [
    hit
    for hit in build(touching_regex_comment, source_suffix=".tsx")["hits"]
    if hit["term"] == "leverage"
]
check(
    "source/tsx regex close touches line comment",
    [(hit["line"], hit["col"]) for hit in touching_hits] == [(1, 28)],
    str([(hit["line"], hit["col"]) for hit in touching_hits]),
)

line_terminators_ok = True
line_terminators_detail = []
for terminator in ("\r\n", "\r", "\u2028", "\u2029"):
    source = (
        "// clean"
        + terminator
        + "const Leverage = 1;"
        + terminator
        + "// Leverage the real helper."
    )
    positions = [
        (hit["line"], hit["col"])
        for hit in build(source, source_suffix=".ts")["hits"]
        if hit["term"] == "leverage"
    ]
    line_terminators_ok = line_terminators_ok and positions == [(3, 4)]
    line_terminators_detail.append(f"{ascii(terminator)}={positions}")
check(
    "source/typescript line terminators",
    line_terminators_ok,
    "; ".join(line_terminators_detail),
)

solidity_line_breaks_ok = True
solidity_line_breaks_detail = []
for terminator in ("\r", "\v", "\f"):
    source = "// clean" + terminator + "/// Leverage the real helper."
    positions = [
        (hit["line"], hit["col"])
        for hit in build(source, source_suffix=".sol")["hits"]
        if hit["term"] == "leverage"
    ]
    solidity_line_breaks_ok = solidity_line_breaks_ok and positions == [(2, 5)]
    solidity_line_breaks_detail.append(f"{ascii(terminator)}={positions}")
check(
    "source/solidity line breaks",
    solidity_line_breaks_ok,
    "; ".join(solidity_line_breaks_detail),
)

solidity_invalid_breaks_ok = True
solidity_invalid_breaks_detail = []
for terminator in ("\x85", "\u2028", "\u2029"):
    source = "// clean" + terminator + "/// Leverage the real helper."
    try:
        build(source, source_suffix=".sol")
    except SourceExtractionError as exc:
        refused = "unsupported Solidity source line break" in str(exc)
        solidity_invalid_breaks_detail.append(str(exc))
    else:
        refused = False
        solidity_invalid_breaks_detail.append("accepted")
    solidity_invalid_breaks_ok = solidity_invalid_breaks_ok and refused
check(
    "source/solidity invalid line breaks refuse",
    solidity_invalid_breaks_ok,
    "; ".join(solidity_invalid_breaks_detail),
)

python_cr = (
    '# "quoted\r'
    '# text"\r'
    "def café():\r"
    '    """Leverage the Unicode-named helper."""\r'
    "    return 1\r"
)
python_cr_hits = [
    hit
    for hit in build(python_cr, source_suffix=".py")["hits"]
    if hit["term"] == "leverage"
]
check(
    "source/python CR Unicode docstring coordinates",
    [(hit["line"], hit["col"]) for hit in python_cr_hits] == [(4, 8)],
    str([(hit["line"], hit["col"]) for hit in python_cr_hits]),
)

with tempfile.TemporaryDirectory() as raw:
    terminator_path = Path(raw) / "terminators.ts"
    markdown_path = Path(raw) / "ordinary.md"
    terminator_payload = b"// first\r\n// second\r// third\n"
    markdown_payload = b"first\r\nsecond\rthird\n"
    terminator_path.write_bytes(terminator_payload)
    markdown_path.write_bytes(markdown_payload)
    read_options = (
        {"preserve_newlines": True}
        if "preserve_newlines" in inspect.signature(read_text).parameters
        else {}
    )
    preserved_terminators = read_text(str(terminator_path), **read_options)
    include_code_newlines = read_text(str(terminator_path))
    markdown_newlines = read_text(str(markdown_path))
check(
    "source/CLI path preserves CRLF and CR",
    preserved_terminators == terminator_payload.decode("utf-8"),
    repr(preserved_terminators),
)
check(
    "source/CLI Markdown keeps universal newline behavior",
    markdown_newlines == "first\nsecond\nthird\n",
    repr(markdown_newlines),
)
check(
    "source/CLI include-code keeps universal newline behavior",
    include_code_newlines == "// first\n// second\n// third\n",
    repr(include_code_newlines),
)

masked = extract_source_prose(solidity, ".sol")
check(
    "source/mask preserves offsets",
    len(masked) == len(solidity)
    and [i for i, c in enumerate(masked) if c == "\n"]
    == [i for i, c in enumerate(solidity) if c == "\n"],
)

for suffix, source in [
    (".sol", "contract C { /* never closes"),
    (".py", "def broken(:\n    pass\n"),
    (".ts", "const value = `never closes;"),
]:
    try:
        build(source, source_suffix=suffix)
    except SourceExtractionError:
        refused = True
    else:
        refused = False
    check(f"source/{suffix[1:]} malformed refuses clean", refused)

for depth, expected_refusal in [(64, False), (65, True)]:
    nested = "const value = " + "{" * depth + "0" + "}" * depth + ";\n"
    try:
        extract_source_prose(nested, ".ts")
    except SourceExtractionError:
        refused = True
    else:
        refused = False
    check(
        f"source/typescript depth {depth}",
        refused == expected_refusal,
        f"refused={refused}",
    )

check(
    "source/markdown masking unchanged",
    build("    Leverage hidden in indented Markdown.\n")["defects"] == 0,
)

# Signal-only patterns do not score.
sig = build("Preserve scope, risk, and uncertainty.")
check("signal/triad not a defect", sig["defects"] == 0 and len(sig["signals"]) > 0)

# Severity ordering.
crit = build("Everything should work now.")["hits"][0]["severity"]
check("severity/invented confidence critical", crit == "critical", f"got {crit}")

# Clean text scores 100.
check("score/clean is 100", build("The market repaid 4.2m USDC on 3 March.")["score"] == 100.0)

# Hook contract.
def hook(payload: dict, stage: str) -> int:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "hook_gate.py"), "--stage", stage],
        input=json.dumps(payload), capture_output=True, text=True,
    ).returncode

check("hook/blocks banned prose",
      hook({"tool_input": {"file_path": "a.md", "content": "The caveat is load-bearing."}}, "pre-write") == 2)
check("hook/ignores source files",
      hook({"tool_input": {"file_path": "a.sol", "content": "// load-bearing"}}, "pre-write") == 0)
check("hook/honours escape hatch",
      hook({"tool_input": {"file_path": "a.md",
                           "content": "<!-- imprimatur:off -->load-bearing<!-- imprimatur:on -->"}}, "pre-write") == 0)
check("hook/honours ignore-file",
      hook({"tool_input": {"file_path": "a.md",
                           "content": "<!-- imprimatur:ignore-file -->\nload-bearing"}}, "pre-write") == 0)
check("hook/gates agent replies",
      hook({"last_assistant_message": "At the end of the day, everything should work now."}, "stop") == 2)
check("hook/survives malformed payload",
      subprocess.run([sys.executable, str(ROOT / "scripts" / "hook_gate.py")],
                     input="not json", capture_output=True, text=True).returncode == 0)

# Self-lint: every shipped document must pass its own rules.
for doc in ["SKILL.md", "NOTICE.md", "README.md",
            "references/lexicon-rationale.md", "references/agent-replies.md",
            "references/rewriting.md"]:
    p = ROOT / doc
    if not p.exists():
        continue
    r = build(p.read_text(encoding="utf-8"))
    check(f"selflint/{doc}", r["defects"] == 0,
          "; ".join(f"{h['line']}:{h['family']}:{h['term']!r}" for h in r["hits"][:5]))

# Lexicon integrity.
for name in ["hard.json", "gated.json", "structural.json"]:
    try:
        json.loads((ROOT / "lexicon" / name).read_text())
        check(f"lexicon/{name} parses", True)
    except Exception as exc:
        check(f"lexicon/{name} parses", False, str(exc))

hard = json.loads((ROOT / "lexicon" / "hard.json").read_text())
all_terms = [t for k, v in hard.items() if not k.startswith("_") for t in v.get("terms", [])]
check("lexicon/no duplicate hard terms",
      len(all_terms) == len(set(all_terms)),
      f"{len(all_terms) - len(set(all_terms))} duplicates")


# ---------------------------------------------------------------------- report

failed = [r for r in results if r[0] == FAIL]
width = max(len(n) for _, n, _ in results) + 2
for status, name, detail in results:
    if status == FAIL:
        print(f"{status:<5} {name:<{width}} {detail}")
print()
print(f"{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
