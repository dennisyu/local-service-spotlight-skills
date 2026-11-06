# Daily check queries (Google Ads MCP, `search` tool)

Same call shape as the main query pack. `{YESTERDAY}` is the last full day in
the account's timezone (check `customer.time_zone`; some accounts run on an
odd zone). `{D7}` is yesterday minus 6 days, `{D35}` yesterday minus 34, `{D90}` yesterday minus 89. Money
in micros, shares as 0 to 1 fractions. Paginate; record counts.

## 0. Account timezone and status
```
resource:   customer
fields:     customer.id, customer.descriptive_name, customer.time_zone, customer.status
```

## 1. Disapprovals and policy

Ads
```
resource:   ad_group_ad
fields:     campaign.name, campaign.status, ad_group.name, ad_group.status,
            ad_group_ad.ad.id, ad_group_ad.status,
            ad_group_ad.policy_summary.approval_status,
            ad_group_ad.policy_summary.review_status,
            ad_group_ad.policy_summary.policy_topic_entries
conditions: ad_group_ad.policy_summary.approval_status IN ('DISAPPROVED', 'AREA_OF_INTEREST_ONLY')
            campaign.status = 'ENABLED'
            ad_group.status = 'ENABLED'
            ad_group_ad.status = 'ENABLED'
```
Diff against yesterday's saved result; report new entries as RED, unchanged as "still open".

Assets (sitelinks, callouts, images, call assets)
```
resource:   campaign_asset
fields:     campaign.name, asset.id, asset.type, asset.name,
            campaign_asset.status, campaign_asset.primary_status,
            campaign_asset.primary_status_reasons
conditions: campaign_asset.primary_status IN ('LIMITED', 'NOT_ELIGIBLE')
            campaign.status = 'ENABLED'
```
Repeat on `ad_group_asset` with the same fields.

Campaign primary status (covers policy, billing, verification, ended; `campaign.start_date` and `campaign.end_date` are not selectable through this MCP, so PENDING-past-start is judged from `primary_status_reasons`)
```
resource:   campaign
fields:     campaign.id, campaign.name, campaign.status, campaign.serving_status,
            campaign.primary_status, campaign.primary_status_reasons
conditions: campaign.status = 'ENABLED'
```
Exception only when `primary_status_reasons` contains POLICY, BILLING, VERIFICATION, SUSPENDED, ACCOUNT or ENDED, or `primary_status` is NOT_ELIGIBLE or MISCONFIGURED. `LIMITED` with `BUDGET_CONSTRAINED` or `LEARNING` is normal and is not an exception. `HAS_ADS_DISAPPROVED` alone is not an exception unless the ads query above returned an ENABLED disapproved ad.

## 2. Serving

Daily impressions, 35-day window, campaign and ad group level
```
resource:   ad_group
fields:     segments.date, campaign.id, campaign.name, campaign.status,
            ad_group.id, ad_group.name, ad_group.status,
            metrics.impressions, metrics.cost_micros
conditions: segments.date BETWEEN '{D35}' AND '{YESTERDAY}'
            campaign.status = 'ENABLED'
            ad_group.status = 'ENABLED'
```
First remove scheduled dark days (section 2.5). Rule 2(a): mean impressions over the prior 7 scheduled days >= 10 and YESTERDAY = 0. Rule 2(b), no volume floor: count consecutive zero-impression scheduled days ending yesterday; if 7 or more, and the 28 days before the run of zeros had impressions on at least 4 days AND at least 20 impressions in total, report (YELLOW at 7, RED at 14). Cross-check the ledger change log for deliberate pauses before reporting either.

## 2.5 Ad schedule (for the dark-day suppression rule)
```
resource:   campaign_criterion
fields:     campaign.name, campaign_criterion.ad_schedule.day_of_week,
            campaign_criterion.ad_schedule.start_hour, campaign_criterion.ad_schedule.end_hour
conditions: campaign_criterion.type = 'AD_SCHEDULE'
```
A weekday absent from the schedule is a scheduled dark day. Confirm against the 35-day impressions series (same weekdays at zero for 3 or more weeks) and record in the ledger.

## 3. Budget

Budget and daily spend and IS lost. Impression-share metrics settle for 24 to 48 hours; recompute the 3-consecutive-day test from this pull every day and never carry a saved value forward.
```
resource:   campaign
fields:     segments.date, campaign.id, campaign.name,
            campaign_budget.amount_micros, campaign_budget.delivery_method,
            metrics.cost_micros, metrics.search_budget_lost_impression_share
conditions: segments.date BETWEEN '{D7}' AND '{YESTERDAY}'
            campaign.status = 'ENABLED'
```
Exceptions: budget-lost IS > 0.25 on a ledger-primary campaign on each of the last 3 days (ledger or roster may set a different bar); cost > 2 x budget on each of the last 3 days; YESTERDAY cost < 0.2 x budget where the MEDIAN cost over D7..D2 was >= 0.5 x budget. Google may spend up to 2x daily budget on any single day; one day is never an exception.

## 4. Tracking

Conversion action status
```
resource:   conversion_action
fields:     conversion_action.id, conversion_action.name, conversion_action.status,
            conversion_action.primary_for_goal, conversion_action.type,
            conversion_action.include_in_conversions_metric
```
Scope = ledger-named lead actions plus ENABLED `primary_for_goal = true` actions with `include_in_conversions_metric = true`. Exception 4(c): an in-scope action whose status is PAUSED. Ignore REMOVED actions entirely. Out-of-scope actions (GOOGLE_HOSTED, include_in_conversions_metric false, secondary) are never graded.

Conversions by action by day, last 90 days
```
resource:   campaign
fields:     segments.date, campaign.name, segments.conversion_action_name,
            metrics.all_conversions, metrics.cost_micros
conditions: segments.date BETWEEN '{D90}' AND '{YESTERDAY}'
            campaign.status = 'ENABLED'
```
Rows segmented by `segments.date` are dated by the click, not the call or booking; for call timing use `call_view.start_call_date_time`. Use `metrics.all_conversions`, not `metrics.conversions`: the latter silently omits any action with include_in_conversions_metric false, which can include ledger-named leads (click_to_call on one account, call_clicks on another). Scope to the actions the ledger names as leads plus ENABLED primary actions with include_in_conversions_metric true. Where the ledger defines an action group, sum the group's fires into one series first. For each: last fire date; count of fires in 90 days; median gap in days between fires; number of spend days (cost > 0 on its campaigns) since the last fire. Stop rule 4(a), no volume floor: fired at least once in 90 days and 14 or more spend days since the last fire, RED. Silence rule 4(b): 10 or more fires in 90 days and days since last fire >= N where N = max(3, 3 x median gap); YELLOW at N, RED at 2N. Never fire on an action that fired in the last 3 days.

## 5. Landing pages

Active final URLs
```
resource:   ad_group_ad
fields:     campaign.name, ad_group.name, ad_group_ad.ad.id, ad_group_ad.ad.final_urls
conditions: campaign.status = 'ENABLED'
            ad_group.status = 'ENABLED'
            ad_group_ad.status = 'ENABLED'
```
Plus keyword-level overrides (`IS NOT NULL` is rejected on this field; pull all enabled keywords and keep the rows whose final_urls is non-empty client-side):
```
resource:   ad_group_criterion
fields:     campaign.name, ad_group.name, ad_group_criterion.keyword.text, ad_group_criterion.final_urls
conditions: campaign.status = 'ENABLED'
            ad_group.status = 'ENABLED'
            ad_group_criterion.status = 'ENABLED'
            ad_group_criterion.type = 'KEYWORD'
```
Dedupe the URL set (usually under 10 per account). The shell sandbox has no outbound network; check URLs through the browser. Navigate to each URL and read the final URL and title; a cross-origin `fetch` from another page returns "Failed to fetch" and looks like a dead site when it is not. Record status code (from the network log), redirect chain, final URL. Compare registrable domains (eTLD+1), not hostnames: www to apex, http to https and trailing-slash changes on the same domain are not exceptions. RED on 4xx/5xx/timeout, on a redirect to the site root, or on a redirect to a different registrable domain; YELLOW on a same-domain redirect to a different non-root path. Strip UTM parameters before comparing. Save the URL set so tomorrow's run diffs against it.

## Persistence

Required top-level keys, every day, explicit empty arrays when a check finds nothing: `disapproved_ads`, `limited_assets`, `campaign_status`, `serving_daily`, `budget_daily`, `conversion_actions`, `conversions_by_action_daily`, `final_urls`, `dark_day_pattern`, `row_counts`. Save each day's raw results to `{OUTPUT_DIR}/{client}/raw/daily/YYYY-MM-DD.json` so "new vs still open" is a diff, not a memory. Keep 30 days.
