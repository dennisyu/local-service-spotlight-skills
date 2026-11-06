# Google Ads GAQL Query Pack (MCP data pull)

> The reusable queries that reproduce every MAA dataset live from a **Google Ads
> MCP** connector (tool: `search`, GAQL). This is the **primary** data source;
> the `maa-data-automation` email is the fallback. See
> `data-pipeline-contract.md` for the source-priority rules.

## How to call

The MCP `search` tool takes: `customer_id` (CID, digits only, no dashes),
`resource`, `fields` (list), `conditions` (list, AND-combined), optional
`orderings`, `limit`. Record each client's CID once in your per-client config
(see CONFIGURATION.md) so runs don't start with a lookup.

If your MCP server sits under an MCC (manager account), the login customer id is
typically baked into the server config; pass the child account's CID as
`customer_id`.

**The MCP is read-only.** The `search` tool is GAQL reporting only. It cannot
mutate the account, negatives, pauses, bid and budget changes all go through
Google Ads change scripts (`google-ads-change-scripts`), never the MCP. Reading
current state to target a change (e.g. confirming a campaign's bid strategy
before writing the switch script) is fine and encouraged.

## Pull discipline

These rules apply to every query in this pack. They exist because each one has
been violated on a live run and produced a wrong claim in a shipped MAA.

- **Pull the full pack before writing any prose.** No analysis sentence is
  drafted until every standard query below has returned and been saved.
- **Paginate every list query** until the returned count is below the limit,
  and record the final count in the run notes. A query that returns exactly its
  cap (its `limit`, or the tool's page size) is **flagged as truncated**, and
  no absence claim ("no negatives for X", "no ad in that group") may rest on it.
- **Inventory queries run with NO status filter.** Keywords, ads, and negatives
  are pulled once with no `status` condition (so paused and removed rows are
  visible), then a separate pass with ENABLED-only conditions for live metrics.
  Never treat the ENABLED pass as the inventory.
- **Count live entities on both parents.** When counting live keywords or ads,
  filter on `ad_group.status = 'ENABLED'` AND `campaign.status = 'ENABLED'`, not
  only the entity's own status. An enabled keyword in a paused ad group is not
  live.
- **Verify campaign names belong to the client on every response.** A wrong
  `customer_id` under an MCC returns another client's data with no error. Check
  the campaign names against the client ledger before reading a single number.
- **Save the raw response verbatim before abridging.** Write the full MCP
  response to the run's data folder first, then summarize. The abridged view is
  never the record.

## Date windows

- **7D** = the 7 days ending yesterday. **30D** = the 30 days ending yesterday.
- Pass as a condition: `segments.date BETWEEN '{START}' AND '{END}'`
  (YYYY-MM-DD, both required). Run each dataset twice (30D and 7D) where the MAA
  needs both.

## Unit conversions (apply after pulling)

- **Money:** `metrics.cost_micros` and `metrics.cost_per_conversion` are
  **micros** → divide by 1,000,000 for dollars.
- **Rates:** `metrics.ctr` and the impression-share metrics are **fractions
  0–1** → ×100 for a percent.
- **Impression share** metrics exist only on Search campaigns; PMax/LSA return
  them empty.

---

## THE QS COMPONENT MAPPING (why MCP-first kills the swap)

The API fields are correctly named at the source, no inversion, no corrector:

| API field | = MAA component |
|---|---|
| `ad_group_criterion.quality_info.search_predicted_ctr` | **Expected CTR** |
| `ad_group_criterion.quality_info.creative_quality_score` | **Ad Relevance** |
| `ad_group_criterion.quality_info.post_click_quality_score` | **Landing Page Experience** |
| `ad_group_criterion.quality_info.quality_score` | Quality Score (1–10) |

**Read these AS-IS. The Expected-CTR ↔ Ad-Relevance swap and
`correct_qs_columns.py` apply ONLY to the email-fallback branch, never to MCP
data.**

---

## 1. Campaign Summary (run 30D and 7D)

```
resource:   campaign
fields:     campaign.name, campaign.status, campaign.advertising_channel_type,
            campaign.bidding_strategy_type,
            metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.average_cpc, metrics.conversions, metrics.cost_per_conversion,
            metrics.search_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_rank_lost_impression_share
conditions: segments.date BETWEEN '{START}' AND '{END}'
            metrics.impressions > 0
```

Omit dormant campaigns ($0 in both windows). `advertising_channel_type` flags
SEARCH vs PERFORMANCE_MAX vs LOCAL_SERVICES, note that LSA campaigns surface on
this path even though the email script never carried them; LSA is out of scope
for the MAA (see the data-pipeline contract).

## 2. Keyword Report + Quality Score (run 30D and 7D)

```
resource:   keyword_view
fields:     campaign.name, ad_group.name,
            ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score,
            metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.average_cpc, metrics.conversions, metrics.cost_per_conversion
conditions: segments.date BETWEEN '{START}' AND '{END}'
            metrics.impressions > 0
orderings:  metrics.cost_micros DESC
```

QS components are current-state (same in both windows); metrics are windowed.
Read QS per the mapping above (no swap).

**Historical quality score, pulled alongside current state (added 2026-09-15).**
Current state under-reports quality on low-volume accounts: on one roofing
account current state showed 1 scored non-brand keyword while the historical
fields showed 8, and separated 6 never-scored keywords carrying $10,561.47 of
lifetime spend. Run the same query once more over the campaign's life (or the
90D window) adding:

```
fields (add): metrics.historical_quality_score,
              metrics.historical_search_predicted_ctr,
              metrics.historical_creative_quality_score,
              metrics.historical_landing_page_quality_score
```

A keyword that returns QS 0 with UNSPECIFIED components in current state is
unscored now; it is not necessarily low-volume (one such keyword had 3,225
impressions and $3,630.35 of spend). Report "never scored" only when the
historical pull is also empty.

**Caveat:** `metrics.impressions > 0` hides zero-cost and paused rows. It is a
performance filter only. Do **not** use this query for inventory or absence
checks ("that keyword is not in the account"); run the no-status-filter
inventory pass described in Pull discipline instead.

## 3. Search Terms (run 30D and 7D)

```
resource:   search_term_view
fields:     search_term_view.search_term, campaign.name, ad_group.name,
            metrics.cost_micros, metrics.impressions, metrics.clicks,
            metrics.conversions, metrics.cost_per_conversion
conditions: segments.date BETWEEN '{START}' AND '{END}'
            metrics.impressions > 0
orderings:  metrics.cost_micros DESC
```

Feeds negative-keyword mining and the n-gram waste read.

## 4. Ad Report, RSA assets + strength (run 30D and 7D)

```
resource:   ad_group_ad
fields:     campaign.name, ad_group.name, ad_group_ad.ad.type, ad_group_ad.ad_strength,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros,
            metrics.conversions
conditions: segments.date BETWEEN '{START}' AND '{END}'
            ad_group_ad.status != 'REMOVED'
```

`headlines`/`descriptions` are lists of asset objects (pull the `.text`).

## 5. Conversion Detail, by action name (run 30D and 7D)

```
resource:   campaign
fields:     campaign.name, segments.conversion_action_name, metrics.conversions,
            metrics.conversions_value
conditions: segments.date BETWEEN '{START}' AND '{END}'
            metrics.conversions > 0
```

Breaks conversions out by action (forms vs calls vs booked) for the lead-quality
read.

## 6. Campaign Budget (current state, one pull)

```
resource:   campaign_budget
fields:     campaign.name, campaign_budget.amount_micros,
            campaign_budget.delivery_method
conditions: campaign.status != 'REMOVED'
```

The `campaign` resource does **not** return the budget; you must query
`campaign_budget`. `amount_micros` is a daily amount in micros. Shared budgets
return one row per attached campaign with the same amount. Pair with
`search_budget_lost_impression_share` from section 1 for the budget-cap read.

## 7. Network Split (run 30D and 7D)

```
resource:   campaign
fields:     campaign.name, segments.ad_network_type,
            metrics.cost_micros, metrics.impressions, metrics.clicks,
            metrics.conversions, metrics.cost_per_conversion
conditions: segments.date BETWEEN '{START}' AND '{END}'
```

Separates Search from Search Partners, Display, YouTube, and Mixed (PMax).
Search-partner spend at a worse cost per lead is a common hidden leak.

## 8. Device Split (run 30D and 7D)

```
resource:   campaign
fields:     campaign.name, segments.device,
            metrics.cost_micros, metrics.impressions, metrics.clicks,
            metrics.conversions, metrics.cost_per_conversion
conditions: segments.date BETWEEN '{START}' AND '{END}'
```

Mobile vs desktop vs tablet. Answers "which device is driving the CPA spike"
without a mid-cycle pull.

## 9. User Location (run 30D)

```
resource:   user_location_view
fields:     campaign.name, segments.geo_target_city,
            user_location_view.targeting_location,
            metrics.cost_micros, metrics.clicks, metrics.conversions
conditions: segments.date BETWEEN '{START}' AND '{END}'
orderings:  metrics.cost_micros DESC
```

Where the clicks physically came from, by city, versus the targeted location.
Spend outside the service area shows up here first. Paginate; this list is
long on any account with broad geo targeting.

## 10. Negatives (three levels, paginate each)

Negatives live at three levels and no single query returns all of them. Run all
three, every time, with **no status filter** on the inventory pass.

**Cap discipline (added 2026-09-15).** A single wide pull at limit 1000 now
exceeds the tool's output cap on accounts with large shared lists (981 and
950 rows on one account). Page shared-list criteria by regex partition on the
keyword text (for example `^[a-h]`, `^[i-p]`, `^[q-z0-9]`), record each
partition's row count, and treat the set as complete only when the partition
total is within a few rows of `shared_set.member_count`. The same applies to
`search_term_view` (use a cost or impressions filter, never one wide pull)
and to `change_event` (30 days maximum; the API rejects older start dates).

**Campaign-level:**

```
resource:   campaign_criterion
fields:     campaign.name, campaign_criterion.keyword.text,
            campaign_criterion.keyword.match_type, campaign_criterion.negative,
            campaign_criterion.status
conditions: campaign_criterion.negative = true
```

**Ad-group-level:**

```
resource:   ad_group_criterion
fields:     campaign.name, ad_group.name, ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type, ad_group_criterion.negative,
            ad_group_criterion.status
conditions: ad_group_criterion.negative = true
```

**Shared negative lists (two steps):**

```
resource:   campaign_shared_set
fields:     campaign.name, shared_set.name, shared_set.resource_name,
            campaign_shared_set.status
conditions: shared_set.type = 'NEGATIVE_KEYWORDS'
```

then, per list:

```
resource:   shared_criterion
fields:     shared_set.name, shared_criterion.keyword.text,
            shared_criterion.keyword.match_type
conditions: shared_set.resource_name = '{SHARED_SET_RESOURCE_NAME}'
```

**Pagination rule, stated explicitly:** each of these queries is paginated
until the returned row count is below the limit, and that count is recorded.
If any level returns exactly its cap, the negatives inventory is marked
truncated and the MAA may not claim a term is un-negated. A shared list
attached to the campaign counts as a negative on that campaign even though
the term never appears in `campaign_criterion`.

## 11. Call Detail (run 30D)

```
resource:   call_view
fields:     campaign.name, ad_group.name, call_view.start_call_date_time,
            call_view.end_call_date_time, call_view.call_duration_seconds,
            call_view.call_status, call_view.type, call_view.caller_area_code,
            call_view.caller_country_code
conditions: call_view.start_call_date_time >= '{START} 00:00:00'
            call_view.start_call_date_time <= '{END} 23:59:59'
```

`segments.date` is **rejected** on `call_view`; filter on
`call_view.start_call_date_time` instead. There is **no caller number field**;
area code and country code are the most the API returns. Do not promise the
client a caller list from this source.

## 11b. Asset-level disapprovals (current state, one pull; added 2026-09-15)

`asset.policy_summary.approval_status` returns UNSPECIFIED for IMAGE and TEXT
assets, and `ad_group_ad_asset_view.policy_summary.approval_status` is not a
recognised field on this build. Disapproved sitelinks, images and callouts are
visible only through primary status reasons:

```
resource:   campaign_asset
fields:     campaign.name, asset.id, asset.type, asset.name,
            campaign_asset.status, campaign_asset.primary_status,
            campaign_asset.primary_status_reasons
conditions: campaign_asset.primary_status IN ('LIMITED', 'NOT_ELIGIBLE')
            campaign.status = 'ENABLED'
```

Repeat on `ad_group_asset`. `campaign_asset` rejects a `campaign.status`
condition unless `campaign.status` is also selected. A claim that "nothing is
disapproved" must name the levels queried (ads, campaign assets, ad group
assets); on 2026-09-11 an ad-level-only pull produced that claim while two
image assets sat at ASSET_DISAPPROVED.

## 12. Change History (change_event) - use with caution

```
resource:   change_event
fields:     change_event.change_date_time, change_event.change_resource_type,
            change_event.resource_change_operation, change_event.user_email,
            change_event.client_type, campaign.name, ad_group.name
conditions: change_event.change_date_time >= '{START} 00:00:00'
            change_event.change_date_time <= '{END} 23:59:59'
orderings:  change_event.change_date_time DESC
limit:      500
```

**Caveat block, read before trusting any result:**

- `change_event` is **unreliable on some MCP builds**: validation errors on
  otherwise valid queries, empty results for changes made in the last few days,
  a hard 500-row page cap, and `change_event.changed_fields` unselectable.
- Always query in **30-day slices** with an explicit date range and an explicit
  `limit`. The API rejects windows over 30 days and open-ended ranges.
- **NEVER infer "no changes" from an empty result.** An empty response means the
  query returned nothing, not that nothing changed. Write "change_event returned
  no rows" and nothing stronger.
- **The client ledger's change log (section 4) is the authoritative record** of
  what we changed and when. Use `change_event` to look for changes made by
  someone else, and reconcile against the ledger, never the reverse.

---

## Mid-cycle pulls: answer your own questions

The MCP makes additional pulls cheap. When the analysis raises a question the
initial datasets can't answer, "is there real demand for long-term rentals?",
"which device is driving the CPA spike?", pull the extra data inside the same
cycle and turn the answer into a grounded action, instead of writing "keep
watching" and deferring it a week. This applies to Google Ads pulls and to any
other connected data source (keyword research tools, page speed tests, analytics).

## Notes

- If a field name errors, confirm it with the MCP's resource-metadata tool for
  that resource rather than guessing.
- Large hierarchy queries (e.g. `customer_client` across an MCC) can exceed the
  tool's output cap, query a specific `customer_id` and filter/limit.
- Auction insight metrics (`metrics.auction_insight_*` with
  `segments.auction_insight_domain`) are listed as selectable on `campaign`
  and `keyword_view` but are rejected with "the developer doesn't have access
  to metrics" on a Basic-access developer token. That is a permission, not an
  absence. Until it is granted, auction insights are a UI read named as a next
  step; never a causal claim in Analysis.
- Impression share fields return 0.0999 and 0.9001 as sentinels for "under
  10%" and "over 90%". Never print them as 9.99% or 90.01%.
- Under Maximize Conversions, `effective_cpc_bid_micros` returns a 10000
  ($0.01) placeholder and the first-page, top-of-page and first-position CPC
  fields return 0. No cost-per-click target can be derived from them.
- Any summary or derived block written into the saved pack (weekly call
  counts, daily notes) is computed from rows by script. A hand-typed block
  that did not sum to its own rows produced four wrong sentences on
  2026-09-11 before the hardener caught it.

---

**Changed in 1.5.0:** added Pull discipline (pagination, cap flag, no-status
inventory pass, parent-status filters, client-name verification, raw save);
added campaign_budget, network split, device split, user_location_view,
three-level negatives, call_view, and change_event queries with their caveats;
keyword report now carries the impressions-filter caveat.

**Changed 2026-09-15 (from run records GAA-2026-09-04-BT and
GAA-2026-09-11-C1):** historical quality score pulled alongside current state;
cap discipline for negatives, search terms and change_event; asset-level
disapproval query (11b); auction-insight permission, impression-share
sentinels, bid placeholders and the no-hand-typed-blocks rule in Notes.
