# Stage 40 — Brand Authority score (ten rows; code checks you)

Score each row 0-10 against its anchor, cite the evidence ids, and give one sentence of reason.
Code then adds the rows and **rejects any number its evidence cannot carry** — so score what the
ledger proves, not what you believe.

## Anchors (shared)

| Score | Standard |
|---:|---|
| 0 | active harm: a false, broken or misidentifying condition (name it in `harm`) |
| 1 | checked and absent |
| 2 | fragment or self-claim only |
| 3-4 | basic asset or isolated corroboration; real gaps |
| 5-6 | credible, partly corroborated; incomplete coverage or linkage |
| 7-8 | strong, current, **independently corroborated** — needs ≥ 2 independent OBSERVED rows |
| 9-10 | high anchor across surfaces — needs ≥ 4 independent OBSERVED rows |

A row resting only on SELF-CLAIM or FIRM-UNATTRIBUTED rows **cannot exceed 4**. A row you did
not check is `"score": "UNKNOWN"`, never 0 or 1.

## Rows

1 Entity home and name rank · 2 Media relationships and offline authority · 3 Content assets ·
4 Social proof · 5 Monetizable positioning · 6 Consistency and schema hygiene ·
7 Current-channel momentum · 8 Link authority to entity home · 9 Search visibility beyond name ·
10 Knowledge Graph presence (graph object only — panel visibility and owner claim are separate).

## Output (JSON)

```json
{"brand_authority": {"rubric": "brand-authority@1.1", "pass_line": 80, "rows": [
  {"n": 4, "score": 7, "why": "386 reviews at 4.9, BBB A+, 104 reviews naming her — strong and current.",
   "evidence": ["V-E011", "V-E016", "V-E013"]}
]}, "separate": [
  {"name": "Website QA", "value": "3 / 10 pass", "note": "form, financing, tap-to-call, speed fail", "evidence": ["V-E031"]}
]}
```

## Known failure to avoid

Cheap drafters run **3-5 points generous on the qualitative rows** (social proof, positioning,
momentum): they credit a company's audience as the person's, credit an offer whose buy button is
broken, or credit "2026 activity" while ignoring a 661-day gap in their own notes. Before you
answer, re-read every gap you wrote and lower any row your own gap text contradicts.
