# Contract surface

## Registry

The concrete deployment. Inherits everything on `RegistryBase`.

### create

Creates an entry. Admin only. Reverts on a duplicate identifier or at capacity.

### retire

Retires an entry. Owner only.

### setFee

Sets the creation fee. Admin only. Takes effect from the next creation.

## RegistryBase

Abstract. Holds storage and access control, and is not deployed on its own.

### entry

Returns the stored entry for an identifier, or a zeroed entry if none exists.

### total

Returns the number of entries ever created.
