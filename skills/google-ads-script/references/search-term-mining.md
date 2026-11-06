# Search Term Mining & Negative Keyword Management

## Overview

This pattern pulls search term data from the past 30 days, identifies problematic queries that are consuming budget without driving conversions, and stages negative keyword candidates in a Google Sheet for human review before adding them to campaigns.

**What it accomplishes:**
- Extracts all search terms triggering ads in active campaigns
- Flags terms with significant spend but zero conversions
- Identifies high-CPA terms exceeding account thresholds
- Detects known waste patterns (job-seekers, DIY, free/cheap queries, wrong geography, review-seekers)
- Stages negatives in a Sheet for manual approval
- Optionally auto-adds high-confidence negatives to campaigns or shared negative lists
- Tracks additions and provides summary metrics for account optimization

**Why it matters for local service businesses:**
Job seekers searching "electrician jobs" or "HVAC technician career" trigger ads built for customers, not employment candidates. DIY queries drain budget on people who won't hire. "Free" and "cheap" queries attract tire-kickers. Geographic mismatches (your city name + "near me" from outside your service area) waste impressions. This pattern catches and eliminates that waste systematically.

---

## GAQL Query

```sql
SELECT
  campaign.name,
  campaign.id,
  ad_group.name,
  ad_group.id,
  search_term_view.search_term,
  search_term_view.status,
  keyword.info.text,
  keyword.info.match_type,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions
FROM search_term_view
WHERE campaign.status = "ENABLED"
  AND metrics.impressions > 0
  AND segments.date DURING LAST_30_DAYS
```

**Key fields explained:**

- `search_term_view.search_term`, The actual query a user searched
- `search_term_view.status`, One of three values:
  - `ADDED`, Term is already added as a keyword in the account
  - `EXCLUDED`, Term is already added as a negative keyword
  - `NONE`, Term has triggered ads but no keyword action has been taken yet
- `keyword.info.text` and `.match_type`, The keyword (if any) that matched this search term
- `metrics.cost_micros`, Cost in microdollars; divide by 1,000,000 for USD
- `metrics.conversions`, Conv count; 0 means no conversions from this term

**Note:** This query returns all search terms. Filter and flag within the script using the waste detection logic.

---

## Waste Detection Logic

Flag a search term as a candidate for negating if it meets ANY of these conditions:

### 1. Zero-Conversion Spend Drain
```javascript
const MIN_COST_THRESHOLD = 20; // dollars
if (clicks > 0 && conversions === 0 && cost > MIN_COST_THRESHOLD) {
  flagReason = "Zero conversions with significant spend";
}
```

A term with 5+ clicks and $20+ cost but no conversions is burning money. Lower the threshold for high-volume accounts; raise it for low-volume.

### 2. High-CPA Terms
```javascript
const accountAverageCPA = 75; // dollars, compute from metrics
const MAX_CPA_MULTIPLIER = 2.0; // 2x the account average

if (conversions > 0) {
  const termCPA = cost / conversions;
  if (termCPA > accountAverageCPA * MAX_CPA_MULTIPLIER) {
    flagReason = `High CPA: $${termCPA.toFixed(2)} vs account avg $${accountAverageCPA}`;
  }
}
```

This finds terms that convert but at an unsustainable cost. Useful for identifying underperforming keywords.

### 3. Known Waste Patterns (Regex)

Apply these patterns. If a search term matches ANY, flag it:

```javascript
const WASTE_PATTERNS = [
  // Job-seekers
  /\b(jobs?|hiring|career|salary|pay|wage|employee|work for|employment)\b/i,

  // DIY intent
  /\b(diy|how to|tutorial|yourself|self|homemade|install myself)\b/i,

  // Price-conscious only
  /\b(free|cheap|discount|coupon|deal|sale|budget)\b/i,

  // Wrong intent (reviews, complaints, legal)
  /\b(reviews?|complaint|lawsuit|scam|reddit|negative|bad|avoid)\b/i,

  // Education/certification seekers
  /\b(course|class|certification|school|degree|training|license)\b/i
];

const searchTermLower = searchTerm.toLowerCase();
for (const pattern of WASTE_PATTERNS) {
  if (pattern.test(searchTermLower)) {
    flagReason = "Matches known waste pattern";
    break;
  }
}
```

### 4. Geographic Mismatches

Flag search terms containing city names outside your service area:

```javascript
const TARGET_CITIES = ["Denver", "Boulder", "Fort Collins"]; // CONFIG
const geoPattern = new RegExp(`\\b(${TARGET_CITIES.join('|')})\\b`, 'i');

// Extract any city name from the search term (requires a city database or manual list)
const containsOutsideCity = searchTerm.match(/\b(Phoenix|Seattle|Austin|Houston)\b/i);
if (containsOutsideCity && !geoPattern.test(searchTerm)) {
  flagReason = "Search term contains city outside service area";
}
```

Alternative: Track geographic signals in your account and flag searches from IP geolocations far from your service area. Use the `segments.geo_target_constant` if available in your query.

---

## Output Structure

Write flagged terms to a Google Sheet with three tabs:

### Tab 1: "Flagged Terms"

| Date | Campaign | Ad Group | Search Term | Matched Keyword | Impressions | Clicks | Cost | Conversions | CPA | Flag Reason | Action |
|------|----------|----------|-------------|-----------------|-------------|--------|------|-------------|-----|-------------|--------|
| 2026-03-27 | HVAC Spring | Furnace Repair | furnace jobs | furnace repair | 12 | 3 | $28.50 | 0 | N/A | Zero conversions with significant spend | Add Negative |
| 2026-03-27 | HVAC Spring | AC Install | how to install ac | ac installation | 8 | 2 | $15.80 | 0 | N/A | Matches known waste pattern (DIY) | Add Negative |

**Columns:**
- **Date**, When the term was flagged (run date)
- **Campaign**, Campaign name from the query
- **Ad Group**, Ad group name from the query
- **Search Term**, The actual search query
- **Matched Keyword**, The keyword that triggered this term (helps you understand why the ad showed)
- **Impressions, Clicks, Cost, Conversions**, Raw metrics
- **CPA**, Cost ÷ Conversions (blank if no conversions)
- **Flag Reason**, Why it was flagged (pull from waste detection logic)
- **Action**, Dropdown with three values: "Add Negative", "Ignore", "Review" (default is "Review")

**Sort by Cost descending** so the biggest waste floats to the top.

### Tab 2: "Auto-Added Negatives"

| Date Added | Campaign | Negative Keyword | Match Type | Status | Added By |
|------------|----------|------------------|-----------|--------|----------|
| 2026-03-25 | HVAC Spring | furnace jobs | Exact | EXCLUDED | Auto-add (High-confidence) |
| 2026-03-25 | HVAC Spring | free hvac repair | Exact | EXCLUDED | Manual (User review) |

Log every negative keyword added, when, match type, and whether it was auto-added or manually reviewed. This provides an audit trail and helps you identify if certain patterns are truly wasteful over time.

### Tab 3: "Summary"

```
Report Date: 2026-03-27
Analysis Period: Last 30 days

Total Flagged Terms: 47
Total Waste Identified (flagged terms, no conversions): $1,245.32
High-CPA Terms: $890.65
Regex-Matched Waste Patterns: $234.23
Geographic Mismatches: $120.44

Top Waste Categories (by spend):
- Zero-conversion spend: $1,245.32 (12 terms)
- Job-seeker queries: $567.89 (8 terms)
- DIY/How-to queries: $234.23 (5 terms)
- Price-conscious queries: $120.44 (3 terms)

Week-over-Week Comparison:
- Week of 3/20: $1,567.23 flagged
- Week of 3/27: $1,245.32 flagged
- Change: -20.5% (trend improving)

Negatives Added This Week: 12
Negatives Auto-Added (High-confidence): 7
Negatives Manually Reviewed: 5
```

---

## Adding Negatives Programmatically

### Default Approach: Staging in Sheet for Review

**Do not auto-add by default.** Always stage in the Sheet for human review first. The human eye catches edge cases the script misses.

```javascript
function stageNegativeInSheet(spreadsheet, sheetName, flaggedTerm) {
  const sheet = spreadsheet.getSheetByName(sheetName);
  sheet.appendRow([
    new Date(),
    flaggedTerm.campaignName,
    flaggedTerm.adGroupName,
    flaggedTerm.searchTerm,
    flaggedTerm.matchedKeyword,
    flaggedTerm.impressions,
    flaggedTerm.clicks,
    flaggedTerm.cost,
    flaggedTerm.conversions,
    flaggedTerm.cpa,
    flaggedTerm.flagReason,
    "Review" // default action
  ]);
}
```

Human reviews the Sheet, changes "Review" to "Add Negative" or "Ignore", then a secondary script processes the Sheet and adds negatives.

### Optional: Auto-Add High-Confidence Negatives

Only enable auto-add if:
1. **AUTO_ADD_NEGATIVES is true in CONFIG**
2. **The term matches a high-confidence waste pattern** (job-seeker, DIY, free)
3. **Cost exceeds MIN_COST_THRESHOLD** (to avoid over-negating cheap terms)

```javascript
const AUTO_ADD_NEGATIVES = true; // CONFIG
const AUTO_ADD_MIN_COST = 20;
const HIGH_CONFIDENCE_PATTERNS = [
  /\b(jobs?|hiring|career|salary|pay|wage|employee|work for)\b/i,
  /\b(free|cheap)\b/i
];

function shouldAutoAddNegative(searchTerm, cost, flagReason) {
  if (!AUTO_ADD_NEGATIVES) return false;
  if (cost < AUTO_ADD_MIN_COST) return false;

  for (const pattern of HIGH_CONFIDENCE_PATTERNS) {
    if (pattern.test(searchTerm.toLowerCase())) {
      return true;
    }
  }
  return false;
}
```

### Campaign-Level Negatives

Add an exact-match negative keyword directly to a campaign:

```javascript
function addCampaignNegative(campaignId, negativeTerm) {
  const campaign = AdsApp.campaigns().withIds([campaignId]).get().next();
  if (campaign) {
    campaign.createNegativeKeyword("[" + negativeTerm + "]"); // exact match
    Logger.log(`Added negative: [${negativeTerm}] to campaign ${campaign.getName()}`);
  }
}
```

**Use exact match** (`[term]`) to ensure you only block the exact phrase, not variations.

### Shared Negative Keyword List Approach

Add terms to a shared negative keyword list, which can be applied to multiple campaigns or accounts:

```javascript
function addToNegativeList(listName, negativeTerm) {
  // Query for existing negative list by name
  const lists = AdsApp.negativeKeywordLists()
    .withCondition(`name = "${listName}"`)
    .get();

  let targetList;
  if (lists.hasNext()) {
    targetList = lists.next();
  } else {
    // Create the list if it doesn't exist
    targetList = AdsApp.negativeKeywordLists().add(listName).getResult();
  }

  // Add the term as exact match
  targetList.addExactMatch("[" + negativeTerm + "]");
  Logger.log(`Added negative: [${negativeTerm}] to list ${listName}`);
}
```

**Benefit of shared lists:** One negative list shared across multiple related campaigns or accounts means you add it once, it applies everywhere. Ideal for multi-campaign accounts or MCCs.

---

## N-gram Analysis (Optional Advanced Feature)

Break down search terms into 1-grams (words), 2-grams (two-word phrases), and 3-grams (three-word phrases). Aggregate cost and conversions per n-gram to surface high-spend, zero-conversion phrases.

**Example:** If 47 different search terms contain "near me" and collectively spend $500 with zero conversions, the 2-gram analysis reveals this pattern even if individual terms had lower spend.

### N-gram Extraction Function

```javascript
function getNgrams(searchTerm, n) {
  const words = searchTerm.toLowerCase().split(/\s+/);
  const ngrams = [];
  for (let i = 0; i <= words.length - n; i++) {
    ngrams.push(words.slice(i, i + n).join(' '));
  }
  return ngrams;
}

// Example:
// getNgrams("best hvac repair near me", 2) returns:
// ["best hvac", "hvac repair", "repair near", "near me"]
```

### Aggregation Logic

```javascript
function aggregateNgrams(searchTermData, ngramSize) {
  const ngramMap = {};

  for (const term of searchTermData) {
    const ngrams = getNgrams(term.searchTerm, ngramSize);
    for (const ngram of ngrams) {
      if (!ngramMap[ngram]) {
        ngramMap[ngram] = {
          ngram: ngram,
          cost: 0,
          conversions: 0,
          clicks: 0,
          termCount: 0
        };
      }
      ngramMap[ngram].cost += term.cost;
      ngramMap[ngram].conversions += term.conversions;
      ngramMap[ngram].clicks += term.clicks;
      ngramMap[ngram].termCount += 1;
    }
  }

  // Convert to array, sort by cost descending
  const ngramArray = Object.values(ngramMap).sort((a, b) => b.cost - a.cost);
  return ngramArray;
}
```

### Identify High-Spend, Zero-Conversion N-grams

```javascript
function flagHighWasteNgrams(ngramData, minCost = 50) {
  const flagged = ngramData.filter(ngram =>
    ngram.cost > minCost &&
    ngram.conversions === 0
  );
  return flagged; // e.g., "near me" : $523 cost, 0 conversions
}
```

### Use Case

N-gram analysis reveals:
- **2-gram "near me"**: appears in 23 different search terms, $523 total cost, 0 conversions → Consider a phrase-match negative `[*near me]` instead of blocking individual terms
- **2-gram "diy"**: $234 cost across 8 terms → Confirms DIY waste pattern
- **2-gram "jobs"**: $189 cost across 4 terms → Confirms job-seeker waste

Add an optional "N-gram Analysis" tab to the output Sheet showing these aggregated patterns.

---

## CONFIG Template

Place this in the script (or import from a CONFIG Sheet tab):

```javascript
const CONFIG = {
  // Sheet and data
  SPREADSHEET_URL: "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit",
  SHEET_NAME: "Search Term Mining",

  // Date range
  DATE_RANGE: "LAST_30_DAYS", // or "LAST_7_DAYS", "LAST_90_DAYS"

  // Waste detection thresholds
  MIN_COST_THRESHOLD: 20, // dollars, flag zero-conv terms above this cost
  MAX_CPA_MULTIPLIER: 2.0, // flag terms with CPA > (account avg CPA × multiplier)

  // Auto-add settings
  AUTO_ADD_NEGATIVES: false, // set true to auto-add high-confidence negatives
  AUTO_ADD_MIN_COST: 20, // only auto-add if spend exceeds this
  NEGATIVE_MATCH_TYPE: "EXACT", // or "PHRASE" for shared lists

  // Waste pattern detection
  WASTE_PATTERNS: [
    { pattern: /\b(jobs?|hiring|career|salary|pay|wage|employee|work for|employment)\b/i, label: "Job-seeker" },
    { pattern: /\b(diy|how to|tutorial|yourself|self|homemade|install myself)\b/i, label: "DIY/How-to" },
    { pattern: /\b(free|cheap|discount|coupon|deal|sale|budget)\b/i, label: "Price-conscious" },
    { pattern: /\b(reviews?|complaint|lawsuit|scam|reddit|negative|bad|avoid)\b/i, label: "Wrong intent" },
    { pattern: /\b(course|class|certification|school|degree|training|license)\b/i, label: "Education" }
  ],

  // Geographic filtering
  TARGET_CITIES: ["Denver", "Boulder", "Fort Collins", "Aurora"],
  BLOCK_CITIES: ["Phoenix", "Seattle", "Austin"], // explicitly block these
  CHECK_GEO: true, // enable geographic mismatch detection

  // N-gram analysis (optional)
  ENABLE_NGRAM_ANALYSIS: false,
  NGRAM_SIZES: [1, 2, 3],
  NGRAM_MIN_COST: 50,

  // Negative keyword list
  SHARED_NEGATIVE_LIST_NAME: "Search Term Mining Negatives", // or null to use campaign-level
  ADD_TO_CAMPAIGNS: ["HVAC Spring", "HVAC Summer"], // or null for all campaigns

  // Logging
  SEND_EMAIL_ON_COMPLETION: false,
  EMAIL_RECIPIENT: "your-email@example.com"
};
```

---

## Scheduling

**Recommended frequency:** Weekly

- **Weekly** is standard for most accounts. Runs every Monday morning, giving you flagged terms to review by EOD and apply negatives mid-week.
- **Daily** for high-spend accounts ($5k+ monthly ad spend). Catch waste faster.
- **Bi-weekly** for low-spend accounts or if you're manually reviewing terms and don't need constant updates.

**Example cron (Monday 9 AM local time):**
```
0 9 * * 1
```

---

## MCC Version (Multi-Account Management)

If you're managing multiple accounts under an MCC (Manager Account), adapt the script:

### 1. Process Each Account

```javascript
function processMCCAccounts() {
  const mccAccount = AdsApp.currentAccount();
  const accountIterator = AdsApp.accounts()
    .withCondition("Account.enabled = true")
    .get();

  while (accountIterator.hasNext()) {
    const account = accountIterator.next();
    AdsApp.changeActiveAccount(account.getCustomerId());

    const searchTermData = fetchSearchTerms(); // reuse function
    const flaggedTerms = detectWaste(searchTermData);
    writeToMasterSheet(account.getName(), flaggedTerms);
  }
}
```

### 2. Master Sheet Layout

Add an **Account Name** column to Tab 1 ("Flagged Terms") so you can see which account each term belongs to:

| Date | **Account** | Campaign | Ad Group | Search Term | ... | Action |
|------|-----------|----------|----------|-------------|-----|--------|
| 2026-03-27 | Heating Pro LLC | HVAC Spring | Furnace | furnace jobs | ... | Review |
| 2026-03-27 | Cool Comfort Inc | AC Install | ACs | free air conditioning | ... | Review |

### 3. Shared Negative Lists Across Accounts

Create shared negative lists at the MCC level and apply them to accounts in the same vertical:

```javascript
function addToMCCNegativeList(listName, negativeTerm) {
  // In MCC context, shared lists are account-level but can be applied across multiple accounts
  // Apply to accounts in your config
  const targetAccounts = CONFIG.MCC_ACCOUNTS; // ["account1", "account2"]

  for (const accountId of targetAccounts) {
    AdsApp.changeActiveAccount(accountId);
    addToNegativeList(listName, negativeTerm);
  }
}
```

**Benefit:** A single negative list called "Industry Waste Patterns" with job, DIY, and free terms can be applied to all HVAC accounts in your MCC, saving time and ensuring consistency.

---

## Notes & Best Practices

1. **Always stage first, auto-add sparingly.** Human reviewers catch context nuances scripts miss. A legal firm might want "law degree" queries; a landscaper might want "certified" to mean something different.

2. **Review the Matched Keyword column.** If a broad-match keyword like "hvac repair" is triggering "furnace jobs", consider tightening match types or adding phrase-match negatives to the keyword itself.

3. **CPA threshold varies by industry.** Adjust MAX_CPA_MULTIPLIER based on your account. Services with razor-thin margins might use 1.5x; high-margin services might use 2.5x or 3x.

4. **Geographic filtering is best effort.** If you can't rely on IP-based geo detection, use explicit city name blocks and track which searches come from outside your service area using conversion location data.

5. **Monitor N-gram output over time.** If "near me" goes from $500 unprofitable to $50 after you add the negative, it confirms the pattern was truly wasteful. Use this to refine patterns.

6. **Don't over-negate early.** Start with high-confidence patterns (job-seekers, DIY, free) and zero-spend terms. Expand cautiously. A $2 waste might be noise; a $200 waste is systematic.
