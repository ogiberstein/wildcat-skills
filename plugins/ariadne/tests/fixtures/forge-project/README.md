# The Foundry fixture project

Two versions of one contract, with their build output committed. The tests read
this output rather than running `forge`, so nothing in the suite needs a
Solidity toolchain.

Generated locally with `forge 1.7.1` and `solc 0.8.28`, then normalised in one
respect: solc's `basePath`, `allowPaths` and `includePaths` record the absolute
directory the build ran in, so those three strings were rewritten to
`/workspace/v1` and `/workspace/v2`. Nothing else was touched, and no field
capture reads was changed. The `cache/` directories were removed for the same
reason.

`v2` differs from `v1` deliberately, so that the delta between them is real:

- `sweep(address)` is added, which gives an ABI entry and a new selector.
- `deadline` is inserted between `owner` and `balance`, which moves `balance`
  from slot 1 to slot 2.
- The constructor takes an argument, which changes the creation bytecode.

The contract is test material. It is not written to be deployed and nothing in
this repository deploys it.

## Rebuilding

```bash
cd v1 && forge build && cd ../v2 && forge build
```

Then remove the `cache/` directories and rewrite the three absolute paths in
`out/build-info/*.json`, or the fixture will carry whichever machine rebuilt it.
