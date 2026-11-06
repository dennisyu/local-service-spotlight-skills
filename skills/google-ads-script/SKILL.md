---
name: google-ads-script
description: >
  Generate production-ready Google Ads Scripts (JavaScript) for automating campaign
  management, data pipelines, monitoring, and reporting. Trigger whenever someone asks to
  write, build, create, or fix a Google Ads script, including BigQuery sync, Quality Score
  tracking, search term mining, conversion health checks, bid/budget automation, alerts, or
  Sheet exports. Also trigger on "Google Ads script for [task]", "automate my Google Ads",
  "write a script that [does X]", "ads script to BigQuery", "budget pacing script", "MCC
  script", or any JavaScript automation within Google Ads. Generates actual script code,
  does NOT analyze performance data (use google-ads-analyzer for MAA reports/audits).
  "Analyze" or "audit" = analyzer skill. "Write a script" or "automate" = this skill.
---

# Google Ads Script Builder

Generate production-ready Google Ads Scripts that follow Google's conventions, handle errors
gracefully, and are ready to paste into the Google Ads Scripts IDE.

## What This Skill Does

This skill writes complete, working Google Ads Scripts for specific automation tasks. Every
script it produces follows a consistent structure, uses the correct API patterns, and
includes a CONFIG block so the user can customize it without touching the logic. The output
is a single JavaScript file the user can paste directly into the Google Ads Scripts editor.

The skill covers two categories of work:

- **Pattern-based scripts**: Common use cases with well-established approaches (BigQuery
  sync, Quality Score tracking, search term mining, conversion health checks, budget pacing,
  etc.). For these, read the matching reference file before generating code, they contain
  tested patterns and important gotchas.
- **Custom scripts**: One-off automation requests that don't match a known pattern. Use the
  core API reference and code patterns to build these from scratch.

## Before Writing Any Script

1. **Clarify the requirements.** Scripts are specific, a vague ask produces a useless
   script. Understand at minimum: what data or entities the script touches, what action it
   takes (read, write, alert, export), and where the output goes (Sheets, BigQuery, email,
   back into the account).

2. **Determine the scope.** Is this a single-account script or an MCC script that runs
   across multiple accounts? MCC scripts use `AdsManagerApp` as the root and require
   `executeInParallel()` for cross-account work. Single-account scripts use `AdsApp`.

3. **Read the relevant reference file.** If the request matches a known pattern, read the
   corresponding file in `references/` before writing code. These patterns encode lessons
   learned, quota workarounds, date handling edge cases, schema decisions that prevent
   headaches later.

## Script Structure Convention

Every script follows this four-section layout. This is non-negotiable, it makes scripts
readable, maintainable, and reusable across accounts.

```javascript
// ============================================================================
// CONFIGURATION, Edit this section to customize the script
// ============================================================================
const CONFIG = {
  // All user-editable settings go here
  // Group by purpose: output destinations, thresholds, behavior flags
};

// ============================================================================
// UTILITIES, Reusable helper functions
// ============================================================================
// Date formatting, error logging, email sending, sheet helpers

// ============================================================================
// MAIN LOGIC, The core work of the script
// ============================================================================
// Data collection, processing, output writing

// ============================================================================
// ENTRY POINT
// ============================================================================
function main() {
  try {
    // Orchestration logic
  } catch (e) {
    Logger.log('ERROR: ' + e.message);
    // Error notification if configured
  }
}
```

### CONFIG Block Rules

The CONFIG block is the only section a non-technical user should need to touch. Every
configurable value belongs here, no magic numbers buried in logic functions.

Required CONFIG fields for every script:
- `SEND_EMAIL_ON_ERROR: true` and `ERROR_EMAIL: 'user@email.com'`, every script should
  be able to alert on failure
- `TIME_ZONE: 'America/Denver'`, default to Mountain Time (user's timezone), always use
  for date formatting
- `DRY_RUN: true`, for scripts that modify the account, include a dry-run mode that logs
  what would change without actually changing it

Common CONFIG fields by script type:
- **Sheet output**: `SPREADSHEET_URL`, `SHEET_NAME`
- **BigQuery output**: `BQ_PROJECT_ID`, `BQ_DATASET_ID`, `BQ_TABLE_ID`
- **Thresholds**: named descriptively, `MIN_CLICKS_FOR_EVALUATION`, `MAX_CPA_THRESHOLD`
- **Date ranges**: `DATE_RANGE` using Google's predefined constants or custom ranges
- **MCC scripts**: `ACCOUNT_LABEL` to filter which managed accounts to process

### Naming Conventions

- Variables: `lowerCamelCase`, `campaignName`, `totalCost`
- Constants: `ALL_CAPS`, `MAX_CPC`, `SHEET_NAME`
- Functions: `lowerCamelCase`, `getCampaignStats()`, `writeToSheet()`
- CONFIG keys: `ALL_CAPS`, `BQ_PROJECT_ID`, `DATE_RANGE`

### Error Handling

Every script wraps `main()` in try/catch. For scripts that process multiple entities
(campaigns, keywords, accounts), catch errors at the entity level too so one failure
doesn't kill the whole run:

```javascript
for (const campaign of campaigns) {
  try {
    processCampaign(campaign);
  } catch (e) {
    Logger.log('Error processing ' + campaign.getName() + ': ' + e.message);
    errors.push({campaign: campaign.getName(), error: e.message});
  }
}
```

### Date Handling

Dates are a common source of bugs in Google Ads Scripts. Key patterns:

- Use `Utilities.formatDate(new Date(), CONFIG.TIME_ZONE, 'yyyy-MM-dd')` for consistent
  formatting
- GAQL date ranges use `YYYYMMDD` format (no dashes): `segments.date DURING [20260301, 20260327]`
- For "yesterday" in GAQL: use the predefined `YESTERDAY` constant or compute it:
  ```javascript
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const yyyymmdd = Utilities.formatDate(yesterday, CONFIG.TIME_ZONE, 'yyyyMMdd');
  ```
- The predefined date ranges (`LAST_7_DAYS`, `LAST_30_DAYS`, `YESTERDAY`, etc.) are the
  safest option when they fit the use case

## Known Use-Case Patterns

For these common requests, **always read the matching reference file first**. The reference
files contain field-level schema details, tested GAQL queries, and important constraints
that aren't obvious from the API docs alone.

| Request | Reference File | Key Capability |
|---------|---------------|----------------|
| Sync Google Ads data to BigQuery | `references/bigquery-sync.md` | Daily push of campaign/keyword/search term data to BQ tables |
| Track Quality Score over time | `references/quality-score-tracker.md` | Daily QS snapshots with component breakdown |
| Mine search terms / manage negatives | `references/search-term-mining.md` | Flag waste, stage negative keyword candidates |
| Check conversion tracking health | `references/conversion-health-check.md` | Detect accounts with spend but no conversions firing |
| General API reference | `references/api-reference.md` | Core objects, selectors, GAQL syntax, external services |
| Reusable code patterns | `references/code-patterns.md` | Sheet helpers, email builders, BQ insert functions, MCC patterns |

If the user's request doesn't match a known pattern, use `references/api-reference.md` and
`references/code-patterns.md` to build the script from scratch.

## Reporting: AdsApp.search() vs AdsApp.report()

Both accept GAQL queries. Prefer `AdsApp.search()` for new scripts, it returns structured
`GoogleAdsRow` objects with dot-notation access (`row.campaign.name`,
`row.metrics.clicks`), which is cleaner for programmatic processing.

`AdsApp.report()` returns flat dictionary rows accessed by column name string. It works but
is the older pattern.

```javascript
// Preferred: AdsApp.search()
const rows = AdsApp.search(
  'SELECT campaign.name, metrics.clicks, metrics.cost_micros ' +
  'FROM campaign ' +
  'WHERE campaign.status = "ENABLED" ' +
  'AND segments.date DURING LAST_7_DAYS'
);
for (const row of rows) {
  Logger.log(row.campaign.name + ': ' + row.metrics.clicks + ' clicks');
}
```

Note: `metrics.cost_micros` returns cost in micros (millionths of the account currency).
Divide by 1,000,000 to get the actual dollar amount. This is a common gotcha.

## Mutate Operations

For creating or modifying entities beyond what the built-in object model supports (like
Performance Max campaigns or Demand Gen), use `AdsApp.mutate()` and `AdsApp.mutateAll()`:

```javascript
// Single operation
const result = AdsApp.mutate({
  campaignOperation: {
    update: {
      resourceName: 'customers/123/campaigns/456',
      status: 'PAUSED'
    },
    updateMask: 'status'
  }
});

// Batch operations (can be atomic)
const results = AdsApp.mutateAll(operations, {partialFailure: false});
```

Always include `DRY_RUN` protection around mutate calls. Log what would change before
actually changing it.

## MCC Script Pattern

MCC scripts use `AdsManagerApp` and process accounts in parallel:

```javascript
function main() {
  const accounts = AdsManagerApp.accounts()
    .withCondition("LabelNames CONTAINS 'Active'")
    .get();

  accounts.executeInParallel('processAccount', 'afterAllAccounts');
}

function processAccount() {
  // Runs in the context of each managed account
  // AdsApp refers to the current managed account here
  const accountName = AdsApp.currentAccount().getName();
  // ... do work ...
  return JSON.stringify({account: accountName, results: data});
}

function afterAllAccounts(results) {
  // Consolidation callback, runs after all accounts finish
  for (const result of results) {
    if (result.getStatus() === 'OK') {
      const data = JSON.parse(result.getReturnValue());
      // ... aggregate results ...
    }
  }
}
```

Limits: 50 accounts max per `executeInParallel()`, 30 minutes for parallel work + 30
minutes for the callback. If you have more than 50 accounts, filter by label and run
multiple script instances.

## BigQuery Advanced API

Scripts can write directly to BigQuery via the Advanced API (enabled in script editor under
Advanced APIs → BigQuery). Key objects:

- `BigQuery.Datasets.insert()`, create datasets
- `BigQuery.Tables.insert()`, create tables with schemas
- `BigQuery.Tabledata.insertAll()`, insert rows
- `BigQuery.Jobs.query()`, run SQL queries

See `references/bigquery-sync.md` for the full pattern including schema definition, row
insertion, and error handling.

## Execution Limits to Remember

| Limit | Value |
|-------|-------|
| Single-account script timeout | 30 minutes |
| MCC parallel timeout | 30 min parallel + 30 min callback |
| Iterator results per selector | 50,000 |
| withIds() per call | 10,000 IDs |
| Mutations per script | 10,000 |
| Max parallel accounts (MCC) | 50 |
| Log output | 100KB truncation |
| Scripts per account | 250 |

If a script is likely to hit the 50,000 iterator limit, use GAQL with pagination or filter
by label/date to stay within bounds.

## Output Requirements

1. **Deliver the complete script as a code block** in the response, ready to paste into the
   Google Ads Scripts IDE
2. **Add a brief setup guide** after the code: what CONFIG values need to be changed, what
   Advanced APIs need to be enabled (if any), and the recommended scheduling frequency
3. **Note any prerequisites**, like enabling BigQuery Advanced API, creating a destination
   Sheet, or having specific labels already set up in the account
4. If the script modifies the account (bids, status changes, budgets), **default DRY_RUN to
   true** and tell the user to run in preview mode first, review the logs, then flip
   DRY_RUN to false
