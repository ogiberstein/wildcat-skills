# Study: TypeScript boundary checks for Phylax

## Assumptions

Assuming, unless corrected:

1. The implementation starts at `b95f332379a9ed9fdacbbbd26fc194eb93ad757a` in the Wildcat Skills repository.
2. The checker remains a Python standard-library program. It reuses the proven lexer layer from Horos as attributed first-party source inside Hexaemeron; it does not install a JavaScript parser, invoke Node, or use packages from the repository being checked.
3. “Both suites” means `python3 plugins/hexaemeron/tests/run_tests.py` and `python3 -m unittest discover -s tests`, run from the Wildcat Skills root.
4. The validation copy of `wildcat-app-v2` is read-only at `.hexaemeron/validation/wildcat-app-v2`, pinned at `9b8b6d5d6db06428c5b539f267623277b65315cd`. The lint may read it but must not format, install, build, or edit it.
5. The prototype TypeScript surface is tracked `.ts` and `.tsx` source. JavaScript variants, source maps, generated bundles and declaration-only analysis are outside this frontier.
6. “Session token” is read narrowly: a persistence site must carry an explicit session/authentication marker such as `sessionToken`, `authToken`, `accessToken`, `jwt` or `bearer`. A generic domain `token` or `signature` is not enough. This keeps `apiTokensSlice` and `pendingSafeMessagesSlice` from becoming findings by name alone.
7. “Fetch against a host” means a fetch whose absolute host can be selected at runtime. A relative URL and a URL built from `window.location.origin` are same-origin neighbours. A fixed absolute literal is a closed one-host choice. A bare `fetch(url)` with no same-file construction evidence is not enough for this prototype to conclude that a caller supplied the host.
8. “A sanitiser after it” means ordering in the render pipeline: every recognised raw-HTML step must be followed by a recognised sanitising step before rendering. For `dangerouslySetInnerHTML`, the value itself must visibly be the result of a sanitiser call. This reading follows `rehype-sanitize`’s own security guidance and makes the condition mechanically checkable.

These readings favour findings that a person can understand from one source file. They give up inter-file taint analysis rather than turn names such as `token`, `url` and `style` into routine false positives.

## Problem statement

Phylax currently checks Python and requirements files only. Its four rules, `P001` through `P004`, cover shell use, string subprocess commands, unpinned Python requirements and credentials in Python source or output. The skill already states three application controls that the checker cannot enforce:

- raw HTML must be sanitised after the last unsafe transform;
- a session credential must not reach persisted browser storage; and
- a host selected outside the program must not reach `fetch` without an allowlist check.

Build a standard-library extension to `plugins/hexaemeron/skills/phylax/scripts/phylax.py` that recognises those three TypeScript cases without changing the existing Python findings, output formats, suppression contract or exit codes. The users are contributors running Phylax on a changed tree and reviewers who need a small, source-located finding they can verify without learning a second tool.

A working prototype has three new finding codes, one isolated failing specimen and at least one close safe neighbour for each code. It also produces no finding over the pinned `wildcat-app-v2` copy and leaves both repository suites green.

### Demo and success criteria

The demo path is the following command sequence from the Wildcat Skills root:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py .hexaemeron/validation/wildcat-app-v2
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
git -C .hexaemeron/validation/wildcat-app-v2 status --porcelain
```

It succeeds only when:

1. an unsafe raw-HTML fixture reports `P005`, while `[rehypeRaw, rehypeSanitize]` and Emotion style injection do not;
2. an explicit session/auth token written through browser storage or a persisted reducer reports `P006`, while ordinary UI storage, an API-token domain slice and a pending-signature slice do not;
3. a runtime-selected absolute host passed to `fetch` without a host membership check reports `P007`, while relative, same-origin, fixed-host and allowlist-guarded fetches do not;
4. the focused test reports all specimens passing;
5. the app lint exits zero and prints `clean` at validation head `9b8b6d5d6db06428c5b539f267623277b65315cd`;
6. both named suites exit zero; and
7. the final status command prints nothing, proving that validation did not alter the app copy.

## Prior art

### In this repository

- `plugins/hexaemeron/skills/phylax/scripts/phylax.py` is the compatibility boundary. `check(path)` dispatches by file type, `Finding` fixes the text and JSON shape, `suppressed` accepts a reason on the finding line or the line above, and `main` fixes exit codes 0, 1 and 2.
- `plugins/hexaemeron/tests/test_phylax_checker.py` establishes the fixture idiom. Each rule has a specimen it must flag and a close neighbour it must allow; `codes(source, name)` writes an isolated temporary file and calls the checker directly. `OverTheMarketplace` is the existing whole-tree no-finding guard.
- `plugins/hexaemeron/skills/phylax/SKILL.md` names the three application boundaries and the intended controls. In particular, it requires `rehype-sanitize` after `rehype-raw`, keeps session tokens out of persisted slices, and requires an allowlist for supplied hosts.
- `plugins/hexaemeron/skills/phylax/EVOLUTION.md` holds this exact frontier and its acceptance condition under revision `off-chain-boundary-controls`.
- Commit `a112860` (`add Phylax, the guard on the off-chain surface`) introduced the checker, its tests and the ledger together. There is no later checker history to preserve beyond the current file contract.
- `plugins/hexaemeron/tests/run_tests.py` discovers every `test_*.py` under the Hexaemeron tests directory and prints a pass count. The root suite covers portable entrypoints, prose and evolution contracts that may be affected by a completed frontier update.
- `plugins/horos/skills/horos/scripts/languages/typescript/typescript.py` already supplies the lexical foundation this job needs. Its `lex(source)` classifies the full input into ordered code, line-comment, block-comment, string, template and regex spans; preserves source offsets and newlines; handles nested template expressions; and returns explicit errors for unterminated constructs. Horos's recorded differential run held the outliner built on this lexer against 866 hand-written TypeScript files, matching 2,237 of 2,239 compiler-visible declarations with no unconfessed misses, extras or crashes.
- `plugins/horos/tests/test_ts_lexer.py` fixes the lexer boundary with coverage for strings, nested templates, both comment forms, regex-versus-division, malformed input and complete span coverage. Reusing this source is cheaper and better evidenced than designing another TypeScript lexer inside Phylax.

### In the Wildcat application

The pinned validation tree contains 872 tracked `.ts` and `.tsx` files. These files supply real safe neighbours that the fixture set must preserve:

- `src/components/Markdown/index.tsx` imports `rehype-raw` and `rehype-sanitize`, then orders `rehypePlugins={[rehypeRaw, rehypeSanitize]}`. This is the positive control for safe raw HTML.
- `src/components/ThemeRegistry/EmotionCache.tsx` uses `dangerouslySetInnerHTML` to insert Emotion-generated `style` and `styles`. A rule that flags every occurrence of the React property is too broad.
- `src/store/slices/apiTokensSlice/apiTokensSlice.ts` and `src/store/slices/pendingSafeMessagesSlice/pendingSafeMessagesSlice.ts` use `persistReducer`; `lenderMlaSignaturesSlice` also persists signatures. These show why `token` and `signature` substrings alone cannot establish that a stored value is a session credential.
- `src/utils/timestamp.ts` and several UI components write names, timestamps and acknowledgement flags to browser storage. These are storage neighbours, not credentials.
- `src/hooks/useGetMarket.ts` builds a URL from `window.location.origin`; most application fetches use relative `/api/...` paths. `src/lib/protocol-stats/subgraph.ts` accepts a `url` parameter whose call sites use fixed exported Goldsky constants. A one-file prototype should not invent an external host where it cannot see one.

### Outside both repositories

- The Microsoft TypeScript Compiler API exposes each file as a `SourceFile` AST through `createSourceFile` and is the normal high-fidelity base for TypeScript linting. It is useful prior art, but adding or locating a Node dependency would break the standard-library and target-independence constraints.
- `rehype-sanitize` says to place sanitation after the last unsafe transform because anything after it can make the tree unsafe again. This supplies the ordering rule for `P005`.
- `redux-persist` documents `blacklist`, `whitelist`, nested persists and transforms. Those are the recognised ways to keep a sensitive field out of persisted state and supply the safe side of `P006`.
- The browser URL model distinguishes same-origin relative references from absolute URLs with a separately selectable host. The prototype uses that syntactic distinction rather than attempting DNS or network policy checks.

## Constraints and non-goals

### Constraints

- Preserve the current command line, text/JSON result shape, `Finding` fields, exit codes and Python rules `P000` through `P004`.
- Use only the Python standard library and do not execute the TypeScript being inspected.
- Preserve Horos provenance on any absorbed lexer code. Keep the shared copy inside Hexaemeron so the Hexaemeron plugin remains independently installable; a runtime import from a separately installed Horos plugin is not a supported dependency boundary.
- Keep findings source-located. The scanner must preserve line numbers while skipping comments and recognising strings, template substitutions and balanced brackets.
- Apply reason-bearing suppression to TypeScript with `// phylax: allow <reason>` on the finding line or the line above. A bare pragma must not suppress. Existing `#` suppression stays valid for Python.
- Read `.ts` and `.tsx`; do not turn on `.js`, `.jsx`, `.mjs`, generated Storybook output or source maps in this frontier.
- Fail with `P000` for unreadable input or an unterminated lexical construct needed by a rule. The scanner is not a TypeScript type checker and must not reject otherwise valid syntax merely because it does not understand a construct.
- Read at most 1 MiB from each TypeScript file and fail closed with `P000` when the file is larger. This bounds memory use and the lexer’s linear work on untrusted source.
- Keep the app validation tree at head `9b8b6d5d6db06428c5b539f267623277b65315cd` and make no write there.
- Keep each rule’s unsafe specimen beside safe neighbours in `plugins/hexaemeron/tests/test_phylax_checker.py` so a future widening has an immediate false-positive cost.

### Non-goals

- Full TypeScript parsing, module resolution, type checking or cross-file taint tracking.
- Proving that arbitrary HTML is safe, that a token is harmless, or that a DNS name resolves only to public addresses.
- Inferring that every value called `token`, `signature`, `url`, `data`, `content`, `style` or `html` is hostile.
- Recognising custom state persistence frameworks, IndexedDB wrappers, service-worker caches, Axios, GraphQL clients or non-`fetch` HTTP libraries.
- Rewriting unsafe code, adding application suppressions, editing `wildcat-app-v2`, installing its packages, or running its build.
- Expanding the checker to JavaScript or changing the four established Python rules.
- Changing the next frontier until implementation, audit, tests and evidence establish this one as complete under `skills/VERSIONING.md`.

### Operational boundaries

**Always.** Run the focused fixture test, the lint against the pinned app, and both repository suites before a commit. Run the Imprimatur lint on any shipped prose changed by the delivery. Record a baseline before claiming a performance change.

**Ask first.** Add any dependency; inspect a different app revision; touch CI; widen the scanned suffixes or the meaning of a session token; add a recognised sanitizer or allowlist idiom that changes the trust boundary.

**Never.** Execute inspected TypeScript; write to the validation app; print credential values in a finding; edit generated or vendored output; delete a failing neighbour to make the fixture test pass; claim a validation command ran when it did not.

## Design options

### Option A: TypeScript Compiler API helper

Invoke a small Node helper from the Python command and use `ts.createSourceFile` to inspect a real TypeScript AST. This gives the best syntax coverage and makes JSX, imports and nested expressions explicit. The trade is a new runtime boundary: Phylax would depend on Node and a resolvable TypeScript package, execute a subprocess for source inspection, and either add a dependency or borrow one from the target. That conflicts with the standard-library assumption and makes the checker least portable where it is most needed.

### Option B: import Horos at runtime

Load `languages.typescript.typescript.lex` directly from the sibling Horos plugin and build the three Phylax recognisers over its spans. This has the smallest source delta and uses the mature implementation without a copy. The trade is packaging: Hexaemeron and Horos install independently, plugin cache paths and versions are host-owned, and Hexaemeron cannot make its lint contract conditional on another plugin being present. A checkout-relative import would pass here and fail for a standalone Hexaemeron installation.

### Option C: absorb Horos's lexer into a shared Hexaemeron utility (chosen)

Copy the proven Horos lexer layer, with provenance, into a small shared Hexaemeron module and use it from Phylax. Preserve its span and error contract rather than designing a new scanner. Build the three narrow Phylax recognisers over the code mask and balanced token ranges. The module sits outside Phylax's rule code so Ephoros's later held TypeScript job can reuse the same lexical boundary.

The trade is a first-party source copy that must be reconciled if Horos's lexer later changes. In return, Hexaemeron stays independently installable, the implementation inherits Horos's recorded lexer evidence, target source is never executed, and Phylax does not acquire a Node or cross-plugin runtime dependency. This is the lowest comprehension cost that meets the prototype, packaging and clean-tree criteria.

### Option D: regular expressions over raw source

Search for `rehypeRaw`, storage calls and `fetch` text with multiline regular expressions. This is the smallest patch. Its trade is that comments, strings, nested expressions, alias imports and array order quickly become indistinguishable from code. It would either miss the `rehype` ordering rule or flag examples and generated text, breaking the required neighbour coverage.

### Option E: a new general JavaScript parser

Write a broader ECMAScript/TypeScript parser in Python. It avoids Node at runtime but ignores the first-party lexer already held against real compiler output, creates a large parser maintenance burden inside a security lint and makes the three controls harder to review than their target code. It is disproportionate to this frontier.

## Chosen construction

Keep `check(path)` as the sole dispatcher and add `check_typescript(path, text)`. Start from Horos's `lex(source)` span contract in an attributed shared Hexaemeron utility: ordered full-source spans for code, comments, strings, templates and regex literals plus explicit lexer errors. Derive a newline-preserving code mask from those spans, then let Phylax's local recognisers add only the import, call, array, object and guard structure needed by `P005` through `P007`. Do not copy Horos's declaration outliner; Phylax needs its lexical boundary, not repository mapping. Do not attempt type inference.

The rule contract is:

| Code | Unsafe syntax concluded in one file | Required safe neighbours |
| --- | --- | --- |
| `P005` | A `rehype-raw` import binding occurs in a rendered `rehypePlugins` array with no later `rehype-sanitize` binding; or a `dangerouslySetInnerHTML.__html` expression bearing an explicit raw/html/markdown/content name is not a visible sanitiser call. | `[rehypeRaw, rehypeSanitize]`; aliases imported from the same package names; Emotion `style`/`styles`; raw-looking input passed through a recognised `sanitize(...)` call. |
| `P006` | `localStorage.setItem` or `sessionStorage.setItem` writes a key/value with an explicit `sessionToken`, `authToken`, `accessToken`, `jwt` or `bearer` marker; or a `persistReducer` persists a same-file state field with one of those markers and does not exclude it through `blacklist`/`whitelist` or a visible transform. | names, timestamps and booleans in storage; `apiTokensSlice`; persisted pending signatures; a sensitive field named in `blacklist` or absent from `whitelist`. |
| `P007` | The first argument to global `fetch` visibly constructs an absolute URL from a runtime host, such as an interpolated authority or `new URL(path, host)`, and the same function/block has no prior membership check of that host against a named allowlist. | `/api/...`, `./...`, `window.location.origin`, a fixed `https://...` literal, and an explicit `ALLOWED_HOSTS.has(host)`/`.includes(host)` guard before the fetch. |

Recognised imports should be tied to their package strings, not just local names. Thus `import raw from "rehype-raw"` and `import clean from "rehype-sanitize"` work, while unrelated functions called `rehypeRaw` or `sanitize` do not silently earn trust. Direct sanitiser calls should likewise come from a short declared set established by imports in the fixture. Any widening of that set requires a hostile specimen and a neighbour.

`P007` should recognise an allowlist only when the checked hostname and the hostname reaching `fetch` are the same token binding and the check dominates the fetch within the same lexical block. A variable named `allowed` is not evidence. The prototype does not follow values into or out of helper functions; that limitation is preferable to treating every `fetch(url)` as an SSRF finding.

All three rules use the established `Finding` and suppression path. Messages describe the missing control without echoing the full expression, for example `P006 session credential written to persisted client storage`. JSON output requires no new schema.

## Risk register seed

| Area | Boundary or failure | Control in the build | Evidence the audit loop should demand |
| --- | --- | --- | --- |
| Untrusted input | Arbitrary TypeScript text can contain misleading comments, strings, templates, regex literals and malformed nesting. | Reuse Horos's fail-open lexer contract without executing source; preserve lines; cap work to a linear scan; emit `P000` when a construct required for analysis is unterminated. | Port the relevant Horos lexer fixtures, add Phylax rule neighbours, and compare representative span output to Horos in this checkout. |
| Trust boundary | Import aliases can make an unsafe plugin look unrelated or make an unrelated `sanitize` call look trusted. | Resolve only bindings imported from recognised package identifiers. | Alias-positive and name-collision-negative fixtures. |
| Raw HTML | A sanitiser before `rehypeRaw` gives a false sense of safety; arbitrary plugins after sanitation may reintroduce unsafe nodes. | Compare order and require sanitation after the recognised raw step. Do not claim safety for unknown post-sanitise transforms. | Reversed-order fixture, safe-order fixture and explicit documentation of the unknown-plugin limit. |
| Session custody | Broad word matching can disclose or misclassify token/signature domain state; narrow matching can miss an aliased JWT. | Report only location and identifier class, never value; require explicit session/auth markers at the persistence site; leave cross-file semantics to review. | Direct browser-storage and persisted-reducer fixtures plus `apiTokensSlice` and pending-signature neighbours. |
| External call | A runtime host can target an internal or metadata service; a name can change after a preflight resolution. | Require syntactic membership in a named host allowlist before a visible dynamic absolute fetch. Do no DNS or network call in the lint. | Unsafe dynamic-host and guarded-host fixtures; relative and same-origin neighbours. Runtime DNS pinning remains outside the mechanical claim. |
| Filesystem | Recursive lint could inspect generated output, enormous bundles or a changing validation checkout. | Restrict TypeScript checking to `.ts`/`.tsx`; pin and record validation HEAD; keep the app read-only. | File-type tests, app HEAD check and empty `git status --porcelain` after the demo. |
| Arithmetic | Token offsets, nesting depth and line numbers can drift around CRLF, multiline comments and templates. | Derive lines while scanning and preserve newline bytes in skipped regions; use a stack for delimiters. | Exact line assertions for multiline specimens and nested templates. |
| Partial run | A killed scan could leave users unsure whether “clean” was complete. | The checker writes no state and prints `clean` only after walking all requested paths; process interruption yields no success receipt. | Interrupt review and unchanged validation status; no output artefact treated as a receipt. |
| External processes | A parser helper could execute target-controlled package hooks or source. | Chosen design uses no subprocess and no target dependency. | Audit the imports and command path; focused test can patch subprocess APIs to ensure none are used if needed. |
| Secret material | Source under inspection may contain an actual secret. | Findings contain path, line, code and a fixed message only; never include the matched string value. | JSON/text fixture asserting no sample secret appears in output. |
| Compatibility | A TypeScript change could disturb `P001` through `P004`, suppressions, JSON or exit codes; an absorbed lexer could drift from Horos. | Dispatch by suffix and reuse `Finding`/filtering; retain all current tests; record Horos provenance and pin representative differential fixtures. | Existing Phylax suite, explicit mixed Python/TypeScript invocation test, and span-equivalence checks against the source Horos lexer in the marketplace checkout. |

There is no arithmetic over funds, blockchain external call, upgradeable storage or signer key custody in this change. “Custody” here is limited to source that may contain credentials and the rule that output must not repeat them.

## Glossary seeds

| Term | Meaning |
| --- | --- |
| allowlist | A finite set of permitted hostnames checked before a runtime-selected absolute URL reaches `fetch`. |
| browser persistence | Client-readable storage that outlives the immediate Redux value, including Web Storage and `redux-persist` for this prototype. |
| dominating guard | An allowlist membership check in the same lexical block that occurs before the fetch it controls. |
| dynamic host | The authority of an absolute URL is supplied through a variable or template substitution rather than fixed in source. |
| raw-HTML step | A renderer or transform that turns untrusted HTML text into nodes the browser may render, such as `rehype-raw`. |
| safe neighbour | Syntax close to an unsafe specimen that must remain unreported, fixing the rule's false-positive boundary. |
| sanitiser ordering | The requirement that a sanitising transform follows the last recognised unsafe transform in the render pipeline. |
| session marker | An explicit identifier showing authentication-session semantics: session/auth token, access token, JWT or bearer credential. |
| source-local conclusion | A finding justified by one file without following imports, callers or runtime values across modules. |
| TypeScript surface | `.ts` and `.tsx` source inspected by the new mechanical rules in this frontier. |

## Sources

- Wildcat Skills starting ref: `b95f332379a9ed9fdacbbbd26fc194eb93ad757a`.
- Phylax checker: `plugins/hexaemeron/skills/phylax/scripts/phylax.py` at the starting ref.
- Phylax fixtures: `plugins/hexaemeron/tests/test_phylax_checker.py` at the starting ref.
- Phylax policy and held frontier: `plugins/hexaemeron/skills/phylax/SKILL.md` and `plugins/hexaemeron/skills/phylax/EVOLUTION.md`.
- Phylax introduction: Git commit `a112860`.
- Horos TypeScript lexer: `plugins/horos/skills/horos/scripts/languages/typescript/typescript.py` at `b95f332379a9ed9fdacbbbd26fc194eb93ad757a`.
- Horos lexer fixtures and live differential record: `plugins/horos/tests/test_ts_lexer.py` and `plugins/horos/docs/evidence/wildcat-app-v2-outline.md` at that ref.
- Version contract: `plugins/hexaemeron/skills/VERSIONING.md`.
- Wildcat app validation ref: `.hexaemeron/validation/wildcat-app-v2` at `9b8b6d5d6db06428c5b539f267623277b65315cd`.
- Safe markdown pipeline: `wildcat-app-v2/src/components/Markdown/index.tsx` at that validation ref.
- Persistence neighbours: `wildcat-app-v2/src/store/slices/apiTokensSlice/apiTokensSlice.ts`, `pendingSafeMessagesSlice/pendingSafeMessagesSlice.ts` and `lenderMlaSignaturesSlice/mlaSignaturesSlice.ts` at that validation ref.
- Fetch neighbours: `wildcat-app-v2/src/hooks/useGetMarket.ts` and `src/lib/protocol-stats/subgraph.ts` at that validation ref.
- Microsoft, “Using the Compiler API”: <https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API> (`SourceFile`, `createSourceFile`, `Program`).
- `rehype-sanitize` security guidance: <https://github.com/rehypejs/rehype-sanitize#security> (“after the last unsafe thing”).
- `redux-persist` README: <https://github.com/rt2zz/redux-persist#blacklist--whitelist> and <https://github.com/rt2zz/redux-persist#transforms>.
- WHATWG URL Standard, URL parsing and relative resolution: <https://url.spec.whatwg.org/>.
