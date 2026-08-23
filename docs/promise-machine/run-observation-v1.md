# Promise Machine run observation v1

`promise-machine-run-observation/v1` is a checked JSON Lines record of
observable events in one run. It is not a transcript, recorder, telemetry
store, or source of hidden model reasoning.

## Check a record

Run the checker from the repository root:

```bash
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/success.jsonl
python3 scripts/run_observation.py check tests/fixtures/run-observation/invalid/hidden-reasoning.jsonl --json
```

Exit zero means only that the named bytes passed the v1 structural and
relational rules. A refusal exits one and reports stable `RO` findings. The
checker reads no network resource, follows no path named inside an event,
executes no record content, and never changes its input.

Input must be one regular, non-symlink UTF-8 file inside the repository. It
must end with a newline and contain one JSON object per line. The command caps
the file at 1,048,576 bytes, each line at 65,536 bytes, the record at 512
events, nesting at 12 levels, strings at 4,096 characters, and collections at
128 members. Finite JSON numbers are parsed as exact decimals and their
absolute value cannot exceed `1.7976931348623157e308`. These ceilings bound
hostile input; they are not performance claims.

A clean result is bound to one final bounded reopen and reread of the
caller-named file. The validator compares the final byte count and SHA-256
digest with the snapshot it checked and requires the same confined regular
file identity. That final reread is the observation instant. It does not lock
the path or claim that a cooperating writer cannot change it after the command
returns.

## Event contract

The schema at `schemas/promise-machine-run-observation-v1.schema.json` owns
the fields and closed shapes. Every event repeats:

- `schema_id`, exactly `promise-machine-run-observation/v1`;
- one `run_id`, a contiguous positive `sequence`, and unique `event_id`;
- a canonical uppercase RFC-3339 `time` with a real civil date, a numeric
  offset or `Z`, at most nine fractional digits, and no leap-second spelling;
  one closed `type`; and a `correlation_id`; and
- optional backward `parent_event_id`, flat scalar `metadata`, or explicit
  `unknowns` with a field and reason.

One `run.started` event opens the file and one `run.finished` event closes it.
The closed union also contains `capability.started`, `capability.finished`,
`transition.refused`, `retry.scheduled`, and `handoff.recorded`. Capability,
retry, handoff, parent, evidence, and finish references resolve only to earlier
events in the same run. The opening context names the issue or topic, step,
role, selected skill, and selected promise. A refusal preserves that promise,
and a handoff preserves the selected skill as its producer. A final `refused`
status requires an earlier transition refusal. A final `handoff` status requires
an earlier handoff event and may cite only evidence one of those events carried.
The handoff producer is the selected skill and its consumer is a different
skill; a self-handoff refuses.

An evidence definition names one id, subject, scope, time domain, Promise
Machine evidence class, source, and either a selector or SHA-256 digest. A
consumer repeats its subject, scope, time domain, and class exactly. A changed
subject or class refuses; the checker defines no universal ranking between
evidence classes. Inferred evidence names its deterministic rule in `source`
and one earlier event id in `selector`. A handoff can carry only evidence
defined or consumed by its named source event.

Optional `host` and `model` facts name their exposed source and identity.
Optional `token_usage` names its source, scope, accounting identity, and at
least one non-negative integer count. JSON Booleans are not token counts.
When a host does not expose a fact, omit it and record an unknown. Do not use a
placeholder, approximation, derivation, inference, rounded value, forecast or
other estimate. An event cannot supply a host, model, or token fact and mark
that same fact unknown.

Raw prompts, completions, instructions and directives, tool output, command
lines and scripts, source code, stack or execution traces, environment values,
credentials, signed payloads, transcripts, and hidden or internal reasoning do
not belong in the record.
Metadata and unknown-fact names use printable ASCII and must
contain an ASCII letter or digit after normalisation; this excludes Unicode
lookalikes from the name classifier. Raw-payload and hidden-work families refuse across separated,
compact, camel, prefix, suffix, token, and recognised acronym forms. Bounded
descriptors remain valid only when their values match the descriptor: counts,
lengths and sizes are non-negative integers, presence is Boolean, digests and
hashes are SHA-256, and formats, identities, names, references, selectors,
statuses and types are bounded stable names. Repository values are bounded
metadata: a repository path is a Unicode-scalar NFC string, relative,
slash-separated, and portable across common repository hosts. Unicode control,
format, and surrogate characters, non-NFC spellings, URI forms, empty
or dot segments, platform-reserved characters and names, and trailing dots or
spaces refuse. Windows device spellings include the superscript-one,
superscript-two and superscript-three forms of `COM` and `LPT`; each path
segment is at most 255 characters and at most 255
bytes when encoded as UTF-8. The complete encoded relative path is at most
4,096 UTF-8 bytes.
An opening repository identity names `before_commit`. A closing identity
repeats that path and commit beside `after_commit`, so the relation is explicit
and checked. Commits are full lowercase Git ids. No recorded path grants file
access. Opening and closing repository identities appear together or are both
omitted; a half-recorded transition refuses.

## Findings

Text and `--json` use the same sorted finding objects. Each finding names its
code, fault class, safe path, recovery, contract, and, when available, run id,
line, event id, and correlation id. A displayed input path is capped at 512
characters and carries a SHA-256 suffix when shortened. Diagnostics do not echo
rejected values or forbidden field names.

- `RO001`: unsafe, absent, unreadable, non-regular, or symlinked input.
- `RO002`: total-byte or event-count limit.
- `RO003`: line-byte limit.
- `RO004`: invalid UTF-8, malformed JSON, or truncation.
- `RO005`: duplicate object key at any depth.
- `RO006`: nesting, string, or collection limit.
- `RO007`: closed-shape or typed-field failure.
- `RO008`: missing, inconsistent, placeholder, or repeated identity.
- `RO009`: sequence or lifecycle failure.
- `RO010`: forward, missing, invalid, or cross-run event reference.
- `RO011`: duplicate or unbound evidence identity.
- `RO012`: changed evidence subject, scope, time domain, or class.
- `RO013`: hidden or internal reasoning field.
- `RO014`: raw or sensitive payload field.
- `RO015`: invalid optional host or model fact.
- `RO016`: invalid or unbound token usage.
- `RO017`: unsafe repository path or invalid Git commit.

The valid fixtures demonstrate success, refusal, retry, handoff, recorded
tokens, and unknown tokens. Refusing fixtures and
`python3 -m unittest tests.test_run_observation -v` exercise identity, order,
evidence, lifecycle, content, limit, path, duplicate-key, truncation, and
combined hostile cases.

## Boundary

Validation establishes neither completeness, external truth, cause, model
quality, delivery correctness, security, nor mutation authority. Fixtures are
constructed examples, not captured production runs. Capture and redaction
remain in issue #435, Fiat receipt binding remains in issue #436, and
cross-run diagnosis remains in issue #449.
