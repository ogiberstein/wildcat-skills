# Runbook: help an external contributor evolve the Shoggoth

## Step 1: Publish the contributor path and its evidence

**Goal.** Commit the accepted study and runbook beside a plain-language guide that explains the present contribution path and the three proposed volunteer lanes.

**Entry.** Run branch `fiat/explain-how-contributors-help-evolve-shoggoth-an` at `98d0cded34bc559ba7ed2466988c40f0c3e28937`, with the study receipt recorded and no tracked run changes.

**Exit.** `docs/how-to-help-shoggoth-study.md` and `docs/how-to-help-shoggoth-runbook.md` match the receipted artefacts; `docs/how-to-help-shoggoth.md` names the current named-issue route, the external-contributor case, the proposed `wave`, `frontier` and `maintenance` lanes, the no-literal-cat mascot rule and the current/proposed boundary. Prove it with `cmp`, required-term assertions, Imprimatur, Brevitas and `python3 -m unittest discover -s tests`.

**Files.** Create `docs/how-to-help-shoggoth-study.md`, `docs/how-to-help-shoggoth-runbook.md` and `docs/how-to-help-shoggoth.md`.

**Tests.** Add a small document assertion script under `tmp/` only for the run; it checks the required headings, contribution facts, current/proposed labels and absence of personal naming. Run the root suite; its expected count is whatever the synced base reports, with zero failures.

**Disciplines.** phylax: the guide consumes GitHub facts, controlled by exact links and a dated snapshot. ephoros: none, no unattended process is added. metron: none, no performance claim. elenchus: any factual or lint failure stops publication and is corrected at the source. hypomnema: the committed study holds the design trade and the guide holds the public path.

## Step 2: Open the volunteer-selector discussion

**Goal.** File one framework observation that asks the repository to settle volunteer intent, default Wave selection, frontier opt-in, maintenance scope and the public claim signal.

**Entry.** Step 1's branch and guide, with no issue URL yet recorded in the guide.

**Exit.** One open issue exists in `wildcat-finance/skills`, labelled `observation` and `origin:ai`; its body opens by giving Protasis ownership of skill selection, includes the proposed intent packet, records the Wave 3 snapshot as the earliest Wave with eligible open issues, names the read-only issue boundary, and asks the unresolved questions. `docs/how-to-help-shoggoth.md` links the exact issue and a `gh issue view` readback matches the previewed title and body.

**Files.** Update `docs/how-to-help-shoggoth.md`. Keep the exact issue preview in `.hexaemeron/` as run evidence; do not commit a second copy.

**Tests.** Run required-term assertions, Imprimatur, Brevitas and `python3 -m unittest discover -s tests`; read the created issue back with `gh issue view --json` and compare title, labels and body.

**Disciplines.** phylax: this step opens a GitHub write boundary, controlled by exact preview, existing labels and readback. ephoros: none, the issue does not run unattended. metron: none, no performance claim. elenchus: a mismatched issue readback stops the step and is repaired before the guide is committed. hypomnema: the issue is the durable home for the unresolved selector decision.

## Step 3: Ship and inspect the mascot field guide

**Goal.** Produce the final wide-page PDF and infographic in the V2 visual system, using a humanoid faceted-head Shoggoth and no literal cat.

**Entry.** Step 2's branch, linked guide and verified discussion issue.

**Exit.** `docs/assets/how-to-help-shoggoth-infographic.png` and the final `output/pdf/how-to-help-shoggoth.pdf` exist. The PDF is no more than six pages, names the external contribution, distinguishes live and proposed routes, includes the discussion URL, uses the cream/black/blue/yellow field-guide system, and passes text extraction, page-count, file-reopen and rendered-page inspection. `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, the prose lints, required-term assertions and `python3 -m unittest discover -s tests` exit zero.

**Files.** Create `docs/assets/how-to-help-shoggoth-infographic.png` and `output/pdf/how-to-help-shoggoth.pdf`; update `.horos/boundary.json` if the tracked infographic earns an entry. Keep builders and page renders under `tmp/`.

**Tests.** Assert the generated image dimensions and readable file format; use `pdfinfo`, PyPDF text extraction and page-count checks; render every PDF page with Poppler and inspect the latest render; run the root suite and all lints covering changed files.

**Disciplines.** phylax: image generation and PDF authoring consume local reference files and write bounded outputs. ephoros: none, no unattended process ships. metron: none, page count is an editorial limit rather than a speed claim. elenchus: identity drift, clipping, overlap or missing text blocks delivery and causes one targeted regeneration or layout correction. hypomnema: the guide and issue remain the sources of meaning; the PDF is a derived public explanation.
