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
      "id": "provenance-contract",
      "kind": "provenance_contract",
      "message": "the page needs exactly one visible pending-or-receipt-linked provenance rail whose same-element identities, deterministic external receipt location, source revision, valid ISO clocks, and semantic times agree",
      "examples": {
        "violating": [
          "<p>By Dennis Yu · Updated July 22, 2026</p>",
          "<!-- <aside data-document-provenance=\"receipt-linked\"></aside> -->",
          "<script type=\"text/template\"><aside data-document-provenance=\"receipt-linked\"></aside></script><template><aside data-document-provenance=\"receipt-linked\"></aside></template>",
          "<div hidden><aside data-document-provenance=\"receipt-linked\"></aside></div>",
          "<aside data-document-provenance=\"receipt-linked\" data-last-checked=\"2026-02-30T20:00:00-05:00\"></aside>",
          "<aside data-document-provenance=\"receipt-linked\" data-human-author=\"someone\"></aside>",
          "<aside data-document-provenance=\"receipt-linked\" data-capture-result=\"success\"></aside>",
          "<aside data-document-provenance=\"verified\"></aside>"
        ],
        "clean": [
          "<!-- BM-FLEET-PAGE:START --><aside data-document-provenance=\"pending-external-verification\" data-verification-scope=\"external-exact-raw-wp-body-and-inclusive-marker-slice\" data-source-contract-url=\"https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/README.md\" data-human-author=\"Dennis Yu\" data-maintainer=\"Fleet documentation function\" data-maintainer-agent=\"agent:codex-fleet-audit\" data-maintainer-model=\"GPT-5\" data-human-reviewer=\"not yet reviewed\" data-capture-run-id=\"fleet-public-run-20260831\" data-scheduler-capture-result=\"success\" data-publication-verification-result=\"pending\" data-publication-receipt-id=\"fleet-page-bbbbbbbbbbbbbbbbbbbb\" data-publication-receipt-index=\"https://github.com/dennisyu/local-service-spotlight-skills/tree/main/receipts/agent-fleet\" data-publication-receipt-discovery-url=\"https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/fleet-page-bbbbbbbbbbbbbbbbbbbb.json\" data-last-checked=\"2026-08-31T20:00:00-05:00\" data-last-changed=\"2026-08-25T23:06:50-07:00\" data-source-url=\"https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/sources/0123456789abcdef0123456789abcdef01234567.json\" data-source-revision=\"0123456789abcdef0123456789abcdef01234567\"><p>State: pending-external-verification. Verification scope: external-exact-raw-wp-body-and-inclusive-marker-slice. Human author: Dennis Yu. Maintainer: Fleet documentation function. Agent: agent:codex-fleet-audit. Model: GPT-5. Human reviewer: not yet reviewed. Capture run: fleet-public-run-20260831. Scheduler capture result: success. Publication verification result: pending. Publication receipt ID: fleet-page-bbbbbbbbbbbbbbbbbbbb. Receipt discovery URL: https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/fleet-page-bbbbbbbbbbbbbbbbbbbb.json. Source revision: 0123456789abcdef0123456789abcdef01234567.</p><a href=\"https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/sources/0123456789abcdef0123456789abcdef01234567.json\">Public sanitized source manifest</a><a href=\"https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/README.md\">public verification rules</a><a href=\"https://github.com/dennisyu/local-service-spotlight-skills/tree/main/receipts/agent-fleet\">Public receipt ledger</a>Changed <time datetime=\"2026-08-25T23:06:50-07:00\">August 25, 2026</time>Checked <time datetime=\"2026-08-31T20:00:00-05:00\">August 31, 2026</time></aside><!-- BM-FLEET-PAGE:END -->",
          "<section data-source-revision=\"0123456789abcdef0123456789abcdef01234567\" data-source-url=\"https://example.test/sources/article.json\" data-last-changed=\"2026-08-25T23:06:50Z\" data-last-checked=\"2026-08-31T20:00:00Z\" data-capture-run-id=\"capture-200\" data-scheduler-capture-result=\"success\" data-publication-verification-result=\"failure\" data-publication-receipt-id=\"receipt-200\" data-publication-receipt-index=\"https://example.test/receipts\" data-publication-receipt-discovery-url=\"https://example.test/receipts/receipt-200.json\" data-human-reviewer=\"Mina Patel\" data-maintainer-model=\"UNKNOWN\" data-maintainer-agent=\"agent:codex-fleet-audit\" data-maintainer=\"Documentation function\" data-human-author=\"Dennis Yu\" data-verification-scope=\"external-exact-live-bytes\" data-document-provenance=\"receipt-linked\"><p>State: receipt-linked. Verification scope: external-exact-live-bytes. Human author: Dennis Yu. Maintainer: Documentation function. Agent: agent:codex-fleet-audit. Model: UNKNOWN. Human reviewer: Mina Patel. Capture run: capture-200. Scheduler capture result: success. Publication verification result: failure. Publication receipt ID: receipt-200. Receipt discovery URL: https://example.test/receipts/receipt-200.json. Source revision: 0123456789abcdef0123456789abcdef01234567.</p><a href=\"https://example.test/sources/article.json\">Public source</a><a href=\"https://example.test/receipts\">Public receipt ledger</a><a href=\"https://example.test/receipts/receipt-200.json\">Committed publication receipt</a><time datetime=\"2026-08-31T20:00:00Z\"><span>Checked August 31, 2026</span></time><time datetime=\"2026-08-25T23:06:50Z\">Changed August 25, 2026</time></section>"
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
  The live `https://blitzmetrics.com/scheduled-jobs-fleet/` target has a concrete
  daily-refresh SLA: its structural fleet sweep blocks when `last_checked` is more
  than 36 hours old. Other live public targets explicitly tagged `current-live`
  have a 30-day re-verification SLA. Immutable receipt/history targets and pages
  without that live-target policy have no inferred max-age rule; their freshness
  remains an explicit target policy or judgment check, never a guess from old HTML.
- **Sign the document without replacing the expert.** Keep the human subject/author,
  and separately name the maintaining function/job, namespaced public agent identity
  (`agent:<slug>` or `job:<slug>`), exact runtime-reported model
  (otherwise the literal `UNKNOWN`), actual human reviewer or an honest pending-review
  state, public-safe source URL and revision, public-safe capture alias, and success or
  failure result. Never invent a reviewer or imply that an agent is the human expert.
  `data-source-url` points to an approved public source or sanitized source manifest;
  `data-capture-run-id` is a public alias, never a private scheduler/job ID. Private
  prompts, schedules, paths, tokens and source records stay in the private receipt. If
  no truthful public-safe source can be linked, the page does not satisfy this public
  contract. Generic pages use the tracked append-only public documentation actor
  registry and a concrete public human name rather than a role/team phrase. Its
  canonical discovery artifact is
  <https://github.com/dennisyu/local-service-spotlight-skills/blob/main/standards/public-documentation-actor-registry.json>
  and its machine schema is
  <https://github.com/dennisyu/local-service-spotlight-skills/blob/main/standards/public-documentation-actor-registry.schema.json>.
  Published registry versions are immutable; the numerically newest current
  selection authorizes fresh generic-page audits and may revoke an old actor.
  The fleet
  scope additionally uses hash-selected versioned actor, reviewed-human, and model
  registries; raw strings must exactly equal a registered member.
  Multi-part and culturally unspaced Unicode names are valid; fleet
  publication separately restricts that name to its reviewed source-controlled roster.
  For the fleet, the source is the resolving sanitized manifest at
  `receipts/agent-fleet/sources/<sourceRevision>.json`, not the receipt-contract README.
  Standalone agents discover the source ledger at
  <https://github.com/dennisyu/local-service-spotlight-skills/tree/main/receipts/agent-fleet/sources>,
  the public receipt/registry contract at
  <https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/README.md>,
  the fleet identity-registry schema at
  <https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/identity-registry.schema.json>,
  and the definitive live article at
  <https://blitzmetrics.com/scheduled-jobs-fleet/>.
  The source-only manifest is stable across retries: it binds the canonical source
  repository, full revision, generator-contract version, configured, archived,
  invalid, and public-definition counts, plus the selected actor/human/model registry
  versions and exact identity-registry SHA-256, but no candidate hash, run identity,
  or clock. The content-addressed identity-registry artifact is committed before the
  source manifest; published registry versions remain immutable, while a newer current
  version may revoke an identity for new fleet evidence without invalidating old
  hash/version-bound receipts.
  Multiple candidates from one source revision reuse its exact URL/bytes; a new source
  revision gets a new append-only manifest. If a current fleet identity-registry
  pointer advances, fresh evidence may not reuse a same-revision manifest that selected
  the prior current registry: create a reviewed source commit and new source manifest
  bound to the current registry. Historical receipts still resolve their old
  hash-selected immutable version. The candidate remains blocked until that
  manifest resolves. Every substantive
  run keeps a private receipt even when no public meta
  article is authorized.
- **Use one visible, semantic provenance rail.** Put the audit fields in an `<aside>`
  or `<section>`. Before the deterministic publication receipt resolves, mark it
  `data-document-provenance="pending-external-verification"`; use
  `data-document-provenance="receipt-linked"` only when the named committed receipt
  already exists at render time and the rail names the real human reviewer. Exact
  candidate bytes emitted pending remain intrinsically pending after their URL later
  resolves; consumers read the external verdict. Re-rendering them linked creates a
  new candidate. `receipt-linked` means only that the receipt exists. Keep the two
  result layers separate:
  `data-scheduler-capture-result` reports only the upstream scheduler capture, while
  `data-publication-verification-result` is `pending` on a pending candidate and is
  `success` or `failure` only on a receipt-linked rendering that mirrors the receipt.
  An exact fleet candidate is not rewritten merely to certify itself; consumers resolve
  its deterministic external receipt. Reject the legacy generic `data-capture-result`
  because it cannot say which layer it describes. Use
  `data-verification-scope="external-exact-live-bytes"` for an exact response contract.
  The fleet's concrete value is
  `external-exact-raw-wp-body-and-inclusive-marker-slice`: the verifier separately
  proves the exact raw owned WordPress post-content body (including outside whitespace)
  and the unique inclusive anonymous slice from the exact
  `<!-- BM-FLEET-PAGE:START -->` through `<!-- BM-FLEET-PAGE:END -->` byte markers.
  It records the SHA-256 and byte length of the whole anonymous response and checks the
  single Article owner and its `dateModified`. The local candidate permits only
  whitespace outside its sole ordered marker pair.
  Put every enforced attribute on the rail itself: author, maintaining function, agent,
  model, reviewer, public scheduler-capture ID/result, publication-verification result,
  deterministic publication receipt ID, public ledger index and mutable discovery URL,
  public source URL/revision, and both clocks. Expose those values in reader-visible
  text. Make the source and resolving ledger index actual visible links; expose the
  expected discovery URL as text rather than a knowingly unresolved anchor while the
  receipt is pending. Once the state is `receipt-linked`, expose exactly one visible
  link whose `href` is that discovery URL, so ordinary link resolution can prove the
  named receipt exists. The fleet also puts the receipt-contract README in
  `data-source-contract-url` and exposes that exact URL through a distinct visible link
  with a non-empty reader-facing label. Use visible `<time>` elements that render the corresponding dates,
  whose `datetime` values exactly match the clocks in either order, and whose
  `Checked`/`Changed` labels are inside, immediately before, or immediately after the time.
- **Let the external verifier own the verdict.** The page never certifies its own bytes.
  The committed public receipt is one envelope; a separate local/private verification
  wrapper pins that receipt's ledger commit, path, immutable commit/blob URL and SHA-256,
  fetches the exact blob, then compares it with the candidate fields. The public receipt
  cannot contain its own commit hash. Publishing a second “verified” rendering would
  change the candidate bytes, so consumers resolve the pending/linked state at the
  external receipt. The mutable discovery URL is only a deterministic lookup; only the
  private wrapper's exact-commit URL plus blob SHA-256 is immutable proof.
  A verified fleet receipt binds the already-committed companion source manifest's exact
  SHA-256 from the later receipt commit's tree. It also carries an external browser attestation:
  `browserVisibilityVerified=true`, a public-safe browser verifier and run-receipt ID,
  and `browserCheckedAt`. The browser check must occur no earlier than Article/WordPress
  modification and no later than the receipt's `checkedAt`; the generator never writes
  that attestation for itself.
  `datePublished` stays separate. Schema `dateModified` is the actual WordPress
  publication-modified instant, not an alias for either visible evidence clock. The
  external verifier requires the single Article `dateModified` to equal the WordPress
  modified instant and to fall no earlier than the candidate's `last_checked` and no
  later than browser verification, which is no later than the receipt's `checkedAt`.
  The public-ledger validator can independently
  enforce the upper bound; the candidate-bound external verifier proves the lower one.
  Preserve all three clocks and allow only one publisher/Article owner.
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

The source sweep proves one structurally renderable rail has the required same-element
fields, real ISO instants, visible labels/links, and matching semantic timestamps. It
ignores comments and inert/closed containers and evaluates inline plus ordinary,
unconditional same-document CSS for the supported tag/class/id/attribute selector
subset, including common explicit offscreen, zero-clip, zero-filter, transparent-text,
and extreme text-indent hiding declarations. It deliberately does not pretend to compute
external stylesheets, conditional media/container rules, layers, animation, occlusion,
or the complete browser cascade. The deterministic publication readback must therefore
inspect the rendered browser's computed `display`, `visibility`, `content-visibility`,
`opacity`, clipping, filter, mask, transform, position, text paint, non-empty client boxes,
viewport intersection, and sampled occlusion for the rail, both times, source, ledger,
and fleet receipt-contract links. Neither check can prove
that the named person reviewed the page, the source revision is genuine, or two numbers
mean the same unit. Those assertions require source comparison and immutable receipt
readback; the structural contract is necessary, never sufficient.
