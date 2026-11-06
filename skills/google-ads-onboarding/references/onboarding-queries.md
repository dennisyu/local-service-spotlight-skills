# Onboarding query pack (Google Ads MCP, `search` tool)

Supplements `shared/frameworks/gaql-query-pack.md`. Same call shape: `customer_id` (digits), `resource`, `fields`, `conditions`, optional `orderings`, `limit`. Money in micros, rates as 0 to 1 fractions. Run every inventory query with NO status filter. Paginate until the returned count is below the limit and record the count. Verify campaign names belong to the client on every response.

## A. Inventory

Campaigns, all statuses
```
resource:   campaign
fields:     campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type,
            campaign.bidding_strategy_type, campaign.start_date, campaign.end_date,
            campaign.network_settings.target_search_network,
            campaign.network_settings.target_content_network,
            campaign.geo_target_type_setting.positive_geo_target_type,
            campaign_budget.amount_micros, campaign_budget.delivery_method
```

Conversion actions
```
resource:   conversion_action
fields:     conversion_action.id, conversion_action.name, conversion_action.category,
            conversion_action.type, conversion_action.status, conversion_action.primary_for_goal,
            conversion_action.counting_type, conversion_action.click_through_lookback_window_days,
            conversion_action.origin
```

Policy and serving
```
resource:   ad_group_ad
fields:     campaign.name, ad_group.name, ad_group_ad.ad.id, ad_group_ad.status,
            ad_group_ad.policy_summary.approval_status,
            ad_group_ad.policy_summary.review_status,
            ad_group_ad.ad_strength
```

Assets (call, location, sitelink)
```
resource:   campaign_asset
fields:     campaign.name, asset.type, asset.call_asset.phone_number,
            asset.sitelink_asset.link_text, asset.location_asset.business_name
```

## B. History

Monthly, 24 months
```
resource:   campaign
fields:     segments.month, campaign.name, metrics.cost_micros, metrics.impressions,
            metrics.clicks, metrics.ctr, metrics.average_cpc, metrics.conversions,
            metrics.cost_per_conversion, metrics.search_impression_share,
            metrics.search_budget_lost_impression_share, metrics.search_rank_lost_impression_share
conditions: segments.date BETWEEN '{START_24M}' AND '{YESTERDAY}'
```

Monthly conversions by action
```
resource:   campaign
fields:     segments.month, campaign.name, segments.conversion_action_name, metrics.conversions
conditions: segments.date BETWEEN '{START_24M}' AND '{YESTERDAY}'
```

Weekly, 13 weeks (trend backfill)
```
resource:   campaign
fields:     segments.week, campaign.name, metrics.cost_micros, metrics.conversions,
            metrics.cost_per_conversion
conditions: segments.date BETWEEN '{START_13W}' AND '{YESTERDAY}'
```

Keyword inventory, all statuses (QS is current state only)
```
resource:   ad_group_criterion
fields:     campaign.name, ad_group.name, ad_group.status, ad_group_criterion.criterion_id,
            ad_group_criterion.status, ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type, ad_group_criterion.final_urls,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score
conditions: ad_group_criterion.type = 'KEYWORD'
            ad_group_criterion.negative = false
```
Then a second pass on `keyword_view` with `segments.date BETWEEN '{START_90D}' AND '{YESTERDAY}'` for metrics; join on criterion_id. Add `metrics.historical_quality_score`, `metrics.historical_search_predicted_ctr`, `metrics.historical_creative_quality_score` and `metrics.historical_landing_page_quality_score` to that pass: current state hides keywords that were scored earlier (one account showed 1 scored non-brand keyword in current state and 8 in the historical fields), and "never scored" may only be written when the historical pull is also empty.

Negatives (three levels; plus `campaign_shared_set` to see which lists attach where)
```
resource:   campaign_criterion
fields:     campaign.name, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type
conditions: campaign_criterion.negative = true
            campaign_criterion.type = 'KEYWORD'

resource:   ad_group_criterion
fields:     campaign.name, ad_group.name, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type
conditions: ad_group_criterion.negative = true

resource:   shared_criterion
fields:     shared_set.name, shared_criterion.keyword.text, shared_criterion.keyword.match_type
```

Search terms, 90D
```
resource:   search_term_view
fields:     search_term_view.search_term, campaign.name, ad_group.name, metrics.cost_micros,
            metrics.impressions, metrics.clicks, metrics.conversions
conditions: segments.date BETWEEN '{START_90D}' AND '{YESTERDAY}'
orderings:  metrics.cost_micros DESC
limit:      500 (paginate)
```

Ads, all statuses
```
resource:   ad_group_ad
fields:     campaign.name, ad_group.name, ad_group_ad.ad.id, ad_group_ad.status,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls, ad_group_ad.ad_strength,
            metrics.cost_micros, metrics.clicks, metrics.conversions
conditions: segments.date BETWEEN '{START_90D}' AND '{YESTERDAY}'
```

Change history (30-day slices; unreliable on some MCP builds, never infer "no changes" from an empty result)
```
resource:   change_event
fields:     change_event.change_date_time, change_event.change_resource_type,
            change_event.resource_change_operation, change_event.old_resource,
            change_event.new_resource, change_event.user_email
conditions: change_event.change_date_time >= '{START} 00:00:00'
            change_event.change_date_time <= '{END} 23:59:59'
limit:      500
```

## C. Geo, device, network, schedule, calls

Targeted locations (resolve names via `geo_target_constant`: name, canonical_name, target_type)
```
resource:   campaign_criterion
fields:     campaign.name, campaign_criterion.location.geo_target_constant,
            campaign_criterion.negative, campaign_criterion.proximity.radius,
            campaign_criterion.proximity.radius_units
conditions: campaign_criterion.type IN ('LOCATION', 'PROXIMITY')
```

Where spend actually lands, 90D
```
resource:   user_location_view
fields:     user_location_view.country_criterion_id, segments.geo_target_city,
            segments.geo_target_county, user_location_view.targeting_location,
            metrics.cost_micros, metrics.clicks, metrics.conversions
conditions: segments.date BETWEEN '{START_90D}' AND '{YESTERDAY}'
```

Device and network, 90D
```
resource:   campaign
fields:     campaign.name, segments.device, segments.ad_network_type,
            metrics.cost_micros, metrics.clicks, metrics.conversions
conditions: segments.date BETWEEN '{START_90D}' AND '{YESTERDAY}'
```

Ad schedule and bid adjustments
```
resource:   campaign_criterion
fields:     campaign.name, campaign_criterion.ad_schedule.day_of_week,
            campaign_criterion.ad_schedule.start_hour, campaign_criterion.ad_schedule.end_hour,
            campaign_criterion.bid_modifier, campaign_criterion.device.type
conditions: campaign_criterion.type IN ('AD_SCHEDULE', 'DEVICE')
```

Calls, 90D (no caller numbers on this resource; filter on start time, `segments.date` is rejected)
```
resource:   call_view
fields:     call_view.start_call_date_time, call_view.call_duration_seconds,
            call_view.call_status, call_view.type, campaign.name
conditions: call_view.start_call_date_time >= '{START_90D} 00:00:00'
```
