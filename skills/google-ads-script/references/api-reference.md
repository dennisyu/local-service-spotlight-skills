# Google Ads Script API Reference

Dense, code-first reference for generating any Google Ads Script. All examples assume modern syntax (AdsScript v2+).

---

## 1. AdsApp Object Model & Traversal

### Entity Hierarchy
```
AdsApp
├── campaigns()
├── adGroups()
├── keywords()
├── ads()
└── adGroupCriteria()
```

### Selector Pattern
All selectors return `AdGroupIterator`, `CampaignIterator`, etc.

```javascript
// Basic traversal
const campaigns = AdsApp.campaigns()
  .withCondition("Status = ENABLED")
  .withIds([12345, 67890])
  .withLimit(100)
  .orderBy("Clicks DESC")
  .forDateRange("20240101", "20240131")
  .get();

// Nested traversal
const campaign = AdsApp.campaigns().withIds([12345]).get().next();
const adGroups = campaign.adGroups();
const keywords = campaign.keywords();
```

### Iterator Pattern
```javascript
for (const item of iterator) {
  Logger.log(item.getName());
  // item is campaign/keyword/ad/etc
}

// Alternative: while loop
const iterator = AdsApp.campaigns().get();
while (iterator.hasNext()) {
  const campaign = iterator.next();
}
```

### Stats Retrieval
```javascript
const stats = campaign.getStatsFor('LAST_7_DAYS'); // or LAST_30_DAYS, ALL_TIME, etc
stats.getClicks();          // number
stats.getImpressions();     // number
stats.getCost();            // number in account currency
stats.getConversions();     // number
stats.getConversionValue(); // number
stats.getCtr();             // 0.05 = 5%
stats.getAverageCpc();      // number
stats.getAveragePosition(); // number
```

Date range options: `TODAY`, `YESTERDAY`, `LAST_7_DAYS`, `LAST_14_DAYS`, `LAST_30_DAYS`, `THIS_WEEK_SUN_TODAY`, `LAST_WEEK`, `LAST_MONTH`, `ALL_TIME`.

---

## 2. GAQL Quick Reference

### Syntax
```
resource WHERE condition ORDER BY field LIMIT n
```

### Common Resources & Fields
| Resource | Key Fields |
|----------|-----------|
| campaign | id, name, status, budget_amount, labels |
| ad_group | id, name, status, campaign_id |
| ad_group_criterion | id, status, type, keyword.text, bid_modifier |
| ad | id, status, type, headlines, description1, description2 |
| ad_group_ad | ad, ad_group |
| feed_item | id, status, attribute_values |

### Operators
- `=`, `!=`, `<`, `>`, `<=`, `>=`
- `IN [val1, val2]`, `NOT IN`
- `LIKE`, `NOT LIKE` (for partial match)
- `DURING`, `BETWEEN` (for dates)
- `IS NULL`, `IS NOT NULL`

### Query Examples
```javascript
const query = `
  SELECT campaign.id, campaign.name, metrics.clicks
  FROM campaign
  WHERE campaign.status = 'ENABLED'
    AND metrics.clicks > 10
  ORDER BY metrics.clicks DESC
  LIMIT 10
`;
```

---

## 3. Entity Methods

### Campaign
```javascript
const id = campaign.getId();
const name = campaign.getName();
const status = campaign.getStatus(); // ENABLED, PAUSED, REMOVED

campaign.pause();
campaign.enable();
campaign.remove();

const label = campaign.applyLabel('my-label');
campaign.removeLabel('my-label');
const labels = campaign.getLabels(); // array of label strings

const budget = campaign.getBudget();
budget.setAmount(1000.00);

const bidding = campaign.bidding();
bidding.getStrategyType(); // e.g., "TARGET_SPEND", "MAXIMIZE_CONVERSIONS"
```

### AdGroup
```javascript
const adGroup = campaign.adGroups().withIds([ag_id]).get().next();

adGroup.getId();
adGroup.getName();
adGroup.getStatus();
adGroup.pause();
adGroup.enable();
adGroup.remove();

adGroup.applyLabel('label');
adGroup.removeLabel('label');

const bidding = adGroup.bidding();
bidding.setCpc(1.50);
bidding.getCpc();
```

### Keyword
```javascript
const keyword = adGroup.keywords().withIds([kw_id]).get().next();

keyword.getId();
keyword.getText();        // The actual keyword text
keyword.getMatchType();   // EXACT, PHRASE, BROAD
keyword.getStatus();
keyword.getQualityScore(); // 1-10 or null

keyword.pause();
keyword.enable();
keyword.remove();

keyword.applyLabel('label');
keyword.removeLabel('label');

// Bidding
const bidding = keyword.bidding();
bidding.setCpc(2.00);
bidding.getCpc();
bidding.clearCpc();
```

### Ad (Responsive Search Ad, etc.)
```javascript
const ad = adGroup.ads().withIds([ad_id]).get().next();

ad.getId();
ad.getType(); // "RESPONSIVE_SEARCH_AD", "TEXT_AD", etc
ad.getStatus();
ad.pause();
ad.enable();
ad.remove();

ad.asType().getHeadlines();  // array of headlines
ad.asType().getDescriptions(); // array of descriptions
```

### Navigation
```javascript
const campaign = keyword.getCampaign();
const adGroup = keyword.getAdGroup();
const adGroup2 = ad.getAdGroup();
const campaign2 = adGroup.getCampaign();
```

---

## 4. AdsApp.search() vs AdsApp.report()

### search(), For Iterating Entities
- Returns **iterators** (campaign/keyword/ad objects)
- Lazy evaluation, only fetches what you iterate
- Best for: Modifying entities, building lists, entity navigation
- **Most common in scripts**

```javascript
const campaigns = AdsApp.campaigns()
  .withCondition("Status = ENABLED")
  .get();

for (const campaign of campaigns) {
  campaign.pause();
}
```

### report(), For Analytics & Aggregation
- Returns **rows of data** (not objects)
- Faster for large data pulls; built-in stats
- Best for: Reporting, metrics, analysis, large exports
- Returns `AdsApp_Report`; iterate with `.rows()`

```javascript
const report = AdsApp.report(`
  SELECT campaign.name, metrics.clicks, metrics.cost
  FROM campaign
  WHERE campaign.status = 'ENABLED'
  DURING LAST_7_DAYS
`);

for (const row of report.rows()) {
  Logger.log(row['campaign.name']);
  Logger.log(row['metrics.clicks']);
}
```

---

## 5. AdsApp.mutate() & AdsApp.mutateAll()

### Single Mutation: `AdsApp.mutate()`
```javascript
const mutationRequest = {
  createOperations: [
    {
      create: {
        resourceName: 'customers/1234567890/campaigns',
        name: 'New Campaign',
        status: 'PAUSED',
        budget: { amountMicros: '1000000000' } // $1.00 in micros
      }
    }
  ],
  updateOperations: [
    {
      update: {
        resourceName: 'customers/1234567890/campaigns/987654321',
        name: 'Updated Name',
        status: 'ENABLED'
      },
      updateMask: { paths: ['name', 'status'] }
    }
  ],
  removeOperations: [
    {
      remove: 'customers/1234567890/campaigns/111111111'
    }
  ]
};

const response = AdsApp.mutate(mutationRequest);
Logger.log(response);
```

### Batch Mutations: `AdsApp.mutateAll()`
```javascript
const requests = [
  {
    createOperations: [{
      create: { resourceName: 'customers/.../campaigns', name: 'Camp1' }
    }]
  },
  {
    updateOperations: [{
      update: { resourceName: 'customers/.../campaigns/123' },
      updateMask: { paths: ['name'] }
    }]
  }
];

const responses = AdsApp.mutateAll(requests, { partialFailure: true });
responses.forEach(response => Logger.log(response));
```

### Key Details
- **resourceName**: Full resource path (customers/CID/resource_type/ID)
- **updateMask.paths**: List which fields are being updated (avoid overwriting unintended fields)
- **partialFailure: true**: Some operations succeed even if others fail
- Amounts in **micros** (multiply dollars by 1,000,000)

---

## 6. External Services

### SpreadsheetApp
```javascript
const sheet = SpreadsheetApp.openByUrl('https://docs.google.com/...');
const data = sheet.getSheetByName('Sheet1');

data.appendRow(['Header1', 'Header2', 'Header3']);
data.appendRow([value1, value2, value3]);

// Get & set ranges
const range = data.getRange('A1:C10');
range.setValues([[1, 2, 3], [4, 5, 6]]);

// Formatting
range.setBackground('#FF0000');
range.setFontSize(12);
range.setNumberFormat('0.00%');

const values = data.getRange('A:A').getValues(); // 2D array
```

### MailApp
```javascript
MailApp.sendEmail('recipient@domain.com', 'Subject Line', 'Plain text body');

MailApp.sendEmail(
  'recipient@domain.com',
  'Subject',
  'Plain text (fallback)',
  {
    htmlBody: '<h1>HTML Title</h1><p>HTML content</p>',
    attachments: [blob],
    cc: 'cc@domain.com',
    bcc: 'bcc@domain.com',
    replyTo: 'reply@domain.com'
  }
);
```

### UrlFetchApp
```javascript
// GET request
const response = UrlFetchApp.fetch('https://api.example.com/data');
const json = JSON.parse(response.getContentText());

// POST with auth
const options = {
  method: 'post',
  headers: { 'Authorization': 'Bearer ' + apiToken },
  payload: JSON.stringify({ key: 'value' }),
  contentType: 'application/json',
  muteHttpExceptions: true
};

const response = UrlFetchApp.fetch('https://api.example.com/create', options);
if (response.getResponseCode() === 200) {
  const data = JSON.parse(response.getContentText());
}
```

### Utilities
```javascript
Utilities.sleep(5000); // 5 seconds
Utilities.formatDate(new Date(), 'GMT', 'yyyyMMdd'); // '20240315'
const encoded = Utilities.base64Encode('text');
const decoded = Utilities.base64Decode(encoded);
Utilities.getUuid(); // random UUID
```

---

## 7. Advanced APIs

### Enabling Advanced APIs
Script Editor → Services (⚙) → Add Google Sheets API, BigQuery, etc.

### Common Advanced APIs
- **BigQuery**: `BigQueryApp.getDataset()`, query large datasets
- **Google Analytics 4**: `AnalyticsAdmin`, fetch GA4 properties, goals, conversions
- **YouTube**: `YouTubeApp`, manage channel, playlists, videos
- **Google Calendar**: `CalendarApp`, schedule events, manage calendars
- **Google Drive**: `DriveApp`, list/create/delete files and folders
- **Google Slides**: `SlidesApp.openById()`, create/modify presentations
- **Google Merchant Center**: Access via Google Ads scripts for Shopping data

```javascript
// BigQuery example
const dataset = BigQueryApp.getDataset('project_id', 'dataset_id');
const results = dataset.query('SELECT * FROM table WHERE ...');
for (const row of results) {
  Logger.log(row);
}
```

---

## 8. MCC (Multi-Client Manager Accounts)

### Basic MCC Traversal
```javascript
const clientAccounts = AdsManagerApp.accounts().get();

for (const account of clientAccounts) {
  const accountId = account.getCustomerId(); // MCC-managed account ID
  AdsManagerApp.select(account);

  // Now AdsApp works in context of this account
  const campaigns = AdsApp.campaigns().get();
}
```

### Parallel Execution
Execute logic across multiple accounts (up to **50 accounts per batch**):

```javascript
const operation = function(accountId) {
  // This runs in context of accountId
  const campaigns = AdsApp.campaigns().withCondition("Status = ENABLED").get();
  for (const campaign of campaigns) {
    campaign.pause();
  }
  return `Processed ${accountId}`;
};

AdsManagerApp.accounts()
  .executeInParallel('operation', 'AdsManagerApp');
```

### Limits
- Max **50 accounts** per `executeInParallel()` call
- Callback function name must be global (top-level)
- Each account context is isolated

---

## 9. Execution Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Script timeout | 30 minutes | Hard limit; use `time.remaining()` to check |
| Iterator size | ~50k entities | Read with `getRange()` for limits |
| Mutations per call | Unlimited | But check time/quota |
| API quota | 50,000/day | Per customer/MCC; resets daily |
| Spreadsheet cells | 2M | Max size per sheet |
| Email recipients | 500/day | Per script execution |
| Advanced API calls | 250k/day | Varies by API |

```javascript
// Check time remaining
const timeRemaining = AdsApp.getExecutionInfo().getRemainingTime();
if (timeRemaining < 60000) {
  // Less than 1 min; exit and reschedule
  return;
}
```

---

## 10. Labels

### Create & Apply Labels
```javascript
// Create label (idempotent, safe to call multiple times)
AdsApp.createLabel('my-pause-label', 'Label for pausing', '#FF0000');

// Apply to campaign
const label = campaign.applyLabel('my-pause-label');
const label2 = campaign.applyLabel('another-label');

// Check labels
const labels = campaign.getLabels(); // ['my-pause-label', 'another-label']

// Remove label
campaign.removeLabel('my-pause-label');
```

### Filter by Label
```javascript
// Selector with label filter
const campaigns = AdsApp.campaigns()
  .withCondition("LabelIds CONTAINS 12345") // Use label ID
  .get();

// Or by label name (less common)
const labeled = AdsApp.campaigns()
  .withCondition("Labels CONTAINS 'my-label'")
  .get();
```

### GAQL Label Filter
```javascript
const query = `
  SELECT campaign.id, campaign.name
  FROM campaign
  WHERE labels CONTAINS 'my-pause-label'
`;
const report = AdsApp.report(query);
```

### Label Use Cases
- **Org/Tagging**: Label campaigns by client, region, product
- **Batch Operations**: Label entities for bulk pause/adjust/remove
- **Filtering**: Quickly select subsets without complex conditions
- **Audit Trail**: Apply labels before modifications for tracking

---

## Quick Patterns

### Pattern: Pause All Low-CTR Keywords
```javascript
for (const campaign of AdsApp.campaigns().get()) {
  for (const adGroup of campaign.adGroups().get()) {
    for (const keyword of adGroup.keywords().forDateRange('LAST_30_DAYS').get()) {
      const stats = keyword.getStatsFor('LAST_30_DAYS');
      if (stats.getClicks() > 10 && stats.getCtr() < 0.01) {
        keyword.pause();
      }
    }
  }
}
```

### Pattern: Adjust Bids by Performance
```javascript
for (const keyword of AdsApp.keywords().withCondition("QualityScore >= 7").get()) {
  const stats = keyword.getStatsFor('LAST_7_DAYS');
  const currentCpc = keyword.bidding().getCpc();
  if (stats.getConversions() > 5 && stats.getCost() < 50) {
    keyword.bidding().setCpc(currentCpc * 1.1); // +10%
  }
}
```

### Pattern: Export Campaign Performance
```javascript
const sheet = SpreadsheetApp.openByUrl('SHEET_URL');
const tab = sheet.getSheetByName('Report');
tab.clearContents();
tab.appendRow(['Campaign', 'Clicks', 'Cost', 'Conversions', 'ROAS']);

for (const campaign of AdsApp.campaigns().get()) {
  const stats = campaign.getStatsFor('LAST_30_DAYS');
  tab.appendRow([
    campaign.getName(),
    stats.getClicks(),
    stats.getCost(),
    stats.getConversions(),
    stats.getConversions() > 0 ? (stats.getConversions() / stats.getCost()) : 0
  ]);
}
```

---

**Last Updated**: 2026-03-27
**Scope**: Google Ads Scripts v2+, Google Ads API v16+
