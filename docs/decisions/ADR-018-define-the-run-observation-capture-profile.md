# ADR-018: Define the run-observation capture profile

## Status

Accepted, 2026-08-24. Recorded for [skills#435](https://github.com/wildcat-finance/skills/issues/435).

## Context

ADR-015 defines a structural record after an observation exists. It does not
say what a host may retain while turning a candidate event into that record.
The absence leaves a tempting but unsafe gap: collect arbitrary diagnostics,
then attempt to remove sensitive content later.

## Decision

The root Promise Machine owns a deterministic pre-persistence profile named
`promise-machine-run-observation-capture/v1`. It has a closed structured
candidate adapter, a direct descriptor allowlist, a visible redaction object,
repository-path de-hosting, and a domain-separated fingerprint for declared
high-entropy correlation material. The durable writer accepts the runtime's
accepted result only.

An unknown, over-limit, unsafe, or unclassifiable candidate produces a bounded
gap or refusal with a stable code. It never produces a partial candidate dump.
Redaction records a field class, reason code, and method; it does not repeat
the source field name, value, size, path, URL, or exception text. This gives
the record a useful omission signal without creating a secret archive.

## Alternatives

- **Denylist raw transcript text.** This has fewer initial fields, but aliases,
  nesting, and unknown shapes can retain material outside the named list.
- **Persist then scrub.** This keeps rich diagnostics, but puts the excluded
  bytes into durable storage before policy applies.
- **Fingerprint every omitted value.** This makes broad correlation possible,
  but lets low-entropy material be guessed and disguises an omission.

## Consequences

The profile has more adapters and fixtures than a denylist scrubber, but each
stored field can be reviewed in advance. A raw vault is rejected because it
persists excluded bytes before any policy applies. Generic text scraping is
also rejected because it cannot state what is safe to retain.

The decision neither binds Fiat receipts (#436), makes the handover report
(#437), nor changes the carryover process (#508). It also does not prove that
another process never retains a source value.
