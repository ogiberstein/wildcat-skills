## Step 1, round 1 -- 2026-08-25

Review basis: full diff `0f835d5..c0594e5`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`, `plugins/hexaemeron/lib/typescript_lexer.py` | The `.ts` and `.tsx` adapter consumed only outer `lex()` spans. A complete template is one `template` span, so genuine line and block comments inside `${...}` were discarded and the prose gate could return clean on source comments. | fixed in this round: shared `comment_spans()` opens substitutions, including nested templates, and assertion guards cover both suffixes |
| S1-R1-02 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`, `plugins/hexaemeron/lib/typescript_lexer.py` | The JavaScript lexical view did not model JSX. `//` and `/* */` in raw child text became false findings, while a closing-tag slash could begin a regex span and hide a genuine following comment; nested and self-closing elements crossed the same boundary. | fixed in this round: the shared comment consumer traverses JSX markup, child text, and code expressions while preserving the existing `lex()` contract; direct shared-library and Imprimatur guards cover each case |

Mechanical gates: Phylax 0; Ephoros 0; Hypomnema 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

Leads not pursued: full parser-level validity for TypeScript and Solidity. The declared boundary is comment extraction with named lexical refusal, not executable semantics.
