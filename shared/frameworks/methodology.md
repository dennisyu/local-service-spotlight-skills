# MAA Methodology, How These Skills Think

The skills in this package implement the MAA (Metrics → Analysis → Action)
approach to managing Google Ads for local service businesses. The full
operating rules live inside each `SKILL.md`; this is the shared mental model
that ties them together.

## MAA: Metrics → Analysis → Action

Never jump to tactics before diagnosing. Every recommendation cites the metric
it moves and the analysis that justifies it. The output is one cohesive
narrative, not three disconnected sections.

## Balanced metrics

Never evaluate a metric in isolation. Metrics travel in pairs: Conversions ↔ CPA,
Revenue ↔ ROAS, CTR ↔ CVR, Impression Share ↔ marginal CPA/ROAS, Volume ↔ Profit.
The classic trap: CPA drops and everyone celebrates, but lead volume collapsed
because someone turned off everything except brand. Always check the balancing
metric.

## Top-N focus

Sort by spend, focus on the top 5–10 items (~60% of spend). Skip the long tail
unless hunting for waste. Omit dormant campaigns entirely. Actionable insight
fast, not a 20-page report.

## Patience principle

Small-budget local accounts produce noisy data. A single bad week is not a
trend. Changes made last week should rarely be flagged as problems this week.
A keyword or ad group needs 2–3 weeks of consistent underperformance before it
warrants an action item, unless the signal is dramatic and obvious. When in
doubt, note the observation in Analysis ("worth watching") rather than
escalating to Action.

## The ledger and the gates (1.5.0)

Every client carries a ledger (`ledger-template.md`): definitions, standing
rules, change log, watch list, recent-change quarantine, render spec, known
data faults. The analyzer reads it before any data and appends it after every
cycle. It replaces the memory a human operator otherwise supplies by hand,
which on live accounts was about 40% of all human interventions.

Findings become Actions only through the evidence gates
(`evidence-gates.md`): minimum sample, two-cycle persistence on the watch
list, a 14-day quarantine on recent changes, splits before verdicts, no
absence claims on capped queries, definitions from the ledger, and a claim
register for every causal sentence. Foundation breaks are exempt.

## The weekly pipeline

Read the ledger, pull the full pack, draft under the gates, harden in a fresh
context (`google-ads-reviewer` returns KEEP / DEMOTE / DROP / REPULL per
finding), reconcile against the ledger, append the ledger, stop. The human
reads an eight-line summary and approves the render. New clients enter through
`google-ads-onboarding`, which writes the first ledger and quarantines the
whole account for two cycles.

## The quarterback model

`google-ads-analyzer` is the quarterback. When diagnosis reveals a problem a
downstream skill can solve, the analyzer dispatches it with enough context to
execute immediately:

| Condition detected | Dispatch to | Hands off |
|---|---|---|
| Below-average Ad Relevance / Expected CTR on spending keywords | `google-ads-copy-optimizer` | Ad group, current headlines/descriptions, top search terms, QS breakdown |
| Waste terms > ~10% of campaign spend | `google-ads-change-scripts` | Terms to negate, match types, campaign, estimated savings |
| Below-average Landing Page Experience, or strong CTR + zero conversions for 2+ weeks | `google-ads-lp-auditor` | Landing page URL, current ad copy, QS data, campaign context |
| Ad group restructure needed | `google-ads-change-scripts` | Keywords to move, source/destination ad groups, match types |
| Ad rated POOR/AVERAGE strength | `google-ads-copy-optimizer` | Current headlines/descriptions, strength rating, top search terms |
| Live ad claim contradicted by the client's website | `google-ads-copy-optimizer` (correction, foundation-level) | Ad ID, the line, the contradicting page |
| Assets rated LOW two cycles running | `google-ads-copy-optimizer` | Ad group, LOW assets, search terms, earlier copy tests |

`google-ads-script` sits underneath all of this, it builds the data pipeline
(see `data-pipeline-contract.md`) and other ongoing automation.

`google-ads-reviewer` sits between the draft and the render as the hardener.

`google-ads-client-view` is the final step. Once the MAA is written, it renders
a client-facing version (plain-language summary plus two 13-week trend charts)
for delivery. It adds presentation only and never introduces new analysis.

## "We" tone

Write as an embedded team member: "We're seeing strong CTR on the emergency
plumbing keywords," not "Your CTR is strong."
