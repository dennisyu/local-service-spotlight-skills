---
{
  "title": "Public documentation has one auditable truth",
  "severity": "error",
  "captured": "2026-08-31",
  "captured_from": "Dennis Yu, Codex task auditing blitzmetrics.com/scheduled-jobs-fleet and the connected documentation ecosystem, 2026-08-31",
  "source": "https://blitzmetrics.com/scheduled-jobs-fleet/",
  "applies_to": [
    "published-html",
    "agent-behaviour"
  ],
  "checks": [
    {
      "id": "visible-provenance-rail",
      "kind": "require_regex",
      "pattern": "<(?:aside|section)\\b(?=[^>]*\\bdata-document-provenance\\s*=\\s*[\"']verified[\"'])(?=[^>]*\\bdata-human-author\\s*=\\s*[\"'][^\"']+[\"'])(?=[^>]*\\bdata-maintainer\\s*=\\s*[\"'][^\"']+[\"'])(?=[^>]*\\bdata-last-checked\\s*=\\s*[\"'][^\"']+[\"'])(?=[^>]*\\bdata-last-changed\\s*=\\s*[\"'][^\"']+[\"'])(?=[^>]*\\bdata-source-revision\\s*=\\s*[\"'][^\"']+[\"'])[^>]*>",
      "message": "the page has no complete, machine-readable provenance rail with author, maintainer, checked/changed timestamps, and source revision",
      "examples": {
        "violating": [
          "<p>By Dennis Yu · Updated July 22, 2026</p>",
          "<aside data-document-provenance=\"verified\" data-human-author=\"Dennis Yu\">Updated today</aside>"
        ],
        "clean": [
          "<aside data-document-provenance=\"verified\" data-human-author=\"Dennis Yu\" data-maintainer=\"Fleet Inventory job / Codex audit\" data-last-checked=\"2026-08-31T20:00:00-05:00\" data-last-changed=\"2026-08-25T23:06:50-07:00\" data-source-revision=\"wp:110278:113449\"><p>Human author: Dennis Yu. Maintained by Fleet Inventory job; audited by Codex.</p><time datetime=\"2026-08-31T20:00:00-05:00\">Checked August 31, 2026</time></aside>"
        ]
      }
    },
    {
      "id": "semantic-provenance-time",
      "kind": "require_regex",
      "pattern": "data-document-provenance\\s*=\\s*[\"']verified[\"'][^>]*>[\\s\\S]{0,5000}?<time\\b[^>]*\\bdatetime\\s*=\\s*[\"']\\d{4}-\\d{2}-\\d{2}(?:T[^\"']+)?[\"'][^>]*>",
      "message": "the provenance rail does not expose a visible semantic time with an ISO datetime",
      "examples": {
        "violating": [
          "<aside data-document-provenance=\"verified\" data-human-author=\"Dennis Yu\" data-maintainer=\"Codex\" data-last-checked=\"2026-08-31\" data-last-changed=\"2026-08-25\" data-source-revision=\"abc123\"><span>Updated recently</span></aside>"
        ],
        "clean": [
          "<aside data-document-provenance=\"verified\" data-human-author=\"Dennis Yu\" data-maintainer=\"Codex\" data-last-checked=\"2026-08-31T20:00:00-05:00\" data-last-changed=\"2026-08-25T23:06:50-07:00\" data-source-revision=\"abc123\"><time datetime=\"2026-08-31T20:00:00-05:00\">Checked August 31, 2026</time></aside>"
        ]
      }
    }
  ]
}
---

## Public documentation has one auditable truth

- **Publish one truth, not a fresh island inside a stale page.** A generator must own
  every claim derived from the same source: visible dates, counts, status cards,
  tables, changelog, links, metadata, and JSON-LD. On 2026-08-31 the Scheduled Jobs
  Fleet page showed a July 22 headline and eight automations around an August 25
  generated table with 53 rows. WordPress and RankMath carried the newer timestamp
  while the manual TechArticle schema carried the older one. Updating one HTML
  marker was therefore not an update to the document.
- **Render facts from typed canonical data.** Do not hand-copy a count, version,
  repository name, bundle name, cadence, or job status into prose. Generate it from
  the marketplace manifest, scheduler API, or other named owner. Label the unit:
  released skills, Task Library task records, scheduler definitions, observed jobs,
  and partner-specific agent roles are different things even when a page calls all of
  them “agents.”
- **Separate the clocks.** `last_checked` is when a named verifier compared the page
  with its sources. `last_changed` is when the public meaning last changed.
  `last_published` is when that revision reached the live URL. A no-change run advances
  only `last_checked` and still leaves a receipt. A generator write that changes only
  an inventory block does not advance the surrounding article's `last_changed` unless
  every dependent claim was reconciled.
- **Sign the document without replacing the expert.** Keep the human subject/author,
  and add the maintaining agent or scheduled job, exact model when the runtime exposes
  it (otherwise `UNKNOWN`), actual human reviewer or `not yet reviewed`, source URL and
  revision/commit, and a success or failure receipt. Never invent a reviewer or imply
  that an agent is the human expert. Public receipts and operational details still
  require the normal privacy and publication gate; every substantive run keeps a
  private receipt even when no public meta article is authorized.
- **Use one visible, semantic provenance rail.** Put the audit fields in an `<aside>`
  or `<section>` marked `data-document-provenance="verified"`, with the data attributes
  enforced above and a real `<time datetime="…">` visible to readers. `datePublished`
  stays separate. Schema `dateModified` must equal the visible clock for the public
  revision: normally `last_changed` on a static article, or `last_checked` when a
  no-change verification itself creates a new evidence-page revision. Preserve both
  clocks in the rail and allow only one publisher/Article owner to describe the document.
- **Prove scheduled state with execution receipts.** “Scheduled” means a definition
  exists. “Observed” means a firing left an immutable timestamped success or failure
  receipt containing timezone, runtime, stable job/run ID, source revision, result,
  destination, and live readback. Expire one-shots after their run window and classify
  disabled, paused, archived, failed, and unknown work separately from active work.
- **Fail visibly and fail closed.** If a source cannot be fetched, a scheduled check
  leaves no receipt, a reviewer has not reviewed, or values conflict, show `unknown`,
  `stale`, or `verification failed`; do not stamp “updated.” Cache-fill time is never
  a content-modified time.
- **Keep the knowledge graph reciprocal.** Every pillar, spotlight, partner page,
  definitive article, task, skill, and authorized meta article links back to its
  canonical owner and forward to the relevant examples and receipts. Reuse the shared
  spine: The System · Content Factory · Task Library · canonical skills/install ·
  Scheduled Jobs · receipt/meta policy · changelog.

The sweep proves that the required rail and semantic timestamp exist. It cannot prove
that the named person reviewed the page, that the source revision is genuine, or that
two numbers mean the same unit. Those assertions require source comparison and receipt
readback during the audit; passing the regex is necessary, never sufficient.
