# MAA (GA4) — Ridgeline Dumpster Rental — last 28 days (through 2026-06-24)

**Graded exemplar — Grade A.** Canonical reference for the GA4 report format, and the output of the Phase 0 end-to-end run. Client-facing text only; all investigative machinery (Data Clarity grade, reconciliation, attribution-coverage %, conformance) is held in the Narrative, never shown here. See `references/report-format.md` and `references/grading-rubric.md`.

---

**The pulse:** You generated **75 leads** from the site over the last 28 days — 40 phone calls, 28 online bookings, and 7 rental-form requests. Traffic grew about 14% versus the prior month, and your Google Ads visitors more than doubled (96 → 211). Lead tracking is solid — every call, booking, and form is captured — and we found one fix that will make your source reporting more accurate.

## The numbers

**Leads by source (last 28 days)**

| Source | Leads | Of site traffic | Lead rate |
|---|---|---|---|
| Google Ads (paid search) | 23 | 211 visits | 10.9% |
| Booking tool* | 20 | — | — |
| Organic search | 19 | 435 visits | 4.4% |
| Direct / repeat | 12 | 657 visits | 1.8% |

\*These 20 are real leads, but your booking software (app.bookflow.io) is being recorded as their "source" instead of the marketing that actually drove them. We're fixing that (below) — once it's in, those leads get credited back to paid, organic, etc., so your true channel numbers are even stronger.

**Traffic trend (vs. prior 28 days):** total visits +14%; Google Ads +120% (96 → 211); organic +18% (370 → 435); direct steady and more engaged than last month.

**Where leads come from (geography):** Columbus (25), Delaware, Westerville, Grove City, Hilliard — squarely in your Columbus service area. A few out-of-state inquiries look like franchising interest rather than rental jobs.

**Top pages:** homepage (655 visits), roll-off rentals page (112), and service-area page (your most engaged, 74%) are doing the work; the cart/checkout page is the next to watch as bookings grow.

## What it means

Google Ads is your most efficient lead source — it converts visitors to leads at nearly 11%, the best of any channel, and you scaled it this month. That's the right move continued: more money into the channel that's actually producing. And it's likely doing even more than it looks, because some of those 20 booking-tool leads almost certainly started as Google Ads or organic visits before the source got overwritten.

That source-overwrite is the one tracking issue worth fixing. When a visitor goes through your booking software, GA4 currently treats the booking tool as the referrer, which hides where the lead really came from — about 1 in 4 of your leads. A quick settings change (a referral exclusion) should fix it going forward.

Direct traffic is mostly repeat customers and the customer portal, which is why it shows few *new* leads — normal for an established business. And your leads are coming from the right places: the Columbus metro, not out-of-area noise.

## What to do next

- ✅ Lock the source fix: add your booking tool (app.bookflow.io) to GA4's referral exclusions so leads keep their real source — your next report should show accurate channel credit.
- Put more budget into Google Ads while it's converting at this rate — it's your best lead engine, and scaling it is the clearest growth move this month.

## Start here

Paid search is carrying the account and still has room — let's talk budget for next month. Once the source fix is in, you'll see its true contribution is even bigger than today's numbers show.
