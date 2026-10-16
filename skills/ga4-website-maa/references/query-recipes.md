# Query Recipes — the Standard Pull

Exact calls for the Google Analytics MCP (`analytics-mcp`, 9 tools). Run these as written; don't improvise dimensions, metrics, or date ranges. If the API rejects a dimension/metric, log the rejection (Decisions-Log candidate) — don't silently substitute.

## Conventions

- **Current window:** `{"start_date": "28daysAgo", "end_date": "yesterday"}`
- **Prior window:** `{"start_date": "56daysAgo", "end_date": "29daysAgo"}`
- **Trend window:** `{"start_date": "91daysAgo", "end_date": "yesterday"}`
- Never include today — incomplete trailing periods poison comparisons.
- `keyEvents` is the current metric name; `conversions` is the legacy alias and still works. Use `keyEvents`, fall back to `conversions` if rejected.
- Every metric reported to the client needs both windows (comparison + % change).

## Pre-flight

**P1 — liveness** (`run_report`)
- dimensions: `date` · metrics: `sessions` · dates: current window
- Reading: sustained ≥10 sessions/week = live. Near-zero = ghost → P2.

**P2 — sibling search** (`get_account_summaries`)
- Scan for same-brand properties. Re-run P1 on candidates. (RDR: handed `100200302` was dead; live data on `100200301` in a different account.)

**P3 — property context** (`get_property_details`) — timezone, currency, industry. Run on first touch or property switch.

## Standard Pull (every run)

**Q1 — event inventory** (`run_report`)
- dimensions: `eventName` · metrics: `eventCount`, `keyEvents` · dates: both windows · limit high enough to get all events
- Purpose: reconstruct leads (case/list-building/micro), detect dilution (C7), detect `form_start`-without-submit.

**Q2 — channel mix** (`run_report`)
- dimensions: `sessionDefaultChannelGroup` · metrics: `sessions`, `engagementRate`, `keyEvents` · dates: both windows
- Purpose: Direct share (C1), Direct surge (C2), Unassigned share (C3), channel trend.

**Q3 — source/medium detail** (`run_report`)
- dimensions: `sessionSource`, `sessionMedium` · metrics: `sessions`, `keyEvents` · dates: current window · order by sessions desc, top 25
- Purpose: non-standard mediums (C4), booking-tool/self referrals (C8), GBP-tagged traffic (D).

**Q4 — lead events × source** (`run_report`)
- dimensions: `eventName`, `sessionSource`, `sessionMedium` · metrics: `eventCount` · dates: current window · dimension filter: `eventName` inList [the case-lead + list-building events found in Q1]
- Purpose: attribution coverage of leads (C5), clean-vs-raw coverage (C6), leads-by-source table, booking-tool lead share (C8).
- Alternative: `run_conversions_report` where its conversion_spec fits; same dimensions.
- **Prior-window pull when C8 is a known issue.** If the locked-config lists a booking-tool/self-referral overwrite (or C8 is expected), run Q4 for the **prior window too**, so the booking-tool lead PoP in the report is a *pulled* number, not one remembered from an earlier report. (RDR: the "~20 last month" booking-tool figure had to be recalled from the exemplar because prior Q4 wasn't pulled — pull it.)

**Q5 — pages** (`run_report`, two calls)
- 5a landing: dimensions: `landingPage` · metrics: `sessions`, `engagementRate` · current window · top 15
- 5b lead pages: dimensions: `pagePath` · metrics: `keyEvents` · current window · top 15
- Purpose: owner-question B; traffic-but-no-leads pages = CTA/form problem; `(not set)` landing share (C9).

**Q6 — geography of leads — LOCAL model only** (`run_report`, two orderings). Run the cities view only when the routed business is local (bounded service area, per business-models.md). For non-local models, run **Q6-ALT** instead and skip the cities W&O.
- 6a: dimensions: `city`, `region` · metrics: `sessions`, `keyEvents` · dates: current window · top 25 **by keyEvents desc** (the winners)
- 6b: same query, top 25 **by sessions desc** (traffic-heavy zero-lead cities — the opportunities; a keyEvents-only sort cannot see them)
- Purpose: spam screen vs service area; out-of-area lead clusters (Tehran test); cities W&O both sides.
- **If spam is found in the current window, re-pull for the prior window too** so both sides of the comparison are screened.
- **6c — spam-screen geo pull when key-event registration is incomplete (REQUIRED whenever candidate lead events exist that are NOT flagged key events).** 6a/6b rank by `keyEvents`, so they are **blind to spam sitting in unregistered lead events** — exactly the broken-anchor case. When Q1 shows candidate lead events not flagged as key events, run: dimensions `eventName`, `city`, `region` · metric `eventCount` · **dimension_filter `eventName` inList [all candidate case-lead events]** · current window · **order by eventCount desc, limit 100** (filter to candidate events and cap cities — the unfiltered event×city×region pull overflows: 2 windows × N events × 300+ cities). This is the pull the Tehran test actually needs when registration is broken. (Brightline Painting: two entire forms were 100% out-of-area bots but invisible to Q6a because they weren't key events.)

**Q6-ALT — the model's primary dimensional lens (non-local models).** Replaces the cities view. Pick per routed model (business-models.md):
- **E-commerce → products:** dimensions `itemName` · metrics `itemsPurchased`, `itemRevenue`, `itemsViewed` · current window · top 25 by itemRevenue. Plus the **checkout funnel**: one `run_report` with dimension `eventName` filtered to `view_item`,`add_to_cart`,`begin_checkout`,`purchase` · metric `eventCount` (report the biggest step drop-off). Consider `run_funnel_report`.
- **Audience → top content + signup sources:** 5b already gives signup pages; add dimensions `pagePath` · metrics `sessions` (top content by traffic) and cross with the signup event by source (Q4-style filtered to the signup event).
- **Membership → offer/pricing pages + enrollment funnel:** dimension `pagePath` filtered to `/pricing`,`/join`,`/enroll` · metrics `sessions`,`keyEvents`; funnel view of offer-view → checkout → enrollment.
- **Donation → campaigns/appeals:** dimensions `sessionCampaignName` (or `landingPage` for appeal pages) · metrics `sessions`, the donation event count/revenue · current window.
Every Q6-ALT keeps both orderings in spirit (by-conversion for winners, by-sessions for opportunities) and feeds the same Winners & Opportunities render.

**Q7 — 13-week trend** (`run_report`)
- dimensions: `isoYearIsoWeek` (fallback `week`) · metrics: `sessions`, `keyEvents` · dates: trend window
- Purpose: leads trend chart, anomaly detection. Drop the incomplete current week from the chart.
- **Clean the trend when the key-event set is contaminated (C7 dilution OR broken registration).** `keyEvents` weekly tracks *whatever is flagged* — under giveaway dilution it draws the giveaway's decline, not leads; under broken registration it only sees the 2 registered events. Either way a "leads trend" built on raw `keyEvents` is a lie. When C7 fires or registration is incomplete, **re-pull Q7 filtered to the locked case-lead events** (dimension_filter `eventName` inList [case leads]) so the trend is the real lead trend; if that's not drawable, fall back to a session-only trend + the PoP lead comparison and SAY it's sessions, not leads. (Wexford Legal: raw Q7 tracked the motorcycle giveaway, not client inquiries.)

**Q8 — new vs returning** (`run_report`)
- dimensions: `newVsReturning`, `sessionDefaultChannelGroup` · metrics: `sessions`, `engagementRate` · dates: both windows
- Purpose: verifies C2 (Direct surge = bot/untag flood only when mostly-new + engagement collapse) and the "Direct = repeat customers" read on established businesses.

## Conditional calls

| When | Call |
|---|---|
| Call attribution question — **only for a call-tracker vendor event** | First check the call event `type` in locked-config. **On-site click event** (`call_clicks`-type) → calls already carry a web touchpoint; attribution is intact, custom dims are irrelevant, do NOT run this expecting a fix. **Call-tracker vendor event** → `get_custom_dimensions_and_metrics` → query `customEvent:source`, `customEvent:medium` if registered (CallRail-specific; not retroactive; other vendors may differ) |
| Paid present | `list_google_ads_links` |
| Trend anomaly | `list_property_annotations` (deploys/launches explain steps) |
| Funnel question (booking flows) | `run_funnel_report` |
| "Is it tracking right now" | `run_realtime_report` |
| Timing opportunity check (monthly, or owner asks about hours/staffing) | `run_report` — dimensions: `dayOfWeek`, `hour` · metrics: `sessions`, `keyEvents` · current window. Renders only as a single opportunity line, sample-guarded (report-format § Winners & Opportunities). |

## Fold-in pulls (Q9–Q11 — run in-line, never defer to a human second pass)

These fire on the triggers below and run **inside the same run**. This week's Opaque reports each needed one of these as a manual follow-up; folding them in is what removes the second pass. Triggers are wired from `SKILL.md` Phases 0, 2, and 4.

**Q9 — off-domain / sibling-property conversion sweep** (`get_property_details`, `get_custom_dimensions_and_metrics`, `run_report`)
- **Trigger (any):** routed model is e-commerce with 0–1 tracked purchases and ~$0 revenue on the main property; OR `get_account_summaries` (P2) shows a same-brand **sibling or subdomain** property with sustained traffic (≥ the main property's); OR checkout is known off-domain (BigCommerce / Shopify / Stripe-hosted).
- On the sibling/subdomain property ID: (1) `get_property_details` — confirm brand + industry; (2) `get_custom_dimensions_and_metrics` — find registered ecommerce params; (3) `run_report` — dimension `eventName`, metric `eventCount`, **both windows** — look for `purchase`, `begin_checkout`, `add_to_cart`, `view_item`.
- If `purchase` fires: `run_report` — dimensions `date`, `sessionSourceMedium`; metrics `transactions`, `purchaseRevenue` (fallback `totalRevenue`), both windows.
- **Reading:** if the sibling/subdomain carries the transactions, the main-site report is **structurally incomplete, not merely tracking-gapped** — say so and headline the combined (or the sibling's) picture per model. (Cascade Trading Post: `auction.cascadetradingpost.example` = `100200303` carries the sales the main-site `$0` hides.)

**Q10 — event-onset daily trend** (`run_report`, then `list_property_annotations`)
- **Trigger:** any candidate conversion/key event goes **0 → N** between prior and current windows, or jumps >2× unexplained.
- `run_report` — dimension `date`, metric `eventCount`, `dimension_filter` `eventName` = [the newly-appearing event], dates = **trend window** (`91daysAgo → yesterday`). Then `list_property_annotations` for a deploy near the onset date.
- **Reading:** a clean step from 0 to a steady daily rate on a specific date = **new instrumentation went live** (note the date; good, expected). Erratic spikes or a rate that tracks pageviews = **possible double-fire** → data-quality watch, flag for a tag check. (Fairmount: `form_submission` 0 → 12.)

**Q11 — out-of-area behavioral confirmation** (`run_report`)
- **Trigger:** a local-only business has an out-of-area lead cluster that **engages normally** (NOT the ~0-engagement datacenter-bot signature), so the Q6 Tehran test can't call it.
- `run_report` — dimensions `city`, `deviceCategory`, `browser`, `landingPagePlusQueryString`; metrics `sessions`, `averageSessionDuration`, `engagementRate`, `screenPageViewsPerSession`; `dimension_filter` `city` NOT inList [confirmed service-area cities]; current window.
- **Decision rule:** real-customer pattern = mixed devices/browsers, normal duration, service/quote landings, spread across cities → legitimate leads of a *different type* (flag to the client, do **not** screen). Bot/noise = single device/browser, ~0 duration, one landing page, concentrated in a datacenter city → screen. (Kestrel Air: ~20% of 89 leads out-of-area but engaged normally.)

## Conversion-event patterns (candidate classification — locked config wins)

**This table is the LEAD-GEN model.** For e-commerce (`purchase`), audience (`sign_up`/`subscribe`), membership (`enroll`/`trial`), and donation (`donate`), the primary-conversion event patterns and tiering are in `references/business-models.md` (one sub-section per model). Route the model first, then use its patterns. The tiering rule is universal: primary conversion = the model's money action (the headline), secondary = a real non-primary action (own line), micro = never counted. An event's tier is model-relative (a newsletter signup is secondary for a plumber, primary for an author).

### Lead-gen pattern table

| Pattern | Tier |
|---|---|
| `click_to_call`, `phone_call`, `first_time_phone_call`, `call`, CallRail/WhatConverts events | Case lead (calls) |
| `generate_lead`, `contact`, `submit_lead_form`, `request_quote`, `quote_request`, named `contact_form_*` | Case lead (forms) — a real contact/quote form, not search/newsletter |
| auto `form_submit` (GA4 enhanced-measurement) | **Disambiguate:** if named custom submit events exist (`contact_form_*`, `submit_lead_form`), the auto `form_submit` is the raw all-Direct **double-counter** → Micro, do not count. Only treat `form_submit` as the case-lead form event when it is the ONLY form event present, and verify it against a known count first (thank-you views/CRM). (Brightline Painting: auto `form_submit` shadowed the named forms.) |
| `book_appointment`, `booking_confirmed`, `purchase` (rental/booking checkouts), `schedule` | Case lead (bookings) |
| qualified chat events (`chat_qualified`, vendor-specific) | Case lead (chat) |
| `sms`, `click_to_text`, `text_lead` (click-to-text capture) | Case lead (text) — verify it's a real text-lead event, not a share button |
| `giveaway_entry`, `newsletter_signup`, `email_signup`, popup captures, `chat_start` | List-building |
| `repeat_phone_call` | Existing customer — not a new lead |
| generic `form` (fires alongside named `generate_lead_*`/`submit_lead_form` events) | Micro — likely the form library's raw interaction event double-counting the named submits; verify before ever counting |
| scheduler/booking **click** events (Calendly-type link clicks with no completion event) | Micro — a click is not a booking; flag "booking completions untracked" |
| `form_start`, `scroll`, `video_*`, `page_view`, `session_start`, `user_engagement`, `first_visit`, `click`, `file_download` | Micro — never leads |
| engagement-timer events (`*_min`, `five_minutes_on_site`, `time_on_site`, `session_time`) and page-view-duplicate events (a custom event like `homepage` that fires on ~every pageview) | Micro — never leads. **Common on content/personal-brand/nonprofit sites, and frequently mis-flagged as GA4 key events** (a coaching brand `homepage` = 99.6% of pageviews flagged as a key event; Wexford Legal/Wexford Legal `time_on_site`; a nonprofit site `five_minutes_on_site`). When one of these is flagged as a key event it drives C7 dilution toward ~90%+ — report the real (near-zero) conversion count, and note the mis-registration as a config fix. |

Ambiguous event on first touch → propose, ask the human, lock in the Narrative. **Name-vs-flag conflict** (lead-patterned name but not a GA4 key event, or key-event flag on a non-lead name): the pattern table classifies, the flag is a tiebreaker only — note the conflict, never silently resolve it.

## Known API limits (don't fight these)

- No organic search query dimension (`organicGoogleSearchQuery` is rejected even with GSC linked) → GSC agent. `googleAdsQuery` (paid) does exist.
- GBP native metrics (calls/directions from the profile) are not in the Data API — need the GBP link, 6-month retention, multi-location aggregate.
- `(data not available)` = Google thresholding on small samples; say so rather than reporting fragments.
