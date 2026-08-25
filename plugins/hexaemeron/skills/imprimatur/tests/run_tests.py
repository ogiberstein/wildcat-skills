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
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from imprimatur import SourceExtractionError, build, extract_source_prose  # noqa: E402

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
