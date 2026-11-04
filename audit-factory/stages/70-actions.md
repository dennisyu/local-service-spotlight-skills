# Stage 70 — Action register (agents do the work; humans approve)

Every finding becomes an action an agent can execute and a stranger can verify. The register
becomes Basecamp to-dos automatically (`python -m factory20 basecamp`).

## Each action (all fields required)

```json
{"id": "A5", "action": "Publish the hail-claim guide page from the top video with transcript",
 "finding": "41,200-view video, no site page", "evidence": ["V-E025", "V-E030"],
 "function": "Content", "skill": "content-factory", "dependency": "Transcript of the top video",
 "destination": "vegaroofing.example/hail-claim-guide", "due": "2026-12-09",
 "human_gate": "Owner approves the page", "acceptance_test": "Guide is live, embeds the video and is indexed",
 "state": "PROPOSED", "executor": "AGENT_AFTER_APPROVAL", "window": "30"}
```

- `executor`: **AGENT** (no approval needed: schema, monitoring, reports) · **AGENT_AFTER_APPROVAL**
  (agent stages it, a named person approves the exact change, then the agent ships) · **HUMAN**
  (only a person can: choose a name, confirm a fact, record a video, sign in, approve spend,
  ask a partner). Aim for ≥ 70% agent-executed.
- `function`: the durable owning function (Web, Content, Search & entity, Reputation, Analytics,
  Paid media, Social, Outreach, Owner decision) — never a person's name.
- `skill`: the exact routed skill (business-website-agent, content-factory,
  knowledge-panel-entity-seo, positive-mentions-harvester, measurement-analytics,
  dollar-a-day-strategist, geo-visibility-audit, evidence-verification, social-amplification-engine,
  business-brand-strategist, reputation-gap-analyzer).
- `due`: a real date from the plan start; `window`: 7, 30, 60 or 90.
- `acceptance_test`: something a stranger can open and see — a URL returning 200, a test lead
  arriving, a schema validator result, a metric in a named report.
- `state`: PROPOSED until the gate clears.

## Shape of a good register

12-40 actions · the first seven days fix anything that leaks leads (forms, phones, tracking)
before any content or spend · owner decisions come first because others depend on them ·
every page-2 card's action ids exist here · no "build awareness", "post more", "improve SEO".

## Output (JSON only)

`{"actions": [ ... ]}`
