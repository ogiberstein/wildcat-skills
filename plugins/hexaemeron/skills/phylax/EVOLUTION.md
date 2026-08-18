Phylax evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `phylax-v0.1.0`
- Frontier status: `open`
- Frontier revision: `off-chain-boundary-controls`
- Current frontier: Phylax names the off-chain boundaries and the control each one needs, but every check it demands is read by a person rather than executed.
- Next Fiat job: Extend the lint to the TypeScript surface, covering raw HTML rendered without a sanitiser after it, a session token written to persisted client storage, and a fetch against a host with no allowlist. Accepted when each is caught in a fixture, the lint runs clean over wildcat-app-v2, and both suites pass.

History

- `phylax-v0.1.0` | baseline | `off-chain-boundary-controls` | `ce1e5ed764d74b77b7a8608305353de47ebd0b1ef6fb0091bd7590140e188fb6` | [ariadne untrusted-input tests](../../../ariadne/tests/test_untrusted_input.py) | Phylax starts here, holding the off-chain surface that the Solidity audit skills do not cover.
