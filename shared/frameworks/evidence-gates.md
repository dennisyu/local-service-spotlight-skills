# Evidence Gates

The mechanical rules that decide whether a finding may become an Action. They
exist because the most expensive failure in a weekly MAA is not a missed
problem; it is a confident recommendation built on a week of noisy data, a
truncated query, or a change nobody wrote down. Every gate here traces to a
real miss on a live account.

The gates are applied twice: by the analyzer while drafting, and by the
reviewer (the hardener) in a fresh context. Neither may waive one. A gate can
only be overridden by the client's ledger, and only where the ledger says so
in a dated standing rule.

## Exempt: foundation breaks

Tracking not firing, geo leaking outside the service area, a bid strategy with
no conversion signal behind it, policy disapprovals, an account or campaign not
serving, budget capped on multiple days in one 7-day window. These are acted on
immediately, on any sample size. Everything else passes the gates.

## The gates

| # | Gate | Rule | Failure it prevents |
|---|---|---|---|
| 1 | Minimum sample | No pause, restrict, bid, budget or copy action on fewer than 30 clicks or 5 conversions in the window cited. Below that, the observation goes to the ledger watch list with a first-seen date. | Restricting a broad term on 48 clicks and 1 conversion, 20 of which were Search Partners. |
| 2 | Persistence | A performance finding becomes an Action only after it has sat on the ledger watch list for two prior cycles. The drafter cannot promote a finding it created this week. | "Query collapse" declared from seven clicks; desktop "collapsed" at 3.5% of spend. |
| 3 | Recent-change quarantine | Anything in the ledger change log under 14 days old cannot be evaluated as a problem or credited as a fix. The draft may say "launched on date, still in ramp." | Reading six days of zero brand impressions as a demand verdict on a campaign launched mid site-rebuild. |
| 4 | Split before verdict | Network (Search vs Partners vs Display) and device splits are pulled before any keyword-level verdict. | The same 48-click case. |
| 5 | Daily before average | Any impression-share-lost-to-budget or spend figure is checked by day before it is averaged. One capped day is reported as one capped day. | A budget increase queued off 12.5% budget-lost that was a single 45% day averaged into a week. |
| 6 | No absence on a capped set | If a query returned exactly its row cap, the drafter may not claim anything is absent from that dataset. Query for the specific items instead. An absence claim also names the levels queried: "nothing is disapproved" is true only for the levels pulled (ads, campaign assets, ad group assets). | "The negatives are not in the account" from a 200-row cap over a 190-item list. "Nothing is disapproved anywhere" from an ad-level pull while two image assets sat at ASSET_DISAPPROVED (2026-09-11). |
| 7 | All statuses | Absence claims about keywords, ads or negatives require a query with no status filter. | A keyword reported as nonexistent that had been paused before the engagement started. |
| 8 | Definitions from the ledger | Lead definition, target, windows and the service-area test come from the ledger. Never from the data, a campaign name, or a guess. | Headlining 12 raw calls when the client's number is 5 counted calls. |
| 9 | Claim register | Every causal or trend sentence in Analysis carries a reference to the dataset and row it rests on, in the Generation notes block. A sentence without one is deleted, not softened. | Six invented or upgraded claims caught in a single render trace check. |
| 10 | Symmetry | Gates apply to good news, bad news and the analyzer's own new theories alike. Being wrong toward alarm is not evidence for the optimistic story. | A landing page test called confounded, then clean, then withdrawn, then restored, in one session. |

## What passes a gate looks like

- "We are watching `house painting near me`: 77% of Exterior spend at $860 per lead over five cycles, and the Partners traffic that inflated its click count is now off. If it still holds over 60% of spend at a CPA above $300 after two clean weeks, we will move it to its own ad group." (Gate 1 and 2 satisfied; the action is dated and conditional.)
- "The brand campaign has shown no impressions since launch. It went live in the middle of the site rebuild, so we are giving it two more cycles before reading that as demand." (Gate 3 applied in the open.)

## What fails a gate looks like

- "Desktop conversions collapsed this week." (Gate 1: 7 clicks. Gate 2: first seen this week. Gate 8: the ledger says desktop is not reported.)
- "The negatives from last week did not land." (Gate 6: capped query. Never make the claim; query the terms.)

## Where the gates live

- `skills/google-ads-analyzer/SKILL.md` applies them while drafting.
- `skills/google-ads-reviewer/SKILL.md` re-applies them to every finding and returns a verdict.
- `skills/google-ads-onboarding/SKILL.md` seeds the ledger so gates 2, 3 and 8 have something to check against from cycle one.
- The per-client ledger (`ledger-template.md`) carries the watch list, change log and quarantine the gates read.
