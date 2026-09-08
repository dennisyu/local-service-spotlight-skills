# Business Models — the router taxonomy (works for any small business)

**Tags:** #framework #ga4 #router #any-business

The five models the router picks from. Every small business maps to one **primary** model (money action) plus an optional **secondary**. This file defines, per model: how to detect it, what the primary conversion is, the candidate event patterns, the report's dimensional lens (what replaces the local "cities" view), the client-facing name for the number, which local-only modules apply, and the model-specific gotchas. The rest of the skill (data trust, Data Clarity, swing decomposition, report voice, QA) is identical across all models.

**There is no "out of scope."** If detection is ambiguous, pick the best-supported model, mark the conversion PROPOSED, produce a full report, and ask the owner to confirm what counts as a conversion. Never reject a business.

## Detection (run in this order)

1. **`industry_category`** from `get_property_details` (always read it; decisive on low-data properties): `SHOPPING` → e-commerce. `BUSINESS_AND_INDUSTRIAL_MARKETS`, `JOBS_AND_EDUCATION`, media/publishing → usually audience or lead-gen. `TRAVEL`, `FOOD_AND_DRINK`, `HEALTH` local storefronts → often lead-gen local.
2. **Event inventory (Q1)**: `purchase`/`add_to_cart`/`begin_checkout` → e-commerce. `subscribe`/`sign_up`/`newsletter`/`registration` as the main action → audience. `donate`/`donation` → donation. call/quote-form/booking events → lead-gen. `trial_start`/`subscription`/`enrollment` → membership.
3. **Page paths (Q5)**: `/product`, `/shop`, `/cart` → e-commerce. `/subscribe`, `/newsletter`, hashed post slugs → audience. `/donate`, `/give` → donation. `/join`, `/enroll`, `/pricing`, `/members` → membership. `/services`, `/contact`, `/quote`, `/book` → lead-gen.
4. **Local test (decides the local modules, independent of model):** does the business have a bounded service area (a metro, a set of cities, a physical storefront)? Signals: service-area pages, city landing pages, a GBP, leads concentrated in one metro. If yes → local modules ON. If national/online → local modules OFF.

Blend rule: a plumber with a newsletter is **lead-gen primary + audience secondary**. An author selling a course is **audience primary + membership secondary**. Headline the primary; put the secondary on its own line.

---

## 1. Lead-gen (local service, B2B, high-ticket coaching)
- **Primary conversion:** an inquiry. Calls (`click_to_call`, `first_time_phone_call`, call-tracker events), contact/quote form submits, bookings, qualified chat.
- **Secondary:** newsletter/giveaway/popup captures, chat starts.
- **Report name:** "leads."
- **Lens:** channels → pages → **cities** (local) OR channels → pages → source detail (national B2B).
- **Local modules:** YES if bounded service area (this is the original skill path; cities W&O, spam-screen, GBP all apply).
- **Gotchas:** all of the existing integration-behaviors.md (call touchpoint rule, booking-tool self-referral, GBP limits). This is the fully-worked model; the exemplar (RDR) is here.

## 2. E-commerce (DTC, retail, catalog)
- **Primary conversion:** `purchase` (carry `purchaseRevenue`, `transactions`, and derive AOV = revenue/transactions).
- **Secondary:** email/SMS capture (`sign_up`, `generate_lead` on a popup).
- **Report name:** "sales" / "orders" (with revenue and AOV).
- **Lens:** channels (by revenue, not just sessions) → **top products** (`itemName`, `itemsPurchased`, item revenue) → **checkout funnel** (`view_item` → `add_to_cart` → `begin_checkout` → `purchase`, report the biggest drop-off step).
- **Local modules:** NO (national shipping) unless there's local pickup/a storefront.
- **Gotchas:** (a) **purchase ≠ settled revenue** — GA4 counts the online transaction; refunds/failed payments/COGS aren't here, so say "online sales," never "revenue you kept." (b) **Checkout/payment self-referral** is the same bug as the booking-tool overwrite (C8): a payment processor or checkout subdomain (`checkout.*`, `shop.*`, PayPal, Stripe, Shopify checkout) overwrites the true source → referral-exclusion action. (c) Watch double-counted `purchase` on thank-you-page reloads. (d) Repeat vs new customer matters for growth read (use `newVsReturning`).

## 3. Audience / list-building (authors, creators, coaches, personal brands, newsletters)
- **Primary conversion:** a signup/subscribe/registration (`sign_up`, `newsletter_signup`, `subscribe`, `webinar_registration`, `lead_magnet_download`).
- **Secondary:** a low-ticket purchase or a coaching/inquiry contact.
- **Report name:** "subscribers" / "signups" / "registrations."
- **Lens:** channels → **top content** (which posts/pages pull the audience, `pagePath` by sessions AND by signups) → **signup sources** (which channel/content converts to a signup). Content engagement (scroll, video, time) is context, never the headline.
- **Local modules:** NO (national/global audience).
- **Gotchas:** (a) **Content-engagement events are routinely mis-flagged as key events** (`homepage`-fires-on-every-pageview, `time_on_site`, `*_min`, `five_minutes_on_site`) — these are Micro, and when flagged they drive C7 dilution to ~90%; report the real signup count and flag the mis-registration. (b) A "signup" page with traffic but **no completion event** = untracked signups (same logic as form_start-without-submit) → verification action. (c) Email channel traffic is usually *returning* subscribers, not new signups — don't read it as acquisition.

## 4. Membership / course / subscription (memberships, online courses, SaaS trials)
- **Primary conversion:** an enrollment / trial start / paid subscription start (`enroll`, `trial_start`, `subscribe`, `purchase` of a membership SKU, `begin_checkout` on `/join`).
- **Secondary:** free lead magnet or waitlist signup (audience-style).
- **Report name:** "members" / "enrollments" / "trials."
- **Lens:** channels → **offer/pricing pages** → **enrollment funnel** (pricing/offer view → checkout → enrollment; report the drop-off).
- **Local modules:** NO.
- **Gotchas:** (a) distinguish **free trial** from **paid conversion** — count them separately, never blend a free-trial number into a paid-member headline. (b) Recurring-billing events can fire monthly on existing members — only the *start* is a new conversion, not each renewal (renewal = existing customer, like `repeat_phone_call`). (c) Checkout self-referral (C8) applies (Teachable/Kajabi/Stripe/Podia domains).

## 5. Donation / advocacy (nonprofits, media, advocacy)
- **Primary conversion:** a donation (`donate`, `donation`, a `purchase` with revenue on `/give`), or a completed advocacy action (petition, contact-legislator, volunteer signup).
- **Secondary:** newsletter/email list growth.
- **Report name:** "donations" / "actions" (donations with amount if revenue present).
- **Lens:** channels → **campaigns/appeals** (UTM campaign, appeal landing pages) → top content driving the action.
- **Local modules:** NO (national/global) unless a local chapter.
- **Gotchas:** (a) **A donate-button click is intent, not a completed donation** — if only a button-click event exists and no completion/thank-you event, donations are untracked; report intent as intent and flag the gap. (b) Donation processors (Classy, Donorbox, Fundraise Up, PayPal) are checkout self-referrals (C8). (c) Content/video engagement dominates a media nonprofit and is context, not the conversion (C7 dilution risk, same as audience).

---

## What stays identical across every model
Pre-flight and dead-tag checks, the Data Clarity table (C1–C9 — attribution fog, bot floods, dilution, self-referral overwrite, capture gaps), the bot/datacenter-city data-quality screen (applies to national businesses too), swing decomposition with comparison integrity, the report voice (plain English, machinery hidden, human-sounding, no em-dashes), and the QA gate. Only the **conversion definition** and the **dimensional lens** change by model. Route once, then run the same machine.
