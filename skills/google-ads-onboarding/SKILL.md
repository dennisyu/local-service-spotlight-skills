---
name: google-ads-onboarding
description: >
  Onboard a new Google Ads client into the weekly MAA system in one run: verify access, scrape the account's full history (12 to 24 months, all statuses, inherited state), investigate the website and landing pages, research the real geographic footprint, package the questions only the client can answer, and bootstrap the client folder with a compact ledger the weekly drafter reads first. Trigger on "onboard [client]", "set up [client] for the MAA", "new Google Ads client", "first run for CID [digits]", "bootstrap the ledger for [client]", or any request to take over an existing Google Ads account. Runs once per client, before the first weekly MAA. Google Ads only; LSA is inventoried but not analyzed.
---

# Google Ads Onboarding

## What this skill does

Turns a CID and a website into a client folder the weekly MAA can run against with almost no human context. It produces one ledger, one onboarding brief for the agency lead, and one intake ask for the client. It writes no MAA and recommends no account changes except foundation breaks.

The reason this exists: the first two or three weekly cycles on a new account are where the analyzer over-reacts most, because it has no history, no definitions and no record of what was inherited. This skill front-loads that memory so cycle one behaves like cycle ten.

## What this skill never does

- Change the account. The MCP is read-only; nothing here ships a script.
- Recommend optimizations. Foundation breaks (tracking not firing, geo leaking, disapprovals, billing) are flagged. Everything else goes on the watch list with a first-seen date.
- Guess a definition. Lead definition, target CPL, seasonality and service exclusions come from the client or are marked (verify) and listed in the intake ask.
- Post, email or send anything.

## Inputs

Required: client name, CID (digits), website URL.
Wanted: MCC, primary contact name and role, Basecamp project, any prior agency notes, target CPL if already stated, GA4 property ID.

If the CID is unknown, run `list_accessible_customers` on the MCP, match by account name, and confirm with the user before proceeding. Never proceed on a guessed CID.

## Procedure

Work the phases in order. Each phase writes its findings into the working brief as it goes, so a stalled run still leaves a usable partial.

### Phase A. Access and inventory (10 minutes)

1. MCP reachable, CID under the MCC, campaign names returned belong to this client.
2. Inventory every campaign regardless of status: name, type (`advertising_channel_type`), status, bid strategy (translate API enums to UI names), daily budget from `campaign_budget`, start date, last day with spend. Mark LSA, PMax, Video and Display separately. LSA is recorded as present and left out of everything downstream.
3. Conversion actions: `conversion_action` with name, category, type, status, primary/secondary, counting (one per click or many), click-through window, source (website, GA4 import, call asset, LSA). Note creation dates where visible. This is the raw material for the lead definition.
4. Billing and policy: account status, any `ad_group_ad.policy_summary` disapprovals or limited-by-policy assets, any campaign flagged as not serving.
5. Assets: call assets and their numbers, location assets and the linked GBP, sitelinks. Record every phone number found; phone-number drift between assets, site and GBP is a common inherited fault.

Foundation breaks found here go to the top of the brief.

### Phase B. Historical account scrape (20 minutes)

Pull with the MCP, save the raw response to `raw/google-ads/YYYY-MM-DD_onboarding-pull.json` verbatim before abridging anything. Use `segments.month` for the long view and `segments.week` for the trend file. Every query on `keyword_view`, `ad_group_criterion`, and negatives runs with NO status filter and is paginated until the returned count is below the cap; record the count.

1. **Monthly campaign performance, 24 months** (or account lifetime if shorter): cost, impressions, clicks, CTR, CPC, conversions, cost per conversion, search IS, budget-lost IS, rank-lost IS. Produces the "what has this account done" table and exposes seasonality.
2. **Monthly conversions by action name, 24 months.** Shows which actions carried volume and when an action started or stopped firing. A conversion action that stopped 6 months ago is a tracking break that predates you.
3. **Weekly campaign performance, last 13 weeks.** Backfills `compiled/trend.csv` so the first client view has a chart.
4. **Keyword inventory, all statuses**, with QS and components, 90D metrics, match type, final URL override. Separate ENABLED from PAUSED from REMOVED and record when known. Anything paused before the engagement start is "inherited paused, not ours" in the ledger.
5. **Negative keywords**: campaign-level, ad-group-level, and shared lists, paginated. Count them. Flag any negative that blocks a service the website says the client offers.
6. **Search terms, 90D**, by cost. Bucket: core service, geo-modified, competitor and brand names, off-service, out-of-area, jobs and DIY. Do not build a negative list; record the buckets and their spend share.
7. **Ads, all statuses**: RSA headlines, descriptions, strength, final URL, pinned fields, 90D metrics. Note ad groups with one RSA, ads with Poor or Average strength, and any final URL that does not resolve (checked in Phase C).
8. **Change history, 90D**, via `change_event` in 30-day slices with an explicit date range and limit. Known to be unreliable on some MCP builds; if it fails, say so in the brief and infer recent changes from budget, status and bid strategy differences instead. Never treat an empty result as "no changes."
9. **Geo targeting settings**: every campaign's location criteria, presence vs presence-or-interest, excluded locations, radius targets. **Geo performance, 90D**: `user_location_view` and `geographic_view` by city, cost and conversions. Feed Phase D.
10. **Device and network, 90D**: split by device and by network (Search, Search Partners, Display expansion). Record whether partners and display are on and what they cost per conversion.
11. **Ad schedule and bid adjustments** per campaign.
12. **Call data, 90D**: `call_view` counts and durations if call assets exist. Compute counted calls (60s+) vs total.

Derive from the pull:
- the account's monthly CPA range and its best and worst months;
- the QS anchor: the highest-spend scored keyword and its three component reads;
- the inherited-state list: everything paused, removed or dormant before the engagement start;
- the budget-binding read: how often budget-lost IS exceeded 10% on a daily basis in the last 30 days.

### Phase C. Website investigation (15 minutes, Claude in Chrome)

1. Home page: business name as written, phone number(s), address(es), CMS (view source for generator tag or platform fingerprints), form provider, chat widget.
2. Services: list every service page. Compare against the campaign and ad group inventory. Services advertised but absent from the site, and services on the site with no campaign, both go in the brief.
3. Service area: the site's own statement (page, footer, schema `areaServed`). Record counties and cities verbatim. This is the primary input to Phase D.
4. Landing pages: open every distinct final URL from Phase B. Record status code, redirect chain, whether the page matches the ad group's service, phone number on the page, form presence, page title. A 404 or a redirect to the home page is a foundation break.
5. Tracking: dispatch the `tag-audit` skill on the home page and on two landing pages (one per top campaign). Record GTM container, GA4 measurement ID, Google Ads conversion tag presence, call-tracking provider (DNI swap present or not), and any duplicate tag stacks.
6. GBP: find the listing(s), record the phone and address and whether they match the site and the call asset.
7. Reviews: count and rating as displayed on the site and on GBP. Record both; never quote the higher one without the source.
8. Language: note any non-English pages or bilingual copy; it changes the language-targeting question.

### Phase D. Geographic footprint (10 minutes)

Produce one service-area test the ledger can apply mechanically.

1. Start from the site's stated area (Phase C.3). Normalize to counties where the site gives counties, otherwise to a city list.
2. Overlay the 90D geo performance from Phase B.9: where do impressions, clicks and conversions actually come from? List cities with spend that fall outside the stated area, and stated-area cities with zero impressions.
3. Overlay the campaign geo settings: targeted locations vs stated area vs actual spend. Three-way mismatches are the finding.
4. Distance check: the yard or office address from the site to the furthest converting city, and the furthest targeted city. A targeted radius that reaches a different metro is a question, not a negative.
5. If the site is silent, use GBP service area and, failing that, the conversion geography, and mark the whole test (verify).
6. Output: `Service area test` block for the ledger with three lists: in area (do not negate), out of area (negate on sight, zero-cost terms logged only), undecided (ask the client). Name the source of each entry.

Do not use campaign or account names as evidence of footprint. Names lie; settings and spend don't.

### Phase E. Human intake (5 minutes to write, days to get back)

Package the questions only the client can answer into one message the agency lead can forward. Keep it to the items the data could not settle. Typical set:

1. What counts as a lead for you: calls over N seconds, form fills, booked jobs, quotes? Which of these do you track, and where (CRM, booking software, phone log)?
2. What is a good cost per lead, and over what period do you judge it?
3. Which services on your site do you NOT want ads for, and which do you offer that the site does not show?
4. Service area: confirm the in-area and undecided lists from Phase D.
5. Seasonality: which months are busy and slow, and any known events (weather, rebrand, site changes, price changes) in the last 12 months that would explain the monthly table.
6. Competitor names you want blocked, and any you are fine appearing against.
7. What has been tried before that you do not want repeated.
8. Who reviews the weekly report and who makes decisions.
9. Can we get read-only access to the CRM or booking system for lead-outcome checks?

Everything in this list also goes into the ledger's Open ASKs with today's date so the weekly run carries it until answered.

### Phase F. Bootstrap the client folder

If the vault has `clients/_template/`, copy it to `clients/<slug>/`. Then write:

1. **`compiled/ledger.md`** with the ten standard sections. This is the deliverable the weekly drafter depends on. Section by section:
   - 1 Identity and access: from Phase A and C.
   - 2 Definitions: lead definition from conversion actions, marked (verify) until the client confirms; target CPL (verify); primary campaigns; windows (7D, 30D, Friday to Thursday unless the spec says otherwise); QS anchor from Phase B; networks and devices that matter from Phase B.10; service area test from Phase D.
   - 3 Standing rules: the house rules from `clients/_shared/` plus any account-specific rule already evident (for example "brand and non-brand are mixed, treat blended CPA as flattered").
   - 4 Change log: engagement start date as the first row, then the inherited-state list dated "before engagement", then anything `change_event` returned.
   - 5 Watch list: every observation from Phases B to D that is not a foundation break, first-seen today, cycles observed 0.
   - 6 Open ASKs: the Phase E list, dated today.
   - 7 Recent-change quarantine: the whole account for two cycles. No non-foundation Action in cycle one or two. Exit date = engagement start + 14 days.
   - 8 Render spec: house defaults from the client-view skill and the binding until the lead sets client-specific norms.
   - 9 Weekly log: the 13 weekly rows from Phase B.3.
   - 10 Known data faults: anything that failed or capped during this run, plus the cross-client faults from `clients/_shared/google-ads-data-contract.md`.
2. **`compiled/data-sources.md`**: CID, MCC, GA4 property, GTM container, call-tracking provider, email pipeline subject string if one will exist.
3. **`compiled/maa-metric-spec.md`**: copy the default section order from the analyzer; note LSA excluded; leave voice conventions at house default.
4. **`compiled/lp-map.md`**: ad group to final URL to status code to page match, from Phases B.7 and C.4.
5. **`compiled/trend.csv`**: 13 weekly rows, `week,leads,cpl_week,cpl_30d`.
6. **`compiled/account-history.md`**: the 24-month monthly table, conversions by action by month, and the derived reads (CPA range, seasonality, inherited state, budget binding).
7. **`client-knowledge-base.md`**: fill what Phases A and C established; mark the rest as open questions.

### Phase G. The onboarding brief

Write `deliverables/YYYY-MM-DD-onboarding-brief.md` for the agency lead, in this order, kept under two pages:

1. Foundation breaks, if any, each with the evidence line and the fix owner. These are the only items that may be phrased as actions.
2. What the account has done: three sentences on the monthly table (CPA range, volume, seasonality) and the conversion actions that carried it.
3. What was inherited: paused and removed inventory, dormant campaigns, negatives that block offered services, tracking that stopped.
4. The three-way geo read: stated area, targeted area, actual spend.
5. Website and landing page state, including the tag audit summary.
6. Watch list preview: the five observations most likely to become actions after two clean cycles, with the evidence each needs.
7. The intake ask, ready to forward.
8. Data faults hit in this run and what was unpullable.

Also write `deliverables/YYYY-MM-DD-weekly-task-prompt.md`: the standard
five-stage weekly prompt from `references/weekly-task-template.md` with every
placeholder filled from the ledger (CID, MCC, vault path, email subject, lead
unit, opening rule, scope notes). The operator pastes it into a new scheduled
task named `maa-{slug}` when the brief is reviewed; nothing here creates the
task. Say in the brief which placeholders were filled from a `(verify)` fact.

Then finish with a chat summary of at most eight lines: CID confirmed, campaigns live, foundation breaks count, lead definition status (confirmed or verify), service area status, files written, whether the weekly task prompt is ready to paste, and the date the quarantine exits.

## Evidence rules that apply here

- 90 days is the minimum window for any keyword or search-term judgement recorded on the watch list. 30-day reads are not recorded.
- Nothing below 30 clicks or 5 conversions is described as performing or failing. Record the counts and move on.
- Every number in the brief cites the dataset it came from. Every claim about the account's past cites a month or a date.
- "The account name says X" is never evidence.
- If a pull returned exactly its cap, the brief says the dataset is partial and no absence claim rests on it.
- The ledger marks every unconfirmed fact (verify). The weekly drafter treats (verify) facts as usable but not as grounds for an Action.

## Handoff

The weekly MAA scheduled task for the client is created only after the brief is reviewed by the agency lead and the intake answers are in the ledger, or after the quarantine exits, whichever comes first. The task prompt reads `compiled/ledger.md` first, per the standard prompt in the suite's onboarding guide.
