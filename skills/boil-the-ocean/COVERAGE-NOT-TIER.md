---
title: Header rewrite for boil-the-ocean
status: apply-to-SKILL.md
---

Do not merge this note as a replacement for SKILL.md. Apply the four replacements below to `skills/boil-the-ocean/SKILL.md`, keep every field learning, then delete this file.

## 1. YAML description

Replace the description line with:

```
description: Operating principles for the whole skill pack. Use when running any Local Service Spotlight skill: loop until the Definition of done passes, self-verify, compound with memory. Completeness is coverage, not model tier. Read before running any skill; this governs HOW they all execute. Pair with model-judgment for which engine.
```

## 2. Opening paragraph

Replace the Fable-5 opening with:

```
This file is the operating layer beneath all ten skills in this pack: it changes nothing about WHAT each skill does and everything about HOW an agent runs it. Persistent agents loop, self-correct, hold memory, and finish end-to-end, so stopping at 90% stopped being a constraint and became a choice.

Completeness is coverage, not model tier. Boil the ocean on COVERAGE. Never on TIER. "Max effort" means do not stop at 90%. It does NOT mean run every step on the most expensive model. Your session model is the CEILING, not the floor. Which engine runs each part is `model-judgment`: cheapest tier that still clears the bar.
```

## 3. Heading

`## How to run every skill now (Fable 5 and friends)` → `## How to run every skill now`

## 4. Notes bullet

Replace the coverage bullet with:

```
- Boil the ocean on coverage, proof, and verification — never on adjectives, scope creep, invented work, or model tier. Completeness is not padding, and it is not "always frontier."
```

Leave the August 2026 model landscape and every `<!-- learning:... -->` block untouched. Fable 5 may stay in the landscape as the ceiling / fallback example, not as the required engine.
