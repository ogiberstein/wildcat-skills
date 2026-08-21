# Study: a complete fixture

Assuming, unless corrected: nothing.

## 1. Problem statement

Build a thing, proved by `pytest`.

## 2. Prior art

The last two merged pull requests were read; there were none to carry.
The audit records were read; there were none to read.

## 3. Constraints and non-goals

Python only.

## 4. Design options

One option, chosen for being the only one.

## 5. Risk register seed

```risk-register
short-line | only two fields
long-line | one | field | too many
Bad_Id | an id that is not kebab-case | flagged
twice-used | the first use is sound | flagged only on reuse
twice-used | the second use of one id | flagged
empty-boundary |  | a check with no boundary
empty-check | a boundary with no check |
```

## 6. Glossary seeds

Fixture: a small, deliberate example.

## 7. Sources

This repository.

## 8. Signals, and the questions behind them

None, and here is why: a terminal lint has no on-call question.

## 9. Boundaries, per capability

The argument list is the boundary; paths are read as given.

## 10. The budget, or its absence

None, and here is why: two file reads carry no budget.

## 11. The fail-closed posture

A failing check stops the step; the guard is a test.

## 12. Decisions and their homes

The one reversible-at-cost decision is recorded in the ledger.
