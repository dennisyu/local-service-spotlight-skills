// ============================================================================
// CHANGE SCRIPT: Round 4 Negatives v2 — Summit Dumpster Rental
// Generated from MAA analysis dated 2026-04-24
// ============================================================================
//
// ANONYMIZED SAMPLE output from `google-ads-change-scripts` for the Summit
// Dumpster Rental account (an earlier cycle). Included to show the change-script
// format. Account ID and competitor names are fictional placeholders — replace
// before any real use.
//
// WHAT THIS SCRIPT DOES:
//   1. Adds new Round 4 competitor brand negatives to the shared list
//      "Summit - Competitor Brands" (phrase match). Sourced from:
//        (a) this week's search term data: "haul it away"
//        (b) pre-emptive competitive research of metro dumpster rental and junk
//            removal brands likely to sneak into the auctions as we continue
//            narrowing intent
//   2. Adds one non-competitor waste term at the campaign level:
//        - "equipment rental" (phrase) — wrong intent ($13.26 this week on
//          "equipment rental brightwater")
//
// WHAT THIS SCRIPT DOES NOT DO:
//   - It does not touch "debris dumpster rental" (held as live keyword —
//     on-intent query, one-cycle observation before negate decision).
//   - It does not touch Fairview or Lakeside. Both cities are inside the service
//     footprint and should continue to serve.
//
// BEFORE RUNNING:
//   1. Replace CUSTOMER_ID / SHARED_SET_ID with your account's real values, and
//      confirm SHARED_LIST_NAME matches the list in the account.
//   2. Run with DRY_RUN: true and review the log carefully.
//   3. Flip DRY_RUN to false and run again to apply.
//   4. Run a negative-list audit afterward to verify final state.
// ============================================================================

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
  DRY_RUN: true, // ALWAYS true first — flip to false only after reviewing the log

  CAMPAIGN_NAME: 'Brightwater Dumpster Rentals ($85 Target CPA to Max Conv 2/24)',

  SHARED_LIST_NAME: 'Summit - Competitor Brands',
  SHARED_LIST_RESOURCE_NAME: 'customers/0000000000/sharedSets/0000000000', // <-- replace

  TIME_ZONE: 'America/Chicago',
};

// ============================================================================
// TERMS DEFINITIONS  (competitor names below are fictional placeholders)
// ============================================================================

// Competitor brands — add to shared list (phrase match).
const ROUND_4_COMPETITORS = [
  // --- From 2026-04-24 search-term data (confirmed waste) ---
  { text: 'haul it away',           matchType: 'PHRASE', source: '4/24 data ($128 single click)' },

  // --- Metro dumpster rental brands (pre-emptive) ---
  { text: 'metro rubbish',          matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'delta haul',             matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'frontier bins',          matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'prairie recycling',      matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'quick bins',             matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'silver star dumpster',   matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'apex waste',             matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'tristate dumpstars',     matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'fusion bins',            matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'metro roll off',         matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'ultimate bins',          matchType: 'PHRASE', source: 'research — competitor' },
  { text: 'bargain dumpster',       matchType: 'PHRASE', source: 'research — national aggregator' },
  { text: 'hometown bins',          matchType: 'PHRASE', source: 'research — national aggregator' },

  // --- Junk removal brands (pre-emptive — we already saw "haul it away" appear) ---
  { text: 'campus haulers',         matchType: 'PHRASE', source: 'research — junk removal' },
  { text: 'bin it dump it',         matchType: 'PHRASE', source: 'research — junk removal' },
  { text: 'standup crew',           matchType: 'PHRASE', source: 'research — junk removal' },
  { text: 'dump the junk',          matchType: 'PHRASE', source: 'research — junk removal' },
  { text: 'zero junk',              matchType: 'PHRASE', source: 'research — junk removal' },
  { text: 'brightwater junk guys',  matchType: 'PHRASE', source: 'research — junk removal' },
];

// Non-brand waste terms — add at CAMPAIGN level, not shared list.
// NOTE: "debris dumpster rental" was in v1 but was pulled per client direction
// on 2026-04-24. On-intent query, one-cycle observation before any negate.
const ROUND_4_CAMPAIGN_LEVEL = [
  { text: 'equipment rental',       matchType: 'PHRASE', source: '4/24 data: "equipment rental brightwater" wrong intent' },
];

// ============================================================================
// UTILITIES
// ============================================================================

function logDivider() {
  Logger.log('------------------------------------------------------------');
}

function logHeader(text) {
  Logger.log('');
  Logger.log('>>> ' + text.toUpperCase());
  logDivider();
}

// Format keyword text for addNegativeKeyword(): "text" = phrase, [text] = exact, text = broad
function formatForAdd(text, matchType) {
  if (matchType === 'EXACT')  return '[' + text + ']';
  if (matchType === 'PHRASE') return '"' + text + '"';
  return text;
}

// ============================================================================
// STEP 1: FIND THE SHARED LIST
// ============================================================================

function getSharedList() {
  const iterator = AdsApp.negativeKeywordLists()
    .withCondition('Name = "' + CONFIG.SHARED_LIST_NAME + '"')
    .get();

  if (!iterator.hasNext()) {
    throw new Error('Shared list "' + CONFIG.SHARED_LIST_NAME + '" not found. Verify the name matches exactly.');
  }

  const list = iterator.next();
  Logger.log('Located: "' + list.getName() + '"');
  return list;
}

// ============================================================================
// STEP 2: READ EXISTING SHARED-LIST KEYWORDS (deduplication check)
// ============================================================================

function getExistingListKeywords() {
  const rows = AdsApp.search(
    'SELECT shared_criterion.keyword.text ' +
    'FROM shared_criterion ' +
    'WHERE shared_criterion.shared_set = "' + CONFIG.SHARED_LIST_RESOURCE_NAME + '" ' +
    'ORDER BY shared_criterion.keyword.text'
  );

  const existing = [];
  while (rows.hasNext()) {
    existing.push(rows.next().sharedCriterion.keyword.text.toLowerCase());
  }
  Logger.log('Keywords already in shared list: ' + existing.length);
  return existing;
}

// ============================================================================
// STEP 3: READ EXISTING CAMPAIGN-LEVEL NEGATIVES (dedup for campaign adds)
// ============================================================================

function getExistingCampaignNegatives() {
  const rows = AdsApp.search(
    'SELECT campaign_criterion.keyword.text, campaign_criterion.keyword.match_type ' +
    'FROM campaign_criterion ' +
    'WHERE campaign_criterion.negative = true ' +
    'AND campaign_criterion.type = KEYWORD ' +
    'AND campaign.name = "' + CONFIG.CAMPAIGN_NAME + '"'
  );

  const existing = [];
  while (rows.hasNext()) {
    const row = rows.next();
    existing.push({
      text: (row.campaignCriterion.keyword.text || '').toLowerCase(),
      matchType: row.campaignCriterion.keyword.matchType,
    });
  }
  Logger.log('Keywords already at campaign level: ' + existing.length);
  return existing;
}

// ============================================================================
// STEP 4: ADD TERMS TO SHARED LIST
// ============================================================================

function addToSharedList(list, terms, existingKeywords) {
  let added = 0;
  let skipped = 0;

  for (const term of terms) {
    const lower = term.text.toLowerCase();

    if (existingKeywords.indexOf(lower) !== -1) {
      Logger.log('  [SKIP — already in list] ' + formatForAdd(term.text, term.matchType) + '  (source: ' + term.source + ')');
      skipped++;
      continue;
    }

    const formatted = formatForAdd(term.text, term.matchType);

    if (CONFIG.DRY_RUN) {
      Logger.log('  [DRY RUN — would add] ' + formatted + '  (source: ' + term.source + ')');
    } else {
      list.addNegativeKeyword(formatted);
      Logger.log('  [ADDED] ' + formatted + '  (source: ' + term.source + ')');
    }
    added++;
  }

  Logger.log('Shared list: ' + added + ' to add' + (CONFIG.DRY_RUN ? ' (dry run)' : '') + (skipped > 0 ? ', ' + skipped + ' already present (skipped)' : ''));
  return { added: added, skipped: skipped };
}

// ============================================================================
// STEP 5: ADD TERMS AT CAMPAIGN LEVEL
// ============================================================================

function addToCampaign(terms, existingCampaignNegs) {
  const campaigns = AdsApp.campaigns()
    .withCondition('Name = "' + CONFIG.CAMPAIGN_NAME + '"')
    .get();

  if (!campaigns.hasNext()) {
    throw new Error('Campaign "' + CONFIG.CAMPAIGN_NAME + '" not found.');
  }
  const campaign = campaigns.next();

  let added = 0;
  let skipped = 0;

  for (const term of terms) {
    const lower = term.text.toLowerCase();
    const alreadyExists = existingCampaignNegs.some(function(e) {
      return e.text === lower && e.matchType === term.matchType;
    });

    if (alreadyExists) {
      Logger.log('  [SKIP — already at campaign level] ' + formatForAdd(term.text, term.matchType) + '  (source: ' + term.source + ')');
      skipped++;
      continue;
    }

    const formatted = formatForAdd(term.text, term.matchType);

    if (CONFIG.DRY_RUN) {
      Logger.log('  [DRY RUN — would add to campaign] ' + formatted + '  (source: ' + term.source + ')');
    } else {
      campaign.createNegativeKeyword(formatted);
      Logger.log('  [ADDED to campaign] ' + formatted + '  (source: ' + term.source + ')');
    }
    added++;
  }

  Logger.log('Campaign level: ' + added + ' to add' + (CONFIG.DRY_RUN ? ' (dry run)' : '') + (skipped > 0 ? ', ' + skipped + ' already present (skipped)' : ''));
  return { added: added, skipped: skipped };
}

// ============================================================================
// ENTRY POINT
// ============================================================================

function main() {
  try {
    Logger.log('========================================================');
    Logger.log('ROUND 4 NEGATIVES — Summit Dumpster Rental');
    Logger.log('Run date: ' + Utilities.formatDate(new Date(), CONFIG.TIME_ZONE, 'yyyy-MM-dd HH:mm'));
    Logger.log('Mode: ' + (CONFIG.DRY_RUN ? 'DRY RUN (no changes made)' : 'LIVE — changes ARE being made'));
    Logger.log('Shared list: "' + CONFIG.SHARED_LIST_NAME + '"');
    Logger.log('Campaign:    "' + CONFIG.CAMPAIGN_NAME + '"');
    logDivider();

    logHeader('Step 1: Locate shared list');
    const list = getSharedList();

    logHeader('Step 2: Read existing shared-list keywords');
    const existingShared = getExistingListKeywords();

    logHeader('Step 3: Read existing campaign-level negatives');
    const existingCampaign = getExistingCampaignNegatives();

    logHeader('Step 4: Add Round 4 competitor brands to shared list');
    const sharedResult = addToSharedList(list, ROUND_4_COMPETITORS, existingShared);

    logHeader('Step 5: Add non-competitor waste terms at campaign level');
    const campaignResult = addToCampaign(ROUND_4_CAMPAIGN_LEVEL, existingCampaign);

    logDivider();
    Logger.log('=== SUMMARY ===');

    if (CONFIG.DRY_RUN) {
      Logger.log('DRY RUN — no changes made.');
      Logger.log('');
      Logger.log('Would add to "' + CONFIG.SHARED_LIST_NAME + '" (' + sharedResult.added + '):');
      ROUND_4_COMPETITORS.forEach(function(t) {
        if (existingShared.indexOf(t.text.toLowerCase()) === -1) {
          Logger.log('  + ' + formatForAdd(t.text, t.matchType));
        }
      });
      Logger.log('');
      Logger.log('Would add at campaign level (' + campaignResult.added + '):');
      ROUND_4_CAMPAIGN_LEVEL.forEach(function(t) {
        const exists = existingCampaign.some(function(e) {
          return e.text === t.text.toLowerCase() && e.matchType === t.matchType;
        });
        if (!exists) Logger.log('  + ' + formatForAdd(t.text, t.matchType));
      });
      Logger.log('');
      Logger.log('If this looks correct, set DRY_RUN to false and run again.');
    } else {
      Logger.log('Changes applied successfully.');
      Logger.log('  Added to shared list:     ' + sharedResult.added);
      Logger.log('  Added at campaign level:  ' + campaignResult.added);
      Logger.log('  Skipped (already exist):  ' + (sharedResult.skipped + campaignResult.skipped));
    }

  } catch (e) {
    Logger.log('FATAL ERROR: ' + e.message);
  }
}
