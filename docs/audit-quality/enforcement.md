# Every agent uses the same audit acceptance process

Execution contract 1.0.0 · 17 October 2026. Required for new audit work governed
by this skill pack under Dennis's instruction to carry audit quality through
across agents. This adopts the checking process, not an uncalibrated numeric
score, a specialist exam change, client consent or a new production privilege.

The [public method](https://blitzmetrics.com/how-we-audit/) owns the audit
procedure; the [quality standard](README.md) and [tier contract](tier-contracts.md)
own report-quality review. Retain valid baseline detail, source citations,
examples, figures and caveats. Preserve contracted outputs, existing task owners,
holds, delivery routes and the canonical private audit library. No new clock.

## Before any agent starts

1. Read the current task, source-owner/hold record, method, specialist exam and
   quality/tier contract. Pin the actual revisions; a model name is not proof
   these instructions loaded. Use the current shared runtime's startup path.
2. Agree the question, reader, scope, outputs, source window, allowance, actions,
   publisher and delivery/library destination. Missing evidence remains UNKNOWN.
3. Open the closest permitted prior audits. Build the baseline crosswalk and
   claim/evidence ledger before editing. Do not remove valid detail for brevity.
4. Use deterministic checks for arithmetic, IDs, schema and file integrity. Route
   judgment to a capable worker and final review to a fresh context. Escalate only
   missing authority, consequential decisions or unresolved material claims.

## Before release

Use the current tier receipt, even for a free diagnostic. Bulk output remains
screening with every record validated and flags plus the reproducible sample
reviewed; it is not full-audit acceptance. Inspect actual sources and final
rendered artifacts, including every contracted PDF page. Record all defects,
fix authorized issues at source, propagate corrections and retest dependencies.

The independent reviewer reads the frozen candidate, baseline, evidence and
contract without the producer's persuasive narrative. Bind content/privacy and
design results to every final hash. Calibrate real reviewers on at least three
safe anchors (clear fail, borderline, strong pass), retaining their independent
scores, disagreement and adjudication. Synthetic software tests do not establish
this calibration. A high score cannot waive a gate. Until calibration is actually
recorded, numbers stay provisional and the quality acceptance gate stays held.

Create `bundle-manifest.json` privately with schema `UAQG-BUNDLE-1.0.0`, a `receipt`
entry and ID-keyed `artifacts` and `evidence` objects. Every entry contains only
`path` (relative to that bundle directory) and `sha256` (actual file bytes).
Include **every** artifact and evidence row in the tier receipt. Capture external
sources/review records in authorized private snapshots; retain original locators
in the receipt. The manifest does not contact websites or resolve access for you.

Each evidence entry points to a JSON capture envelope with exactly these fields:
`schema_version: UAQG-EVIDENCE-SNAPSHOT-1.0.0`, `synthetic` (boolean), `evidence_id`,
`original_locator` (matching the receipt), and `capture: {path, sha256}` for the
separate actual source/review file. The tier receipt's additive `bundle_evidence`
array pins every envelope with `{id, path, sha256}`. Thus changing just the
manifest, an envelope or the captured bytes invalidates the frozen commitment.
Keep all snapshots private; they may contain private records. `synthetic` describes
fabricated test evidence, not whether a real inspected source discusses a
hypothetical. Real recorded calibration on safe synthetic anchors is real review
evidence; copying the software fixture's invented calibration is not.

```json
{
  "schema_version": "UAQG-BUNDLE-1.0.0",
  "receipt": {"path": "run.json", "sha256": "<actual receipt SHA256>"},
  "artifacts": {"report": {"path": "report.pdf", "sha256": "<actual final SHA256>"}},
  "evidence": {"E-source": {"path": "evidence/source.txt", "sha256": "<actual capture SHA256>"}}
}
```

That abbreviated example is not a passing receipt. Use the
[tier template](tier-run-template.json) and include every required row.

```sh
python3 docs/audit-quality/verify_bundle.py --root /authorized/private/audit-bundle
```

The default is production mode: declared/known synthetic fixtures, missing/changed files,
incomplete evidence inventories, malformed receipts, stale reviews, missing
calibration and unresolved gates fail closed. The exit code is nonzero on HOLD.
`--mode exercise` requires synthetic inputs and yields only `EXERCISE_PASS`.
The checker emits its exact code/schema/profile hashes. Origin declarations and
locators must be independently checked: software cannot discover deliberate
relabelling of fabricated material as real. A bundle result is
**BUNDLE_CONSISTENT**, not a semantic certification, independence proof or
permission to send. Two agents can conspire to assert false evidence; the
independent source review and owning release gate remain necessary.

Only the existing authorized publisher delivers. Then obtain actual destination
readback, update the release evidence and rerun the bundle check. File the full
package and verify its intended library/delivery access in the same session.
Record quality acceptance, delivery and filing separately. Never mark done from
a generated PDF, sent message, merged code or folder listing alone. A truthful
limited diagnostic may be shared only within its existing authority, labeled
incomplete rather than accepted; it cannot substitute for a contracted full audit.

## Prove each runtime can follow it

Use the existing private runtime registry; do not create a competing agent roster.
For each intended runtime/account/workspace record source revision READ, a
fresh-session load, and a harmless checked exercise. Have it show that changing
a final file or removing evidence changes PASS to HOLD. Corrected arithmetic must
reach every dependent output; stopped tasks remain stopped and retries create no
duplicate delivery. Record the actual app/model label or UNKNOWN, tested revision,
output and reviewer. Successful exercise does not establish production judgment.

Track READ, APPLIED, TESTED and BLOCKED separately. Require a source-backed real
run with independent acceptance/delivery/filing evidence before operational
quality claims. Candidate seats and missing bindings stay unresolved. One agent's
test cannot clear the others. Installation, instruction loading, canary success,
calibration and a real delivered audit are separate states.

The current shared-runtime coordinator maintains adoption through its existing
registry/receipt process. This file installs no scheduler, model service, access
grant or vendor-side restriction. Source-level requirements cannot physically
prevent a disconnected agent from bypassing a publisher; only an integrated
publisher gate can do that. Report unintegrated routes explicitly.

## Required real-media package for every human-facing audit

Dennis Yu, 18 November 2026: “Real pictures, videos, thumbnails, greatest hits,
and useful next steps should be required to earn an A.” This applies to every
agent and every human-facing audit: personal brand, SEO, GEO, security,
subscriptions, weekly MAA, ads, profiles and operations, regardless of price.

An A, A+ or A- requires genuine relevant source-bound photographs; verified real
video with its original accurate thumbnail/poster and exact usable watch link
(or a tested QR to that exact source in print); curated greatest hits stating
source, date, buyer relevance, intended reader and next use; and useful
source-linked next actions with owner/function, concrete first step, timeframe,
dependencies, authority, destination, done test and measurement when applicable.
Audio can add proof but cannot replace required video. Diagrams, screenshots,
charts and process maps add explanation; they cannot replace this package.
Stock/generated imagery cannot serve as observed proof. Counts cannot prove truth.

Independently inspect the final artifact, each included source and its relevance,
rights, identity, crop, accurate video/thumbnail pairing, greatest-hit selection
and action usefulness. Bind the review to exact final hash, physical page/section,
source evidence/capture and media IDs. Metadata discovery is not recording review;
record actual frames/transcript or muted recording inspection and never claim to
have heard/watched lessons from metadata alone. Test click/QR destinations and
intended-recipient access. A homepage, broken link or inaccessible private player
is insufficient. Historic media may be useful when clearly dated and relevant;
a stale capture/review or unrelated asset cannot earn current acceptance.

If any component cannot be verified, disclose the exact gap, required revision
and next verification; mark report quality A-INELIGIBLE / REVISION_REQUIRED.
There is no missing-media, N/A, “where useful”, or “only on request” A waiver.
Do not fabricate assets or lower the subject's reputation/SEO/security score
because the report lacks media. Keep specialist exams and numerical report
weights 25/25/20/15/10/5, threshold 85, calibration, privacy, authority and full
package gates intact. Pure machine/bulk outputs may stay SCREENING, with no A
or full-report claim. Historical receipts remain historical; legacy schemas
cannot accept new production reports. Synthetic tests are exercises, never real
runtime adoption or client proof. Source publication is not fleet activation.

The November 10 article publication fallback remains an article rule; it does
not waive this stricter audit A gate. Run the versioned typed contract and bundle
checks, then independent semantic review; a consistency PASS is not a truth certificate.

UAQG 2.0.0 is a breaking receipt contract: use UAQG-TIER-RECEIPT-2.0.0. Retain previous records without retroactive acceptance.

Video curation may use verified video identity, original poster and an explicitly attributed publisher description without pretending the full recording was watched. Claims of a lesson, quote or observed behavior require inspection of the corresponding recording content. Record this distinction in claim_basis and content_review_method.
