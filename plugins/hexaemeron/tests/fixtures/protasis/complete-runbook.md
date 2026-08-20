# Runbook: a complete fixture

Two steps, both carrying every required field.

## Step 1: Scaffold the thing

**Goal.** Put the layout in place.
**Entry.** The run branch at its first commit.
**Exit.** The layout exists and the suite runs.

```bash
python3 -m unittest discover -s tests
```

**Files.** `src/thing.py`.
**Tests.** `tests/test_thing.py`, one case.
**Disciplines.** phylax: none, no new input. hypomnema: the layout is a
placement decision recorded in the README.

## Step 2: Demonstrate the thing

**Goal.** Run the demo path.
**Entry.** Step 1's exit state.
**Exit.** The demo exits 0, proved by `python3 -m thing --demo`.
**Files.** `README.md`.
**Tests.** No new tests.
**Disciplines.** ephoros: none, nothing runs unattended.
