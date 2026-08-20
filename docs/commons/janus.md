# janus

<!-- marketplace-context:start -->
**Place in the marketplace.** Janus remains an unbuilt hook-conformance specification. Use the marketplace audit skills for a broader security review; Janus is the narrower before-and-after host boundary described here.
<!-- marketplace-context:end -->

Test a contract hook at the threshold it controls: what may happen before the
host action, what may happen after it, and what the hook must never change.

**Desk:** protocol engineering and security. **Status:** unbuilt spec.

## Naming

Janus is the Roman god of gates, passages and transitions, shown looking in
both directions. Hooks live at exactly that boundary. They inspect or alter an
action as it enters and leaves its host.

## Why this exists

Hooks make a fixed protocol extensible, but the host and the hook rarely share
a machine-readable contract describing permitted effects. An interface says
which function can be called. It does not say whether the hook may move value,
write host state, consume all remaining gas, change an authorisation result or
leave a user unable to exit.

That policy remains distributed across implementation code, comments and the
assumptions of whoever wrote the first hook. A new module can satisfy the ABI
and violate the host's economic contract.

## Why this belongs to Wildcat Labs

Wildcat uses hooks for access and policy around deposits, transfers,
withdrawals, borrowing and repayment. Those hooks receive protocol context and
extra data while sitting beside lender funds and borrower permissions. The
most dangerous mistakes are therefore effects the type system cannot express:
redirected value, stale credentials, gas grief, nested entry back into a host
action and an exit path that worked until a provider disappeared.

Wildcat can write the first host adapter against known mechanics and actual
hook templates. The useful public result is broader: a conformance format that
lets any host state what a module may observe and change, without asserting
that different hook architectures are interchangeable.

## What it does

A host adapter exposes actions, relevant state and economic roles. A hook
manifest declares:

- Entry points and the host actions around which they run.
- Calls and callbacks the hook is permitted to make.
- Host, hook and external storage it may change.
- Assets and recipients it may cause to move.
- Required behaviour on hook revert, host revert and partial batch failure.
- Gas budget and whether failure is fail-open or fail-closed.
- Liveness conditions for withdrawal, uninstall and emergency paths.

The harness generates ordinary and hostile sequences, snapshots state before
and after each threshold, and compares the observed delta with the manifest.

## Gates

1. **Permitted effects are enumerated.** An omitted storage write, call target
   or value movement is forbidden rather than implicitly accepted.
2. **Value conservation is independent of return values.** The harness checks
   balances and claims even when every call reports success.
3. **Exit gets a liveness property.** Credential expiry, provider removal,
   sanctions changes and hook failure cannot be tested only on entry paths.
4. **Revert behaviour is part of conformance.** State and value after nested or
   partial failure must match the host's declared rollback rule.
5. **Gas grief is exercised.** The suite includes hooks that consume gas,
   expand return data and create expensive callback paths.
6. **Re-entry crosses actions.** Tests enter a different host action from a
   callback, not only the function that invoked the hook.
7. **A host adapter limits every result.** Passing the Wildcat suite makes no
   claim about an ERC-7579 account or another protocol's callback model.

## What ships with it

- Hook-manifest schema.
- Host-adapter interface and state-delta recorder.
- Stateful Foundry harness and a deterministic unit-test mode.
- Hostile reference hooks for callback re-entry, gas grief, value redirection,
  storage mutation and stale authorisation.
- Wildcat host adapter and tests for its maintained hook templates.
- One second adapter only after the generic boundary survives the Wildcat
  implementation.
- Human and SARIF reports linking each violation to a manifest rule and trace.

## Relationship to existing work

Pandects supplies economic properties the harness can run across hook-driven
state transitions. Fizz can generate protocol-specific sequences around the
host adapter. Ariadne can record the manifest revision and conformance result
for a released hook.

## Prior art and boundary

[ERC-7579](https://eips.ethereum.org/EIPS/eip-7579) defines interoperable
module types and optional pre- and post-execution hooks for modular smart
accounts. That is a useful second architecture to study, but its hooks are not
Wildcat hooks and the two must not share claims merely because they share a
word.

Static analysers and fuzzers already find general Solidity defects. Janus
tests the semantic contract between a host and an extension: allowed effects,
rollback and exit liveness.

## Open questions

- Whether storage-delta rules can remain stable across host upgrades.
- How to describe a deliberately broad hook without reducing the manifest to
  "may change anything".
- Whether the first external adapter should target ERC-7579, a DEX hook model
  or another lending protocol.
- How to test liveness without pretending a bounded fuzz campaign proves that
  an exit will always complete.
