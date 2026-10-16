# Report structure and the weekly MAA block

Two deliverables from every run: a visual report, and six lines that paste into the
Basecamp MAA thread. The MAA block is the one that has to exist every week.

---

## The MAA GEO block — paste-ready

Add this under **Metrics** in the weekly MAA, above SEO Performance. Keep the field
names identical week to week so the numbers line up.

```
GEO / AI Visibility (live-queried {date})

• Engines recognising {name}: 4 of 4 (ChatGPT, Gemini, Perplexity, Claude) — no change
• Distinct domains cited as evidence: 15 (+3)
• Third-party share of citations: 63% (26 of 41) — up from 40%
• Known-item prompts won: 7 of 7
• Discovery prompts won: 1 of 5 (+1 — MageCloud now #7 on Perplexity's UK shortlist)
• New citing source this week: cm-alliance.com

Clean referring domains: 27 (+1). Raw count 407, of which 380 Ahrefs-flagged spam.
```

Rules for this block:

- **Clean referring domains, always, with the raw number beside it.** Never report a
  raw refdomain delta as progress without checking `is_spam` first.
- Name the new citing source. One named domain is more convincing than any percentage.
- If a number did not move, write "no change" rather than dropping the line. A flat
  metric that is being watched reads very differently from a metric that vanished.
- Discovery-tier movement is the headline when it happens. It is the hardest number
  to move and the one that maps to revenue.

---

## The visual report

Build with the `dataviz` skill. Validate the palette with the script; do not eyeball it.

| § | Section | Chart |
|---|---|---|
| — | **Finding in one line** | none — a callout, written as a sentence a client can repeat |
| — | **Stat tiles** ×4 | engines recognising · distinct domains · citation instances · discovery won |
| 01 | **The two tiers** | horizontal bars, one row per prompt, grouped by tier, bar length = sources returned, colour = named/absent |
| 02 | **The evidence base** | table: domain × type × DR × which engines cited it |
| 03 | **Positioning** | claim consistency — n of 4 engines per claim; plus 3–4 verbatim quotes |
| 04 | **Direction of travel** | two line charts side by side: DR, and clean referring domains |
| 05 | **The measurement problem** | one stacked bar: spam vs clean, share labelled |
| 06 | **Troubleshooting** | table: what we tried → result → why. Include the dead ends. |
| 07 | **Benchmark** | bar chart of indexed AI citations by property |
| 08 | **Actions** | numbered list, each naming a specific page/directory and an owner |

Every chart gets a table view behind a toggle, a hover tooltip, and dark mode.

---

## Tone

This report usually lands in a thread where a colleague already filed a weekly update
that did not have this data. Three rules:

1. **Never frame it as a correction.** Frame it as new instrumentation. The previous
   report was not wrong; it was measuring what the older tools could see.
2. **Give the method away in the report.** §06 exists so the next person can run it
   without asking. Explaining why Ahrefs returns zero is more useful than the zero.
3. **Lead with what is working.** There is almost always a real win in the identity
   tier — open with it, then spend the length of the report on the gap.

Bad: "Dylan's MAA missed GEO rankings."
Good: "Adding a GEO block to the weekly from here — here is the first one, and here
is why the tools we were checking showed nothing."

---

## Cadence

- **Weekly:** the MAA block. ~15 minutes. Fixed prompt ladder.
- **Monthly:** full visual report, with month-over-month deltas on every metric.
- **On placement:** when a new directory listing or press hit goes live, re-run the
  discovery prompts it should affect within 2–3 weeks and record whether it moved.
  This is how the team learns which placements actually buy citations — log the result
  either way, including the ones that did nothing.
