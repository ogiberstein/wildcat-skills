# v2-protocol v2.1.0 code finding

Hermes inspected the source at `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`, the commit referenced by the `v2.1.0` release tag.

`BaseAccessControls.grantRoles` is external and only reads its two dynamic-array arguments. Both arguments are declared as `memory`, which copies ABI-decoded input before the function can use it. The candidate changes them to `calldata`:

```diff
-  function grantRoles(address[] memory accounts, uint32[] memory roleGrantedTimestamps) external {
+  function grantRoles(address[] calldata accounts, uint32[] calldata roleGrantedTimestamps) external {
```

This remains a code finding rather than an accepted optimisation. Hermes stopped at Gate 3 because the required `forge test --gas-report` command did not complete. The protocol repository was not changed or pushed.

See [`candidate.solidity.diff`](./candidate.solidity.diff) for the complete candidate.
