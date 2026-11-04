# Stage 50 — Synthesis: the eight findings that change the plan (frontier slice)

This is where frontier judgment pays for itself. You read the whole evidence ledger and write
the two pages a busy owner actually reads: the cover and the executive summary. Everything after
page 2 elaborates what you decide here.

## What a finding is

A finding is **a checked fact the reader would not have guessed, that changes a decision.**
It has four parts, always:

1. **Title** — the surprising fact as a claim, with a number, ≤ 12 words.
   "236 of 386 reviews describe an insurance claim. The homepage never says it."
2. **Body** — 30-50 words of proof: the numbers, the sources, the dates, named. No adjectives
   doing the work of evidence.
3. **So:** — the decision it changes, in one sentence of 8-18 words a fifth grader understands.
4. **Ids** — evidence ids that prove it and the action ids that act on it.

**Page 2 is one printed page.** Eight cards fit at about **600 words in total** (titles + bodies +
"So:" lines), counting each micro-chart as 20 words; six or fewer cards get about 80 more. Gate
G24 checks this budget before rendering, and if the page still runs over, the render report says
by how much and which card is tallest. Cut words; never ask for smaller type. Both blind-test
drafts of 2026-11-04 overflowed page 2 on their first render; one still ran over after three
fix rounds at 535 words and five charts.

Bad: "Strong reputation but weak online presence." (true of everyone; no number; no decision)
Good: "Her best video has 41,200 views. Her website has 0 videos." (two numbers that should
not sit together; the decision is obvious)

## The reasoning moves (use at least five different ones across the eight cards)

| Move | Look for | Example |
|---|---|---|
| **Contrast** | two numbers that should not coexist | 1,149 episodes vs 33 reviews |
| **Stranded authority** | proof on someone else's domain that never points home | TV segment links to a dead Facebook page |
| **Name collision** | the bare name belongs to someone else in search, the graph or an AI answer | first six results are a realtor and an actress |
| **Contradiction ladder** | the subject's own numbers disagree across surfaces | 3,000 / 4,000 / 4,500 / 5,000 retailers |
| **Dead door** | a listed URL, form, phone or buy button that fails | form emails a domain that expired |
| **Market's word vs their word** | what customers call them vs what they call themselves | 61% of reviews say "claim"; site says "quality" |
| **Buyer mismatch** | content speaks to buyer A, the offer sells to buyer B | podcast for owners, product for bookkeepers |
| **Invisible graph** | a dense real network published nowhere machines can read | repeat guests never linked or credited |
| **Momentum cliff** | activity that stopped, with the date | 194 days since the last video |
| **Proof ladder** | tier-1 proof hidden while tier-3 self-claims lead | award absent, unsourced quotes on the hero |
| **Our own footprint** | what our team built or changed, stated plainly | our placeholder domain, our Wikidata edits |
| **Measurement blind spot** | the goal cannot be measured from today's setup | 0 conversion events, no call tracking |
| **Already-offered unlock** | a ready action that only needs a yes | the repurposing offer that got no reply |
| **Rival with less** | a competitor that outranks them with fewer assets, and what it does instead | DR 49 vs 37 from fewer referring domains |
| **Brief vs evidence** | facts the brief or work order states that the ledger does not support — say so, never print them as settled | "Target 2,000+" appears in the brief, not on any page |

The last two are the calls a non-frontier model missed in the Nov 4 blind test while finding
11 of the other 12, so look for them on purpose.

At most two of the eight cards may be UNKNOWN. If more of your candidates are UNKNOWN, the
research is unfinished — say so and send the gap back to stage 10 instead of writing around it.

## Honesty rules (code checks most of these)

- A self-claim stays attributed: "the site says 3,500+ roofs", never "she has replaced 3,500 roofs".
- Sales copy is not an audited fact: a "$60M founder" product title does not become "$60M company".
- A visible panel is not a claimed panel; a graph object is not a panel.
- Co-presence is not a relationship; a relationship is not permission.
- No invented market size, conversion rate or revenue. UNKNOWN beats a plausible guess.

## Output (JSON only)

```json
{
  "positioning": {"buyer": "...", "problem": "...", "proof": "...", "offer": "...", "state": "INFERRED"},
  "storylines": ["claim positioning", "broken doors", "stranded media proof", "name collision", "measurement"],
  "next_decision": "One sentence: the decision only the owner can make, and what starts when she answers.",
  "pages": [
    {"n": 1, "type": "cover", "kicker": "Personal & company brand audit",
     "headline": "**386 five-star reviews** say she is Tulsa's insurance-claim roofer. Her website says “quality roofing.”",
     "dek": "2-3 sentences: who the buyer is, the most useful finding, the decision this audit enables.",
     "blocks": [
       {"type": "stat_strip", "span": 12, "items": [{"value": "4.9★", "label": "386 Google reviews", "sub": "BBB A+ since 2015", "evidence": ["V-E011"]}]},
       {"type": "finding_map", "span": 7, "items": [{"title": "...", "proof": "...", "evidence": ["..."]}]},
       {"type": "photo", "span": 5, "src": "assets/....png", "caption": "what it establishes", "evidence": ["..."]},
       {"type": "callout", "span": 6, "tone": "info", "title": "What she asked for", "body": "...", "evidence": ["..."]},
       {"type": "callout", "span": 6, "tone": "decision", "title": "If you read only this — the first week", "body": "...", "actions": ["A1"]}
     ]},
    {"n": 2, "type": "summary", "kicker": "Executive summary — what changes the plan",
     "headline": "Eight things the evidence says that you would **not guess** from their profiles",
     "dek": "...",
     "blocks": [{"type": "cards", "span": 12, "cols": 2, "items": [
       {"badge": "OBSERVED", "title": "...", "body": "...", "so": "...",
        "viz": {"type": "pair", "a": {"label": "...", "value": 236}, "b": {"label": "...", "value": 0}},
        "evidence": ["..."], "actions": ["A3"]}
     ]}]}
  ]
}
```

Cover: exactly four stats, five finding-map items, a real captured image, the ask box and the
first-week strip. `**bold**` in a headline renders in the accent colour — use it once, on the
surprising part. `viz` is optional per card; give at least two cards a `pair` (two numbers to
scale) or `doors` (`{"type":"doors","items":[{"label":"Form","ok":false}]}`) micro-chart.
Use action ids A1, A2… now; stage 70 fills in the register that matches them.
