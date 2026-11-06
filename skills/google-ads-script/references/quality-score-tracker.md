# Quality Score Tracker Reference

## Overview

This pattern captures a daily snapshot of keyword-level Quality Score and its three component metrics (Expected CTR, Ad Relevance, Landing Page Experience) into a Google Sheet or BigQuery table. Since Google Ads doesn't retain historical Quality Score data, daily snapshots enable trend analysis that's impossible in the UI.

The output is a time-series record where each row represents one keyword's QS state on a given day. By running this script daily, you build a historical record that reveals:
- Whether QS is improving or degrading over time
- Which keywords respond to landing page or ad copy changes
- Seasonal or account-wide QS trends
- The composition of your account (how many keywords are Below Average vs Average vs Above Average)

## Why This Matters

**The Problem:** Google Ads UI shows only today's Quality Score. Click a keyword tomorrow and you'll see a new score, but you have no way to know if it improved from yesterday or dropped.

**The Impact on MAA Reporting:** When you recommend landing page changes or ad copy rewrites, you need proof that the changes actually moved the needle. Without historical QS data, you're flying blind. A client makes a landing page fix, and two weeks later you can't prove whether QS improved because you only see today's snapshot.

**The Solution:** Automated daily snapshots create a control group for your own experiments. Did QS go up after we fixed the landing page? This script answers that question.

---

## GAQL Query

This is the core query that pulls Quality Score data from the keyword_view:

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
  ad_group_criterion.status,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros
FROM keyword_view
WHERE campaign.status = "ENABLED"
  AND ad_group.status = "ENABLED"
  AND ad_group_criterion.status = "ENABLED"
  AND segments.date DURING YESTERDAY
```

### Key Notes

**Quality Score Fields:**
- `quality_info.quality_score`, Returns integer 1–10. This is the overall Quality Score.
- `quality_info.creative_quality_score`, Ad Relevance component. Returns "ABOVE_AVERAGE" | "AVERAGE" | "BELOW_AVERAGE".
- `quality_info.search_predicted_ctr`, Expected CTR component. Returns "ABOVE_AVERAGE" | "AVERAGE" | "BELOW_AVERAGE".
- `quality_info.post_click_quality_score`, Landing Page Experience component. Returns "ABOVE_AVERAGE" | "AVERAGE" | "BELOW_AVERAGE".

**Missing Data:**
- Some keywords won't have a QS (returns null or 0). This typically happens for keywords with very low impression volume or brand-new keywords that haven't accumulated enough data.
- If a keyword has 0 impressions on a given day but had impressions previously, it still appears in the result with yesterday's QS (Google retains the score even if there were no impressions that day).

**Segment Timing:**
- `segments.date DURING YESTERDAY` pulls the previous day's data because QS scores stabilize overnight. This is more reliable than pulling the current day's scores.

---

## Sheet Output Pattern

Recommended structure for appending snapshots to a Google Sheet:

### Headers

```
Date | Campaign | Ad Group | Keyword | Match Type | QS | Expected CTR | Ad Relevance | Landing Page | Impressions | Clicks | Cost
```

### Data Structure

- **One row per keyword per day**, If an account has 500 keywords, each daily run adds 500 rows.
- **New rows appended, never overwritten**, This is critical. Each run should append to the sheet, not replace. You're building a time-series history.
- **Null handling**, If a keyword has no QS data, record it as blank or "N/A" so you know it was tracked that day but had insufficient data.
- **Cost column**, Store in micros (cost_micros from the API). Convert to dollars when displaying: `cost_micros / 1_000_000`.

### Sheet Organization Example

```
Date       | Campaign    | Ad Group    | Keyword           | Match Type | QS | Expected CTR | Ad Relevance | Landing Page | Impressions | Clicks | Cost
2026-03-26 | Plumbing SEM| Emergency   | emergency plumber | Exact      | 9  | Above Avg    | Above Avg    | Above Avg    | 45          | 12     | 24.50
2026-03-26 | Plumbing SEM| Emergency   | 24 hr plumber     | Phrase     | 6  | Average      | Below Avg    | Average      | 8           | 1      | 4.20
2026-03-27 | Plumbing SEM| Emergency   | emergency plumber | Exact      | 9  | Above Avg    | Above Avg    | Above Avg    | 52          | 15     | 28.75
```

### Summary Sheet (Optional)

Add a second sheet that aggregates QS distribution per snapshot date:

```
Date       | QS_10 | QS_9 | QS_8 | QS_7 | QS_6 | QS_5 | QS_4 | QS_3 | QS_2 | QS_1 | Below_Average_Count | Avg_Quality_Score
2026-03-26 | 5     | 12   | 18   | 14   | 8    | 3    | 0    | 0    | 0    | 0    | 11                  | 7.4
2026-03-27 | 6     | 13   | 19   | 14   | 7    | 2    | 0    | 0    | 0    | 0    | 9                   | 7.5
```

This allows quick visualization of overall account health and whether your changes are moving the needle across the entire portfolio.

---

## BigQuery Output Pattern

For accounts that want QS data in their warehouse:

### Table Schema

```sql
CREATE TABLE google_ads_quality_scores (
  date DATE,
  account_id STRING,
  campaign_name STRING,
  ad_group_name STRING,
  keyword_text STRING,
  match_type STRING,
  quality_score INT64,
  expected_ctr STRING,
  ad_relevance STRING,
  landing_page_experience STRING,
  impressions INT64,
  clicks INT64,
  cost FLOAT64,
  snapshot_timestamp TIMESTAMP
);
```

### Insert Pattern

On each run, insert the day's snapshot:

```sql
INSERT INTO google_ads_quality_scores (
  date, account_id, campaign_name, ad_group_name, keyword_text, match_type,
  quality_score, expected_ctr, ad_relevance, landing_page_experience,
  impressions, clicks, cost, snapshot_timestamp
)
VALUES
  ('2026-03-26', '1234567890', 'Plumbing SEM', 'Emergency', 'emergency plumber', 'Exact',
   9, 'ABOVE_AVERAGE', 'ABOVE_AVERAGE', 'ABOVE_AVERAGE', 45, 12, 24.50, CURRENT_TIMESTAMP()),
  ...
```

Never update or delete rows from this table. Each daily run appends a complete snapshot, so you have a full audit trail and can compare any two dates.

---

## Filtering Strategies

For large accounts, tracking QS on every keyword creates noise and API overhead. Consider these filters:

### 1. **Active Keywords Only**
Filter to keywords with >0 impressions in the last 30 days:

```sql
AND metrics.impressions > 0
```

This excludes paused keywords and active-but-dormant keywords, focusing on what actually drives traffic.

### 2. **Label-Based**
If you have a "Track QS" label applied to priority keywords:

```sql
AND ad_group_criterion.labels CONTAINS "Track QS"
```

Useful for focusing on keywords that matter for MAA reporting.

### 3. **Top N by Spend**
For accounts with thousands of keywords, track only the top spenders:

```sql
ORDER BY metrics.cost_micros DESC
LIMIT 500
```

This ensures your snapshots cover the keywords that actually affect account performance.

### 4. **Minimum Impression Threshold**
Exclude very low-volume keywords (QS unreliable below ~10 impressions):

```sql
AND metrics.impressions >= 10
```

### 5. **Campaign Filter**
If you only care about certain campaigns:

```sql
AND campaign.name IN ("Plumbing SEM", "HVAC Branded")
```

**Note on Iterator Limits:** Google Ads API has a 50,000 keyword iterator limit per script run. For most accounts, this isn't a constraint, even large accounts rarely have >10,000 active keywords. But if you're hitting the limit, layer the filters above.

---

## CONFIG Template

```javascript
const CONFIG = {
  // Destination
  output: {
    type: "SHEET", // or "BIGQUERY"
    sheetUrl: "https://docs.google.com/spreadsheets/d/ABC123.../edit",
    sheetName: "QS Snapshots",
    summarySheetName: "QS Distribution", // Optional
    bigQueryDataset: "marketing_analytics", // If type is BIGQUERY
    bigQueryTable: "google_ads_quality_scores"
  },

  // Filtering
  filters: {
    minImpressions: 0, // Set to 10+ to exclude low-volume keywords
    activeOnly: true, // Only keywords with impressions in last 30 days
    label: null, // Set to "Track QS" to filter by label
    campaigns: null, // Set to ["Campaign 1", "Campaign 2"] or null for all
    limit: null // Set to 500 to track top N keywords, or null for all
  },

  // Timezone (for date labeling)
  timezone: "America/Chicago",

  // Logging
  debug: false // Set to true for verbose console output
};
```

---

## Scheduling

**Frequency:** Daily

**Timing:** Early morning (6–8 AM in your account's timezone)

**Rationale:**
- QS stabilizes overnight, so pulling "yesterday's" data is more reliable than pulling live scores.
- Early morning run ensures the snapshot is in place before your team reviews performance.
- Consistent timing makes trend analysis cleaner (e.g., every morning at 7 AM UTC).

**Setup in Google Ads Scripts:**
- Deploy the script with a daily trigger.
- Use the CONFIG.timezone to ensure date labels match your business timezone, not UTC.

---

## Analysis Tips

Once you have 2+ weeks of data, you can spot patterns:

### Week-over-Week QS Trends
Compare the same keywords across two weeks. Did QS improve after your landing page changes?

```
Keyword              | Week 1 Avg QS | Week 2 Avg QS | Change
emergency plumber    | 7.2           | 8.1           | +0.9 (improvement)
24 hr plumber        | 5.8           | 5.9           | +0.1 (flat)
```

### Component Breakdown
Identify which component is dragging down QS. If Ad Relevance is "Below Average" across many keywords, your ad copy might be too generic. If Landing Page Experience is consistently low, the landing page isn't matching ad promises.

```
Campaign         | Avg QS | Below Avg CTR Count | Below Avg Relevance | Below Avg LP
Plumbing SEM     | 7.4    | 3                   | 8                   | 2
HVAC Seasonal    | 6.1    | 12                  | 5                   | 18 ← LP is the problem
```

### Keyword-Level Diagnosis
Flag keywords with high spend but declining QS:

```
Keyword               | Spend (Last 7d) | QS Trend (7 days)   | Action
commercial plumber    | $450            | 8→7→7→6→6→6→5      | Declining. Review landing page.
blocked drain         | $120            | 4→4→5→5→6→6→6      | Improving. Keep landing page as-is.
```

### Account Health Snapshot
If your summary sheet shows an increasing number of "Below Average" keywords, it's an early warning sign. Before QS tanks, you can investigate and fix.

---

## Script Integration Points

When building the actual script:

1. **API Call**, Execute the GAQL query using `AdsManagerScriptObjects`.
2. **Data Transformation**, Map API response fields to your output schema (Sheet or BigQuery).
3. **Deduplication** (if rerunning), Check if today's date already exists in the Sheet/table. If it does, delete yesterday's entries and reinsert to handle late-arriving data.
4. **Append Logic**, For Sheet, use `appendRow()` or batch `insertRows()`. For BigQuery, use streaming inserts.
5. **Error Handling**, Log any keywords with null QS. Email alerts if the query returns 0 rows (indicating a quota issue or account problem).

---

## Related Patterns

- **Landing Page Experience Audit**, Deep dive into which landing pages are causing QS to drop.
- **Keyword Bid Optimization**, Use QS trends to identify keywords worth increasing bids on (high QS + low spend = opportunity).
- **Ad Copy A/B Testing**, Track whether ad copy changes move Ad Relevance scores.
