---
name: horos
description: Emit and verify an evidence-backed reading boundary over a repository. Classify token sinks (generated files, vendored trees, lockfiles, minified bundles, single-line blobs), write the deterministic boundary agents consult before reading, and print Python skeleton maps for oriented reading. Use when a user names Horos or asks to cut the reading cost of a repository without rewriting its code. Never apply a boundary during security review.
metadata:
  version: "1.1.0"
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

**Current frontier.** Text assets and machine-emitted migration SQL evidenced in the wildcat-app-v2 bundle stay readable, and TypeScript skeleton maps are refused rather than built.

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
python3 scripts/horos.py map <file.py>
```

prints the file's skeleton (signatures, class structure, first docstring
lines) so a large Python file can be oriented in without being read whole.
It parses; it never imports or executes what it reads.

`map` reads Python only, by decision rather than omission. TypeScript
skeletons were considered and refused on 2026-08-18: stdlib Python cannot
parse TypeScript honestly, a regex sketch of a language is a guess this
marketplace refuses, and no parser dependency or subprocess boundary is
justified by a secondary verb. The refusal is on the ledger in
[EVOLUTION.md](EVOLUTION.md). The measured win on TypeScript repositories
comes from `scan`, which classified 80.3% of the live wildcat-app-v2 tree;
the recorded capture lives at
[../../docs/evidence/wildcat-app-v2.md](../../docs/evidence/wildcat-app-v2.md).

## The discipline

1. Entering a repository, look for `.horos/boundary.json`. If it exists, run
   `check` before trusting it; a stale or forged boundary fails by name. If
   it does not exist and the repository is large, offer a scan.
2. Treat every path inside a checked boundary as unread-by-default. The entry
   itself carries what a reader needs: category, size, evidence.
3. Before opening a Python file over a few hundred lines, run `map` and read
   the skeleton first. Open the file whole only when the skeleton was not
   enough.
4. Classification is fail-open, so the boundary understates the sinks. What
   it lists is evidenced; what it omits is merely unproven.

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
