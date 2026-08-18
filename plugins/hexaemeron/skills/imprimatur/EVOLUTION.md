Imprimatur evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `imprimatur-v2.1.0`
- Frontier status: `open`
- Frontier revision: `labelled-prose-v2`
- Current frontier: Imprimatur has a provenance-bound 64-sample evaluation, but labelled-prose-v1 failed the pre-registered annotation-agreement and structural-holdout coverage gates; its holdout is spent and its provisional scores cannot support tuning.
- Next Fiat job: Build labelled-prose-v2 by deterministically refilling structural holdout coverage, obtain two fresh blind annotations with sample-by-tier kappa and raw span F1 at least 0.80, then run calibration and one sealed holdout without tuning on v1 holdout.

- `imprimatur-v1.1.0` | baseline | `labelled-corpus-calibration` | `ed610953c08d982f939838315687b6672e19c2a20bdc0db6139fd4349e551535` | [skills#74](https://github.com/wildcat-finance/skills/issues/74) | Versioning starts here. Imprimatur has governed maturity handling and its own held frontier.
- `imprimatur-v2.1.0` | evolution | `labelled-prose-v2` | `092addc4bcae8cd93d34df41146b3a3bbd3fd24a529cd84b1d16e0399d7affb4` | [labelled-prose-v1](evals/labelled-prose-v1/README.md) | Published the provenance-bound corpus, independent raw labels, adjudication, deterministic evaluator, untouched baseline and single provisional holdout result. Agreement and structural holdout coverage failed, so the lint stayed unchanged and the frontier remains open.
