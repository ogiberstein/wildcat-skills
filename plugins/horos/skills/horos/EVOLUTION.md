# Horos evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `horos-v1.1.0`
- Frontier status: `open`
- Frontier revision: `text-asset-and-sql-rules`
- Current frontier: Text assets and machine-emitted migration SQL evidenced in the wildcat-app-v2 bundle stay readable, and TypeScript skeleton maps are refused rather than built.
- Next Fiat job: Add evidence-bearing rule classes for text assets and machine-emitted migration SQL, holding zero false exclusions against the recorded wildcat-app-v2 bundle. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `horos-v0.1.0` | baseline | `live-evidence-and-ts-maps` | `35be1190b60ef3acab18434ca647628943a0073ecbbc14dc0a0f041365352fe8` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `horos-v1.1.0` | evolution | `text-asset-and-sql-rules` | `00037861d1e760fac2143bb83dd5d2d8c0978c391c3d669fc06cf70d01f7e187` | [wildcat-app-v2 evidence bundle](../../docs/evidence/wildcat-app-v2.md) | The held live-evidence job completed. The wildcat-app-v2 capture records 80.3% of readable bytes classified with zero false exclusions, and the maintainer refused TypeScript skeleton maps rather than take a parser dependency or a subprocess boundary. The new held job takes the capture's two quantified misses. |
