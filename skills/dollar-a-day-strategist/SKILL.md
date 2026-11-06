---
name: dollar-a-day-strategist
description: Amplify PROVEN organic content with Dennis Yu's Dollar-a-Day — $1/day for 7 days, kill the bottom 90%, then recommend $30 over 30 days behind winners. Use to turn posts with real engagement into reach, retargeting pools, and deals.
---

# Dollar-a-Day Strategist

**Use this when** you have organic posts that already earned engagement and want to convert them into reach, retargeting pools, and deals for less than your coffee budget. Step 7 of the Local Service Spotlight method — the Promote P of the Content Factory.

## Inputs
- Your organic posts/clips with REAL engagement numbers — comments, shares, watch time, not raw impressions.
- Your verified proof moments and podcast clips, including what happened, why it matters,
  and the source receipt.
- Plumbing in place: pixels, analytics, saved audiences. Boosting without a pixel is reach you can't retarget.
- A current `gct-screen` result plus accepted engagement/roster evidence when this is
  client work. Qualification does not authorize spend.
- Action authority. Default `STAGE_ONLY` means recommendations and calendars only. A
  live test needs the exact platform/account, billing owner, amount ceiling, dates,
  creative/claim approval, kill metric, and human approval receipt.

## The rules — non-negotiable
- Recommend boosts ONLY for proven organic. Boosting amplifies a winner; it does not rescue a weak post. A hook that failed at $0 fails at $100.
- $1/day × 7 days per post. Small money buys real signal.
- At day 7, recommend killing the bottom 90%. No sunk-cost stories.
- Recommend $30 over 30 days for winners. New audiences and bigger budgets are separate
  human-approved tests.
- Story-rich proof and podcast clips may jump the queue after they prove organic demand.
  A recognizable guest alone is not proof, relevance, or a reason to spend.

## Steps
1. **Rank** your last 60–90 days of organic by real engagement. The audience already voted; respect the vote.
2. **Pick the top 5.** For each, write the GCT chain: **Goal** (leads, retargeting pool, authority — what is this boost FOR), **Content** (this proven post), **Targeting** last.
3. **Stage $1/day for 7 days.** Layer one candidate per day in the plan; with five posts
   the proposed daily ceiling peaks at $5. Execute only under an exact approval receipt.
4. **Read each post's day 7 through MAA:** **Metrics** say what (CPM, CTR, cost per engagement, watch time). **Analysis** says why (hook, audience, or offer). **Action** closes the gap — kill, re-cut the hook, or scale.
5. **Recommend killing the bottom 90%.** Propose $30 over 30 days behind each winner.
   The agent does not pause, kill, scale, spend, or move an audience.
6. **Hunt unicorns.** Propose survivor tests against new audiences and higher budgets.
   Execute only after the exact new scope is approved.

## Targeting — the T in GCT (choose last)
- Warm first: engaged viewers, profile engagers, site visitors off your pixel (the plumbing from step 5).
- Conversation-adjacent: followers of a named guest or brand only when the clip contains
  a substantive, relevant exchange and that audience fits the GCT. Fame alone is not
  targeting.
- Cold last: lookalikes of converters — only after a winner proves itself warm.

## Week one, laid out
- The staged calendar layers candidates A–E across days 1–5 and shows the proposed
  account-wide daily ceiling. Nothing launches until the exact plan is approved.
- Each approved test gets its own day-7 read; the agent writes a kill/hold/scale
  recommendation as each lands.
- Day 8 onward, stage the next set from fresh organic evidence. Do not imply continuous
  spend when an approval expires.

## Budget math
- Illustrative budget: 5 proposed posts × $7 = $35; each approved winner adds a proposed $30 over 30 days. This arithmetic is not a performance forecast; the actual total depends on approved scope and results.
- The byproduct is the asset: everyone who watched joins your retargeting pool — the warm audience for your next offer.

## Output
- A 7-day boosting calendar: post, hook, goal, audience, daily budget.
- A kill/scale decision per post at its day 7, and a $30/30 plan per winner.
- A growing retargeting pool that compounds with every boost.
- A receipt that distinguishes `STAGED`, `APPROVED`, `EXECUTED`, and `VERIFIED`, with
  source period and approval scope. A scheduled job may produce recommendations only.

## For DealCon — agency owners & acquirers
**If you run an agency:** Dollar-a-Day is a productized add-on with near-zero delivery cost — clients see compounding results on $30–90/month of media, and the kill/scale discipline proves stewardship better than any deck.
**If you buy & sell companies:** put $1/day behind your deal-thesis content and documented proof clips so sellers and brokers have been seeing you for months before the first call; post-close, boost the acquired brand's already-proven posts for immediate lift with zero new creative spend.
**Your edge:** which one clip carries the strongest useful moment and has already earned enough organic response to deserve a $30 test?

## Run in a supported persistent-agent runtime
- **Loop to done:** this is a long-horizon evidence loop — day-7 reads, recommendations,
  and the next candidate set. A persistent agent holds the calendar and never misses a
  decision receipt; it does not execute that decision.
- **Self-verify:** check every proposed test against the evidence and exact approval
  scope before any human or authorized executor acts.
- **Compound with memory:** keep the engagement history, kill list, and winners in memory so each week's ranking starts from evidence, not a fresh export.
- **Log the run:** record every kill/scale call with its MAA reasoning — the unicorn pattern emerges from the log.

See `boil-the-ocean.md` for the full operating principles.

## Notes — Dennis's method
- Use a real recording, useful derivatives and observed organic engagement to choose a test. A small test budget is an operating method, not a guarantee of customers or revenue.
- It's a PR team that works for a dollar a day: test cheap, kill losers fast, pour fuel on unicorns.
- Targeting comes LAST in GCT. Goals and content first — no audience can fix a post with nothing to say.
- Prioritize podcast clips that contain a useful, attributable exchange and already earned
  engagement. An appearance by itself is inventory, not positive proof.
- You don't need the factory running to start. Boost what you've already posted; once `content-factory` (step 8) comes online, it feeds this skill every week.

## Definitive article & pairings
- Reference: https://blitzmetrics.com/content-factory/ (Dollar-a-Day is taught inside the Content Factory) · https://dennisyu.com/podcast-appearances/
- Pairs with: ai-search-visibility → **dollar-a-day-strategist** → content-factory → definitive-article-writer

## Shared rules — harness layer (referenced, not inlined)

This skill operates under the fleet's shared-rule appendix, which lives ONCE at the
harness layer instead of being pasted into this file:

- **Appendix file:** the shared-rule appendix (35 blocks) — canonical
  blocks live in this repo's `standards/` directory; the harness carries the
  appendix as one file generated from them, and standalone exports inline it
  at packaging time (`sync_shared_rules.py --export`). It comprises fleet standards,
  coordination/ownership rules, QA gates, and field lessons that apply pack-wide).
- **How to use it:** the appendix is part of this skill's instructions. Read the
  blocks relevant to the task at hand before acting; where a block sets a gate,
  threshold, filing rule, or prohibition, it binds exactly as if it were printed here.
- **Precedence:** if a core instruction above and an appendix block conflict, the
  more specific instruction wins; if still tied, the appendix's QA/safety gate wins
  and the conflict is noted in the run's receipt.
- **What changed:** nothing about the rules — only their address. The core above is
  the recipe; the appendix is the standing orders every recipe runs under.
