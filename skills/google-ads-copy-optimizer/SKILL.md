---
name: google-ads-copy-optimizer
description: >
  Write Google Ads RSA headlines, descriptions and asset text for a local service
  business where every line traces to a source: the client's own website (a dated
  fact sheet), the landing page the ad points to, the ad group's real search terms,
  or the results of copy that already ran. Fact-checks live ads first and flags any
  claim the website contradicts. Trigger when the analyzer dispatches it (low Ad
  Relevance or Expected CTR, Poor/Average ad strength, a contradicted claim, or
  assets rated Low two cycles running), or on "write headlines for [ad group]",
  "improve my ad copy", "fix ad relevance", "RSA recommendations", "rewrite these
  ads", "check our ads against the site", "extension suggestions". Produces text
  and a test plan, never account changes. Use google-ads-analyzer for diagnosis and
  google-ads-change-scripts to ship the approved copy.
category: Strategy & Measurement
stage: —
status: needs-work
version: 1.6.0 (BlitzBase, 2026-10-19; not yet pushed to the public repo)
---

# Google Ads Copy Optimizer (1.6.0)

You write ad copy for one ad group at a time. You do not invent anything. Every
headline, description and asset line you propose names where it came from, and
every factual claim in it is on the client's fact sheet. Your first action is to
read the client ledger. Your second is to check the live ads against the fact
sheet, because a wrong claim in a running ad is the most urgent copy problem an
account can have. When you are done, the project lead reads one table per ad
group and approves or rejects a single test.

**Why 1.6.0 exists.** Through 1.5.0 this skill wrote from a generic template.
On a live dumpster account it shipped a headline advertising a 10-yard size the
business does not carry and a review count that went stale, both copied from
template-style examples, and those ads were still serving months later. The
operator's verdict: the copy "didn't try to pull from the website or tie to any
particular data points." This version fixes the sources, not the wording.

## Inputs

| Input | Required | Where it comes from |
|---|---|---|
| Client ledger | Yes | `compiled/ledger.md` (BlitzBase) or `{Client}_Ledger.md`. Definitions, standing rules, change log (earlier copy launches and their dates), watch list, quarantine. Read in full first. |
| Vertical file | If it exists | `verticals/<vertical>.md` in the vault. Copy patterns seen across accounts in the same industry. The client ledger wins on conflict. |
| Fact sheet | Yes; build it if missing or older than 30 days | `compiled/copy-facts.md`, format in `../../shared/frameworks/copy-facts-template.md`. Built from the client's website (and Google Business Profile for the review figure). |
| Landing page language | Yes, per ad group | The final URL of every enabled ad in the ad group, read live. Stored in the fact sheet's "Page language" section. |
| Search terms, 90 days | Yes | GAQL pack query 3 (`search_term_view`) for the ad group, 90-day window, ordered by clicks, with conversions. Use the 30D and 7D pulls only as context. |
| Live ads and their results, 90 days | Yes | GAQL pack query 4 (RSA headlines, descriptions, ad strength) plus ad-level clicks, CTR, conversions and cost for every enabled and recently paused ad in the ad group. |
| Asset ratings | Yes | `ad_group_ad_asset_view` with `performance_label`, `field_type`, `asset.text_asset.text` for the ad group's ads. Labels read PENDING on young or low-volume ads; record that, do not treat it as a verdict. |
| Quality Score components | Yes | GAQL pack query 2 for the ad group's keywords. On the MCP path components read as-is. |
| Dispatch note from the analyzer | If dispatched | Which trigger fired and the numbers behind it. |

Access is read-only. The MCP cannot change the account and neither can this
skill. Approved copy ships through `google-ads-change-scripts`, dry-run first.

If the website cannot be reached from the session (network allowlist), use the
browser. If neither works, stop: no fact sheet means no copy. Say so and add an
Open ASK to the ledger. Do not fall back to writing from memory or from the
current ads.

## Steps

### Step 1. Read the ledger and the copy history

Read the ledger in full. From the change log, list every copy change in this ad
group: date, ad ID, what changed. Those dates matter twice: anything changed in
the last 14 days is quarantined (evidence gate 3), and anything older is a test
whose result you can read in Step 4. Read the standing rules for anything about
copy, tone, claims to avoid or services out of scope.

### Step 2. Build or refresh the fact sheet

Follow `../../shared/frameworks/copy-facts-template.md`. In short:

- Read the homepage, the pricing page, each service page, the service-area
  page, and the about or reviews page. Read the Google Business Profile for the
  current rating and review count.
- Record each claim the business can back up on one line, with the URL it came
  from and the date read: sizes and services offered, services NOT offered,
  service area, pricing model and any published prices, delivery or timing
  promises, guarantees, licensing, years in business, review rating and count.
- Record what the site says the business does NOT do (no long-term contracts,
  no 10-yard, no hazardous waste). These lines are what catch bad copy.
- For every final URL the ad group's ads point to, record the page's own
  language: the H1, the main headings, the call to action wording, the service
  terms it uses, and anything on the page that contradicts the ad group's
  theme (for example a "No Long-Term Contracts" section on the page a "long
  term rental" ad group points to).

A fact sheet entry is a quote or close paraphrase of a page, never an
inference. If the site is silent on something, the fact sheet says "not stated"
and copy may not claim it.

### Step 3. Fact-check the live ads (always, before writing anything)

Compare every headline, description, sitelink and callout currently serving in
the ad group against the fact sheet. Each line gets one of:

- **Supported**: the claim is on the fact sheet.
- **Contradicted**: the fact sheet says otherwise (a size not carried, an old
  review count, a service not offered, a price that changed).
- **Unsupported**: the site does not state it.

Contradicted lines are a **correction**, reported at the top of the output and
handed to the analyzer as a foundation-level finding: a false claim in a
running ad is a trust and policy risk, so it is exempt from the sample-size and
persistence gates, like other foundation breaks. Unsupported lines go in a
table for the project lead; they are not urgent but they may not be reused.

### Step 4. Read what the data says about the copy

Before proposing anything, write down what the account already tells you:

- **Search language**: the top search terms by clicks and by conversions in
  this ad group over 90 days. Which ones convert, at what cost per lead.
  Which words recur. Which searches the current headlines never echo.
- **Earlier tests**: for each copy change in the change log, the ad's results
  before and after, or the two ads side by side if they ran together, on the
  same window. Note that ad rotation under Smart Bidding is optimized, not
  random, so two ads in one ad group are a comparison, not a controlled
  experiment. Say which won on cost per lead and conversion rate, and whether
  the volume is enough to say anything (evidence gate 1: 30 clicks or 5
  conversions per ad).
- **Asset ratings**: headlines and descriptions rated Low or Best, with the
  caveat that PENDING means unrated.
- **Quality Score components**: which of Expected CTR, Ad Relevance and
  Landing Page Experience is Below Average, and on which keywords.
- **Page match**: where the ad copy and the landing page use different words
  for the same thing, or where the page contradicts the ad group's theme.

This step is the diagnosis. If it finds nothing worth changing, the output says
so and proposes no copy. "The ads are accurate, the winning ad is clear, and
nothing has enough data to test" is a valid result.

### Step 5. Write the proposal: one test per ad group

Propose at most one change per ad group per cycle, so its result can be read:

- **Prefer adding a new RSA** next to the current winner over editing an
  existing one. Editing an RSA creates a new ad and resets its history.
- **A correction** replaces only the contradicted lines and changes nothing
  else, so the fix is not confused with a test.

Every line in the proposal carries a source in one of these forms:

| Source type | How it is cited |
|---|---|
| Search term | `search term "roll off dumpster", 123 clicks, 20 conv, 90D` |
| Fact sheet | `fact sheet: /dumpsters/ lists 15, 20, 30, 40 yard (read 2026-10-19)` |
| Landing page language | `page H1 on /rolloff-dumpster-rentals/: "Roll Off Dumpster Rentals"` |
| Earlier result | `kept from ad 811903208626, asset rated Best` |

A line with no source is deleted, not softened. A line whose claim is not on
the fact sheet is deleted. Mirror the landing page's own words where the page
and the search terms agree; where they disagree, follow the search terms in the
ad and record the mismatch as a page note for the project lead (page edits are
outside this skill).

Hard limits: headlines 30 characters, descriptions 90, sitelink text 25 and
lines 35, callouts 25. Count by script, not by eye. No two headlines may say
the same thing. At least two headlines carry the ad group's top converting
search language; at least one carries a fact only this business can claim (from
the fact sheet). Pin only when a line must show (the core service), never to
force a claim.

### Step 6. Write the test plan

For the one change proposed, state:

- what is being tested against what (ad IDs),
- the metric that decides it (cost per lead first, conversion rate second, CTR
  only as a tiebreaker), using the ledger's lead definition,
- the read date: no earlier than 14 days after launch (quarantine) and not
  before the new ad has 30 clicks or 5 conversions; if the ad group cannot
  reach that in 6 weeks, say so and judge on the monthly view,
- what happens on each outcome (keep, pause the loser, or revert).

### Step 7. Hand off and record

- Save the output (format below).
- Append to the ledger: a watch-list row for the test with its read date, an
  Open ASK if the project lead must approve, and a change-log row only when the
  change actually ships.
- Corrections and unsupported claims also go to the analyzer's next run as
  findings.
- Approved copy goes to `google-ads-change-scripts`.

## Output format

```markdown
# Ad Copy, {Client}, {Ad group}, {YYYY-MM-DD}

## Corrections (live ads contradicted by the website)
| Ad ID | Field | Live text | Fact sheet says | Source URL |
(or "None. Every live claim is supported.")

## What the data says
Five to eight lines: top search language with numbers, earlier test results,
asset ratings, QS components, page match. Each line cites its dataset.

## Proposed test
One sentence: what is added or replaced, against which ad, and why.

| # | Headline | Chars | Source |
| # | Description | Chars | Source |
(Assets only if they are the test.)

## Test plan
Decides on / read date / outcomes.

## Unsupported claims in live ads
| Ad ID | Text | Note |

## Page notes (for the project lead, outside this skill)
Where the landing page and the ads disagree.
```

Save to `deliverables/ad-copy/{Client}_AdCopy_{YYYY-MM-DD}.md` in BlitzBase
mode, or `{OUTPUT_DIR}/{Client}/{Client}_AdCopy_{YYYY-MM-DD}.md` otherwise.

## Definition of done

- [ ] Ledger read; copy history for the ad group listed with dates.
- [ ] Fact sheet exists, is under 30 days old, and every entry has a URL and a read date.
- [ ] Page language recorded for every final URL in the ad group.
- [ ] Every live headline, description and asset line graded Supported, Contradicted or Unsupported.
- [ ] Every proposed line has a source; every claim in it is on the fact sheet.
- [ ] Character counts computed, not estimated.
- [ ] At most one test per ad group, with a decides-on metric and a read date that respects the 14-day quarantine and the 30-click / 5-conversion floor.
- [ ] Ledger appended (watch list, ASK); nothing shipped to the account.

## What this skill does not do

- Change the account. Approved copy ships through `google-ads-change-scripts`.
- Edit landing pages. Mismatches go in Page notes.
- Claim anything the website does not state, however standard it is in the
  industry ("family-owned", "licensed and insured", "same-day") and however
  likely it seems.
- Run several tests in one ad group at once, or judge a test before its read date.
- Write for Meta, Display image ads or Video.

## Reference

- `references/copy-patterns.md`: angles and structure for headlines,
  descriptions and assets. Examples there use placeholders such as
  `{size list from fact sheet}`; they are shapes, never claims.
- `../../shared/frameworks/copy-facts-template.md`: fact sheet format.
- `../../shared/frameworks/evidence-gates.md`: gates 1, 2, 3 and 9 apply to
  copy tests; corrections are exempt as foundation-level.
- `../../shared/frameworks/gaql-query-pack.md`: queries 2, 3 and 4.
