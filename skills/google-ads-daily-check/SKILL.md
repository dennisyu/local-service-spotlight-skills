---
name: google-ads-daily-check
description: >
  Daily exceptions-only health check across a roster of Google Ads accounts: new disapprovals and policy or verification notices, campaigns that served yesterday and not today or carry a not-serving reason, budget caps and spend far outside the daily budget, conversion actions gone silent on campaigns still spending, and final URLs that stop resolving. Reports breaks only, changes nothing, optimizes nothing. Trigger on "daily check", "run the daily Google Ads check", "any disapprovals today", "is anything broken across the accounts", "morning ads health check", or on the scheduled daily run. Google Ads only; LSA out of scope until migrated.
---

# Google Ads Daily Check

## What this skill does

Runs once a day across every account in the roster and prints one line per
exception. On a clean day it prints one line per account saying so. It exists
to catch the things that cost a full day of spend before the weekly MAA would
see them: an ad disapproved overnight, a campaign that stopped serving, a
budget cap, a conversion tag that died, a landing page that 404s.

It replaces the "daily optimization" line in a manual operator's checklist
with the part of it that is actually worth doing daily. The rest of that line
(keyword and bid tuning, negatives, recommendations) is deliberately not here:
a local service account does not produce enough data in a day to act on, and
daily reaction is how accounts get churned. Anything this check notices that is
not a break goes to the client ledger's watch list for the weekly run.

## What this skill never does

- Change the account. Read-only MCP, no scripts.
- Recommend optimizations, bid changes, negatives or pauses.
- Read Google's Recommendations tab. Auto-apply is the thing we tell clients to
  turn off; we do not automate reading it either.
- Report LSA. Pre-migration LSA is the project lead's; post-migration it is a
  campaign and shows up in the serving and budget checks like any other.
- Post to a client. Output goes to the internal thread or file the roster names.

## Inputs

- **The roster file** (`{OUTPUT_DIR}/_shared/daily-check-roster.md` or the
  vault's `clients/_shared/daily-check-roster.md`): one row per account with
  client slug, CID, project lead, ledger path, delivery target, Basecamp
  internal thread URL, and any per-account thresholds that override the
  defaults. If the roster is missing, stop and report.
  - Read the live table at the start. **If a slug appears in both the live
    table and the Pending table, do not run it**; report the conflict for that
    account and continue with the others. Pending wins.
  - **Re-read the roster after the last account.** Any row that appeared in
    the live table since the first read is reported as "added mid-run, not
    checked" in the summary line. Never finish silently past it.
- **Each client's ledger** (`compiled/ledger.md`): read only sections 2
  (definitions: which campaigns are primary, which conversion actions count),
  4 (change log: anything paused or launched on purpose in the last 14 days
  is not an exception) and 7 (quarantine). Do not read the whole ledger.
- The Google Ads MCP.

## Checks

Run every check for every account. "Yesterday" is the last full day in the
account's timezone. Queries in `references/daily-queries.md`.

Two rules below exist to catch low-volume breaks and carry **no volume
floor**. When an item feels like noise, that feeling is not a threshold; read
the rule's own precondition and nothing else.

| # | Check | Exception when | Severity |
|---|---|---|---|
| 1 | Disapprovals and policy | An ENABLED ad (in an ENABLED ad group and campaign) whose approval status is DISAPPROVED or AREA_OF_INTEREST_ONLY and was not in that state yesterday; an asset (campaign or ad group level) with primary status LIMITED or NOT_ELIGIBLE on an ENABLED campaign; a campaign whose primary status reasons include any of POLICY, BILLING, VERIFICATION, SUSPENDED, ACCOUNT, or ENDED. Campaign-level `HAS_ADS_DISAPPROVED` counts only when at least one ENABLED ad is disapproved. `LIMITED` with `BUDGET_CONSTRAINED` belongs to check 3 | RED |
| 2(a) | Serving stop, high volume | An ENABLED ad group or campaign averaging 10 or more impressions a day over the prior 7 scheduled days that had zero yesterday | RED |
| 2(b) | Serving stop, **no volume floor** | An ENABLED ad group or campaign with zero impressions for 7 consecutive scheduled days (YELLOW) or 14 (RED), where the 28 days before the run of zeros had impressions on at least 4 days AND at least 20 impressions in total. The 10-a-day figure in 2(a) does not apply here | YELLOW at 7, RED at 14 |
| 2(c) | Serving status | A campaign whose primary status is NOT_ELIGIBLE, MISCONFIGURED, ENDED, or PENDING past its start date | RED |
| 3 | Budget | Search budget-lost impression share above 25% on a ledger-primary campaign on 3 consecutive days, recomputed from today's pull (impression-share metrics settle for 24 to 48 hours; never carry yesterday's saved values into the 3-day test); spend above 2x the daily budget for 3 consecutive days; yesterday's spend below 20% of budget where the MEDIAN of the prior 6 scheduled days was at least 50% of budget | YELLOW |
| 4(a) | Tracking stop, **no volume floor** | Scope: conversion actions the ledger names as leads, plus ENABLED `primary_for_goal` actions with `include_in_conversions_metric = true`. Where ledger section 2 defines an **action group** (two or more actions fed by the same source, e.g. a call asset that reports under one action while a sibling receives merged rows), the group is one series: sum its fires before applying any rule and never grade a member alone. An in-scope action that fired at least once in the prior 90 days and has fired zero times across the last 14 days on which its campaigns spent. One fire in 90 days is enough to be in scope; there is no minimum count | RED |
| 4(b) | Tracking silence, needs 10 or more fires in 90 days | Same scope. An action with at least 10 fires in the prior 90 days, silent for N days where N is the larger of 3 and three times its median gap between fires | YELLOW at N, RED at 2N |
| 4(c) | Tracking status | An in-scope action whose status is PAUSED. REMOVED actions are ignored. Actions outside the scope (GOOGLE_HOSTED, `include_in_conversions_metric = false`, secondary) are never graded; if they go quiet they get a watch-list line with no severity | RED |
| 5 | Landing pages | Any final URL on an ENABLED ad or keyword in an ENABLED ad group and campaign that returns a status other than 200, or redirects to the site root, or redirects to a different registrable domain (eTLD+1). www to apex, http to https, and trailing-slash redirects on the same domain are not exceptions. Follow redirects and report the chain | RED for 4xx/5xx/timeout and cross-domain; YELLOW for a same-domain redirect to a non-root path |

Suppression rules, applied before anything is reported:

- **Scheduled dark days are not zero-impression days.** Before check 2, look
  for a weekly pattern of zero-impression days on the campaign (the same
  weekdays dark for 3 or more weeks) and confirm against the ad schedule
  query. Record the pattern in the ledger (section 2). Exclude those days from
  every "consecutive zero days" count and from the prior-7-day mean in 2(a)
  and the median in check 3.
- If the ledger change log shows the item was paused, ended or launched on
  purpose within 14 days, it is not an exception. Say nothing.
- If the item was reported yesterday and is unchanged, report it once as
  "still open, day N" rather than as new.
- **Under audit.** If the ledger (section 7) marks an item "under audit
  {date}, see {deliverable}", carry it in the daily file with exactly that
  wording and no severity, and leave it out of the RED count and the
  paste-ready block, until the ledger line is cleared. An audit that has
  already explained the item is not re-alarmed every morning.
- Zero-spend legacy campaigns (no spend in the prior 30 days) are ignored
  entirely for checks 2, 3 and 5.
- Check 4 never fires on an action that fired in the last 3 days on any
  campaign; low-volume actions having a quiet weekend are not a break.
- Per-account thresholds in the roster override the defaults above. Record
  the reason next to the override.
- A single day under 20% of budget on a weekend is not an exception for
  accounts whose ledger notes a weekend-quiet shape.

## Output

One block per account, written to the delivery target the roster names
(default: `{OUTPUT_DIR}/{client}/deliverables/daily/YYYY-MM-DD-daily-check.md`)
and summarised in chat. Exceptions only; a clean account is one line.

```
{Client} - {YYYY-MM-DD}
RED    Disapproval: ad 8081963xxxxx in "Roll Off Dumpster" disapproved 09/06 03:12, reason DESTINATION_NOT_WORKING. Final URL /rolloff-dumpster-rentals/ returns 404. Owner: {project lead}.
YELLOW Budget: Dallas Dumpster Rentals lost 23.4% IS to budget yesterday ($117/day, spent $116.98). Second day. Not an action; logged to watch list.
```

or

```
{Client} - {YYYY-MM-DD}: clean.
```

After all accounts, one summary line in chat: "{N} accounts checked, {R} red,
{Y} yellow, {P} paste-ready. Red items: {client: one phrase each}. Not
checked: {slugs added mid-run or in both tables, or 'none'}." Nothing else.
No prose, no recommendations, no "consider".

Every RED item names an owner from the roster. Every exception carries the
timestamp it was first seen and the query it came from, so the project lead
can verify in the UI in under a minute.

## Delivery of RED items

The deliverable is the paste-ready block in the daily file. The agent does
not post and does not stage in Basecamp's editor. (Basecamp's composer is a
Lexical editor: programmatic text does not populate the form, drafts are
discarded when the tab is backgrounded, and single-letter keystrokes sent to
an unfocused page fire global shortcuts that navigate and open tabs. A run
that tried it opened five blank tabs. Not worth it.)

When an account has one or more RED items, write under a `## For Basecamp`
heading in the daily file:

- the thread URL from the roster on its own line;
- then the block, in plain prose with no internal labels (no RED/YELLOW tags,
  no query names, no ledger section numbers), addressed to the project lead
  by name;
- the block opens with the identification line from
  `../../shared/frameworks/agent-receipt.md`:
  `Automated daily Google Ads health check by the google-ads-daily-check agent. {Client}, {date}.`
  and closes with `Sent by google-ads-daily-check / {operator}'s desk` and
  `Agent receipt: Basecamp — google-ads-daily-check [Claude] · action: reported · human review: reviewed by {operator} before posting`.
  A block missing either line is not ready to post.

The operator pastes it. If the operator later asks the agent to confirm that
a post landed, verify by API
(`GET /{account}/buckets/{bucket}/recordings/{id}/comments.json`, filter
`created_at` to today), never by reading the page.

YELLOW items are never included in the block; they live in the daily file and
the ledger watch list for the weekly run.

## Ledger write-back

For each exception, append one line to the client ledger:

- RED items: section 10 (known data faults) if it is a tracking or URL
  break, otherwise section 5 (watch list) with first-seen today and the note
  "daily check".
- YELLOW items: section 5, first-seen today.
- Out-of-scope actions that went quiet (4(c) last sentence): section 5, no
  severity.
- A RED item resolved (no longer detected) gets a dated "resolved" line.
- A scheduled-dark-day pattern found by the suppression rule: section 2.

Never edit the change log. The daily check observes; the change log records
what people did.

## Persistence

Save each day's results to `{OUTPUT_DIR}/{client}/raw/daily/YYYY-MM-DD.json`
so "new vs still open" is a diff, not a memory. Keep 30 days.

The file must carry these top-level keys, one per check, every day:
`disapproved_ads`, `limited_assets`, `campaign_status`, `serving_daily`,
`budget_daily`, `conversion_actions`, `conversions_by_action_daily`,
`final_urls`, `dark_day_pattern`, `row_counts`. A check that ran and found
nothing writes an explicit empty array; a key that is absent means the check
did not run, and tomorrow's run must say so rather than treat it as clean.
First-seen dates are only trustworthy when yesterday's file has the key.

## Adding an account

One row in the roster and a ledger that has sections 2, 4 and 7 filled. The
onboarding skill produces both. Do not add an account to the roster before its
ledger exists; the suppression rules depend on it.

## Evidence rules that apply

From `../../shared/frameworks/evidence-gates.md`: these checks report
foundation breaks, which are gate-exempt, so they may name an owner and a fix
on one day's data. Nothing else in the account is evaluated here. If the
check finds something interesting that is not a break (a CPC jump, a CTR
drop, a new search term), it is not reported; it goes to the watch list for
the weekly run to consider under the gates.
