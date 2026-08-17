# Medusa, over an adapter you wrote

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** No law prevents fees from reducing pooled lender claims below amounts owed on open withdrawal batches.
<!-- marketplace-context:end -->

`medusa.json` carries the settings and leaves `targetContracts` empty, because
the target is the only part that is yours: the contract extending
`CorpusMedusa` or `DrivenCorpusMedusa` and naming your system.

Fill it in, or pass it on the command line and skip the file:

```bash
medusa fuzz --compilation-target . --target-contracts YourHarness --test-limit 20000
```

The settings match `adapters/echidna/echidna.yaml` wherever the two engines
have the same knob: twenty thousand transactions, sequences up to sixty-four
calls, assertion testing off and property testing on. `property_` is what
Medusa reads by default, and it is why the adapter carries that prefix rather
than a name somebody preferred.

Two things differ, and both reach the search record.

**Medusa exposes no seed.** Echidna takes one and reports the one it used, so a
campaign under it can be reproduced call for call. A Medusa record therefore
carries the engine, the configuration, the sequence length and the corpus
digest, and says nothing about a seed -- rather than carrying a null, which
would read as a run that had no seed instead of one nobody can read.

**Medusa reports the sequence it found; Echidna shrinks it first.** Turning a
Medusa failure into a deterministic replay is work that turning an Echidna one
mostly is not.

If a campaign exits before it starts -- `Failed to initialize the test chain`,
or a target reported missing from the compilation artefacts -- clear
`crytic-export/` and `.medusa-artifact-hash` and run again. An exit like that
produces output with no failures in it, which reads exactly like a clean run
and is not one.
