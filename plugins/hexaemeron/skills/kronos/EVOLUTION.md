# Kronos evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `kronos-v0.3.0`
- Frontier status: `mature`
- Frontier revision: `terminal-goal-loop`
- Current frontier: Kronos ranks eligible held Next Fiat jobs, selects the highest-value one, sets one durable goal, runs Fiat, and repeats until none remain.
- Next Fiat job: `None -- mature`

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `kronos-v0.0.0` | baseline | `terminal-goal-loop` | `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` | [skills#74](https://github.com/wildcat-finance/skills/issues/74) | Kronos starts here. It is complete and terminal by design. |
| `kronos-v0.1.0` | generation | `terminal-goal-loop` | `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` | Maintainer report: nine governed plugin ledgers were invisible to discovery | Scope now spans every plugin in the checkout rather than the invoking plugin alone, discovery descends into each plugin's own skills directory and names a skill by its own directory, ungoverned skills are reported instead of dropped, and the end-of-loop rescan re-evaluates every governed skill. Terminal by design is unchanged: the evolution counter stays at 0. |
| `kronos-v0.2.0` | generation | `terminal-goal-loop` | `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` | Maintainer request: constrain a native Kronos mode to the phase skills | Adds a fail-closed phase-only mode whose market is fixed to the six Hexaemeron phase skills, with an optional iteration cap. Ranking, Fiat ownership, repeated rescans and the full-market terminal loop are unchanged. |
| `kronos-v0.3.0` | generation | `terminal-goal-loop` | `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` | Wishlist kronos-1, taken at the maintainer's direction | Each ranking pass is now recorded. Step 4 appends the pass to `.kronos/scoreboard.jsonl` at the scope root and step 8 reads it back before reranking, so an axis score that moves for a held job nobody touched is visible rather than lost with the chat that carried it. A new `scripts/kronos.py` computes each candidate's held-job hash from that ledger on disk, as the SHA-256 of the canonical frontier line `VERSIONING.md` defines, so a recorded line can be checked against the digest the ledger already stores; taking a hash from the caller would have been a second way of naming one thing. The scoreboard is gitignored on purpose. Fiat refuses to start against a dirty tree, so a committed scoreboard would stop the loop's next iteration before it began, and having Kronos commit it instead would break the first hard rule. The cost is that the record lives on the machine that ran the loop. Ranking, the four axes and their caps, the tie-break and Fiat ownership are unchanged, and the writer records a judgement rather than making one. Terminal by design is unchanged: the evolution counter stays at 0 and the frontier is retained byte for byte. |
