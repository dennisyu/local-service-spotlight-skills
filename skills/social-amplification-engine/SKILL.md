---
name: social-amplification-engine
description: >-
  Use when packaging or running Dennis Yu's Social Amplification Engine as an
  agentic service for a client that already passed the GCT qualify screen.
  Orchestrates existing LSS skills across the six SAE stages; does not invent
  a parallel method.
---
# Social Amplification Engine (orchestrator)

**Use this when** a client (or Special Project) has clear Goals, Content, and Targeting plus proof, and you need agents to run the full loop: plumbing → Content Factory → Dollar-a-Day → weekly MAA.

This skill is a **router and runbook**. It does not replace `client-access-checklist`, `content-factory`, `dollar-a-day-strategist`, or `weekly-brand-maa`. Read and run those skills for their phases.

Canonical course leaf (SEO only, do not promote BlitzMetrics): https://blitzmetrics.com/sae/

## PARAMETERS (caller supplies)

```
entity_name:
roster_status: # Active Client | Special Project — never Not Active
gct_screen_result: # PASS required; path to qualify card
canonical_brief: # path or URL to verified GCT + proof
owner:
steward:
domains: []
handles: {}
access_register:
maa_delivery: # Basecamp / email / Drive path
dad_budget_cap: # default $1/day tests; never invent spend
report_dir:
escalate_rule:
```

## Preconditions

1. Roster status is Active Client or Special Project (`client-roster-never-delete`).
2. `gct-qualify-screen` returned **PASS** with evidence.
3. Steward lock respected (one writer). If another steward holds the claim, stop.
4. Read `boil-the-ocean` operating rules before looping.

## Six stages → skills

| Stage | Name | Run |
|---|---|---|
| 1 | Plumbing | `client-access-checklist` until rows 1–4 green |
| 2 | Goals | `business-brand-strategist` + `nine-triangles` (GCT Goals) — confirm, do not blank-form |
| 3 | Content | `positive-mentions-harvester` → `evidence-verification` → `content-factory` produce/process + `definitive-article-writer` / `video-repurposing-agent` as needed |
| 4 | Targeting | Lock ICP + geo/niche from GCT; write targeting last on every boost (`dollar-a-day-strategist`) |
| 5 | Amplification | `dollar-a-day-strategist` on proven organic only |
| 6 | Optimization | `weekly-brand-maa` every Friday (certainty date from `one-session-client-onboarding`) |

Content Factory line inside stages 3–5: **produce → process → post → promote**.  
Skill alias “4 P’s” (Plumbing, Publish, Promote, Perform) maps Perform → Stage 6 MAA.

## Kickoff sequence

1. Run `one-session-client-onboarding` (prefilled GCT; access in one sitting).
2. Stage 1 until gate green. Content does not ship before rows 1–4.
3. Stage 2–3: lock brief, harvest proof, stand up one canonical hub per major claim.
4. Stage 4–5: post organic; boost only winners per Dollar-a-Day rules.
5. Stage 6: schedule Friday MAA with PARAMETERS for `weekly-brand-maa`.
6. Loop: ask client only for more proof, more raw content, or more budget on winners. Agents own the rest.

## Definition of done (package live)

- [ ] Qualify card PASS on file
- [ ] Access rows 1–4 green (or routed blocker with owner + date)
- [ ] Verified GCT brief saved
- [ ] At least one canonical hub URL live
- [ ] Dollar-a-Day candidate list exists (even if spend not yet approved)
- [ ] Friday MAA scheduled with delivery channel
- [ ] Agent note written; status board updated

## Do not

- Staff FAIL screens
- Boost unproven posts
- Promote BlitzMetrics as the product brand (use Local Service Spotlight / person / vertical)
- Duplicate recipes that already live in child skills
- Send client or Basecamp messages without approval when the desk requires it
- Start a second OS copy in dennis-os-vault for client knowledge (BlitzBase is SoT)

## Pairs with

`gct-qualify-screen`, `skill-registry`, `recursive-self-improvement-qa`

## Receipt

Leave entity, stages completed, skill versions/commit, blockers, next Friday MAA date.
