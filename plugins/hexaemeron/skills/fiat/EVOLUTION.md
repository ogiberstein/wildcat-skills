# Fiat evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `fiat-v2.3.0`
- Frontier status: `mature`
- Frontier revision: `installed-path-and-maturity-proof`
- Current frontier: Fiat's receipt-backed controller is unit-tested, and this delivery exercises its installed-path resolution and terminal maturity rule together from a packaged plugin.
- Next Fiat job: `None -- mature`

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `fiat-v1.1.0` | baseline | `installed-path-and-maturity-proof` | `a30bea33332e20c6780a77f5d82bc899d7004b8d09321628777d36289bd128d0` | [skills#74](https://github.com/wildcat-finance/skills/issues/74) | Versioning starts here. Fiat has explicit active-skill path resolution, a mature-frontier refusal, and its own held frontier. |
| `fiat-v1.2.0` | generation | `installed-path-and-maturity-proof` | `a30bea33332e20c6780a77f5d82bc899d7004b8d09321628777d36289bd128d0` | [skills#74](https://github.com/wildcat-finance/skills/issues/74) | Made publish terminal only after final staging, push, merge, branch cleanup where permitted, and closure of any recorded task issue. |
| `fiat-v2.2.0` | evolution | `installed-path-and-maturity-proof` | `17c94c70b434ea1cbc9c3cd6ff5f3054972af08f8e027b7ea9850f5e06695f77` | [installed delivery proof](../../docs/fiat-installed-path-and-maturity-proof/proof.md) | Closes the held frontier after recording the installed controller path and passing the installed and checkout test suites; later delivery receipts remain governed by the live controller. |
| `fiat-v2.3.0` | generation | `installed-path-and-maturity-proof` | `17c94c70b434ea1cbc9c3cd6ff5f3054972af08f8e027b7ea9850f5e06695f77` | Maintainer report: stacked runs on a named base silently retargeted to the default branch | The push phase now passes the base recorded at `init` to `gh pr create` instead of letting GitHub default it, so a run started from a named branch merges back into that branch. Frontier unchanged and still mature. |
