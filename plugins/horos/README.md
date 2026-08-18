# Horos

<!-- marketplace-context:start -->
## In one line

Horos classifies a repository's token sinks with evidence and emits the reading boundary agents respect.

**Try something else when.** Use Lemma to chunk source for retrieval, Brevitas for prose budgets, and Hexaemeron's Metron for runtime cost. Horos decides what goes unread; it never rewrites what is read.

**Current frontier.** Horos's map verb reads Python only; the maintainer-directed TypeScript outline extractor, internal to Horos with verbatim source slices and confessed unparsed regions, remains unbuilt.

**Next Fiat job.** Use /hexaemeron:fiat to Build the TypeScript outline extractor inside Horos's map verb: verbatim declaration slices, confessed unparsed regions, stdlib-only shipping, a dev-time differential corpus. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Why it exists

An agent working in a repository spends most of its reading budget on files
that return nothing: build output committed to the tree, vendored
dependencies, lockfiles, minified bundles, data blobs on a single line.
Measured against two Wildcat repositories, those files were 66% and 87% of
readable bytes. Rewriting code to save tokens was studied first and rejected;
the licensed saving was about 3% and published evidence prices aggressive
rewriting at up to 12 points of task completion. Not reading the sinks at all
is the mechanism that wins, and Horos makes it checkable. The full argument
is committed at [docs/study.md](./docs/study.md).

## What it ships

- a standard-library scanner that classifies token sinks and quotes the
  evidence line that earned each entry;
- a deterministic committed boundary at `.horos/boundary.json`, verified
  against the tree by `check`, which names every drifted path;
- Python skeleton maps, so a large file can be oriented in without being
  read;
- a shipped example at [examples/](./examples/) whose committed boundary a
  fresh scan reproduces byte for byte; and
- one binding rule: no boundary applies during security review.

The build trail is the runbook at [docs/runbook.md](./docs/runbook.md), one
reviewed step per verb.

## Day to day

**Developers.** An agent is pointed at a frontend repository where two thirds
of the readable bytes are a checked-in Storybook build, a lockfile and a data
file on one line. The committed boundary sends the reading budget to `src/`
instead, `check` catches the day the boundary goes stale, and a skeleton map
orients the agent in a thousand-line module without opening it whole.

## Adopting a boundary in any repository

The boundary binds agents that carry this skill; everyone else's agents
learn it from the adopting repository's own instructions file. `scan
--write` prints a short stanza for that repository's AGENTS.md or CLAUDE.md:
consult `.horos/boundary.json` before reading broadly, leave listed paths
unread unless the task demands one, and never apply the boundary during
security review. Harnesses load those files at session start, so one paste
makes the boundary effective for any instruction-following agent, with no
install.

## Where it is honest about limits

Classification is fail-open. A file Horos cannot evidence stays readable, so
Horos misses sinks a person would catch, and its report says what it skipped.
The scanner reads at most a fixed prefix of any file, so a scan never costs
more than a fraction of what it saves.
