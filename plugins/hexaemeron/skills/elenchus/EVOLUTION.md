# Elenchus evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `elenchus-v1.1.0`
- Frontier status: `mature`
- Frontier revision: `observed-failure-root-cause`
- Current frontier: A check overlays a fix's changed tests onto the parent and classifies unittest, Forge and Node guards from fresh runner-owned reports, while diagnostics remain inert evidence.
- Next Fiat job: None -- mature

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `elenchus-v0.1.0` | baseline | `observed-failure-root-cause` | `82ba62d430f8c7d248bcef1b2678aca9c56eefd21282a54cbce24d78e444cd8a` | [fiat audit loop reference](../fiat/references/audit-loop.md) | Elenchus starts here, holding root-cause work on failures that have already been observed. |
| `elenchus-v1.1.0` | evolution | `observed-failure-root-cause` | `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b` | [structured runner fixtures](../../tests/test_elenchus_checker.py), [study](../../docs/elenchus-structured-runner-reports/study.md) | The guard check replaces diagnostic matching with fresh unittest, Forge and Node report adapters; no evidenced next frontier remains. |
