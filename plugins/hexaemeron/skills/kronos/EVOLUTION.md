Kronos evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `kronos-v0.1.0`
- Frontier status: `mature`
- Frontier revision: `terminal-goal-loop`
- Current frontier: Kronos ranks eligible held Next Fiat jobs, selects the highest-value one, sets one durable goal, runs Fiat, and repeats until none remain.
- Next Fiat job: `None -- mature`

- `kronos-v0.0.0` | baseline | `terminal-goal-loop` | `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` | [skills#74](https://github.com/wildcat-finance/skills/issues/74) | Kronos starts here. It is complete and terminal by design.
- `kronos-v0.1.0` | generation | `terminal-goal-loop` | `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` | Maintainer report: nine governed plugin ledgers were invisible to discovery | Scope now spans every plugin in the checkout rather than the invoking plugin alone, discovery descends into each plugin's own skills directory and names a skill by its own directory, ungoverned skills are reported instead of dropped, and the end-of-loop rescan re-evaluates every governed skill. Terminal by design is unchanged: the evolution counter stays at 0.
