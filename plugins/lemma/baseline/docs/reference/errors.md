# Errors

Every revert in the registry is a custom error. There are no string reverts.

## DuplicateEntry

Raised by `create` when the identifier is already in use.

## AtCapacity

Raised by `create` when the total has reached the immutable capacity.

## NotAdmin

Raised by the `onlyAdmin` modifier, and also by `retire` when the caller is not
the entry owner. The reuse is a known wart and is documented in the
troubleshooting guide.
