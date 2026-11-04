# Stage 60 — Write pages 3-19 as blocks

You receive the evidence ledger, the synthesis (pages 1-2, positioning, storylines) and the
action ids. You write pages 3-19. **You choose blocks and fill fields; the renderer draws
everything.** Never write HTML, CSS or markdown tables.

## Every page

- `headline`: the page's takeaway as a sentence with a number or name, ≥ 5 words. Never a label
  ("Proof", "Overview"). Wrap the surprising part in `**…**` once.
- `dek`: 1-2 sentences — what the page shows and how to read it.
- 2-4 blocks. **At least one visual block** (graph, bars, matrix, timeline, swimlane, ladder,
  flow, topic_wheel, photo, screenshot, heatmap, qr). Tables and prose do not count as visuals.
- **≥ 3 evidence ids** cited inside the blocks, and ~260-380 words of reader text: captions,
  "So:" lines, table cells, card bodies. Depth comes from specifics, never from padding.
- Vary the visual: no three pages in a row with the same block layout.
- Spans add up to 12 per row (12, 6+6, 7+5, 8+4, 4+4+4).

## Page plan (type → what it must carry → good visual)

| n | type | Must carry | Visual |
|---|---|---|---|
| 3 | goal | buyer → problem → proof → offer; stated vs inferred goal; mutual-value hypothesis | `flow` + `table` |
| 4 | identity | two attributes, namesakes, owned surfaces, contradictions, coverage | `graph` (conflict edges for namesakes) |
| 5 | exams | renderer adds the ten-row heatmap; you add what moves the number and what it does not mean | `callout`×2 (auto `heatmap`) |
| 6 | proof | top proof ranked on the 30-point scale, where each lives, what moves to page one | `bars` + `cards` |
| 7 | connections | public associations by type, depth UNKNOWN unless proven, what not to imply | `graph` + `table` |
| 8 | assets | value-to-buyer vs current use; ranked next uses | `matrix` + `cards` |
| 9 | lighthouse | partners whose success to feature, proposed value exchange, consent gates | `matrix` + `table` |
| 10 | offer | buyer journey with door states, economics with UNKNOWNs, door-by-door fixes | `flow` + `stat_strip` + `table` |
| 11 | dollar_a_day | organic winner → $1/day × 7 → day-7 MAA → $30/30, candidates, spend gate | `flow` + `table` |
| 12 | audience | demand by topic, where each audience looks, one message each | `bars` + `cards` |
| 13 | content_factory | Produce → Process → Post → Promote state, next 30 days from real sources | `flow` + `timeline` |
| 14 | capture | topic weights from real data, questions customers ask, dated moments | `topic_wheel` + `table` |
| 15 | entity | proposed Person/Org graph, sameAs, fixes in order, panel boundary | `graph` (proposed edges) |
| 16 | search_ai | known-item vs discovery by engine, cited sources, the ask per source | `bars` + `table` + `cards` |
| 17 | agents | agent roster: skill, input, output, cadence, gate; what only the owner does | `table` (renderer adds QR) |
| 18 | plan | first seven days, days 8-30, days 31-90 by owner | renderer adds `swimlane`; you add `table`s |
| 19 | risks | conflict ledger, holds and consent, decisions only the owner makes with defaults | `conflicts` + `checklist` + `ladder` |

Pages 3-19 may be reordered or merged when the story is better; list merged types in `covers`.

## Block reference (fields)

```
prose        {text: str|[str], evidence:[ids]}
cards        {cols:1-3, items:[{badge:OBSERVED|INFERRED|UNKNOWN, title, body, so, viz?, evidence, actions}]}
stat_strip   {items:[{value, label, sub, evidence}]}            # 3-4 tiles
table        {title, columns:[...], rows:[[...]]}               # a column named "Evidence" renders id chips
callout      {tone: info|warn|decision, title, body, evidence, actions}
checklist    {title, items:[{label, state: PASS|FAIL|UNKNOWN|WARN}]}
conflicts    {items:[{metric, values:[{value, source}], resolution, evidence}]}
quote        {text, who, evidence}                               # real public words only
bars         {title, items:[{label, value:number|null, display?, highlight?}], max?, caption, evidence}
graph        {height?, center:{id,label}, nodes:[{id,label,state,sub}], edges:[{from,to,type,label}], caption, evidence}
             edge type: repeat|collab|interview|testimonial|employment|co-presence|proposed|conflict|link
matrix       {height?, x_label, y_label, quadrants:[4 labels], points:[{label,x:0-1,y:0-1,state}], evidence}
timeline     {events:[{date,label,state}], caption, evidence}
flow         {steps:[{label, detail, state, evidence}]}          # 3-5 steps
ladder       {markers:[{label, level:0-5, target:0-5}], evidence}
topic_wheel  {center_label, topics:[{label, weight}], caption, evidence}
photo        {src:"assets/…", height?, caption, evidence}        # real captured image only
```

`value: null` in bars renders UNKNOWN hatching — never write 0 for something not measured.

## Output (JSON only)

`{"pages": [ {"n": 3, "type": "goal", "kicker": "...", "headline": "...", "dek": "...", "blocks": [ ... ]}, ... ]}`

## Self-check (the gates will run these)

Each page: claim headline · ≥ 1 visual block · ≥ 3 real ledger ids · no invented number ·
no buzzwords (leverage, unlock, elevate, robust, holistic, seamless, game-changer, next level) ·
every action id you cite exists in the register · namesake rows cited only on pages 4 and 19.
