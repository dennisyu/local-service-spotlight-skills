# BigQuery Sync Pattern for Google Ads Scripts

## Overview

This pattern syncs Google Ads performance data to BigQuery on a daily schedule. The script pulls campaign, ad group, keyword, and search term metrics from the previous day and appends them to BigQuery tables, creating a historical performance database.

**Use case:** Build a data warehouse of Google Ads performance, enabling custom reporting, cross-account analysis, and historical trend analysis that goes beyond the Google Ads native reports.

**Data flow:**
1. Script runs daily (typically after midnight)
2. Queries yesterday's data via GAQL
3. Creates BigQuery dataset and tables if they don't exist
4. Inserts rows into the appropriate tables
5. Logs success/failure

## Prerequisites

### Google Ads Script Setup
- **BigQuery Advanced API** must be enabled in the script editor
  - Open the script editor → Advanced APIs → Find "BigQuery" → Toggle ON → Click Save
- The script will run under the Google Ads account's context

### Google Cloud Setup
- User needs a Google Cloud project with BigQuery API enabled
- The script must authenticate via OAuth (automatically handled when BigQuery API is enabled)
- User's Google Ads account must be linked to a Google Cloud project

### Self-Creating Infrastructure
- The script auto-creates the BigQuery dataset if it doesn't exist
- The script auto-creates tables with proper schemas if they don't exist
- No manual BigQuery setup required on first run

## Schema Design

Define each table's schema as a BigQuery `fields` array. These are passed to `BigQuery.Tables.insert()`.

### `google_ads_campaigns`
Holds daily campaign-level performance data.

```javascript
{
  fields: [
    {name: 'date', type: 'DATE', mode: 'NULLABLE'},
    {name: 'account_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'account_name', type: 'STRING', mode: 'NULLABLE'},
    {name: 'campaign_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'campaign_name', type: 'STRING', mode: 'NULLABLE'},
    {name: 'campaign_type', type: 'STRING', mode: 'NULLABLE'},
    {name: 'bid_strategy', type: 'STRING', mode: 'NULLABLE'},
    {name: 'status', type: 'STRING', mode: 'NULLABLE'},
    {name: 'impressions', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'clicks', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'ctr', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'cost', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'conversions', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'conversion_value', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'cpa', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'roas', type: 'FLOAT64', mode: 'NULLABLE'}
  ]
}
```

### `google_ads_ad_groups`
Holds daily ad group-level performance data.

```javascript
{
  fields: [
    {name: 'date', type: 'DATE', mode: 'NULLABLE'},
    {name: 'account_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'campaign_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'campaign_name', type: 'STRING', mode: 'NULLABLE'},
    {name: 'ad_group_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'ad_group_name', type: 'STRING', mode: 'NULLABLE'},
    {name: 'status', type: 'STRING', mode: 'NULLABLE'},
    {name: 'impressions', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'clicks', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'ctr', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'cost', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'conversions', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'cpa', type: 'FLOAT64', mode: 'NULLABLE'}
  ]
}
```

### `google_ads_keywords`
Holds daily keyword-level performance data with quality score.

```javascript
{
  fields: [
    {name: 'date', type: 'DATE', mode: 'NULLABLE'},
    {name: 'account_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'campaign_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'ad_group_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'keyword_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'keyword_text', type: 'STRING', mode: 'NULLABLE'},
    {name: 'match_type', type: 'STRING', mode: 'NULLABLE'},
    {name: 'status', type: 'STRING', mode: 'NULLABLE'},
    {name: 'quality_score', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'impressions', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'clicks', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'ctr', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'cost', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'conversions', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'cpa', type: 'FLOAT64', mode: 'NULLABLE'}
  ]
}
```

### `google_ads_search_terms`
Holds daily search term (query) performance data.

```javascript
{
  fields: [
    {name: 'date', type: 'DATE', mode: 'NULLABLE'},
    {name: 'account_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'campaign_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'ad_group_id', type: 'STRING', mode: 'NULLABLE'},
    {name: 'search_term', type: 'STRING', mode: 'NULLABLE'},
    {name: 'keyword_text', type: 'STRING', mode: 'NULLABLE'},
    {name: 'impressions', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'clicks', type: 'INTEGER', mode: 'NULLABLE'},
    {name: 'ctr', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'cost', type: 'FLOAT64', mode: 'NULLABLE'},
    {name: 'conversions', type: 'FLOAT64', mode: 'NULLABLE'}
  ]
}
```

## GAQL Queries

All queries filter to `YESTERDAY` to pull the previous day's complete data. Date range filtering ensures data consistency.

### Campaign Data Query

```
SELECT
  campaign.id,
  campaign.name,
  campaign.type,
  campaign.bidding_strategy,
  campaign.status,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversion_value,
  metrics.cost_per_conversion,
  metrics.value_per_conversion
FROM campaign
WHERE campaign.status = 'ENABLED'
AND segments.date DURING YESTERDAY
```

**Notes:**
- `campaign.type` returns values like `SEARCH`, `DISPLAY`, `SHOPPING`, `VIDEO`, `PERFORMANCE_MAX`
- `campaign.status` filters to active campaigns (use `IN ('ENABLED', 'PAUSED')` to include paused)
- `metrics.cost_micros` requires division by 1,000,000 to get actual cost
- `metrics.cost_per_conversion` is already in the correct currency units (not micros)

### Ad Group Data Query

```
SELECT
  ad_group.id,
  ad_group.name,
  campaign.id,
  campaign.name,
  ad_group.status,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.cost_micros,
  metrics.conversions,
  metrics.cost_per_conversion
FROM ad_group
WHERE campaign.status = 'ENABLED'
AND segments.date DURING YESTERDAY
```

### Keyword Data Query

```
SELECT
  keyword_view.resource_name,
  ad_group.id,
  campaign.id,
  keyword.id,
  keyword.text,
  keyword.match_type,
  keyword.status,
  keyword_view.quality_score,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.cost_micros,
  metrics.conversions,
  metrics.cost_per_conversion
FROM keyword_view
WHERE campaign.status = 'ENABLED'
AND segments.date DURING YESTERDAY
```

**Notes:**
- `keyword_view` is the only way to access `quality_score` in GAQL
- `keyword.status` can be `ENABLED`, `PAUSED`, `REMOVED`
- `keyword_view.quality_score` returns an integer 1–10, or empty/null if no score assigned

### Search Term Data Query

```
SELECT
  search_term_view.search_term,
  ad_group.id,
  campaign.id,
  keyword.text,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.cost_micros,
  metrics.conversions
FROM search_term_view
WHERE campaign.status = 'ENABLED'
AND segments.date DURING YESTERDAY
```

**Notes:**
- `search_term_view.search_term` is the actual query the user searched
- `keyword.text` is the keyword the search matched (null if no matched keyword)
- This data is valuable for finding new keyword opportunities and negative keywords

## BigQuery Insert Pattern

### Complete Helper Function

```javascript
function ensureDatasetAndTable(projectId, datasetId, tableId, schema) {
  // Check if dataset exists, create if not
  try {
    BigQuery.Datasets.get(projectId, datasetId);
  } catch (e) {
    Logger.log('Dataset ' + datasetId + ' not found. Creating...');
    var dataset = {
      datasetReference: {
        projectId: projectId,
        datasetId: datasetId
      }
    };
    BigQuery.Datasets.insert(dataset, projectId);
  }

  // Check if table exists, create with schema if not
  try {
    BigQuery.Tables.get(projectId, datasetId, tableId);
  } catch (e) {
    Logger.log('Table ' + tableId + ' not found. Creating...');
    var table = {
      tableReference: {
        projectId: projectId,
        datasetId: datasetId,
        tableId: tableId
      },
      schema: schema
    };
    BigQuery.Tables.insert(table, projectId, datasetId);
  }
}
```

### Building Rows from GAQL Results

The pattern converts GAQL result rows into BigQuery-compatible objects. Key conversion:
- Divide `metrics.cost_micros` by 1,000,000
- Preserve all other values as-is
- Handle null/undefined metrics gracefully

```javascript
function buildCampaignRows(campaignRows) {
  var rows = [];
  var yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  var dateString = Utilities.formatDate(yesterday, 'America/Los_Angeles', 'yyyy-MM-dd');

  for (var i = 0; i < campaignRows.length; i++) {
    var row = campaignRows[i];
    var metrics = row.metrics || {};

    rows.push({
      json: {
        date: dateString,
        account_id: AdsApp.currentAccount().getCustomerId(),
        account_name: AdsApp.currentAccount().getName(),
        campaign_id: row.campaign.id,
        campaign_name: row.campaign.name,
        campaign_type: row.campaign.type,
        bid_strategy: row.campaign.biddingStrategy,
        status: row.campaign.status,
        impressions: metrics.impressions || 0,
        clicks: metrics.clicks || 0,
        ctr: metrics.ctr || 0,
        cost: (metrics.costMicros || 0) / 1000000,
        conversions: metrics.conversions || 0,
        conversion_value: metrics.conversionValue || 0,
        cpa: metrics.costPerConversion || 0,
        roas: metrics.valuePerConversion || 0
      }
    });
  }

  return rows;
}
```

### Inserting Rows with Batching

BigQuery's `insertAll` has limits:
- ~500 rows per request is safe
- ~10 MB per request total size
- Batch large result sets to avoid timeout/quota errors

```javascript
function insertRowsToBigQuery(projectId, datasetId, tableId, rows) {
  var batchSize = 500;
  var totalInserted = 0;
  var errors = [];

  for (var i = 0; i < rows.length; i += batchSize) {
    var batch = rows.slice(i, i + batchSize);

    var request = {
      rows: batch,
      skipInvalidRows: false,
      ignoreUnknownValues: true
    };

    try {
      var response = BigQuery.Tabledata.insertAll(
        request,
        projectId,
        datasetId,
        tableId
      );

      totalInserted += batch.length;
      Logger.log('Inserted batch of ' + batch.length + ' rows');

      // Check for errors in the response
      if (response.errors && response.errors.length > 0) {
        for (var e = 0; e < response.errors.length; e++) {
          Logger.log('Error in row ' + response.errors[e].index + ': ' + JSON.stringify(response.errors[e].errors));
          errors.push(response.errors[e]);
        }
      }
    } catch (err) {
      Logger.log('Error inserting batch: ' + err.message);
      errors.push({batch: batch, error: err.message});
    }
  }

  Logger.log('Total rows inserted: ' + totalInserted);
  if (errors.length > 0) {
    Logger.log('Total errors: ' + errors.length);
    Logger.log('Errors: ' + JSON.stringify(errors));
  }

  return {
    inserted: totalInserted,
    errors: errors
  };
}
```

### Full Sync Workflow

```javascript
function syncCampaignsToBigQuery(projectId, datasetId) {
  // Ensure dataset and table exist
  var campaignSchema = {
    fields: [
      {name: 'date', type: 'DATE', mode: 'NULLABLE'},
      {name: 'account_id', type: 'STRING', mode: 'NULLABLE'},
      {name: 'account_name', type: 'STRING', mode: 'NULLABLE'},
      {name: 'campaign_id', type: 'STRING', mode: 'NULLABLE'},
      {name: 'campaign_name', type: 'STRING', mode: 'NULLABLE'},
      {name: 'campaign_type', type: 'STRING', mode: 'NULLABLE'},
      {name: 'bid_strategy', type: 'STRING', mode: 'NULLABLE'},
      {name: 'status', type: 'STRING', mode: 'NULLABLE'},
      {name: 'impressions', type: 'INTEGER', mode: 'NULLABLE'},
      {name: 'clicks', type: 'INTEGER', mode: 'NULLABLE'},
      {name: 'ctr', type: 'FLOAT64', mode: 'NULLABLE'},
      {name: 'cost', type: 'FLOAT64', mode: 'NULLABLE'},
      {name: 'conversions', type: 'FLOAT64', mode: 'NULLABLE'},
      {name: 'conversion_value', type: 'FLOAT64', mode: 'NULLABLE'},
      {name: 'cpa', type: 'FLOAT64', mode: 'NULLABLE'},
      {name: 'roas', type: 'FLOAT64', mode: 'NULLABLE'}
    ]
  };

  ensureDatasetAndTable(projectId, datasetId, 'google_ads_campaigns', campaignSchema);

  // Query campaigns
  var report = AdsApp.report('SELECT campaign.id, campaign.name, campaign.type, campaign.bidding_strategy, campaign.status, metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros, metrics.conversions, metrics.conversion_value, metrics.cost_per_conversion, metrics.value_per_conversion FROM campaign WHERE campaign.status = "ENABLED" AND segments.date DURING YESTERDAY');

  var rows = [];
  var reportRows = report.rows();
  while (reportRows.hasNext()) {
    rows.push(reportRows.next());
  }

  // Convert to BigQuery format
  var bqRows = buildCampaignRows(rows);

  // Insert
  var result = insertRowsToBigQuery(projectId, datasetId, 'google_ads_campaigns', bqRows);
  Logger.log('Campaign sync result: ' + JSON.stringify(result));

  return result;
}
```

## MCC Version

To sync all managed accounts into the same BigQuery dataset, use `executeInParallel()` with account_id and account_name columns for distinction.

### MCC Helper Function

```javascript
function executeInParallel(callback) {
  var accountSelector = AdsApp.accounts();
  var accounts = [];
  var accountIterator = accountSelector.get();

  while (accountIterator.hasNext()) {
    var account = accountIterator.next();
    accounts.push({
      customerId: account.getCustomerId(),
      name: account.getName()
    });
  }

  var results = [];
  for (var i = 0; i < accounts.length; i++) {
    AdsApp.changeSubAccount(accounts[i].customerId);
    try {
      var result = callback(accounts[i].customerId, accounts[i].name);
      results.push({
        customerId: accounts[i].customerId,
        status: 'success',
        result: result
      });
      Logger.log('Account ' + accounts[i].customerId + ' (' + accounts[i].name + '): success');
    } catch (e) {
      results.push({
        customerId: accounts[i].customerId,
        status: 'error',
        error: e.message
      });
      Logger.log('Account ' + accounts[i].customerId + ' (' + accounts[i].name + '): error - ' + e.message);
    }
  }

  return results;
}
```

### MCC Main Function

```javascript
function syncAllAccountsToBigQuery(projectId, datasetId) {
  var allResults = [];

  executeInParallel(function(customerId, accountName) {
    // This callback runs for each managed account
    var syncResult = syncCampaignsToBigQuery(projectId, datasetId);
    return syncResult;
  });

  Logger.log('All accounts processed. Check logs for details.');
}
```

**Key differences:**
- `executeInParallel()` iterates all managed accounts
- Each account's sync function runs independently
- Rows automatically include `account_id` and `account_name` via the conversion function
- All data appends to the same tables in the same dataset
- Dates are consistent across all accounts

## Scheduling Recommendation

**Frequency:** Daily

**Time:** After midnight (typically 12:05 AM or 1:00 AM)
- Google Ads data has a ~3 hour lag (data for "yesterday" is complete by 3 AM PT)
- Scheduling after midnight ensures the previous day's data is fully available
- Avoid scheduling before 3 AM PT if real-time freshness is critical

**Example:** Schedule for 1:00 AM every day in the account's local timezone.

## CONFIG Template

Create a CONFIG object at the top of the script for all required settings.

```javascript
var CONFIG = {
  // BigQuery Settings
  GCP_PROJECT_ID: 'your-gcp-project-id',
  BQ_DATASET_ID: 'google_ads_data',

  // Data Sync Settings
  SYNC_CAMPAIGNS: true,
  SYNC_AD_GROUPS: true,
  SYNC_KEYWORDS: true,
  SYNC_SEARCH_TERMS: true,

  // MCC Mode
  // Set to true to sync all managed accounts, false to sync current account only
  MCC_MODE: false,

  // Logging
  LOG_LEVEL: 'INFO', // 'INFO', 'DEBUG', 'ERROR'
  SEND_EMAIL_ON_ERROR: false,
  ERROR_EMAIL: 'your-email@domain.com'
};
```

### CONFIG Usage in Main Function

```javascript
function main() {
  try {
    Logger.log('Starting BigQuery sync...');

    if (CONFIG.SYNC_CAMPAIGNS) {
      syncCampaignsToBigQuery(CONFIG.GCP_PROJECT_ID, CONFIG.BQ_DATASET_ID);
    }

    if (CONFIG.SYNC_AD_GROUPS) {
      syncAdGroupsToBigQuery(CONFIG.GCP_PROJECT_ID, CONFIG.BQ_DATASET_ID);
    }

    if (CONFIG.SYNC_KEYWORDS) {
      syncKeywordsToBigQuery(CONFIG.GCP_PROJECT_ID, CONFIG.BQ_DATASET_ID);
    }

    if (CONFIG.SYNC_SEARCH_TERMS) {
      syncSearchTermsToBigQuery(CONFIG.GCP_PROJECT_ID, CONFIG.BQ_DATASET_ID);
    }

    Logger.log('BigQuery sync completed successfully');
  } catch (e) {
    Logger.log('Error: ' + e.message);
    if (CONFIG.SEND_EMAIL_ON_ERROR) {
      MailApp.sendEmail(CONFIG.ERROR_EMAIL, 'Google Ads Script Error', e.message);
    }
  }
}
```

## Common Issues & Solutions

### Cost is in Micros (Divide by 1,000,000)

GAQL returns `metrics.cost_micros` as an integer representing cost in millionths of the currency unit.

```javascript
// Wrong:
var cost = metrics.costMicros;

// Correct:
var cost = metrics.costMicros / 1000000;
```

Always divide by 1,000,000 when inserting into BigQuery. Other metrics (like `cost_per_conversion`) are already in the correct units.

### BigQuery insertAll Batch Limits

`insertAll()` has soft limits:
- ~500 rows per request
- ~10 MB total request size
- Batching prevents timeouts and quota errors

**Solution:** Always batch inserts in chunks of 500 rows or less (see batching example above).

### Date Formatting

GAQL returns dates as `YYYY-MM-DD` strings. BigQuery DATE type expects the same format.

```javascript
// GAQL returns: '2024-03-27'
// BigQuery DATE type accepts: '2024-03-27'
// No conversion needed.

var dateString = Utilities.formatDate(yesterday, 'America/Los_Angeles', 'yyyy-MM-dd');
// Result: '2024-03-27' ✓
```

### Dataset/Table Auto-Creation on First Run

The `ensureDatasetAndTable()` function creates missing infrastructure automatically. On the first run:
1. Script checks if dataset exists
2. If missing, creates it
3. Script checks if table exists
4. If missing, creates it with the provided schema

**No manual BigQuery setup is required.** The script is self-bootstrapping.

### Keywords or Search Terms Iterator Limit (50K+ Results)

For accounts with 50,000+ keywords, GAQL report iterators may time out or hit limits.

**Solution:** Filter by campaign or label to reduce the dataset:

```javascript
// Original query
SELECT keyword.id, keyword.text FROM keyword_view
WHERE campaign.status = 'ENABLED' AND segments.date DURING YESTERDAY

// Filtered by campaign (sync one campaign at a time)
SELECT keyword.id, keyword.text FROM keyword_view
WHERE campaign.id = '123456789' AND segments.date DURING YESTERDAY

// Or filtered by label
SELECT keyword.id, keyword.text FROM keyword_view
WHERE campaign.labels CONTAINS ALL ('sync_to_bq') AND segments.date DURING YESTERDAY
```

Alternative: Query for a specific date range instead of YESTERDAY:

```javascript
WHERE segments.date >= '2024-03-26' AND segments.date <= '2024-03-26'
```

### Null/Undefined Metrics

If a campaign has 0 impressions, some metrics may be null or undefined. Always use `||` to default to 0:

```javascript
impressions: metrics.impressions || 0,
conversions: metrics.conversions || 0,
```

### Verifying Data in BigQuery

After the script runs, verify the data was inserted:

```sql
SELECT COUNT(*) as total_rows FROM `project-id.google_ads_data.google_ads_campaigns` WHERE date = '2024-03-26';
```

Check for errors:

```javascript
Logger.log('Errors: ' + JSON.stringify(errors));
```

Errors appear in the Apps Script logs. Common errors:
- Schema mismatch (field type doesn't match data)
- Authentication failure (BigQuery API not enabled or permissions lacking)
- Invalid project ID or dataset ID
