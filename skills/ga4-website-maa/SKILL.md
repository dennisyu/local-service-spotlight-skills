---
name: ga4-website-maa
description: "Produce the investigative Website / GA4 report for ANY small business using the Google Analytics MCP. A business-model router adapts the analysis to the client (local-service lead-gen, e-commerce, audience/list-building, membership/course, or donation/nonprofit) so it works for any vertical, never rejecting a business as \"out of scope.\" Establishes data trust first (pre-flight, Data Clarity), reconstructs and classifies the business's primary conversion, answers the owner questions (what's converting, which channels/pages/products drive it, momentum), and outputs the client-facing report per the Local Service Spotlight report format. Trigger on: \"GA4 report/MAA for [client]\", \"website MAA\", \"run the GA4 agent\", \"analyze [client]'s GA4\", \"where are my leads/sales/signups coming from\", weekly GA4 reporting runs, or any request to analyze a GA4 property for a small business. GA4 only — organic search terms belong to the GSC agent, paid performance to the Google Ads agent."
author: Daniel Goodrich — Local Service Spotlight
references:
  - skills/weekly-brand-maa/SKILL.md
  - skills/measurement-analytics/references/source-contracts.md
---

# GA4 Website Report (any small business)

## Executive Summary

This skill produces the weekly website report that goes to a business owner. It reads the Google Analytics account for that business, works out what actually counts as a result there, whether that is a lead, a sale, a signup, a membership or a donation, and then answers the three questions an owner asks: what is bringing people in, what changed since last time, and what to do about it. It adapts to any kind of small business rather than assuming one industry. The owner gets plain language and real numbers, and the technical checks that make those numbers trustworthy stay behind the scenes.

## Business-model router — adapt, never reject (do this FIRST)

This skill works for **any small business**. There is no "out of scope." Nothing is ever rejected. A business is never told the analysis "doesn't apply" — the worst honest outcome is "we need to confirm what counts as a conversion for you," never a refusal. Before Phase 1, route the client to its **business model** and let that choice drive what a conversion is, which dimensional lens the report uses, and which local-only modules run. The data-trust, Data Clarity, swing-decomposition, and report machinery are identical across every model; only the conversion definition and the lens change.

**Detect the model** from `industry_category` (`get_property_details`, always read it), the event inventory (Q1), and the page paths (Q5). Full detection + taxonomy in `references/business-models.md`. The five models:

| Model | Primary conversion | Report calls it | Primary lens (replaces cities) | Local modules (cities/GBP/spam-screen)? |
|---|---|---|---|---|
| **Lead-gen** (local service, B2B, high-ticket coaching) | inquiry: call, quote/contact form, booking, qualified chat | "leads" | channels → pages → **cities** | **Yes** if bounded service area |
| **E-commerce** (DTC, retail, catalog) | `purchase` (with revenue) | "sales / orders" | channels → **products** → checkout funnel | No (unless local pickup/storefront) |
| **Audience / list** (authors, creators, personal brands, newsletters) | signup / subscribe / registration | "subscribers / signups" | channels → **top content** → signup sources | No |
| **Membership / course** (memberships, courses, SaaS trials) | enrollment / trial / subscription start | "members / enrollments" | channels → **offer pages** → enrollment funnel | No |
| **Donation / advocacy** (nonprofits) | donation, volunteer, petition | "donations / actions" | channels → **campaigns/appeals** → top content | No |

**Rules of the router:**
1. **Always run `get_property_details` for `industry_category`** (SHOPPING → e-commerce; BUSINESS_AND_INDUSTRIAL / media / publishing → often audience or lead-gen). It is decisive on low-data properties where event names haven't accumulated yet.
2. **Pick the ONE primary model** that matches how the business makes money, and note any **secondary** (a local plumber with a newsletter is lead-gen primary, list secondary; an author who also sells a course is audience primary, membership secondary). The primary conversion is the headline; the secondary is a separate line, never mixed in.
3. **Local modules are conditional, not default.** Cities W&O, the service-area spam-screen, and the GBP panel run **only** when the business is genuinely local (bounded service area). For a national or online business, drop them silently and use the model's primary lens instead. Dropping the local lens is normal routing, NOT an "out of scope" finding, and is never mentioned to the client as a limitation.
4. **If you genuinely cannot tell the model** (first touch, ambiguous events): pick the best-supported model, mark the conversion definition PROPOSED, proceed with a full report, and put "confirm what counts as a conversion for you" in the actions. Never stop, never reject.
5. **A no-data / dead-tag property is a DATA problem, not a model problem** — it still routes to Phase 0's escalation shape. Model routing and the data-escalation check are independent; a dormant e-commerce property gets both the model (e-commerce) and the tracking-gap memo.

## Contract

Same evidence → same flags, same structure. The fixed procedure collapses evidence variance; interpretation variance is bounded by the QA gate and human review — never promise beyond that. This skill is deterministic where determinism is possible and reserves judgment for interpretation. You MUST:

1. Run the **fixed sequence** below in order. Never skip a phase, never reorder.
2. Pull the **Standard Pull** queries exactly as written in `references/query-recipes.md`. Do not improvise dimensions or date ranges.
3. Trigger expansions only by the **decision tables** — numeric conditions, not vibes.
4. Consult `references/integration-behaviors.md` BEFORE diagnosing any tool/integration behavior (call tracking, booking tools, form events, source buckets). This is where confident-wrong errors live.
5. Pass the **QA gate** (`references/grading-rubric.md`) before delivering. A report that fails a criterion gets revised once, then delivered with the failure flagged.
6. Run the **fold-in pulls (Q9–Q11 in `references/query-recipes.md`) in-line** whenever their triggers fire — never defer them to a human second pass. This week's Opaque reports each needed a manual follow-up (subdomain sales, event-onset date, out-of-area behavior); folding them in removes that pass.

Hard boundary, stated internally always: GA4 measures the **online conversion action** (a form submit, a call click, a `purchase` event, a signup), not the fulfilled outcome (a booked job, a shipped order, settled revenue net of refunds, a retained member). Report the online conversion and say so; never imply GA4 proves revenue collected or jobs completed. Read-only: every tracking fix is written as an action for a human.

## Run modes — decide this FIRST (before Phase 0)

This skill runs in one of two modes. Decide which before anything else; they differ in who reads the output and what gate protects it.

| | **First-Run (team-operated, gated)** | **Recurring Re-Run (owner-facing, guarded)** |
|---|---|---|
| **When** | First touch for a client; OR any run flagged for team review by a tripwire last time; OR the operator forces it. | An established client with a **locked-config** (`references/locked-config.md`) and a clean prior run — the owner (or a schedule) triggers the weekly pulse. |
| **Judgment work** | Full procedure. Proposes/locks the lead classification, service-area, known-integration fixes. Seeds/updates the locked-config. | Reuses the locked-config. Does **not** re-litigate classification or service area. |
| **Gate before delivery** | **Human review, always.** Draft only; a person signs off before the owner sees it. | **Tripwire gate (`references/tripwires.md`), then deliver.** A clean week goes to the owner directly. A week that trips any material-change tripwire is **held for the team** — it does not go to the owner unreviewed. |
| **Voice** | Full MAA voice. | Recurring-run voice (`references/report-format.md` § Recurring-run voice): report fix-progress, raise only genuinely new asks, never fabricate ✅ team commitments for a week the team isn't acting. |

**The rule that makes Recurring safe:** an owner-triggered run has no human in the loop that week, so it must self-detect when it is out of its depth and route back to the team instead of confidently shipping. That detection is the tripwire gate in Phase 0.5 and Phase 7. Never deliver an owner-facing report that tripped a tripwire without team review.

If there is **no locked-config**, you cannot be in Recurring mode — run First-Run and produce one. The human process around these modes — owner GA4 connection pre-flight, First-Run validation, and flipping a client to owner-facing Recurring — is in `references/team-sop.md`.

## Phase 0 — Narrative + pre-flight (never skip)

1. **Read the client's config first.** In **Recurring** mode read `{client_vault}/{client}/locked-config-ga4.md` (`references/locked-config.md`), where `{client_vault}` is the client folder your team keeps configs in — it is the source of truth for property ID/known ghosts, the locked lead classification, service-area + out-of-area intent, known integrations + fix status, and the baselines the tripwire gate checks. In **First-Run** mode also read the Narrative (`{client_vault}/{client}/Narrative-GA4.md`, or a compiled metric spec if your team keeps one) for open questions and history, and seed/refresh the locked-config as part of writeback. Do not re-litigate settled facts.
   - No Narrative → this is a **first touch**: after the event inventory (Q1), propose a lead classification, ask the human to confirm, and seed the Narrative before reporting.
   - **Unattended run (no human reachable):** propose the classification, mark every dependent number "PROPOSED — needs confirmation" in the internal log, proceed, and put the confirmation ask in the report's actions. Never silently lock a classification the human hasn't seen.
2. **Liveness check** (query P1): sessions by date, last 28 days.

| Result | Verdict | Action |
|---|---|---|
| ≥ 10 sessions/week sustained | Live | Proceed |
| Near-zero or trailing off to zero | Abandoned ghost | Run P2 (account summaries), look for a same-brand sibling property with live data. Found → switch to it, note both IDs in the Narrative. |
| **Two or more live same-brand properties** (e.g. regional US/UK) | Not a ghost case | **Ask the human which property to use.** Unattended: pick the larger/most relevant, mark the choice "UNCONFIRMED" in log + report ask. (Property-selection ambiguity, not a business-model question — the model router still runs on the chosen property.) |
| No live same-brand property anywhere accessible | Not implemented / access gap | **Stop.** Escalate — and distinguish the two cases in the escalation: **(a) GA4 exists but wasn't shared with us** → ask for user access; **(b) GA4 was never implemented** → propose setup as step one. If you can't tell, ask which it is. Do NOT fabricate an analysis. Automatic F if you report "business is dead" without this check. |

**Pre-flight edge cases (name them, don't force the table):**
- **Configured but never fired (dead tag — a THIRD state, distinct from "not shared" and "never implemented").** The property exists AND has setup artifacts (a Google Ads link, custom dimensions, a stream) proving implementation happened, yet has no usable current data. Two shapes: (a) ~zero sessions across its entire lifetime and no lead event ever; (b) **fired for real at launch, then went dark** (a burst of sessions when created, then months-to-years of near-silence — Summit Bands: 407 sessions in a 2-month 2023 launch window, then ~zero for 2.5 years). Both are the same verdict. This is not an access gap (queries return valid *empty* results, not permission errors) and not "never implemented" (setup clearly occurred). Verdict: the live tag isn't firing (broken deploy, consent-tool blocking, migration, wrong stream). **Escalate as a fixable tracking gap, not a business verdict** — do a lifetime-sessions check to confirm, then produce the escalation report shape below. Do NOT fabricate an analysis; do NOT say "the business is dead." (Ironwood Fence: property + Ads link + 2 custom dims, but 2 lifetime sessions and 0 lead events ever.)
- **When Phase 0 stops the run (any no-data escalation), use the escalation report shape**, not the 5-section numbers report: a short plain-English diagnostic memo — what we checked, what we found (no usable data + the setup artifacts that prove it's a tracking gap), what it means (fixable, not a traffic verdict), and the one next step (get the tag firing / confirm the right property). Phases 1–7 and their lint checks are N/A for a zero-data run — note them N/A, don't force them. Seed the locked-config as `mode_ready: escalated` with empty lead_events/baselines and the open questions (see `locked-config.md`).
- **Adjacent-brand or barely-live sibling.** A same-account property with a *different brand name* and only a single-day/near-zero traffic blip (not sustained) is neither a same-brand sibling nor the target — pick the sustained-live property and note the other as an inactive/adjacent sub-brand. (Brightline Painting: "The Coat Crew" had one 93-session day, else zero → not the target.)
- **Main-site + funnel-subdomain split.** Two live same-brand properties that are a primary site + a funnel/consultation subdomain are NOT the "two regional peers" case — use the primary, flag the subdomain for the team to scope before enabling Recurring. (Wexford Legal: `consultation.wexfordlegal.example`.) **But when the subdomain/sibling plausibly carries the primary conversion** (an e-commerce checkout or auction/booking subdomain heavier than the main site, or an off-domain checkout), run **Q9** in-line to pull its event inventory + revenue *before* deferring; only flag for the team if Q9 can't resolve where conversions live. (Cascade Trading Post: the auction subdomain `100200303` carries the transactions the main-site `$0` hides.)
- **Timezone/geo mismatch.** From `get_property_details`, if the property timezone doesn't match the client's actual region (e.g. America/Chicago for an Eastern-time firm), note it — it skews any day-of-week/hour analysis. Don't silently trust the TZ.

## Phase 1 — Standard Pull (fixed, every run)

Run queries **Q1–Q8** from `references/query-recipes.md` exactly. Both date windows: current = `28daysAgo → yesterday`, prior = `56daysAgo → 29daysAgo`. Never include today (incomplete trailing period).

Q1 event inventory · Q2 channel mix (both periods) · Q3 source/medium detail · Q4 lead events × source · Q5 landing pages + lead pages · Q6 geography of leads · Q7 13-week trend · Q8 new-vs-returning.

Record every number in a working table before interpreting anything.

## Phase 2 — Conversion reconstruction and classification (model-aware)

Never trust the key-event flag alone. What counts as the **primary conversion depends on the routed model** (see `references/business-models.md`). From Q1:

1. **Identify candidate conversion events yourself** using the pattern tables in `references/query-recipes.md` (§ Conversion-event patterns, which has one sub-table per model). A newsletter signup is *list-building/secondary* for a plumber but the *primary conversion* for an author — the model decides the tier, not the event name in isolation.
2. **Classify each event into exactly one tier, relative to the routed model:**

| Tier | What it is | Reported as |
|---|---|---|
| **Primary conversion** | the model's money action: lead-gen → call/quote-form/booking; e-commerce → `purchase`; audience → signup/subscribe; membership → enrollment/trial; donation → donate/volunteer | THE headline number (named per model: leads / sales / subscribers / members / donations) |
| **Secondary conversion** | a real but non-primary action (a plumber's newsletter, an author's low-ticket tripwire, an e-com email capture) | separate line, never mixed into the headline |
| **Micro** | `form_start`, `scroll`, `video_*`, `page_view`, `session_start`, `user_engagement`, `first_visit`, engagement timers, page-view-duplicate events | never conversions, never reported |

   Locked definition in the config wins over the pattern table. An existing-customer or repeat action (`repeat_phone_call`, a returning-member login) is not a *new* conversion. **Name-vs-flag conflicts** (event named like a conversion but not flagged as a key event, or vice versa): the pattern table classifies, the GA4 flag is a tiebreaker only; note every conflict rather than silently picking.
3. **`form_submit` is a candidate, not a lock**: GA4's auto-captured `form_submit` can fire on invalid/incomplete submissions and can't distinguish which form fired. On first touch, verify against a known count (thank-you page views, CRM, or the client's own tally) before locking it as a case lead; until verified, mark it proposed.
4. **Reconcile both directions**: reconstructed case-leads vs GA4's key-event count. Gap > 1.5× in either direction (under-count or dilution) = a finding with a cause. State whether the gap is **explained** (a visible config cause you can point to, e.g. unregistered key events) or **unexplained** (no visible cause) — only unexplained gaps >2× push toward Opaque.
   - **Ordering matters and is fixed: SCREEN FIRST, then reconcile.** Reconcile the **post-spam-screen real case-lead count** against GA4's flagged key events — not the raw pre-screen reconstruction. (Reconcile-then-screen vs screen-then-reconcile can change the Opaque grade: Brightline Painting pre-screen-vs-flagged = 10.5× but post-screen-vs-flagged = 3.4×.) When the pre- and post-screen numbers differ materially, record all three internally (GA4-flagged, raw reconstruction, screened-real) and reconcile on screened-real.
5. **Spam-screen — with the out-of-area intent branch** (Q6): out-of-area leads are NOT automatically spam. Decide per the locked-config `out_of_area_leads` flag:
   - **Business sells beyond the service area** (franchise sales, national coaching, authors, e-com): out-of-area inquiries are plausibly real leads of a *different type*. Reclassify them (e.g. "franchise inquiry") and either keep them in the headline with a note or break them onto their own line — do **not** screen them as spam. (RDR sells franchises; its out-of-state singles are franchise interest, and the Grade-A exemplar keeps them.)
   - **Local-only business, no out-of-area reason** (e.g. a painter): out-of-area case leads are contamination — screen them out of the headline and note. (Brightline Painting: Tehran was the #1 "lead" city.)
   - **Tie-breaker for "is this spam?":** foreign/datacenter city clusters with ~0 engagement and no conversions are junk traffic regardless of business type, and this test applies even to national / no-service-area businesses (it is a general data-quality check, not only a service-area screen). Known hyperscaler/datacenter cities that recur as bot origins: Ashburn VA, Boardman OR, Prineville OR, The Dalles OR, Council Bluffs IA, Des Moines IA, Moses Lake WA, San Jose CA, Singapore, Dublin, Lanzhou, Urumqi. A cluster in these at near-zero engagement is a data-quality note, never leads. On a national business with no city W&O, surface it as a one-line "suspected bot/datacenter traffic" note under "what it means."
   - **Calls vs forms get different screens.** Bot spam floods *forms* (a script POSTs from Tehran); an **on-site click-to-call is genuine on-device engagement** and is low spam-risk. Screen an out-of-area *call* out of the headline only when it's clearly outside the service area AND part of a junk pattern — don't geo-screen real calls as aggressively as forms, or you'll delete real leads. Note the judgment either way.
   - **Out-of-area but normally-engaged → confirm behaviorally (Q11), don't guess.** When an out-of-area cluster engages *normally* (not the ~0-engagement datacenter signature), run **Q11** before deciding. Real-customer pattern (mixed devices, normal duration, service/quote landings, spread across cities) = legitimate leads of a *different type* — flag to the client, don't screen. Single-device / ~0-duration / one-landing / datacenter-concentrated = screen. (Kestrel Air: ~20% out-of-area but engaged normally — Q11 resolves it instead of a manual log-check.)
   If spam is found in the current window, pull Q6 for the prior window too, so the comparison is screened on both sides.
6. **`form_start` special rule**: if `form_start` fires but no `form_submit`/completion event exists, form leads are **untracked** — flag "verify the form submits and that submission is tracked." Never infer form volume from starts. The same click-without-completion logic applies to scheduler/booking links (Calendly-type): a click event is not a booking.
7. **Call event type — on-site click vs. call-tracker (prevents a confident-wrong attribution hunt)**: classify the call event's *type* from the locked-config. An **on-site click-to-call event** (e.g. `call_clicks`, `click_to_call` fired by the site) has a website touchpoint by definition — it is attributed by the session that fired it, so the off-site/`(not set)` touchpoint apparatus and the CallRail custom-dimension recovery do **NOT** apply, and empty custom dims are irrelevant, not a problem. Only a **call-tracker vendor event** (CallRail/WhatConverts/FirmPilot dynamic-number events) invokes the touchpoint rule and the "segment `(not set)` calls into a GBP/Ads bucket" logic. Never hunt for missing call attribution on an on-site click event.

## Phase 2.6 — Swing decomposition (whenever the headline moves materially — never narrate a swing you haven't decomposed)

A material lead swing (≥ ~20% PoP, and always any swing beyond the ±35% surface threshold) will alarm the owner, so the report MUST explain *what drove it* — and the driver must be **pulled from data, not guessed**. A plausible-but-wrong driver is the failure mode here: a v1 Wexford Legal draft passed every mechanical lint check and still blamed "the giveaway ending" when 76% of the drop was off-website calls the giveaway never drove. Required before writing the "what drove it" sentence:

1. **Comparison integrity first.** Confirm both sides of the comparison are computed on the **same basis** — same classification, same spam-screen, same dilution-separation applied to *both* windows. Never compare a clean current number to a raw or differently-counted prior. Recompute the prior on the current basis if needed and say so. (Wexford Legal 355 was already clean; Target's prior 44 had to be re-screened, not carried over raw at 95.)
2. **Decompose the swing by type × source × touchpoint.** Pull prior-window leads by type (calls/forms/bookings/texts) and by source (Q4 prior window), and split calls into off-site vs web-touch, both windows. Lay prior beside current. Identify the **largest mover** — that, not a narrative hunch, is the driver.
3. **Verify the named driver IS the largest mover.** If your explanation names a bucket that isn't the biggest contributor to the change, it's wrong — fix it. (Blaming paid/giveaway for a drop that lives in off-site GBP calls is the canonical error.)
4. **Respect the off-site attribution limit.** When the dominant lead type carries no source (off-site calls in `(not set)`), GA4 cannot tell you *why* those moved — emit a verification action ("pull the call-tracker + GBP call logs for the two months") instead of asserting a cause. Say what you can prove and route the rest to a check.

This runs in both modes. In Recurring mode it is what turns a fired "large swing" surface-item into an honest owner explanation rather than a scary bare number.

## Phase 3 — Data Clarity (decision table, not judgment)

Evaluate every row. Each triggered condition is a flag; flags roll into the grade.

| # | Check | Data | Condition | Flag |
|---|---|---|---|---|
| C1 | Direct share | Q2 | 20–25% watch · >25% elevated · >40% alarm (industry consensus: healthy 5–20%) | Attribution fog |
| C2 | Direct surge | Q2+Q8 | Direct sessions +50% PoP AND engagement rate falling AND ≥90% new users | Bot/untagged flood (verify via Q8, not assumption) |
| C3 | Unassigned share | Q2 | >10% of sessions | **Decompose the bucket before diagnosing — it holds two unrelated things at once:** (a) mistagged traffic (non-standard UTM medium → C4, a "fix the tags" defect) and (b) off-site conversions with no source (off-touchpoint calls in `(not set)` → C5, which is CORRECT, not broken). Split Unassigned into these before reporting; never treat the whole bucket as one problem or double-count the calls as mistagged. (Wexford Legal: 532 mistagged the regional-TV buy CTV sessions + 137 correct off-site calls in the same Unassigned group.) |
| C4 | Non-standard UTM medium | Q3 | custom `medium` that maps to no channel (e.g. `Live Sports`) | UTM fix action |
| C5 | Attribution coverage of case leads | Q4 | apply the **calls touchpoint rule** (integration-behaviors § calls) BEFORE flagging. Off-site calls in `(not set)` are CORRECT — segment into their own bucket (GBP + Ads), don't call them broken. Unattributed **forms** = real tracking problem. Web-touch calls unattributed = real problem. | Possibly invalidates channel analysis |
| C6 | Clean vs raw coverage | Q4 | clean = paid + organic + real referral/social only. Direct = absence of source; booking-tool referral = wrong source. Never report "X% tracked" by counting Direct. | Report both numbers internally |
| C7 | Conversion dilution | Q1 | one non-case event >50% of key events | Separate from case leads; **headline it if >70% in EITHER comparison window, OR if it is the single largest counted conversion.** (Wexford Legal: giveaway 71.3% prior / 61.6% current — the >70%-current-only reading would wrongly demote the account's defining data-trust story in the very window that made it the dilution anchor.) |
| C7b | Tagged junk flood | Q2+Q3+Q8 | a NON-Direct labeled channel (Paid Social, Referral, a specific source) sends a large session block with engagement <½ site norm and ≈0 leads, verified new/low-quality via Q8 | Junk-quality traffic on a tagged channel — screen from the "traffic up" read, flag "under review," never celebrate. (C2 is Direct-only and misses these: Brightline Painting's 526-session Paid Social flood, 6.8% engagement, 0 leads.) |
| C8 | Booking-tool / self referral | Q3+Q4 | booking/checkout/CRM domain (`app.*`, `*.bookflow.io`, `force.com`, `infusionsoft`…) carries ≥10% of **leads** | Source overwrite — headline finding + referral-exclusion action (RDR: 27%) |
| C9 | Capture gaps | Q5 | `(not set)` landing pages, `(data not available)`, sampling | Note; elevate if material |

**Grade (internal only, never shown to client):**
- 🔴 **Opaque** — C5 invalidates channel analysis (unexplained after the touchpoint rule), or C7 >70%, or C8 ≥25% of leads, or reconciliation gap >2× unexplained. → Report becomes clarity-first: leads you CAN trust + the fix plan.
- 🟡 **Hazy** — any elevated flag, but case-lead count is trustworthy after classification. → Answer with caveats, lead with the fix.
- 🟢 **Clear** — no elevated flags. → Answer straight.

**Near-threshold rule:** any check landing within 20% of its trigger (either side) is a **watch item** — reported softly internally and carried in the Narrative, never silently passed or silently escalated. (Westerville: expected leads 1.6 vs guard 2 → watch, not omit.)

## Phase 3.5 — Tripwire gate (Recurring mode only)

After Data Clarity, before writing an owner-facing report, evaluate `references/tripwires.md` against the locked-config. Any tripwire that fires **routes this week to the team**: finish the analysis, write the internal draft, and emit a one-line banner — "This week needs Local Service Spotlight review before it reaches the owner: <reason(s)>" — instead of delivering. A material business swing (large PoP lead change) is **surfaced prominently in the owner report**, not escalated; escalation is reserved for **data-trust breaks** (new lead event, property switch/ghost, Opaque grade, reconciliation break, a newly-appearing spam/contamination cluster, or a previously-applied fix that regressed). First-Run mode skips this gate — its human-review gate already covers it.

## Phase 4 — Conditional expansions (rule-triggered only)

| Trigger | Expansion |
|---|---|
| Case leads include calls AND any call attribution question | `get_custom_dimensions_and_metrics` → if CallRail custom dims registered (`customEvent:source`/`customEvent:medium`), query them for call attribution (not retroactive). Vendor mechanics are CallRail-specific — other tools: "may indicate", verify per tool. |
| GBP link status unknown or owner-question D asked | Check UTM-tagged GBP traffic in Q3; native GBP data needs the link — if absent, that IS the finding (a tracking action, not a chart). |
| Paid traffic present | `list_google_ads_links`; report paid lead rate from Q4. Depth belongs to the Ads agent. |
| Anomaly in Q7 trend | Spikes suspect-until-verified. Key event → zero = broken tag until proven otherwise. Check `list_property_annotations` for deploys/changes. |
| Candidate conversion/key event appears **0→N** between windows (or jumps >2× unexplained) | Run **Q10** (daily onset trend) to date the onset — a clean step on a date = new instrumentation (good); erratic / pageview-tracking = possible double-fire (data-quality watch). |
| Routed model has a funnel (e-commerce checkout, membership enrollment) | Run `run_funnel_report` / `run_conversions_report` for the step-by-step drop-off — don't stop at event-count deltas; this is where conversions read Opaque. |
| Owner-question C (organic search terms) | **Refuse and route**: the GA4 Data API has no query dimension (rejects `organicGoogleSearchQuery`). GSC agent's job. Never attempt. |

## Phase 5 — Verification principle (every interpretive claim)

1. State current state as fact only when the data shows it.
2. Hypotheses are "may indicate…", never conclusions.
3. Verify in-data when possible (e.g. C2 requires the Q8 check).
4. Not provable from GA4 → emit a verification action instead of a claim.

## Phase 6 — The client report

Structure and voice per `references/report-format.md`; match `references/exemplar-report.md` (Grade A). Non-negotiables:

- **Machinery stays internal.** No grades, no "reconciliation", "attribution coverage", "conformance", no thread names. Translate: "🔴 attribution 24%" → "Your phone leads aren't tracking to a source yet, so we can't tell which marketing drives your calls. Here's the fix."
- **Primary conversion first (named per model).** The pulse opens with the model's headline number + mix vs prior period, using the client's own word: leads, sales, subscribers, members, or donations — never the internal word "conversion."
- **Every number gets a comparison + % change.** No baseline → not reported.
- **Data shown as Winners & Opportunities** (see report-format § Winners & Opportunities), in the **model's lens order** (business-models.md): lead-gen (local) → channels → pages → cities; e-commerce → channels → products → checkout funnel; audience → channels → top content → signup sources; membership → channels → offer pages → enrollment funnel; donation → channels → campaigns → top content. Each is a top-5 "what's producing" list paired with a guarded "worth a look" list using the expected-vs-actual line ("enough traffic for ~4 at your normal rate; produced 0"). The 13-week trend of the primary conversion gives momentum context. Cities/GBP appear only for local businesses. Full tables stay internal, never in the client text. Charts derive from the report's own numbers only.
- **Hedge fixes**: a change *should* resolve an issue, never *will*.
- **Grounded prescriptions only.** Every recommended fix, named product/feature, and causal mechanism must come from (a) integration-behaviors.md, (b) your own pulled data, or (c) an explicit "we'll confirm the right approach" hedge. Never invent a product ("Google-provided call tracking" does not exist), never prescribe a real feature for a problem it can't solve (a GBP link does NOT surface data in this report's pipeline), never infer setup status from absence of tagged traffic. Render-time danger signs: "which likely means…", "should give us visibility into…" — if a causal connective bridges a gap the reference doesn't cover, cut it or hedge it.
- **Number integrity.** Every client-facing number is either a pulled number or clearly framed as our reconstruction — never present your own derived/reclassified count as something "GA4 shows" (Northside Fitness: told the client GA4 shows 44 when the dashboard shows 64). Tables must sum to their headline; a known small mismatch gets a footnote, not silence.
- Sections: 1 Business pulse · 2 The numbers, shown (trend, then the model's-lens W&O per business-models.md) · 3 What it means (includes the decomposed driver of any material swing, per Phase 2.6) · 4 **What to do next** — 2–3 decisive next-step *recommendations*, not a recap of internal work-in-progress (✅ our-side commitment vs named client-side ask; a ✅ is a forward step we're committing to, never completed-work) · 5 Start here (one move, not a restatement of action #1).

## Phase 7 — QA gate, then writeback

The QA gate has three layers because self-grading alone is unreliable (self-preference bias is documented and was observed in testing: self-grades ran A- while external grades ran B to C-).

1. **Mechanical lint (deterministic — do these as literal checks, not judgment):**
   - Grep the client text for banned vocabulary: Clear/Hazy/Opaque, reconciliation, attribution, coverage, conformance, key events, case leads, touchpoint, C-flag references, thread names. Zero hits required.
   - Every client-facing number has a comparison (see report-format § Comparison scope for the pages/cities carve-out); word count within ~1.5× of the exemplar (~530 words, prose only — markdown table syntax doesn't count toward the limit). **Carve-out:** Phase-0 escalation (no-data/dead-tag) reports may run ~150 words over, since honestly explaining the tracking gap costs words the standard report doesn't spend.
   - **Sums-to-headline (literal check — tables AND prose lists).** Add the rows of every client table — or the items of any prose/list lead breakdown ("34 calls, 14 bookings, 1 form") — and confirm it equals the headline it sits under, or carry an explicit "other / minor sources — N" line so it visibly sums. A silent residual fails. (RDR miss: leads-by-source table showed 17+13+11+6=47 under a 49 headline — the 2 minor-source leads must appear.)
   - **Numeric-band containment (literal check).** Any stated range/band ("leads held in a 12–25/week band") must contain **every** in-window value from the source query; recompute min/max from Q7 and correct the band, and never cite a week as evidence of a floor/ceiling it violates. (RDR miss: "12–25" band while W19=8 and W28=9.)
   - **Row-level count adjectives (literal check).** Any word asserting a per-row count — "singles," "one each," "a handful" — is verified against the actual Q6/Q5 counts. (RDR miss: called Blacklick/Lewis Center/Canal Winchester/Grandview "singles" when each had 2 leads.)
   - **Loss/gain attribution check.** If the report says where a change concentrated ("most of the lost leads sit in X"), the named bucket must be the largest mover in the source decomposition. (RDR miss: named paid −12 as "most," but the booking-tool/referral bucket dropped −15.)
   - Action block: every bullet is future-tense work; no ✅ on completed diagnostics.
   - **AI-writing-tell check (literal).** Count em-dashes (`—`) in the client text; rewrite each as a period, comma, colon, or parentheses, leaving at most one. Flag other tells (the "it's not just X, it's Y" construction, "fast-paced world," reflexive "leverage/utilize/delve," three-adjective triads). A report that reads as machine-written fails the voice bar even if every number is right.
   - **Recurring mode:** confirm the Phase 3.5 tripwire gate ran; if any tripwire fired, the output carries the team-review banner and is NOT formatted as owner-delivered.
2. **Self-grade** against all 8 criteria + the prescription audit in `references/grading-rubric.md` (criterion 9). Any fail → revise once. Check the four auto-penalties explicitly (machinery leak, unsupported number, dead-property claim, missing comparison).
3. **External grade when the harness allows it** (subagent or separate session, fresh context, no generation history): give the grader only the report, the data log, and the rubric. Record its grade beside the self-grade; a disagreement is itself a finding. The human review gate stays regardless — it is the final layer, not replaced by any of this.
2. **Writeback** (per Narrative pattern):
   - Report → `02-Clients/{client}/MAAs-GA4/YYYY-MM-DD.md`
   - Narrative: dated Weekly Log entry (leads, findings, actions, start-here, open questions); update Running Themes; update Account Context if setup changed; carry open questions forward. Corrections are noted in place, never deleted.
   - **Locked-config:** append this run to `run_history` (date, mode, headline leads, clarity, escalated?); update `fix_status`/`last_checked` where a fix was verified this run; refresh `baselines` only on a team-reviewed First-Run. If a tripwire fired, set next cycle to First-Run. Locked fields never change on a Recurring run.
   - System-level gap (would change how EVERY client is analyzed, not just this one) → `05-Decisions-Log/YYYY-MM-DD_GA4-{title}.md` (trigger, gap, fix, landed-in) and flag this skill for the change. Client-specific findings go in the Narrative, not the log.
3. **Draft only.** Human reviews before anything posts. Never auto-post.

<!-- shared-rule:agents-draft-humans-send:start -->
## Agents draft; a human sends and publishes

- **An agent may write anything and send nothing.** Email, DMs, social posts, client
  messages, public pages — staged and ready, never dispatched.
- **Stage it so approving is one click**, not one more round of work: the full text, the
  recipient, the subject, and where it will appear.
- This is a security control, not a confidence rating. It holds even when the draft is
  obviously correct, because the failure it prevents is the one nobody predicted.
- It is the boundary on `be-proactive-see-it-through`: act freely on reversible work,
  stop at anything that reaches another person or the public.
<!-- shared-rule:agents-draft-humans-send:end -->

<!-- shared-rule:ask-blocking-questions-up-front:start -->
## Ask every blocking question up front

- **Front-load every question and every missing access into the planning step**, before
  the long work starts. The person who briefed you intends to walk away; a question
  raised at minute ninety costs them the whole ninety minutes.
- **Do not guess to avoid asking.** A guess that turns out wrong is discovered at the end,
  when it is most expensive to undo.
- After the short plain-language context, put an explicit **open questions and
  missing access** block near the start of every plan. If the list is empty, say
  so — that is information too.
- Once the questions are answered, work continuously to the end rather than stopping to
  check in on things you could have decided.
<!-- shared-rule:ask-blocking-questions-up-front:end -->

<!-- shared-rule:assign-work-to-a-function:start -->
## Assign work to a function, not a person

- **Every task is owned by a function** — web, content, analytics, client success — and
  people sit inside functions. People join, leave and go on holiday; the function does not.
- **Escalate to a function too.** "I told Muzamil" is not an escalation if Muzamil is
  away; "escalated to the web function" is.
- A function with exactly one person in it is still a function. Name it that way, so the
  second person changes nothing.
- Work assigned to a named individual and nowhere else is work that silently stops when
  that individual does.
<!-- shared-rule:assign-work-to-a-function:end -->

<!-- shared-rule:basecamp-updates-stay-in-basecamp:start -->
## Basecamp updates stay in Basecamp

- Never use Gmail Reply, Reply All, Forward, Send, or Draft to
  `notifications@app.basecamp.com` or `notifications@3.basecamp.com`. Those
  visible From addresses are notification infrastructure, not destinations.
- Post the update in the exact existing Basecamp thread through an authorized
  Basecamp connector, API, or the Basecamp UI. The company delivery rail is
  Basecamp itself, so do not substitute a per-message
  `*@replies.app.basecamp.com` email token even when one is present.
- Before any Gmail mutation, inspect the resolved To and Cc fields. If either
  contains a generic Basecamp notifications address, stop without creating or
  sending the message.
- Changing the Gmail From identity does not repair this failure. In the
  incident that produced this rule, the connector resolved the visible From
  address as the recipient and discarded Basecamp's unique Reply-To route; the
  result was an `Email Received in Error` bounce and no Basecamp comment.
- A Basecamp update is complete only after readback proves the live thread URL
  or recording ID, the expected author, and a unique phrase from the comment.
  A Gmail SENT item is not proof. If no Basecamp write path exists, report the
  blocker and put the intended update in the run result; do not fall back to
  email.
- Embed this rail directly in every scheduled or cloud task that may touch
  Basecamp. Such runs may not load repository instructions before using an
  already-authorized Gmail tool.
- This rule controls the delivery path; it does not grant permission to post or
  weaken any existing human approval requirement.
<!-- shared-rule:basecamp-updates-stay-in-basecamp:end -->

<!-- shared-rule:be-proactive-see-it-through:start -->
## Be proactive and see it through

- **When you find something broken, fix it.** Do not file it, mention it in passing, or
  wait to be asked. If it is outside what you can fix, escalate it to the function that
  owns it, by name, with what you found.
- **You do not need permission for reversible work.** Do it, then report exactly what you
  did so it can be adjusted. Asking first for everything makes an agent slower than doing
  the work by hand.
- **Reversible is the line, not confidence.** Sending a message, publishing to the public,
  spending money, and deleting data stay behind an explicit approval — see
  `agents-draft-humans-send`. Everything short of that, act.
- Report what you changed in enough detail that undoing it is a one-line instruction.
<!-- shared-rule:be-proactive-see-it-through:end -->

<!-- shared-rule:capture-what-you-learn:start -->
## Capture what you learn as a standard, in the same session

- **A rule that lives only in an article, a chat message, a call recording, or your
  context window is a rule the next agent will break.** That is not a prediction. The
  black-button rule was published, illustrated, and given an enforcement plugin on
  17 May 2026, and on 15 August 2026 an agent holding the entire skill pack in context
  shipped a black button. The rule was never in `standards/`, so it never reached the
  skills, so it was not there to be read.
- When anyone — the client, the account owner, an audit, or your own failure — states a
  rule that should hold next time, **your job is not to remember it. It is to write
  `standards/<slug>.md` before the session ends.** Memory does not survive a session
  boundary. A file does.
- Scaffold it in one command, which forces every field including where the rule came
  from:

  ```bash
  python3 scripts/new_standard.py "no autoplay with sound" \
    --from "Dennis Yu, Cowork session, 2026-08-16" --applies-to published-html
  ```

- Then write the rule, run `python3 scripts/sync_shared_rules.py`, and open the pull
  request. The sync copies the rule into `AGENTS.md` and every distributed `SKILL.md`,
  so it reaches every agent and every member who installed the pack. Nobody has to be
  told about it.
- **Give the rule a machine check whenever one is honest.** A `checks` block in the
  header compiles straight into the live fleet sweep, so a violation on a published page
  is caught by a schedule instead of by a person noticing. Every check must carry
  passing and failing examples — a pattern that matches nothing reports a clean site
  forever, which is worse than no check at all.
- **Where a machine check would be dishonest, say so and leave `checks` out.** Judgement
  rules are still rules; they are enforced by being read pre-flight, and pretending a
  regex covers them hides the fact that nothing does.
- **Provenance is required, not decoration.** `captured_from` is how the team sees which
  channels leak. If dozens of recorded calls have produced no standards, those calls are
  not being captured, and that is visible at a glance instead of being a suspicion.
- **When a new rule contradicts an existing one, resolve it in the file and say so
  out loud.** Two standards that disagree are worse than one that is wrong, because
  every agent that reads both will pick whichever it happened to see last. Write the
  reconciliation into the newer rule and flag it to the account owner for confirmation.
- The order is Checklist → Content → Software. Write the checkable rule first, publish
  the article that teaches it second, and let the sweep be generated from the rule
  rather than hand-written beside it. Writing the article first is how rules get lost:
  the article is the artifact everyone can see, so it feels finished, and the
  enforceable form never gets written.
<!-- shared-rule:capture-what-you-learn:end -->

<!-- shared-rule:content-factory-four-stages:start -->
## Content Factory four stages

- The Content Factory line is locked: **Produce → Process → Post → Promote**.
  Do not rename, reorder, or merge these four.
- **Plumbing** is onboarding / access / tracking **before** the factory
  (`client-access-checklist`). It is not a factory stage.
- **Perform** is MAA (Metrics → Analysis → Action) **after** the factory /
  promotion loop (`weekly-brand-maa`). It is not a factory stage.
- If copy still lists Plumbing / Publish / Promote / Perform as the factory's
  4 P's, or uses Publish instead of Post inside that line, rewrite to the locked
  names. Upstream skill: `skills/content-factory/SKILL.md`. Canon pages:
  https://blitzmetrics.com/content-factory/ and
  https://blitzmetrics.com/the-4-stages-of-the-content-factory/.
- SAE course map (Plumbing → Goals → Content → Targeting → Amplification →
  Optimization) is separate; the Content Factory block inside it is still only
  Produce → Process → Post → Promote.
<!-- shared-rule:content-factory-four-stages:end -->

<!-- shared-rule:definitive-articles-show-what-they-are-and-where-they-fit:start -->
## Definitive articles show what they are, their evidence strength, and where they fit

- **Name the kind of canonical page before judging it.** A task-definitive article
  is the maintained recipe for one repeatable task. A topic, entity or framework hub
  explains its subject and links to the task recipes it owns; it need not pretend to
  execute one task. Supporting stories, opinion pieces, tool comparisons, references,
  historical posts and meta-articles remain distinct. A repaired opening, lead visual,
  incoming link or prior fleet-audit label does not promote any of them to a task SOP.
- **A task recipe must let another worker repeat and check the work.** Require all of:
  the trigger and starting state; required inputs and access; linked prerequisite tasks
  and their expected outputs; ordered steps with decision points; the measurable output
  and observable pass/fail criteria; and the downstream task, receiving owner/function
  and handoff artifact. Link the canonical task in the
  [Task Library](https://local-service-spotlight.github.io/task-library/) and its parent in the
  [Content Factory](https://blitzmetrics.com/content-factory/). Do not invent a task,
  prerequisite, threshold or relationship to fill a box. Mark a missing required field
  as a gap and hold task-definitive certification until the source supports it.
- **Keep the recipe separate from each execution record.** Every task execution writes
  a [meta article recording the run](https://localservicespotlight.com/meta-articles/)
  using the [meta-article guidelines](https://blitzmetrics.com/meta-article-prompt/).
  It links to the exact canonical task, the recipe revision used and the run evidence.
  Writing is required; publishing the meta article and changing the canonical recipe
  follow the existing authorization for those actions. The run record feeds reviewed
  improvements back into the recipe and skill; it never becomes a second recipe.
- **The marker is a reviewed semantic claim, not a workflow status.** Mark a page as a
  Definitive Article, Definitive SOP or Definitive Framework only after a reviewer has
  confirmed that its labels, steps, links, evidence and canonical ownership agree with
  the accepted source of truth. A complete Task Library task, an all-tasks-complete hub,
  a taxonomy term or a `READY` state is useful workflow evidence, but none is sufficient
  by itself. An archive, alias, WIP page or semantically conflicted page gets no marker.
- **Mark the reviewed canonical hub visibly.** Put the appropriate marker above the
  opening summary so a reader can distinguish the maintained source of truth from a
  supporting post before scrolling. Supporting stories, updates and meta-articles point
  to the hub; they do not wear the marker themselves.
- **Keep certification, task priority and evidence volume separate.** Definitive status
  says the page is the reviewed canonical owner. Task importance decides which gap to
  work first. Meta-orbit strength measures only the number of verified completed-run
  meta-articles behind the hub. None of the three may be used as a proxy for another.
- **Derive each named metric from evidence; never type it into two sources.** One
  generated manifest owns the exact hub URL, mapped Task Library tasks, counted and held
  evidence records, known execution IDs or explicit missing-ID states, audit time,
  metric names, counts and strength bands. The article and Task Library render from
  that manifest. Keep historical public-example volume separate from verified task
  execution frequency. If a metric cannot be checked, report `unknown`; if only a lower
  bound is proved, report `partial`. Never turn either into zero.
- **Preserve dated public-example counts as article volume.** An earlier review may
  establish that a hub had a stated number of qualifying public meta articles on its
  audit date without establishing execution IDs. Keep that dated evidence and its
  inspectable sources. It remains historical public-example volume; it is not a claim
  of that many distinct task runs. Missing IDs do not erase verified article evidence.
- **Count task execution frequency separately.** Deduplicate each canonical task's
  executions by ID and state the reporting period and result statuses. Revisions,
  retries within one run, translations, clips and syndicated copies do not create
  executions. A separately scoped rerun has its own ID and evidence. Keep failed/partial
  and unpublished runs in internal history with their statuses. Older articles without
  a reliable run identity cannot establish execution frequency; that metric remains
  UNKNOWN or PARTIAL even when their dated article-volume count is valid.
- **Count a primary worked example, not a generic cross-link.** A counted meta-article
  must be published, explicitly classified as a meta-article, document a completed run,
  materially execute the hub's task, and link to the exact canonical hub in its
  task-specific narrative or receipt. A shared framework map, compliance table,
  related-reading list, template, index, instructional page, archive, self-link or
  incidental concept mention does not make the post part of that hub's orbit. Preserve
  the reason for every excluded or held candidate.
- **Use fixed, transparent evidence bands.** Show the exact count next to the definitive
  pill and label 0 as `No verified examples`, 1–2 as `Emerging`, 3–5 as `Supported`,
  6–10 as `Strong`, and 11+ as `Deep`. This label measures documented-run volume only,
  not accuracy, freshness, traffic, quality or certification. Do not emit rating or
  review schema from it.
- **Make the graph work in both directions.** The Task Library task links to the final
  canonical article. The article's generated, collapsed evidence footer links to the
  exact filtered Task Library route and back to every counted meta-article. A stable
  `?task=` route opens one task and a stable `?article=` route opens the complete hub.
  A count without its inspectable source URLs is decoration, not evidence.
- **Lead with the specific GCT and the article's own evidence.** In 2–3 sentences
  at fifth-grade reading level or below, name who this is for, what it does, why
  it matters and the useful outcome. Use the reader's actual situation and the
  mechanism or evidence that makes the outcome useful; follow
  `every-article-and-project-starts-with-specific-gct`. A generic benefit claim
  or an acronym definition is not a passing opening. Keep the topic-specific visual beside that
  short opening in the first screen; it may lead. A checklist is secondary and
  must not push it below the fold. Keep the most
  specific primary visual or proof for that article above the fold: the actual framework
  diagram on a framework hub, the task-specific screenshot or flow on a software SOP,
  or the real photograph, artifact or result that proves the work. A generic system map
  must never displace that evidence or push it below the fold. Keep the audience in
  the opening; move extended background, history and secondary evidence below it.
- **Show where a task fits after its first-screen orientation.** A Content Factory task
  needs a responsive context diagram lower in the article: Produce → Process → Post →
  Promote in the maintained order, only the work this task performs highlighted, and
  linked prerequisites → this task → the next task. Show the meta-record feedback into
  the canonical recipe. This context map is additional to the topic-specific lead
  visual. Keep access/tracking before the factory and measurement after it when those
  boundaries apply. An unverified placement stays a stated gap; it is not permission
  to invent a station or certify a task with an unknown handoff.
- **Use the larger system map as truthful context.** When an established framework has
  an exact relationship to the article, place its maintained detailed map after the
  article-specific primary visual and highlight only the subcomponents the article
  actually performs. Keep surrounding components visible but muted and caption what the
  highlight and handoff mean. On a framework hub, the canonical framework diagram is
  itself the primary visual and may serve both purposes.
- **A stage-only highlight or no map is valid.** If the task belongs to a stage but no
  named child station truthfully represents it, highlight only the stage and, where
  useful, its verified boundary or handoff. If no honest placement exists, omit the map
  and explain the cross-system relationship in text. Never activate a nearby box merely
  to make the diagram look complete.
- **Do not redraw a framework from memory.** Reuse the maintained labels, order, palette
  and relationships. A task-specific flow may accompany the system-placement view, but
  neither visual may make a relationship the accepted source does not support.

No fleet regex can enforce this honestly: a crawler cannot infer canonical ownership,
primary-parent evidence, truthful framework placement or whether a generic link documents
a completed run. Enforce it in the semantic preflight, source-backed orbit manifest,
bidirectional-link verifier and rendered desktop/mobile review.
<!-- shared-rule:definitive-articles-show-what-they-are-and-where-they-fit:end -->

<!-- shared-rule:explain-with-linked-examples:start -->
## Explain with linked examples

- When explaining a concept (GCT, Content Factory, Dollar-a-Day, MAA, SAE, Nine
  Triangles, or similar), always **show and link** at least one concrete example.
  A definition alone is incomplete.
- Prefer live canonical URLs: Task Library, Local Service Spotlight, blitzmetrics.com
  SEO leaves, dennisyu.com. Never invent example URLs.
- Pattern: one sentence what it is, one sentence why it matters, then the linked
  example(s).
- Starters: GCT → Task Library GCT task + theninetriangles.com; Content Factory →
  https://blitzmetrics.com/content-factory/ and name Produce → Process → Post →
  Promote; MAA → weekly-brand-maa / a client-safe Friday MAA; Dollar-a-Day → method
  page + one public-safe winner when available.
<!-- shared-rule:explain-with-linked-examples:end -->

<!-- shared-rule:keep-the-system-of-record-outside-the-model:start -->
## Keep the system of record outside any one model

- **Standards, SOPs, metadata and completed work live in files and repositories we own**,
  not inside one vendor's memory, project or chat history.
- **The test:** if the model changed tomorrow, could a new one pick up every piece of work
  in progress from the artifacts alone? If not, something important is stored in the wrong
  place.
- **Write it down where it can be read by anything.** Plain markdown, plain JSON, in a
  repository — not a proprietary format tied to one product.
- This is also why rules are copied into distributed skills rather than linked: the copy
  survives being separated from the system that made it.
<!-- shared-rule:keep-the-system-of-record-outside-the-model:end -->

<!-- shared-rule:lead-with-a-visual-executive-summary:start -->
## Every deliverable leads with a visual executive summary

- **Page one answers the question**, for someone who will read only page one. The most
  important and least obvious findings, up front.
- **Open with the reader's decision and the value of this deliverable.** In the
  first two or three sentences, connect the strongest supported finding to the
  reader's situation and the action it enables. Follow
  `every-article-and-project-starts-with-specific-gct`; a title, biography,
  table of contents or methodology paragraph alone does not orient the reader.
  On a multi-page document or deck, each later page or section also leads with
  its useful takeaway, without repeating the whole introductory pitch.
- **Interesting and non-obvious, not a restatement.** A summary that repeats what the
  reader already assumed has told them nothing; lead with what would change their mind.
- **Use colour, diagrams and tables to carry the point.** A wall of text on page one is a
  failure of the deliverable, not a style preference.
- Depth still matters behind it — a substantial analysis runs long. The summary earns the
  reader's attention for the rest; it does not replace it.
<!-- shared-rule:lead-with-a-visual-executive-summary:end -->

<!-- shared-rule:learn-do-teach:start -->
## Learn it, do it, then teach it

- **Read the standard before you touch the work.** Skipping to doing produces output that
  looks right and is wrong in ways the person reviewing it has to find for you.
- **Then do it,** all the way to a verified artifact.
- **Then teach it** — write the run up so the next agent inherits what you learned. That
  write-up is what turns one person's lesson into everyone's default, and it is the whole
  reason `standards/` exists.
- The order is not a preference. A rule taught before it is understood is repeated
  without judgement; a rule learned and then taught survives contact with a case it did
  not anticipate.
<!-- shared-rule:learn-do-teach:end -->

<!-- shared-rule:lss-is-the-public-company:start -->
## Local Service Spotlight is the public company

- **Dennis's current company in new public copy is Local Service Spotlight**, plus the
  vertical spotlight sites (law firm, pest control, dunker, and the rest). Be specific
  to that vertical. Do not present a sunset brand as the current company.
- **Do not name the sunset brand (BlitzMetrics) in new public pages, client-facing
  emails, social posts, or new product copy.** Historical URLs and git history may
  still contain it. Do not add more.
- **The existing canon/audit domain remains a publish host** for definitive articles
  and audits. Linking that URL is fine. Calling it the current company is not.
- Prefer `@localservicespotlight.com` addresses in new mail. Legacy aliases may still
  deliver; they are not a reason to put the sunset name in the body.
- This does not rewrite old articles or legal entity paperwork. It is a public-facing
  naming rule for new work.
<!-- shared-rule:lss-is-the-public-company:end -->

<!-- shared-rule:named-entities-link-to-the-most-helpful-canonical-destination:start -->
## Named entities link to the most helpful canonical destination

- **Route the first meaningful mention of a named entity to the page that best helps
  the reader understand or act on it.** Link once; do not turn every repeated name
  into a link. Use the entity's natural name for a person or company, and use 3–6
  descriptive words for a training or concept link.
- **People point to their verified personal-brand home.** Prefer the person's owned
  website over an author archive, search result or social profile. If no owned site can
  be verified, use the relevant first-party company page or a canonical article that
  establishes who the person is; otherwise leave the name plain.
- **Companies point to their owned company site.** Correct the entity name before
  linking it. A plausible domain for the wrong spelling teaches the wrong association.
- **Tools and concepts point to our canonical training when it exists.** In explanatory
  copy, use a destination-naming phrase such as "our Listen Notes inventory guide" for
  the definitive how-to page; do not point the bare product name at our domain. Put the
  product's natural name and official website on the execution step where the reader
  actually opens it. This preserves both education and a direct path to action without
  making the anchor lie about where it goes.
- **Search our article inventory before choosing a provider help page.** Look up
  the object in the Canonical Directory, Task Library and site search, then read
  the candidate to verify that it answers this reader's question. For Obsidian,
  use “our Obsidian setup guide” when that guide is the relevant lesson. Record
  the entity, chosen URL and reason in the link audit. If no suitable owned
  guide exists, keep a conceptual mention plain or cite the precise primary
  source needed for the claim; record the content gap instead of inventing a URL.
- **Give the page a place in the SEO Tree.** Name the canonical parent topic,
  link supporting articles up to it, connect the hub to useful supporting proof,
  and link across only to related guides that help the next task. Verify those
  links in the article body; a catalog listing or sitewide footer is insufficient.
  One topic keeps one owner across our sites. Do not mass-add unrelated links or
  use a quota to turn every provider citation into an internal link.
- **Keep primary citations and execution links when they do a different job.**
  A provider's API reference can substantiate a technical claim; its download or
  sign-in page can be the required action. Label those links by their purpose
  and retain them alongside our training when useful. A provider citation does
  not replace the internal explanation of how we use the tool.
- **Verify every destination before publishing.** The name, page title and live content
  must identify the intended entity. SEO value is a by-product of a truthful,
  reader-helpful relationship; it is never a reason to guess a domain.

This extends `no-unnamed-link-text`: that rule makes the anchor truthful; this rule makes
the destination useful. When a bare entity name and a training page would conflict, the
destination-naming anchor above is the reconciliation. No generic fleet regex can identify
people, ownership or the right internal training page, so enforce this through the
entity-linking preflight and a live link audit.
<!-- shared-rule:named-entities-link-to-the-most-helpful-canonical-destination:end -->

<!-- shared-rule:no-flattery-tell-it-straight:start -->
## No flattery — tell it straight

- **Do not open with praise, and do not pad findings with reassurance.** The value of a
  report is the part that is uncomfortable; softening it destroys the only reason to read
  it.
- **Every claim is proof-driven** — name the URL, the number, the date, the source. "This
  looks great" is not a finding; "the sameAs target returns 404" is.
- **Say what is broken before what is working**, and be specific about how bad it is.
- Being wrong is recoverable. Being agreeable and wrong is not, because nobody checks
  the agreeable answer.
<!-- shared-rule:no-flattery-tell-it-straight:end -->

<!-- shared-rule:outbound-email-names-the-agent:start -->
## Every outbound agent action names the agent

- **When agent-authored content reaches another person, name the agent in the
  message itself.** This covers sent email, Basecamp comments and messages,
  DMs, support replies, scheduled reports, and the human-visible receipt for a
  publish or system change. A GitHub commit or private log is supporting
  evidence, not a substitute for visible attribution.
- End with one compact line:

  `Agent receipt: <agent> [<model if known>] · action: <drafted|sent|posted|published|changed> · human review: <reviewed by Dennis|authorized, not separately reviewed|no human review recorded>`

- Put the name a human recognizes first: `Claude`, `Codex`, `Grok`, `Cursor`,
  or the actual agent name. A persona alone is ambiguous; write `Grok — Meter
  Maid`, not only `Meter Maid`. Include the exact model only when the runtime
  exposes it. Otherwise omit it or say `model UNKNOWN`; never infer it from the
  writing style, OAuth client, or vendor name.
- State review truthfully. `Reviewed by Dennis` requires evidence that Dennis
  reviewed that exact message or action. Permission to act is not review, so
  use `authorized, not separately reviewed` when that is what happened. If the
  record is missing, use `no human review recorded`.
- Resolve the exact destination, audience, thread or record before acting. If
  routing or authority is unclear, fail closed instead of sending to Dennis or
  asking him to relay the work.
- An outbound action is complete only after source-system read-back verifies
  the destination/audience, thread or record, intended content/result, and
  agent receipt. A toast, sent item, commit, or private note alone is not proof.
- Leave the next action with its real owner. For completed Gmail work, archive
  the exact thread after verified action and restore it after seven days only
  when no human reply arrived; automation and system notices are not human
  replies.
- Name the agent even when `From:` or the source-system creator is Dennis. That
  identity is the delivery account; the receipt is authorship and action
  transparency. Place the receipt after the body and before any automatic legal
  footer.
- If an agent only prepared material and a human sent the final version, use
  `Prepared with <agent>; sent by <human>` when attribution is appropriate. Do
  not label a purely human-authored message as agent-authored, and never invent
  a fake human assistant signature to hide agent authorship.
- For a public page or code change, put the line in the delivery receipt or
  source-system update; do not add operational metadata to visitor-facing copy
  unless the publishing brief asks for it.
- This rule grants no authority to send, post, publish, spend, merge, or change
  access. Apply the existing approval and destination rules first. Once an
  outbound action is separately authorized, attribution is mandatory. When only
  drafting, include the agent name in the draft so it survives handoff.
- Scheduled prompts that may act externally must explicitly use the
  `outbound-action-closeout` skill and embed its routing, receipt, read-back,
  ownership, and fail-closed rails because an unattended session may not load
  repository rules or prior conversation.
<!-- shared-rule:outbound-email-names-the-agent:end -->

<!-- shared-rule:pre-audit-before-the-client-does:start -->
## Audit our own work before anyone else can

- **Assume an outside expert will audit everything you ship**, and build so that audit
  comes back clean. That assumption is what makes the work honest rather than merely
  presentable.
- **Run the adversarial pass yourself, before delivery.** Find the broken thing while it
  is still cheap and while finding it is a credit rather than a defence.
- **Give the client the same auditing tools you use.** Work that only survives because
  nobody looked closely is not work worth selling.
- Ship the audit result alongside the deliverable, including what it found.
<!-- shared-rule:pre-audit-before-the-client-does:end -->

<!-- shared-rule:process-real-content-never-generate:start -->
## Process real content; never generate it

- **Every published piece starts from something real** — a recording, a call, a job
  actually done, a person actually speaking. AI processes that raw material; it does not
  invent the material.
- **The provenance must survive to the page.** Link the video, embed the clip, name the
  person, cite the date. A reader — and a language model reading on their behalf — should
  be able to trace the claim back to the moment it was said.
- **Repurpose one source across every surface** rather than generating a fresh piece per
  channel. The article, the short, the profile post and the email come from the same
  recording.
- An article with no traceable source is indistinguishable from an invented one, and will
  eventually be treated as invented.
- The sweep looks for a source artifact — an embed, a captioned figure, or an attributed
  quote — and reports rather than blocks, because a well-sourced piece can still fail the
  proxy. Treat a hit as "check where this came from", not as proof it was generated.
<!-- shared-rule:process-real-content-never-generate:end -->

<!-- shared-rule:qa-from-a-different-context-window:start -->
## QA comes from a different context window

- **Self-QA is necessary and never sufficient.** The agent that made a mistake is the
  agent least able to see it, because the reasoning that produced the mistake is still
  in its context.
- **Audit work with a second agent started fresh**, given the artifact and the standard
  but not the first agent's reasoning. Delegate it explicitly rather than re-reading your
  own output.
- The auditor's job is to **refute**, not to confirm. Brief it that way.
- This applies to your own work most of all. If you cannot spawn an auditor, say the work
  is unaudited rather than implying it was checked.
<!-- shared-rule:qa-from-a-different-context-window:end -->

<!-- shared-rule:report-business-impact-not-volume:start -->
## Report business impact, never volume

- **Count outcomes, not output.** Posts published, words written and tasks closed are
  activity. Calls, booked jobs, leads and revenue are results.
- **Trace the chain and show it**: published thing → ranking or traffic → call or lead →
  booked job → revenue. Where the chain breaks, say where it breaks rather than reporting
  the last link that looked good.
- **Impressions and clicks are context, not the headline.** Never lead with them.
- If the business impact cannot be measured yet, say that plainly and fix the measurement
  first — see `analytics-on-every-page`.
<!-- shared-rule:report-business-impact-not-volume:end -->

<!-- shared-rule:screen-gct-before-amplification:start -->
## Screen GCT before amplification

- **Qualification is an evidence gate, not an execution grant.** A passing business-fit
  screen still needs independent review, an accepted scope/agreement receipt, and the
  authoritative Ops roster decision before onboarding or recurring work.
- **Gate outcome and evidence quality are separate.** Every GCT gate records outcome
  `UNKNOWN | MET | NOT_MET` and evidence state
  `UNKNOWN | OBSERVED | VERIFIED | CONTRADICTED | EXPIRED`. Unknown is never zero or
  failure; preserve the exact question, owner, due date, and blocked action.
- **Verdicts are deterministic, not scored.** Evaluator disagreement, an `UNKNOWN`
  outcome, or any evidence state other than `VERIFIED` routes to
  `DISCOVERY_REQUIRED`. With no discovery condition, verified `NOT_MET` routes to
  `DEVELOP`. Only eight verified `MET` pairs can be `QUALIFIED_PENDING_REVIEW`.
- **Amplify what is already working.** Verified new-idea, no-proof, undifferentiated,
  overbroad-ICP, unfocused-offer, or capacity conditions route to one development action
  and re-screening. They do not earn plumbing, publishing, or ad spend as a consolation.
- **Fail closed on authority.** Prospect screening is public-read-only. Publishing,
  messaging, permissions, Basecamp delivery, and spend require exact scoped approval;
  `Not Active`, `HOLD`, missing roster evidence, or blocked plumbing stops execution.
- The public guide is https://blitzmetrics.com/social-amplification/. The operational
  control plane is the roster-driven Money Tree; derived output folders are not state.
<!-- shared-rule:screen-gct-before-amplification:end -->

<!-- shared-rule:silent-media-playback:start -->
## Silent media playback

- Never let audio from browser, video, audio, presentation, or application testing play through the user's speakers unless the user explicitly asks to hear it.
- Before starting any media playback, mute the player and set its volume to zero. Keep it muted for the full test, including replays, reloads, new tabs, and alternate players.
- Apply this rule to the primary agent and every delegated agent. Include the mute requirement whenever work that may involve media playback is delegated.
- If the mute state cannot be controlled and verified before playback, do not start playback. Use metadata, captions, transcripts, frames, screenshots, network state, or player state instead.
- Only unmute when the user explicitly requests audible playback in the current task.
<!-- shared-rule:silent-media-playback:end -->

<!-- shared-rule:verify-by-opening-the-live-artifact:start -->
## Verify by opening the live artifact

- **"I did it" is not evidence. The artifact is.** Before reporting any work complete,
  fetch the live URL, open the file, or query the API and confirm the change is actually
  there. An agent that has been caught reporting published articles onto a site with no
  articles has burned more trust than the task was worth.
- **Check the thing a user would see, not the thing you wrote.** A database row is not a
  published page — caches, builders and permissions all sit in between. Fetch the public
  URL as an anonymous visitor.
- **A page that could not be fetched has not been verified.** Report it as unverified,
  never as done.
- Quote the evidence in the report: the URL, the status code, and the string you found.
<!-- shared-rule:verify-by-opening-the-live-artifact:end -->

<!-- shared-rule:an-unanswered-ask-never-stops-the-work:start -->
## An unanswered ask never stops the work

- **Silence is not a blocker, it is a trigger.** When someone does not reply, the work
  continues on the rescue path you chose before you sent the ask. "Waiting on them" is
  never a status an agent reports twice.
- **Try to need them less before you try to reach them harder.** In order: do it yourself;
  route around; engineer the dependency so it cannot block again; only then ask. Most asks
  disappear at step one once you actually test them, because "I need this from them" is
  usually "I would prefer this from them."
- **Only three things justify asking a human at all** — binding authority, credentials or
  physical access nobody else holds, and a fact that exists only in their head. Preference,
  convenience, and "they would probably want to weigh in" are not gates.
- **Every ask ships with its rescue, decided before sending**: a deadline, a named fallback
  action, and you as the owner of that fallback. Put it in the message. "If I do not hear
  back by Friday I will assume X and proceed" turns silence into a decision, and usually
  produces the reply anyway.
- **Shrink the ask until it can be answered in ten seconds.** One question, one message, a
  yes or no where possible, plus what you already tried. A question that makes someone
  reconstruct context is a question that does not get answered.
- **When the deadline passes, execute the rescue quietly.** Do not re-send the same ask.
  Do not hand the chase to whoever is busiest. Log the miss for the periodic reliability
  record and move on: a pattern is a management conversation, held later with evidence in
  hand, not an interruption now.
- **The second time the same dependency blocks, stop treating it as a people problem.**
  Build the thing that makes their non-response harmless — a watchdog, a fallback route, a
  second credential, a cached copy. Building it once costs less than chasing it forever.
- This does not loosen `agents-draft-humans-send`. Rescue means doing the *work* yourself,
  never dispatching messages, publishing, spending or deleting on someone's behalf because
  they went quiet. Where the rescue would cross that line, stage it and say so.
- Rescue toward the function, not the person — see `assign-work-to-a-function`. A rescue
  aimed at an individual who is away is not a rescue.
- **A parked ask carries a date or it is not parked, it is dropped.** Any status row that
  says "waiting on", "blocked on" or "pending <person>" must also say when someone
  comes back to it. In the agent runtime this is failure mode `F10 Silence as a status`
  and `tools/lint_unanswered_ask.py` fails the build on a row without a date. The first
  run of that linter found two real ones: one five days old, one thirteen days old and
  not actually blocked on anybody.
- Canonical public statement, indexable and pulled at runtime by every scheduled agent:
  https://dennisyu.com/unanswered-ask/ — linked from https://dennisyu.com/agent-disclosure/
  and from the new-agent bootstrap box. Marker `UNANSWERED-ASK-RESCUE-2026-09-04`.
<!-- shared-rule:an-unanswered-ask-never-stops-the-work:end -->

<!-- shared-rule:every-article-and-project-starts-with-specific-gct:start -->
## Every opening makes its reader, value and purpose clear

- **Write the specific Goals, Content, Targeting before work begins.** Goals name
  the change the reader or project needs; Content names the source-backed lesson,
  proof or deliverable that will produce that change; Targeting names the people
  and situation it serves. “Publish an article” or “use AI” is an activity, not
  the desired outcome. Use the same brief for the article and the project behind it.
- **Apply the same opening standard to every format.** Documents, reports, PDFs,
  presentations, articles, homepages, landing pages, service pages, relationship
  pages and task guides must earn attention at the beginning. Improve their
  maintained owner in place. A report leads with the decision its evidence
  enables; a guide leads with the task the reader can accomplish; a buying page
  leads with the relevant customer need and the offer's supported value. Do not
  paste a sales pitch or "for entrepreneurs" onto a page whose reader needs
  something else.
- **Put the reader's situation, why it matters and the useful outcome in the
  first 2–3 sentences.** The first line offers a specific reason to continue:
  a recognizable problem, a consequential finding or a true moment with a clear
  lesson. Explain what this page or document helps the reader do and how the
  offered method, evidence or tool helps. The reader may be named directly or
  made unmistakable through their situation. They should not have to scroll
  through history, credentials, an abstract definition or a system description
  to find the point. Write the opening at US fifth-grade reading level or below.
  Use familiar words and short sentences; explain unavoidable terms on first use.
  Put commands, architecture details and specialist terms after this orientation.
  Readers should not have to know the acronym GCT to understand the page.
- **Make the value concrete without inflating the promise.** On an entrepreneur's
  Money Tree page, explain how existing customer stories, interviews and useful
  articles connect to what customers can buy. That gives a prospect relevant
  proof and a clear next step. On another page, name that reader's actual useful
  outcome: choose a service, check a result, prepare for a workshop or complete
  a task. "Build authority," "unlock potential" and "follow the stories" alone
  do not explain the benefit. Do not claim increased conversions, revenue,
  speed or certainty unless the evidence supports that exact claim.
- **Use confident, source-backed language.** State the supported value directly.
  Keep authentic moments and compact receipts; do not add doubt, reassurance,
  hype, false urgency, invented statistics or status borrowing. A necessary
  disclosure stays next to its claim. A true story may lead, but its relevance
  and takeaway must become clear in that same short opening.
- **Explain jargon on its first meaningful mention and link the owned explainer.**
  Give the familiar phrase before the specialist label: “the result we want, the
  material we will use, and who it serves — our
  [Goals, Content, Targeting (GCT) brief](https://blitzmetrics.com/gct-business-strategy/).”
  Apply this to other frameworks, acronyms and unfamiliar task terms. Verify the owned
  destination teaches the term; use honest descriptive anchors. If no suitable owned
  explanation exists, define the term in place and record the gap instead of inventing
  a link. Keep this explanation short so it does not bury the lead visual.
- **Make the opening specific enough to judge.** For a shared-memory guide:
  “Use this guide if you work with more than one AI assistant and keep repeating
  the same facts. It shows how to give them one set of notes, so each assistant
  can pick up where the last one stopped.” The project brief also names the
  source files, checks and expected handoff; never invent facts to fill the brief.
- **Review meaning before accepting a score.** Save the exact opening and its
  artifact revision in the existing editorial or proof inventory. Have a
  reviewer identify the reader/situation, the reason to care, the useful outcome
  and the mechanism or evidence supporting it, quoting the actual words. Then
  check that the promised outcome is delivered by the body and next step.
  Record PASS, FAIL or UNKNOWN with a concrete reason and the readability
  diagnostic. A short paragraph, keyword, grade score, audience label or
  conversion word alone never passes this gate. If the opening could be moved
  unchanged to an unrelated subject, rewrite it. Unchecked meaning or readability
  stays UNKNOWN; the check belongs in the internal receipt, not public copy.
- **Keep the useful visual with the short opening.** Follow
  `visuals-above-the-fold`: the topic-specific picture or diagram may come first,
  or immediately after the short opening, whichever makes the first screen
  useful. A long GCT card, checklist, changelog or navigation block must not bury
  that visual.

### Money Tree opening example

Before: "A useful conversation becomes a story. The story points to something
you can learn, build or do with us. Here is how those connections look on my site."

After: "Your best customer stories should help your next customer decide to buy.
A Money Tree connects those stories, interviews and useful articles to the
services you sell, so people can see your work and take the next step. Explore
mine to see how the same approach can work on your site."

This is a writing example, not a measured conversion claim. Adapt it to the real
reader, proof and contents of the artifact; do not duplicate it across the fleet.

The maintained public writing standard is
https://localservicespotlight.com/article-guidelines/; the definitive-hub method
is https://blitzmetrics.com/definitive-article-guide/. The older
`/blog-posting-guidelines/` page is an archive and SEO leaf. Improve these owners
in place rather than publishing a competing guideline. No regex can honestly
certify a specific GCT or human comprehension; enforce this in editorial review.
<!-- shared-rule:every-article-and-project-starts-with-specific-gct:end -->

<!-- shared-rule:every-task-execution-writes-a-meta-article:start -->
## Every task execution writes a meta article

- **Write the run record every time the task is executed.** Follow the
  [meta-article guidelines](https://blitzmetrics.com/meta-article-prompt/) and the
  [recipe and run-record relationship](https://localservicespotlight.com/meta-articles/).
  A task's definitive article is the reusable recipe. Its meta article records one
  actual execution. Writing the meta article is required even when publication is
  pending or the run ends failed, partial or blocked after work began. A plan that
  never executes is a plan, not an execution example.
- **Make the record checkable.** Include a stable execution ID; canonical task URL and
  recipe/skill revision; trigger and starting state; date and operator; inputs and
  prerequisite outputs; steps taken and deviations; output and pass/fail results;
  evidence links; lessons; and the next action, artifact and receiving function. Record
  steps, time, token use and cost when measured; preserve UNKNOWN when unavailable.
  Protect credentials and private data, and retain the full record in an authorized
  location when a public-safe version cannot include them.
- **Writing and publishing are different states.** Write and save the meta draft under
  the task's existing authority. Publish or send it only through the applicable
  authorized rail. Preserve draft, reviewed, published and verified states accurately.
  An internal agent note, task comment or publication receipt is useful evidence but
  does not replace the structured meta article. Required writing grants no new send,
  publish, merge, spend or access authority.
- **Close the learning loop with evidence.** Compare this run and prior meta articles
  with the canonical recipe. Propose the smallest supported correction for a missing
  input, ambiguous step, failed check or handoff. Record the decision and version any
  accepted recipe/skill change, using the existing review and publishing authority.
  Link the change back to the run evidence. No improvement is needed when the evidence
  reveals no defect; do not rewrite a working recipe just to show activity.
- **Count distinct executions once per canonical task.** Use the execution ID to
  deduplicate drafts, edits, derivatives and retries within a run. A separately scoped
  rerun has a new ID and its own evidence. Keep failed/partial and unpublished records
  in internal history with their status. Verified execution frequency and dated public
  example volume are separate metrics. Existing reviewed public-article counts remain
  valid as historical article volume even when those articles lack execution IDs; they
  do not establish task frequency. Preserve the evidence and audit date. Execution
  uncertainty remains UNKNOWN or PARTIAL; do not infer a run from a mere link.
- **Do not create a documentation loop with no end.** Writing and revising the meta
  article is part of the original execution. It does not recursively require another
  meta article unless a separate documentation task is explicitly scoped and executed.

No text pattern can prove that a task ran, an artifact passed, or two pages describe
separate executions. Enforce this through the run record, evidence manifest and review.
<!-- shared-rule:every-task-execution-writes-a-meta-article:end -->

<!-- shared-rule:skills-packs-plugins-and-jobs-have-distinct-states:start -->
## Skills, packs, plugins, workers and jobs have distinct states

Use these terms to choose the setup your business needs. Start with one guide and one job. Check the result before you add more tools.

- A **skill** is a written recipe for a kind of task. A **skill pack** is a selected group of skills. A **plugin** is a package for a particular app; it may contain skills, tool connections or other components. Name only what the reviewed package contains. Use the [owned explainer](https://localservicespotlight.com/plugin/) and [pack library](https://localservicespotlight.com/skill-packs/).
- An **agent** is the AI worker doing an assigned task with approved tools and access. A **job** is an assigned run with inputs, checks and a result. A **scheduled job** adds a saved time or supported event; installing instructions does not create a worker or schedule. Link the [agent guide](https://blitzmetrics.com/build-agents/) and [job guide](https://blitzmetrics.com/persistent-agents/).
- **Access** is permission to reach a source or tool in the named account and environment. Record required access, granted scope, observed connection and remaining human action separately. A downloaded ZIP, installed plugin or ready document proves none of them. Never infer approval from a package, task status or connected account.
- **Document-ready** means the recipe has its required content and review. Task Library `complete` is a contributor-supplied document-status claim. It does not by itself prove that the guide meets the required content and review standard, or that a client task ran. Record independent document review, installed-skill activation, source access, scheduled firing, business success and semantic certification separately. Record actual executions separately with their IDs, outputs and checks.
- Make the ZIP a useful first start: include a short start file, a one-task draft prompt, a manifest and dated source information. Say whether it is a guide archive or a platform-installable package. A downloaded snapshot does not update itself. Do not tell readers to delete old copies without considering their rollback and active-job dependencies.
- Use the current maintained marketplace URL and exact package name. Derive any counts from its manifest, with a revision/date; do not equate the broad Task Library with the smaller curated marketplace. Mark older names and installation receipts as historical, and verify actual installed copies before claiming parity.
- Check external platform claims against current official docs for that product, surface, plan and environment. Keep package format, installation, activation, connectors, local-file access and scheduling separate. No blanket promise that every job works on a free plan, on a phone, or while the laptop sleeps. Confirm the actual first run, output and failure handling before calling a schedule observed.
<!-- shared-rule:skills-packs-plugins-and-jobs-have-distinct-states:end -->

<!-- shared-rule:visuals-above-the-fold:start -->
## Visual and interactive content sits above the fold

- **The visual is the hook, not the reward.** A chart, diagram, photograph,
  calculator or interactive tool must be substantially visible in the first
  screen alongside the page title. This applies to every fleet page, including
  home, money, relationship, article, archive, resource and policy pages. Two or three sentences of
  lead-in above it is the maximum.
- **A blank or hidden block is a failed visual.** A colored shell, empty SVG,
  broken image, loading placeholder, clipped labels or content visible only after
  scrolling does not pass. The first screen must show a meaningful part of the
  picture or diagram with readable labels, not just its border or a thin strip.
  Give the figure an honest caption or accessible description of what it teaches.
- **If the page has an interactive tool, the tool leads.** The prose becomes the
  explanation of it, not the preamble to it. Reword any copy that points "below"
  into a back-reference to the tool at the top.
- **No prose run longer than about two screens** without a figure, pull quote,
  callout or list breaking it.
- **Why:** `every-article-has-pictures` only asks whether an image exists. A page
  can satisfy it and still bury the picture four screens down, where nobody
  scrolls. That is the exact failure this rule closes, and it shipped on
  dennisyu.com before anyone noticed.
- **Server-render the initial state of any interactive block.** WP Rocket and
  similar optimisers delay inline JavaScript until the visitor's first
  interaction, so a block that builds its own DOM paints as an empty shell —
  worst of all when it is now the first thing on the page. Bake the default state
  into the markup and make the script idempotent (`el.innerHTML = ''` before it
  populates) so it replaces that markup instead of appending a second copy.
- **Verify by measuring on the live URL, not the local render.** Site chrome is
  routinely 300–400px, so a layout that clears the fold locally can fail once
  published. Check at 1280x800 and 390x844 as an anonymous first visit, before
  any click, scroll or other interaction. Capture the viewport and record the
  visible content and its position, working media/labels, and overflow. Also
  confirm the initial figure survives delayed or unavailable JavaScript.
  Verify the saved source separately from the served page: source equality,
  HTTP 200 and an image tag alone do not prove a working above-fold visual.
- **Check what WordPress serves, including the CSS.** Paragraph formatting can
  insert markup into an unprotected inline style block and discard its first
  rule. Use a valid Custom HTML block (`wp:html`) and avoid blank lines inside
  inline CSS. Compare the served markup and applied browser styles after the
  save; a correct editor source does not prove the browser received valid CSS.
- **Minimum visible proof:** on both required viewports, the loaded visual must
  expose at least 220px of width and 160px of height, at least 40% of its own area,
  and 8% of the viewport area. At least 90% of sampled visible points must be
  unobscured by navigation, sticky bars or overlays. These are minimum acceptance
  limits, not a design target. Show the face, action or diagram's useful labels;
  geometric success cannot approve an irrelevant crop.
- **Measure painted content, not letterboxing.** For contain/scale-down/none
  images, use intrinsic aspect ratio, content-box dimensions and object-position
  to measure the photo pixels that are actually displayed. Empty padding and
  letterboxing cannot meet the visible-area or minimum-width requirement.
  CSS backgrounds currently require background-size:cover for an automated
  geometry pass. Contain, auto and explicit sizes stay unmeasured and fail that
  gate until their painted bounds receive a dedicated measurement/review.
- **Keep the title readable in that same first screen.** At least one natural
  H1 (or level-one accessible heading) text line must be visible at 18px or
  larger, with at least 90% of its text-line area visible and unobscured. A long
  title may wrap; the visual may sit beside, above or below it. Do not fill the
  viewport with a photo that hides the entire page title.
- **A background must actually show through.** Loading the photo URL is not
  enough. Opaque descendant panels and before/after overlays count as covers,
  including pointer-events:none. Transparent text or a light tint can coexist
  with the photo, but the useful visible crop still needs screenshot review.
- **The content earns the space.** A logo, social icon, navigation, cookie banner,
  decorative gradient, generic stock photo or unrelated portrait does not count.
  Use an authentic relevant moment, playable captioned source video with a loaded
  poster, or a specific diagram that teaches the page's point. Open the source
  and the rendered screenshot. A coappearance alone never proves endorsement.
- **Every page means every page.** The former prose/policy exemption is removed
  by Dennis's 2026-09-05 instruction. A short policy can use a concise diagram
  explaining its actual process. Do not invent a person or pad a page with stock.
- **Keep media invited and silent during QA.** First paint must not autoplay.
  YouTube uses youtube-nocookie.com, rel=0, cc_load_policy=1 and a page-language
  cc_lang_pref. A click-to-play poster counts only when the real relevant image
  loads and its destination/player is verified. An iframe rectangle, thumbnail
  URL or screenshot of a broken player is not playable video proof. Follow
  youtube-captions-on-by-default; never invent missing caption tracks. During
  testing mute and set volume zero before any playback; use silent metadata and
  posters if playback cannot be safely controlled.
- **Use the browser gate in every builder and publisher.** After generating the
  actual source, run scripts/rendered_visual_check.mjs on its preview and again
  on the ordinary anonymous live URL after publication, with fresh screenshot
  receipts for both viewports and JavaScript-disabled first paint. No selector,
  geometry failure, missing image or measurement error is a pass. The checker
  reads the numeric limits from this standard's rendered_gate header. Store the
  selected visual, source/permission receipt, relevant lesson, crop/label review,
  URL, timestamp and screenshot hashes in the existing proof inventory. Review
  those actual screenshots before marking a page compliant; the script reports
  geometry only and never invents a semantic or playback verdict.
- **Reconcile hero style with this rule.** A composed full-bleed hero is welcome
  where it works. If the usable evidence is a selfie or small authentic moment,
  pair a restrained type layout with that image at an honest size above the fold,
  or use a useful diagram. The older typographic-only fallback does not authorize
  a first screen without a meaningful visual.

The HTML sweep remains an early source-order warning; it cannot measure the
fold. The rendered browser gate plus source-backed editorial review is the
publication acceptance gate. A merged standard, a regenerated skill, an installed
pack and a live-page pass are separate receipts. No whole-fleet success claim is
valid while unsampled URLs, Not Active stops or per-site holds are omitted.
<!-- shared-rule:visuals-above-the-fold:end -->

<!-- shared-rule-index:start -->
## Other house rules that apply to this work

These are not repeated here because they govern published pages rather than agent behaviour. They are binding all the same — read the full text in `AGENTS.md` or `standards/` before touching a website.

- **Analytics goes on before anything gets optimised** (`analytics-on-every-page`)
- **A button must contrast with what it sits on** (`buttons-must-contrast-with-their-background`)
- **Every article has pictures** (`every-article-has-pictures`)
- **Every public page shows real people or real work** (`every-public-page-has-real-imagery`)
- **Icon-only social controls stay tappable and separate** (`icon-only-social-controls-stay-tappable`)
- **Personal-brand heroes are immersive, not boxed** (`immersive-hero-standard`)
- **Every link and every entity claim resolves** (`links-must-resolve`)
- **Never ship a black button** (`no-black-buttons`)
- **Placeholder copy never reaches production** (`no-placeholder-copy`)
- **No popup on page load** (`no-popup-on-load`)
- **No unnamed link text** (`no-unnamed-link-text`)
- **Nothing plays at the visitor uninvited** (`nothing-plays-uninvited`)
- **Order proof by authority, strongest first** (`order-proof-by-authority`)
- **A photograph has to earn full bleed** (`photo-earns-full-bleed`)
- **Show the moment, not the resume** (`show-the-moment-not-the-resume`)
- **Every URL we say out loud resolves** (`spoken-urls-must-resolve`)
<!-- shared-rule-index:end -->
