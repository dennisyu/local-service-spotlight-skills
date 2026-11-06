# Advanced Analysis Frameworks (Tier 4)

These frameworks are for mature accounts where Tiers 1-3 are clean and the
question shifts from "fix what's broken" to "find the next 10% of growth." Most
local service accounts won't need these, but they're available when the situation
calls for them.

## Intent Coverage & Cannibalization Analysis

**When to use**: When you suspect gaps in keyword coverage, or when PMax and
Search campaigns may be competing for the same queries.

**Inputs**: Search terms (last 30/90 days), n-grams, negatives map, asset group
URLs, brand exclusion lists.

**Process**:
1. Map every query to an intent tier (Tier 0: brand, Tier 1: high-intent
   transactional, Tier 2: evaluative/consideration, Tier 3: problem/symptom)
2. Identify coverage gaps, intent tiers with few or no queries
3. Identify conflicts, brand queries leaking into non-brand campaigns, PMax
   claiming Search queries
4. Produce a re-routing plan: which queries belong where, which need new
   campaigns or ad groups

**Output**: Query-to-intent mapping, gap list, conflict list, re-routing
recommendations.

## Creative Effectiveness Analysis

**When to use**: When ad copy performance has plateaued or when testing new
messaging themes.

**Inputs**: RSA asset ratings, combination performance data, headline/description
lift metrics.

**Process**:
1. Evaluate RSA asset mix: which headlines and descriptions have "Best", "Good",
   "Low" ratings?
2. Compare CTR vs. Quality Score Expected CTR, divergence suggests the ad is
   compelling but misaligned with the keyword
3. Analyze landing page cohorts: CVR and bounce by LP template
4. Check Core Web Vitals and form friction indicators

**Output**: Refresh recommendations, message kit suggestions (pain-point, proof,
offer, CTA variations), LP improvement priorities.

## Bidding & Budget Efficiency Analysis

**When to use**: When the account is hitting performance targets but you suspect
budget could be allocated more efficiently, or when there's pressure to scale.

**Inputs**: Campaign-level tROAS/tCPA delivery, constraint diagnosis (Lost IS:
Budget vs. Rank), ROAS vs. Impression Share curves.

**Process**:
1. **Goal Attainment Grid**: For each campaign, plot actual CPA/ROAS vs. target.
   Identify which are hitting target with headroom, which are at capacity, and
   which are missing target.
2. **Price Elasticity**: Plot ROAS vs. Impression Share at varying spend levels.
   Find the efficient frontier, the point where incremental spend yields
   diminishing returns.
3. **Reallocation Model**: Shift budget from campaigns past their efficient
   frontier to campaigns with headroom. Consider shared budgets or portfolio
   bidding to smooth allocation.

**Output**: Budget reallocation recommendations, portfolio strategy suggestions,
spend efficiency frontier visualization.

## Metric Trade-Off Analysis

**When to use**: When facing the classic tension between volume and efficiency.
This is the quantitative expression of Dennis Yu's balanced metrics principle.

**Inputs**: CPA, Conversions, ROAS, Profit (or estimated profit if revenue data
is available).

**Process**:
1. Plot the trade-off curve: volume (conversions) on one axis, efficiency (CPA
   or ROAS) on the other
2. Identify the current operating point and the sweet-spot range
3. Flag early-warning zones: where pushing for more volume will break efficiency,
   or where tightening efficiency will starve volume

**Output**: Trade-off visualization, sweet-spot recommendation, specific levers
to adjust (CPA targets, bids, negatives, audience mix).

**Common scenarios for local service**:
- Low CPA, low volume: Broaden match types with negatives, expand audiences,
  relax CPA targets incrementally
- High volume, unprofitable CPA: Tighten negatives and LP relevance, apply
  value rules, shift budget toward higher-intent campaigns

## Profit Modeling

**When to use**: When close-rate data is available (from CRM) and you want to
optimize for actual profit rather than lead volume.

**Inputs**: Close-rate by keyword/audience, average revenue per closed deal,
COGS/variable costs if available.

**Formulas**:
- POAS = (Revenue - COGS - variable fees) / Ad Cost
- Blended CAC = Total Marketing Cost / New Customers
- Payback (months) = CAC / Monthly Gross Margin per Customer
- True ROAS (lead-gen) = (Closed Revenue x Close Rate x Gross Margin) / Ad Cost
- Expected Profit Per Click (EPPC) = (Conversion Rate x Close Rate x Gross
  Margin) - CPC

**Process**: Calculate EPPC by keyword or ad group. Rank by EPPC to identify
which keywords actually make money vs. which look good on CPA but don't convert
downstream. This is the ultimate balanced metric, it captures the full funnel.

## Experimentation Protocol (Detailed)

For Tier 4 experiments, use the full protocol from the coaching guide but with
additional rigor:

**YAML Experiment Spec** (for documentation):
```yaml
name: "Emergency plumbing tCPA test"
hypothesis: "Lowering tCPA from $60 to $45 will maintain 80%+ of volume while
  improving efficiency, because current bid is above the efficient frontier"
metrics:
  primary: cost_per_conversion
  balancing: conversions
segments: [campaign: emergency-plumbing-phoenix]
exposure: 100%  # full campaign, no split possible
duration: 21 days  # 3 weeks, 2x conversion lag
success_criteria:
  stop: "CPA > $75 for 5 consecutive days"
  scale: "CPA < $50 AND conversions >= 20/week for 14 days"
rollback: "Revert tCPA to $60"
owner: "account_manager_name"
```

## When to Recommend Tier 4

Don't proactively push Tier 4 analysis. Engage it when:
- The user specifically asks about incrementality, profit modeling, or advanced
  testing
- Tiers 1-3 are genuinely clean and the conversation naturally evolves toward
  growth questions
- The account has sufficient data density (multiple months of clean conversion
  data, ideally with CRM close-rate integration)
- The business is sophisticated enough to act on the insights (a solo plumber
  probably doesn't need EPPC modeling; a multi-location HVAC franchise might)
