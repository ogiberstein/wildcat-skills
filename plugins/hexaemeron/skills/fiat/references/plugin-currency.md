# Plugin currency

How a run gets the plugin it is supposed to be running, and what to do when it
is not. Two callers share this: preflight, when the controller turns out to be
older than the repository it is about to edit, and the marketplace pass, when an
install has just landed and the host has not seen it yet.

## Refreshing, per host

There is no portable way to reload a plugin, so use the one the host has. Pick
by the runtime you are actually in, not by the one the transcript mentions:

- **Claude Code.** Run the supported `/reload-plugins` or `/reload-skills`
  command. If the runtime refuses it, or the command is unavailable in this
  surface, treat that as no live refresh and fall through to the last case.
- **Codex.** Ask the user to continue the same Fiat run in a new chat. The
  controller state is durable, so `hexctl next` resumes exactly where the run
  stopped; nothing is lost by changing session.
- **Any other host.** Use its native refresh mechanism. Where none exists,
  request a new session, and say plainly that the run continues after it rather
  than during it.

After a refresh or a new session, re-resolve the paths from the newly active
`SKILL.md` rather than reusing the ones held from before. That is the whole
point of the refresh, and a stale `FIAT_SKILL_DIR` silently keeps the old
controller alive.

## An out-of-date controller

`hexctl init` compares its own ledger version against any Fiat checked into the
target repository and warns when they differ. A marketplace plugin is installed
from a published copy, so a repository that also holds Fiat's source can be a
whole evolution ahead of the controller driving the run.

This matters more than a version string. Every rule the newer controller
enforces goes unenforced, and the receipt cannot show it: a flag the old
controller does not accept looks exactly like a rule nobody ever wrote. A run
has already recorded its lint results as prose for this reason, against a
controller one evolution behind the flags its own ledger documented.

### Where the plugin actually comes from

Two repositories. All work lands in the public one; the private one is a mirror:

- **`wildcat-finance/skills`** is public and is where every pull request in this
  loop targets.
- **`wildcat-finance/skills-marketplace`** is private. A scheduled job
  force-pushes every branch and tag from the public repository into it. The cron
  asks for five minutes and GitHub has been delivering closer to twenty, so read
  the two heads rather than trusting an interval. `gh workflow run
  sync-skills-marketplace.yml --repo wildcat-finance/skills-marketplace` runs it
  now.

The lag is a chain rather than a step, and each link can sit behind the one
before it: a merge into the public repository, the mirror on its own schedule
after that, the install only when something updates it. All three were visibly
different during one run, at `fiat-v4.5.1`, `fiat-v4.4.1` and `fiat-v3.4.1`.

### Which route this host used

Do not assume. The same plugin arrives by different routes, and they do not all
let an agent update anything:

- **A git-backed marketplace.** The host holds a clone or a remote it can pull,
  and names a repository. The Claude Code CLI adds one with
  `/plugin marketplace add <owner/repo>`; Codex points at a repository and
  derives the plugin from it. Here an update is a command, and the agent can run
  it.
- **A managed marketplace.** The host holds an extracted, packaged copy under an
  opaque id, with a marketplace name and no git remote, no ref and no commit
  recorded anywhere. Nothing in the install says which commit it came from, which
  is why the version has to be read out of the skill's own `EVOLUTION.md`. Here
  an update means somebody re-publishing the package, and **the agent cannot do
  it**.

Tell them apart by looking, before promising anything:

```text
ls -d "$PLUGIN_ROOT/.git" 2>/dev/null            # git-backed if this exists
```

A managed install typically also sits beside a host manifest naming a
marketplace by id rather than by URL. If the plugin tree has no `.git` and the
path is an opaque identifier, treat it as managed.

Which repository matters only on the git-backed route, and then it is whichever
one that marketplace was added from. A private marketplace is added from the
mirror; a public one from `wildcat-finance/skills` directly. Read the host's
configuration rather than inferring it from the two names above.

### On a warning

Do not carry on and mention it.

1. Check what the marketplace is actually serving before installing anything,
   or you will install the version before last and conclude the update failed:

   ```text
   gh api repos/wildcat-finance/skills/contents/plugins/hexaemeron/skills/fiat/EVOLUTION.md \
     --jq '.content' | base64 -d | grep '^- Current version'
   gh api repos/wildcat-finance/skills-marketplace/contents/plugins/hexaemeron/skills/fiat/EVOLUTION.md \
     --jq '.content' | base64 -d | grep '^- Current version'
   ```

   On Claude Code the second one is what an update can give you. If it is behind
   the first, the mirror has not run yet. Trigger it rather than reaching around
   it, with `gh workflow run sync-skills-marketplace.yml --repo
   wildcat-finance/skills-marketplace`; hand-installing from the public
   repository puts an unpublished tree behind a run's receipts.
2. Update the installed plugin through the host's own installer, from the
   marketplace that host uses. Do not hand-edit a plugin cache and do not copy
   files over an installed plugin: the next legitimate update overwrites it, and
   nothing records that the run was driven by a tree nobody published.
3. Refresh through the host boundary above, then re-resolve the paths.
4. Confirm the versions now agree. `hexctl init` warns only at init, so check
   the two ledgers directly:

   ```text
   grep '^- Current version' "$FIAT_SKILL_DIR/EVOLUTION.md"
   grep '^- Current version' <target>/plugins/*/skills/fiat/EVOLUTION.md
   ```

5. If the run has already been initialised, `hexctl reset` is wrong: it archives
   a run that has done nothing. Continue the initialised run under the updated
   controller, which the durable state is designed for.

A Fiat change that lands in this repository cannot take effect for the very run
that made it. The controller driving a run is the one that was installed when it
started, so a rule shipped at step 3 governs the next run and not this one. Say
that plainly in the final report rather than implying the run enforced what it
had just written.

## When it cannot be updated

The gap goes on the ledger rather than into the conversation, the same way a
security suite that cannot run is waived rather than skipped:

```text
hexctl record controller_version '{"running":"fiat-vX.Y.Z","checked_in":"fiat-vA.B.C","reason":"<why the update could not happen>"}'
```

Then say so out loud, once, and continue. Record it when the host has no refresh
path, when the account cannot install, or when the user declines the update. Do
not record it merely because updating is inconvenient.

The receipt is what makes the rest of the run readable later. Any rule the newer
controller would have enforced is now a named, dated gap with both versions
beside it, rather than a reader in six months wondering why a round recorded no
lint exits and concluding that rounds never did.

## The case that is not a problem

A run whose target repository *is* the plugin's own source tree finds its own
ledger and compares it against itself. `init` skips that by identity, so there
is no warning and nothing to do. Developing Fiat inside this repository is the
normal case, not a misconfiguration.
