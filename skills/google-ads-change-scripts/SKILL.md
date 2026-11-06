---
name: google-ads-change-scripts
description: >
  Generate one-time Google Ads Scripts that implement specific account changes from MAA
  recommendations, adding negatives, pausing ads/keywords, updating RSA copy, adjusting
  bids, or restructuring ad groups. Every script defaults to dry-run mode. Trigger on
  "implement these changes", "script to add these negatives", "pause these keywords",
  "bulk update my ads", "apply the MAA actions", or any request to turn Google Ads
  recommendations into a runnable script. This is for one-time change scripts, use
  google-ads-script for data pipelines and ongoing automation.
---

# Google Ads Change Scripts

## What This Skill Does

This skill translates MAA action items and ad copy recommendations into one-time
Google Ads Scripts that an account manager can review, paste into the Google Ads
Scripts IDE, preview, and execute. Every script defaults to dry-run mode so the
AM sees exactly what will change before anything happens.

The key principle: **the AM approves every change.** These scripts are tools for
implementing decisions that have already been made by a human, they don't make
decisions themselves. Dry-run output should be clear enough that a non-technical
AM can verify the changes are correct.

## Supported Change Types

### 1. Add Negative Keywords

The most common MAA action. Takes a list of negative keywords and adds them at
the campaign or ad group level.

**Input needed:**
- List of negative keywords to add
- Match type for each (exact, phrase, or broad, default to exact for precision)
- Target level: campaign negative keyword list, specific campaign, or ad group
- Campaign/ad group names if targeting specific entities

**Script behavior:**
- Check if each negative already exists before adding (avoid duplicates)
- Log every addition with the campaign/ad group context
- In dry-run mode: list all keywords that would be added and where
- Support both shared negative keyword lists and campaign-level negatives

### 2. Pause Underperforming Ads

Takes specific ad identifiers or criteria and pauses them.

**Input needed:**
- Either specific ad group + ad combinations to pause, OR
- Criteria-based: "pause all ads in [campaign] with CTR below X% and 1000+
  impressions"
- Reason for pausing (logged in the script output for the AM's records)

**Script behavior:**
- Log each ad being paused with its current metrics for the record
- Never delete, always pause. Deletion is irreversible.
- In dry-run mode: show each ad that would be paused with its performance stats

### 3. Update RSA Headlines/Descriptions

Takes specific headline/description changes and applies them via the
`AdsApp.mutate()` API.

**Input needed:**
- Campaign and ad group name
- Which headlines/descriptions to remove (by text match)
- Which headlines/descriptions to add (typically from google-ads-copy-optimizer
  output, which provides ready-to-paste text with character counts)
- Any pin changes

**Script behavior:**
- RSA modifications use the mutate API, this is the only reliable way to
  edit RSA assets in Google Ads Scripts
- Log the before and after state of each ad
- In dry-run mode: show what the RSA would look like after the change

**Important constraint:** Google Ads Scripts cannot directly edit individual RSA
assets in-place. The standard approach is to create a new ad with the desired
assets and pause the old one, OR use `AdsApp.mutate()` with the ad resource name
to update the responsive search ad's headlines and descriptions. Read
`references/rsa-mutation-patterns.md` for the tested approach.

### 4. Pause/Enable Keywords

Takes specific keywords to pause or re-enable.

**Input needed:**
- List of keywords with their campaign and ad group
- Whether to pause or enable
- Optional: reason for the change

**Script behavior:**
- Match keywords by text and match type within the specified ad group
- Log each change with the keyword's recent performance
- In dry-run mode: list all keywords that would be affected with their stats

### 5. Adjust Bids (Manual CPC only)

For accounts on Manual CPC, adjust keyword-level bids.

**Input needed:**
- Keywords to adjust with target bid amounts, OR
- Adjustment rules: "increase bids 20% on keywords with QS 7+ and IS lost to
  rank > 30%"

**Script behavior:**
- Only works for Manual CPC or enhanced CPC campaigns. If the campaign uses
  automated bidding (Max Conversions, Target CPA, etc.), the script should
  refuse and explain why: automated bid strategies set their own bids, and
  manual overrides conflict with the algorithm
- Log current bid vs. new bid for each keyword
- Cap bid changes at a configurable maximum (e.g., no single bid increase > 50%)
  to prevent runaway changes
- In dry-run mode: show proposed bid vs. current bid for every keyword

### 6. Restructure Ad Groups

Move keywords between ad groups or create new ad groups with specific keywords.
This is for implementing "tighter ad group theming" recommendations.

**Input needed:**
- Source ad group(s) and which keywords to move
- Destination ad group name (will be created if it doesn't exist)
- Whether to copy the existing ads to the new ad group or create fresh ones

**Script behavior:**
- Create destination ad group if needed
- Add keywords to new ad group
- Pause keywords in source ad group (don't delete, keeps history)
- Copy ads if requested
- In dry-run mode: show the proposed restructure as a before/after table

## Script Structure

Every change script follows this structure. This is adapted from the
google-ads-script skill's conventions:

```javascript
// ============================================================================
// CHANGE SCRIPT: [Description of what this script does]
// Generated from MAA analysis dated [date]
// ============================================================================

// ============================================================================
// CONFIGURATION
// ============================================================================
const CONFIG = {
  // What this script changes
  DRY_RUN: true,  // ALWAYS true by default, preview before executing

  // Error handling
  SEND_EMAIL_ON_ERROR: true,
  ERROR_EMAIL: '',  // AM's email
  TIME_ZONE: 'America/Denver',

  // Change-specific settings below
};

// ============================================================================
// CHANGE DEFINITIONS
// ============================================================================
// The specific changes to make, this is what the AM reviews before running.
// Structured as arrays/objects so the AM can add, remove, or modify entries.

// ============================================================================
// EXECUTION LOGIC
// ============================================================================

// ============================================================================
// ENTRY POINT
// ============================================================================
function main() {
  var changes = [];
  var errors = [];

  try {
    // Execute changes
    // ...

    // Summary
    Logger.log('=== CHANGE SUMMARY ===');
    if (CONFIG.DRY_RUN) {
      Logger.log('DRY RUN, no changes were made.');
      Logger.log('Review the log above. If everything looks correct,');
      Logger.log('set DRY_RUN to false and run again.');
    }
    Logger.log('Changes: ' + changes.length);
    Logger.log('Errors: ' + errors.length);

  } catch (e) {
    Logger.log('FATAL ERROR: ' + e.message);
    if (CONFIG.SEND_EMAIL_ON_ERROR && CONFIG.ERROR_EMAIL) {
      MailApp.sendEmail(CONFIG.ERROR_EMAIL, 'Change Script Error', e.message);
    }
  }
}
```

### The Change Definitions Section

This is the most important section for the AM. It should be a clear, readable
data structure that maps directly to what will happen. The AM should be able to
scan this section and say "yes, those are the right changes" without reading the
execution logic.

**Example for negative keywords:**
```javascript
const NEGATIVES_TO_ADD = [
  {keyword: 'dumpster rental jobs', matchType: 'EXACT', level: 'CAMPAIGN', campaign: 'SF-Search-Dumpster'},
  {keyword: 'how to build a dumpster', matchType: 'PHRASE', level: 'CAMPAIGN', campaign: 'SF-Search-Dumpster'},
  {keyword: 'free dumpster', matchType: 'EXACT', level: 'CAMPAIGN', campaign: 'SF-Search-Dumpster'},
];
```

**Example for pausing ads:**
```javascript
const ADS_TO_PAUSE = [
  {campaign: 'SF-Search-Dumpster', adGroup: 'Dumpster Rental', reason: 'CTR 1.2% vs 3.8% on other ad, dragging group average'},
  {campaign: 'SF-Search-Dumpster', adGroup: 'Roll Off Container', reason: 'Ad strength Poor, needs rewrite before re-enabling'},
];
```

## DRY_RUN Is Non-Negotiable

Every change script starts with `DRY_RUN: true`. The dry-run output should be
detailed enough that the AM can verify every change:

- For negative keywords: list each keyword, where it will be added, and whether
  it already exists (skip if duplicate)
- For pausing ads/keywords: show the entity name, its recent performance, and
  the reason for pausing
- For RSA changes: show the before state and proposed after state
- For bid changes: show current bid vs. proposed bid with the % change

The AM runs the script once in preview mode, reads the dry-run log, then flips
`DRY_RUN: false` and runs again to execute. This is the workflow. No exceptions.

## Connecting to the MAA Pipeline

Change scripts are the implementation layer of the MAA pipeline:

1. **google-ads-analyzer** diagnoses the account and produces action items
2. **google-ads-copy-optimizer** writes the specific ad copy (if needed)
3. **This skill** translates those action items and copy into executable scripts

When building a change script from MAA output, reference the specific MAA action
item that drives each change. This creates an audit trail:

```javascript
// From MAA dated 2026-04-03, Action Item #1:
// "Add these 12 negative keywords, $640/month in waste on job-seeker queries"
const NEGATIVES_TO_ADD = [ ... ];
```

## After the Run: Write the Ledger Row (1.5.0)

`change_event` on the Google Ads API is unreliable on the MCP path (validation
errors, empty results for recent changes, page caps). The client ledger's
change log is the authoritative record of what changed and when, and it only
fills if someone writes to it. This skill is the main place changes originate,
so it owns the write.

Every script this skill produces ends with a **Ledger row** block in its
header comment, pre-filled with everything known at authoring time:

```javascript
// LEDGER ROW (append to compiled/ledger.md section 4 when this runs live):
// | {YYYY-MM-DD} | Negatives Round 18: 19 campaign-level phrase negatives on Dallas Dumpster Rentals ({term list} tail) | {who} | scripts/{filename}.js, MAA {date} Action 2 |
// QUARANTINE (section 7): exits {date + 14 days}. Spend redistribution on the affected terms is expected, not a result.
// WATCH (section 5): none | {item to watch and its promote condition}
```

When the operator confirms a live run ("ran it", "script is live", "done"),
the response is the ledger write, not an acknowledgement:

1. Fill the date and who, append the row to section 4 of the ledger.
2. Append the quarantine entry to section 7 with its exit date.
3. If the script pauses or enables anything, update section 2 (definitions) or
   section 5 (watch list) as the header block says.
4. Verify the change by reading the account back (the MCP is fine for this),
   and note "API-verified" or "unverified" in the row. A script log is never
   evidence of account state; the IDE Preview button discards changes while
   reporting success, and `setFinalUrl()` fails silently on RSAs.
5. Reply with the rows you wrote, nothing else.

**UI edits.** Changes made by hand in the Google Ads UI bypass this skill.
The trigger "log a change: {what}, {campaign}, {date}" appends the same row
shape to the ledger without a script. The analyzer should prompt for this
whenever a pull shows a state the ledger does not explain.

## What This Skill Does NOT Do

- **Diagnose problems.** Use google-ads-analyzer for that.
- **Write ad copy.** Use google-ads-copy-optimizer for headlines and descriptions.
  This skill takes that copy and puts it into a script.
- **Build data pipelines or reporting.** Use google-ads-script for BigQuery sync,
  QS tracking, search term mining, and other ongoing automation.
- **Make decisions.** The AM decides what changes to make. This skill makes those
  changes easy to execute safely.
- **Run on a schedule.** These are one-time scripts. If you need ongoing
  automation (auto-pause below a threshold, auto-add negatives from a watch
  list), that's a different tool for a future version.
