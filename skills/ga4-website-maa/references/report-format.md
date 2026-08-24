# GA4 Report Format — the client-facing deliverable

**Source:** Local Service Spotlight MAA conventions (canonical SOP: `skills/weekly-brand-maa/SKILL.md`), adapted for GA4.
**Tags:** #framework #ga4 #report #client-facing

The consistent report the GA4 agent produces every run. Same voice and bones as the Ads MAA so a client gets one consistent product across data sources.

## The cardinal rule: machinery stays internal

Everything investigative — Data Clarity grades (Clear/Hazy/Opaque), the lead reconciliation ratio, attribution-coverage %, conformance /10, thread names — is **internal reasoning**. It is the GA4 equivalent of the Ads "framework vocabulary stays internal" rule. The client never sees it. It lives in the Narrative and drives the report; the report **translates it into plain-English business language and data**.

Translation examples:
- 🔴 Opaque / attribution coverage 24% → "Your phone leads aren't tracking to a source yet, so we can't tell which marketing drives your calls. Here's the fix."
- Reconstruction gap 4.8× → "You're getting about 90 leads a month, but only 19 are showing up in reports — here's the tracking gap and how we close it."
- Conformance 2/10 → (not shown; becomes a tracking-cleanup action in plain terms.)
- Conversion dilution → "Most of what's being counted as a 'conversion' is giveaway entries, not real case leads — here's the real number."

## Data-rich, not minimal

Dennis wants charts and data points, *then* the explanation and the action. Show the numbers; don't just summarize them. Lead with the business metrics (the "M" that usually gets skipped).

## Model-adaptive (read first)

This format works for any business model (see `business-models.md`). The bones never change: pulse → numbers shown as Winners & Opportunities → what it means → what to do next → start here. Two things flex by model: the **name of the headline number** (leads / sales / subscribers / members / donations — use the client's own word, never "conversion") and the **third dimensional lens** (local lead-gen uses Cities; e-commerce uses Products; audience uses Top Content; membership uses Offer Pages; donation uses Campaigns). Channels and Pages are shared by all models. Cities and the GBP panel render only for local businesses. Below, "leads" is written as the lead-gen example; substitute the model's word.

## Structure (every run)

1. **Business pulse** — plain-English headline: the primary conversion this period vs. last, and the trend, in the client's own word (leads / sales / subscribers / members / donations). 2–3 sentences. Primary conversion first.
2. **The numbers, shown** — momentum first, then the Winners & Opportunities pairs in the model's lens order:
   - **Primary-conversion trend** — 13-week (or available) line of the headline number over time, split by type where meaningful (e.g. calls / forms / bookings; or product categories; or signup sources).
   - **Channels** — Winners & Opportunities pair. Flag any source under review (booking-tool/checkout referrals) rather than silently counting it. Shared by all models.
   - **Pages** — Winners & Opportunities pair. Shared by all models.
   - **Third lens (model-dependent)** — Cities (local lead-gen, spam-screened + service-area-filtered) · Products (e-commerce, by revenue) · Top Content (audience) · Offer Pages (membership) · Campaigns (donation).
   - **GBP panel** — local businesses only; parked until the GBP↔GA4 link matures. If clearly connected and UTM-tagged it may render; otherwise omit silently. Never render for a national/online business.
   Every number gets a comparison (vs. prior period, % change). A number with no baseline is not reported.

## Winners & Opportunities — the render pattern

The owner is not an analyst. Every dimensional section is a paired view, never a data dump: **what's producing** (top 5) vs **worth a look** (top 5, guarded). One plain-English read per list, one line per row.

Read "leads" below as "the primary conversion" (sales / subscribers / members / donations by model).

| Dimension | Winner = | Opportunity = |
|---|---|---|
| Channels (all models) | most conversions, with conversion rate | sends real traffic, converts at <25% of site average |
| Pages (all models) | producing conversions | visitors but no conversions → CTA/form/content fix |
| Cities (local lead-gen only) | most leads | in-service-area traffic with no leads |
| Products (e-commerce) | most revenue / units | high views, low add-to-cart or purchase → PDP/pricing look |
| Top Content (audience) | most signups / most engaged | high traffic, few signups → weak or missing signup CTA |
| Offer Pages (membership) | most enrollments | pricing/offer views, few enrollments → checkout friction |
| Campaigns (donation) | most donations / raised | traffic/appeal with few completed gifts → donation-flow friction |
| Device / timing (all) | — (no winner list) | a single line, only when a material gap passes the guards (e.g. mobile converts at half of desktop) |

**The expected-vs-actual line** makes an opportunity legible: compute the lead rate and apply it to the row's traffic — "Bexley sent enough visitors for about 4 leads at your normal rate; it produced 0." Arithmetic on the Standard Pull; no new queries.

**Dimension-attributable rate (correctness rule, not optional).** Before computing the rate for a W&O view, check whether the dominant lead type(s) actually carry the dimension being ranked. Phone-call events typically land `(not set)` for landingPage, pagePath, and often city — a blended site-wide rate is then dominated by leads that can never appear in those rows, and "expected leads" becomes fiction (FixDoor: blended rate implied ~37 expected homepage leads when only ~3 were form-attributable). Rule: compute the expected-vs-actual math using **only the lead types that carry the dimension** (e.g. form-only rate for pages/cities), and say so in the internal log. If the dimension-attributable lead count is too small for the guards to bite, the honest render is "most leads (calls) can't be placed on a page/city yet" — not a forced ranking.

**Guards (mandatory):**
- **Minimum sample.** A row qualifies as an opportunity only if expected leads ≥ 2 (sessions × the dimension-attributable lead rate ≥ 2) AND actual leads = 0 or lead rate < 25% of that same rate. Below the bar it's noise, not evidence — don't print it. Within 20% of the bar → internal watch item (near-threshold rule), carried in the Narrative.
- **Winner collapse.** Don't rank five rows when three have 1 lead each. Single-lead rows collapse into one line ("plus a handful of singles across the metro"). Fewer than 3 meaningful winners → show fewer; never pad.
- **Completion pages never rank.** Thank-you/confirmation/receipt pages are where leads *complete*, not what *produced* them — fold them into the lead count ("your 28 bookings confirm on the thank-you page") or omit; never list one as a top page.

**Order and filters:** channels → pages → third lens (model-dependent: cities / products / top content / offer pages / campaigns), always. An out-of-area city is never an "opportunity" — that's contamination, handled in Data Clarity. Sources under review (booking-tool/checkout referrals) are flagged in place, not silently ranked.

**Depth cap:** each pair ≤ 10 lines plus its two reads. The full tables live in the vault deliverable for Daniel, never in the client text.
3. **What it means** — the read on the data: what's working, what's off, any tracking issue in plain language. 2–4 short paragraphs, narrative arc. Translate, never expose the grade.
4. **What to do next** — 2–3 decisive, data-driven **recommendations**, framed as next moves the owner (and we) should make — NOT a status recap of internal work-in-progress. "Rework or pause the Facebook campaign — it's your biggest traffic source and produced one lead," not "we're working on the Facebook campaign." An our-side task may still carry ✅, but phrase it as a next step we're committing to ("Lock the tracking this pass: filter bots and register all forms"), never as a description of ongoing effort. Client-side items name the contact and ask one specific question. Forward-only — completed diagnostics belong in "what it means," not here.
5. **Start here** — the single next move or most important open question. Not a restatement of action #1.

## Comparison scope (what "every number needs a comparison" actually means)

Criterion 2 ("every number gets a comparison + % change; no baseline → not reported") applies to the **leads headline, the lead mix, channels, and the 13-week trend** — the momentum numbers. It does **not** demand a prior-period figure on the **pages and cities** Winners & Opportunities rows: those are current-window "what's producing right now" snapshots, and they carry their comparison through the **expected-vs-actual line** ("enough traffic for ~4 leads at your normal rate; produced 0"), not a PoP delta. The Standard Pull deliberately pulls Q5/Q6 current-window only. So a page/city row with no prior number is fine; a channel or headline number with no prior number is not. State page engagement % as a current figure, not a fabricated trend. (This carve-out is explicit so it stops reading as a rule the exemplar silently breaks.)

## Recurring-run voice (owner-triggered weeks)

On a Recurring Re-Run the team may not be doing hands-on work that week, so the "What to do next" section changes shape:

- **Report fix-progress, don't re-promise.** For a known issue already in the locked-config, say whether the fix landed — "we flagged the booking-tool source fix earlier; it doesn't look applied yet" — rather than issuing a fresh ✅ commitment as if starting new work.
- **No fabricated team ✅.** Only mark ✅ an action the team is actually committed to this cycle. If the week is clean and owner-triggered, "What to do next" may be mostly a client-side ask plus "keep doing X."
- **New asks only.** Raise a client-side ask only when it's genuinely new or unresolved; don't re-ask a settled question every week.
- Everything else (leads-first pulse, data shown, machinery hidden, hedged fixes) is identical to First-Run.

## Voice rules (inherited from the MAA framework)

- Plain English. Translate to business impact ("about 4 leads' worth of traffic," not "830 sessions").
- Tactful: "still gathering data," not "failing."
- **Hedge fix outcomes.** Tracking is complex — a change may not fully resolve an issue. Say a fix *should* resolve something, not that it *will*: "a referral exclusion should fix it," never "fixes it." Promise the action, not a certain outcome.
- No framework/grade vocabulary, ever.
- **Write like a person, not an AI (the report goes to a skeptical owner).** Avoid the em-dash (`—`); it is the single strongest AI-writing tell. Use a period, a comma, a colon, or parentheses instead, and cap it at roughly one em-dash per report if any. Avoid the other tells too: the "it's not just X, it's Y" construction, "in today's fast-paced world," reflexive "leverage / utilize / delve," and three-adjective triads. A report that reads as machine-written costs trust, which is the whole game for a small-business owner.
- Charts carry real data with a one-line read; don't make the client interpret a raw chart.
- Keep it tight — a busy owner reads it in a couple of minutes.

## Rendering

The markdown report (data tables + prose) is the canonical deliverable, saved to the vault. The chart render (Basecamp-ready, like the Ads client-view stage) is a post-processing step on top — it reads the report's data points and draws the trend + source charts. The agent never invents a chart number; every chart is derived from the report's data.

## Where it's saved

`{client_vault}/{client}/MAAs-GA4/YYYY-MM-DD.md`, where `{client_vault}` is whatever client folder your team uses — GA4 reports sit beside the Ads MAAs in it.
