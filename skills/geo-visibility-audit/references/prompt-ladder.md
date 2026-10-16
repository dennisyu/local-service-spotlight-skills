# Building the prompt ladder

The audit is only as good as the prompts. Nine well-chosen prompts beat fifty
generic ones, because each one has to be a question a real buyer would actually type.

## The two tiers, and why the split matters

| Tier | The prompt names… | What it measures | Fixed by |
|---|---|---|---|
| **Known-item** | the person or their company | Does the entity exist in the model, and is it described correctly? | Owned pages, consistent bio, schema, a Knowledge Panel |
| **Discovery** | only a *need* | Do they get recommended to a stranger? | Third-party directories, roundups, review platforms, speaker rosters |

Reporting a single blended "AI visibility" number hides which of these is broken, and
they have completely different fixes. Always report them separately.

## Known-item prompts — 4 minimum, all four engines

1. `Who is {full name}? What is he known for, and what sources support that?`
2. `Who is the CEO/founder of {company}?`
3. `Who runs {their community, event, podcast or programme}?`
4. `Is {company} any good? What do reviews say?`

Add, when they apply:

5. `What has {name} spoken about at conferences?` — tests whether speaking has left a trace
6. `What is {name}'s background before {company}?` — tests biographical depth
7. `{name} vs {closest named peer}` — surfaces who the model thinks the peer set is

**Run #1 on all four engines.** It is the single highest-value cell in the whole
audit and the engines disagree in informative ways.

## Discovery prompts — 5 minimum

Derive these from the buy box, not from keyword tools. The question is what the buyer
types the week before they buy.

1. `Best {category} agency in {country}` — the short head. Hardest, most valuable.
2. `Best {category} agency in {their city}` — local variant; often a different source set.
3. `Top {category} experts to follow in {year}` — the personal-brand equivalent.
4. `Who are the top {category} speakers in {country}?` — if they speak.
5. **The long one.** Write it as the buyer, with real constraints:

   > "I run a UK ecommerce brand doing about £5M a year on Magento. Which UK agencies
   > and consultants should I shortlist to help me replatform and improve conversion?
   > Name specific people and firms."

   Run this one on **Perplexity sonar-pro**. Long high-intent questions surface deeper
   shortlists than short head terms, so this is usually where a mid-tier player first
   appears. It is the leading indicator that discovery-tier work is landing — watch it
   week over week.

## Scoring rules

- **Named** = the person or their company appears in the answer body. A citation
  without a mention is a half-win — record it, but do not score it as named.
- **Absent** = not present. Always record who won instead **and the source page the
  model used.** That page is the action item.
- Never soften an absence. The value of this audit is that it is the one report that
  says plainly where the client is not showing up.

## Turning losses into actions

Every discovery loss hands you a URL. From one real run:

| Lost prompt | Model's source | Action |
|---|---|---|
| Best Magento agency UK | goodfirms.co | Get listed on GoodFirms |
| Best ecommerce agency Manchester | sortlist.co.uk | Get listed on Sortlist |
| Top UK ecommerce speakers | ecomm.live/speakers | Apply to the speaker roster |
| Top Magento experts 2026 | echoglobal.tech | Pitch the listicle — 19 names, all reachable |

Four prompts, four named assets, no guessing. This is the payoff of running discovery
prompts properly.

## Week over week

Keep the prompt set **fixed** so the numbers compare. Add prompts, never swap them —
a changed prompt set silently resets the baseline. Log the set with the run date so
next week's agent runs the same ladder.
