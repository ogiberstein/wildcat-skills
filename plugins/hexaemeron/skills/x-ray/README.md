# X-Ray

Know your protocol before auditors do.

Built for:

- **Protocol teams** preparing for an audit — fix the obvious so auditors can focus on what matters
- **Security researchers** starting a new engagement — get the full picture in minutes

Not a vulnerability scanner — it's the briefing you read before opening the first file.

## What You Get

One command produces:

| Output | What's Inside |
|--------|--------------|
| `x-ray.md` | Protocol overview, threat model, test gaps, git history, readiness verdict |
| `entry-points.md` | Every state-changing function classified by access level with call chains |
| `invariants.md` | Full invariant map — enforced guards, single-contract invariants, cross-contract trust assumptions, and higher-order economic properties |
| `architecture.svg` | Visual architecture diagram — contracts, actors, trust boundaries |

## Usage

```
Use the bundled `hexaemeron:x-ray` skill to prepare this codebase for audit.
```

## Tips

- **Start with the verdict.** The report ends with a tier and 3-5 structural facts. If you only read one section, read that.
- **Use entry-points.md as your map.** Start with permissionless functions — those are the highest-risk surface.
- **Follow the `invariants.md` links.** Attack-surface bullets point into that file where the underlying code relationships are recorded.
