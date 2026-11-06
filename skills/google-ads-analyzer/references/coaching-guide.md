# Coaching Mode Guide

## When to Enter Coaching Mode

Coaching mode activates when the user:
- Submits their own MAA and asks for feedback ("Here's my MAA, help me improve
  it")
- Asks to learn how to write an MAA
- Wants to understand the analytical process, not just get an answer
- Asks about experimentation or testing methodology

## Evaluating a User-Written MAA

When reviewing a user's MAA, evaluate across these dimensions. Be specific,
"the analysis needs work" teaches nothing. "The analysis identifies the CPA drop
but doesn't check what happened to lead volume" teaches a transferable principle.

### Metrics Section Review

- **Completeness**: Are the key metrics present? For local service, at minimum:
  spend, conversions, CPA, CTR, impression share
- **Paired presentation**: Are metrics shown in balanced pairs, or presented in
  isolation? Flag any metric that appears without its counterpart
- **Top-N focus**: Does the summary prioritize the highest-spend/highest-volume
  items, or does it try to cover everything equally?
- **Data gaps**: Are missing metrics acknowledged, or silently ignored?

### Analysis Section Review

- **Diagnostic depth**: Does the analysis explain WHY a metric moved, or just
  restate that it moved? "CPA increased 40%" is a metric. "CPA increased 40%
  because three high-cost search terms entered the auction after we broadened
  match types" is analysis
- **Balanced metrics awareness**: When one metric improves, does the analysis
  check the counterpart? A CPA improvement without checking volume is incomplete
- **Business context**: Does the analysis connect data to the business reality?
  A 15% conversion rate drop during December might be seasonal for roofers but
  alarming for emergency plumbers
- **Tone**: Is it "we" language or detached third-person? Does it sound like a
  team member or an auditor?
- **Speculation vs. evidence**: Does the analysis distinguish between what the
  data shows and what it might suggest?

### Action Section Review

- **Tied to analysis**: Does every action trace back to a specific insight? Flag
  any recommendation that appears without supporting analysis
- **Prioritized**: Are actions ranked by impact and effort? The single most
  important thing should be obvious
- **Specific**: "Improve ad copy" is vague. "Test 3 new headlines emphasizing
  24/7 availability on the emergency plumbing ad group, where CTR is 2.1% vs.
  the account average of 4.3%" is actionable
- **Priority-appropriate**: Are the actions sequenced by impact? Recommending
  audience layering when conversion tracking is broken is putting optimization
  before fundamentals, always fix what's broken before improving what works
- **Sequenced**: Is there a clear "do this first" recommendation?

## Teaching the MAA Process

When a user wants to learn the MAA framework, walk them through it using their
actual data if available. The progression:

1. **Start with the question**: "What's the one thing about this account you most
   want to understand?" This grounds the analysis in a real concern rather than
   abstract methodology.

2. **Model the paired-metric habit**: Show them how to always pull up the
   counterpart metric. Make it a reflex. "You mentioned CPA dropped, great.
   What happened to conversion volume in the same period?"

3. **Teach Top-N discipline**: Have them sort by spend and look at the top 5
   items. What patterns emerge? This prevents the common trap of spending an hour
   analyzing a keyword that spent $12 last month.

4. **Practice the "because" bridge**: The gap between metrics and analysis is the
   word "because." Train them to never state a metric without following up: "CPA
   increased 40% BECAUSE..."

5. **Connect actions to evidence**: For each recommended action, ask "which
   metric does this move, and what in the analysis supports it?"

## Experimentation Protocol

When the coaching conversation moves toward testing, introduce the hypothesis-
driven experimentation framework. This is especially valuable for local service
accounts where the temptation is to "just try stuff."

### Structure of an Experiment

**Hypothesis**: What do you expect to happen, and why? Be specific about the
metric AND the mechanism. "Switching the emergency plumbing campaign from
maximize clicks to target CPA ($45) will increase conversion volume by 15-20%
because the current manual bids are undervaluing high-intent evening queries."

**Controlled Exposure**: Limit the blast radius. For local service accounts, this
often means: test on one service line before rolling out to all; or test in one
geographic area if the business has multiple service zones.

**Duration & Power**: Run for at least 2x the typical conversion lag. For local
service businesses with phone call conversions, this is usually 7-14 days.
Longer for businesses with longer sales cycles (remodeling, commercial HVAC).

**Success Criteria**: Define in advance what "winning" looks like. Must include
the primary metric AND the balancing metric. "Target CPA held below $50 AND
conversion volume remained above 25 leads per week."

**Guardrails**: Pre-define the stop/scale rules. "If CPA exceeds $70 for 3
consecutive days, revert. If CPA is below $40 with 30+ conversions/week after
14 days, roll out to remaining campaigns."

**Documentation**: Record what you tested, what happened, and what you learned.
Even failed experiments have value, they narrow the solution space.

### Common Experiments for Local Service Accounts

- Switch from manual CPC to maximize conversions or target CPA
- Add negative keywords for top waste categories (jobs, DIY, wrong location)
- Test dedicated service landing pages vs. homepage
- Test urgency-based headlines vs. trust-based headlines
- Broaden geographic targeting slightly with bid modifiers
- Add call extensions or test different call-to-action variants

## Analysis Checklists

### Daily Quick Check (5-10 min)

- Spend pacing vs. daily budget, any campaigns limited by budget?
- Any anomalies in cost, conversions, or CPA vs. trailing 7-day average?
- Any new disapproved ads or policy flags?
- Quick scan of search terms from yesterday, anything obviously irrelevant?

### Weekly Analysis (20-30 min)

- Full search terms review: add negatives, graduate good terms to exact
- QS component check: any keywords that dropped below average?
- Budget allocation review: any rebalancing needed based on performance?
- Ad copy rotation: are all RSA variants serving? Any underperformers?
- Impression share trends: are we losing ground to competitors?
- Running experiments check: how are active tests performing vs. criteria?

### Monthly Review (45-60 min)

- Full MAA: Metrics summary, Analysis narrative, prioritized Action list
- Conversion data verification: do Google Ads numbers match CRM/call tracking?
- Balanced metrics check across the full account: volume AND efficiency trends
- Budget planning: any seasonal adjustments needed for next month?
- Experiment post-mortems: what did we learn? What's the next test?
- Competitive landscape: any Auction Insights shifts?
- Report to stakeholder/client: what happened, what we did, what's next
