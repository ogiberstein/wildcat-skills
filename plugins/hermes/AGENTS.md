Hermes runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Hermes.** Hermes measures one Solidity gas optimisation class at a time and rejects the candidate when its Foundry evidence does not clear every gate. Use Pandects for credit-specific laws, or Hexaemeron's audit skills for a broader security review. **Current frontier:** No complete, reproducible live Wildcat evidence bundle is published.
<!-- marketplace-context:end -->

- Hermes is one Agent Skill. Read `skills/hermes/SKILL.md` in full before working on Solidity gas usage; it is the only instruction copy, so do not add a sibling browsing README.
- The agent needs text-file read and write access plus a shell in the user's target repository.
- The target needs Git, Python 3, Foundry and a clean working tree. If one is absent, follow the refusal in `SKILL.md`; do not estimate a result.
- Resolve `scripts/hermes.py` and `references/optimisation-catalogue.md` from `skills/hermes/`, regardless of the working directory.
- Run the harness in the target Foundry repository. Do not use this plugin checkout unless the user names it.
- `$hermes`, `/hermes:hermes` and a plain request to use Hermes are equivalent activations.
- Shell snippets describe commands to execute, not text to paraphrase.
- A non-zero harness exit rejects the gate. Do not continue, weaken a check or report acceptance.
- Only `result.json` with status `accepted` and exit code 0 signals acceptance. Report its evidence directory.
- Repository issue, branch, review and approval rules still apply before Hermes changes target source.
