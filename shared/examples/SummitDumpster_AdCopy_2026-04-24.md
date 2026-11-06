# Ad Copy Recommendations, Summit Dumpster Rental
## Generated: 2026-04-24

> **Pre-1.6.0 sample, kept for history. Do not copy from it.** Headline 5 and
> Description 1 advertise a 10-yard size the real business does not carry; the
> 1.5.0 skill had no fact check against the client's website. From 1.6.0 every
> line must cite a source and every claim must be on the client's fact sheet
> (`../frameworks/copy-facts-template.md`).

> Anonymized **sample output** from `google-ads-copy-optimizer` for the Summit
> Dumpster Rental account (an earlier cycle, 2026-04-24). Included to show the
> copy-optimizer's output format. It is a separate sample, not the dispatch from
> the 2026-06-26 MAA in this folder.

> **STATUS: STAGED, HOLD UNTIL 2026-05-01 MAA.** The current 4/17 Roll Off Dumpster
> RSA only has one week of data. After 295 impressions and 1 conversion in week one,
> it's too early to swap in a second variant. Re-evaluate after the 2026-05-01 data
> pull, if the current RSA is still rated AVERAGE with Ad Relevance still Below
> Average on "roll off dumpster" and "roll off dumpster rental brightwater," launch
> the copy below alongside the existing RSA at that point.

### Context
The Roll Off Dumpster RSA launched on 4/17 as part of the dedicated-ad-group restructure. After one week it has pulled 295 impressions, 15 clicks (5.08% CTR), and 1 conversion, directionally right, but Google still rates the ad **AVERAGE** and Ad Relevance on the core keywords (`roll off dumpster`, `roll off dumpster rental brightwater`) is still **Below Average**. Expected CTR is Above Average and Landing Page Experience is Average, so the copy fix is specifically about **Ad Relevance and thematic diversity**, not hooks or LP alignment.

The current 15 headlines are heavily repetitive, 13 of 15 contain "Roll Off," which triggers Google's redundancy penalty and keeps ad strength at AVERAGE. The fix is to keep core-keyword density high enough to preserve Ad Relevance (search terms show people are searching `roll off dumpster rental`, `roll off dumpster rental brightwater`, `roll off dumpster rental service`, `same day roll off dumpster`) while adding real diversity across size, use case, price, trust, and CTA angles.

### RSA Headlines (Campaign: Brightwater Dumpster Rentals → Ad Group: Roll Off Dumpster)

| # | Headline | Angle | Chars |
|---|----------|-------|-------|
| 1 | Roll Off Dumpster Rental | Core service (pin to H1) | 24 |
| 2 | Roll Off Dumpsters Brightwater | Core + geo | 30 |
| 3 | {KeyWord:Roll Off Dumpster} | DKI, matches query language |, |
| 4 | Same-Day Roll Off Delivery | Urgency + core | 26 |
| 5 | 10, 20, 30 & 40 Yard Roll Offs | Size menu (full) | 30 |
| 6 | Rent a Roll Off in Brightwater | Core + geo variant | 30 |
| 7 | 40 Yard Roll Off Dumpsters | Largest size (search term signal) | 26 |
| 8 | Demo & Construction Debris | Use case, heavy jobs | 26 |
| 9 | Heavy Material Roll Offs | Use case, dirt/concrete/debris | 24 |
| 10 | Roofing, Remodel, Cleanouts | Use case, residential jobs | 27 |
| 11 | Flat-Rate, No Dump Fees | Pricing transparency | 23 |
| 12 | Transparent Upfront Pricing | Pricing trust | 27 |
| 13 | Locally Owned in Brightwater | Trust + local | 28 |
| 14 | Book Online in 2 Minutes | CTA, digital path | 24 |
| 15 | Call for Instant Pricing | CTA, phone path | 24 |

### RSA Descriptions (Campaign: Brightwater Dumpster Rentals → Ad Group: Roll Off Dumpster)

| # | Description | Chars |
|---|-------------|-------|
| 1 | Roll off dumpsters for demo, construction & cleanouts in Brightwater. 10-40 yd sizes. | 85 |
| 2 | Same-day Brightwater delivery. Flat-rate pricing, no hidden dump fees. Family-owned. | 84 |
| 3 | Open-top roll offs for heavy debris, dirt, concrete, demo & construction cleanup. | 81 |
| 4 | Book online in under 2 minutes or call for instant pricing. On-time delivery every time. | 88 |

### Pin Recommendations

- **Pin Headline 1 ("Roll Off Dumpster Rental") to H1 only.** This guarantees the core keyword is always in the top slot, which directly addresses the Below Average Ad Relevance. Do not pin H2, H3, or any description, let Google test combinations so ad strength can climb to GOOD/EXCELLENT.
- Keep the DKI headline (#3) unpinned so it rotates naturally into H1/H2/H3 depending on the query.

### Extensions

#### Sitelinks (add at the ad group level if not already present)

| Title | Desc 1 | Desc 2 | URL |
|-------|--------|--------|-----|
| Roll Off Dumpster Sizes | 10, 20, 30 & 40 yard open-top | roll-off containers available. | /roll-off-dumpsters |
| Get an Instant Quote | Upfront flat-rate pricing | with no hidden dump fees. | /quote |
| Demo & Construction Bins | Heavy debris, dirt, concrete | & construction site cleanups. | /construction |
| Residential Cleanouts | Home remodels, estate cleanouts | & roofing jobs made simple. | /residential |

#### Callouts

"Same-Day Delivery" | "Flat-Rate Pricing" | "No Hidden Dump Fees" | "Family-Owned" | "Locally Operated" | "On-Time Delivery & Pickup" | "Licensed & Insured" | "5-Star Rated"

#### Structured Snippets

**Header:** Services
**Values:** Roll Off Dumpsters, Construction Cleanup, Demo Debris Removal, Concrete & Dirt, Residential Cleanouts, Roofing Debris

### Implementation Notes

- **Add this as a new RSA alongside the existing 4/17 RSA, do NOT pause the current one immediately.** Let both serve for 10–14 days so Google can compare. After that window, whichever is winning on CTR and conversions stays; the other pauses.
- **Ad Relevance improvement will show on the QS breakdown at the keyword level**, not inside the RSA itself. Watch "roll off dumpster" and "roll off dumpster rental brightwater" in next week's keyword report, we want to see Ad Relevance move from Below Average to Average.
- **Expect ad strength to climb to GOOD** with these 15 headlines (much more thematic diversity), but Google's rating is not deterministic, if it stays AVERAGE, the headline set can still outperform the current one on CTR and relevance, which is what actually matters.
- **Character counts are verified**, all headlines ≤ 30 chars, all descriptions ≤ 90 chars.
- **Dispatch to change-scripts skill is next**, this copy is staged to be turned into a `AdsApp.newResponsiveSearchAdBuilder()` call in a one-time Google Ads Script (dry-run first, as always).
