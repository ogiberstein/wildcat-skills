---
name: horos
description: Emit and verify an evidence-backed reading boundary over a repository. Classify token sinks (generated files, vendored trees, lockfiles, minified bundles, single-line blobs), write the deterministic boundary agents consult before reading, and print Python skeleton maps for oriented reading. Use when a user names Horos or asks to cut the reading cost of a repository without rewriting its code. Never apply a boundary during security review.
metadata:
  version: "3.2.0"
---

# Horos

From *horos*, the boundary stone. Horos decides what an agent does not read,
and proves the decision instead of asserting it.

## Where this sits

Horos owns the reading boundary: which files in a repository an agent leaves
unread by default, each exclusion carrying the evidence that earned it. Its
version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md).

**Use another tool when.** Use Lemma to chunk source for retrieval rather than
to skip it; use Brevitas for prose volume; use Metron for runtime cost. Horos
never rewrites code: the compression premise was measured and rejected in the
study this plugin ships at `docs/study.md`.

**Current frontier.** A repository's walk-worthiness and its missing extractors are still decided by guesswork; scan records no per-filetype breakdown.

## The verbs

All three live in one standard-library script,
[scripts/horos.py](./scripts/horos.py):

```bash
python3 scripts/horos.py scan <root> --write
```

walks the tree and commits `.horos/boundary.json`: every file it can
evidence as a token sink, with its category, size and the exact evidence
line that earned the entry. The write is atomic; a killed run leaves the old
boundary or the new one, never half. `--json` prints the same canonical
bytes instead of writing them.

```bash
python3 scripts/horos.py check <root>
```

re-derives the classification and compares it with the committed boundary.
Exit 0 means the boundary matches the tree. Drift names every path, in both
directions: a new sink the boundary lacks, and a committed entry the tree no
longer evidences.

```bash
python3 scripts/horos.py map <file>
```

prints the file's skeleton so it can be oriented in without being read
whole. Extractors live one folder per language under
[scripts/languages/](./scripts/languages/) and a suffix registry dispatches
between them; an unregistered suffix is refused naming the supported list.
Python (`.py`) parses through the standard library's own ast. TypeScript
(`.ts`, `.tsx`) is lexed, never parsed: declarations are quoted as verbatim
source slices, and every region the recognisers do not understand is
confessed by count and line range instead of guessed at. Neither path
imports or executes what it reads.

The TypeScript extractor exists by revision of a recorded refusal. Parsing
TypeScript or taking a parser dependency was refused on 2026-08-18 and
stays refused; the maintainer directed the design that needs neither, and
it was held against the real compiler before shipping: across all 866
hand-written TypeScript files of a live repository, 2,237 of 2,239
compiler-visible declarations matched, with zero misses outside the
outliner's own confessions, zero extras and zero crashes. The recorded run
lives at
[../../docs/evidence/wildcat-app-v2-outline.md](../../docs/evidence/wildcat-app-v2-outline.md).

## The discipline

1. Entering a repository, look for `.horos/boundary.json`. If it exists, run
   `check` before trusting it; a stale or forged boundary fails by name. If
   it does not exist and the repository is large, offer a scan.
2. Treat every path inside a checked boundary as unread-by-default. The entry
   itself carries what a reader needs: category, size, evidence.
3. Before opening a file over a few hundred lines in a language the
   registry supports, run `map` and read the skeleton first. Open the file
   whole only when the skeleton was not enough, and mind the confession
   line: a large unparsed region means the skeleton understates the file.
4. Classification is fail-open, so the boundary understates the sinks. What
   it lists is evidenced; what it omits is merely unproven.
5. When writing a boundary into a repository other agents will work in, add
   the adoption stanza that `scan --write` prints to that repository's
   AGENTS.md or CLAUDE.md. Agent harnesses load those files at session
   start, so the discipline travels with the repository; without the
   stanza, the boundary binds only agents carrying this skill.

## The one rule that outranks the rest

No reading boundary applies during security review. A committed boundary in a
hostile repository could list source files as sinks precisely so a reviewing
agent never opens them. During any audit, review or incident work, read as if
no boundary exists. `check` re-derives everything it asserts for the same
reason.

## The shipped example

[../../examples/fixture/](../../examples/fixture/) holds one file per rule
class and its committed boundary; [../../examples/README.md](../../examples/README.md)
shows the demo commands and the mutation that makes `check` fail.
