# Brevitas

<!-- marketplace-context:start -->
## In one line

Brevitas puts mechanical volume and structure limits on engineering review prose without cutting its evidence.

**Try something else when.** Use Imprimatur for banned vocabulary, Vulgate for register, and Sapheneia for AuDHD interaction shape. Brevitas does not own any of those jobs.

**Current frontier.** The linter has not been forward-tested across a held cross-model corpus of engineering reviews, and preservation of counterexamples and reproduction steps remains agent-checked.

**Next Fiat job.** Use /hexaemeron:fiat to Forward-test Brevitas across held x-ray, Solidity-auditor, gas, invariant and diff-review outputs, then add every confirmed structural bypass to the corpus without weakening evidence precedence. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Brevitas is the last structural pass for audit findings, security reviews, gas
analysis, invariant discussion, diff review and protocol commentary. It does
not choose words or voice. It controls line count, finding shape, headings,
tables, code fences and the prose between points.

The evidence rule comes first. Addresses, transaction hashes, `file:line`
references, numbers, counterexamples, reproduction steps and statements of
what could not be established survive every rewrite. `--source` checks the
machine-readable subset. An explicit evidence exception keeps longer material
when the five-line finding form cannot hold it.

Brevitas includes:

- one canonical [`SKILL.md`](skills/brevitas/SKILL.md) shared by Codex, Claude Code and portable agents;
- the standard-library [`brevitas.py`](skills/brevitas/scripts/brevitas.py) linter for files and stdin;
- a Make target for written reports and source-preservation checks; and
- three audit-derived corpus cases, including one that must retain the original finding rather than compress it.

#### Day to day

**Developers.** A diff review has two real defects buried under setup, transitions and a repeated summary. Brevitas keeps each defect to claim, location, mechanism, impact and fix, then rejects the draft if its line budget or structure drifts.

**Security and audit.** A finding carries addresses, exact locations, numeric traces and a reproduction sequence. Brevitas cuts connective prose first, checks the machine-readable evidence against the source, and permits a marked exception when the remaining evidence needs more than five lines.
