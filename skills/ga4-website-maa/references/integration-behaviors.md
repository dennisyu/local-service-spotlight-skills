# Call Tracking & Integration Behaviors — the gotchas reference

**Tags:** #framework #ga4 #integrations #reference

Tool- and platform-specific behaviors that are non-obvious and where the agent is most likely to be **confidently wrong** — because you have to *know* the mechanics, not reason them out. **Consult this before diagnosing anything that depends on how a specific integration writes data to GA4.** Each entry: behavior → why → what to do. Learned from the client validation set; correct any entry here when a run disproves it (and log it to the Decisions-Log).

## Call tracking (CallRail, FirmPilot, etc.)

- **First: is it a call-tracker event at all? (prevents a confident-wrong hunt.)** An **on-site click-to-call event** (`call_clicks`, site-fired `click_to_call`) is a website interaction — it has a session/touchpoint by definition, so it is attributed normally and none of the off-site/`(not set)`/custom-dimension apparatus below applies. Empty call custom dims on such a client are expected and irrelevant, not a tracking gap. Everything in this section is about **dynamic-number call-tracker vendor events** (CallRail/WhatConverts/FirmPilot). Check the event `type` in locked-config before applying any of it. (RDR's calls are on-site `call_clicks` — the touchpoint hunt does not apply; a less careful run wrongly looked for "lost call source.")
- **The touchpoint rule (the big one).** GA4 attributes a conversion to the session that generated it. A call **with a website touchpoint** (caller browsed, then called) should receive attribution. A call with **no touchpoint** — GBP call button, Google Ads call asset, direct dial — has no session and **correctly lands as `(not set)`**. This is expected, not a bug.
- **Don't auto-diagnose a "broken snippet"** when calls are `(not set)`. Treat them as off-site leads and **segment them into their own bucket** (GBP + Google Ads). The real red flag is the *opposite*: **web-touch calls landing in `(not set)`** — those should have been attributed.
- **CallRail's GA4 integration limitation:** Google doesn't expose the channel fields to CallRail, so it can't write source/medium/campaign into the default channel grouping — it sends them as **custom parameters** instead. So default channels show `(not set)`/Unassigned even when CallRail knows the source. Registering CallRail's custom dimensions in GA4 surfaces it — but that's **not retroactive** (set up at integration time, or historical call source is lost). When registered, they appear in the API as `customEvent:source` / `customEvent:medium` (event-scoped). **Detect them via `get_custom_dimensions_and_metrics`; when present, query those to attribute calls** instead of the channel grouping. (Greenline Turf registered these 2026-06 — "CallRail Source" / "CallRail Medium" — so its call source becomes queryable from that date forward.)
- **`first_time_phone_call` vs `repeat_phone_call`** — only first-time is a *new* lead; repeat = existing customer. Don't count repeats as new leads.
- **Vendor caveat — the touchpoint rule is vendor-agnostic; tool *mechanics* are not.** Any call with no session lands Unassigned regardless of the call tracker, so the off-site/touchpoint read holds generally. But the **custom-parameter behavior above is CallRail-specific** — do NOT assume other tools (FirmPilot, WhatConverts, etc.) integrate the same way. Verify per tool before asserting mechanics; flag it as "may indicate," not a conclusion.
- *(Greenline Turf: 239/247 calls `(not set)`, likely off-site/GBP — CallRail confirmed via custom dims. Wexford Legal: ~250/332 call leads Unassigned — the off-site read holds by the touchpoint rule, but its tracker's specific GA4 mechanics are **unverified** — earlier conflation with CallRail was an unfounded assumption.)*

## Booking / checkout / scheduling tools (app.bookflow.io, etc.)

- **Cross-domain self-referral.** The booking/checkout flow routes through the tool's own domain, so when the user returns GA4 credits the **tool** as the source — overwriting the real one. It can become a top "referral" lead source.
- **Fix:** add the domain to GA4's referral exclusions ("List unwanted referrals"). Watch `app.*`, `*.bookflow.io`, booking/checkout/scheduling/portal subdomains, payment processors.
- **Exclusion caveats (say them to the client):** NOT retroactive — applies from save-date forward, historical leads stay mis-attributed; capped at 50 domains per data stream. Hedge accordingly: "should improve source credit on future reports."
- Flag it as a headline only when it carries a **material share of leads** (at session level it's minor noise).
- *(RDR: `app.bookflow.io` = 27% of leads, all overwritten; the 6/24 exclusion action verified NOT applied on 7/8 — always re-verify by date that a claimed fix actually landed.)*

## GA4 enhanced-measurement events

- **`form_start` is faulty/noisy** — fires on field focus, misfires, catches bots. **Never a lead**, and not reliable evidence of real form activity. `form_start` with **no `form_submit`/completion event** = form leads untracked → flag "verify the form submits and that submission is tracked." *(Greenline Turf: 161 starts, no completion.)*
- **`scroll`, `video_*`, `page_view`, `session_start`, `user_engagement`, `first_visit`** — micro/diagnostic, never leads.

## Source / attribution buckets — what each actually means

- **`(direct) / (none)`** — the *absence* of a source (typed URL, untagged link, in-app, stripped referrer). Not a real source; never counts as "attributed." High Direct **+ mostly new users** = untagged acquisition (verify with new-vs-returning, not brand/repeat).
- **Unassigned** — GA4 couldn't map the hit to a channel (non-standard medium, consent, call-tracking events without source).
- **`(not set)`** — the value is missing for that dimension/scope (off-touchpoint calls; landing page on event-only/bot sessions).
- **`(data not available)`** — Google thresholding (small samples + Google Signals).
- **Coverage ≠ clean attribution.** Direct (no source) and overwritten referrals (wrong source) are not clean attribution. Report clean coverage (paid / organic / real referral / social) separately; never claim "X% tracked to a source" by counting Direct.

## UTM / tagging issues

- **Non-standard UTM medium** — a custom `medium` that doesn't match a channel rule (e.g. a CTV buy tagged `medium="Live Sports"`) gets dumped into Unassigned. Fix the UTMs. *(Wexford Legal/the regional-TV buy.)*
- **Programmatic/DSP & preview referrals** — `ads.simpli.fi` (DSP), `ads.google.com` (ad preview), `imasdk.googleapis.com` (video player), `tagassistant.google.com` — untagged paid leaking as referral, or internal/tooling noise. Tag paid with UTMs; ignore the tooling. *(Greenline Turf.)*
- **Self / CRM referrals** — `*.force.com`, `infusionsoft`, `lusha` — noise unless carrying lead share.

## GBP — what you can and cannot claim (confident-wrong hotspot)

Both known render-time fabrications clustered here. The rules:

- **You cannot infer GBP link status from traffic.** Untagged GBP clicks land as `google / organic` or Direct whether or not the GBP↔GA4 link exists. Absence of GBP-tagged sessions proves only that the GBP website link isn't UTM-tagged — never say "this likely means GBP isn't connected."
- **Linking GBP does NOT surface GBP data in this report.** GBP-linked metrics live in GA4's special UI reports, not the Data API this analysis runs on. Never promise that connecting GBP "will give us visibility" in these reports. Honest framings: "tag the GBP website link with UTMs so GBP-driven *site* visits become measurable here," or "GBP's own call/direction data is a separate check outside this report."
- **What IS grounded:** detecting UTM-tagged GBP traffic in Q3 (if tagged, report it); recommending UTM-tagging the GBP link (real, actionable); asking the human to check link status in GBP settings (a verification action, not a claim).
- The GBP↔GA4 connection changed in 2026 and its behavior is still settling — treat any GBP mechanics claim beyond the above as unverified; hedge or omit.

## GA4 Data API limits (what the GA MCP can't see)

- **No organic search query dimension.** GA4 killed keyword data; the Data API has no query field even when GSC is linked (it rejects `organicGoogleSearchQuery`). Organic search terms come from the **GSC agent**. Note: `googleAdsQuery` (paid) *is* available.
- **Search Console data** lives in GA4's special UI reports, not the Data API.
- **GBP native data** (calls/directions/clicks/bookings) lives in the GBP-linked reports, not the standard Data API; needs the link, aggregates multi-location, 6-month retention.
- **`conversions` vs key events** — GA4 renamed "conversions" to "key events"; the `conversions` metric still works in the API and marks which events are key events.

## Property hygiene

- **Duplicate / abandoned properties** are common (agency migrations leave ghosts). Pre-flight every run. Three outcomes: (a) live → proceed; (b) abandoned but a live same-brand sibling exists → switch; (c) no accessible live property → not implemented / access gap → escalate, don't fabricate. *(RDR ghost `100200302`; Halverson: no live property.)*
