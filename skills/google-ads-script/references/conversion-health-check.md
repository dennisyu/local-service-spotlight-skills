# Google Ads Conversion Health Check Script Reference

## Overview

The Conversion Health Check pattern audits whether conversion actions are actually firing in Google Ads accounts. This script catches broken tracking **before** it appears in an MAA report by monitoring:

1. **Campaigns with active spend but zero conversions**, Strong signal of tracking failure
2. **Sudden drops in conversion rate**, Catches partial tracking breaks (some conversions still fire, but most don't)
3. **Conversion actions that have stopped recording**, Identifies disabled or broken actions
4. **High CTR with zero conversions**, Most reliable indicator of broken tracking or dead landing pages

The script runs daily, flags issues by severity (CRITICAL/WARNING/INFO), and logs results to a spreadsheet and email alert. Use for accountability: managers can see exactly when tracking broke and when it was fixed.

---

## Detection Logic

### Check 1: Spend with Zero Conversions

**Purpose:** Flag campaigns burning money with no conversion recording.

**GAQL Query:**
```
SELECT campaign.name, campaign.id, campaign.advertising_channel_type,
       metrics.cost_micros, metrics.conversions, metrics.clicks
FROM campaign
WHERE campaign.status = "ENABLED"
  AND metrics.cost_micros > 0
  AND segments.date DURING LAST_7_DAYS
```

**Logic:**
- Pull the last 7 days of campaign data
- Flag if: `cost_micros > MIN_SPEND_THRESHOLD` (default: $50 = 50,000,000 micros) AND `conversions == 0`
- **Exclude by campaign type:**
  - `advertising_channel_type` = VIDEO (awareness campaigns often don't convert in 7 days)
  - `advertising_channel_type` = DISPLAY (same reason)
  - Campaigns labeled "Exclude Health Check" (explicit opt-out)
- **Exclude new campaigns:** Skip campaigns less than 14 days old (need maturation time)

**Severity:** CRITICAL (if cost > $500 or CTR > 3%), WARNING (if $50-$500 spend)

**Sample flagged result:**
```
Campaign: "Local HVAC Service - Search"
Campaign ID: 123456789
Cost (7 days): $1,245
Conversions: 0
Clicks: 87
→ CRITICAL: High spend ($1,245) with zero conversions. CVR = 0%, CTR = 15/87 = 17.2%
```

---

### Check 2: Conversion Rate Cliff

**Purpose:** Detect sudden drops in conversion performance (partial tracking failures).

**Logic:**
- **Query 1:** Get conversion metrics for LAST_7_DAYS
  ```
  SELECT campaign.name, campaign.id,
         metrics.conversions, metrics.clicks, metrics.cost_micros
  FROM campaign
  WHERE campaign.status = "ENABLED"
    AND segments.date DURING LAST_7_DAYS
  ```

- **Query 2:** Get conversion metrics for the 21 days before the last 7 (prior 4-week baseline)
  ```
  SELECT campaign.name, campaign.id,
         metrics.conversions, metrics.clicks
  FROM campaign
  WHERE campaign.status = "ENABLED"
    AND segments.date DURING LAST_28_DAYS
    AND segments.date NOT DURING LAST_7_DAYS
  ```

**Calculation:**
```
this_week_cvr = this_week_conversions / this_week_clicks (if clicks > 0)
prior_4week_cvr = prior_conversions / prior_clicks (if clicks > 0)

cvr_drop_pct = ((prior_4week_cvr - this_week_cvr) / prior_4week_cvr) * 100

if cvr_drop_pct > CVR_DROP_THRESHOLD (default: 50%):
  FLAG as WARNING
```

**Thresholds (configurable):**
- **50%+ drop:** WARNING (e.g., went from 10% CVR to 5% CVR)
- **75%+ drop:** CRITICAL (e.g., went from 10% CVR to 2.5% CVR)
- **Exclude:** Campaigns with < 10 clicks in baseline period (not enough data)

**Sample flagged result:**
```
Campaign: "NYC Plumbing - Emergency"
Prior 4-week CVR: 8.2% (41 conversions / 500 clicks)
This week CVR: 3.1% (5 conversions / 161 clicks)
Drop: 62% ↓
→ WARNING: Conversion rate dropped 62% week-over-week. Likely tracking issue or landing page breakage.
```

---

### Check 3: Conversion Action Audit

**Purpose:** Identify conversion actions that aren't recording or are misconfigured.

**GAQL Query:**
```
SELECT conversion_action.name, conversion_action.id,
       conversion_action.status, conversion_action.type,
       conversion_action.category,
       metrics.conversions, metrics.all_conversions
FROM conversion_action
WHERE segments.date DURING LAST_7_DAYS
```

**Flags:**
1. **ENABLED but 0 conversions in 7 days**
   - Severity: INFO (unless this is a primary action)
   - Likely causes: misconfigured, nobody triggered it, tracking broken
   - Action: Verify the conversion tag is installed and firing

2. **Status != ENABLED but should be**
   - Check: Is the action `status = PAUSED`, `REMOVED`, or `ARCHIVED`?
   - Severity: WARNING
   - Action: Re-enable if still relevant

3. **All-Conversions > Conversions (dual-count detection)**
   - If `all_conversions >> conversions`, action may be measuring duplicate events
   - Severity: INFO
   - Example: Facebook pixel both as conversion action AND remarketing audience action

**Sample flagged result:**
```
Conversion Action: "Phone Call (CallRail)"
Status: ENABLED
Conversions (7 days): 0
All-Conversions: 0
→ INFO: ENABLED conversion action recorded 0 events in 7 days. Check if CallRail tag is configured.

Conversion Action: "Form Submit"
Status: PAUSED
Conversions: 0
→ WARNING: Form Submit is PAUSED. Re-enable if this should be tracked.
```

---

### Check 4: CTR vs CVR Sanity Check

**Purpose:** Most reliable signal of tracking breakage, high engagement but zero conversions is unnatural.

**Logic:**
```
For each campaign where conversions == 0 in LAST_7_DAYS:
  ctr = clicks / impressions
  if ctr > 3%:
    FLAG as CRITICAL: "High CTR (%X) with zero conversions = broken tracking or dead landing page"
```

**Why this works:**
- CTR > 3% means people are clicking the ads
- If tracking is working, even a poor landing page should convert some % of that traffic
- Zero conversions at 3%+ CTR is statistically impossible for any functioning page
- This is your most reliable "tracking is 100% broken" indicator

**Sample flagged result:**
```
Campaign: "Brand - Search"
Spend: $342
Clicks: 234
Conversions: 0
CTR: 8.5%
→ CRITICAL: 8.5% CTR with ZERO conversions. Tracking is broken or landing page is completely broken.
```

---

## Alert Format

### Alert Severity Levels

```
CRITICAL  → Zero conversions with significant spend (>$500 OR CTR >3%)
            OR CVR dropped >75%
            OR conversion action completely non-functional

WARNING   → Zero conversions with moderate spend ($50-$500)
            OR CVR dropped 50-75%
            OR ENABLED conversion action hasn't fired in 7 days (but is primary action)

INFO      → CVR dropped 25-50% (monitor but not urgent)
            OR conversion action paused/archived
            OR all-conversions > conversions (potential duplicate counting)
```

### Email Alert Content

**Subject Line Example:**
```
[Conv Health] CRITICAL: Local HVAC Services, Campaign "Emergency Service" has $1,245 spend with 0 conversions
```

**Body Structure (HTML table):**
| Account | Campaign | Check Type | Status | Metric | Severity | Suggested Action |
|---------|----------|-----------|--------|--------|----------|------------------|
| Summit HVAC | Emergency Service | Spend + Zero Conv | FAIL | $1,245 / 0 conv | CRITICAL | Check conversion tag installation. Run GA4 debug. |
| Summit HVAC | Seasonal (Video) | Spend + Zero Conv | PASS | $890 / 0 conv (excluded) | PASS | Campaign type excluded from check. |
| Summit HVAC | NYC Plumbing | CVR Cliff | FAIL | 8.2% → 3.1% (-62%) | WARNING | Review landing page. Check if GA4 event firing. |
| Summit HVAC | Phone Calls | Conv Action Audit | FAIL | ENABLED / 0 events | WARNING | Verify CallRail tag is firing. Check account ID. |

**Email Rules:**
- Only send email if there are actual failures (no "all green" emails)
- Sort by severity (CRITICAL first), then by spend amount (highest first)
- Include summary line: "X CRITICAL issues, Y WARNING issues found"
- Include timestamp and account ID/name
- Include link to spreadsheet log

---

## Sheet Log Pattern

### Google Sheet Columns

```
A: Date             (TODAY())
B: Account          (account name)
C: Campaign         (campaign name)
D: Check Type       (Spend+Zero Conv | CVR Cliff | Conv Action | CTR+Zero Conv)
E: Status           (PASS | FAIL)
F: Details          (description of the issue)
G: Spend (7d)       (cost in dollars)
H: Conversions (7d) (raw conversion count)
I: CVR              (conversions / clicks, formatted as %)
J: Actions Taken    (backfill: what was done to fix this)
K: Resolution Date  (backfill: when issue was resolved)
```

### Formatting Rules

- **Red fill (RGB 255, 0, 0):** FAIL status rows (especially CRITICAL)
- **Yellow fill (RGB 255, 255, 0):** WARNING status rows
- **Green fill (RGB 0, 255, 0):** PASS status rows
- **Bold font:** CRITICAL severity rows
- **Freeze header row** (row 1)
- **Auto-filter:** Enable on all columns for easy sorting

### Sample Log Entry

```
Date: 2026-03-27
Account: Summit HVAC
Campaign: Emergency Service
Check Type: Spend + Zero Conv
Status: FAIL (CRITICAL)
Details: $1,245 spend, 0 conversions, 17.2% CTR (234 clicks). CallRail tag likely not firing.
Spend: $1,245.00
Conversions: 0
CVR: 0%
Actions Taken: [backfilled later] "Called client. CallRail account ID was wrong. Re-linked tracking."
Resolution Date: [backfilled later] 2026-03-27
```

---

## Email Alert Pattern

### HTML Email Template

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; font-size: 12px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th { background-color: #333; color: white; padding: 10px; text-align: left; }
        td { border: 1px solid #ddd; padding: 8px; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .critical { background-color: #ffcccc; font-weight: bold; }
        .warning { background-color: #ffffcc; }
        .pass { background-color: #ccffcc; }
        h2 { color: #d32f2f; }
    </style>
</head>
<body>
    <h1>Google Ads Conversion Health Check</h1>
    <p><strong>Run Date:</strong> {TODAY}</p>
    <p><strong>Account:</strong> {ACCOUNT_NAME} ({ACCOUNT_ID})</p>

    <h2>Summary</h2>
    <p>
        <strong style="color: red;">{CRITICAL_COUNT} CRITICAL issues</strong> |
        <strong style="color: orange;">{WARNING_COUNT} WARNING issues</strong> |
        {PASS_COUNT} passing checks
    </p>

    <h2>Issues Found</h2>
    <table>
        <tr>
            <th>Campaign</th>
            <th>Check Type</th>
            <th>Metric</th>
            <th>Severity</th>
            <th>Next Step</th>
        </tr>
        {TABLE_ROWS}
    </table>

    <h2>Recommended Actions</h2>
    <ul>
        {ACTION_LIST}
    </ul>

    <p style="font-size: 10px; color: #999;">
        Conversion Health Check runs daily.
        <a href="{SHEET_URL}">View full history in log sheet</a>.
    </p>
</body>
</html>
```

### Suggested Actions by Check Type

| Check Type | Next Step |
|-----------|-----------|
| Spend + Zero Conv | 1. Verify conversion tag is installed (GTM, hardcode). 2. Check GA4 debug mode. 3. Run test transaction if possible. 4. Check if landing page has redirect loop. |
| CVR Cliff | 1. Review landing page for changes (design, form fields, copy). 2. Check GA4 event configuration (events still firing?). 3. Compare traffic source mix (are low-converting sources getting more spend?). 4. Check if there's a spike in bot traffic. |
| Conv Action | 1. Verify conversion tag installation. 2. Check if conversion action category is correct. 3. Ensure conversion window (click-through vs view-through) matches campaign. |
| High CTR + Zero Conv | 1. This is critical. Check landing page for 404, redirect, or broken form. 2. Verify conversion tag loads on page. 3. Check browser console for errors. 4. Test form submission end-to-end. |

---

## MCC (Manager Account) Version

### Pattern: Multi-Account Aggregation

Use `executeInParallel()` to audit multiple client accounts in parallel, consolidate results, and send one summary email.

**Pseudo-code structure:**

```javascript
function main() {
  const managedAccounts = AdsManagerApp.accounts().get();
  const allResults = [];

  managedAccounts.executeInParallel(
    'runHealthCheck',  // callback function name
    function(accountResult) {
      // Consolidation callback
      if (accountResult.hasNext()) {
        allResults.push(accountResult.next());
      }
    }
  );

  // After all accounts complete, consolidate and alert
  const consolidatedAlerts = consolidateResults(allResults);
  sendConsolidatedEmail(consolidatedAlerts);
  logToSheet(consolidatedAlerts);
}

function runHealthCheck() {
  // Same checks as single-account version
  // Return object: { account, checks: [], alerts: [] }
  const account = AdsApp.currentAccount();
  return {
    accountId: account.getCustomerId(),
    accountName: account.getName(),
    checks: [
      checkSpendWithZeroConv(),
      checkConversionRateCliff(),
      checkConversionActionStatus(),
      checkCTRVsCVR()
    ]
  };
}

function consolidateResults(accountResults) {
  // Group by severity across all accounts
  // Sort: CRITICAL > WARNING > INFO, then by spend
  // Return single alert list for email
  return {
    criticalCount: ...,
    warningCount: ...,
    allAlerts: [...]
  };
}
```

**Key benefits:**
- One email summarizing health issues across all managed accounts
- Parallel execution = faster (runs all accounts simultaneously)
- Callback consolidation = clean, aggregated results
- Easy to filter by severity or account

**Sample MCC email subject:**
```
[MCC Conv Health] 3 CRITICAL issues across 5 accounts
```

---

## CONFIG Template

Create a configuration object at the top of the script:

```javascript
const CONFIG = {
  // Alert settings
  alertEmail: 'alerts@example.com',
  sendOnPass: false,  // only email on failures

  // Spend + Zero Conv thresholds
  minSpendThreshold: 50,  // dollars (50,000,000 micros)
  minSpendForCritical: 500,  // dollars

  // Conversion Rate Cliff thresholds
  cvrDropThreshold: 50,  // percent (50% drop = warning)
  cvrDropCritical: 75,   // percent (75% drop = critical)
  minClicksForCVRCheck: 10,  // need minimum volume for comparison

  // CTR + Zero Conv
  ctrThresholdForCritical: 3,  // percent (3% CTR = critical if 0 conv)

  // Exclusions
  excludeCampaignTypes: ['VIDEO', 'DISPLAY'],
  excludeLabel: 'Exclude Health Check',
  minCampaignAgeInDays: 14,

  // Sheet logging
  sheetUrl: 'https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit',
  sheetName: 'Health Check Log',

  // Lookback period
  lookbackDays: 7,  // LAST_7_DAYS
  priorLookbackDays: 28  // for CVR cliff comparison
};
```

**How to customize:**
- **Lower `minSpendThreshold`** if you want to catch small issues early (e.g., $20)
- **Raise `cvrDropThreshold`** if your account has naturally volatile CVR (increase to 60-70%)
- **Add accounts to `excludeLabel`** to skip specific campaigns from health checks
- **Update `sheetUrl`** to point to your logging sheet
- **Adjust `minCampaignAgeInDays`** for longer conversion cycle businesses (e.g., 30 days)

---

## Scheduling

**Frequency:** Daily (recommended morning, before workday starts)

**Timing:** 8:00 AM account's local timezone

**Why daily?**
- Tracking issues compound fast, waiting a week means lost revenue
- Morning alert gives team time to diagnose and fix
- Early detection = less data loss

**In Google Ads Scripts UI:**
1. Click **"Schedule"** in script editor
2. Select **Daily**
3. Set time to **8:00 AM** (or preferred timezone)
4. Save

**If using MCC:** Set MCC script to run 8:00 AM, which executes across all managed accounts in parallel.

---

## False Positive Management

### Common False Positives and Filters

**False Positive 1: New campaigns in their first week**
- **Problem:** New campaigns legitimately have zero conversions
- **Filter:** Exclude campaigns less than 14 days old
  ```javascript
  const campaignAge = (TODAY - campaign.getCreationDate()) / (24 * 60 * 60);
  if (campaignAge < MIN_CAMPAIGN_AGE_DAYS) return; // skip
  ```
- **Tuning:** Increase `minCampaignAgeInDays` to 21 or 30 for long conversion cycles

**False Positive 2: Very low-spend campaigns**
- **Problem:** A $10 campaign with 0 conversions isn't urgent
- **Filter:** Use `minSpendThreshold` (default: $50)
  ```javascript
  if (cost < CONFIG.minSpendThreshold) return; // skip small campaigns
  ```

**False Positive 3: Awareness campaigns (Video, Display)**
- **Problem:** Awareness campaigns may not convert in 7 days (longer conversion window)
- **Filter:** Exclude by channel type
  ```javascript
  if (CONFIG.excludeCampaignTypes.includes(campaign.getAdvertisingChannelType())) {
    return; // skip VIDEO, DISPLAY
  }
  ```

**False Positive 4: Seasonal or paused campaigns**
- **Problem:** Campaign is intentionally paused or it's off-season
- **Filter:** Apply the "Exclude Health Check" label manually
  ```javascript
  if (campaign.labels().includes(CONFIG.excludeLabel)) {
    return; // skip marked exclusions
  }
  ```

**False Positive 5: Long conversion cycle businesses**
- **Problem:** B2B, HVAC, plumbing may have 14+ day sales cycles
- **Filter:** Increase lookback period or CVR drop threshold
  ```javascript
  CONFIG.lookbackDays = 14; // or 21
  CONFIG.cvrDropThreshold = 60; // more tolerance for drop
  ```

**False Positive 6: CVR cliff due to traffic mix shift**
- **Problem:** More budget to cold traffic / lower-intent keywords naturally lowers CVR
- **Filter:** Add keyword-level check
  ```javascript
  // Optional: Break down CVR by keyword, not just campaign
  // Flag only if high-intent keywords (branded, exact match) drop CVR
  ```

### Label-Based Exclusion Pattern

Add a label "Exclude Health Check" to campaigns you want to skip:

```javascript
function shouldCheckCampaign(campaign) {
  // Check 1: Age filter
  const createdDate = new Date(campaign.getCreationDate());
  const ageInDays = (Date.now() - createdDate) / (1000 * 60 * 60 * 24);
  if (ageInDays < CONFIG.minCampaignAgeInDays) return false;

  // Check 2: Campaign type filter
  if (CONFIG.excludeCampaignTypes.includes(
      campaign.getAdvertisingChannelType())) {
    return false;
  }

  // Check 3: Explicit label exclusion
  const labels = campaign.labels().get();
  while (labels.hasNext()) {
    if (labels.next().getName() === CONFIG.excludeLabel) {
      return false;
    }
  }

  return true; // proceed with checks
}
```

---

## Error Handling and Edge Cases

### GAQL Query Errors

**Common error:** `INVALID_ENUM_VALUE` when filtering by campaign type
- **Fix:** Use exact enum names: `SEARCH`, `DISPLAY`, `VIDEO`, `SHOPPING`, `SMART`
- **Verify:** Campaign type must be a string, not integer ID

**Common error:** `metrics.` fields in WHERE clause
- **Fix:** Metrics can only be in SELECT and custom date ranges, not WHERE filters
- **Correct:** `WHERE segments.date DURING LAST_7_DAYS` (not `metrics.cost_micros > 0`)

### Timezone Issues

- Conversion data is stored in account timezone, not script runtime timezone
- `LAST_7_DAYS` respects the account's timezone automatically
- For custom date ranges, use account timezone:
  ```javascript
  const today = new Date();
  // Subtract 7 days in account timezone
  ```

### API Rate Limits

- MCC scripts can execute across many accounts, if you hit rate limits, add throttling:
  ```javascript
  Utilities.sleep(100); // 100ms between API calls
  ```

### Empty Result Sets

- If a campaign has no impressions, `metrics.clicks` and `metrics.conversions` may be missing entirely
- **Safer:** Default to 0 if field is null
  ```javascript
  const conversions = row.metrics.conversions || 0;
  const clicks = row.metrics.clicks || 0;
  ```

---

## Real-World Implementation Notes

### When Tracking Actually Breaks

**Example 1: CallRail tracking (phone campaigns)**
- CallRail account ID in Google Ads is wrong
- Script flags: Campaign with $2,000 spend, 0 conversions, 12% CTR
- Alert goes out, client checks CallRail, fixes account ID, issue resolved next day

**Example 2: GA4 event not firing**
- GTM container has stale code, new form doesn't fire event
- Script flags: CVR dropped from 6% to 1% week-over-week
- Client checks GA4 debug mode, finds form event missing, fixes container, CVR returns to normal

**Example 3: Landing page 404**
- Campaign gets rebid, budget increases, old landing page accidentally deleted
- Script flags: Campaign with 200 clicks, 0 conversions, 15% CTR (impossible)
- Client gets alert, checks 404, restores landing page, conversions resume same day

### Integration with MAA Workflow

This health check complements MAA reporting:
- **MAA:** "Your conversion rate is 3%, which is below target" (what happened)
- **Health Check:** "Your conversion tracking completely broke yesterday" (why it happened)

Run health check **before** MAA analysis, so you can exclude broken periods from analysis.

---

## Testing the Script

### Test Queries (manually run in Scripts UI)

**Test 1: Verify GAQL syntax**
```javascript
function testGAQL() {
  const report = AdsApp.report(
    'SELECT campaign.name, metrics.cost_micros, metrics.conversions ' +
    'FROM campaign ' +
    'WHERE campaign.status = "ENABLED" ' +
    'AND segments.date DURING LAST_7_DAYS'
  );

  while (report.hasNext()) {
    const row = report.next();
    Logger.log(`${row.campaign.name}: ${row.metrics.cost_micros}, ${row.metrics.conversions}`);
  }
}
```

**Test 2: Verify email sending**
```javascript
function testEmail() {
  MailApp.sendEmail(
    'your@email.com',
    '[TEST] Conv Health Check',
    'Test email body'
  );
  Logger.log('Email sent');
}
```

**Test 3: Verify sheet logging**
```javascript
function testSheet() {
  const ss = SpreadsheetApp.openByUrl(CONFIG.sheetUrl);
  const sheet = ss.getSheetByName(CONFIG.sheetName);
  sheet.appendRow(['2026-03-27', 'Test Account', 'Test Campaign', 'TEST', 'FAIL', 'Test entry', 100, 0, '0%']);
  Logger.log('Sheet entry added');
}
```

**Before going live:**
1. Run `testGAQL()`, verify you're getting campaign data
2. Run `testEmail()`, verify email goes to your inbox
3. Run `testSheet()`, verify rows appear in the sheet
4. Manually run `main()` once, check output in Logs
5. Schedule the script for daily execution

