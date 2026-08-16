# Retiring entries

Retirement is available to the owner of an entry and to nobody else, including
the admin.

## Effect

Retiring sets the status to `Retired` and emits `EntryRetired`. It does not
free the identifier, does not reduce the total, and does not refund the creation
fee.

## Why the total does not decrease

The total counts entries ever created rather than entries currently active,
because a decreasing total would make capacity a moving target and let a
deployment exceed its stated bound over time.
