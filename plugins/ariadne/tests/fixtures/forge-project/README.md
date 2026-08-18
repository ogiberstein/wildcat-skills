The Foundry fixture project

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.
<!-- marketplace-context:end -->

Two versions of one contract have committed build output. Tests read it instead
of running `forge`, so the suite needs no Solidity toolchain.

Generated with `forge 1.7.1` and `solc 0.8.28`. Solc records the build directory
in `basePath`, `allowPaths`, and `includePaths`; only those strings were changed
to `/workspace/v1` and `/workspace/v2`. No capture field changed. The `cache/`
directories were removed for the same reason.

`v2` differs from `v1` so the delta is real:

- `sweep(address)` is added, which gives an ABI entry and a new selector.
- `deadline` is inserted between `owner` and `balance`, which moves `balance`
  from slot 1 to slot 2.
- The constructor takes an argument, which changes the creation bytecode.

The contract is test material. It is not written to be deployed and nothing in
this repository deploys it.

```bash
cd v1 && forge build && cd ../v2 && forge build
```

Then remove the `cache/` directories and rewrite the three absolute paths in
`out/build-info/*.json`, or the fixture will carry whichever machine rebuilt it.
