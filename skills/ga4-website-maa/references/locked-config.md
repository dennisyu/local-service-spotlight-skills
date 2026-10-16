# Locked-Config — the portable per-client spec

**Tags:** #framework #ga4 #config #recurring

The durable facts a **Recurring Re-Run** needs, in one small file that travels with the client — so a weekly owner-facing run never needs the full agency vault. First-Run seeds it; every run may append to `open_questions` and `run_history`, but the locked fields change only through a team-reviewed First-Run. It is the contract the tripwire gate checks against: a Recurring run compares this week's pull to the locked-config, and any material divergence trips a tripwire (`tripwires.md`).

Save at `{client_vault}/{client}/locked-config-ga4.md` (canonical) and hand a copy to whatever runs the owner-facing pulse. Keep it human-readable; keep secrets (raw IDs) in the private vault if the owner copy must be shareable.

## Fields

```yaml
client: Ridgeline Dumpster Rental
business_model: lead-gen         # lead-gen | ecommerce | audience | membership | donation (see business-models.md)
model_secondary: none           # optional second model (e.g. audience) reported on its own line
is_local: true                  # true → cities/GBP/spam-screen modules run; false → use the model's lens, no cities/GBP
conversion_name: leads          # the client-facing word for the headline number (leads/sales/subscribers/members/donations)
mode_ready: recurring            # recurring | first-run-only (not yet validated) | escalated (Phase 0 no-data/tracking-gap — do NOT run until fixed)
locked_on: 2026-07-22
locked_by: <team member>

property:
  live_id: 100200301
  known_ghosts: [100200302]      # pre-flight must NOT switch back to these
  timezone: America/Los_Angeles
  currency: USD

lead_events:                     # THE locked classification — pattern table & GA4 flag do not override this
  case:
    - name: call_clicks
      type: on_site_click        # on_site_click | call_tracker | form | booking | chat | text
      note: on-site click-to-call — has a web touchpoint; touchpoint/CallRail apparatus does NOT apply
    - name: confirmed_booking
      type: booking
    - name: rental_form
      type: form
  list_building: []              # reported on their own line, never in the lead headline
  existing_customer: []          # e.g. repeat_phone_call — never a new lead
  micro_ignore: [video_progress, video_start, page_view, session_start, first_visit, user_engagement, video_complete, scroll, click, view_search_results]

service_area:
  cities: [Columbus, Bexley, Powell, Delaware, Gahanna, Worthington, Reynoldsburg, Pickerington, Marysville, Whitehall, New Albany]
  out_of_area_leads: reclassify_franchise   # spam | reclassify_franchise | reclassify_other:<label>
  out_of_area_note: business sells franchises nationally; out-of-state inquiries are franchise interest, not spam

known_integrations:
  booking_tool:
    domain: app.bookflow.io
    behavior: cross-domain self-referral overwrites true source (C8)
    fix: GA4 referral exclusion ("List unwanted referrals")
    fix_status: NOT_APPLIED        # NOT_APPLIED | APPLIED:<date> | VERIFYING
    last_checked: 2026-07-22
  call_tracker: none               # on-site click event only — no vendor tracker
  gbp_link: unknown

baselines:                         # what "normal" looks like — tripwire thresholds read these
  headline_leads_prior: 75         # last locked/known-good period (through 2026-06-24)
  lead_mix_prior: {calls: 40, bookings: 28, forms: 7}
  clean_lead_rate: 0.044           # site blended form/booking-attributable rate for expected-vs-actual math
  direct_share_normal: 0.20        # for an established business much Direct = repeat; watch elevation vs this
  data_clarity_baseline: hazy      # clear | hazy | opaque — a DROP below this trips a tripwire

open_questions:
  - CRM access still pending (lead-quality validation) — carried from Ads Narrative.
run_history:
  - {date: 2026-07-22, mode: first-run(validation), headline_leads: 49, clarity: hazy, escalated: false}
```

## Rules

- **Locked fields** (property, lead_events, service_area, known_integrations, baselines) change **only** through a team-reviewed First-Run. A Recurring run reads them; it never edits them.
- **Appendable fields** (open_questions, run_history, and `fix_status`/`last_checked` when a run verifies a fix) may be updated by any run.
- A field you cannot fill on First-Run gets `unknown` and becomes an `open_question` — never a guess.
- If `mode_ready` is `first-run-only`, Recurring mode is disabled until a First-Run validates and flips it to `recurring`.
- The locked lead classification here **wins** over the pattern table and the GA4 key-event flag (per SKILL Phase 2). This file is the single source of truth for what counts as a lead for this client.
