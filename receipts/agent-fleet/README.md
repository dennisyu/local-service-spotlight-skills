# Public agent-fleet publication receipts

This directory is the public, model-independent audit rail for sanitized agent-fleet
pages. A receipt records an external verdict about one publication candidate; it is
not a scheduler registry, a job-definition store, or permission to publish.

## Two honest page states

- A candidate is rendered `pending-external-verification` before its deterministic
  receipt exists. Pending is not failure. Those exact candidate bytes remain honestly
  pending even when the URL resolves later; consumers obtain the verdict externally.
- A distinct document may be rendered `receipt-linked` only when the named receipt
  already exists and a real human reviewer is named. Linked means “the receipt exists,”
  not “verified”: the receipt's `status` supplies the external publication verdict.
  Rewriting a pending candidate into linked creates different bytes and therefore a new
  candidate rather than retroactively certifying the old one.

The rail keeps two evidence layers separate. `data-scheduler-capture-result` is only
the upstream scheduler capture outcome (`success` or `failure`).
`data-publication-verification-result` is `pending` on a pending candidate; a distinct
receipt-linked rendering uses `success` or `failure` to mirror its receipt. The exact
fleet candidate is not rewritten merely to certify itself—consumers resolve its
deterministic external receipt. The legacy generic
`data-capture-result` is ambiguous and is not part of the contract.

The fleet contract is
`external-exact-raw-wp-body-and-inclusive-marker-slice` and keeps two different
hashes. `postContentHash` is the SHA-256 of the exact raw owned WordPress post-content
body, including whitespace outside the markers. The anonymous extraction
starts at the first byte of the exact
`<!-- BM-FLEET-PAGE:START -->` comment and ends at the last byte of the exact
`<!-- BM-FLEET-PAGE:END -->` comment. Both marker comments are included in
`extractedPostContentSha256`; every outside byte is excluded. The local candidate may
have only whitespace outside its sole ordered marker pair. The external verifier proves
the raw body hash from authenticated WordPress content/readback and independently
proves the inclusive slice in the anonymous response. It separately records the SHA-256
and byte length of that entire anonymous response, and confirms that exactly one Article
owner exists with the expected `dateModified`.
An exact-whole-response contract may use `external-exact-live-bytes`, but that is not
the fleet page's scope.

The clocks are distinct. The rail's `last_changed` records when meaning changed and
`last_checked` records the candidate evidence check. Article/WordPress `dateModified`
records the later publication modification. The external verifier requires
`last_checked <= articleDateModified == wordpressModifiedAt <= browserCheckedAt <= checkedAt`;
the public receipt validator can enforce the equality and latter bounds, while the
candidate-bound private wrapper proves the first lower bound.

## Deterministic ID without self-reference

Use one new file per publication: `<receiptId>.json`. Compute `receiptId` as
`fleet-page-` plus the first 20 lowercase hexadecimal characters of
`verificationHash`:

```text
receiptId = "fleet-page-" + verificationHash[:20]
```

The generator computes `verificationHash` before rendering the page, over canonical
JSON (sorted keys, no insignificant whitespace) containing the semantic content hash,
checked/changed clocks, change summary, public capture/source/model/review fields, and
the hash of private evidence—not the private evidence itself. That payload excludes
candidate page bytes, WordPress revision, receipt fields, and response hashes.

The page's deterministic discovery URL is:

```text
https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/<receiptId>.json
```

The mutable `main` URL is only the expected lookup location, never the immutability
proof. Neither that URL nor `receiptId` enters `verificationHash`, so embedding the
expected lookup in the candidate is not self-referential.

Human signatures use a concrete public human name (including culturally unspaced
Unicode names) and fleet publication restricts
them to the reviewed source-controlled roster. Machine/checking identities are never
free prose: `data-maintainer-agent`, `checkedBy`, and `browserCheckedBy` use a stable
`agent:<slug>` or `job:<slug>` identity with a lowercase public-safe slug of at least
three characters. The exact runtime model is separate from that actor identity.

## Sanitized source manifest

The receipt-contract README is not the fleet's data source. Before publication, commit
one strict public manifest at `sources/<sourceRevision>.json`, where the filename is the
full lowercase 40-hex source commit. Its exact fields are `schemaVersion`,
`status: sanitized-source-manifest`, `sourceRepository`, `sourceRevision`,
`generatorContract`, `configuredCount`, `archivedCount`, `invalidDefinitionCount`, and
`publicDefinitionCount`, plus `actorRegistryVersion`,
`humanReviewerRegistryVersion`, `modelRegistryVersion`, and
`identityRegistrySha256`; unknown or duplicate members fail validation. The repository
and generator values are fixed to
`https://github.com/Local-Service-Spotlight/agent-fleet` and
`fleet-public-render-v3`.

The canonical discovery registry is
[`public-identity-registry.json`](public-identity-registry.json). Its exact bytes are
also stored before publication at
`identity-registries/<identityRegistrySha256>.json`. A source manifest selects one
immutable actor, reviewed-human, and model version from that hash-addressed artifact.
Published version member arrays never change; a later numerically newer current
version may revoke an identity for new candidates without invalidating old evidence,
because historical receipts resolve the registry hash/version selected by their
source manifest. Registry strings are raw-exact public identifiers—Unicode lookalikes,
control/variation characters, placeholders, paths, emails, and credentials fail.
[`identity-registry.schema.json`](identity-registry.schema.json) describes the
machine shape. The exact top-level members are `schemaVersion` (integer `1`),
`currentActorRegistry`, `currentHumanReviewerRegistry`, `currentModelRegistry`,
`actorRegistries`, `humanReviewerRegistries`, and `modelRegistries`. Registry-map
keys end in a positive numeric `-vN`; values are nonempty, sorted, unique arrays.
Each current pointer must select the numerically newest version defined for its
kind. Published version arrays are immutable. Adding a newer version may choose a
smaller current roster to revoke an identity for new work, but it never deletes or
changes the old array. JSON Schema covers the portable shape; the duplicate-aware
Python contract additionally enforces exact canonical bytes, public-safe semantic
identities, newest-pointer and append-only-history rules.

The companion is source-only: it contains no candidate `contentHash`, run/reviewer
identity, or checked clock. Those values change across retries even when the source
commit does not. Commit the companion once in a source-only change and let the
candidate's deterministic mutable `data-source-url` resolve before publication. Normal
retries and multiple candidates from the same source revision reuse the identical URL
and bytes; a new source revision gets a new append-only companion. Only after publication
and external readback may a later change add the public receipt. The later receipt
commit's tree contains the already-committed, unchanged companion; the verified receipt
repeats its source revision and configured/public counts and records
`sourceManifestSha256`. Candidate `contentHash` remains bound by the receipt itself, not
by the source-only companion. The private wrapper pins that later receipt commit and
fetches both exact blobs from its tree.
If any current identity-registry pointer advances, no fresh candidate may reuse an
older source manifest that selected the prior current registry. Make a reviewed source
commit (even when the fleet inventory meaning is otherwise unchanged), publish its new
append-only source manifest with the current registry hash/versions, and render from
that revision. Historical receipts continue to validate against their hash-selected
immutable registry; this source-revision bump is what makes revocation effective for
new evidence without mutating an old companion.
[`sources/source.schema.json`](sources/source.schema.json) is the machine schema.
The production `sources/` namespace contains only real prepublication evidence. The
fabricated golden companion lives under `examples/sources/`; it is test data, is never
a resolving candidate source, and is excluded from the append-only production ledger.

## Receipt schema

[`receipt.schema.json`](receipt.schema.json) is the machine-readable schema. Every
receipt has `schemaVersion: 1`, a discriminating `status` of `verified` or
`verification-failed`, and the common candidate, source, reviewer, and verifier fields.
The schemas reject unknown members. The duplicate-aware Python validator separately
rejects repeated JSON member names before normal JSON decoding can discard them. The
only approved aggregate counters are `configuredCount`, `publicDefinitionCount`, and
`itemListCount` in a verified receipt.

A `verified` receipt additionally requires HTTP 200, a final anonymous readback,
both the raw owned-body and marker-bounded anonymous hashes, the whole-response hash and length,
one Article owner and its checked `dateModified`, the source-manifest SHA-256, and an
external rendered-browser visibility attestation. A `verification-failed` receipt
instead requires sanitized `failureStage`, `failureCode`, and `failureDetail` and must
omit success-only fields that were not proved. A failure receipt is still an immutable
audit record. Its publication-verification result is `failure`; that says nothing about
the separate scheduler-capture result.

`browserVisibilityVerified: true` attests that a separate rendered-browser run checked
computed `display`, `visibility`, `content-visibility`, `opacity`, clipping, filter, mask,
transform, position, and readable text paint; non-empty boxes intersecting the viewport;
and sampled occlusion for the rail, both semantic times, the source link, the ledger link,
and the separately named receipt-contract link. A box merely existing offscreen or under
a zero clip/transparent paint does not pass. The generator cannot set this field; the
external verifier records its own time, namespaced public identity, and run-receipt ID.

The verified success envelope has exactly these fields—no extras. The tracked
[`examples/fleet-page-bbbbbbbbbbbbbbbbbbbb.json`](examples/fleet-page-bbbbbbbbbbbbbbbbbbbb.json)
and its exact-byte
[`fleet-page-bbbbbbbbbbbbbbbbbbbb.html`](examples/fleet-page-bbbbbbbbbbbbbbbbbbbb.html)
plus the explicit fixture-only
[`source companion`](examples/sources/0123456789abcdef0123456789abcdef01234567.json)
form the shared machine-testable golden set. Tests hash the full raw body/anonymous
response and the inclusive marker slice independently, validate the rail, compare its
IDs/source/model/reviewer/run with the receipt, and prove the three-clock chronology:

```json
{
  "schemaVersion": 1,
  "status": "verified",
  "receiptId": "fleet-page-<20 hex from verificationHash>",
  "postContentHash": "<SHA-256 of exact raw owned WordPress body>",
  "extractedPostContentSha256": "<SHA-256 of inclusive anonymous marker slice>",
  "anonymousResponseSha256": "<64 lowercase hex>",
  "anonymousContentLength": 1,
  "extractionStart": "<!-- BM-FLEET-PAGE:START -->",
  "extractionEnd": "<!-- BM-FLEET-PAGE:END -->",
  "contentHash": "<64 lowercase hex>",
  "verificationHash": "<64 lowercase hex whose prefix forms receiptId>",
  "sourceRevision": "<full source commit>",
  "sourceManifestSha256": "<SHA-256 of exact sanitized source-manifest bytes>",
  "model": "<runtime-reported model or UNKNOWN>",
  "humanReviewer": "<actual human's concrete public name>",
  "humanReviewerRole": "human",
  "runId": "<public-safe scheduler capture run alias>",
  "configuredCount": 0,
  "publicDefinitionCount": 0,
  "itemListCount": 0,
  "linkContentHash": "<same value as contentHash>",
  "linkReceiptId": "<stable link-receipt ID>",
  "liveUrl": "https://blitzmetrics.com/scheduled-jobs-fleet/",
  "finalAnonymousReadback": true,
  "browserVisibilityVerified": true,
  "browserCheckedAt": "<timezone-qualified ISO instant>",
  "browserCheckedBy": "<agent:slug or job:slug browser verifier ID>",
  "browserRunReceiptId": "<public-safe stable browser-run receipt ID>",
  "httpStatus": 200,
  "cacheBuster": "<public cache-buster alias>",
  "checkedAt": "<timezone-qualified ISO instant>",
  "checkedBy": "<agent:slug or job:slug receipt verifier ID>",
  "wordpressRevision": "wp:110278:<public-safe revision>",
  "articleSchemaCount": 1,
  "articleDateModified": "<timezone-qualified ISO instant>",
  "wordpressModifiedAt": "<same timezone-qualified ISO instant>"
}
```

`runId`, `linkReceiptId`, `browserRunReceiptId`, and `cacheBuster` are 3–200
character public references matching `[A-Za-z0-9][A-Za-z0-9._:-]{2,199}`.
They never contain slashes, invisible/control characters, placeholders, paths,
private data, or credentials. `wordpressRevision` is exactly
`wp:110278:[A-Za-z0-9][A-Za-z0-9._-]{0,119}`.

Example failed-attempt shape:

```json
{
  "schemaVersion": 1,
  "status": "verification-failed",
  "receiptId": "fleet-page-<20 hex from verificationHash>",
  "contentHash": "<64 lowercase hex>",
  "verificationHash": "<64 lowercase hex whose prefix forms receiptId>",
  "sourceRevision": "<full source commit>",
  "model": "UNKNOWN",
  "humanReviewer": "<actual human's concrete public name>",
  "humanReviewerRole": "human",
  "runId": "<public-safe scheduler capture run alias>",
  "liveUrl": "https://blitzmetrics.com/scheduled-jobs-fleet/",
  "checkedAt": "<timezone-qualified ISO instant>",
  "checkedBy": "<agent:slug or job:slug receipt verifier ID>",
  "failureStage": "anonymous-readback",
  "failureCode": "HASH_MISMATCH",
  "failureDetail": "The published bytes did not match the expected hashes."
}
```

Failure details are not free text. The schema and validator accept only the tracked,
exact stage/code/detail triples for candidate validation, link verification, WordPress
readback, anonymous HTTP/hash/marker checks, Article schema validation, and count
validation. Add a new sanitized template through a human-reviewed contract change;
never paste a raw exception, response, identifier, name, path, or customer detail into
an immutable receipt.

## Prepublication link receipt

The separate prepublication link receipt binds the stable `contentHash` and the exact,
duplicate-free URL/anchor result set. It carries `schemaVersion`, `status`, `receiptId`,
`contentHash`, `checkedAt`, `checkedBy`, and `results`; each result names its exact URL,
HTTP result, and anchor evidence when applicable. Its `checkedAt` must be no more than
24 hours old when consumed. It deliberately does **not** bind `verificationHash` or the
candidate's volatile `lastCheckedAt`, because a normal verification retry would
otherwise invalidate its own prerequisite. The publication receipt records the link
receipt's ID and repeats the stable content hash as `linkContentHash`.

## Prepublication artifacts and receipt immutability

When a new identity registry is needed, its content-addressed artifact is committed
first. The sanitized source companion is committed in a later source-only change and
may select only registry bytes that already existed in its base. After the live
page and external readback exist, the public receipt is added in a later commit and
**must not contain its own git commit hash**. Only after that receipt commit exists does
a separate local/private verification wrapper record `ledgerCommit`, `ledgerPath`, the
immutable exact-commit raw/blob URL, and the public receipt file's SHA-256. For a
verified receipt it fetches the unchanged source manifest from that later commit's tree
and matches its exact SHA-256 and bound fields. The wrapper verifier hashes and parses
both exact commit-path blobs, then compares their fields with the exact candidate. This
two-commit public sequence plus the private wrapper avoids an impossible
self-referential commit while still giving consumers immutable proof.

Merged receipt JSON is append-only: never overwrite, delete, rename, or reuse an ID. A
correction or republish gets a new ID and a new human-reviewed pull request. The
validator enforces the strict field set, deterministic ID, success/failure conditions,
approved failure templates, obvious path/email/credential patterns and—when given a
base ref—the append-only diff. The same base comparison requires every newly added
publication receipt's source companion to have existed as a valid regular blob in the
base commit, so source and receipt cannot first appear together. CI compares both pull
requests with their base commit and direct pushes to `main` with the pre-push commit:

```bash
python3 scripts/validate_agent_fleet_receipts.py
python3 scripts/validate_agent_fleet_receipts.py --base-ref origin/main
```

## Public-data boundary and review

`liveUrl` is exactly `https://blitzmetrics.com/scheduled-jobs-fleet/`; private,
loopback, link-local, dotless, alternate-host, credential-bearing, and query-string
variants are not valid fleet receipt targets.

Receipts must not contain private job IDs, prompts, schedules, registry or machine
paths, client data, emails, tokens, credentials, private artifact URLs, raw failure
payloads, or the private wrapper fields. Keep sensitive evidence in the private run
receipt and publish only the strict public schema's fields and an approved failure
template. Machine validation rejects duplicate JSON members, recursively decodes URL
escapes before scanning known leak shapes, and narrows the possible public payload; it
cannot infer whether an otherwise ordinary name or public-safe alias is
confidential in context. Human review remains the semantic privacy gate.

An agent may prepare a receipt on a branch. A human must review the exact JSON, privacy
boundary, live page, source revision, and hashes before merging. Every receipt pull
request and delivery update names the agent/model and states the actual human review
status.
