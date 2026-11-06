# GAQL Queries & Export Specifications

This file defines the exact data needed for each diagnostic tier. These queries
serve dual purposes:

1. **MCP Mode**: Execute directly against the Google Ads API when the MCP server
   is connected
2. **Upload Mode**: Define the exact columns the user needs to export, so you can
   provide precise export instructions if they're pulling data manually

## Export Instructions for Account Managers

When the user needs to manually export data, provide these instructions tailored
to whichever reports are needed. Don't dump all of them at once, request only
what the current diagnostic tier requires.

### Campaign Summary Export

In Google Ads UI: Campaigns → Columns → Modify Columns. Include:

Campaign Name, Campaign Status, Campaign Type, Bid Strategy Type, Budget,
Cost, Impressions, Clicks, CTR, Avg CPC, Conversions, Conversion Rate, Cost
per Conversion, Conversion Value, Search Impression Share, Search Lost IS
(Budget), Search Lost IS (Rank)

Date range: Last 30 days (minimum). Download as CSV.

### Keyword Performance Export

In Google Ads UI: Keywords → Search Keywords → Columns → Modify Columns. Include:

Campaign Name, Ad Group Name, Keyword, Match Type, Status, Quality Score,
Expected CTR, Ad Relevance, Landing Page Experience, Impressions, Clicks, CTR,
Avg CPC, Cost, Conversions, Conversion Rate, Cost per Conversion

Date range: Last 30 days. Download as CSV.

### Search Terms Export

In Google Ads UI: Keywords → Search Terms → Columns → Modify Columns. Include:

Search Term, Campaign Name, Ad Group Name, Keyword, Match Type, Impressions,
Clicks, CTR, Cost, Conversions, Conversion Rate, Cost per Conversion,
Added/Excluded

Date range: Last 30 days. Download as CSV.

### Ad Copy Performance Export

In Google Ads UI: Ads & Assets → Ads → Columns → Modify Columns. Include:

Campaign Name, Ad Group Name, Ad Type, Headlines, Descriptions, Final URL,
Status, Impressions, Clicks, CTR, Avg CPC, Cost, Conversions, Conversion Rate,
Cost per Conversion

Date range: Last 30 days. Download as CSV.

### Geographic Performance Export

In Google Ads UI: Campaigns → Locations → Columns → Modify Columns. Include:

Campaign Name, Location, Location Type, Impressions, Clicks, Cost, Conversions,
Cost per Conversion, Conversion Rate

Date range: Last 30 days. Download as CSV.

## GAQL Queries for MCP Mode

These queries are designed for the Google Ads MCP server. When the MCP server is
connected, execute them directly. Each query includes the resource, fields, and
any relevant filtering.

### Campaign Summary (Tier 1)

```sql
SELECT
  campaign.id,
  campaign.name,
  campaign.status,
  campaign.advertising_channel_type,
  campaign.bidding_strategy_type,
  campaign_budget.amount_micros,
  metrics.cost_micros,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.average_cpc,
  metrics.conversions,
  metrics.conversions_value,
  metrics.cost_per_conversion,
  metrics.search_impression_share,
  metrics.search_budget_lost_impression_share,
  metrics.search_rank_lost_impression_share
FROM campaign
WHERE campaign.status != 'REMOVED'
  AND segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

### Keyword Performance with Quality Score (Tier 1-2)

```sql
SELECT
  campaign.name,
  ad_group.name,
  ad_group_criterion.keyword.text,
  ad_group_criterion.keyword.match_type,
  ad_group_criterion.quality_info.quality_score,
  ad_group_criterion.quality_info.creative_quality_score,
  ad_group_criterion.quality_info.search_predicted_ctr,
  ad_group_criterion.quality_info.post_click_quality_score,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.average_cpc,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value,
  metrics.cost_per_conversion
FROM keyword_view
WHERE campaign.status = 'ENABLED'
  AND ad_group.status = 'ENABLED'
  AND ad_group_criterion.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

### Search Terms Report (Tier 2)

```sql
SELECT
  search_term_view.search_term,
  campaign.name,
  ad_group.name,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.cost_micros,
  metrics.conversions,
  metrics.cost_per_conversion,
  search_term_view.status
FROM search_term_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 500
```

### Ad Copy Performance (Tier 2-3)

```sql
SELECT
  campaign.name,
  ad_group.name,
  ad_group_ad.ad.responsive_search_ad.headlines,
  ad_group_ad.ad.responsive_search_ad.descriptions,
  ad_group_ad.ad.final_urls,
  ad_group_ad.ad.type,
  ad_group_ad.status,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.average_cpc,
  metrics.cost_micros,
  metrics.conversions,
  metrics.cost_per_conversion
FROM ad_group_ad
WHERE ad_group_ad.status = 'ENABLED'
  AND campaign.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

### Geographic Performance (Tier 1)

```sql
SELECT
  campaign.name,
  geographic_view.country_criterion_id,
  geographic_view.location_type,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.cost_per_conversion
FROM geographic_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 200
```

### Location Targeting Settings (Tier 1)

```sql
SELECT
  campaign.name,
  campaign.geo_target_type_setting.positive_geo_target_type,
  campaign.geo_target_type_setting.negative_geo_target_type
FROM campaign
WHERE campaign.status = 'ENABLED'
```

## Which Queries to Run by Tier

**Tier 1 (Foundations)**: Campaign Summary + Keyword Performance (for QS and bid
strategy context) + Geographic Performance + Location Targeting Settings

**Tier 2 (Hygiene)**: All of Tier 1 + Search Terms Report + Ad Copy Performance

**Tier 3 (Structural)**: All of Tier 2 (refresh data if stale). Additional
queries for device/time-of-day segmentation can be constructed by adding
`segments.device` or `segments.hour` to the campaign or keyword queries.

**Tier 4 (Advanced)**: Custom queries based on the specific analysis framework
being applied. See `playbook-frameworks.md`.
