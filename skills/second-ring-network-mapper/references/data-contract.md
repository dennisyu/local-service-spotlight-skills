# Second Ring local data contract

Read this before changing the parser, evidence labels, or report schema.

## Accepted input

### LinkedIn

Accept a `Connections.csv` file or a standard ZIP containing it. Scan past a short preamble for a row containing `First Name` and `Last Name`. Recognize these optional fields:

- `URL`
- `Email Address`
- `Company`
- `Position`
- `Connected On`

Every LinkedIn row is first-degree platform evidence. It is not proof of relationship strength.

### Google Contacts

Accept a Google Contacts CSV with `Name`, or `Given Name` plus `Family Name`. Recognize organization, title, and email variants when supplied. Treat this as address-book evidence, not proof of a social connection. Generic website fields are not person-identity evidence.

### Relationship CSV

Require these columns:

```csv
Source,Target,Relationship,Status,Evidence,Observed At
```

Optional target-context columns are `Target Company`, `Target Position`, and `Target URL`. The file must be separately owner-authorized. A public co-appearance belongs in `Status=shared_context`; it is not a supported private introduction edge.

## Safety limits

| Limit | Value |
|---|---:|
| Compressed ZIP | 25 MiB |
| Expanded ZIP total | 100 MiB |
| ZIP entries | 5,000 |
| Supported entry | 20 MiB |
| Compression ratio | 50:1 |
| Contacts | 50,000 |

Do not extract ZIP entries to disk. Reject encrypted, multi-disk, malformed, or ZIP64-dependent archives when the local runtime cannot validate them safely.

## Identity rules

Deduplicate only on a normalized email or safe HTTP(S) profile URL. Preserve name-only rows as separate records with stable source/row identities. Normalize diacritics for matching while retaining the displayed spelling. Reject non-HTTP(S) profile URLs.

If a target query matches multiple records, return ambiguity and no chosen person. Never merge on bare name, company, or title.

## Evidence statuses

Evaluate normalized exact values, never substring regexes.

| Class | Exact statuses | Supported path? |
|---|---|---|
| Verified | `confirmed`, `verified`, `verified participant` | Yes |
| Consented | `consented`, `consented contribution`, `contributed` | Yes |
| Documented | `documented`, `direct`, `direct connection`, `exported`, `saved`, `user export` | Yes |
| Contextual | `context`, `contextual`, `public`, `shared`, `shared context`, `shared_context` | No |
| Negative | `confirmation pending`, `not consented`, `not confirmed`, `not documented`, `not verified`, `unconfirmed`, `undocumented`, `unverified` | No |
| Unknown | Anything else | No |

Evaluate the negative set before provenance or other positive signals.

## Output contract

Default output is Markdown on stdout. Include:

- parser version and run time;
- source type, not source filename or path;
- imported, duplicate, skipped, direct, and supported-path counts;
- ranked direct actions with explainable factors;
- supported and unsupported two-hop candidates separately;
- ambiguity and missing-data warnings;
- one explicit next action;
- a statement of what the input proves and does not prove.

Never intentionally select dedicated email-address or provider-ID fields for output. Apply best-effort redaction to email-like and known provider-ID tokens found inside selected display fields, but do not claim that arbitrary hostile text is guaranteed free of every possible sensitive identifier. Do not include the source path or source filename. Do not create a file unless `--output` is supplied. Redacted mode replaces people with stable aliases and removes company/title context.
