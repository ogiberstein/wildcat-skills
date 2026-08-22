# ADR-012: Run Fiat in a dedicated worktree, created at init

## Status

Accepted, 2026-08-22. Recorded for [skills#439](https://github.com/wildcat-finance/skills/issues/439).

## Context

A Fiat run took over the checkout it was started in. The contract had the model
cut the run branch with `git checkout -b`, and every step branch the same way,
so `HEAD` moved under whoever was standing in that directory, repeatedly, for
the length of the run.

Two costs are recorded in the issue. A clone sitting on an unrelated branch had
a run fast-forward that branch to `origin/main`, commit onto it, and report the
commit as being on `main`; the push then failed non-fast-forward, because local
`main` was a stale ref the run had never touched. The commit was right and the
report was wrong. Separately, two agents worked one repository in the same
period, and only an accident of one being in a worktree kept them from fighting
over `HEAD` and the index.

Preflight refused to start against a dirty tree, which is correct in itself and
meant an operator holding uncommitted work could not start a run at all.

Fiat already knew the answer and only said so after the collision. The word
`worktree` appeared in the controller exactly once, inside the refusal printed
when the kernel lock was already held, advising `git worktree add ../<name>
main`. That advice is also wrong in the ordinary case: git will not check out a
branch that is already checked out elsewhere, so borrowing the base fails
whenever the operator is standing on it.

## Decision

`hexctl init` creates the run's worktree before any preflight work touches a
branch, and the run lives there for its whole length.

- **Where it lives.** `tmp/fiat/<run branch with separators flattened>`, under
  the worktree root git reports. One run maps to one directory, and an
  issue-backed branch keeps its leading number.
- **The home ignores itself.** `init` writes a `.gitignore` holding `*` into
  `tmp/fiat/`, the same trick the state directory has always used. Without it
  the home shows as untracked in the origin checkout, which breaks the promise
  that a run leaves that checkout's `git status` alone and blocks the next run,
  because preflight refuses a dirty tree. Doing it here rather than leaning on
  the target repository's own ignore rules means the promise holds whichever
  repository the run was started in.
- **The run branch is created in the new tree.** `git worktree add -b <run
  branch> <path> <base>` cuts it there rather than borrowing the base, which is
  what makes the ordinary case work.
- **State moves with it.** `.hexaemeron/` is written inside the worktree, so
  `--dir` points at the worktree for the rest of the run. `init` prints the
  exact command to use next.
- **The origin checkout keeps a breadcrumb.** One line at
  `.hexaemeron/worktree` naming the run's tree, so a resume can find it without
  being told.
- **Fail closed.** A target that is not a Git repository, a derived path that is
  occupied or escapes the repository, a run branch already checked out
  somewhere, or a failing `git worktree add`, each refuse by name before any
  state, ledger or breadcrumb is written. This is a breaking change for anyone
  who relied on an in-place run, and it is stated as one rather than hidden
  behind a flag nobody sets.

## What the origin checkout actually keeps

Three files, all inside `.hexaemeron/` and all invisible to git: the
self-ignoring `.gitignore` the controller has always written, the kernel lock
taken before any mutating command runs, and the breadcrumb. The breadcrumb is
the only one the run itself adds. The study's phrasing, that write access is
narrowed to one breadcrumb line, describes the run's own writing and not the
lock that precedes it.

## Alternatives

- **Contract text only.** Tell the model in `SKILL.md` to create a worktree
  first. Cheapest, and rejected because it is the same shape as the defect: the
  advice already there is contract text, and it is both unenforced and wrong in
  the common case. A rule with no mechanism leaves no trace when it is skipped.
- **A separate `hexctl worktree` command before `init`.** Composable, and it
  keeps `init` free of filesystem work. Rejected because a run can simply not
  call it, which is the previous option with more surface, and because
  responsibility for isolating a run would sit in two commands either of which
  can run without the other.
- **An opt-in `--worktree` flag.** Smallest blast radius and no breaking
  change. Rejected because the default stays broken, and every incident in the
  issue happened on the default path.
- **A sibling directory outside the repository.** Offered and declined. Keeping
  the tree inside the repository also keeps state writes on one filesystem,
  which the existing atomic replace depends on.

## Consequences

`init` now mutates the filesystem beyond its own state directory and owns a
failure path it did not have before. Every one of those effects is refusable
before any state exists, which is the compensation.

The kernel lock stays exactly as it is. Separate worktrees mean separate state
directories, which makes collision rarer without removing the need for the
guard when two writers share one directory.

Runs started before this change keep working: an existing `.hexaemeron/` in a
checkout still resumes, and the archived-run fixtures still verify.

Every test fixture that runs `init` is now a real repository, because a run that
creates a worktree needs one to create it in.
