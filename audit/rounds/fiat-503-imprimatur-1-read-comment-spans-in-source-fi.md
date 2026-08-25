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

## Step 1, round 4 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-4 fixes starting from signed round-3 commit `3303a92514f886cfb56a12be9f3aa12c7fcce1ea`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | TypeScript 5.9.2 accepted declarations for which the comment scanner carried the division goal across ASI. Generic defaults ended type-alias state, while static imports, re-exports, ambient or uninitialised declarations, and bodyless functions did not end at their declaration boundary. Valid source could return a named refusal or retain regex bytes as comment prose. | fixed in this round: bounded type, module, variable, and body-declaration state restores the declaration-following regex goal; direct and Imprimatur guards cover plain `.ts` and `.tsx`, nested signatures, sequential statements, division controls, and declaration-following regexes |
| S1-R4-02 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | Declaration candidates leaked into expression contexts. Contextual identifiers and ASI-separated class member names could hide a later real division comment, and dynamic `import()` was mistaken for a static import whose completion allowed a following division slash to consume a real block-comment opener. | fixed in this round: member and object contexts cannot start declarations, contextual assignments clear pending declarations, and `import(` cancels static-import state; parser-confirmed expression and semicolon controls guard both supported suffixes |
| S1-R4-03 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | `Path.read_text()` translated CRLF and lone CR before default source extraction. A real source path therefore reached the same-length mask with changed length and terminators, contrary to the documented source view and Promise evidence. | fixed in this round: default supported-source paths opt into untranslated newline reads; Markdown and `--include-code` keep universal-newline behavior; actual-file and dispatch guards cover all three paths |

### Negative review

TypeScript 5.9.2 returned empty `parseDiagnostics` for 58/58 primary audit specimens and 35/35 independent transition specimens. The valid forms covered aliases with nested defaults, static imports and re-exports, ambient and multi-declarator variables, bodyless and implemented generic functions, generic classes and return types, comments and newlines inside signatures, declaration and expression closures, labels, case/default and control heads, optional chaining, postfix and non-null division, adjacent regex division/comments, sequential statements, templates, TSX fragments, generic arrows, spreads, attributes, and CR/LF/LS/PS boundaries. Invalid division controls remained refusals instead of widening the regex goal. The comment traversal remained forward and bounded, and extraction errors still discard every accumulated prefix before CLI output.

Python 3.12.3 probes covered Unicode before token and AST columns, CR/CRLF input, true concatenated docstrings, later standalone string expressions, PEP 701 f-string comments, and the shared linear string-token cursor. Solidity 0.8.30 comparison covered LF, VT, FF, CR, NEL, LS, and PS outside literals, in line and block comments, and in strings, plus multi-file no-partial-output behavior. The compiler's VT/FF validity result was not elevated because the Promise explicitly says successful extraction does not establish source validity; the documented retained VT/FF mask and named NEL/LS/PS refusal remained unchanged. Markdown masking, `--include-code`, the complete-span `lex()` API, recursion and angle-depth boundaries, coordinates, and frontier/version invariants remained green.

### Mechanical gates

Mechanical gates: focused shared-lexer and source-extraction suites 69/69; focused Imprimatur 93/93; pinned Node v26.6.0 full Hexaemeron 1126/1126; evolution and version propagation 16/16; Promise Machine copies 14/14; root suite 350/350; root inoculation 1,258 cases, 0 crashes, 0 unexpected clean; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and protected-source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Full parser-level validity for TypeScript and Solidity remains outside the declared comment-extraction boundary. TypeScript 5.9.2 and Solidity 0.8.30 were audit oracles, not repository dependencies. The bounded repair does not attempt a full parser.

## Step 1, round 5 -- 2026-08-25

Review basis: full fixed Step 1 diff `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841..0d20abe905ecc3906237609367236d47e5491fb5`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R5-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | TypeScript 5.9.2 accepted `break`, `continue`, their labelled forms, and `debugger` when ASI ended them at CR, LF, LS, PS, or a comment-held line break. The scanner retained its division goal, so a following regular-expression body containing `/*...*/` became comment prose. | fixed in this round: explicit restricted-statement state restores the regular-expression goal only after the language-owned line break; member, property, expression-division, and comment controls guard state reset |
| S1-R5-02 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | The same restricted-statement state prevented TSX element recognition after ASI. Raw JSX child `//` or `/*...*/` text then became source-comment prose. | fixed in this round: the completed restricted statement also admits the TSX element path; raw-child and JSX-expression controls guard the transition |
| S1-R5-03 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | A generic-typed uninitialised variable or bodyless function ending in `>` finished before a following type alias, class, or bodyless function in accepted sequences. The old state cleared, but the `>` still made the next `class` or `function` look like an expression and prevented the next declaration boundary from restoring the regular-expression goal. Valid ordered declarations could expose `/*...*/` bytes from a later regular expression as prose. | fixed in this round: a local completed-declaration marker wins only when tracked declaration state ended; 324 ordered declaration pairs and a binary `>` plus class-expression division control guard both sides |

### Negative review

TypeScript 5.9.2 returned empty `parseDiagnostics` for 17/17 new restricted-statement, declaration-sequence, TSX, Unicode-terminator, and binary-expression controls. All 324/324 parser-valid ordered declaration pairs produced only their genuine trailing comment. Ten nearby statement, member, property, division, block, declaration, and TSX controls matched their expected comments. A 30,079-byte accumulated-state specimen yielded 201 comments and 0 errors after 200 declaration/expression clusters and one 64-region tail.

Python probes retained true concatenated module and function docstrings, PEP 701 f-string comments, Unicode coordinates, CR and CRLF comments, and rejected later string expressions. Solidity probes kept NatSpec and ordinary comments, excluded ordinary, Unicode, and hex string contents, preserved the documented LF, VT, FF, and CR coordinates, and refused NEL, LS, and PS outside a comment or string. Multi-file failure still emitted no partial standard output. Markdown, `--include-code`, same-length masks, original coordinates, recursion refusal, the complete-span `lex()` API, and Imprimatur frontier and version invariants stayed unchanged.

### Mechanical gates

Mechanical gates: focused shared-lexer and source-extraction suites 73/73; focused Imprimatur 95/95; pinned Node v26.6.0 full Hexaemeron 1130/1130; evolution and version propagation 16/16; Promise Machine copies 14/14; root suite 350/350; root inoculation 1,258 cases, 0 crashes, 0 unexpected clean; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and protected-source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Full parser-level TypeScript and Solidity validity remains outside the declared comment-extraction contract. TypeScript 5.9.2 was an audit oracle and is not a repository dependency. No full parser was added.
