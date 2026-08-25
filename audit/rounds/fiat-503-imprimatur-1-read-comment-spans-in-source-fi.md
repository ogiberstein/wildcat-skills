## Step 1, round 1 -- 2026-08-25

Review basis: full diff `0f835d5..c0594e5`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`, `plugins/hexaemeron/lib/typescript_lexer.py` | The `.ts` and `.tsx` adapter consumed only outer `lex()` spans. A complete template is one `template` span, so genuine line and block comments inside `${...}` were discarded and the prose gate could return clean on source comments. | fixed in this round: shared `comment_spans()` opens substitutions, including nested templates, and assertion guards cover both suffixes |
| S1-R1-02 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`, `plugins/hexaemeron/lib/typescript_lexer.py` | The JavaScript lexical view did not model JSX. `//` and `/* */` in raw child text became false findings, while a closing-tag slash could begin a regex span and hide a genuine following comment; nested and self-closing elements crossed the same boundary. | fixed in this round: the shared comment consumer traverses JSX markup, child text, and code expressions while preserving the existing `lex()` contract; direct shared-library and Imprimatur guards cover each case |

Mechanical gates: Phylax 0; Ephoros 0; Hypomnema 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

Leads not pursued: full parser-level validity for TypeScript and Solidity. The declared boundary is comment extraction with named lexical refusal, not executable semantics.

## Step 1, round 2 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-2 fixes starting from signed round-1 commit `eeb62230b83ab99c437ae1ebc414c351bc917786`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | Generic JSX type arguments prevented element recognition, and a slash after `}` could open a speculative regular expression whose close consumed the first slash of a later comment. Valid `.ts` and `.tsx` inputs could therefore discard genuine trailing comments and return clean. | fixed in this round: generic JSX angle groups are traversed, the comment consumer uses a comment-safe regular-expression close, and direct guards cover both suffixes |
| S1-R2-02 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | JSX classification depended on finding a future matching close. An unterminated opening tag or element was treated as code and could return clean instead of the promised named extraction failure. | fixed in this round: expression-position JSX prefixes enter the traversal directly, and missing or mismatched closes return named errors |
| S1-R2-03 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | The ASCII-only JSX name start rejected valid Unicode element names, so comment-shaped raw child text became a false finding. | fixed in this round: the JSX name boundary accepts Unicode word starts, and a Unicode child-text guard preserves only the real trailing comment |
| S1-R2-04 | medium | `plugins/hexaemeron/lib/typescript_lexer.py`, `plugins/hexaemeron/skills/imprimatur/SKILL.md` | Recursive code, template, and JSX traversal had no owned depth boundary. Deep supported input leaked `RecursionError` and a traceback instead of exit 2 with a named refusal. | fixed in this round: 64 recursively entered regions are accepted, the 65th is documented and refused by name, and a final recursion translation prevents interpreter leakage |
| S1-R2-05 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | Plain template substitutions repeatedly lexed the remaining tail, while JSX candidates searched or copied the remaining suffix. These paths were quadratic and contradicted the accepted bounded-forward-pass design for untrusted local source. | fixed in this round: one shared forward comment traversal advances by returned offsets; guards bound complete-lexer calls, tail searches, and suffix slices on repeated substitutions and valid JSX elements |
| S1-R2-06 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | Every Python docstring node scanned the complete token list, making a file with many docstrings quadratic in docstrings times tokens. | fixed in this round: source-ordered docstrings share one `string_cursor` over source-ordered tokens, with traced line-event growth guarded below quadratic |

Negative review: Solidity literal and comment boundaries, Python docstring ownership, same-length masks and coordinates, Markdown and `--include-code` behavior, the existing `lex()` consumer contract, and frontier/version invariants remained green under their named guards and gates.

Mechanical gates: Phylax 0; Ephoros 0; Hypomnema 0. Pinned Node v26.6.0 full Hexaemeron suite 1095/1095; focused Imprimatur suite 76/76; evolution and version propagation 16/16; Promise Machine copies 14/14; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

Leads not pursued: full parser-level validity for TypeScript and Solidity remains outside the declared comment-extraction boundary. Regular-expression lexical-goal ambiguity beyond the guarded comment-safe case is not elevated to parser semantics. Iterative type-argument depth remains uncapped because it is a forward non-recursive counter; the public 64-region refusal covers recursively entered code, template, and JSX regions.

## Step 1, round 3 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-3 fixes starting from signed round-2 commit `3613febd0435f612185ace8c3cddd04834400d52`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | The TSX generic-arrow probe accepted only a narrow comma or `extends` head. Valid defaulted or `const` type parameters and comment trivia inside or after the angle group entered JSX traversal and returned `unterminated JSX element`. | fixed in this round: the bounded probe traverses the complete angle group and recognizes trailing commas, defaults, constraints, modifiers, contextual names, and comment trivia before parameter-list entry |
| S1-R3-02 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | The comment scanner derived the slash lexical goal from one undifferentiated closing-brace token and refused valid division after object, function, class, postfix, assertion, and type-expression closures. It also read declaration-following regexes as division and could reclassify an adjacent regex close plus division or comment as comment prose. | fixed in this round: bounded brace, control-head, postfix, function/class signature, type-alias newline, and adjacent-regex state separates the parser-confirmed expression and statement contexts without changing the public `lex()` contract |
| S1-R3-03 | high | `plugins/hexaemeron/lib/typescript_lexer.py`, `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | LF-only comment, quote-mask, and coordinate handling absorbed code after valid source line breaks or erased those breaks. CR Python comments were omitted, TypeScript CR/LS/PS code became prose, and Solidity line-comment boundaries did not match its language rules. | fixed in this round: language-specific masks and coordinates preserve Python CR/LF and TypeScript CR/LF/LS/PS; Solidity accepts LF/VT/FF/CR and names parser-invalid NEL/LS/PS outside comments or strings as extraction refusals |
| S1-R3-04 | low | `plugins/hexaemeron/skills/imprimatur/SKILL.md` | Promise evidence said every supported suffix supplied successful source extraction even when `--include-code` intentionally bypassed extraction. | fixed in this round: evidence conditions source extraction on default masking, while the running instructions retain the whole-input meaning of `--include-code` |

### Negative review

Negative review: Solidity ordinary, hex, and Unicode string, NatSpec, and block-comment boundaries; Python docstring ownership and AST byte columns versus token code-point columns; TSX fragments, nesting, attributes, spreads, generic components, and regular-expression character classes; multi-file refusal without partial output; Markdown and `--include-code`; bounded traversal and suffix-copy behavior; exact masks and coordinates; the stable `lex()` API; and frontier/version invariants remained green.

### Mechanical gates

Mechanical gates: TypeScript 5.9.2 parsed 50/50 audit specimens; focused shared-lexer and source-extraction suites 55/55; focused Imprimatur 84/84; pinned Node v26.6.0 full Hexaemeron 1112/1112; evolution and version propagation 16/16; Promise Machine copies 14/14; root suite 350/350; root inoculation 1,258 cases, 0 crashes, 0 unexpected clean; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Leads not pursued: full parser-level validity for TypeScript and Solidity remains outside the declared comment-extraction boundary. The TypeScript compiler was an audit oracle for the 50 named valid forms, not a repository dependency. Solidity NEL, LS, and PS outside comments or strings and a 65th recursively entered TypeScript code, template, or JSX region use the documented named-refusal boundary rather than speculative parsing.
