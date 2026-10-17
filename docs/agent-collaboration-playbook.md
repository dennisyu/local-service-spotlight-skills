# How to equip your AI agents to work together

This is the public playbook behind the Local Service Spotlight agent fleet. It answers the question we hear most often: **"How do I get my Claude, Codex, Grok, or other agents to share knowledge and pick up each other's work the way yours do?"**

Everything below is implemented in this repository, so you can inspect the working version instead of trusting a description.

## The short answer

Agents coordinate through files, not through conversations. Give them one canonical repository of written skills and standards, one operational log of everything they do, and a scheduled review that turns experience back into documentation. Any agent — any vendor — that can read markdown can then join the fleet.

## How do agents share one source of truth?

One public GitHub repository holds every skill as a portable `SKILL.md` file (see `skills/`). The same repository installs into Claude, Grok Build, and other agent hosts, so every agent reads identical instructions. Bundles in `.claude-plugin/marketplace.json` are selections over the same `skills/` folder — skills are never copied between bundles, so there is nothing to drift.

## How does a hard-won lesson reach every agent?

A lesson is written once as a single markdown file in `standards/`. A sync script stamps that rule verbatim into `AGENTS.md` and every applicable `SKILL.md`, and CI rejects any pull request where a required copy is missing or stale. One file produces the agent instruction, the human checklist, and the automated check — the rule and the thing that enforces it cannot disagree. The full story: [HOW-KNOWLEDGE-PROPAGATES.md](../HOW-KNOWLEDGE-PROPAGATES.md).

## How does a new agent pick up a task it has never seen?

The fleet keeps a private operations log — one markdown file per operation, each recording:

- who approved the work and what triggered it,
- which agent did it and through what access path,
- the exact scope, commands, and tools used,
- verification evidence proving the end state,
- rollback steps and backup locations.

An agent arriving cold greps the log for the system it is about to touch, reads the matching runbook, and can reconstruct — or undo — any past operation without asking a human. The rule that makes it work: *an agent that changes production state without logging it has not finished the job.*

## How do you know an agent actually did the job?

Receipts, not claims. Every installation, update, and scheduled job has acceptance checks — see [ACCEPTANCE.md](../ACCEPTANCE.md). A plugin in a list proves installation; a good answer alone does not prove that the installed skill was used.

## How does the system keep improving?

A scheduled weekly review reads the operations log, scores entries against the documentation standard, extracts reusable patterns, and promotes them here as pull requests — including improvements to the standard itself. Documentation is a loop, not a project.

## How do I copy this for my own team?

1. Create one canonical repository of skills — written recipes, one folder each, portable across agent hosts.
2. Add an `AGENTS.md` at the root: the operating manual every agent reads first.
3. Keep a private ops log with the entry format above; make logging part of the definition of done.
4. Write every house rule once and sync it mechanically into every skill — never maintain copies by hand.
5. Require receipts: verification evidence inside every log entry and every install.
6. Schedule a recurring review that reads the log and feeds lessons back into the repository.

Start small: one skill, one log, one rule. The loop compounds.
