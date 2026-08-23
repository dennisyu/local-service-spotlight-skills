---
name: gct-qualify-screen
description: >-
  Use before staffing the Social Amplification Engine agentic package. Score
  whether a business has clear Goals, Content, and Targeting plus enough proof
  to amplify. PASS enters the package; FAIL stays on the self-serve start page.
---
# GCT Qualify Screen

**Use this when** someone wants agents to run the full SAE / Content Factory package, or when filling the public start-page inventory. Screen first. Do not spend agent cycles on undifferentiated or proof-empty businesses.

## Naming lock (Strategy Bot 2026-08-22)

The SAE course page lists Goals / Content / Targeting as **three sequential stages** (Stages 2–4). That is **course taxonomy** for the package run after PASS.

`gct-qualify-screen` is different: GCT is **one Nine Triangles gate** — three corners scored together with proof. Do **not** make agents run three separate stage pass/fails before qualify. PASS/HOLD/FAIL is a single card.

Public framing: https://theninetriangles.com/ · https://localservicespotlight.com/tasks/gct-goals-content-targeting/

## Inputs

- Website, GBP, recent posts/ads
- Reviews / testimonials / named mentions (even thin)
- What they say they sell and to whom
- Roster status if known

## Score each corner (0–5)

### Goals
- 5: One mission / end result a stranger can repeat; 90-day numbers named
- 3: Directionally clear but fuzzy metrics
- 0: “Get more leads / awareness” only

### Content (proof)
- 5: Multiple checkable proof points (jobs, reviews, named mentions, video)
- 3: Some reviews or photos; thin story
- 0: New idea, no trail, stock claims

### Targeting
- 5: Named ICP + geography or niche; few SKUs they want more of
- 3: Local but broad; too many services
- 0: “Anyone”; national with no niche; 20+ products equally pushed

### Differentiation (swap test)
- Pass/Fail: one sentence that could not sit on a competitor’s site unchanged

## Decision

| Result | Rule |
|---|---|
| **PASS** | Goals≥3 AND Content≥3 AND Targeting≥3 AND Differentiation Pass |
| **HOLD** | Close but missing access owner or one thin corner — list exact fix |
| **FAIL** | Any corner 0, Differentiation Fail, Not Active roster, or no proof path |

## Disqualify patterns (Dennis)

- New idea with no credibility trail
- Competitive market, not differentiated
- Serving too many people / too many products
- No clear processes

## Output card (always)

```
entity:
date:
goals_score: /5 + evidence
content_score: /5 + evidence
targeting_score: /5 + evidence
differentiation: Pass|Fail — sentence
decision: PASS|HOLD|FAIL
evidence_urls: []
gaps: []
next_action: # one owner + date
package: # social-amplification-engine | start-page-only
```

## After the screen

- **PASS** → hand to `social-amplification-engine` + `one-session-client-onboarding`
- **HOLD** → one requirement list; re-screen when closed
- **FAIL** → start-page GCT inventory only; do not staff

## Do not

- Soft-pass to be nice
- Invent proof
- Staff agents on FAIL
- Ask the prospect to write a blank biography (prefill from public evidence)
- Run three separate stage pass/fails for Goals then Content then Targeting before qualify

## Canonical GCT framing

- `nine-triangles` skill
- https://theninetriangles.com/
- https://localservicespotlight.com/tasks/gct-goals-content-targeting/

GCT is the screen triangle before Content Factory. Do not invent a second GCT.

## Pairs with

`nine-triangles`, `business-brand-strategist`, `evidence-verification`, `positive-mentions-harvester`, `social-amplification-engine`
