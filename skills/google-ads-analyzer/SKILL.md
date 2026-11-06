---
name: google-ads-analyzer
description: Turn a local service business's Google Ads data into a short weekly report (Metrics, Analysis, Action) that a project lead can act on, drafted under evidence rules and checked by a second agent before anyone sees it; trigger on "do the MAA for [client]", "weekly Google Ads MAA", "analyze my Google Ads", "Google Ads audit", an uploaded Google Ads export, or a scheduled weekly run.
category: Strategy & Measurement
stage: —
definitive_article: https://localservicespotlight.com/google-ads-maa-agent/ (published 2026-07-10; revised in place for the 1.5.0 process on 2026-09-15)
status: needs-work
---

# Google Ads Analyzer (weekly MAA)

You run Google Ads for a local service business, or you manage the person who does. Each week you need to know three things. What did the ads do? Why? What should change next? This skill reads the account data and writes that weekly report. The report is called an MAA. That stands for Metrics, Analysis, Action. A second agent checks every number and every suggestion before a person sees it. Your first action is to check that the client has a ledger file. The ledger is the client's memory. It says what counts as a lead, what changed and when, and what we already watch. No ledger? Run the onboarding skill first. When this skill is done, the project lead reads a short summary and decides what to post.

Terms used below, explained once: **MAA** is the report format, Metrics then
Analysis then Action. **PMax** is Performance Max, a Google campaign type
that places ads across Google's networks automatically. **Quality Score** is
Google's 1 to 10 rating of a keyword's ad and page fit. **Keywords** are what
we bid on; **search terms** are what people actually typed. **Ledger** is the
one file per client that holds definitions, rules, changes, watch items and
known data faults (`../../shared/frameworks/ledger-template.md`). **Hardener**
is the second agent, `google-ads-reviewer`, that checks the draft.

Reading grade of the opening above: 3.7 (Flesch-Kincaid, measured 2026-09-15
on the paragraph as written; 130 words, 15 sentences).

## Inputs

**Boundary, stated first: this skill never changes a Google Ads account.** It
reads through a read-only connector and writes files. Negatives, pauses, bids,
budgets and copy changes leave this skill as recommendations and become
dry-run scripts in `google-ads-change-scripts`, run only after a person
approves them.

Everything the run needs before it starts. If any required item is missing,
the agent **stops and hands off** to the operator with the missing item named.
It does not guess, does not proceed on partial data, and does not splice
sources.

**Access (separate from files):**

| Access | Required | Notes |
|---|---|---|
| Google Ads read access to the client account | Yes | Via the read-only Google Ads MCP. The account is reached through a manager account (MCC) that lists the client CID, or as a single account the credential can see. The MCP needs a developer token with Basic access or higher and an OAuth grant on the `https://www.googleapis.com/auth/adwords` scope; setup in `../../shared/frameworks/mcp-setup-guide.md`. |
| Fallback: the weekly data email | Only if the MCP is down | Gmail label `maa-data-automation`, subject `[MAA Data] {Client} {date}`; contract in `../../shared/frameworks/data-pipeline-contract.md`. Requires the corrector script on the keyword report. |
| Client folder, read and write | Yes | `{OUTPUT_DIR}/{Client}/` per `CONFIGURATION.md`, or the vault path named in the deployment's binding file. |
| Basecamp, email, any client channel | Never | This skill posts nothing anywhere. |

**Files (must exist before the run):**

| File | Produced by | Checked output it must contain |
|---|---|---|
| `compiled/ledger.md` (or `{Client}_Ledger.md` in simple mode) | `google-ads-onboarding` | All ten sections; section 2 names the lead definition, target and windows; section 7 has a quarantine exit date. |
| Client metric spec (`compiled/maa-metric-spec.md`) | onboarding, or the first run | Section order and metric names for this client. |
| The most recent dated MAA in `deliverables/` | the prior weekly run | Used for deltas and voice. First run: none, and the report says so. |
| The deployment's overlay and procedure files, if any | the agency | e.g. `maa-skills-binding.md`, `maa-generation.md`. |

**Data pulled by the run (not pre-supplied):** the full pack in
`../../shared/frameworks/gaql-query-pack.md`, both windows, 7 days and 30 days
ending yesterday: campaign summary, campaign budgets, keyword report with
Quality Score components (all statuses), search terms, ad report with
strength, conversions by action, network and device splits, user location,
negatives at three levels, call data. On the email path the ten datasets in
the export body.

**Prerequisite task:** `google-ads-onboarding`, once per client. Its checked
output is the ledger above plus `compiled/trend.csv` with 13 weekly rows.

**Missing-access behavior, stated once:** no ledger, stop and report "no
ledger; run google-ads-onboarding". MCP unavailable and no email export, stop
and report; never splice. Any query that returns exactly its row cap is
flagged and supports no claim that something is absent. Any account state
the ledger's change log does not explain is recorded as an "unlogged change"
question for the operator, not analyzed.

## Steps

The run is five stages; the detailed procedure for each is in the Full
procedure section below.

1. **Read** (Stage 0): the ledger in full, then the knowledge base, metric
   spec, overlay files and the last MAA. No data yet.
2. **Pull** (Stage 0b): the whole pack, both windows, saved verbatim to
   `raw/`, with row counts. No prose yet.
3. **Draft** (Stage 1): under the ten evidence gates in
   `../../shared/frameworks/evidence-gates.md`, in the client's section order,
   with a claim register in the Generation notes block. Weekly runs answer
   context questions from the ledger or add them to its Open ASKs; they do not
   ask in chat.
4. **Harden** (Stage 2): dispatch `google-ads-reviewer` in a fresh context
   with only the frozen draft, the raw pack, the ledger and the spec. Apply
   its verdicts once. One round.
5. **Reconcile and wrap** (Stages 3 and 4): numbers tie to the pack; every
   Action has watch-list age or is a foundation break; append the ledger and
   the trend row; read back the saved files; stop. The client view is not
   rendered on a scheduled run.

## Definition of done (QA checklist)

Every box must be checked before the run reports itself complete. A run that
cannot check a box says which one and why.

- [ ] Ledger, spec and last MAA were read before the first query (Generation
      notes lists them by path).
- [ ] Raw pack saved to `raw/google-ads/YYYY-MM-DD_mcp-pull.json` (or the
      email export to `raw/google-ads/YYYY-MM-DD_email-data.txt` plus the
      corrected copy), and the row count of every query is recorded, with any
      query at its cap flagged. Any summary or derived block inside the pack
      was computed from its rows by script, never typed by hand (a hand-typed
      weekly call summary that did not sum to its rows produced four wrong
      sentences on 2026-09-11).
- [ ] Generation notes record the run's start and end timestamps (account
      timezone). Tokens and cost are recorded when the runtime exposes them
      and written as UNKNOWN otherwise.
- [ ] Every campaign figure in Metrics ties to the pack to the cent; CTR, CPC
      and CPA were recomputed, not copied.
- [ ] Every number in Analysis carries its comparison (delta or baseline) or
      says it is new.
- [ ] Every causal or trend sentence in Analysis has a dataset and row
      reference in the claim register.
- [ ] Every Action names an owner inline, states what and why, and either has
      two prior cycles on the ledger watch list or is a foundation break
      (tracking, geo, bidding without signal, disapproval, not serving, budget
      capped on multiple days).
- [ ] Nothing in the ledger quarantine is judged; nothing on the ledger's
      never-surface list appears; no internal vocabulary or API enum in the
      report body.
- [ ] The hardener ran in a fresh context and its output is pasted into
      Generation notes verbatim: the verdict ledger as a table (one row per
      finding and Action), the format punch list counts (BLOCK / WARN / STYLE),
      and the grade before and after the round; each row carries Applied /
      Reworded / Unaddressed; nothing contested is hidden. Prose summaries of
      the verdicts do not satisfy this box (first live cycle, 2026-09-11: one of
      four reports printed the table, none printed a grade).
- [ ] Ledger appended (weekly log row, change-log rows, watch-list updates,
      new ASKs, quarantine entries, data faults) and `trend.csv` row appended;
      no past line rewritten.
- [ ] **Read-back:** the agent re-opened `deliverables/YYYY-MM-DD-google-ads-maa.md`,
      the ledger and `trend.csv` after writing and confirmed each exists, the
      MAA has all three sections in the spec's order, and the ledger's new
      lines are present. The read-back result is the last line of Generation
      notes.
- [ ] The chat summary is at most eight lines: leads and CPL vs last cycle,
      Actions proposed, items the hardener demoted or dropped, open ASKs, data
      faults.

**Receiving owner:** the client's project lead, who reads the summary and the
draft. **Receiving tasks:** `google-ads-client-view` renders the client-facing
report after the lead approves; `google-ads-copy-optimizer` takes any RSA
work the Actions dispatch; `google-ads-change-scripts` turns approved Actions
into dry-run scripts and writes the ledger change-log row when they run.

## Example(s)

- `docs/meta/GAA-2026-09-11-C1A.md`: the meta article for one real scheduled
  run under 1.5.0 (2026-09-11; client anonymized, numbers unchanged). It
  shows the five stages on a one-lead week: the gates holding a lead collapse
  off the Action list at 34 clicks, the hardener grading the first draft F
  and correcting fifteen numbers, a same-day investigation that explained the
  week from data already in the pack, and the ledger rows appended. Time and
  cost are recorded as UNKNOWN; two human interventions are recorded.
- `../../shared/examples/SummitDumpster_MAA_2026-06-26.md` is a real weekly
  report on a live account (client, people, locations, IDs and competitor
  names changed; numbers and reasoning preserved), produced under version
  1.1.0. It proves the report shape, the "we" voice and the balanced-metrics
  discipline; it predates the ledger, the gates and the hardener.
- Published run articles under the earlier process, linked from the
  definitive article: the 2026-07-10 American AF Dumpsters and Target
  Painting runs.

## Definitive article & links

- Definitive article: https://localservicespotlight.com/google-ads-maa-agent/
  (The Google Ads MAA Agent, published 2026-07-10, revised in place for the
  five-stage process on 2026-09-15 and read back live). The source of the
  live body is `docs/definitive-article/google-ads-analyzer.md`. Parent hub:
  https://blitzmetrics.com/maa/ . Sibling that stubs the Google Ads row this
  task feeds: https://blitzmetrics.com/inside-the-weekly-maa-report/ .
- In this repo: `README.md` (what the suite is), `WALKTHROUGH.md` (end-to-end
  weekly loop), `ONBOARDING-AGENCY.md` (setup and the standard scheduled
  prompt), `CHANGELOG.md`.
- Frameworks this skill depends on, all in `../../shared/frameworks/`:
  `evidence-gates.md`, `ledger-template.md`, `gaql-query-pack.md`,
  `data-pipeline-contract.md`, `maa-grading-rubric.md`, `agent-receipt.md`,
  `methodology.md`.
- The MAA method (Metrics, Analysis, Action) is Dennis Yu's framework; the
  maintained explainer is https://blitzmetrics.com/maa/ (fetched and read
  2026-09-15). Meta-article guidelines: https://blitzmetrics.com/meta-article-prompt/ .
  Task Library home: https://local-service-spotlight.github.io/task-library/ .

## Routing lane and tools

- Lane: **`judgment`**. Drafting and hardening are judgment work on a top
  model; the pull and the reconciliation are mechanical and may be delegated
  down inside the run.
- Tools the lane needs: the Google Ads MCP (read-only; `search` with GAQL) or
  the email export; file read and write on the client folder; a subagent
  facility for the hardener's fresh context. No browser is required for the
  weekly run; the Call details UI report is optional and only when the
  operator asks for full caller numbers.
- When a tool is absent: MCP absent and no export, stop and report; subagent
  facility absent, run the hardener as a second pass in the same session and
  say so in Generation notes (the independence rule is weakened and the
  summary must state it).

## Sources and labels for numbers and claims

Every threshold below is labeled as either Google-published or a house
heuristic. House heuristics are ours; they are not Google guidance.

| Figure or claim | Label | Source or setter, date |
|---|---|---|
| Gate 1: no Action under 30 clicks or 5 conversions | House heuristic | Set by Daniel Goodrich for the 1.5.0 gates, 2026-09-06, from a transcript audit of live runs |
| Gate 2: two prior cycles on the watch list; gate 3: 14-day quarantine | House heuristic | Same |
| "Top 5 to 10 items account for about 60% of spend" | House heuristic, rule of thumb | BlitzMetrics MAA practice; not a Google figure |
| "A keyword needs 2 to 3 weeks of consistent underperformance" | House heuristic | Same |
| "Smart bidding wants roughly 15 to 30 conversions per campaign per 30 days" and "15 conversions in 30 days" | Google-published historically, now a house heuristic | Google Ads Help once listed a 30-day conversion minimum for Target CPA; Google has since removed hard minimums. Treated as our floor, not Google's requirement. Verify against Google Ads Help "About Smart Bidding" before quoting to a client. |
| "Restructuring doesn't trigger learning periods", "AI Max uses LLM-based intent matching", "consolidation over granularity", "brand and geo controls are the modern segmentation levers" | Unverified, from Google account representative conversations in 2026 | Not confirmed against a published Google page. Label as "per Google rep, unverified" in any client copy, or leave out. |
| "12+ headlines, 4+ descriptions in RSAs" | House heuristic | Google allows up to 15 headlines and 4 descriptions per RSA (Google Ads Help "About responsive search ads"); the 12 is our fill target. |
| "$200 CPA might be excellent for roofing and terrible for drain cleaning" | Illustration only | Not a benchmark. |
| Quality Score components read as-is on the MCP path; column swap on the email path | Verified | `../../shared/frameworks/data-pipeline-contract.md`, decision dated 2026-06-05 |
| Bid strategy enum translations | Verified | Google Ads API enum names to UI labels, `../../shared/frameworks/gaql-query-pack.md` |

Any new number added to this skill must be added to this table with a label.


# Full procedure

## What This Skill Does

This skill analyzes Google Ads campaign data (Search, PMax, Video, Display) for
local service businesses and delivers a concise MAA (Metrics → Analysis →
Action). The output is a tight, actionable document, not a comprehensive audit
report. Think 2-3 action steps tied directly to what the data shows, starting
with the highest-impact foundational fixes before moving to optimization.

**Campaign type depth:** Search and PMax campaigns are the primary focus and get
full diagnostic treatment. Video and Display campaigns get a lighter touch,
condensed metrics and a brief note in Analysis, since they typically serve
awareness goals rather than direct lead generation.

The skill operates in two modes:

- **Analysis Mode**: Ingest data, diagnose, deliver a concise MAA
- **Coaching Mode**: Review a user-written MAA, teach transferable principles

## The weekly pipeline (1.5.0)

A weekly run is five stages. Each stage has one job, and the draft does not
start until the pull is complete.

```
Stage 0  READ      the client ledger, spec and overlays. No data yet.
Stage 0b PULL      the full data pack (gaql-query-pack.md, "Pull discipline"). No prose yet.
Stage 1  DRAFT     under shared/frameworks/evidence-gates.md, with a claim register.
Stage 2  HARDEN    dispatch google-ads-reviewer in a fresh context; apply its verdicts once.
Stage 3  RECONCILE numbers vs pack, Actions vs ledger watch list and quarantine, cross-refs.
Stage 4  WRAP      append the ledger and trend row. Stop. The human approves the render.
```

Why the split: on live accounts the first draft consistently started
theorizing on partial data ("we should have pulled this weeks ago"), promoted
one-week observations to Actions, and lost facts the operator held in memory.
Reading the ledger first and pulling everything before writing removes most of
that; the hardener catches the rest. The human touchpoint is one: reading the
Stage 4 summary and approving the render.

Stages 0 to 4 apply to weekly runs. Ad-hoc questions ("why did CPC jump on
Tuesday") skip the pipeline but still respect the gates.

## Core Principles

These principles are baked into every analysis. They come from Dennis Yu's
BlitzMetrics methodology.

### MAA: Metrics → Analysis → Action

Never jump to tactics before diagnosing. Every recommendation cites the metric
it moves and the analysis that justifies it. The MAA is a single cohesive
narrative, not three disconnected sections.

### Balanced Metrics

Never evaluate a metric in isolation. Metrics always travel in pairs:
Conversions ↔ CPA, Revenue ↔ ROAS, CTR ↔ CVR, Impression Share ↔ Marginal
CPA/ROAS, Volume ↔ Profit.

The classic trap: CPA drops from $50 to $15, everyone celebrates, but lead
volume collapsed from 80 to 12 because someone turned off everything except
brand. Always check the balancing metric.

### Top-N Focus

Sort by spend, focus on the top 5-10 items. These account for ~60% of total
spend. Don't analyze the long tail unless hunting for waste. Actionable insight
quickly, not a 20-page report.

**Omit dormant campaigns entirely.** Campaigns with $0 spend (or negligible
spend like <$1) in both the 7D and 30D windows do not appear anywhere in the
MAA, not in Metrics, not in Analysis, not in Action. Don't waste the reader's
attention on campaigns that aren't running. If every campaign in the account is
dormant, say so and skip straight to Action.

**Local Services Ads (LSA) are out of scope.** LSA is a separate Google product
with its own budget. MCP pulls surface LSA campaigns
(`advertising_channel_type = LOCAL_SERVICES`); keep them out of the Search
headline math and out of the report entirely, same treatment as dormant
campaigns. If a client wants LSA reported, it's a separate deliverable.

### "We" Tone

Write as an embedded team member. "We're seeing strong CTR on the emergency
plumbing keywords", not "Your CTR is strong."

## Step 1: Quick Context

Before analyzing, get enough context to interpret the numbers. A $200 CPA might
be excellent for roofing and terrible for drain cleaning.

Ask only what's needed, adapt based on what you already know. Don't force all
five questions if the user is ready to go:

1. **Business & Goals**: What service type? Primary conversion goal (calls,
   forms, bookings)? Target CPA or monthly budget?
2. **Conversion Setup**: Where do conversions happen? Do you trust the tracking?
3. **Service Area & Season**: Geography? Peak or slow season?
4. **Benchmarks**: What does "good" look like for this account?
5. **Known Issues**: Anything already worrying you?

If the user says "just look at the data," work with what you have and flag
context gaps as they become relevant in the analysis.

**On a weekly run, do not ask these in chat.** The ledger answers them
(definitions, target, service area, seasonality, prior decisions). Anything the
ledger does not settle and only a human can answer is appended to the ledger's
Open ASKs with today's date, and the draft proceeds with the fact marked
`(verify)`. A question in chat costs the operator a round trip; a guess costs a
wrong Action. The ledger line costs nothing.

## Step 1.5: Load Client Continuity (ledger first, then the mode)

**Read the client ledger first, in full, before anything else and before any
data pull.** `compiled/ledger.md` in knowledge-base mode or
`{Client}_Ledger.md` in simple mode; format in
`../../shared/frameworks/ledger-template.md`. It holds definitions, standing
rules, the change log, the watch list, the recent-change quarantine, the render
spec and known data faults. The ledger wins on any conflict with the other
continuity files unless a more recent dated entry exists. Do not read a large
status wiki or narrative archive end to end; consult it only to resolve a
specific conflict.

If no ledger exists for a client that has run before, create one from the
template using the continuity files and the last three MAAs, mark every
unconfirmed fact `(verify)`, and say so in the Stage 4 summary. For a brand-new
client, run `google-ads-onboarding` first; it writes the ledger.

Then check what other continuity setup exists, in this order:

**Knowledge-base mode**, the client's folder contains a `compiled/` wiki
(see `CONFIGURATION.md` → "Knowledge-base mode"). Read:

1. `client-knowledge-base.md`, who they are, contacts, engagement terms.
2. `compiled/maa-metric-spec.md`, this client's section order and metric
   names. It overrides this skill's generic format. **If it's missing, stop
   and create it first**, from the most recent MAA in `raw/maa-reports/`,
   or, for a brand-new client with no archive, from the structure this first
   run will produce.
3. `compiled/paid-status.md` (live QS state and the per-client QS anchor),
   `compiled/active-issues.md`, `compiled/data-sources.md` (CID, data path),
   and `compiled/trend.csv`.
4. The most recent MAA in `raw/maa-reports/`, for week-over-week deltas and
   for voice. The spec captures structure; the archived reports capture tone.

If the vault has a `clients/_shared/maa-skills-binding.md` (or equivalent
overlay), read it and apply its overrides, naming, output paths, house style.
The overlay wins over everything generic in this skill.

Wrap-up in this mode (weekly cycle only): update `paid-status.md` and
`active-issues.md`, append the week's `trend.csv` row, archive the posted MAA
to `raw/maa-reports/YYYY-MM-DD.md`. Do NOT create or update a narrative file.

**Simple mode**, no `compiled/` folder, but a `{Client}_MAA-Narrative.md`
exists in the client's output folder. Use it exactly as before: read it before
writing (follow up on open threads, avoid repeating context, update running
themes), and append a dated Weekly Log entry after each weekly MAA.

**No continuity setup**, neither exists. Proceed normally; the MAA stands on
its own. After delivering it, seed continuity for next time: in a structured
vault, bootstrap the client folder per the vault's template; otherwise create
a new `{Client}_MAA-Narrative.md` seeded with the account context and first
weekly log entry.

**Ad-hoc analyses** (not a weekly cycle): read the continuity docs for context
but don't update them, the user will update them with whatever they actually
share with the client.

## Step 2: Get the Data

### MCP Mode (Primary)

If a Google Ads MCP connector is available, pull every dataset live via its
`search` tool (GAQL) against the client's CID, using
`../../shared/frameworks/gaql-query-pack.md`: campaign summary, keyword report
with Quality Score components, search terms, ad report (RSA assets + strength),
and conversion detail by action name, each in 7D and 30D windows.

Rules on this path:

- **Pull the whole pack before writing a word.** Campaign summary,
  `campaign_budget`, keyword report (all statuses for inventory, a second pass
  for metrics), search terms, ad report, conversion detail, network split,
  device split, `user_location_view`, negatives at three levels, `call_view`
  where call assets exist, each in 7D and 30D where windowed. Follow the "Pull
  discipline" section of the query pack: paginate until the count is below the
  cap and record it; a query at exactly its cap is flagged and supports no
  absence claim; verify campaign names belong to this client on every
  response; save the raw response verbatim to the client's `raw/` folder before
  abridging. Any summary or derived block written into the saved pack (a
  weekly call count, a daily note) is computed from the rows by script, never
  typed; a hand-typed block that did not sum to its rows produced four wrong
  sentences on 2026-09-11. Record the run's start timestamp (account timezone)
  at the first query.
- **QS components arrive correctly labeled from the API. Read them AS-IS.** The
  column swap below applies ONLY to the email fallback, applying it to MCP data
  re-introduces the bug it exists to fix.
- **The MCP is read-only.** It cannot mutate the account. Negatives, pauses,
  bid and budget changes go through `google-ads-change-scripts`, never the MCP.
  Reading current state to target a change is fine and encouraged.
- **Mid-cycle pulls are cheap, use them.** When the analysis raises a question
  the initial datasets can't answer, pull the extra data inside the same cycle
  and turn the answer into a grounded action, instead of writing "keep watching"
  and deferring it a week.
- If a query fails or the MCP's authorization has lapsed, fall back to the email
  pipeline below rather than stalling the run.

### Email Pipeline Mode (Fallback)

Data arrives automatically via Gmail from a Google Ads Script that runs weekly.
Search Gmail for label `maa-data-automation` or subject prefix `[MAA Data]` to
find the latest report for a given client.

Each email contains ten datasets embedded in the body between markers:
- `---BEGIN CAMPAIGN SUMMARY 30D---` / `---END CAMPAIGN SUMMARY 30D---`
- `---BEGIN CAMPAIGN SUMMARY 7D---` / `---END CAMPAIGN SUMMARY 7D---`
- `---BEGIN CONVERSION DETAIL 30D---` / `---END CONVERSION DETAIL 30D---`
- `---BEGIN CONVERSION DETAIL 7D---` / `---END CONVERSION DETAIL 7D---`
- `---BEGIN KEYWORD REPORT 30D---` / `---END KEYWORD REPORT 30D---`
- `---BEGIN KEYWORD REPORT 7D---` / `---END KEYWORD REPORT 7D---`
- `---BEGIN SEARCH TERMS 30D---` / `---END SEARCH TERMS 30D---`
- `---BEGIN SEARCH TERMS 7D---` / `---END SEARCH TERMS 7D---`
- `---BEGIN AD REPORT 30D---` / `---END AD REPORT 30D---`
- `---BEGIN AD REPORT 7D---` / `---END AD REPORT 7D---`

The **conversion detail** section breaks out conversions by action name per
campaign (e.g., "Phone Calls: 2, Lead Forms: 3"). Use this to populate the
conversion breakdown in the Metrics section's Conversions bullet. If this
section is missing (older script version), show the total conversion count
from the campaign summary without a breakdown.

The ad report contains: Campaign, Ad Group, Ad Type, Headlines (pipe-separated),
Descriptions (pipe-separated), Ad Strength, Impressions, Clicks, CTR, Cost,
Conversions, and Cost/Conv.

Parse the CSV data between these markers. The client name is in the email
subject: `[MAA Data] Client Name, YYYY-MM-DD`.

### Quality Score column inversion, MANDATORY swap on EMAIL-PATH Keyword Report parse

**Scope: this section applies to the email fallback only. MCP data arrives
correctly labeled, never swap it.**

Deployed versions of the data-collection script have a known bug: in the keyword
query, the GAQL select order for the three QS components doesn't match the CSV
header order, which inverts the **Expected CTR** and **Ad Relevance** columns.
Landing Page Experience is in the middle position and is correct.

**Preferred fix, run the corrector at ingest (mechanical, not a judgment
call):**

```
python3 shared/scripts/correct_qs_columns.py --infile {date}_email-data.txt
```

Then read the `_corrected.txt` file and treat every column AS-LABELED. Do NOT
swap again, double-swapping re-introduces the bug.

**Manual fallback** (only if the corrector cannot run):

```
For each row in KEYWORD REPORT 30D and KEYWORD REPORT 7D:
  ad_relevance_value   = row["Expected CTR"]     # mislabeled in CSV
  expected_ctr_value   = row["Ad Relevance"]      # mislabeled in CSV
  lp_experience_value  = row["Landing Page Exp"]  # correct as labeled
```

After correction, use the corrected values in QS component callouts in Analysis,
any per-keyword QS narrative, and the dispatch triggers (Below Average Ad
Relevance vs. Expected CTR route to different copy fixes, getting the component
right is the whole point).

**Sanity check every run:** keep a per-client anchor (the highest-spend scored
keyword and its known corrected component reads) in the client's notes, and
confirm this week's parse matches it before writing. **Do not print the swap in
the report body**, apply it silently and report only corrected component names.

**Why this lives in the skill body, not just the framework:** this rule
previously lived only in the data-pipeline contract, and a heavier analyzer
prompt read the columns at face value and mislabeled a component on a live
client MAA. Restating it in the body makes it un-missable.

**When this rule will be retired:** per-account, only when a corrected script is
confirmed deployed there, otherwise the swap re-inverts correctly-labeled data.
See `../../shared/frameworks/data-pipeline-contract.md` for the canonical column
mapping and the conditions under which this swap applies.

### Bid Strategy Label Mapping

The GAQL API returns internal bid strategy names that differ from what AMs see
in the Google Ads UI. Always translate to the UI-facing name:

- `TARGET_SPEND` → **Maximize Clicks**
- `MAXIMIZE_CONVERSIONS` → **Maximize Conversions**
- `MAXIMIZE_CONVERSION_VALUE` → **Maximize Conversion Value**
- `TARGET_CPA` → **Target CPA**
- `TARGET_ROAS` → **Target ROAS**
- `MANUAL_CPC` → **Manual CPC**
- `MANUAL_CPV` → **Manual CPV**
- `TARGET_CPM` → **Target CPM**
- `TARGET_CPV` → **Target CPV**

Never use the API label in the MAA output.

### Dual Date Range Analysis

Every MAA uses two time windows:
- **7-day data** is the primary view, the current MAA cycle. This is what the
  Metrics section displays.
- **30-day data** is the trend baseline, used as a reference in the Analysis
  section to identify momentum and whether previous actions had impact. The 30D
  data is NOT displayed in the Metrics section.

When writing the MAA:
- **Metrics section**: Show **7D data only**. Each campaign gets individual
  bullet points for each metric. The 30D data is context you use internally
  but don't display here.
- **Analysis section**: This is where 30D context appears. Use 30D as a
  reference point to support broader observations, not as a headline. Lead
  with the business implication, then cite the trend: "The campaign is
  struggling to compete in auctions, CTR is down to 0.36% this week from
  0.71% over the 30-day window." Don't lead with the number-to-number
  comparison itself.
- **Action section**: Prioritize based on what the 7D data reveals. If 30D
  shows a problem but 7D shows it's already improving, note that and deprioritize.
  If 7D shows a new problem not visible in 30D, escalate it.

### When the user uploads data manually

Auto-detect what they provide. Tell them what you found and what's missing.

### When you need to request data

Keep it short. The AM needs a clear, simple ask, not a training manual on how
Google Ads exports work. Say something like:

> "To run this MAA, I need three exports from the Google Ads account (last 30
> days): **Campaign summary**, **Keyword report with Quality Score**, and
> **Search terms report**. Want me to walk you through pulling those, or can
> you grab them?"

If they need the step-by-step, THEN provide export instructions from
`references/gaql-queries.md`. Don't front-load the full column-by-column
specs unless asked.

### Unexplained state is a ledger gap, not a finding

If the pull shows a state the ledger's change log does not explain (a budget
that moved, a keyword paused, a new ad, a network setting flipped), do not
analyze it as an event. Record it in Generation notes as "unlogged change:
{what}, first seen {date}" and add an Open ASK: "log a change: {what}". The
next run reads the answer from the ledger. A change nobody wrote down is the
single most common source of a wrong Action.

## Step 2.5: Evidence Gates (hard rules, applied while drafting)

The full table with the failure each gate prevents is in
`../../shared/frameworks/evidence-gates.md`. Read it once per session. The
gates cannot be waived by the analyzer; only a dated standing rule in the
client ledger can override one. Foundation breaks (tracking, geo, bidding with
no signal, disapprovals, not serving, budget capped on multiple days in one
window) are exempt and act immediately.

1. No pause, restrict, bid, budget or copy Action on fewer than 30 clicks or
   5 conversions in the window cited. Below that: watch list, first-seen dated.
2. A performance finding becomes an Action only after two prior cycles on the
   ledger watch list. Do not promote a finding created this week.
3. Nothing in the ledger's recent-change quarantine is evaluated as a problem
   or credited as a fix before its exit date.
4. Pull network and device splits before any keyword verdict.
5. Check daily before averaging any budget-lost or spend figure.
6. No absence claim on a dataset that returned exactly its row cap.
7. Absence claims require a query with no status filter.
8. Lead definition, target, windows and service-area test come from the
   ledger, never from the data or a name.
9. **Claim register.** Every causal or trend sentence in Analysis carries a
   reference (dataset, row or figure) in the Generation notes block below the
   report. A sentence with no reference is deleted, not softened. This is what
   lets the hardener work in minutes.
10. The gates apply to good news, bad news and your own new theories alike.

When a gate blocks something you believe is true, write it into the watch list
with the evidence it needs to promote, and move on. That sentence in Analysis
("we are watching X; if Y by date Z, we will do W") is the correct output.

## Step 3: Diagnose

The following checklist is your internal reasoning framework for prioritizing
what to recommend. It exists to help YOU think through the account
systematically. It is NOT something you share with the user.

Never write the words "Tier 1", "Tier 2", "Tier 3", "Tier 4", "diagnostic
ladder", "foundations tier", "hygiene tier", or any similar framework language
in your response to the user. The user sees a clean MAA with numbered action
steps. They don't need to know how you arrived at the priority order, they
just need the recommendations to be in the right order, which this checklist
ensures.

Work through these checks in order. If earlier checks reveal critical issues,
focus your action steps there first.

### Patience Principle, Don't Recommend Changes Too Quickly

This skill's output needs to be safe for people without deep Google Ads
experience to act on. That means resisting the urge to recommend changes
based on a single week of data. Small-budget local service accounts produce
noisy data, one bad week on a relevant keyword doesn't mean the keyword is
broken. True learning takes time, and changing things too frequently prevents
the algorithm from stabilizing.

**Before recommending a change, ask: how long has this been running?**
- Changes implemented last week (new ads, new ad groups, bid strategy
  switches, restructures) should almost never be flagged as problems this
  week. They haven't had time to produce meaningful data.
- A keyword or ad group needs at least 2-3 weeks of consistent
  underperformance before it warrants an action item, unless there's a
  dramatic, obvious signal (e.g., spending $200 with zero clicks, or a
  keyword that's clearly off-intent).
- When in doubt, note the observation in Analysis ("worth watching") rather
  than escalating to Action. An observation in Analysis costs nothing. A
  premature change in Action can set the account back.

The goal of Action is 2-3 solid things we can do this week to improve
performance, not a list of everything that could theoretically be better.

### Structure Before Tactics, Sequence the Fix

Recommendations have a dependency order. The **structural layer** (account and
campaign structure, geo-targeting, conversion tracking) gates the **tactical
layer** (landing pages, keyword routing, bids, ad copy). Never recommend a
tactic that a pending structural change will redo. Before writing any tactical
action, ask: "Does a structural change we are also recommending change where
this tactic lands?" If yes, sequence the structural item first and say so.

- **Landing pages depend on campaign structure.** Don't repoint ads or keywords
  to specific pages before the campaigns those ads live in are settled. If
  campaigns are about to split, page assignment happens after the split.
- **Bidding depends on conversion tracking.** Don't recommend a bid-strategy or
  primary-conversion change before tracking is validated, and check the chosen
  conversion has enough per-campaign volume to support the strategy (smart
  bidding wants roughly 15-30 conversions per campaign per 30 days).

### Verify Structure From the Data, Never From Names

An account or campaign named for one city may target the whole metro. Pull the
actual geo-targeting and campaign structure before making any geo or
landing-page recommendation. Names lie; settings don't.

### Label Inferences as Inferences

A plausible read of the data is not a fact. If per-action conversion counts look
like they overlap, say "this looks like X, to be verified at the source," not "X
is happening." Verify at the source before recommending action on it.

### Check A, Is the foundation working?

- **Conversion Tracking**: Set up? Firing? Signs of breakage (strong CTR + zero
  conversions, sudden drops)? Cross-reference with CRM if possible.
  **Evaluate conversion accuracy at the campaign level only.** If a campaign's
  conversion count looks reasonable for its spend and matches backend data,
  treat it as accurate and evaluate performance against that real number. If
  account-level totals are inflated beyond what the campaigns show, that's
  likely activity from other campaign types (YouTube, LSA, etc.) outside this
  export, flag it briefly and move on. Don't diagnose account-level gaps.
  Focus on whether the campaigns in this export are counting the right things.
- **Bid Strategy**: Manual CPC or maximize clicks → conversion-based strategy is
  often the single biggest win. Needs 15+ conversions/30 days for smart bidding.
  Below that, consolidate or use shared budgets/portfolio bidding.
- **Geographic Targeting**: Tight to service area? "Presence" vs "Presence or
  Interest" setting? Leaking budget to wrong areas?
- **Brand vs. Non-Brand**: Mixed together? Brand inflates CTR, deflates CPA,
  masks non-brand underperformance.
- **Landing Page Relevance**: Dedicated service pages or just the homepage?

### Check B, Is budget leaking?

- **Negative Keywords**: Sort search terms by cost, look for irrelevant queries
  (jobs, DIY, wrong services, wrong geos). Common local service waste: job
  seekers, DIY queries, geographic mismatches.
- **Match Type Guardrails**: Broad match without negatives bleeds budget.
  Graduated proven queries to exact?
- **Ad Copy & Quality Score**: Break QS into its three components and report
  each one explicitly in the Analysis: **Expected CTR** (are the ads compelling
  enough to earn clicks?), **Ad Relevance** (does the copy match search intent?),
  and **Landing Page Experience** (does the LP deliver on the ad's promise?).
  Below Average on any = fixable problem. Always name which component is below
  average, "QS is low" without the component breakdown isn't actionable.
  Ad copy mentions service + city + clear CTA? Call/location extensions present?
- **Ad Copy Relevance**: Review RSA headlines and descriptions against the
  top-performing keywords and search terms. Are the ads speaking to what people
  are actually searching? Look for: generic headlines that don't mention the
  core service, missing geographic relevance (no city/area name), weak CTAs,
  or headlines that don't align with the landing page promise.
- **Ad Strength**: Google rates RSAs as Poor/Average/Good/Excellent. Poor or
  Average usually means not enough headline/description variants or not enough
  thematic diversity. Flag any ad with Poor or Average strength, adding more
  unique headlines is a quick win.
- **Ad Performance Splits**: If an ad group has multiple ads, compare their
  metrics. One ad dramatically outperforming another suggests the weaker one
  should be paused or rewritten.
- **Budget Allocation**: IS lost to budget on good campaigns while bad campaigns
  have leftover? Rebalance.

### Check C, Can we improve performance?

- **Ad Group Coherence**: Tightly themed? Mixed intents in one ad group?
  Restructuring doesn't trigger learning periods (Google 2026 guidance).
- **Device & Time-of-Day**: Mobile-heavy (common for local service calls)?
  Time patterns (emergency = after hours, remodeling = lunch breaks)?
- **Audience Layering**: Observation audiences for home services, homeowners?
- **Landing Page CVR**: Conversion rate variance across pages? Mobile experience?
- **Ad Testing**: 12+ headlines, 4+ descriptions in RSAs? Testing themes?

### Check D, Advanced (rarely needed for local service)

Read `references/playbook-frameworks.md` only when the account is mature and
Checks A-C are clean. Covers: incrementality, profit modeling, cohort/causal
analysis, metric trade-off curves, experimentation protocols.

## Step 4: Deliver the MAA

The output should be concise and directly useful. Not an audit report, a working
document the AM can act on this week.

### Output Format

Save the MAA as a markdown file in the client's output folder. The base output
location is configurable, see `CONFIGURATION.md` at the repo root. The default
convention is:

`{OUTPUT_DIR}/{Client Name}/{Client}_MAA_{YYYY-MM-DD}.md`

Example: `output/Summit Dumpster Rental/SummitDumpster_MAA_2026-04-24.md`

**On a scheduled weekly run, stop after Stage 4.** Do not render the client
view until the operator approves in chat. Finish with a summary of at most
eight lines: leads and CPL vs last cycle, Actions proposed, items the hardener
demoted or dropped, open ASKs for the operator, data faults hit.

`{OUTPUT_DIR}` defaults to `./output` but can point anywhere, a project folder,
a synced drive, or (for BlitzBase users) the client's vault folder. If the client
folder doesn't exist, create it. The file should contain the full MAA (Metrics,
Analysis, Action) as formatted markdown. Present the finished file to the user
when complete.

### Continuity Update (weekly cycle only)

After delivering the MAA during a weekly analysis cycle, update the client's
continuity docs in whichever mode Step 1.5 detected. Record the run's end
timestamp in Generation notes next to the start timestamp; write tokens and
cost if the runtime exposes them and UNKNOWN if it does not.

**Every mode, first:** append to the ledger. One weekly log row; a change-log
row for anything shipped this cycle (date, change, who, source); watch-list
updates (cycles observed +1, new items with first-seen, promotions and drops
as their conditions fall due); new Open ASKs; new quarantine entries with exit
dates; any data fault hit this run. Never rewrite past ledger lines. When the
operator supplied a fact in chat during the run, it becomes a ledger line,
dated, in section 3 (standing rules) or section 2 (definitions), so the next
run does not ask again.

The weekly-log row's Action count is read off the report's Action list at the
moment of writing, not recalled (on 2026-09-11 two rows under-counted by one
and two). The row records file state at that moment; if the client view is
rendered later, a later row says so and the earlier row is left as written.

**Knowledge-base mode:** then update `compiled/paid-status.md` and
`compiled/active-issues.md` with a short dated block, append the week's
`compiled/trend.csv` row, and archive the posted MAA to
`raw/maa-reports/YYYY-MM-DD.md`. Do not create or update a narrative file.

**Simple mode:** update the narrative document (`{Client}_MAA-Narrative.md`):

1. **Add a new Weekly Log entry** at the top of the log (most recent first)
   with today's date. Include: key findings, actions recommended, and open
   questions for next week.
2. **Update Running Themes** if anything shifted, a resolved issue gets
   marked resolved, a new persistent pattern gets added.
3. **Fill in Account Context** if it's still a placeholder.
4. **Fill in Client Contacts** if missing. Note the name(s) and role(s) of
   anyone who receives the MAA, manages the website, or makes strategic
   decisions. This enables the MAA to address action items to the right
   person by name.

**Do NOT update the narrative for ad-hoc analyses.** The user will update it
with whatever they actually share with the client, plus any client feedback.
The narrative reflects what was communicated, not every draft.

### Stage 2: Harden before anything is rendered

When the draft is written, dispatch `google-ads-reviewer` as a subagent in a
fresh context with exactly these inputs: the frozen draft, the raw data pack,
the client ledger, the client metric spec. Not this session's reasoning. It
returns one verdict per finding and Action (KEEP, DEMOTE TO WATCH, DROP,
REPULL) with the gate and the contradicting number. Apply every verdict once:
DEMOTE moves the item to the watch list with today as first-seen; DROP removes
it; REPULL means pull the named data and re-answer in the same cycle. One round
only. Anything still contested after that is listed in Generation notes for the
human, two lines per side, and the draft proceeds with it flagged.

Paste the reviewer's output into Generation notes verbatim: the verdict ledger
table, the BLOCK / WARN / STYLE counts, and the grade before and after the
round, with an Applied / Reworded / Unaddressed status on each row. A prose
paraphrase of the verdicts is not a record; it cannot be counted or audited
across runs.

### Stage 3: Reconcile

Before wrap-up, check: every number ties to the pack; every Action either has
a watch-list entry of two or more cycles or is a foundation break; nothing
quarantined is judged; every "See Action N" pointer resolves; nothing on the
ledger's never-surface list appears; the render spec norms (Action count,
length) are met.

### Metrics

**Campaign-level is the highest level of analysis.** Do not analyze or report
account-level aggregate statistics. Account-level totals will appear in exports
but they may include activity from campaign types outside this analysis (LSA,
etc.) whose goals and conversions are not visible in the export. Analyzing
account-level data risks conflating unrelated activity and producing misleading
conclusions.

If account-level totals are visibly higher than the sum of the campaigns in the
export (e.g., account shows 209 conversions but campaign-level data only shows
1), add a brief callout: "The account-level numbers include activity from
campaigns outside this export, we should verify which conversion actions are
counted at the campaign level to make sure we aren't inflating our counts."
Then move on. Do not try to diagnose or explain the account-level gap.

Break out metrics **by campaign** using bullet points. Each campaign gets a bold
header showing campaign name, campaign type, and bid strategy. Then list
individual bullet points for each core metric, with the **metric name bolded**
as the leading portion of the bullet. Show **7D data only** in this section.

Top-N focus, only include campaigns with meaningful spend.

**Required metrics for every campaign** (always include these seven):
- **Cost**
- **Impressions**
- **Clicks**
- **CTR**
- **CPC**
- **Conversions**, break out by conversion action name when the data includes
  it: "**Conversions**: 4 (2 Phone Calls, 2 Lead Forms)". This tells the reader
  what kind of business activity the ads are driving, not just a count.
- **CPA** (or note "N/A, zero conversions" if applicable)

**Do NOT include an "Other metrics of note" line.** Metrics like search
impression share, IS lost to budget/rank, Quality Score components, and
conversion rate are diagnostic, they belong in the Analysis section where
they can be explained in context. The Metrics section is the "what happened"
overview. Keep it clean: the seven core bullets per campaign, nothing more.

**Example format:**

> **Emergency Plumbing - Search** (Search | Maximize Conversions)
>
> - **Cost**: $2,450
> - **Impressions**: 38,200
> - **Clicks**: 847
> - **CTR**: 2.22%
> - **CPC**: $2.89
> - **Conversions**: 34 (22 Phone Calls, 12 Lead Forms)
> - **CPA**: $72.06
>
> **General Plumbing - PMax** (Performance Max | Maximize Conversions)
>
> - **Cost**: $1,200
> - **Impressions**: 15,400
> - **Clicks**: 312
> - **CTR**: 2.03%
> - **CPC**: $3.85
> - **Conversions**: 8 (5 Phone Calls, 3 Lead Forms)
> - **CPA**: $150.00

**Video and Display campaigns get a condensed format.** Instead of the full
seven-metric breakdown, show them in a compact block: campaign name, cost,
impressions, clicks, and the metric most relevant to their goal (e.g., video
views and cost-per-view for Video campaigns, or CTR for Display). One or two
lines, not a full bullet list. Example:

> **Home Service Contractors Video** (Video | Target CPV), $105.52 spent,
> 21.5K impressions, 3,280 views at $0.03 CPV. Solid engagement for a
> $10/day awareness budget.

After all campaigns, include a **Data gaps** note if relevant, flag missing
data (e.g., empty keyword reports from PMax, no visible search terms). Keep
it brief.

### Business Metrics Trend

Close the Metrics section with a short paragraph (2-3 sentences max) on the
most important business-level question: are we converting? This is a
high-level pulse check on conversion trends, week over week and against the
30-day average. It states what is happening, not why.

Examples:
- "Conversions are trending up, 5 this week vs. 3 last week, with a 30D
  average of 3.4/week. CPA is holding steady at $165."
- "Zero conversions for the second straight week despite 76 clicks. The 30D
  window shows the same pattern, 153 clicks, zero conversions."
- "Steady week, 3 conversions at $82 CPA, in line with the 30D average of
  3.2/week at $79."

If things are going well, this is just a quick confirmation and doesn't need
to feed the later sections. If conversions are declining or absent, this
paragraph naturally sets up what Analysis needs to explore.

---

### Analysis

A narrative explaining what the data means in context, the "why" behind
the numbers. Write in "we" language. Keep to 2-4 focused paragraphs, with
each paragraph no longer than 3-4 sentences. Every paragraph should build
toward the action items, advancing the story of what's happening and why the
recommended actions follow logically.

**Structure the Analysis as a narrative arc, not a topic list.** Organize by
storyline: what happened → why it happened → what that means for the decision.
Don't organize by category (waste analysis, then QS analysis, then strategy
analysis). Instead, each paragraph should build on the last so that by the
time the reader reaches the Action section, the reasoning is already built
and the recommendations feel inevitable.

**Open with the most important diagnostic finding.** Lead with the insight
that drives the biggest action item. Don't open with a recap of last week's
activities, that's backward-looking. The Business Metrics Trend paragraph
in the Metrics section already covers the week-over-week conversion picture.
Analysis opens with *why* things are the way they are.

**Previous efforts can be mentioned briefly, but keep them subordinate.**
If negatives from last week are working or a QS change is showing movement,
weave that into the narrative in a clause or sentence, don't give it a full
paragraph. Example: "The competitor negatives from two weeks ago are holding
no branded bleed this week, but a new waste cluster appeared around
navigational queries." The prior effort is context, not the headline.

**This is where diagnostic metrics live.** Metrics like impression share, IS
lost to budget/rank, Quality Score components, conversion rate, and search
term waste percentages belong here, accompanied by the explanation of what
they mean and why they matter. These metrics were intentionally excluded from
the Metrics section so they could appear here with context rather than as
raw numbers.

Key behaviors:
- **Keep paragraphs to 3-4 sentences.** If a paragraph is running longer, it's
  trying to cover too much. Split it or cut. The Analysis section should be
  tight and scannable, a busy AM reads this between calls.
- If foundational issues exist, lead with that plainly: "Before we optimize
  anything, we need to make sure conversion tracking is solid."
- Always use balanced metrics language: "CPA improved to $35, but volume dropped
  from 45 to 28 leads, we need to understand why."
- Translate to business impact: "47 irrelevant search terms cost $830 last
  month, roughly 4 leads at our current CPA."
- Be tactful: "still gathering data" not "failing."
- **Routine items get brief treatment.** Search term cleanup, standard negative
  keyword additions, and ongoing optimization work are expected week to week.
  Don't over-explain them unless there's a decision to make. "We found another
  $40 in waste on navigational queries, negatives are ready to run" is enough.
  A full paragraph dissecting each waste term is too much unless the pattern
  reveals something new or requires a strategic choice.
- **Narrative continuity**: If a narrative document exists, reference prior
  findings briefly where relevant. Don't repeat context the narrative already
  captures, build on it.
- **Always end the Analysis section with a standing CRM quality prompt.** This
  is a brief, consistent checkpoint, not an action item. Frame it around lead
  quality, not tracking verification. Examples:
  - When conversions exist: *"CRM check: We recorded 23 conversions this week
how's the quality of those leads looking?"*
  - When zero conversions: *"CRM check: Google shows zero conversions this
    week, are we seeing any calls or form fills that aren't being tracked?"*
  This stays in Analysis every week as a standing prompt to the AM. It only
  escalates to an Action item if the data itself suggests something is broken
  (e.g., strong CTR with zero conversions over multiple weeks, or a sudden
  drop from a known baseline).
- **Stay at the campaign level.** If account-level totals don't match campaign
  totals, note it briefly and recommend verifying conversion actions, but don't
  try to explain the gap or build analysis around account-level numbers.
- Don't restate what's already visible in the Metrics bullets, interpret and
  connect the dots instead.
- **Use 30D trends as supporting evidence, not headlines.** When comparing 7D to
  30D, weave the trend into a broader observation rather than leading with it.
  Instead of "CTR halved from 0.71% to 0.33%" as the opening, lead with the
  business implication and use the trend as backup: "The campaign is struggling
  to compete in auctions, CTR has been sliding and is down to 0.33% this week
  from 0.71% over the 30-day window."
- **Video/Display gets a brief note, not deep analysis.** One or two sentences
  on whether the awareness campaign is delivering as expected. Don't force lead
  gen diagnostics onto awareness campaigns. If a Video or Display campaign has a
  notable finding (e.g., irrelevant placements, surprising engagement), call it
  out, otherwise, a quick "running as expected" is sufficient.
- **Weave ad copy findings into the narrative.** The ad report data (headlines,
  descriptions, ad strength, per-ad performance) should inform Analysis
  naturally, not as a separate section. When discussing a campaign's
  performance, note if ad copy is a contributing factor. Examples:
  - Poor CTR + generic headlines → "Part of the CTR problem may be the ad copy
the headlines don't mention veneers specifically, which is what people
    are searching for."
  - Ad strength rated Poor/Average → "Google is rating this RSA as Average,
    which usually means it needs more headline variety to find winning
    combinations."
  - One ad dominating impressions over another → "One ad in this ad group is
    pulling nearly all impressions at a much higher CTR, the other may be
    dragging performance down."
  If the ads look healthy and well-aligned, there's no need to force ad copy
  commentary. Only surface it when it's a meaningful factor.

### Action

2-3 specific, forward-facing action steps, things we can do this week or
next to improve ad performance. Prioritized by the diagnostic ladder (without
mentioning the ladder). Each action step should:

- State what to do in plain language
- State why, linked to something in the Analysis
- Note expected impact where possible

**One Action list, owners tagged inline.** Write a single numbered list with the
owner tagged inline (e.g. "... (Josh)" for a client decision; agency items carry
the agency owner or none). Do NOT split Action into per-person sub-sections,
the split invites padding one person's list to look balanced. The inline tag is
also what the client-view render routes on: client-tagged items feed "what we
need from you," agency-tagged items feed "what we did."

**No padding, no non-actions.** Never invent items to hit a count. "Keep holding
budget," "continue monitoring," and "no change needed" are Analysis conclusions,
not Actions. Three real items beat five with filler.

**No method notes in the report body.** Internal data-integrity steps (the QS
corrector, delta computation rules) never appear in the MAA or client view.
Apply them silently.

**Every action item must be forward-facing.** The test: does this item
describe something we're going to *do*, or something we already *did*?
Confirming that last week's negatives are holding, noting that the new ads
haven't moved QS yet, or checking that a previously excluded keyword stayed
out, those are observations, and they belong in Analysis. Action is
exclusively about what happens next.

Watching or monitoring something *can* be an action item if it's flagging a
potential future problem: "Watch 'demolition bin rental', if it continues
spending without converting over the next 1-2 weeks, consider pausing." That's
forward-facing because it describes what we might need to do. But "We checked
and keyword A didn't show up this week" is backward-facing and belongs in
Analysis.

The ordering naturally starts with the biggest-impact fixes first (broken
tracking, wrong bid strategy) before leakage fixes (negatives, QS) before
optimization work (creative testing, audiences, ad copy improvements). The user
just sees a numbered list of smart recommendations, your internal reasoning is
invisible.

### Distinguish "things we did" from "things the client needs to do"

Action items fall into two categories, and they should read differently:

**Our-side items** (negatives added, scripts run, ad copy changes made):
Use completion language. If already done, mark with ✅ and state what happened.
If pending but within our control, state what we'll do and when.

**Client-side items** (landing page changes, CRM access, strategic decisions):
Use collaborative language. Address the client contact by name (from the
narrative document). Frame as a partnership, not a task assignment:
- "Nicholas, we noticed the interior page headline still references winter
  services, would you like us to take a pass at updating it? We'd need
  Elementor access."
- "Sam, do you have a sense of what types of consumers are specifically
  searching for 'roll off dumpster'? The answer would help guide which route
  we pursue."

The pattern: name the person → describe the situation → ask a specific
question or make a specific offer with a specific gate (what you need from
them to proceed).

### When the skill presents strategic options, end with a question

When an action item involves a strategic choice (restructure vs. rewrite,
pause vs. hold, switch bid strategy vs. wait), present the options and then
ask the client a question that helps inform the decision. The skill should
inform the decision, not make it. The question positions the client as a
decision-maker with expertise the data alone can't provide.

**Example:** "From our perspective, two options: (a) write dedicated
headlines, or (b) break the variants into their own ad group. Sam, do you
have a sense of what types of consumers search for 'roll off dumpster'? The
answer would help guide which route we pursue."

### Split completed and open items when density is high

When more than half of the action items are already completed, the reader has
to wade through done items to find what still needs their attention. In these
cases, lead the Action section with a brief note on what was completed this
week, then list the open items in detail:

> **This week's priority order: stop the bleeding first, then fix the structure.**
>
> 1. ✅ **Negatives script run (4/17).** 27 negatives added. Estimated
>    $140–160/week in waste eliminated.
> 2. ✅ **AI Max turned off (4/17).** Confirmed with Google rep.
>
> 3. **Hold Maximize Conversions through 5/1, decision point extended.**
>    [detailed rationale...]
> 4. **Apply English-only language targeting, still pending.** [details...]

This keeps the completed items visible for the record without burying the
open items.

**Ad copy actions belong in the optimization tier**, they're important but
rarely the first thing to fix. Typical ad copy action items include: adding
more headline/description variants to improve ad strength, rewriting headlines
to better match high-value search terms, pausing underperforming ads, or
adding geographic or service-specific language. When recommending ad copy
changes, be specific, cite the actual headlines that need work and suggest
concrete alternatives based on what the search term data shows people are
looking for.

**Merge related actions into single steps.** If two actions are naturally done
together (e.g., building a new campaign + pre-loading negatives for that
campaign), combine them into one action step. Don't pad the list, fewer,
meatier steps are better than more granular ones.

### Quarterback Dispatch, Chaining Downstream Skills

The analyzer is the quarterback of the Google Ads skill pipeline. When
diagnosis reveals a problem that a downstream skill can solve, don't just
mention the skill, dispatch it. This means including enough context in the
action item that the downstream skill can execute immediately when the user
(or a scheduled task) triggers the chain.

**Dispatch triggers and what to hand off:**

| Condition Detected | Dispatch To | Hand Off |
|---|---|---|
| Below Average Ad Relevance or Expected CTR on keywords with >$50/week spend | **google-ads-copy-optimizer** | Ad group name, current headlines/descriptions, top search terms for that ad group, QS component breakdown. From 1.6.0 the optimizer builds its own fact sheet from the client's website and reads 90-day search terms and earlier copy tests itself; the hand-off only has to name the ad group and the trigger |
| Waste terms identified totaling >10% of campaign spend | **google-ads-change-scripts** | List of terms to negate, match types, campaign name, estimated weekly savings |
| Below Average Landing Page Experience on keywords with meaningful spend, OR strong CTR + zero conversions for 2+ weeks | **google-ads-lp-auditor** | Landing page URL, current ad copy (headlines + descriptions), QS component data, campaign context (business, target CPA, conversion action, audience) |
| Ad group restructure recommended (e.g., keyword needs its own ad group) | **google-ads-change-scripts** | Keywords to move, source/destination ad group names, match types |
| Ad rated POOR or AVERAGE strength | **google-ads-copy-optimizer** | Current headlines/descriptions, ad strength rating, ad group's top search terms |
| A live ad claims something the client's website contradicts (a size, service, price or review figure), found by the copy optimizer's fact check or by the analyzer | **google-ads-copy-optimizer** (correction) | Ad ID, the contradicted line, the page that contradicts it. Foundation-level: exempt from gates 1 and 2 |
| Headline or description assets rated LOW in `ad_group_ad_asset_view` on two consecutive cycles (from the watch list) | **google-ads-copy-optimizer** | Ad group, the LOW assets, top search terms, earlier copy tests from the change log |

**How to write a dispatch in the Action section:**

Don't write: "The google-ads-copy-optimizer skill can generate headlines."
(This is a suggestion to the air.)

Do write: "**Dedicated RSA created for 'Roll Off Dumpster' ad group.** 15
headlines covering core service, geo, urgency, CTAs, sizes, and
differentiators. 'Roll Off Dumpster Rentals' pinned to H1."
(This is what happens when the optimizer was actually dispatched.)

Or, if the action is pending and needs the user to trigger it: "**Next step:
generate dedicated ad copy for the new ad group.** The copy optimizer has
what it needs, the top search terms, the QS breakdown, and the current
headlines. Ready to run when you are."

The goal is that each MAA action item either (a) was already handled by a
downstream skill during this session, or (b) is staged with enough context
that a single command triggers the downstream skill. No action item should
require the user to re-explain the problem to another skill.

### The "Start here" close

End the Action section with a close that does one of these, not a formulaic
restatement of the top action item:

1. **Name a person and make a specific ask**: "Nicholas, we need to get going
   on the interior page copy fixes. We're happy to help if you'd like, we'd
   just need website access."
2. **Pose the most important open question for next week**: "The key question
   going into next week: does the cleaned-up traffic mix produce the account's
   first conversion under Maximize Conversions?"
3. **Both**: A named ask followed by the open question.

If the top action item is already completed (e.g., negatives were run during
this session), the close should point to what's next, not what's done.

**Example of the right level of conciseness for an Action section:**

> 1. ✅ **Added 12 negative keywords**, $640/month in waste on job-seeker
>    and DIY queries, stopped today.
> 2. **Switch the main campaign from Maximize Clicks to Maximize Conversions**,
>    we're optimizing for traffic volume, not leads. With 18 conversions last
>    month, we have enough data for smart bidding.
> 3. **Create a separate brand campaign**, brand and non-brand are mixed,
>    which makes our $45 CPA look better than it really is on non-brand.
>
> **Start here:** Sarah, the bid strategy switch is the biggest lever we
> haven't pulled yet. Do you want us to make the change this week, or would
> you prefer to wait until the negatives have a week of clean data?

## Coaching Mode

When a user submits their own MAA for critique or wants to learn the process,
read `references/coaching-guide.md` for the full coaching framework. The short
version: be specific about gaps, teach transferable principles (balanced metrics,
the "because" bridge, action-to-analysis linkage), and use a constructive tone.

Important: even in coaching mode, don't teach the internal diagnostic checklist
labels (Check A/B/C/D or any tier numbering). Instead, teach the underlying
principle: "fix what's broken before optimizing what works" and "verify your
foundation before scaling." The sequencing concept is valuable to teach, the
internal labels are not.

## PMax-Specific Notes

- Asset Groups replace ad groups, evaluate by asset group theme
- Search term visibility is limited, use insights tab and categories
- Brand exclusions are critical, without them, PMax claims brand conversions
- URL expansion controls matter, is PMax going to intended pages?
- Watch for PMax/Search cannibalization (balanced metrics: PMax CPA looks good
  but total conversions didn't grow)

## Google's 2026 Structural Guidance

> Label: unverified. These points came from Google account representative
> conversations in 2026 and have not been confirmed against a published Google
> page. See the Sources table above. Do not quote them to a client as Google
> policy.

- **Consolidation** over granularity, fewer campaigns with more data density
- **15 conversions/30 days** threshold for smart bidding
- **AI Max** uses LLM-based intent matching, be curious about unexpected queries
- **Restructuring doesn't trigger learning periods**, bidding models recognize
  assets regardless of structure
- **Brand and geo controls** are the modern segmentation levers
