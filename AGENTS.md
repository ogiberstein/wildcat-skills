# Instructions for local agents

This repository distributes agent skills. Do not treat a skill as active merely
because its files are present in context. Match the user's request against the
portable entries under `.agents/skills/`, load the selected entry, and follow
the canonical `SKILL.md` it names.

## Repository map

- Ariadne is under `plugins/ariadne/`. Read `plugins/ariadne/AGENTS.md` before
  running its skill or changing that plugin.
- Hermes is under `plugins/hermes/`. Read `plugins/hermes/AGENTS.md` before
  running its skill or changing that plugin.
- Hexaemeron is under `plugins/hexaemeron/`. Read
  `plugins/hexaemeron/AGENTS.md` before running one of its skills or changing
  that plugin.
- Lemma is under `plugins/lemma/`. Read `plugins/lemma/AGENTS.md` before
  running its skill or changing that plugin.
- Lazarus is under `plugins/lazarus/`. Read `plugins/lazarus/AGENTS.md` before
  running its skill or changing that plugin.
- Pandects is under `plugins/pandects/`. Read `plugins/pandects/AGENTS.md`
  before running its skill or changing that plugin.
- Probitas is under `plugins/probitas/`. Read `plugins/probitas/AGENTS.md`
  before running its skill or changing that plugin.
- Tabularium is under `plugins/tabularium/`. Read
  `plugins/tabularium/AGENTS.md` before running its skill or changing that
  plugin.
- `.claude-plugin/` and `.codex-plugin/` files install the same canonical skill
  directories on their named hosts. They do not change the meaning of a skill.
- `.agents/skills/` contains host-neutral entrypoints for agents that implement
  the Agent Skills discovery convention.

## Loading rules

1. Read the selected `SKILL.md` in full before acting.
2. Resolve paths relative to the directory containing that `SKILL.md`, unless
   the file defines another base explicitly.
3. Load linked references only when the selected skill directs you to them.
4. Treat slash commands, dollar-prefixed names, and plugin-qualified names as
   invocation aliases. They are not shell syntax.
5. Keep the user's target repository separate from this distribution
   repository. Run a skill's commands in the target named by the user.
6. Obey the target repository's own instructions and permission rules before
   any write or external side effect.

## Checks for changes to this repository

Run the checks that cover every changed area:

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py
python3 plugins/lemma/tests/test_markdown.py
python3 plugins/lemma/tests/test_solidity.py
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
python3 -m unittest discover -s plugins/pandects/tests -t plugins/pandects
python3 -m unittest discover -s plugins/probitas/tests -t plugins/probitas
python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium
```

Pandects also carries Solidity. From `plugins/pandects/`:

```bash
forge build
forge test
```

Validate every changed skill directory against the Agent Skills frontmatter
rules. Keep `SKILL.md` names equal to their parent directory names and keep
descriptions precise enough to select the skill without reading its body.
