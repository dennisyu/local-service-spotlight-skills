---
name: boil-the-ocean
description: Operating principles for the whole skill pack. Use when running any Local Service Spotlight skill: loop until the Definition of done passes, self-verify, compound with memory. Completeness is coverage, not model tier. Read before running any skill; this governs HOW they all execute. Pair with model-judgment for which engine.
---

# Boil the Ocean — operating principles for persistent agents

This file is the operating layer beneath all ten skills in this pack: it changes nothing about WHAT each skill does and everything about HOW an agent runs it. Persistent agents loop, self-correct, hold memory, and finish end-to-end, so stopping at 90% stopped being a constraint and became a choice.

Completeness is coverage, not model tier. Boil the ocean on COVERAGE. Never on TIER. "Max effort" means do not stop at 90%. It does NOT mean run every step on the most expensive model. Your session model is the CEILING, not the floor. Which engine runs each part is `model-judgment`: cheapest tier that still clears the bar.

## The principle

Retire "don't boil the ocean." That advice kept teams focused when implementation was expensive. Garry Tan's February 2026 post (https://garryslist.org/posts/boil-the-ocean) names the turn: AI compresses implementation time 10–100x, so raise ambitions 10x and take on the whole problem.

The working rule: **always prefer the complete approach over the 90% shortcut** — full coverage, edge cases, error paths, the test, the doc. The delta between "mostly done" and "done" now costs seconds, so the marginal cost of completeness is near zero.

This was already the house rule. Dennis has taught "always boil the ocean — because good enough is not enough" for years; in his words: "do the whole thing, do it right, with tests and docs; ship the finished product, not a plan." Persistent agents are the first workers that can hold that bar on every run — without fatigue, without being asked twice.

## How to run every skill now

Eight rules. They apply to every skill in this pack, on every run.

1. **Loop until the Definition of done passes.** Every skill states its output or done-bar. Run, check, fix, run again — 90% is a draft, not a deliverable.
2. **Self-verify every run.** Before reporting done, grade your own output against the skill's QA checklist or Definition of done, line by line. No gut calls.
3. **Use memory to compound.** Read prior outputs, notes, and the upstream skills' results before starting. Never start from scratch twice — the second run begins where the first ended.
4. **Document every run as a meta-article example.** What happened, what broke, what you'd change — the write-up is the fuel for recursive self-improvement (below).
5. **Prefer full coverage.** Handle the edge cases, write the test, write the doc. Sweep every source, not the first page of results.
6. **Persist through obstacles.** Fix root causes, not workarounds — a workaround is a deviation you re-pay on every future run.
7. **When blocked, surface it and keep moving.** Name the blocker, what you need, and what you did instead — then finish everything that isn't blocked.
8. **Do it yourself — never hand a human an action you can perform.** If you have the access and the capability, execute. A numbered click-path emailed to a teammate is not a deliverable; it is the work, relabelled and queued behind someone else's inbox. Writing instructions is only correct when you genuinely cannot act: no credential, no permission, or a decision that is legitimately the human's to make. "It would be tidier if they did it," "they own that system," and "they'll want to review it" are not blockers — if you can reach it, finish it, then tell them what you changed so nobody duplicates the work. When a guardrail stops a write, that is rule 7, not rule 8: name the blocker, get authorization, then come back and finish the job yourself.

## Recursive self-improvement

**Do → Document → QA → Example (Meta-Article) → Improve (SOP update) → ↺**

Every run of every skill feeds this loop: do the task per the SOP, document the run, QA it against the canonical instructions, publish the run as a worked example, fold the fixes back into the skill, run again. Each cycle the library gets sharper and needs less of you.

The loop is the `recursive-self-improvement-qa` skill (step 10 of this pack); https://blitzmetrics.com/knowledge-system-maintenance documents the maintenance standard behind it.

## Why this is positive-sum

- **Ephemeralization** (Buckminster Fuller): do more and more with less and less until you do everything with nothing. Every documented, agent-run skill takes fewer human hours per result each cycle.
- **Jevons Paradox for intelligence:** when intelligence gets cheap, the work doesn't shrink — the amount of work worth doing explodes. Efficiency means more usage, more clients served, more jobs. Not fewer.
- **The chain:** documented skills → agents that run them → a marketplace where those agents work and eventually earn → operators freed for the judgment work only they can do.
- **The mission:** that chain is the engine behind Dennis's goal of creating a million jobs — completeness at near-zero marginal cost, multiplied across everyone who installs the library.

## Notes — Dennis's method

- Dennis's rule, verbatim: "The marginal cost of completeness is near zero with AI — do the whole thing, do it right, with tests and docs; ship the finished product, not a plan."
- This file governs execution; each skill still owns its inputs, steps, and outputs. Where they meet, the skill's Definition of done wins — this file just forbids stopping short of it.
- Boil the ocean on coverage, proof, and verification — never on adjectives, scope creep, invented work, or model tier. Completeness is not padding, and it is not "always frontier."
- Rules 1 and 2 travel together: a persistent agent that loops without verifying just automates its own mistakes.
- Install this file alongside the ten skills (Project knowledge, Skills, or your `memory/` folder) so every chat that runs a skill runs it this way.
- Date every run. "We keep the skills current" is a claim; a dated meta-article trail is the proof.

## Model landscape — kept current (August 1, 2026)

Reviewed the past month's releases. The persistent-agent thesis this file is built on is now shipping infrastructure, not a bet:

- **Claude Opus 5** (July 24, 2026) added a 1M-token context window and a per-turn reasoning-effort dial — low, medium, high, xhigh. Treat that dial as a routing lever, not a preference: raise effort for the one hard call inside a skill instead of moving the whole run to a pricier model, and drop it for the mechanical steps. Escalate effort before you escalate model.
- **Claude Sonnet 5** (June 30, 2026) is the cheap agentic workhorse — it plans, drives browsers and terminals, and self-checks. Route bulk skill runs here: draft, collect, sweep, first pass. It is now the sensible default for any step that chains several tool calls; smaller models stay right for single-shot classification and extraction inside a step.
- **Claude Fable 5** returned July 1, 2026 after a two-and-a-half-week export-control suspension. It stays the ceiling for verification and the hard calls — and that outage is the lesson worth keeping. Never let a scheduled run hard-depend on a single model. A routing table without a fallback tier is a 4am job that fails at 4am for reasons nobody in the building controls.
- **Scheduled agent tasks now run in the cloud** (July 7, 2026) — a recurring job keeps going with the laptop closed. The carve-out matters more than the headline: work that touches local files or drives a browser still needs the desktop app open. Know which of your scheduled skills are which before you assume the schedule is covered.
- **The MCP spec revision dated 2026-07-28** moved to a stateless core and is not fully backward compatible. Before upgrading any connector a skill depends on, check which revision it speaks — a routine version bump is no longer automatically safe.
- **Every major vendor now ships this file's assumptions.** OpenAI's GPT-5.6 (July 9, 2026) exposes Sol, Terra, and Luna as an explicit cheap-to-flagship ladder and adds programmatic tool calling, where the model writes a small program to coordinate tools instead of round-tripping each one. Google's Gemini 3.6 Flash and 3.5 Flash-Lite (July 21, 2026) fold computer use in as a built-in tool. A tiered ladder, real tool use, long-horizon runs — that is the shape of the whole field now, not one vendor's bet. Gemini 3.5 Pro had not shipped as of this review.
- **Managed Agents** run skills on a schedule with vault-stored secrets and browser/CLI access — this file's "persistent, looping agent" is a product surface, not just a way of working. This library is itself kept current by one.

Rule of thumb after this month: pick the cheapest tier that clears the bar, turn the effort dial before you turn to a bigger model, and give every scheduled job a fallback. See `model-judgment` for the full routing ladder.
## Definitive article & links

- The source idea: https://garryslist.org/posts/boil-the-ocean — Garry Tan, "Boil the ocean" (Feb 2026)
- Keeping the library current: https://blitzmetrics.com/knowledge-system-maintenance
- The engine the skills run on: https://blitzmetrics.com/content-factory/
- The standard at scale — the Task Library: https://blitzmetrics.com/task-library-dashboard/
- Applies to: all ten skills, `personal-brand-strategist` through `recursive-self-improvement-qa`.

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

SEE_APPLIED_FILE_FOR_REMAINING_47_LEARNING_BLOCKS_AND_SHARED_RULES
