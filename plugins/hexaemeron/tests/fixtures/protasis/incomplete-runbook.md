# Runbook: an incomplete fixture

Each step below omits exactly one required field, and the last states an exit
with no command anywhere in the step.

## Step 1: Missing goal

**Entry.** A clean tree.
**Exit.** Proved by `pytest`.
**Files.** `a.py`.
**Tests.** One case.
**Disciplines.** none, docs only.

## Step 2: Missing entry

**Goal.** Do the thing.
**Exit.** Proved by `pytest`.
**Files.** `b.py`.
**Tests.** One case.
**Disciplines.** none, docs only.

## Step 3: Missing exit

**Goal.** Do the thing.
**Entry.** A clean tree.
**Files.** `c.py`.
**Tests.** One case.
**Disciplines.** none, docs only.

## Step 4: Missing files

**Goal.** Do the thing.
**Entry.** A clean tree.
**Exit.** Proved by `pytest`.
**Tests.** One case.
**Disciplines.** none, docs only.

## Step 5: Missing tests

**Goal.** Do the thing.
**Entry.** A clean tree.
**Exit.** Proved by `pytest`.
**Files.** `e.py`.
**Disciplines.** none, docs only.

## Step 6: Missing disciplines

**Goal.** Do the thing.
**Entry.** A clean tree.
**Exit.** Proved by `pytest`.
**Files.** `f.py`.
**Tests.** One case.

## Step 7: Exit with no command

**Goal.** Do the thing.
**Entry.** A clean tree.
**Exit.** Reviewed and working.
**Files.** g.py
**Tests.** One case.
**Disciplines.** none, docs only.
