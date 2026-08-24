<p align="center">
  <img src="./assets/characters/shoggoth.png" width="1200">
</p>

# The Shoggoth

The Shoggoth is a collective of specialist assistants built by
[Wildcat Labs](https://wildcat.finance) to help crypto developers at both the
protocol and frontend level. Its members preserve evidence, test contracts,
measure gas, investigate failures, shape documentation, and carry engineering
work through a controlled delivery loop.

[Hexaemeron](./plugins/hexaemeron) has proved to be an effective engineer on
work that can be reduced to explicit steps, tests, audits, and receipts. That is
a claim about recorded repository work, not a claim that it is infallible or
ready to operate without supervision.

The illustrated [contributor guide](./docs/how-to-help-shoggoth.md), also
available as a [PDF](./docs/pdf/how-to-help-shoggoth.pdf), explains how a
Hexaemeron run moves from a named issue through study, implementation,
independent review, and a pull request with evidence a maintainer can inspect.
You do not need to understand the whole collective before taking one bounded
job through that process.

The [Shoggoth Interceptor](https://github.com/laurenceday/shoggoth-interceptor)
puts the same collective into a harness for tearing through issue queues in
external repositories. It is experimental and is not production-ready.

The name Shoggoth can refer to one agent or the collective. The full convention
lives in the [Shoggoth identity contract](./SHOGGOTH.md).

## So, You Want To Build God?

Ask the Atlas for a number. Pick your harness. Finish what you start.

The [Shoggoth Wave Atlas](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/)
draws one random open issue from the full pool whose recorded hard dependencies
are closed. You do not choose a Wave. Pick one tested bootstrap below; that
single click asks the Atlas for a job and opens a new chat with its number,
issue URL, install request and Fiat request filled in.

[![OpenAI - ChatGPT web bootstrap](https://img.shields.io/badge/OpenAI-ChatGPT_web_bootstrap-10A37F?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/chatgpt)
[![Anthropic - Claude web bootstrap](https://img.shields.io/badge/Anthropic-Claude_web_bootstrap-D97757?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/claude)
[![Atlas - manual prompt](https://img.shields.io/badge/Atlas-Manual_prompt-3E68FF?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/api/job)

The friendly hand-off looks like: **Aye, here you go - #123.**

> [!WARNING]
> Fiat does not yet support checkpointing. Work is actively ongoing to complete
> it. Once Fiat starts, complete the entire run locally. Closing the harness,
> abandoning the run or moving an unfinished run to another session can lose
> the work. Do not assume that another contributor or session can resume it.

This route is for an external human contributor, not Shoggoth. Keep your own
Git author, valid signing identity and GitHub account. The required Shoggoth
provenance trailers supplement that authorship; they do not authorise use of
Shoggoth's private key or account. Confirm that the coding environment can sign
and publish as you before `hexctl init`; otherwise move the Atlas prompt to a
suitable local harness before the run starts.

The ChatGPT and Claude links are the only Atlas routes covered by the current
launcher tests. They allocate a job and prefill its prompt; they do not prove
that a browser chat can complete a local Fiat run. The prompt tells the chat to
stop before `hexctl init` when it cannot work in the repository, sign as the
human contributor and publish through that contributor's GitHub account. Open
the repository in the local coding harness you will keep for the whole run.
[Codex](./INSTALL.md#codex) and [Claude Code](./INSTALL.md#claude-code) have
native Wildcat marketplace packages. GitHub Copilot, Cursor, Gemini CLI and
Windsurf use the [manual route](./docs/how-to-help-shoggoth.md#the-secondary-manual-route):
open the repository, read `AGENTS.md`, then paste the exact Atlas prompt. They
are not presented as tested one-click Atlas launchers. Cline and Roo Code are
not listed as launch options because this repository has no checked Atlas
hand-off for them.

Fiat keeps the bounded run in order: study, runbook, implementation, audit,
prose, push and integration. Code that looks finished is not the endpoint. The
run is complete when the controller says its required steps and checks are
complete and the contribution is ready for the normal GitHub pull-request
path. The [contributor guide](./docs/how-to-help-shoggoth.md) and
[printable PDF](./docs/pdf/how-to-help-shoggoth.pdf) show that route. If the
result is merged with your human authorship intact, GitHub includes you in the
repository's contributor history.

Fiat now checks the first half of that sentence and records the answer. It
stores, for every commit it pushes, the GitHub account the commit was matched
to and a digest of the author address, and it refuses to record a run as
integrated unless the base still carries each of those identities. Two
conditions are GitHub's rather than the repository's. The commit author address
has to be one GitHub can match to your account, and the list itself is GitHub's
to compute and publish on its own schedule. A run whose author address matches
no account records that plainly instead of guessing.

That record is what the contributor list is built from.
[CONTRIBUTORS.md](./CONTRIBUTORS.md) ranks the humans who have finished a job
here by merged commits, with merged pull requests as the tie-break, and the
thanks at the foot of this file name the same people by handle. A weekly job
regenerates both from the repository's own history, so nobody has to remember to
add anyone and there is nothing to ask for. Runtime host identities, the
Shoggoth's own account and the repository owner are excluded by name, each with
its reason shown in the generator's output.

## What Is It?

At the last recorded count, the Shoggoth had 24 members: 15 domain agents and
9 phase agents. They are independent specialists with separate jobs, evidence,
and refusal rules, but they can hand work to one another without pretending the
next agent knows more than the previous one established.

The collective works alongside the vendored
[Pashov security suite](https://github.com/pashov/skills). That suite remains
Pashov's work under its upstream MIT licence. It is included without being
renamed, governed, or relicensed by Wildcat Labs.

## The Promise Machine

Every first-party skill is governed by the
[Promise Machine](./PROMISE_MACHINE.md). A promise says what a successful
operation actually establishes, names the evidence behind it, and states what
the result still does not prove. A handoff may narrow that evidence or add new
evidence; it may not silently strengthen the claim.

Missing, stale, or mismatched evidence blocks only the transition that depends
on it. Inspection, repair, rerun, rollback, and safe exit remain available.
The machine checks the contracts, identities, installation copies, host
manifests, evidence coverage, and first-party licence boundary. It does not
turn a passing structural check into proof that a domain claim is true.

## Meet the Shoggoth

### Alexandria

[Alexandria](./plugins/alexandria) keeps original lending and credit data intact
and produces a smaller view whose sources and mapping choices can be checked.
It is the archive desk: it preserves what arrived before anybody interprets it.

### Ariadne

[Ariadne](./plugins/ariadne) ties a released file to the evidence behind it in
a receipt another person can inspect. It records what was built and checked;
it does not claim that every statement inside the file is true.

### Berean

[Berean](./plugins/berean) tests a protocol research assistant against fixed
source material and recorded questions. It checks whether citations point to
the claimed bytes and whether live values belong to the stated chain and block.

### Brevitas

[Brevitas](./plugins/brevitas) keeps engineering writing short enough to use
without throwing away addresses, numbers, counterexamples, reproduction steps,
or other evidence that changes the decision.

### Hermes

[Hermes](./plugins/hermes) reduces the gas used by Solidity code one kind of
change at a time. It measures the saving, reruns behaviour checks, and rejects
an optimisation when the proof of safety or improvement does not hold.

### Hexaemeron

[Hexaemeron](./plugins/hexaemeron) turns a request into a study, a runbook, an
implementation, repeated independent audits, clear prose, and a controlled
integration. Its phase agents each own one part of that process, while Fiat
keeps the receipts and decides what may happen next.

### Horos

[Horos](./plugins/horos) identifies generated files, vendored trees, large data
blobs, and other material an agent can usually leave unread. Every exclusion
needs evidence, and no exclusion is allowed during security review.

### Janus

[Janus](./plugins/janus) checks what a smart-contract hook is allowed to see or
change before and after a host action. It tests the real effects against a
written permission boundary instead of assuming that a matching interface is
safe.

### Lemma

[Lemma](./plugins/lemma) divides Solidity compiler input or Markdown documents
into source-linked JSONL records. Each record keeps quotation text separate
from text prepared for a model or search system.

### Lazarus

[Lazarus](./plugins/lazarus) preserves the finite slice of historical Ethereum
state and RPC traffic needed by one application test. It can verify and replay
that fixture later without quietly falling back to a live endpoint.

### Pandects

[Pandects](./plugins/pandects) turns important credit-accounting rules into
executable Solidity checks. Each rule comes with a deliberately broken example
that proves the test catches the failure it claims to catch.

### Probitas

[Probitas](./plugins/probitas) assembles a sourced picture of a counterparty's
borrowing and repayment history from addresses they declared. Gaps remain
visible, and the result is evidence for a human decision rather than a verdict.

### Sapheneia

[Sapheneia](./plugins/sapheneia) shapes an assistant's replies for an AuDHD
reader. It keeps the current action, boundaries, evidence, unknowns, and next
step visible across a long task without changing the underlying facts.

### Tabularium

[Tabularium](./plugins/tabularium) turns preserved source records into a
rebuildable history of credit events. It keeps the source, mapping, coverage,
and gaps beside the output so somebody else can reproduce it later.

## How the members fit together

The names are job boundaries, not personalities pasted onto the same general
assistant. Alexandria preserves source material; Tabularium interprets it;
Probitas uses it in a bounded dossier. Lemma prepares source-linked chunks;
Berean evaluates an assistant that uses a pinned corpus. Lazarus preserves the
historical state a test needs; Ariadne binds a finished release to its evidence.
Pandects supplies accounting laws, Janus checks hook effects, and Hermes changes
gas only against measurements and behavioural evidence.

Hexaemeron coordinates delivery but does not absorb those jobs. It hands a
task to the relevant specialist and records what came back. The Promise Machine
is the shared rulebook that prevents any handoff from becoming an excuse to
claim more.

Installation, host-specific invocation, and publishing instructions live in
[INSTALL.md](./INSTALL.md).

## Use

### Requirements

Requirements apply only to the skills and operations named in the last column.
Checked-in examples and verification paths may need less.

| Requirement | Skills | When it is needed |
| --- | --- | --- |
| Python 3 | Alexandria, Ariadne, Brevitas, Hermes, Hexaemeron, Horos, Janus, Pandects | Their standard-library tools and checks |
| Python 3.9 or later | Berean, Probitas, Tabularium | Their release, dossier, and verification tools |
| Python 3.10 or later | Lemma | All Lemma commands |
| Python 3.11 or later plus its pinned packages | Lazarus | Capture, verification, replay, and release |
| Git | Hermes, Hexaemeron | Worktree, diff, and receipt checks |
| GitHub CLI (`gh`) | Hexaemeron | Issue, pull request, and integration phases |
| Foundry | Hermes, Janus, Pandects; Ariadne and Hexaemeron when working with Foundry projects | Solidity builds, tests, measurements, and captures |
| `solc`, Docker, or Podman | Lemma | Solidity chunking only |
| Archive Ethereum RPC | Lazarus | Capture only; verification and replay are offline |
| No local runtime | Sapheneia | It changes the assistant's interaction rather than running a tool |

### Requests

Each line below is a complete starting request for one first-party skill.

```text
Use $alexandria to preserve this lending-data capture, derive its reviewed credit rows, and query the declared address without hiding coverage gaps.
Use $ariadne to capture this release in an evidence statement, run its gates, and report its signature state without checking signatures.
Use $berean to verify this release's citations, chain readings, and promotion record against its pinned corpus.
Use $brevitas to shorten this engineering review without dropping addresses, hashes, file-and-line references, numbers, counterexamples, or reproduction steps.
Use $hermes to optimise gas in this repository. Name the corpus rule each candidate implements, work one optimisation class at a time, and keep the complete verification record.
Use $fiat to take this issue from study to a merged delivery, one receipted phase at a time.
Use $kronos to rank the held frontier jobs and run the best eligible one through Fiat until none remain.
Use $protasis to decide whether this study and runbook are ready to build from.
Use $elenchus to find the cause of this failure, fix it, and leave a test that fails without the fix.
Use $phylax to harden the off-chain inputs, subprocesses, network calls, secrets, dependencies, and model-output boundary of this change.
Use $ephoros to decide which events, metrics, traces, and alerts this step must emit so an operator can explain it later.
Use $metron to measure this slow path, change one thing, measure it the same way, and keep or revert the change on the result.
Use $hypomnema to record this decision, its alternatives, and its consequences where the next person will find them.
Use $imprimatur to check this draft for banned wording and unsupported technical claims.
Use $vulgate to rewrite this draft in plain human language without changing what it says.
Use $horos to create or check an evidence-backed reading boundary for this repository; do not apply it during security review.
Use $janus to check this hook against a conformance manifest for what it may observe and change around a host action.
Use $lemma to turn this Solidity compiler input or Markdown tree into validated, source-linked JSONL chunks.
Use $lazarus to capture this finite historical fixture, verify its proof-backed state, and replay only its exact requests.
Use $pandects to check this credit protocol against the executable laws in the corpus.
Use $probitas to build a sourced dossier on this counterparty from the addresses they declared.
Use $sapheneia to shape your replies for an AuDHD reader throughout this task.
Use $tabularium to build or verify a reproducible release of sourced credit events without hiding coverage gaps.
```

Fiat remains explicit-only. Describing a delivery task does not start the
controller unless the user names Fiat or Hexaemeron and asks it to run.
The Pashov suite keeps its upstream invocation and operating instructions.

## Repository layout

```text
.claude-plugin/marketplace.json   one entry per plugin
.agents/plugins/marketplace.json  the same set, host-neutral
.agents/skills/promise-machine/   the sole host-neutral suite router
plugins/<name>/
├── .claude-plugin/plugin.json    host manifests; discovery and installation only
├── .codex-plugin/plugin.json
├── AGENTS.md                     runtime contract and selection table
├── LICENSE                       first-party plugin licence
├── README.md                     landing page
├── tests/
└── skills/<skill>/SKILL.md       canonical instructions, one directory per skill
```

Hexaemeron also carries the Pashov suite as a vendored, upstream-owned set.
Those skill directories keep their own MIT `LICENSE` and `NOTICE.md`; the
first-party Apache licence does not replace or govern them.

Codex, Claude Code, and portable agents load the same canonical skill
directories. Host manifests handle discovery and installation only. The target
repository's own instructions and the active skill's checks still apply.

## Wildcat Commons

The [Wildcat Commons](https://wildcat.finance) is in the process of creating an
accessible, permanent repository of credit-related data. This suite supplies
the tools needed to preserve original inputs, create reproducible credit-event
records, state executable credit laws, preserve historical test fixtures,
assemble evidence-bounded dossiers, evaluate source-grounded assistants, test
Wildcat hook boundaries, and bind releases to their evidence.

Those tools have all been produced: [Alexandria](./plugins/alexandria),
[Tabularium](./plugins/tabularium), [Pandects](./plugins/pandects),
[Lazarus](./plugins/lazarus), [Probitas](./plugins/probitas),
[Berean](./plugins/berean), [Janus](./plugins/janus), and
[Ariadne](./plugins/ariadne). Their individual boundaries still apply; the
Commons description does not turn a recorded source into verified truth or a
dossier into a lending verdict.

## Licence

Wildcat Labs first-party work in this repository is licensed under
[Apache-2.0](./LICENSE). The vendored Pashov skill set is explicitly excluded
and remains under its upstream MIT licence and notices.

<!-- contributors:start -->

## Thanks

Thanks to @kethcode and @radup1337.

<!-- contributors:end -->
