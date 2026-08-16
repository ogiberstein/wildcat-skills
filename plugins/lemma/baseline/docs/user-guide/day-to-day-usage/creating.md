# Creating entries

Creation is admin-only. The admin supplies an identifier and an amount, and the
call returns the fee charged.

## Before you start

Check that the identifier is unused and that the deployment is below capacity.
Both conditions revert rather than returning a status, so a failed simulation is
the cheapest way to find out.

## What the fee depends on

The fee is a proportion of the amount, rounded up. Changing the fee affects
subsequent creations only; entries already created are unaffected, because the
charged amount is computed once and not stored.
