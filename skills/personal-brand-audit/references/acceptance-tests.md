# Acceptance tests and receipt

Run these against the final evidence ledger, rendered PDF, action register, and staged
delivery package. A check that was not run is **UNTESTED**, not passed.

## 1. Scope, identity, and evidence

- [ ] The subject is qualified by current company/role and at least two independent identity
  attributes; excluded namesakes are listed.
- [ ] Every substantive PDF claim, chart value, score, quote, and relationship edge points to
  an evidence ID.
- [ ] Every evidence ID resolves to an exact URL or authorized private record locator with
  title/publisher, event/publication date when known, capture timestamp, and source class.
- [ ] `OBSERVED`, `INFERRED`, and `UNKNOWN` are used according to the ledger tests. Every
  inference names its supporting IDs.
- [ ] No UNKNOWN is rendered as zero, failure, an empty chart bar, or a definitive absence.
- [ ] Public self-claims are not described as independent verification.
- [ ] Contradictory titles, dates, counts, pricing, roles, or results are grouped and visible;
  unresolved conflicts are not silently normalized.
- [ ] Search coverage lists names, aliases, handles, languages, markets, sources, date window,
  blocks, and timeouts.
- [ ] Source selection records the strongest suitable source for each claim, inspected
  captures/extracts and rejected or unresolved candidates. Distinct supporting URLs/authorized
  locators, underlying records, evidence rows and citation occurrences have separate counts.
  Duplicate links, mirrors, tracking fragments and uncited padding cannot meet the brief's
  declared research target; unmet coverage remains PARTIAL. No universal source quota applies.
- [ ] The claim map traces source/capture → extract → evidence ID → exact PDF claim/page →
  implication/action. A reviewer checks its completeness against the actual final report;
  merely validating the enumerated rows cannot prove no claims were omitted.
- [ ] The canonical [LSS Knowledge Graph
  Explorer](https://localservicespotlight.com/knowledge-graph-explorer/) was queried for the
  resolved subject, relevant company/employer, and every ranked public-association entity used
  in the report; the receipt records exact queries, capture time, candidates, and failures.
- [ ] The ledger records
  `graph_object_status=RESOLVED | AMBIGUOUS | NO_SAFE_OBJECT_RETURNED | UNKNOWN` and a separate
  `kgmid=<identifier> | UNKNOWN`; any resolved KGMID passes the two-independent-attribute
  identity gate. Human-facing display labels map explicitly to those enums, and a no-result is
  not described as proof that no panel exists.
- [ ] A normal Google name/name-plus-role query was checked separately from Explorer and forced
  `?kgmid=` links. Its
  `normal_google_panel_status=VISIBLE | NOT_VISIBLE_IN_THIS_CHECK | UNKNOWN` records query,
  date/timezone, locale/language, approximate location, device/surface, signed-in and
  personalization state, and screenshot/response locator.
- [ ] `owner_claim_status` is `UNKNOWN` unless the authorized owner-side Google claim dashboard,
  a screenshot/export from that dashboard, or a Google claim receipt proves `CLAIMED` or
  `NOT_CLAIMED`; Explorer defaults and public panel controls are not treated as owner-dashboard
  proof.

## 2. Connections, consent, and privacy

- [ ] Every “top connection” has dated public association evidence or direct user-confirmed
  private evidence.
- [ ] Every ranked public-association person or organization uses the same
  `graph_object_status`/`kgmid` enums as the subject, with dated association evidence and
  association-safe wording; the graph result is not presented as friendship, endorsement,
  relationship depth, or permission.
- [ ] Association type and relationship depth are separate; event co-presence, a follow, a
  tag, or a group photo never becomes friendship, endorsement, or warm access.
- [ ] Permission to quote, reuse a photo, name a private client, or contact a person is explicit
  or marked UNKNOWN/consent required.
- [ ] No private phone, email, home address, credential, token, attendee list, or unnecessary
  message text appears in the public artifact.
- [ ] Security-sensitive public exposure is routed privately and not reproduced as brand copy.
- [ ] Every non-public source records data classification, owner, export scope, redaction
  decision, restricted locator, retention/deletion date, and final disposition; restricted or
  security-sensitive fields do not appear in public artifacts.

## 3. Score and analysis integrity

- [ ] The receipt names the Brand Authority rubric version, and every numeric row cites both
  its evidence IDs and the exact anchor or documented interpolation that produced the score.
- [ ] All ten Brand Authority rows were checked and the headline equals their arithmetic sum,
  or the result says INCOMPLETE with a known subtotal and no pass verdict.
- [ ] The 80/100 pass line is unchanged.
- [ ] Brand Authority, SEO, Website QA, GEO, reputation, and social metrics remain separate;
  no blended “overall score” was invented.
- [ ] The top proof is sorted by the published 30-point authority dimensions, and any buy-box
  score is visibly provisional when the buy box is UNKNOWN.
- [ ] Page 1 contains four evidence-backed headline facts and stands alone; page 2 contains
  five to eight non-obvious findings that lead to decisions, not generic praise or a biography
  recap.
- [ ] The exact opening is saved with its revision. A reviewer quotes the words establishing
  the reader's situation, reason to care, useful decision/outcome and supporting evidence or
  mechanism. The audit delivers that promise. A short paragraph or readability score alone
  cannot pass meaning; unchecked fields remain UNKNOWN. Later pages lead with their takeaway.
- [ ] Recommendations distinguish a proof gap, a findability gap, a consistency gap, a
  measurement gap, and an access gap.
- [ ] Every live model/search observation records prompt, product/provider, model/version when
  surfaced, query mode, time/timezone, locale/language, account and personalization state,
  response/screenshot locator, citations, and failures or refusals.

## 4. Exact PDF and visual QA

- [ ] The rendered PDF has exactly **20 pages** according to a PDF parser, not a source-file
  page estimate.
- [ ] Pages 1, 2, and 20 satisfy their invariant contracts; a coverage crosswalk maps every
  default page requirement to actual pages 1–20, with no uncovered requirement or padding.
- [ ] All 20 pages were rendered to images and visually inspected at normal desktop/print size;
  record the montage/contact-sheet path and reviewer.
- [ ] Pages 1, 2, 7, the mapped agent-install page, and 20 received full-size spot checks; any defect triggered review of
  all affected pages.
- [ ] Every page contains a meaningful approved real photo, source screenshot, data chart, or
  evidence-backed diagram with caption/evidence IDs.
- [ ] **Cover-specific gate:** page 1 contains the approved real subject/context photograph
  required by the blueprint. The original source, identity/context match, permission and
  asset hash resolve; the final render shows a useful, readable crop. A website screenshot,
  wrong-person/unknown-rights portrait or decorative QR fails this gate. If a permitted photo
  is unavailable, the partial draft stays HOLD for full acceptance.
- [ ] The reviewer evaluates the final pages against the declared image-led visual brief,
  not only a visual-element count or a readability formula. Repetitive two-column memos,
  unreadable source thumbnails, decorative diagrams and generic action cards fail. Record
  page-specific reasons, corrections and the reviewed PDF/render hashes.
- [ ] No clipped text, overflow, accidental blank page, tiny unreadable type, broken glyph,
  low-resolution hero, obscured face, or chart legend mismatch appears.
- [ ] Required fonts are embedded, hyperlinks are present, no page is empty/near-empty, and
  repeated-text or overflow checks identify no accidental duplication.
- [ ] Color contrast, reading order, table headers, link labels, page numbers, and status
  distinctions remain understandable without color alone.
- [ ] No placeholder copy, generic stock proof, invented portrait, invented quote, or fabricated
  chart value appears.
- [ ] The file name, title, subject, research cutoff, version, and confidentiality label agree.

## 5. Links, QR, and installability

- [ ] All eight routed skills are present in the named account/runtime at the recorded
  marketplace version. If not, the artifact says PARTIAL, missing lanes are UNKNOWN/HOLD,
  and no complete-audit claim is made. A topical-bundle install alone is not a pass.
- [ ] Every external and `sameAs` link was requested anonymously. Record HTTP status, redirect
  chain, final URL, title/entity match, and check time; authentication-block responses are
  labelled rather than guessed.
- [ ] The QR on the mapped agent-install page decodes from the rendered PDF—not only the source—to exactly
  `https://localservicespotlight.com/install/`.
- [ ] Neither `/skills/`, a legacy ZIP page, nor a model-specific local path is presented as
  the install rail.
- [ ] The full printed HTTPS link appears beside the QR and resolves anonymously to the intended
  installation guide without a 404 or cross-entity mismatch.
- [ ] The anonymous install guide names or links to
  `https://github.com/dennisyu/local-service-spotlight-skills`, the
  `lss-everything` bundle, and the current `.claude-plugin/marketplace.json`. Follow the
  actual manifest link, resolve its commit, inspect the bundle membership and record its
  version/count. A guide may deliberately avoid duplicating hard-coded numbers. A stale
  printed claim, stale/wrong linked manifest or wrong bundle fails; HTTP 200 alone cannot pass.
- [ ] The agent diagram names the eight routed skills exactly and describes input, output,
  human gate, and handoff for each.
- [ ] The receipt says only AVAILABLE, INSTALLED, ENABLED, TESTED, SCHEDULED, or OBSERVED when
  that exact state has evidence for a named account/runtime and version.
- [ ] **Conditional kit gate:** applicability comes from the engagement. When a bespoke kit
  is promised, open the exact package and check START-HERE, subject facts/UNKNOWNs, runnable
  instructions for every promised skill, first real task, worked output example, versioned
  contents manifest, permission gates and receipt forms. Include subject-specific inputs,
  evidence IDs, outputs, cadence and ordered handoffs. A hub with a missing starter file or
  promised skill fails. Private facts remain within the authorized audience.
- [ ] Decode the separate kit QR from the final PDF; compare its printed URL and subject,
  test the intended recipient's access, download/open the contents, and match the final kit
  hash. A working generic installer, login interstitial, owner-only share or another client's
  package fails. Unperformed recipient checks stay UNTESTED/HOLD. A valid ZIP proves prepared
  content; it cannot establish installed, enabled, tested or running agents.

## 6. Action plan and business impact

- [ ] Every 7/30/60/90-day item has action ID, evidence IDs, owning function, routed skill,
  dependency, exact destination, due date, human gate, acceptance test, and current state.
- [ ] No action is merely “post more,” “build awareness,” “improve SEO,” or another activity
  without an outcome and observable test.
- [ ] The plan uses real source material through Produce → Process → Post → Promote.
- [ ] Dollar-a-Day items begin with proven organic evidence and are STAGED unless the exact
  account, amount, dates, audience, creative, metric, and human approval are recorded.
- [ ] Company/partner recommendations name mutual customer value, each side’s contribution,
  owner, risk, success metric, and consent boundary.
- [ ] Measurement follows the chain from published asset to qualified visit/lead/call to sale or
  another agreed business outcome; content volume is not the headline result.

## 7. Authority and state closeout

- [ ] Outside-in and credentialed findings are separate, with access scope and capture date.
- [ ] Research/drafting authority was not treated as approval to send, publish, spend, install,
  grant access, edit profiles, or use relationships.
- [ ] The receipt separately records RESEARCHED, DRAFTED, GENERATED, RENDERED, REVIEWED,
  STAGED, APPROVED, SENT/PUBLISHED, DELIVERED, RECEIVED, INSTALLED, ENABLED, TESTED,
  SCHEDULED, and OBSERVED as applicable.
- [ ] A fresh-context reviewer tried to refute identity, strongest claims, arithmetic, top
  connections, QR decoding, and visual integrity. Record the reviewer, time, failures, and
  corrections.
- [ ] The final handoff names remaining UNKNOWNs, who can resolve them, and the exact next
  evidence or decision required.

## Receipt template

Use [acceptance-manifest.template.json](acceptance-manifest.template.json) as the machine
companion to this receipt in the existing private job directory. Do not commit client manifests,
captures, access links or packages here. From a repository checkout run:

```bash
python3 scripts/personal_brand_acceptance.py /path/to/private-job/acceptance.json
```

Install the pinned PDF parser from `scripts/requirements-personal-brand-qa.txt` if unavailable.
The checker performs no network access, QR decoding or installations; it validates the saved
decoder/access receipts against the files. Exit 0 means mechanical PASS and **REVIEW_REQUIRED**,
never undifferentiated acceptance PASS or A+. Exit 1 is HOLD; exit 2 is input/setup failure.
Missing, failed or untested required checks block full acceptance. N/A needs a brief-based
reason and cannot waive the invariant cover or a promised kit. Research coverage, report
acceptance, delivery, recipient receipt and agent lifecycle remain separate.

The template is deliberately incomplete. Expand its arrays to every source, atomic claim,
page, visual and action; use private locators rather than committing the filled template.
`guide_hashes` are SHA256 of the six pinned guide files. Each `{path, sha256}` pair names an
actual companion file relative to the job directory. Companion receipt JSON shapes:

Copy shapes from [synthetic-receipts.template.json](synthetic-receipts.template.json); its
UNTESTED/UNKNOWN placeholders cannot pass. Public URL normalization collapses tracking and
fragments while retaining meaningful query parameters. For evidenced mirrors/republications,
use `duplicate_of` (source ID) and `dedupe_basis`; dangling/cyclic mappings fail. The reviewer
must verify that grouping. A photo's `original_source` is its captured source ID.

- Decoder: `pdf_sha256`, `crop_sha256`, `decoded_value`, `decoder`, `checked_at`.
- Install check: `guide_url`, `status`, `access`, `checked_at`, `repository`, `bundle`,
  `manifest_commit`, `linked_manifest_verified`, `guide_capture`, `manifest_capture`,
  `manifest_url`, `resolved_manifest_url`, `manifest_version`, `master_skill_count`. The two
  captures use `{path, sha256}`. Retain the actual guide link and the resolved commit URL;
  the captured manifest establishes version and bundle membership/count without requiring
  duplicated numbers in the guide.
- Pinned engagement brief JSON: `subject_id`, `kit_required` (boolean), `promised_skills`
  and `source_target` (integer distinct URL target or null when no quota was agreed).
- Kit contents QA projection: `kit.contents_manifest` points to a private JSON file with
  `subject_id`, `version`, `source_revision`, `skills`
  and `files` rows (`path`, `role`, `sha256`). Roles are `start_here`, `subject_facts`,
  `source_map`, `instructions`, `first_task`, `output_example`, `permission_gates`,
  `receipt_template`. Each skill mapping has `id`, `canonical_route`, `instruction_path`,
  `output_example_path`, `input`, `output`, `cadence`, `human_gate`, `handoff`, `receipt`.
  Bespoke IDs may differ from canonical routes; both referenced files must actually exist
  with the correct hash/role in the package. `delivered_manifest` names the archive's actual
  versioned manifest (`path`, `sha256`, `version_path` array of JSON keys). Its version must
  match the QA projection. The external projection alone cannot replace a recipient's
  manifest. An existing kit may keep its own schema/filename; create this QA projection
  privately without renaming the delivered files or claiming new package guarantees.
- Kit access: `status`, `access` (`anonymous` or `authorized_recipient`), `subject_id`,
  `final_url`, `downloaded_sha256`, `contents_opened`, `checked_at`.
- Editorial review: `pdf_sha256`, `kit_sha256` when applicable, `input_binding_sha256`, `reviewer_context`, `gates`
  and `pages`. Each gate has `status` and a source-based `basis`; required gates are
  `source_truth`, `claim_inventory_complete`, `visual_brief`, `normal_size_readability`,
  `strategy`, `privacy`, `cover_identity_provenance`, and conditional `bespoke_kit`.
  Each physical page key (`"1"`–`"20"`) records `render_sha256`, `status`, `basis`.
  Before review, run `python3 scripts/personal_brand_acceptance.py acceptance.json --binding-only`
  and record that value as `input_binding_sha256`: SHA256 of canonical sorted compact UTF-8 JSON excluding only `editorial_review`
  and `_instructions`. Any source, asset, permission, brief, QR/access receipt, action,
  page metadata or kit mapping change requires a new review of the affected dependencies.
- Lifecycle: `state`, `runtime`, `source_revision`, `event_id`, `checked_at`, `kind`.
  Kinds are `merged_source`, `account_inventory`, `account_setting`, `fresh_task_output`,
  `scheduler_definition`, `scheduler_firing` for the six existing lifecycle states.

Use PASS only for a performed check with its actual evidence. The review basis must state
what was inspected and why it satisfies the promise; synthetic fixture declarations are
never receipts for a real audit. The checker binds declarations but cannot authenticate
their author, prove a photo depicts the subject, establish rights, or prove the live URL was
tested. Those remain fresh-context review duties. Source rows in this machine projection
are inspected UTF-8 captures supporting enumerated PDF claims; private-record locators
require `data_classification: PRIVATE-AUTHORIZED` and are counted separately in
`source_counts.private_record_locators`, never padded into public URL totals. Other source
formats and specialist rubric/graph receipts remain in the existing ledger and are checked
separately. This projection does not replace the entire acceptance suite.

```text
Subject:
Audit version / research cutoff:
Pinned source revision and guide/rubric hashes:
Engagement brief / image-led visual brief:
Evidence ledger path or URL:
Rendered PDF path or URL:
Action register path or URL:
PDF parser / page count:
Rendered-page montage:
QR decoded value:
Kit promised / applicability basis:
Kit version / package path / final hash / actual contents:
Kit QR decoded value / printed URL / recipient access / actual download hash:
Install URL anonymous status / final URL / checked at:
Linked marketplace manifest commit / version / bundle membership / count:
Distinct supporting locators / URL count / underlying records / citation occurrences:
Declared research target / unit / brief basis / coverage state:
Outside-in coverage:
Credentialed coverage:
LSS Knowledge Graph Explorer queries / captured at:
Graph object status (RESOLVED / AMBIGUOUS / NO_SAFE_OBJECT_RETURNED / UNKNOWN) / separate KGMID:
Normal Google panel status / query / date / locale / location / personalization:
Owner claim status / owner-dashboard or Google claim-receipt proof locator / UNKNOWN:
Ranked public-association entity graph outcomes:
Independent reviewer / context / reviewed at:
Tests passed:
Tests failed:
Tests untested and why:
Corrections made after review:
Final PDF hash / reviewed render hashes / kit hash:
Mechanical result / editorial review result / required failures or untested gates:
Work-product state:
Delivery/publication state:
Agent lifecycle state and named account/version:
Remaining UNKNOWNs / owner / next evidence:
```

The receipt proves only the states it names. A passing local suite does not prove delivery,
publication, installation, enablement, or a scheduled run.
